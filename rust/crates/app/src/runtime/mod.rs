//! Minimal runtime for orchestrating long-running services with graceful shutdown.
//!
//! The runtime provides two primitives:
//!
//! - [`Service`] — a trait for anything that runs over shared state until told to stop.
//! - [`ShutdownHandle`] — listens for OS signals (SIGINT/SIGTERM), broadcasts shutdown
//!   to all services, and waits for them to finish.
//!
//! # How it works
//!
//! 1. Create a [`ShutdownHandle`]. This starts listening for SIGINT/SIGTERM and
//!    returns a `watch::Receiver<()>` that will fire when a signal arrives.
//!
//! 2. Spawn services. Each service gets a clone of the shutdown receiver.
//!    When the receiver fires, the service is responsible for its own cleanup
//!    (draining connections, finishing in-progress work, flushing buffers, etc).
//!
//! 3. Call [`ShutdownHandle::wait`]. This blocks until a signal arrives, then
//!    waits up to 30 seconds for all services to exit before force-killing.
//!
//! # Example
//!
//! ```rust,ignore
//! use crate::runtime::{Service, ShutdownHandle};
//!
//! // Define a service — just implement `run`.
//! struct MyServer;
//!
//! #[async_trait::async_trait]
//! impl Service for MyServer {
//!     type State = AppState;
//!
//!     async fn run(state: AppState, mut shutdown_rx: watch::Receiver<()>) {
//!         let listener = TcpListener::bind(state.addr).await.unwrap();
//!         axum::serve(listener, app)
//!             .with_graceful_shutdown(async move {
//!                 let _ = shutdown_rx.changed().await;
//!             })
//!             .await
//!             .unwrap();
//!     }
//! }
//!
//! // In main: create handle, spawn services, wait.
//! let (mut handle, shutdown_rx) = ShutdownHandle::new();
//!
//! // `spawn` is provided for free — it tokio::spawns `run` and returns the handle.
//! handle.push(MyServer::spawn(state.clone(), shutdown_rx.clone()));
//! handle.push(MyWorker::spawn(state.clone(), shutdown_rx.clone()));
//!
//! // Blocks until SIGINT/SIGTERM, then waits for services to finish.
//! handle.wait().await;
//! ```

use std::time::Duration;

use futures::future::join_all;
use tokio::signal::unix::{signal, SignalKind};
use tokio::sync::watch;
use tokio::task::JoinHandle;

/// Maximum time to wait for services to shut down after a signal is received.
/// If services haven't exited by this point, the process is force-killed.
const FINAL_SHUTDOWN_TIMEOUT: Duration = Duration::from_secs(30);

/// Grace period after SIGTERM before broadcasting shutdown. This gives
/// load balancers time to stop routing traffic before we start tearing down.
/// SIGINT (ctrl-c) shuts down immediately with no grace period.
const REQUEST_GRACE_PERIOD: Duration = Duration::from_secs(10);

/// A long-running service that runs over shared state.
///
/// Implement [`run`](Service::run) to define what the service does.
/// [`spawn`](Service::spawn) is provided for free — it wraps `run` in
/// `tokio::spawn` and returns the join handle.
///
/// Each service owns its own shutdown logic. When `shutdown_rx` fires,
/// the service decides how to wind down: drain connections, finish current
/// jobs, flush buffers, or just return immediately.
#[async_trait::async_trait]
pub trait Service: Send + 'static {
    /// The shared state this service runs over. Typically `AppState`.
    type State: Clone + Send + Sync + 'static;

    /// Run the service until `shutdown_rx` fires or the service completes.
    ///
    /// This is the only method you need to implement. The service should
    /// monitor `shutdown_rx` and exit gracefully when it fires.
    async fn run(state: Self::State, shutdown_rx: watch::Receiver<()>);

    /// Spawn the service on the tokio runtime.
    ///
    /// You get this for free. Just push the returned handle into a
    /// [`ShutdownHandle`] so the runtime can wait on it during shutdown.
    fn spawn(state: Self::State, shutdown_rx: watch::Receiver<()>) -> JoinHandle<()> {
        tokio::spawn(Self::run(state, shutdown_rx))
    }
}

/// Orchestrates graceful shutdown across multiple services.
///
/// Listens for SIGINT and SIGTERM. When a signal arrives, broadcasts shutdown
/// to all services via the `watch` channel, then waits for them to finish.
///
/// - **SIGINT** (ctrl-c): immediate shutdown broadcast.
/// - **SIGTERM** (e.g. from container orchestrator): waits [`REQUEST_GRACE_PERIOD`]
///   before broadcasting, giving load balancers time to drain.
pub struct ShutdownHandle {
    /// Task that blocks until a signal is received.
    graceful_waiter: JoinHandle<()>,
    /// Join handles for all spawned services.
    handles: Vec<JoinHandle<()>>,
}

impl ShutdownHandle {
    /// Create a new shutdown handle and its associated receiver.
    ///
    /// The returned `watch::Receiver<()>` should be cloned and passed to each
    /// service via [`Service::spawn`]. When a signal arrives, all receivers
    /// will fire, telling each service to begin its shutdown.
    pub fn new() -> (Self, watch::Receiver<()>) {
        let mut sigint = signal(SignalKind::interrupt()).unwrap();
        let mut sigterm = signal(SignalKind::terminate()).unwrap();

        let (tx, rx) = watch::channel(());

        let graceful_waiter = tokio::spawn(async move {
            tokio::select! {
                _ = sigint.recv() => {
                    tracing::debug!("graceful exit on SIGINT");
                }
                _ = sigterm.recv() => {
                    tokio::time::sleep(REQUEST_GRACE_PERIOD).await;
                    tracing::debug!("graceful shutdown with delay on SIGTERM");
                }
            }
            let _ = tx.send(());
        });

        let handle = Self {
            graceful_waiter,
            handles: Vec::new(),
        };
        (handle, rx)
    }

    /// Register a spawned service's join handle.
    ///
    /// All registered handles are awaited during [`wait`](ShutdownHandle::wait).
    pub fn push(&mut self, handle: JoinHandle<()>) {
        self.handles.push(handle);
    }

    /// Block until a shutdown signal arrives, then wait for all services to finish.
    ///
    /// If services don't exit within [`FINAL_SHUTDOWN_TIMEOUT`] (30s), the
    /// process is force-killed with exit code 4.
    pub async fn wait(self) {
        let _ = self.graceful_waiter.await;

        if tokio::time::timeout(FINAL_SHUTDOWN_TIMEOUT, join_all(self.handles))
            .await
            .is_err()
        {
            tracing::error!(
                "failed to shut down within {}s",
                FINAL_SHUTDOWN_TIMEOUT.as_secs()
            );
            std::process::exit(4);
        }
    }
}
