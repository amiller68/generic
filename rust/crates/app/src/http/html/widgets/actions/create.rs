use axum::extract::State;
use axum::response::{IntoResponse, Redirect};
use axum::Form;
use serde::Deserialize;

use crate::database::models::Widget;
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
    Form(form): Form<WidgetForm>,
) -> impl IntoResponse {
    let _ = Widget::create(&form.name, &form.description, &state.database).await;
    Redirect::to("/widgets")
}
