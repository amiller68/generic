mod actions;
mod views;

use axum::routing::{get, post};
use axum::Router;

use crate::state::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(views::list::handler))
        .route(
            "/new",
            get(views::new::handler).post(actions::create::handler),
        )
        .route("/:id", get(views::show::handler))
        .route(
            "/:id/edit",
            get(views::edit::handler).post(actions::update::handler),
        )
        .route("/:id/process", post(actions::process::handler))
        .route("/:id/archive", post(actions::archive::handler))
}
