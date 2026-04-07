use askama::Template;
use axum::response::Html;

use crate::http::auth::OptionalUser;

#[derive(Template)]
#[template(path = "pages/index.html")]
struct IndexTemplate {
    user_name: Option<String>,
}

pub async fn handler(OptionalUser(user): OptionalUser) -> Html<String> {
    let tmpl = IndexTemplate {
        user_name: user.map(|u| u.name().to_string()),
    };
    Html(tmpl.render().unwrap_or_default())
}
