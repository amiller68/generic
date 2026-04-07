mod callback;
mod login;

use axum::routing::get;
use axum::Router;

use crate::state::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/login", get(login::handler))
        .route("/callback", get(callback::handler))
}
