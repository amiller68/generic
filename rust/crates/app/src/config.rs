use std::net::SocketAddr;

use url::Url;

#[derive(Debug)]
pub struct Config {
    pub listen_address: SocketAddr,
    pub sqlite_database_url: Url,
    pub log_level: tracing::Level,
    pub host_name: String,
    pub google_client_id: String,
    pub google_client_secret: String,
    pub service_secret: String,
}

#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("invalid listen address: {0}")]
    InvalidAddress(#[from] std::net::AddrParseError),
    #[error("invalid database url: {0}")]
    InvalidDatabaseUrl(#[from] url::ParseError),
    #[error("missing required env var: {0}")]
    MissingEnv(String),
}

impl Config {
    pub fn from_env() -> Result<Self, ConfigError> {
        let listen_address: SocketAddr = std::env::var("LISTEN_ADDRESS")
            .unwrap_or_else(|_| "127.0.0.1:9000".to_string())
            .parse()?;

        let sqlite_database_url = Url::parse(
            &std::env::var("SQLITE_DATABASE_URL")
                .unwrap_or_else(|_| "sqlite://data/app.db".to_string()),
        )?;

        let log_level = std::env::var("LOG_LEVEL")
            .unwrap_or_else(|_| "info".to_string())
            .parse()
            .unwrap_or(tracing::Level::INFO);

        let host_name =
            std::env::var("HOST_NAME").unwrap_or_else(|_| format!("http://{listen_address}"));

        let google_client_id = std::env::var("GOOGLE_O_AUTH_CLIENT_ID")
            .map_err(|_| ConfigError::MissingEnv("GOOGLE_O_AUTH_CLIENT_ID".into()))?;

        let google_client_secret = std::env::var("GOOGLE_O_AUTH_CLIENT_SECRET")
            .map_err(|_| ConfigError::MissingEnv("GOOGLE_O_AUTH_CLIENT_SECRET".into()))?;

        let service_secret = std::env::var("SERVICE_SECRET").unwrap_or_else(|_| {
            use rand::Rng;
            let secret: String = rand::rng()
                .sample_iter(&rand::distr::Alphanumeric)
                .take(64)
                .map(char::from)
                .collect();
            tracing::info!("No SERVICE_SECRET set, generated random secret");
            secret
        });

        Ok(Self {
            listen_address,
            sqlite_database_url,
            log_level,
            host_name,
            google_client_id,
            google_client_secret,
            service_secret,
        })
    }
}
