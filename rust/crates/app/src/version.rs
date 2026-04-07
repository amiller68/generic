use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct Version {
    pub version: &'static str,
    pub build_profile: &'static str,
    pub build_timestamp: &'static str,
}

impl Version {
    pub fn new() -> Self {
        Self {
            version: env!("REPO_VERSION"),
            build_profile: env!("BUILD_PROFILE"),
            build_timestamp: env!("BUILD_TIMESTAMP"),
        }
    }
}
