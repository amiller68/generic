mod google;
mod logout;

use axum::async_trait;
use axum::extract::FromRequestParts;
use axum::http::request::Parts;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Redirect};
use axum::routing::get;
use axum::Router;
use jsonwebtoken::{decode, DecodingKey, Validation};
use serde::{Deserialize, Serialize};

use crate::database::models::User;
use crate::database::Database;
use crate::state::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .nest("/google", google::router())
        .route("/logout", get(logout::handler))
}

/// JWT claims stored in the session cookie.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub email: String,
    pub name: String,
    pub exp: usize,
}

/// Extractor: optional logged-in user from DB.
pub struct OptionalUser(pub Option<User>);

/// Extractor: requires a logged-in user. Redirects to login if missing.
pub struct RequireUser(pub User);

/// Extractor: requires a logged-in admin user. Returns 403 if not admin.
pub struct RequireAdmin(pub User);

#[async_trait]
impl FromRequestParts<crate::state::AppState> for OptionalUser {
    type Rejection = StatusCode;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &crate::state::AppState,
    ) -> Result<Self, Self::Rejection> {
        let user = resolve_user(parts, &state.database, &state.service_secret).await;
        Ok(OptionalUser(user))
    }
}

#[async_trait]
impl FromRequestParts<crate::state::AppState> for RequireUser {
    type Rejection = axum::response::Response;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &crate::state::AppState,
    ) -> Result<Self, Self::Rejection> {
        match resolve_user(parts, &state.database, &state.service_secret).await {
            Some(user) => Ok(RequireUser(user)),
            None => Err(Redirect::to("/auth/google/login").into_response()),
        }
    }
}

#[async_trait]
impl FromRequestParts<crate::state::AppState> for RequireAdmin {
    type Rejection = axum::response::Response;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &crate::state::AppState,
    ) -> Result<Self, Self::Rejection> {
        match resolve_user(parts, &state.database, &state.service_secret).await {
            Some(user) if user.is_admin() => Ok(RequireAdmin(user)),
            Some(_) => Err(StatusCode::FORBIDDEN.into_response()),
            None => Err(Redirect::to("/auth/google/login").into_response()),
        }
    }
}

/// Decode the session JWT, then look up the user in the database.
async fn resolve_user(parts: &Parts, db: &Database, secret: &str) -> Option<User> {
    let claims = extract_claims(parts, secret);
    if claims.is_none() {
        tracing::debug!("no valid session claims found");
        return None;
    }
    let claims = claims.unwrap();
    let user = User::find_by_email(&claims.email, db).await.ok().flatten();
    if user.is_none() {
        tracing::warn!(
            email = claims.email,
            "session valid but user not found in DB"
        );
    }
    user
}

fn extract_claims(parts: &Parts, secret: &str) -> Option<Claims> {
    let cookie_header = parts.headers.get("cookie")?.to_str().ok()?;

    let session_value = cookie_header
        .split(';')
        .filter_map(|c| {
            let mut parts = c.trim().splitn(2, '=');
            let name = parts.next()?.trim();
            let value = parts.next()?.trim();
            if name == "session" {
                Some(value.to_string())
            } else {
                None
            }
        })
        .next()?;

    if secret.is_empty() {
        return None;
    }

    let token_data = decode::<Claims>(
        &session_value,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::new(jsonwebtoken::Algorithm::HS256),
    )
    .ok()?;

    Some(token_data.claims)
}
