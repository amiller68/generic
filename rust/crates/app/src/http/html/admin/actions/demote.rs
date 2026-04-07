use axum::extract::{Path, State};
use axum::response::{IntoResponse, Redirect};
use uuid::Uuid;

use crate::database::models::{User, UserPatch};
use crate::http::auth::RequireAdmin;
use crate::state::AppState;

pub async fn handler(
    RequireAdmin(admin): RequireAdmin,
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    if admin.id() == id {
        return Redirect::to("/_admin/").into_response();
    }
    if let Some(user) = User::find_by_id(id, &state.database).await.ok().flatten() {
        let patch = UserPatch {
            is_admin: Some(false),
            ..Default::default()
        };
        let _ = user.patch(patch, &state.database).await;
        tracing::info!(admin = admin.email(), target = %id, "demoted user from admin");
    }
    Redirect::to("/_admin/").into_response()
}
