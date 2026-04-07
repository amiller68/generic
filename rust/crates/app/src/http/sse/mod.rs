use std::convert::Infallible;

use crate::events::widget::WidgetEvent;
use crate::events::{AppEvent, Scope};
use crate::http::auth::RequireUser;
use crate::state::AppState;
use axum::extract::State;
use axum::response::sse::{Event, Sse};
use axum::routing::get;
use axum::Router;
use futures::stream::Stream;
use tokio_stream::wrappers::BroadcastStream;
use tokio_stream::StreamExt;

pub fn router() -> Router<AppState> {
    Router::new().route("/", get(events))
}

async fn events(
    RequireUser(user): RequireUser,
    State(state): State<AppState>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let rx = state.events.subscribe();
    let user_id = user.id();

    let stream = BroadcastStream::new(rx).filter_map(move |msg| {
        let envelope = msg.ok()?;

        match &envelope.scope {
            Scope::Broadcast => {}
            Scope::User(id) => {
                if user_id != *id {
                    return None;
                }
            }
        }

        let event_type = match &envelope.event {
            AppEvent::Widget(WidgetEvent::Processing { .. }) => "widget_processing",
            AppEvent::Widget(WidgetEvent::Processed { .. }) => "widget_processed",
            AppEvent::Widget(WidgetEvent::ProcessFailed { .. }) => "widget_process_failed",
        };
        let json = serde_json::to_string(&envelope.event).ok()?;
        Some(Ok(Event::default().event(event_type).data(json)))
    });

    Sse::new(stream).keep_alive(
        axum::response::sse::KeepAlive::new()
            .interval(std::time::Duration::from_secs(15))
            .text("ping"),
    )
}
