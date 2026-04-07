use axum::extract::{Path, State};
use axum::response::IntoResponse;
use uuid::Uuid;

use crate::http::auth::RequireUser;
use crate::state::AppState;
use crate::tasks::ProcessWidgetTask;

pub async fn handler(
    RequireUser(_user): RequireUser,
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    let task = ProcessWidgetTask { widget_id: id };
    if let Err(e) = state.tasks.push(task).await {
        tracing::error!(widget_id = %id, "failed to enqueue process task: {e}");
    }
    axum::http::StatusCode::ACCEPTED
}
