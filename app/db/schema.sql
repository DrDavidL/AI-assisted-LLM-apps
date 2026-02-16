CREATE TABLE IF NOT EXISTS cases (
    case_id     UUID PRIMARY KEY,
    case_title  TEXT NOT NULL DEFAULT '',
    specialty   TEXT NOT NULL DEFAULT 'general',
    difficulty  TEXT NOT NULL DEFAULT 'medium',
    case_data   JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cases_specialty ON cases (specialty);
CREATE INDEX IF NOT EXISTS idx_cases_difficulty ON cases (difficulty);
CREATE INDEX IF NOT EXISTS idx_cases_data_gin ON cases USING GIN (case_data);
