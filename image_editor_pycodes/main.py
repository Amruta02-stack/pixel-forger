import os
from PIL import Image, UnidentifiedImageError

import image_ops
import session as session_ops

#implemenating the SQL lite
import sqlite3
from pathlib import Path
import database as db_ops
# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------

MAIN_MENU_TEXT = (
    "\nMain Menu:\n"
    "1. Load Image  2. Apply Filter  3. Apply Composite  4. Transform\n"
    "5. Undo  6. Redo  7. Preview  8. Save  9. Delete  10. Show Images\n"
    "11. Exit"
)

MAIN_MENU_CHOICES = set(range(1, 12))

# All saves live in one folder, so "what have I saved" is just
# "what's in this folder" - no separate list to keep in sync.
SAVE_FOLDER = "saved_images"

FILTER_MENU_TEXT = (
    "\nApply Filter:\n"
    "1. Grayscale  2. Negative  3. Sepia  4. Halftone (Dot Pattern)  5. Back"
)

COMPOSITE_MENU_TEXT = (
    "\nApply Composite:\n"
    "1. Simple Overlay  2. Green-Screen Key  3. Back"
)

TRANSFORM_MENU_TEXT = (
    "\nTransform:\n"
    "1. Rotate  2. Flip  3.Back"
)

PREVIEW_MENU_TEXT = (
    "\nPreview:\n"
    "1. Open in image viewer  2. Print dot preview in terminal  3. Back"
)

LOAD_MENU_TEXT = (
    "\nLoad Image:\n"
    "1. Enter a file path  2. Choose from saved images  3. Back"
)

# Filters/composites where reapplying the same operation right after
# itself changes the image further (rather than being a harmless
# no-op or reverting itself), so the user gets a confirmation prompt.
REAPPLY_WARNING_LABELS = {"Negative", "Halftone", "Sepia", "Simple Overlay", "Green-Screen Key"}


# ---------------------------------------------------------------------------
# FR1 - User Loads Image
# ---------------------------------------------------------------------------


def load_image():
    """
    Ask the user for an image path and try to load it once.
    Returns the loaded image, or None if the path is empty or invalid.
    """
    path = input("Enter image path: ").strip().strip('"').strip("'")

    if not path:
        print("Error: image path cannot be empty")
        return None

    try:
        img = Image.open(path)
        img.load()
        img = img.convert("RGB")

        print(f"Image loaded: {path} ({img.width}x{img.height})")
        return img

    except FileNotFoundError:
        print("Error: file not found")
    except UnidentifiedImageError:
        print("Error: file is not a valid image")
    except OSError:
        print("Error: cannot read that file")

    return None            


def load_image_from_saved():
    """
    List saved images and let the user pick one by number. Returns
    the loaded image, or None if there are no saved images or the
    user backs out.
    """
    filenames = list_saved_images()

    if not filenames:
        print("No saved images yet.")
        return None

    print("\nSaved Images:")
    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")
    back_choice = len(filenames) + 1
    print(f"{back_choice}. Back")

    choice = read_menu_choice(set(range(1, back_choice + 1)))
    if choice == back_choice:
        return None

    path = os.path.join(SAVE_FOLDER, filenames[choice - 1])

    try:
        img = Image.open(path)
        img.load()
        img = img.convert("RGB")
        print(f"Image loaded: {path} ({img.width}x{img.height})")
        return img

    except (FileNotFoundError, UnidentifiedImageError, OSError):
        print(f"Error: cannot load {path}")
        return None


def handle_load(session):
    """Ask how to load an image (typed path or pick a saved one), then load it."""
    
    while True:
        print(LOAD_MENU_TEXT)
        choice = read_menu_choice({1, 2, 3})

        if choice == 3:
            return session

        if choice == 1:
            image = load_image()
        else:
            image = load_image_from_saved()

        if image is None:
            continue # back to load image submenu

        return session_ops.new_session(image)



# ---------------------------------------------------------------------------
# Menu Plumbing
# ---------------------------------------------------------------------------

def render_menu(session):
    return MAIN_MENU_TEXT


def require_loaded_image(session):
    if session["current"] is None:
        print("Error: load an image first")
        return False

    return True


def confirm_reapply(session, label):
    """
    If label is in REAPPLY_WARNING_LABELS and was also the very last
    operation applied, ask the user to confirm before doing it again
    (reapplying would change the image further, not just undo it).
    Returns True if the operation should proceed.
    """
    if label not in REAPPLY_WARNING_LABELS:
        return True

    if not session["undo_stack"] or session["undo_stack"][-1][1] != label:
        return True

    answer = input(
        f"{label} was just applied — applying it again will change "
        f"the image (not just remove it). Continue? (y/n): "
    ).strip().lower()

    if answer != "y":
        print(f"{label} cancelled.")
        return False
    return True


