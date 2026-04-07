use axum::extract::{Path, State};
use axum::response::{IntoResponse, Redirect};
use uuid::Uuid;

use crate::database::models::{Widget, WidgetPatch};
use crate::http::auth::RequireUser;
use crate::state::AppState;

pub async fn handler(
    RequireUser(_user): RequireUser,
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    if let Some(widget) = Widget::find(id, &state.database).await.ok().flatten() {
        let now = chrono::Utc::now().to_rfc3339();
        let patch = WidgetPatch {
            archived_at: Some(Some(now)),
            ..Default::default()
        };
        let _ = widget.patch(patch, &state.database).await;
    }
    Redirect::to("/widgets")
}
