CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_timestamp TEXT NOT NULL,
    raw_log TEXT NOT NULL,
    class TEXT NOT NULL DEFAULT 'unknown',
    confidence REAL NOT NULL DEFAULT 0.0,
    correlated_cause TEXT,
    report_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_incidents_incident_timestamp
    ON incidents (incident_timestamp);

CREATE INDEX IF NOT EXISTS idx_incidents_class
    ON incidents (class);
