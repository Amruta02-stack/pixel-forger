# Himage DBMS Design (Version 1)

## Scope
SQLite stores structured records and relationships. Image bytes stay in the filesystem so database rows remain small and images can be opened by standard tools.

## Entities and relationships

```text
PROJECTS (1) -------- (many) IMAGES
IMAGES    (1) -------- (many) EDIT_HISTORY
IMAGES    (1) -------- (many) EXPORT_HISTORY
FILTER_PRESETS is a reusable catalog of named operations and JSON parameters.
```

### Tables

| Table | Primary key | Important columns / rules |
|---|---|---|
| `projects` | `project_id` | Unique non-empty name; created/updated timestamps |
| `images` | `image_id` | `project_id` FK; unique canonical file path; supported format; positive dimensions; non-negative byte size |
| `edit_history` | `operation_id` | `image_id` FK; operation; JSON parameters; timestamp |
| `export_history` | `export_id` | `image_id` FK; output path, format, dimensions, export timestamp |
| `filter_presets` | `preset_id` | Unique name; operation; JSON parameters; created timestamp |

## DBMS concepts demonstrated

- **Primary keys:** uniquely identify each row and provide stable references.
- **Foreign keys:** prevent edit/export rows from referring to an image that does not exist.
- **Referential integrity:** deleting an image cascades to its edit/export records; deleting a project cascades to its images.
- **Constraints:** `NOT NULL`, `UNIQUE`, `CHECK`, and foreign-key rules reject invalid records.
- **Normalization:** project data is stored separately from image data; edit and export events are separate one-to-many records instead of repeating them in an image row.
- **Indexes:** foreign-key and history lookup columns are indexed to support common queries.
- **Parameterized SQL:** values are passed separately from SQL text, avoiding SQL injection through user-provided values.
- **Transactions:** SQLite connection context managers commit successful statements and roll back on exceptions.
- **JSON parameters:** variable operation settings are stored as JSON text because different filters need different parameters. Stable, frequently queried fields remain normal columns.

## Example queries for the presentation

### 1. List images and their project names (JOIN)

```sql
SELECT i.filename, i.width, i.height, p.name AS project_name
FROM images AS i
JOIN projects AS p ON p.project_id = i.project_id
ORDER BY i.imported_at DESC;
```

### 2. Count images in each project (LEFT JOIN + GROUP BY)

```sql
SELECT p.name, COUNT(i.image_id) AS image_count
FROM projects AS p
LEFT JOIN images AS i ON i.project_id = p.project_id
GROUP BY p.project_id, p.name;
```

### 3. Count exports per image

```sql
SELECT i.filename, COUNT(e.export_id) AS export_count
FROM images AS i
LEFT JOIN export_history AS e ON e.image_id = i.image_id
GROUP BY i.image_id, i.filename;
```

### 4. Show edit history for one image

```sql
SELECT operation, parameters_json, created_at
FROM edit_history
WHERE image_id = ?
ORDER BY operation_id;
```

The `?` is a parameter placeholder. The application supplies the value separately.

## Current implementation boundary

Image metadata and export records are currently connected to the save workflow. The schema and API for edit history and filter presets exist, but those features are not yet wired into every editing menu. Project management screens and durable session restoration are also future work. State this boundary accurately during the viva.