def read_menu_choice(valid, prompt="Choice: "):
    while True:
        raw = input(prompt)

        try:
            choice = int(raw)
        except ValueError:
            print("Error: invalid menu choice")
            continue

        if choice not in valid:
            print("Error: invalid menu choice")
            continue

        return choice


# ---------------------------------------------------------------------------
# FR2 - Filters
# ---------------------------------------------------------------------------

def handle_filter_menu(session):
    if not require_loaded_image(session):
        return session

    while True:
        print(FILTER_MENU_TEXT)
        choice = read_menu_choice({1, 2, 3, 4, 5})

        if choice == 5:
            return session

        if choice == 1:
            new_image = image_ops.grayscale(session["current"])
            label = "Grayscale"

        elif choice == 2:
             
            
            new_image = image_ops.negative(session["current"])
            label = "Negative"
        elif choice == 3:
            new_image = image_ops.sepia(session["current"])
            label = "Sepia"

        else:
            default_size = session["halftone_cell_size"]

            while True:
                raw = input(
                    f"Enter cell size (default {default_size}): "
                ).strip()

                if raw == "":
                    cell_size = default_size
                    break

                if image_ops.is_valid_cell_size(raw):
                    cell_size = int(raw)
                    break

                print("Error: cell size must be a positive integer")

            session = session_ops.set_cell_size(session, cell_size)

            new_image = image_ops.halftone(
                session["current"],
                cell_size
            )

            label = "Halftone"

        if not confirm_reapply(session, label):
            continue

        session = session_ops.push_state(
            session,
            new_image,
            label
        )

        print(f"Filter applied: {label}")
        # Loop back to the submenu so multiple filters can be applied
        # in a row without bouncing back to the main menu each time.


# ---------------------------------------------------------------------------
# FR3 - Composite
# ---------------------------------------------------------------------------

def handle_composite_menu(session):
    if not require_loaded_image(session):
        return session

    while True:
        print(COMPOSITE_MENU_TEXT)
        choice = read_menu_choice({1, 2, 3})

        if choice == 3:
            return session

        # Ask user for the second image. A bad path returns to the
        # Composite menu instead of re-prompting forever.
        second_path = input("Enter image path: ").strip().strip('"').strip("'")

        try:
            foreground = Image.open(second_path)
            foreground.load()
            foreground = foreground.convert("RGB")
        except FileNotFoundError:
            print("Error: file not found")
            continue
        except UnidentifiedImageError:
            print("Error: file is not a valid image")
            continue
        except OSError:
            print("Error: cannot read that file")
            continue



        # Position
        while True:
            position = input(
                "Enter position (x,y) (default 0,0): "
            ).strip()

            if position == "":
                x, y = 0, 0
                break

            try:
                x_text, y_text = position.split(",")
                x = int(x_text.strip())
                y = int(y_text.strip())
                break

            except ValueError:
                print("Error: invalid position. Use format x,y")

        background = session["current"]

        if not image_ops.is_valid_position(
            background.width,
            background.height,
            foreground.width,
            foreground.height,
            x,
            y
        ):
            print("Error: overlay position is out of bounds")
            continue

        # Simple Overlay
        if choice == 1:

            while True:
                alpha_text = input(
                    "Enter blend strength (0-1) (default 0.5): "
                ).strip()

                if alpha_text == "":
                    alpha = 0.5
                    break

                if image_ops.is_valid_blend_strength(alpha_text):
                    alpha = float(alpha_text)
                    break

                print(
                    "Error: blend strength must be between 0 and 1"
                )

            new_image = image_ops.simple_overlay(
                background,
                foreground,
                x,
                y,
                alpha
            )

            label = "Simple Overlay"

        # Green Screen
        else:
            default_margin = session["green_margin"]

            while True:
                margin_text = input(
                    f"Enter green-key sensitivity margin (default {default_margin}): "
                ).strip()

                if margin_text == "":
                    margin = default_margin
                    break

                if image_ops.is_valid_green_margin(margin_text):
                    margin = int(margin_text)
                    break

                print("Error: margin must be a non-negative integer")

            session = session_ops.set_green_margin(session, margin)

            new_image = image_ops.green_screen(
                background,
                foreground,
                x,
                y,
                margin
            )

            label = "Green-Screen Key"

        if not confirm_reapply(session, label):
            continue

        session = session_ops.push_state(
            session,
            new_image,
            label
        )

        print(f"Composite applied: {label}")
        # Loop back to the submenu so another composite can be
        # applied without bouncing back to the main menu.


# ---------------------------------------------------------------------------
# FR4 - Rotation
# ---------------------------------------------------------------------------

