"""SQLite persistence layer for Himage.

Image bytes remain on disk; SQLite stores projects, image metadata, edit
operations, export records, and reusable filter presets.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "himage.db"
SUPPORTED_FORMATS = {"jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"}

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS projects (
    project_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) BETWEEN 1 AND 120),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS images (
    image_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    format TEXT NOT NULL CHECK (lower(format) IN ('jpg','jpeg','png','webp','bmp','gif','tiff')),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes >= 0),
    imported_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS edit_history (
    operation_id INTEGER PRIMARY KEY,
    image_id INTEGER NOT NULL,
    operation TEXT NOT NULL CHECK (length(trim(operation)) > 0),
    parameters_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS export_history (
    export_id INTEGER PRIMARY KEY,
    image_id INTEGER NOT NULL,
    output_path TEXT NOT NULL,
    format TEXT NOT NULL,
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    exported_at TEXT NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE
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
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection with foreign-key enforcement enabled."""
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def delete_image_record(file_path, db_path=None) -> bool:
    path = Path(file_path).expanduser().resolve()
    initialize_database(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM images WHERE file_path = ?", (str(path),))
        return cursor.rowcount > 0

def initialize_database(db_path: str | Path | None = None) -> None:
    """Create all tables/indexes and the default project if absent."""
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
        now = _now()
        connection.execute(
            "INSERT OR IGNORE INTO projects(name, created_at, updated_at) VALUES (?, ?, ?)",
            ("Default Project", now, now),
        )


def create_project(name: str, db_path: str | Path | None = None) -> int:
    name = name.strip()
    if not name or len(name) > 120:
        raise ValueError("Project name must contain 1 to 120 characters.")
    initialize_database(db_path)
    now = _now()
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO projects(name, created_at, updated_at) VALUES (?, ?, ?)",
            (name, now, now),
        )
        return int(cursor.lastrowid)


def get_default_project_id(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT project_id FROM projects WHERE name = ?", ("Default Project",)
    ).fetchone()
    if row is None:
        now = _now()
        cursor = connection.execute(
            "INSERT INTO projects(name, created_at, updated_at) VALUES (?, ?, ?)",
            ("Default Project", now, now),
        )
        return int(cursor.lastrowid)
    return int(row["project_id"])


def register_image(file_path: str | Path, width: int, height: int,
                   project_id: int | None = None,
                   db_path: str | Path | None = None) -> int:
    """Insert/update an image record and return its image_id."""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Image file does not exist: {path}")
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive.")
    fmt = path.suffix.lower().lstrip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {fmt or '(none)'}")
    initialize_database(db_path)
    now = _now()
    with connect(db_path) as connection:
        if project_id is None:
            project_id = get_default_project_id(connection)
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE project_id = ?", (now, project_id)
        )
        connection.execute(
            """INSERT INTO images
               (project_id, file_path, filename, format, width, height, file_size_bytes, imported_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(file_path) DO UPDATE SET
                 project_id=excluded.project_id, filename=excluded.filename,
                 format=excluded.format, width=excluded.width, height=excluded.height,
                 file_size_bytes=excluded.file_size_bytes""",
            (project_id, str(path), path.name, fmt, width, height, path.stat().st_size, now),
        )
        row = connection.execute("SELECT image_id FROM images WHERE file_path = ?", (str(path),)).fetchone()
        return int(row["image_id"])


def record_edit(image_id: int, operation: str, parameters: dict[str, Any] | None = None,
                db_path: str | Path | None = None) -> int:
    if not operation.strip():
        raise ValueError("Operation name cannot be empty.")
    initialize_database(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO edit_history(image_id, operation, parameters_json, created_at) VALUES (?, ?, ?, ?)",
            (image_id, operation.strip(), json.dumps(parameters or {}, sort_keys=True), _now()),
        )
        return int(cursor.lastrowid)


def record_export(image_id: int, output_path: str | Path, width: int, height: int,
                  db_path: str | Path | None = None) -> int:
    path = Path(output_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Export file does not exist: {path}")
    if width <= 0 or height <= 0:
        raise ValueError("Export dimensions must be positive.")
    initialize_database(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO export_history(image_id, output_path, format, width, height, exported_at) VALUES (?, ?, ?, ?, ?, ?)",
            (image_id, str(path), path.suffix.lower().lstrip("."), width, height, _now()),
        )
        return int(cursor.lastrowid)


def list_images(project_name: str | None = None, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize_database(db_path)
    query = """SELECT i.*, p.name AS project_name FROM images i
               JOIN projects p ON p.project_id = i.project_id"""
    params: tuple[Any, ...] = ()
    if project_name is not None:
        query += " WHERE p.name = ?"
        params = (project_name,)
    query += " ORDER BY i.imported_at DESC, i.image_id DESC"
    with connect(db_path) as connection:
        return [dict(row) for row in connection.execute(query, params).fetchall()]


def get_edit_history(image_id: int, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with connect(db_path) as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM edit_history WHERE image_id = ? ORDER BY operation_id", (image_id,)
        ).fetchall()]


def save_preset(name: str, operation: str, parameters: dict[str, Any],
                db_path: str | Path | None = None) -> int:
    name, operation = name.strip(), operation.strip()
    if not name or len(name) > 100 or not operation:
        raise ValueError("Preset name and operation must be valid.")
    initialize_database(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO filter_presets(name, operation, parameters_json, created_at) VALUES (?, ?, ?, ?)",
            (name, operation, json.dumps(parameters, sort_keys=True), _now()),
        )
        return int(cursor.lastrowid)
