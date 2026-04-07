use askama::Template;
use axum::extract::State;
use axum::response::{Html, IntoResponse};

use crate::database::models::{Widget, WidgetListItem};
use crate::http::auth::RequireUser;
use crate::http::html::{is_htmx, wrap};
use crate::state::AppState;

#[derive(Template)]
#[template(path = "pages/widgets/list.html")]
struct WidgetListTemplate {
    widgets: Vec<WidgetListItem>,
}

pub async fn handler(
    RequireUser(user): RequireUser,
    State(state): State<AppState>,
    request: axum::http::Request<axum::body::Body>,
) -> impl IntoResponse {
    let widgets = Widget::list(&state.database).await.unwrap_or_default();
    let tmpl = WidgetListTemplate { widgets };
    let html = tmpl.render().unwrap_or_default();

    if is_htmx(&request) {
        return Html(html).into_response();
    }
    Html(wrap("Widgets", html, user.email(), user.is_admin())).into_response()
}
