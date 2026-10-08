"""Tests for Himage's SQLite data layer."""
import sqlite3

import pytest
from PIL import Image

import database


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test_himage.db"
    database.initialize_database(path)
    return path


def make_image(path, size=(8, 6), color=(20, 40, 60)):
    Image.new("RGB", size, color).save(path)
    return path


def test_initialization_creates_schema_and_default_project(db_path):
    with database.connect(db_path) as connection:
        names = {row["name"] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"projects", "images", "edit_history", "export_history", "filter_presets"} <= names


def test_register_image_persists_metadata(db_path, tmp_path):
    image_path = make_image(tmp_path / "sample.png")
    image_id = database.register_image(image_path, 8, 6, db_path=db_path)
    records = database.list_images(db_path=db_path)
    assert len(records) == 1
    assert records[0]["image_id"] == image_id
    assert records[0]["filename"] == "sample.png"
    assert records[0]["width"] == 8 and records[0]["height"] == 6
    assert records[0]["project_name"] == "Default Project"


def test_registering_same_path_updates_existing_record(db_path, tmp_path):
    image_path = make_image(tmp_path / "same.png", (8, 6))
    first_id = database.register_image(image_path, 8, 6, db_path=db_path)
    Image.new("RGB", (12, 10)).save(image_path)
    second_id = database.register_image(image_path, 12, 10, db_path=db_path)
    assert first_id == second_id
    assert len(database.list_images(db_path=db_path)) == 1
    assert database.list_images(db_path=db_path)[0]["width"] == 12


def test_foreign_key_prevents_orphan_edit(db_path):
    with pytest.raises(sqlite3.IntegrityError):
        database.record_edit(9999, "Grayscale", db_path=db_path)


def test_edit_history_stores_parameters(db_path, tmp_path):
    path = make_image(tmp_path / "history.jpg")
    image_id = database.register_image(path, 8, 6, db_path=db_path)
    database.record_edit(image_id, "Rotate", {"degrees": 90}, db_path=db_path)
    rows = database.get_edit_history(image_id, db_path=db_path)
    assert rows[0]["operation"] == "Rotate"
    assert rows[0]["parameters_json"] == '{"degrees": 90}'


def test_export_history_records_successful_export(db_path, tmp_path):
    path = make_image(tmp_path / "export.jpg")
    image_id = database.register_image(path, 8, 6, db_path=db_path)
    export_id = database.record_export(image_id, path, 8, 6, db_path=db_path)
    with database.connect(db_path) as connection:
        row = connection.execute("SELECT * FROM export_history WHERE export_id=?", (export_id,)).fetchone()
    assert row["format"] == "jpg"
    assert row["width"] == 8


def test_duplicate_preset_name_is_rejected(db_path):
    database.save_preset("Warm", "Sepia", {"strength": 1}, db_path=db_path)
    with pytest.raises(sqlite3.IntegrityError):
        database.save_preset("Warm", "Sepia", {"strength": 0.5}, db_path=db_path)


def test_invalid_dimensions_are_rejected(db_path, tmp_path):
    path = make_image(tmp_path / "bad.png")
    with pytest.raises(ValueError):
        database.register_image(path, 0, 6, db_path=db_path)


def test_project_names_are_validated(db_path):
    with pytest.raises(ValueError):
        database.create_project("   ", db_path=db_path)
    assert database.create_project("Coursework", db_path=db_path) > 0


def test_delete_image_cascades_to_history(db_path, tmp_path):
    path = make_image(tmp_path / "delete.png")
    image_id = database.register_image(path, 8, 6, db_path=db_path)
    database.record_edit(image_id, "Grayscale", db_path=db_path)
    with database.connect(db_path) as connection:
        connection.execute("DELETE FROM images WHERE image_id=?", (image_id,))
        remaining = connection.execute("SELECT COUNT(*) FROM edit_history").fetchone()[0]
    assert remaining == 0


def test_editor_save_rejects_path_traversal(tmp_path, monkeypatch, capsys):
    import main
    import session as session_ops

    monkeypatch.setattr(main, "SAVE_FOLDER", str(tmp_path / "saved_images"))
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", tmp_path / "himage.db")
    monkeypatch.setattr("builtins.input", lambda _prompt="": "../outside.png")
    session = session_ops.new_session(Image.new("RGB", (4, 4), (1, 2, 3)))
    main.handle_save(session)
    assert not (tmp_path / "outside.png").exists()
    assert "directory paths are not allowed" in capsys.readouterr().out


def test_editor_save_registers_metadata_and_export(tmp_path, monkeypatch):
    import main
    import session as session_ops

    save_folder = tmp_path / "saved_images"
    db_path = tmp_path / "himage.db"
    monkeypatch.setattr(main, "SAVE_FOLDER", str(save_folder))
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "portfolio.png")
    session = session_ops.new_session(Image.new("RGB", (7, 5), (1, 2, 3)))
    result = main.handle_save(session)
    assert result["dirty"] is False
    assert (save_folder / "portfolio.png").is_file()
    assert len(database.list_images(db_path=db_path)) == 1
    with database.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM export_history").fetchone()[0] == 1
