use axum::extract::State;
use axum::response::{IntoResponse, Redirect};

use crate::state::AppState;

/// Redirect the user to Google's OAuth consent screen.
pub async fn handler(State(state): State<AppState>) -> impl IntoResponse {
    let redirect_uri = format!("{}/auth/google/callback", state.host_name);

    let url = format!(
        "https://accounts.google.com/o/oauth2/v2/auth?\
         client_id={}&\
         redirect_uri={}&\
         response_type=code&\
         scope=openid%20email%20profile&\
         access_type=offline",
        state.google_client_id,
        urlencoding::encode(&redirect_uri),
    );

    Redirect::temporary(&url)
}
