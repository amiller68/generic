// TODO: add cleanup method to purge completed/failed jobs from the queue
pub mod widget;

use apalis::prelude::*;
use serde::{de::DeserializeOwned, Serialize};
use tokio::sync::watch;

use crate::database::Database;
use crate::events::EventBus;
use crate::runtime;
use crate::state::AppState;

pub use widget::ProcessWidgetTask;

/// Trait for self-registering background task types.
///
/// Each task type declares its own worker name, registration, and push logic.
/// The `TaskWorker` chains `T::register(monitor, ...)` for each task type,
/// and callers push via `TaskProducer::push(task)`.
///
/// Apalis stores all task types in the same Jobs table, distinguished by
/// `job_type` (the Rust type name). Each task type gets its own
/// `SqliteStorage<T>` and named worker — no additional migrations needed.
pub trait Task: Serialize + DeserializeOwned + Send + Sync + 'static {
    /// Worker name for logging/monitoring (e.g. "process-widget-worker").
    const WORKER_NAME: &'static str;

    /// Register this task's worker with the monitor.
    /// Each impl creates its own SqliteStorage and WorkerBuilder.
    fn register(monitor: Monitor, db: Database, events: EventBus) -> Monitor;

    /// Push this task onto the queue.
    fn push(
        self,
        db: &Database,
    ) -> impl std::future::Future<Output = Result<(), anyhow::Error>> + Send;
}

#[derive(Clone)]
pub struct TaskProducer {
    db: Database,
}

impl TaskProducer {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn push<T: Task>(&self, task: T) -> Result<(), anyhow::Error> {
        task.push(&self.db).await
    }
}

pub struct TaskWorker;

#[async_trait::async_trait]
impl runtime::Service for TaskWorker {
    type State = AppState;

    async fn run(state: Self::State, mut shutdown_rx: watch::Receiver<()>) {
        let db = state.database.clone();
        let events = state.events.clone();

        let monitor = Monitor::new();
        let monitor = ProcessWidgetTask::register(monitor, db, events);
        let monitor = monitor.on_event(|ctx, event| {
            tracing::debug!(worker = ctx.name(), ?event, "worker event");
        });

        tracing::info!("task workers started");

        tokio::select! {
            result = monitor.run() => {
                if let Err(e) = result {
                    tracing::error!("task monitor error: {e}");
                }
            }
            _ = shutdown_rx.changed() => {
                tracing::info!("shutting down task workers");
            }
        }
    }
}
