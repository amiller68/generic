use askama::Template;
use axum::response::Html;

#[derive(Template)]
#[template(path = "pages/login.html")]
struct LoginTemplate {}

pub async fn handler() -> Html<String> {
    let tmpl = LoginTemplate {};
    Html(tmpl.render().unwrap_or_default())
}
