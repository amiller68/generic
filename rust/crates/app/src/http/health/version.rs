use axum::response::{IntoResponse, Response};
use axum::Json;
use http::StatusCode;

#[tracing::instrument]
pub async fn handler() -> Response {
    (StatusCode::OK, Json(crate::version::Version::new())).into_response()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_handler_direct() {
        let response = handler().await;
        assert_eq!(response.status(), StatusCode::OK);
    }
}