def handle_transform_menu(session):
    if not require_loaded_image(session):
        return session

    while True:
        print(TRANSFORM_MENU_TEXT)
        choice = read_menu_choice({1, 2, 3})

        if choice == 3:
            return session

        current = session["current"]

        # Rotate
        if choice == 1:
            while True:
                raw = input("Enter rotation (90, 180, or 270): ").strip()

                try:
                    degrees = int(raw)
                except ValueError:
                    print("Error: invalid rotation")
                    continue

                if not image_ops.is_valid_rotation(degrees):
                    print("Error: invalid rotation")
                    continue

                break

            new_image = image_ops.rotate(current, degrees)
            label = f"Rotate {degrees}"
            success_message = f"Rotated {degrees} degrees"
                # Flip
        else:  # choice == 2
            while True:
                axis = input("Enter h for horizontal flip or v for vertical flip: ").strip().lower()

                if axis == "h":
                    new_image = image_ops.flip_horizontal(current)
                    label = "Flip Horizontal"
                    success_message = "Flipped horizontally"
                    break
                elif axis == "v":
                    new_image = image_ops.flip_vertical(current)
                    label = "Flip Vertical"
                    success_message = "Flipped vertically"
                    break
                else:
                    print("Error: enter h or v")
                    continue

        session = session_ops.push_state(session, new_image, label)

        print(success_message)
        # Loop back to the submenu so Rotate and flip can both be
        # applied without bouncing back to the main menu in between.


# ---------------------------------------------------------------------------
# FR5 / FR10 - Preview
# ---------------------------------------------------------------------------

def handle_preview(session):
    if not require_loaded_image(session):
        return session

    while True:
        print(PREVIEW_MENU_TEXT)
        choice = read_menu_choice({1, 2, 3})

        if choice == 3:
            return session

        if choice == 1:
            session["current"].show()
            continue

        al_neg = (
            session["undo_stack"]
            and session["undo_stack"][-1][1] == "Negative"
        )

        if al_neg:
            preview_image = session["current"]
        else:
            preview_image = image_ops.negative(session["current"])

        default_width = session["braille_width_chars"]

        while True:
            width_text = input(
                f"Enter preview width in characters (default {default_width}): "
            ).strip()

            if width_text == "":
                width_chars = default_width
                break

            if image_ops.is_valid_braille_width(width_text):
                width_chars = int(width_text)
                break

            print("Error: width must be a positive integer")

        session = session_ops.set_braille_width(session, width_chars)

        print(
            image_ops.braille_dots(
                preview_image,
                width_chars
            )
        )
        # Loop back to the submenu instead of bouncing to the main menu.


# ---------------------------------------------------------------------------
# FR7 - Save
# ---------------------------------------------------------------------------

def _next_default_save_name(folder):
    """
    Return the next unused auto-incrementing default filename inside
    folder: result.jpg, then result_1.jpg, result_2.jpg, ... This only
    ever applies to the *default* - a filename the user types is
    always used exactly as given, never auto-incremented.
    """
    candidate = "result.jpg"
    if not os.path.exists(os.path.join(folder, candidate)):
        return candidate

    counter = 1
    while True:
        candidate = f"result_{counter}.jpg"
        if not os.path.exists(os.path.join(folder, candidate)):
            return candidate
        counter += 1


def handle_save(session):
    if not require_loaded_image(session):
        return session

    os.makedirs(SAVE_FOLDER, exist_ok=True)

    default_name = _next_default_save_name(SAVE_FOLDER)

    raw_name = input(
        f"Enter save filename (default {default_name}): ").strip()

    filename = raw_name if raw_name else default_name

    if (
        filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or Path(filename).name != filename
    ):
        print("Error: enter a filename only; directory paths are not allowed.")
        return session

    if Path(filename).suffix.lower().lstrip(".") not in db_ops.SUPPORTED_FORMATS:
        print("Error: supported formats are JPG, JPEG, PNG, WEBP, BMP, GIF, and TIFF.")
        return session

    save_path = os.path.join(SAVE_FOLDER, filename)

    # The auto-generated default name never collides with an existing
    # file, but a name the user typed in might - confirm before
    # overwriting anything that's already there.
    if raw_name and os.path.exists(save_path):
        answer = input(
            f"{filename} already exists. Overwrite? (y/n): "
        ).strip().lower()

        if answer != "y":
            print("Save cancelled.")
            return session

    try:
        session["current"].save(save_path)

    except (OSError, ValueError):
        print(f"Error: cannot save to {save_path}")
        return session

    try:
        image_id = db_ops.register_image(
            save_path,
            session["current"].width,
            session["current"].height
        )

        db_ops.record_export(
            image_id,
            save_path,
            session["current"].width,
            session["current"].height
        )

    except (OSError, ValueError, sqlite3.Error) as exc:
        print(
            "Warning: image saved, but database metadata was not recorded: "
            f"{exc}"
        )

    session = session_ops.mark_saved(session)

    print(f"Image saved to {save_path}")

    return session


