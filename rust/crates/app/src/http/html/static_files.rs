use axum::response::IntoResponse;
use rust_embed::Embed;

#[derive(Embed)]
#[folder = "static/"]
struct StaticAssets;

pub async fn handler(axum::extract::Path(path): axum::extract::Path<String>) -> impl IntoResponse {
    match StaticAssets::get(&path) {
        Some(content) => {
            let mime = mime_guess::from_path(&path)
                .first_or_octet_stream()
                .to_string();
            (
                axum::http::StatusCode::OK,
                [(axum::http::header::CONTENT_TYPE, mime)],
                content.data.to_vec(),
            )
                .into_response()
        }
        None => axum::http::StatusCode::NOT_FOUND.into_response(),
    }
}
