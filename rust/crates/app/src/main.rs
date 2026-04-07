use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{EnvFilter, Layer};

use generic_rust_app::config::Config;
use generic_rust_app::http::HttpServer;
use generic_rust_app::runtime::{Service, ShutdownHandle};
use generic_rust_app::state::AppState;
use generic_rust_app::tasks::TaskWorker;

fn init_logging(log_level: tracing::Level) -> Vec<tracing_appender::non_blocking::WorkerGuard> {
    let mut guards = Vec::new();

    let (stdout_writer, stdout_guard) = tracing_appender::non_blocking(std::io::stdout());
    guards.push(stdout_guard);

    let stdout_filter = EnvFilter::builder()
        .with_default_directive(log_level.into())
        .from_env_lossy();

    let stdout_layer = tracing_subscriber::fmt::layer()
        .compact()
        .with_writer(stdout_writer)
        .with_filter(stdout_filter);

    tracing_subscriber::registry().with(stdout_layer).init();

    std::panic::set_hook(Box::new(|panic| match panic.location() {
        Some(loc) => {
            tracing::error!(
                message = %panic,
                panic.file = loc.file(),
                panic.line = loc.line(),
                panic.column = loc.column(),
            );
        }
        None => tracing::error!(message = %panic),
    }));

    guards
}

#[tokio::main]
async fn main() {
    let config = match Config::from_env() {
        Ok(config) => config,
        Err(e) => {
            eprintln!("Error loading configuration: {e}");
            std::process::exit(1);
        }
    };

    let _guards = init_logging(config.log_level);

    let state = match AppState::from_config(&config).await {
        Ok(s) => s,
        Err(e) => {
            tracing::error!("failed to create app state: {e}");
            std::process::exit(3);
        }
    };

    let (mut handle, shutdown_rx) = ShutdownHandle::new();

    handle.push(HttpServer::spawn(state.clone(), shutdown_rx.clone()));
    handle.push(TaskWorker::spawn(state.clone(), shutdown_rx.clone()));

    handle.wait().await;
}
