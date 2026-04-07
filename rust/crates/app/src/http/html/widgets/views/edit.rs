use askama::Template;
use axum::extract::{Path, State};
use axum::response::{Html, IntoResponse, Redirect};
use uuid::Uuid;

use crate::database::models::Widget;
use crate::http::auth::RequireUser;
use crate::http::html::{is_htmx, wrap};
use crate::state::AppState;

#[derive(Template)]
#[template(path = "pages/widgets/form.html")]
struct WidgetFormTemplate {
    widget: Option<Widget>,
}

pub async fn handler(
    RequireUser(user): RequireUser,
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    request: axum::http::Request<axum::body::Body>,
) -> impl IntoResponse {
    match Widget::find(id, &state.database).await {
        Ok(Some(widget)) => {
            let tmpl = WidgetFormTemplate {
                widget: Some(widget),
            };
            let html = tmpl.render().unwrap_or_default();

            if is_htmx(&request) {
                return Html(html).into_response();
            }
            Html(wrap("Edit Widget", html, user.email(), user.is_admin())).into_response()
        }
        _ => Redirect::to("/widgets").into_response(),
    }
}
