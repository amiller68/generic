use serde::{Deserialize, Serialize};
use struct_patch::Patch;
use uuid::Uuid;

use crate::database::types::DbUuid;
use crate::database::Database;

#[derive(Debug, Clone, Serialize, sqlx::FromRow, Patch)]
#[patch(attribute(derive(Debug, Default, Deserialize)))]
pub struct Widget {
    #[patch(skip)]
    id: DbUuid,
    name: String,
    description: String,
    status: String,
    #[patch(skip)]
    created_at: String,
    #[patch(skip)]
    updated_at: String,
    archived_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, sqlx::FromRow)]
pub struct WidgetListItem {
    id: DbUuid,
    name: String,
    description: String,
    status: String,
    created_at: String,
    updated_at: String,
    archived_at: Option<String>,
}

impl WidgetListItem {
    pub fn id(&self) -> Uuid {
        self.id.into()
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn description(&self) -> &str {
        &self.description
    }

    pub fn status(&self) -> &str {
        &self.status
    }

    pub fn created_at(&self) -> &str {
        &self.created_at
    }

    pub fn updated_at(&self) -> &str {
        &self.updated_at
    }

    pub fn archived_at(&self) -> Option<&str> {
        self.archived_at.as_deref()
    }

    pub fn is_archived(&self) -> bool {
        self.archived_at.is_some()
    }
}

impl Widget {
    pub fn id(&self) -> Uuid {
        self.id.into()
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn description(&self) -> &str {
        &self.description
    }

    pub fn status(&self) -> &str {
        &self.status
    }

    pub fn created_at(&self) -> &str {
        &self.created_at
    }

    pub fn updated_at(&self) -> &str {
        &self.updated_at
    }

    pub fn archived_at(&self) -> Option<&str> {
        self.archived_at.as_deref()
    }

    pub fn is_archived(&self) -> bool {
        self.archived_at.is_some()
    }

    pub async fn create(name: &str, description: &str, db: &Database) -> Result<Self, sqlx::Error> {
        let id = DbUuid::new();
        sqlx::query_as::<_, Widget>(
            r#"
            INSERT INTO widgets (id, name, description, status)
            VALUES (?, ?, ?, 'draft')
            RETURNING *
            "#,
        )
        .bind(id)
        .bind(name)
        .bind(description)
        .fetch_one(&**db)
        .await
    }

    pub async fn patch(mut self, patch: WidgetPatch, db: &Database) -> Result<Self, sqlx::Error> {
        self.apply(patch);
        sqlx::query_as::<_, Widget>(
            r#"
            UPDATE widgets SET name = ?, description = ?, status = ?, archived_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            RETURNING *
            "#,
        )
        .bind(&self.name)
        .bind(&self.description)
        .bind(&self.status)
        .bind(&self.archived_at)
        .bind(self.id)
        .fetch_one(&**db)
        .await
    }

    pub async fn find(id: Uuid, db: &Database) -> Result<Option<Self>, sqlx::Error> {
        let db_id = DbUuid::from(id);
        sqlx::query_as::<_, Widget>("SELECT * FROM widgets WHERE id = ?")
            .bind(db_id)
            .fetch_optional(&**db)
            .await
    }

    pub async fn find_by_name(name: &str, db: &Database) -> Result<Option<Self>, sqlx::Error> {
        sqlx::query_as::<_, Widget>("SELECT * FROM widgets WHERE name = ?")
            .bind(name)
            .fetch_optional(&**db)
            .await
    }

    pub async fn list(db: &Database) -> Result<Vec<WidgetListItem>, sqlx::Error> {
        sqlx::query_as::<_, WidgetListItem>(
            "SELECT * FROM widgets WHERE archived_at IS NULL ORDER BY created_at DESC",
        )
        .fetch_all(&**db)
        .await
    }
}
