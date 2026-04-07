use askama::Template;
use axum::response::{Html, IntoResponse};

use crate::database::models::Widget;
use crate::http::auth::RequireUser;
use crate::http::html::{is_htmx, wrap};

#[derive(Template)]
#[template(path = "pages/widgets/form.html")]
struct WidgetFormTemplate {
    widget: Option<Widget>,
}

pub async fn handler(
    RequireUser(user): RequireUser,
    request: axum::http::Request<axum::body::Body>,
) -> impl IntoResponse {
    let tmpl = WidgetFormTemplate { widget: None };
    let html = tmpl.render().unwrap_or_default();

    if is_htmx(&request) {
        return Html(html).into_response();
    }
    Html(wrap("New Widget", html, user.email(), user.is_admin())).into_response()
}
