use axum::extract::{Query, State};
use axum::response::{IntoResponse, Redirect};
use jsonwebtoken::{encode, DecodingKey, EncodingKey, Header};
use serde::Deserialize;

use crate::database::models::User;
use crate::http::auth::Claims;
use crate::state::AppState;

#[derive(Deserialize)]
pub struct CallbackQuery {
    code: String,
}

#[derive(Deserialize)]
struct TokenResponse {
    id_token: String,
}

#[derive(Deserialize)]
struct GoogleUserInfo {
    sub: String,
    email: String,
    name: Option<String>,
}

/// Google redirects here with an authorization code.
/// Exchange it for tokens, extract user info, find or create user, set session cookie.
pub async fn handler(
    State(state): State<AppState>,
    Query(query): Query<CallbackQuery>,
) -> impl IntoResponse {
    let redirect_uri = format!("{}/auth/google/callback", state.host_name);

    // Exchange code for tokens
    let client = reqwest::Client::new();
    let token_res = client
        .post("https://oauth2.googleapis.com/token")
        .form(&[
            ("code", query.code.as_str()),
            ("client_id", &state.google_client_id),
            ("client_secret", &state.google_client_secret),
            ("redirect_uri", &redirect_uri),
            ("grant_type", "authorization_code"),
        ])
        .send()
        .await;

    let token_res = match token_res {
        Ok(r) => r,
        Err(e) => {
            tracing::error!("token exchange failed: {e}");
            return Redirect::to("/").into_response();
        }
    };

    let tokens: TokenResponse = match token_res.json().await {
        Ok(t) => t,
        Err(e) => {
            tracing::error!("failed to parse token response: {e}");
            return Redirect::to("/").into_response();
        }
    };

    // Decode the ID token (we trust Google's signature in this simple flow)
    let mut validation = jsonwebtoken::Validation::new(jsonwebtoken::Algorithm::RS256);
    validation.insecure_disable_signature_validation();
    validation.set_audience(&[&state.google_client_id]);
    validation.set_issuer(&["https://accounts.google.com", "accounts.google.com"]);

    let user_info: GoogleUserInfo = match jsonwebtoken::decode::<GoogleUserInfo>(
        &tokens.id_token,
        &DecodingKey::from_secret(&[]),
        &validation,
    ) {
        Ok(data) => data.claims,
        Err(e) => {
            tracing::error!("failed to decode id_token: {e}");
            return Redirect::to("/").into_response();
        }
    };

    // Find or create user
    let name = user_info.name.unwrap_or_default();
    if User::find_by_email(&user_info.email, &state.database)
        .await
        .ok()
        .flatten()
        .is_none()
    {
        if let Err(e) = User::create(&user_info.email, &name, &state.database).await {
            tracing::error!("failed to create user: {e}");
        }
    }

    // Create our session JWT
    let exp = chrono::Utc::now() + chrono::Duration::hours(24);
    let claims = Claims {
        sub: user_info.sub,
        email: user_info.email,
        name,
        exp: exp.timestamp() as usize,
    };

    let token = match encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.service_secret.as_bytes()),
    ) {
        Ok(t) => t,
        Err(e) => {
            tracing::error!("failed to create session token: {e}");
            return Redirect::to("/").into_response();
        }
    };

    // Set cookie and redirect
    let cookie = format!("session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400");

    (
        [(axum::http::header::SET_COOKIE, cookie)],
        Redirect::to("/widgets"),
    )
        .into_response()
}
