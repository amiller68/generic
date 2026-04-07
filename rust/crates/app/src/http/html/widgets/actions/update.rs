use axum::extract::{Path, State};
use axum::response::{IntoResponse, Redirect};
use axum::Form;
use serde::Deserialize;
use uuid::Uuid;

use crate::database::models::{Widget, WidgetPatch};
use crate::http::auth::RequireUser;
use crate::state::AppState;

#[derive(Deserialize)]
pub struct WidgetForm {
    name: String,
    description: String,
}

pub async fn handler(
    RequireUser(_user): RequireUser,
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    Form(form): Form<WidgetForm>,
) -> impl IntoResponse {
    if let Some(widget) = Widget::find(id, &state.database).await.ok().flatten() {
        let patch = WidgetPatch {
            name: Some(form.name),
            description: Some(form.description),
            ..Default::default()
        };
        let _ = widget.patch(patch, &state.database).await;
    }
    Redirect::to(&format!("/widgets/{id}"))
}
