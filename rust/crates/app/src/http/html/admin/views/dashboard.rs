use askama::Template;
use axum::extract::State;
use axum::response::{Html, IntoResponse};

use crate::database::models::{User, UserListItem, Widget};
use crate::http::auth::RequireAdmin;
use crate::http::html::{is_htmx, wrap};
use crate::state::AppState;

#[derive(Template)]
#[template(path = "pages/admin/dashboard.html")]
struct AdminDashboardTemplate {
    users: Vec<UserListItem>,
    user_count: i64,
    widget_count: i64,
    active_widget_count: i64,
    current_user_id: String,
}

pub async fn handler(
    RequireAdmin(user): RequireAdmin,
    State(state): State<AppState>,
    request: axum::http::Request<axum::body::Body>,
) -> impl IntoResponse {
    let users = User::list(&state.database).await.unwrap_or_default();
    let user_count = User::count(&state.database).await.unwrap_or(0);
    let all_widgets = Widget::list(&state.database).await.unwrap_or_default();
    let widget_count = all_widgets.len() as i64;
    let active_widget_count = all_widgets
        .iter()
        .filter(|w| w.status() == "active")
        .count() as i64;

    let tmpl = AdminDashboardTemplate {
        users,
        user_count,
        widget_count,
        active_widget_count,
        current_user_id: user.id().to_string(),
    };
    let html = tmpl.render().unwrap_or_default();

    if is_htmx(&request) {
        return Html(html).into_response();
    }
    Html(wrap("Admin", html, user.email(), user.is_admin())).into_response()
}
