use serde::Serialize;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type", content = "data")]
pub enum WidgetEvent {
    Processing {
        widget_id: Uuid,
        progress: u8,
        message: String,
    },
    Processed {
        widget_id: Uuid,
    },
    ProcessFailed {
        widget_id: Uuid,
        error: String,
    },
}
