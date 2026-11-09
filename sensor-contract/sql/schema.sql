-- SQLite persistence contract for validated APOLO observations.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sensor_observations (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL CHECK(length(trim(name)) > 0),
  value TEXT NOT NULL CHECK(length(trim(value)) > 0),
  origin TEXT NOT NULL CHECK(origin IN ('HOST_OS', 'PHYSICAL_INTERFACE')),
  source TEXT NOT NULL CHECK(length(trim(source)) > 0),
  observed_at_ms INTEGER NOT NULL CHECK(observed_at_ms > 0)
);
CREATE INDEX IF NOT EXISTS idx_sensor_observations_time
  ON sensor_observations(observed_at_ms);
