use apalis::prelude::*;
use apalis_sqlite::SqliteStorage;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::database::models::{Widget, WidgetPatch};
use crate::database::Database;
use crate::events::widget::WidgetEvent;
use crate::events::{AppEvent, Envelope, EventBus, Scope};
use crate::tasks::Task;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessWidgetTask {
    pub widget_id: Uuid,
}

impl Task for ProcessWidgetTask {
    const WORKER_NAME: &'static str = "process-widget-worker";

    fn register(monitor: Monitor, db: Database, events: EventBus) -> Monitor {
        let storage = SqliteStorage::<Self, (), ()>::new(&db);

        monitor.register(move |_| {
            WorkerBuilder::new(Self::WORKER_NAME)
                .backend(storage.clone())
                .data(db.clone())
                .data(events.clone())
                .build(handler)
        })
    }

    async fn push(self, db: &Database) -> Result<(), anyhow::Error> {
        let mut storage = SqliteStorage::<Self, (), ()>::new(db);
        storage
            .push(self)
            .await
            .map_err(|e| anyhow::anyhow!("failed to enqueue process task: {e}"))?;
        Ok(())
    }
}

pub async fn handler(
    task: ProcessWidgetTask,
    db: Data<Database>,
    events: Data<EventBus>,
) -> Result<(), BoxDynError> {
    let widget_id = task.widget_id;
    tracing::info!(%widget_id, "processing widget");

    let widget = match Widget::find(widget_id, &db).await {
        Ok(Some(w)) => w,
        Ok(None) => return Err(format!("widget {widget_id} not found").into()),
        Err(e) => return Err(e.into()),
    };

    match widget
        .patch(
            WidgetPatch {
                status: Some("processing".into()),
                ..Default::default()
            },
            &db,
        )
        .await
    {
        Ok(_) => {}
        Err(e) => {
            tracing::error!(%widget_id, error = %e, "failed to set processing status");
            return Err(e.into());
        }
    };

    events.publish(Envelope {
        scope: Scope::Broadcast,
        event: AppEvent::Widget(WidgetEvent::Processing {
            widget_id,
            progress: 0,
            message: "Starting processing...".into(),
        }),
    });

    for step in 1..=3 {
        tokio::time::sleep(std::time::Duration::from_millis(500)).await;
        let progress: u8 = (step * 33).min(99);
        events.publish(Envelope {
            scope: Scope::Broadcast,
            event: AppEvent::Widget(WidgetEvent::Processing {
                widget_id,
                progress,
                message: format!("Step {step}/3 complete"),
            }),
        });
    }

    // Re-fetch since widget was consumed by first patch
    let widget = match Widget::find(widget_id, &db).await {
        Ok(Some(w)) => w,
        Ok(None) => return Err(format!("widget {widget_id} not found").into()),
        Err(e) => return Err(e.into()),
    };

    if let Err(e) = widget
        .patch(
            WidgetPatch {
                status: Some("active".into()),
                ..Default::default()
            },
            &db,
        )
        .await
    {
        tracing::error!(%widget_id, error = %e, "failed to set active status");
        return Err(e.into());
    }

    events.publish(Envelope {
        scope: Scope::Broadcast,
        event: AppEvent::Widget(WidgetEvent::Processed { widget_id }),
    });

    tracing::info!(%widget_id, "widget processed");
    Ok(())
}
