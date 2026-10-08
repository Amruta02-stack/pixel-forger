# Himage — Image Editor and Management System

Himage is a menu-driven image editor that runs in the terminal, written in Python. Load a picture, apply filters, combine images, rotate or flip, preview the result, and save it, all from numbered menus. Every pixel operation is written by hand; [Pillow](https://python-pillow.org/) is used only to open, hold, show and save images. A SQLite database layer records image metadata and export history.

## Features

- **Filters:** Grayscale, Negative, Sepia, and Halftone (a black-and-white dot pattern with an adjustable cell size).
- **Composites:** Simple Overlay (adjustable blend strength) and Green-Screen Key (adjustable sensitivity), placed at any `x,y` position.
- **Transform:** rotate by 90°, 180° or 270°, and flip horizontally or vertically.
- **Preview:** open the image in your system viewer, or print a Braille dot preview straight in the terminal.
- **Undo / Redo:** up to 20 steps back.
- **Safe editing:** a warning before you reapply the same effect, and a warning before unsaved work is lost.
- **Save and manage:** saves go into a `saved_images` folder with automatic names (`result.jpg`, `result_1.jpg`, …). You can list saved images, reload one, or delete one.
- **Database tracking:** image metadata and successful exports are recorded in a local SQLite database (`himage.db`).

## Requirements

- Python 3.10 or newer
- Pillow
- pytest (only for running the tests)

The image-viewer preview needs a desktop with a default image viewer. The terminal dot preview needs a terminal and font that can show Braille characters (most modern ones can).

## Setup

```bash
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
```

## Run

Run commands from the project directory so the `saved_images` folder behaves as expected:

```bash
python main.py
```

On first launch the program initializes `himage.db` beside the Python files and creates a `Default Project`. Image files are saved under `saved_images/`; SQLite stores metadata and export records, not image bytes.

## Run tests

```bash
python -m pytest -q
```

## Using it

Every choice is a whole number from the menu on screen.

```
Main Menu:
1. Load Image  2. Apply Filter  3. Apply Composite  4. Transform
5. Undo  6. Redo  7. Preview  8. Save  9. Delete  10. Show Images
11. Exit
```

A short example session (prompts shortened):

```
Choice: 1
Enter image path: sources/photo1.jpg
Image loaded: sources/photo1.jpg (800x600)

Choice: 2
Choice: 1
Filter applied: Grayscale

Choice: 5
Choice: 8
Image saved to saved_images/result.jpg
```

Things worth knowing:

- Filter, Composite, Transform and Preview open submenus that stay open until you choose **Back**, so you can apply several operations in a row.
- Halftone cell size, green-screen margin and preview width are remembered for the session. Pressing Enter accepts the default shown in the prompt.
- Loading a new image starts a fresh session (history and preferences reset).
- If a path can't be opened, the program reports the error and returns to the menu; it does not crash.

## Project structure

```
.
├── docs/
│   ├── PRD.md               # product requirements
│   └── Design_Document.md   # function signatures, algorithms and formulas
│   └── DB_Design.md        # design for the SQL implementation
├── image_editor_pycodes/
│      └── main.py            # menus, prompts and file handling
│      └── image_ops.py       # pixel processing: filters, composites, rotate/flip, Braille preview
│      └── session.py         # undo/redo history and preferences (pure functions)
│      └── database.py        # application-facing SQLite API
│      └── tests/             # pytest tests
├── schema.sql         # database schema
├── himage.db          # created automatically on first launch
├── saved_images/      # created automatically when you save
└── README.md
```

## How it is built

- **`image_ops.py`** has no input or output, so each function can be tested on its own.
- **`session.py`** holds the editing state as a dictionary: the current image, the undo and redo stacks, an unsaved-changes flag, and the preferences. Every function returns a new session instead of changing the old one, so Undo and Redo stay reliable.
- **`database.py`** is the only module that talks to SQLite, and `schema.sql` documents the tables it uses.
- **`main.py`** connects the layers: it shows the menus, reads input, and calls the functions above.

## Database

Himage uses SQLite for local, single-user storage of metadata. Image bytes stay on disk in `saved_images/`.

| Table | Purpose |
|---|---|
| `projects` | Project records. |
| `images` | File path, format, dimensions and size; each image belongs to a project. |
| `edit_history` | Operation names and JSON parameters associated with an image. |
| `export_history` | Records of successful outputs. |
| `filter_presets` | Named, reusable operation parameters. |

Primary keys uniquely identify records. Foreign keys enforce relationships between tables, `CHECK` constraints reject invalid values, and indexes support project and history lookups.

## Documentation

- [Product Requirements Document](docs/PRD.md): what the program must do, edge cases and test cases.
- [Design Document](docs/Design_Document.md): terminology and formulas, program flow, function signatures and step-by-step algorithms.

## Scope and limitations

- Local, single-user application. SQLite suits this use; it is not a substitute for a managed multi-user server database.
- One image session at a time; undo/redo history and preferences are lost when you exit.
- Currently only image metadata and export records are connected to the save workflow. The `edit_history` and `filter_presets` tables are prepared in the schema but not yet used by the editor.
- No cropping, resizing, arbitrary-angle rotation, transparency (alpha) or batch processing.
- Pixel processing is done by hand in Python, so very large images will be slow.

**Future improvements:** project create/edit/delete screens, a graphical interface, crash recovery, cloud sync, and saving edit history to the database.

## Author

Your Name, Course / Institution, Year

## License

Add a license here (for example MIT), or remove this section.
