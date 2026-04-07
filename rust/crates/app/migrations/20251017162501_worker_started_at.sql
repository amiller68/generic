-- APALIS MIGRATION — DO NOT MODIFY (see 20220530084123_jobs_workers.sql)

ALTER TABLE
    Workers
ADD
    COLUMN started_at INTEGER;
