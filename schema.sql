Image relational schema. The canonical schema is also embedded in database.py.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS projects (
  project_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) BETWEEN 1 AND 120),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS images (
  image_id INTEGER PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  file_path TEXT NOT NULL UNIQUE,
  filename TEXT NOT NULL,
  format TEXT NOT NULL CHECK (lower(format) IN ('jpg','jpeg','png','webp','bmp','gif','tiff')),
  width INTEGER NOT NULL CHECK (width > 0),
  height INTEGER NOT NULL CHECK (height > 0),
  file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes >= 0),
  imported_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edit_history (
  operation_id INTEGER PRIMARY KEY,
  image_id INTEGER NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
  operation TEXT NOT NULL CHECK (length(trim(operation)) > 0),
  parameters_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS export_history (
  export_id INTEGER PRIMARY KEY,
  image_id INTEGER NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
  output_path TEXT NOT NULL,
  format TEXT NOT NULL,
  width INTEGER NOT NULL CHECK (width > 0),
  height INTEGER NOT NULL CHECK (height > 0),
  exported_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS filter_presets (
  preset_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) BETWEEN 1 AND 100),
  operation TEXT NOT NULL CHECK (length(trim(operation)) > 0),
  parameters_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_images_project_id ON images(project_id);
CREATE INDEX IF NOT EXISTS idx_edit_history_image_time ON edit_history(image_id, created_at);
CREATE INDEX IF NOT EXISTS idx_export_history_image_time ON export_history(image_id, exported_at);
