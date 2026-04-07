use axum::response::{IntoResponse, Redirect};

pub async fn handler() -> impl IntoResponse {
    let cookie = "session=; Path=/; HttpOnly; Max-Age=0";
    (
        [(axum::http::header::SET_COOKIE, cookie.to_string())],
        Redirect::to("/"),
    )
}
