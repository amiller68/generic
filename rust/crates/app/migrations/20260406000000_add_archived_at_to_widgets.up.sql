ALTER TABLE widgets ADD COLUMN archived_at TEXT;
CREATE INDEX idx_widgets_archived_at ON widgets (archived_at);