# ---------------------------------------------------------------------------
# Show Images
# ---------------------------------------------------------------------------

def list_saved_images():
    """Return the sorted filenames currently in SAVE_FOLDER (possibly empty)."""
    if not os.path.isdir(SAVE_FOLDER):
        return []

    supported = {"." + ext for ext in db_ops.SUPPORTED_FORMATS}

    return sorted(
        name for name in os.listdir(SAVE_FOLDER)
        if (
            os.path.isfile(os.path.join(SAVE_FOLDER, name))
            and Path(name).suffix.lower() in supported
        )
    )


def handle_show_images():
    filenames = list_saved_images()

    if not filenames:
        print("No saved images yet.")
        return

    print("\nSaved Images:")
    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")


# ---------------------------------------------------------------------------
# FR6 - Undo / Redo
# ---------------------------------------------------------------------------

def handle_undo(session):
    result = session_ops.undo(session)

    if result is None:
        print("Error: nothing to undo")
        return session

    print("Undo successful. Reverted to previous state.")

    return result


def handle_redo(session):
    result = session_ops.redo(session)

    if result is None:
        print("Error: nothing to redo")
        return session

    print("Redo successful.")

    return result


# ---------------------------------------------------------------------------
# FR8 - Delete / Clear
# ---------------------------------------------------------------------------

def confirm_discard(session):
    if not session_ops.has_unsaved_changes(session):
        return session

    while True:
        answer = input(
            "You have unsaved changes. Save before continuing? (y/n): ").strip().lower()

        if answer == "y":
            session = handle_save(session)
            if session_ops.has_unsaved_changes(session):
                print("Save was unsuccessful. Let's try again.")
                continue
            return session

        if answer == "n":
            return session

        print("Error: please answer y or n")



def handle_delete(session):
    choice = read_menu_choice(
        {1, 2},
        prompt="Enter (1) Delete image or (2) existing saved image? "
    )

    if choice == 1:
        session = confirm_discard(session)
            

        print("Image session cleared.")

        return session_ops.clear_session()

    # choice == 2: delete a saved file - doesn't touch the in-memory
    # session at all, so it's returned unchanged.
    filenames = list_saved_images()

    if not filenames:
        print("No saved images to delete")
        return session

    print("\nSaved Images:")
    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")

    file_choice = read_menu_choice(set(range(1, len(filenames) + 1)))
    target = filenames[file_choice - 1]

    confirm = input(f"Delete {target}? (y/n): ").strip().lower()
    while confirm not in ("y", "n"):
        print("Error: please answer y or n")
        confirm = input(f"Delete {target}? (y/n): ").strip().lower()

    if confirm == "y":
        target_path = os.path.join(SAVE_FOLDER, target)
        try:
            os.remove(target_path)
        except OSError:
            print(f"Error: cannot delete {target}")
        else:
            print(f"Deleted {target}")
            try:
                db_ops.delete_image_record(target_path)
            except sqlite3.Error as exc:
                print(f"Warning: file deleted, but database record was not removed: {exc}")
    else:
        print("Delete cancelled")
    return session


# ---------------------------------------------------------------------------
# Main Program
# ---------------------------------------------------------------------------

def main():
    try:
        db_ops.initialize_database()
    except sqlite3.Error as exc:
        print(f"Warning: database initialization failed: {exc}")
        
    # Start with an empty session
    session = session_ops.clear_session()

    print("=================================")
    print("       IMAGE EDITOR")
    print("=================================")

  

    while True:

        print(render_menu(session))

        choice = read_menu_choice(MAIN_MENU_CHOICES)

        # 1. Load another image
        if choice == 1:

            session = confirm_discard(session)
            session = handle_load(session)

        # 2. Filter
        elif choice == 2:

            session = handle_filter_menu(session)

        # 3. Composite
        elif choice == 3:

            session = handle_composite_menu(session)
            

        # 4. Transform
        elif choice == 4:

            session = handle_transform_menu(session)

        # 5. Undo
        elif choice == 5:

            session = handle_undo(session)

        # 6. Redo
        elif choice == 6:

            session = handle_redo(session)

        # 7. Preview
        elif choice == 7:

            session = handle_preview(session)

        # 8. Save
        elif choice == 8:

            session = handle_save(session)

        # 9. Delete
        elif choice == 9:

            session = handle_delete(session)

        # 10. Show Images
        elif choice == 10:

            handle_show_images()

        # 11. Exit
        elif choice == 11:

            session =confirm_discard(session)
            print("Goodbye!")
            break


# ---------------------------------------------------------------------------
# Program Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()