-- APALIS MIGRATION — DO NOT MODIFY (see 20220530084123_jobs_workers.sql)

ALTER TABLE Jobs RENAME COLUMN last_error TO last_result;
