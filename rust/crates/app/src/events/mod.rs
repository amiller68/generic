pub mod widget;

use serde::Serialize;
use tokio::sync::broadcast;
use uuid::Uuid;

use widget::WidgetEvent;

#[derive(Debug, Clone)]
pub enum Scope {
    User(Uuid),
    Broadcast,
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "domain", content = "event")]
pub enum AppEvent {
    Widget(WidgetEvent),
}

#[derive(Debug, Clone)]
pub struct Envelope {
    pub scope: Scope,
    pub event: AppEvent,
}

#[derive(Clone)]
pub struct EventBus {
    tx: broadcast::Sender<Envelope>,
}

impl EventBus {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = broadcast::channel(capacity);
        Self { tx }
    }

    pub fn publish(&self, envelope: Envelope) {
        let _ = self.tx.send(envelope);
    }

    pub fn subscribe(&self) -> broadcast::Receiver<Envelope> {
        self.tx.subscribe()
    }
}
