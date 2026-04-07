use std::time::Duration;

use sqlx::migrate::Migrator;
use sqlx::sqlite::{
    SqliteConnectOptions, SqliteJournalMode, SqlitePool, SqlitePoolOptions, SqliteSynchronous,
};
use sqlx::ConnectOptions;
use tracing::log::LevelFilter;
use url::Url;

use crate::database::DatabaseSetupError;

static MIGRATOR: Migrator = sqlx::migrate!("./migrations");

pub async fn connect(url: &Url) -> Result<SqlitePool, DatabaseSetupError> {
    let options = SqliteConnectOptions::from_url(url)
        .map_err(DatabaseSetupError::Unavailable)?
        .create_if_missing(true)
        .journal_mode(SqliteJournalMode::Wal)
        .synchronous(SqliteSynchronous::Normal)
        .log_statements(LevelFilter::Trace)
        .log_slow_statements(LevelFilter::Warn, Duration::from_millis(100))
        .statement_cache_capacity(2_500);

    SqlitePoolOptions::new()
        .min_connections(1)
        .max_connections(16)
        .idle_timeout(Duration::from_secs(90))
        .max_lifetime(Duration::from_secs(1_800))
        .connect_with(options)
        .await
        .map_err(DatabaseSetupError::Unavailable)
}

pub async fn migrate(pool: &SqlitePool) -> Result<(), DatabaseSetupError> {
    MIGRATOR
        .run(pool)
        .await
        .map_err(DatabaseSetupError::MigrationFailed)
}
