use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;

#[tracing::instrument]
pub async fn handler() -> Response {
    let msg = serde_json::json!({"status": "ok"});
    (StatusCode::OK, Json(msg)).into_response()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_handler_direct() {
        let response = handler().await;
        assert_eq!(response.status(), StatusCode::OK);

        let body = axum::body::to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap();

        assert_eq!(&body[..], b"{\"status\":\"ok\"}");
    }
}
