mod admin;
mod index;
mod login;
mod static_files;
mod widgets;

use askama::Template;
use axum::routing::get;
use axum::Router;

use crate::state::AppState;

pub fn router(state: AppState) -> Router<AppState> {
    Router::new()
        .route("/", get(index::handler))
        .route("/login", get(login::handler))
        .route("/static/*path", get(static_files::handler))
        .nest("/widgets", widgets::router())
        .merge(admin::router())
        .with_state(state)
}

#[derive(Template)]
#[template(path = "layouts/wrapper.html")]
struct AppLayout {
    title: String,
    content: String,
    user_email: String,
    is_admin: bool,
}

pub(crate) fn wrap(title: &str, content: String, email: &str, is_admin: bool) -> String {
    let layout = AppLayout {
        title: title.to_string(),
        content,
        user_email: email.to_string(),
        is_admin,
    };
    layout.render().unwrap_or_default()
}

pub(crate) fn is_htmx(request: &axum::http::Request<axum::body::Body>) -> bool {
    request.headers().get("HX-Request").is_some()
}
