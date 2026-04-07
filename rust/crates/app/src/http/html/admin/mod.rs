mod actions;
mod views;

use axum::routing::{get, post};
use axum::Router;

use crate::state::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/_admin", get(views::dashboard::handler))
        .route("/_admin/", get(views::dashboard::handler))
        .route(
            "/_admin/users/{id}/promote",
            post(actions::promote::handler),
        )
        .route("/_admin/users/{id}/demote", post(actions::demote::handler))
}
