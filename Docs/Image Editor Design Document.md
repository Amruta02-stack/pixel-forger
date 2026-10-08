# Image Editor Design Document | Program Design & Development

## 1. Terminology

### The session

The session is the one dictionary that holds everything the editor remembers. Every session function returns a NEW session and never changes the one it was given.

| Field | Meaning |
| --- | --- |
| `current` | The image being edited, or None when nothing is loaded |
| `undo_stack` | List of (image, label) pairs, oldest first, at most 20 long (`MAX_UNDO_STEPS`) |
| `redo_stack` | Same shape as `undo_stack`; filled by Undo, emptied by any new edit |
| `dirty` | True when there are changes not yet saved |
| `halftone_cell_size` | Preference, default 10 |
| `green_margin` | Preference, default 30 |
| `braille_width_chars` | Preference, default 67 |

### Labels

Each history entry carries a label naming the operation that was applied on top of the stored image. The label on the top of `undo_stack` therefore names the last operation applied. The labels are: Grayscale, Negative, Sepia, Halftone, Simple Overlay, Green-Screen Key, Rotate 90 / 180 / 270, Flip Horizontal, Flip Vertical.

### Edits and preferences

An edit (filter, composite, rotate, flip) pushes a new state, clears `redo_stack` and sets `dirty`. A preference (cell size, green margin, preview width) changes one field only: it is not undoable and does not set `dirty`.

### Undo cap

When `undo_stack` grows past 20 entries, the oldest entry is dropped silently. This bounds memory, because every entry holds a full copy of the image.

### Reapply warning

Negative, Halftone, Sepia, Simple Overlay and Green-Screen Key change the image further when applied twice in a row. If the chosen label equals the label on top of `undo_stack`, the user is asked "Continue? (y/n)" first. Grayscale, rotations and flips are exempt.

### Default save name

The default filename inside `saved_images` is the first unused name in the order `result.jpg`, `result_1.jpg`, `result_2.jpg`, and so on. A filename the user types is always used exactly as given; if it already exists the user must confirm the overwrite.

## 2. Program Flow

1. Create an empty session and print the IMAGE EDITOR banner.
2. Print the main menu.
3. Read a menu choice from 1 to 11, asking again until it is valid.
4. Run the handler for that choice and replace the session with what it returns:
    1. Load Image: if there are unsaved changes, run the discard warning first; then load by typed path or from `saved_images` and start a brand-new session. If a load fails, the Load menu is shown again; Back returns to the main menu.
    2. Apply Filter: Grayscale, Negative, Sepia, or Halftone, then push the result onto the history.
    3. Apply Composite: Simple Overlay or Green-Screen Key, then push the result onto the history.
    4. Transform: Rotate or Flip, then push the result onto the history.
    5. Undo: restore the previous state, or report there is nothing to undo.
    6. Redo: restore the undone state, or report there is nothing to redo.
    7. Preview: open the image viewer or print the Braille dot preview.
    8. Save: write the current image into `saved_images` and mark the session saved.
    9. Delete: clear the session, or delete a saved file.
    10. Show Images: list the files in `saved_images`.
    11. Exit: if there are unsaved changes, run the discard warning first; then print Goodbye! and stop.
5. Options 2, 3, 4 and 7 stay inside their own submenu, so several operations can be applied in a row, until the user chooses Back.
6. Options 2, 3, 4, 7 and 8 print "Error: load an image first" and do nothing when no image is loaded.
7. Unless the user exited in step 4, go back to step 2.
8. End.

## 3. Function Signatures

The code is split in three files: `image_ops.py` (pure picture functions and validators, no input or output), `session.py` (pure history and preference functions), and `main.py` (menus, prompts and file handling). Image means PIL's `Image.Image`. `session.py` imports the green margin and preview width defaults (30 and 67) from `image_ops.py`, so each default is defined in one place.

### image_ops.py

| Functions | What it's for |
| --- | --- |
| `def clamp(value: int) -> int:` | Restricts a channel value to 0–255. |
| `def _luminosity(r: int, g: int, b: int) -> float:` | Returns the luminosity-weighted brightness of one pixel, unrounded. |
| `def grayscale(image: Image) -> Image:` | Returns a new image where every pixel is its luminosity gray. |
| `def negative(image: Image) -> Image:` | Returns a new image with every channel inverted. |
| `def sepia(image: Image) -> Image:` | Returns a new image with the sepia matrix applied, clamped. |
| `def is_valid_cell_size(text: str) -> bool:` | Returns True if the text is a whole number of 1 or more. |
| `def halftone(image: Image, cell_size: int) -> Image:` | Returns a new black-and-white dot-pattern image, one dot per cell. |
| `def is_valid_braille_width(text: str) -> bool:` | Returns True if the text is a whole number of 1 or more. |
| `def _box_downsample_luminosity(image: Image, target_width: int, target_height: int) -> list:` | Shrinks the image by hand to a grid of average luminosity per cell. |
| `def _floyd_steinberg_dither(grid: list, width: int, height: int) -> list:` | Turns a luminosity grid into a grid of on/off dots with error diffusion. |
| `def braille_dots(image: Image, max_width_chars: int = 67) -> str:` | Returns the image as multi-line Braille text for the terminal preview. |
| `def is_valid_green_margin(text: str) -> bool:` | Returns True if the text is a whole number of 0 or more. |
| `def is_green_pixel(r: int, g: int, b: int, margin: int = 30) -> bool:` | Returns True if the pixel counts as keyed green. |
| `def valid_region(bg_w: int, bg_h: int, fg_w: int, fg_h: int, x: int, y: int) -> tuple:` | Returns (x0, y0, x1, y1), the rectangle both images share. |
| `def is_valid_position(bg_w: int, bg_h: int, fg_w: int, fg_h: int, x: int, y: int) -> bool:` | Returns True if the placed foreground overlaps the background by at least one pixel. |
| `def is_valid_blend_strength(text: str) -> bool:` | Returns True if the text is a number from 0 to 1 inclusive. |
| `def simple_overlay(background: Image, foreground: Image, x: int, y: int, alpha: float) -> Image:` | Returns a new image with the foreground blended onto the background. |
| `def green_screen(background: Image, foreground: Image, x: int, y: int, margin: int = 30) -> Image:` | Returns a new image with the non-green foreground pixels placed over the background. |
| `def _rotate_90(image: Image) -> Image:` | Returns a new image turned one quarter-turn clockwise. |
| `def is_valid_rotation(degrees: int) -> bool:` | Returns True only for 90, 180 or 270. |
| `def rotate(image: Image, degrees: int) -> Image:` | Returns a new image rotated clockwise by 90, 180 or 270 degrees. |
| `def flip_horizontal(image: Image) -> Image:` | Returns a new image mirrored left to right. |
| `def flip_vertical(image: Image) -> Image:` | Returns a new image mirrored top to bottom. |

### session.py

| Functions | What it's for |
| --- | --- |
| `def new_session(image: Image) -> dict:` | Returns the starting session for a freshly loaded image. |
| `def push_state(session: dict, image: Image, label: str) -> dict:` | Returns a new session with the new image as current and the old one pushed onto `undo_stack`. |
| `def undo(session: dict) -> dict \| None:` | Returns a new session one step back, or None if there is nothing to undo. |
| `def redo(session: dict) -> dict \| None:` | Returns a new session one step forward, or None if there is nothing to redo. |
| `def mark_saved(session: dict) -> dict:` | Returns a new session with dirty set to False. |
| `def has_unsaved_changes(session: dict) -> bool:` | Returns the dirty flag. |
| `def set_cell_size(session: dict, cell_size: int) -> dict:` | Returns a new session with the Halftone cell size preference updated. |
| `def set_green_margin(session: dict, margin: int) -> dict:` | Returns a new session with the green margin preference updated. |
| `def set_braille_width(session: dict, width_chars: int) -> dict:` | Returns a new session with the preview width preference updated. |
| `def clear_session() -> dict:` | Returns a fresh empty session with default preferences. |

### main.py

| Functions | What it's for |
| --- | --- |
| `def load_image() -> Image:` | Asks for an image path once and returns the image, or None if the path is empty or cannot be opened. |
| `def load_image_from_saved() -> Image \| None:` | Lists saved images and returns the chosen one, or None if there are none or the user backs out. |
| `def handle_load(session: dict) -> dict:` | Runs the Load submenu and returns a brand-new session, or the same session if the user backs out. |
| `def render_menu(session: dict) -> str:` | Returns the main menu text. |
| `def require_loaded_image(session: dict) -> bool:` | Returns True if an image is loaded; otherwise prints the error and returns False. |
| `def confirm_reapply(session: dict, label: str) -> bool:` | Asks for confirmation if the same compounding operation was just applied; returns True to go ahead. |
| `def read_menu_choice(valid: set, prompt: str = "Choice: ") -> int:` | Reads a whole number until it is in the valid set. |
| `def handle_filter_menu(session: dict) -> dict:` | Runs the Filter submenu and returns the updated session. |
| `def handle_composite_menu(session: dict) -> dict:` | Runs the Composite submenu and returns the updated session. |
| `def handle_transform_menu(session: dict) -> dict:` | Runs the Transform submenu and returns the updated session. |
| `def handle_preview(session: dict) -> dict:` | Runs the Preview submenu and returns the updated session. |
| `def _next_default_save_name(folder: str) -> str:` | Returns the first unused name among `result.jpg`, `result_1.jpg`, and so on. |
| `def handle_save(session: dict) -> dict:` | Saves the current image into `saved_images` and returns the updated session. |
| `def list_saved_images() -> list:` | Returns the sorted filenames in `saved_images`, possibly empty. |
| `def handle_show_images() -> None:` | Prints the saved filenames numbered, or says there are none. |
| `def handle_undo(session: dict) -> dict:` | Undoes one step and prints the result. |
| `def handle_redo(session: dict) -> dict:` | Redoes one step and prints the result. |
| `def confirm_discard(session: dict) -> dict:` | Warns about unsaved changes, saves first if the user says y, and returns the session (marked saved if the save worked). |
| `def handle_delete(session: dict) -> dict:` | Clears the session or deletes a saved file, as chosen. |
| `def main() -> None:` | Runs the menu loop until the user exits. |

## 4. Function-Level Algorithm

### image_ops.py

**`clamp(value)`**

1. If value is below 0, return 0.
2. If value is above 255, return 255.
3. Return value.

**`_luminosity(r, g, b)`**

1. Return 0.299 × r + 0.587 × g + 0.114 × b.

**`grayscale(image)`**

1. Convert image to RGB, read its width and height, and make a new blank RGB image of the same size.
2. For each row y, then each column x:
3. Read (r, g, b) at (x, y).
4. Set gray to clamp(round(_luminosity(r, g, b))).
5. Write (gray, gray, gray) to the new image at (x, y).
6. Return the new image.

**`negative(image)`**

1. Convert image to RGB and make a new blank RGB image of the same size.
2. For each pixel (x, y), read (r, g, b).
3. Write (255 − r, 255 − g, 255 − b) to the new image at (x, y).
4. Return the new image.

**`sepia(image)`**

1. Convert image to RGB and make a new blank RGB image of the same size.
2. For each pixel (x, y), read (r, g, b).
3. Set new_r to clamp(round(0.393r + 0.769g + 0.189b)).
4. Set new_g to clamp(round(0.349r + 0.686g + 0.168b)).
5. Set new_b to clamp(round(0.272r + 0.534g + 0.131b)).
6. Write (new_r, new_g, new_b) to the new image at (x, y).
7. Return the new image.

**`is_valid_cell_size(text)`**

1. Try to convert text to a whole number; if that fails, return False.
2. Return True if the number is at least 1, otherwise False.

**`halftone(image, cell_size)`**

1. Convert image to RGB and make a new RGB image of the same size, filled white.
2. For each cell, stepping down by cell_size rows and across by cell_size columns:
3. Set the cell's bottom and right edges to the cell size, cut off at the image edge.
4. Add _luminosity of every pixel inside the cell and count the pixels.
5. Set brightness to the total divided by the count (255 if the count is 0).
6. Set radius to round((255 − brightness) / 255 × cell_size / 2).
7. Set the centre to the middle of the cell, ((left + right − 1) / 2, (top + bottom − 1) / 2).
8. If radius is greater than 0, write black to every pixel in the cell whose distance from the centre is at most radius.
9. Return the new image.

**`is_valid_braille_width(text)`**

1. Try to convert text to a whole number; if that fails, return False.
2. Return True if the number is at least 1, otherwise False.

**`_box_downsample_luminosity(image, target_width, target_height)`**

1. Convert image to RGB and make an empty target_height × target_width grid.
2. For each target cell (tx, ty):
3. Set y0 to ty × source_height // target_height, and y1 to the larger of y0 + 1 and (ty + 1) × source_height // target_height.
4. Set x0 and x1 the same way using the widths.
5. Set the cell to the average _luminosity of the source pixels in x0..x1 by y0..y1.
6. Return the grid.

**`_floyd_steinberg_dither(grid, width, height)`**

1. Copy the grid into work, so the caller's grid is not changed, and make an all-False grid called on.
2. For each row y, then each column x:
3. Set old_value to work[y][x].
4. Set dark to True if old_value is below 128, and store it in on[y][x].
5. Set error to old_value minus 0 if dark, or minus 255 if not.
6. Add error × 7/16 to the pixel on the right, if it exists.
7. If a row below exists, add error × 3/16 to the pixel below-left (if it exists), × 5/16 to the pixel below, and × 1/16 to the pixel below-right (if it exists).
8. Return on.

**`braille_dots(image, max_width_chars)`**

1. Convert image to RGB and read its width and height.
2. Set target_width to the larger of 2 and max_width_chars × 2.
3. Set target_height to the larger of 4 and round(source_height × target_width / source_width), then round it down to a multiple of 4 (use 4 if that gives 0).
4. Call _box_downsample_luminosity to get the luminosity grid.
5. Call _floyd_steinberg_dither on that grid to get the on/off dots.
6. For each block of 4 rows, and within it each block of 2 columns:
7. Set bitmask to 0.
8. For each of the 8 sub-dot positions, skip it if it lies past the grid edge; otherwise, if its dot is on, add its bit value to bitmask.
9. Add the character chr(0x2800 + bitmask) to the current row.
10. Join each row's characters into a line, join the lines with newlines, and return the text.

**`is_valid_green_margin(text)`**

1. Try to convert text to a whole number; if that fails, return False.
2. Return True if the number is at least 0, otherwise False.

**`is_green_pixel(r, g, b, margin)`**

1. Return True if g is greater than r + margin and g is greater than b + margin; otherwise return False.

**`valid_region(bg_w, bg_h, fg_w, fg_h, x, y)`**

1. Set x0 to the larger of 0 and x, and y0 to the larger of 0 and y.
2. Set x1 to the smaller of bg_w and x + fg_w, and y1 to the smaller of bg_h and y + fg_h.
3. Return (x0, y0, x1, y1).

**`is_valid_position(bg_w, bg_h, fg_w, fg_h, x, y)`**

1. Call valid_region to get (x0, y0, x1, y1).
2. Return True if x1 > x0 and y1 > y0, otherwise False.

**`is_valid_blend_strength(text)`**

1. Try to convert text to a decimal number; if that fails, return False.
2. Return True if the number is from 0 to 1 inclusive, otherwise False.

**`simple_overlay(background, foreground, x, y, alpha)`**

1. Convert both images to RGB and make out as a copy of the background.
2. Call valid_region to get the shared rectangle.
3. For each background pixel (bx, by) inside that rectangle:
4. Find the matching foreground pixel at (bx − x, by − y).
5. For each of the three channels, write clamp(round(bg × (1 − alpha) + fg × alpha)) into out.
6. Return out.

**`green_screen(background, foreground, x, y, margin)`**

1. Convert both images to RGB and make out as a copy of the background.
2. Call valid_region to get the shared rectangle.
3. For each background pixel (bx, by) inside that rectangle:
4. Read the matching foreground pixel (r, g, b) at (bx − x, by − y).
5. If is_green_pixel(r, g, b, margin) is False, write (r, g, b) into out at (bx, by).
6. Return out.

**`_rotate_90(image)`**

1. Read the width and height and make a new RGB image of size height × width.
2. For each pixel (x, y), write it to the new image at (height − 1 − y, x).
3. Return the new image.

**`is_valid_rotation(degrees)`**

1. Return True if degrees is 90, 180 or 270, otherwise False.

**`rotate(image, degrees)`**

1. Convert image to RGB.
2. Set turns to 1 for 90, 2 for 180, or 3 for 270.
3. Repeat turns times: replace the result with _rotate_90 of the result.
4. Return the result.

**`flip_horizontal(image)`**

1. Convert image to RGB and make a new RGB image of the same size.
2. For each pixel (x, y), write it to the new image at (width − 1 − x, y).
3. Return the new image.

**`flip_vertical(image)`**

1. Convert image to RGB and make a new RGB image of the same size.
2. For each pixel (x, y), write it to the new image at (x, height − 1 − y).
3. Return the new image.

### session.py

**`new_session(image)`**

1. Return a session with current set to image, empty undo_stack and redo_stack, dirty False, and the three preferences at their defaults (10, 30, 67).

**`push_state(session, image, label)`**

1. Make new_undo_stack from undo_stack plus the pair (current, label).
2. If new_undo_stack has more than 20 entries, keep only the newest 20.
3. Return a copy of the session with current set to image, undo_stack set to new_undo_stack, redo_stack emptied, and dirty True. Preferences are unchanged.

**`undo(session)`**

1. If undo_stack is empty, return None.
2. Take the last pair (prev_image, label) from undo_stack.
3. Return a copy of the session with current set to prev_image, that pair removed from undo_stack, the pair (old current, label) added to redo_stack, and dirty True.

**`redo(session)`**

1. If redo_stack is empty, return None.
2. Take the last pair (next_image, label) from redo_stack.
3. Return a copy of the session with current set to next_image, that pair removed from redo_stack, the pair (old current, label) added to undo_stack, and dirty True.

**`mark_saved(session)`**

1. Return a copy of the session with dirty set to False.

**`has_unsaved_changes(session)`**

1. Return session["dirty"].

**`set_cell_size(session, cell_size)`**

1. Return a copy of the session with halftone_cell_size set to cell_size. Nothing else changes.

**`set_green_margin(session, margin)`**

1. Return a copy of the session with green_margin set to margin. Nothing else changes.

**`set_braille_width(session, width_chars)`**

1. Return a copy of the session with braille_width_chars set to width_chars. Nothing else changes.

**`clear_session()`**

1. Return a session with current set to None, empty undo_stack and redo_stack, dirty False, and the three preferences at their defaults.

### main.py

**`read_menu_choice(valid, prompt)`**

1. Read a line of text with the prompt.
2. If it is not a whole number, print "Error: invalid menu choice" and go back to step 1.
3. If the number is not in valid, print the same error and go back to step 1.
4. Return the number.

**`require_loaded_image(session)`**

1. If current is None, print "Error: load an image first" and return False.
2. Return True.

**`render_menu(session)`**

1. Return the main menu text.

**`confirm_reapply(session, label)`**

1. If label is not Negative, Halftone, Sepia, Simple Overlay or Green-Screen Key, return True.
2. If undo_stack is empty, or the label on its top entry is not label, return True.
3. Ask `<label> was just applied — applying it again will change the image (not just remove it). Continue? (y/n)`.
4. If the answer is not y, print `<label> cancelled.` and return False.
5. Return True.

**`load_image()`**

1. Ask for an image path, trim it, and remove any surrounding quote marks.
2. If it is empty, print "Error: image path cannot be empty" and return None.
3. Try to open it, load the pixels and convert to RGB. If that fails, print "Error: file not found", "Error: file is not a valid image" or "Error: cannot read that file" (whichever applies) and return None.
4. Print `Image loaded: <path> (<width>x<height>)` and return the image.

**`load_image_from_saved()`**

1. Get the filenames from list_saved_images.
2. If there are none, print "No saved images yet." and return None.
3. Print the filenames numbered, followed by a Back option numbered one higher.
4. Read a choice. If it is Back, return None.
5. Try to open the chosen file in saved_images and convert to RGB. If that fails, print `Error: cannot load <path>` and return None.
6. Print `Image loaded: <path> (<width>x<height>)` and return the image.

**`handle_load(session)`**

1. Print the Load menu and read a choice from 1 to 3.
2. If the choice is 3, return the session unchanged.
3. If the choice is 1, call load_image; otherwise call load_image_from_saved.
4. If no image came back, go back to step 1 (the Load menu is shown again).
5. Return new_session(image).

**`handle_filter_menu(session)`**

1. If no image is loaded, return the session.
2. Print the Filter menu and read a choice from 1 to 5.
3. If the choice is 5, return the session.
4. For choices 1 to 3, call grayscale, negative or sepia on current and set the label to Grayscale, Negative or Sepia.
5. For choice 4, ask for a cell size, offering the stored preference as the default. Pressing Enter keeps the default; a value that fails is_valid_cell_size prints "Error: cell size must be a positive integer" and asks again.
6. Store the cell size with set_cell_size, call halftone on current, and set the label to Halftone.
7. If confirm_reapply returns False, go back to step 2.
8. Replace the session with push_state(session, new_image, label).
9. Print `Filter applied: <label>` and go back to step 2.

**`handle_composite_menu(session)`**

1. If no image is loaded, return the session.
2. Print the Composite menu and read a choice from 1 to 3. If it is 3, return the session.
3. Ask for the second image path once. If it cannot be opened, print "Error: file not found", "Error: file is not a valid image" or "Error: cannot read that file" (whichever applies) and go back to step 2.
4. Ask for the position as x,y. Pressing Enter gives 0,0; text that is not two whole numbers separated by a comma prints "Error: invalid position. Use format x,y" and asks again.
5. If is_valid_position is False, print "Error: overlay position is out of bounds" and go back to step 2.
6. If the choice is Simple Overlay: ask for blend strength (Enter gives 0.5; reject values failing is_valid_blend_strength with "Error: blend strength must be between 0 and 1"), then call simple_overlay and set the label to Simple Overlay.
7. Otherwise (Green-Screen Key): ask for the margin, offering the stored preference as the default (reject values failing is_valid_green_margin with "Error: margin must be a non-negative integer"), store it with set_green_margin, call green_screen, and set the label to Green-Screen Key.
8. If confirm_reapply returns False, go back to step 2.
9. Replace the session with push_state(session, new_image, label).
10. Print `Composite applied: <label>` and go back to step 2.

**`handle_transform_menu(session)`**

1. If no image is loaded, return the session.
2. Print the Transform menu and read a choice from 1 to 3. If it is 3, return the session.
3. If the choice is Rotate: ask for 90, 180 or 270 until the answer is a whole number that passes is_valid_rotation ("Error: invalid rotation" otherwise), call rotate, and set the label to `Rotate <degrees>`.
4. If the choice is Flip: ask for h or v until one is entered ("Error: enter h or v" otherwise), call flip_horizontal or flip_vertical, and set the label to Flip Horizontal or Flip Vertical.
5. Replace the session with push_state(session, new_image, label).
6. Print the success message and go back to step 2.

**`handle_preview(session)`**

1. If no image is loaded, return the session.
2. Print the Preview menu and read a choice from 1 to 3. If it is 3, return the session.
3. If the choice is 1, show the current image in the image viewer and go back to step 2.
4. If the label on top of undo_stack is Negative, use current as the preview image; otherwise use negative(current).
5. Ask for the width in characters, offering the stored preference as the default (reject values failing is_valid_braille_width with "Error: width must be a positive integer").
6. Store the width with set_braille_width, then print braille_dots(preview image, width).
7. Go back to step 2.

**`_next_default_save_name(folder)`**

1. If result.jpg does not exist in folder, return "result.jpg".
2. Set counter to 1.
3. If `result_<counter>.jpg` does not exist in folder, return that name.
4. Add 1 to counter and go back to step 3.

**`handle_save(session)`**

1. If no image is loaded, return the session.
2. Make the saved_images folder if it does not exist.
3. Set default_name to _next_default_save_name(saved_images).
4. Ask for a filename, offering default_name. Pressing Enter uses default_name.
5. If the user typed a name and that file already exists, ask `<filename> already exists. Overwrite? (y/n)`. If the answer is not y, print "Save cancelled." and return the session.
6. Try to save current to the path. If that fails, print `Error: cannot save to <path>` and return the session.
7. Replace the session with mark_saved(session), print `Image saved to <path>`, and return it.

**`list_saved_images()`**

1. If the saved_images folder does not exist, return an empty list.
2. Return the folder's filenames, sorted.

**`handle_show_images()`**

1. Get the filenames from list_saved_images.
2. If there are none, print "No saved images yet." and return.
3. Print the filenames numbered.

**`handle_undo(session)`**

1. Call undo(session).
2. If it returned None, print "Error: nothing to undo" and return the session.
3. Print "Undo successful. Reverted to previous state." and return the result.

**`handle_redo(session)`**

1. Call redo(session).
2. If it returned None, print "Error: nothing to redo" and return the session.
3. Print "Redo successful." and return the result.

**`confirm_discard(session)`**

1. If there are no unsaved changes, return the session.
2. Ask "You have unsaved changes. Save before continuing? (y/n)".
3. If the answer is y: call handle_save. If the session is still unsaved, print "Save was unsuccessful. Let's try again." and go back to step 2. Otherwise return the session.
4. If the answer is n, return the session unchanged.
5. For any other answer, print "Error: please answer y or n" and go back to step 2.

**`handle_delete(session)`**

1. Read a choice of 1 (delete image) or 2 (delete a saved file).
2. If the choice is 1: set session to confirm_discard(session), print "Image session cleared.", and return clear_session().
3. If the choice is 2: get the saved filenames. If there are none, print "No saved images to delete" and return the session.
4. Print the filenames numbered and read a choice for the file.
5. Ask `Delete <file>? (y/n)` until the answer is y or n.
6. If y, try to remove the file and print `Deleted <file>` (or `Error: cannot delete <file>` on failure). If n, print "Delete cancelled".
7. Return the session unchanged.

**`main()`**

1. Set session to clear_session() and print the banner.
2. Print the main menu and read a choice from 1 to 11.
3. If the choice is 1, set session to confirm_discard(session), then set session to handle_load(session).
4. If the choice is 2, 3, 4, 5, 6, 7, 8 or 9, set session to the result of handle_filter_menu, handle_composite_menu, handle_transform_menu, handle_undo, handle_redo, handle_preview, handle_save or handle_delete.
5. If the choice is 10, call handle_show_images.
6. If the choice is 11, set session to confirm_discard(session), then print "Goodbye!" and end.
7. Go back to step 2.

## 5. Formulas used for functions

### Clamping and luminosity

Every computed channel is clamped to 0–255 before it is written (EC9). Brightness is always the luminosity-weighted value below, never a plain average.

```math
\mathrm{clamp}(v) = \min(255,\ \max(0,\ v)) \qquad L = 0.299\,R + 0.587\,G + 0.114\,B
```

### Filters

Grayscale gives every pixel the same value g in all three channels. Negative inverts each channel.

```math
g = \mathrm{clamp}(\mathrm{round}(L)) \qquad (R',G',B') = (255-R,\ 255-G,\ 255-B)
```

Sepia applies this matrix, rounds, and clamps each result:

```math
\begin{aligned}
R' &= 0.393R + 0.769G + 0.189B \\
G' &= 0.349R + 0.686G + 0.168B \\
B' &= 0.272R + 0.534G + 0.131B
\end{aligned}
```

Halftone splits the image into cell_size × cell_size cells (edge cells may be smaller). For each cell, the average luminosity B sets the radius of one black dot on a white background. Darker cells give bigger dots, up to half the cell size. A pixel is black if its distance from the cell centre is at most the radius.

```math
B = \frac{1}{n}\sum L \qquad r = \mathrm{round}\!\left(\frac{255-B}{255}\cdot\frac{\mathrm{cell\_size}}{2}\right) \qquad c = \left(\frac{left+right-1}{2},\ \frac{top+bottom-1}{2}\right)
```

### Composites

The position (x, y) is where the top-left corner of the second image lands. Only the rectangle shared by both images is processed; the position is valid only if that rectangle has at least one pixel.

```math
x_0=\max(0,x),\ y_0=\max(0,y),\ x_1=\min(W_{bg},\ x+W_{fg}),\ y_1=\min(H_{bg},\ y+H_{fg}) \qquad \text{valid if } x_1>x_0 \text{ and } y_1>y_0
```

Simple Overlay blends each channel with blend strength α (0 to 1, default 0.5). Green-Screen Key treats a foreground pixel as green when its green channel beats both other channels by more than the margin m (default 30); non-green foreground pixels replace the background, green ones are skipped.

```math
out = \mathrm{clamp}(\mathrm{round}(bg\,(1-\alpha) + fg\,\alpha)) \qquad \text{green if } G > R+m \ \text{and}\ G > B+m
```

### Transforms

For an image W wide and H tall, a pixel at (x, y) moves as follows. Rotation is clockwise; 180° is two quarter-turns and 270° is three.

```math
\text{rotate 90°: } (x,y)\to(H-1-y,\ x) \qquad \text{flip horizontal: } (x,y)\to(W-1-x,\ y) \qquad \text{flip vertical: } (x,y)\to(x,\ H-1-y)
```

### Terminal dot preview

The preview is built from Braille characters. Each character covers a 2-wide by 4-tall block of sub-dots, so the working grid is twice as wide as the requested width in characters. The height is scaled to keep the aspect ratio, then rounded down to a multiple of 4 (minimum 4).

```math
W_t = \max(2,\ 2\cdot\mathrm{chars}) \qquad H_t = 4\left\lfloor \tfrac{1}{4}\,\mathrm{round}\!\left(H\cdot\tfrac{W_t}{W}\right)\right\rfloor \text{ (at least 4)}
```

Each grid cell is the average luminosity of its block of source pixels (box filter). A cell is dark (dot on) when its value is below 128. Floyd–Steinberg dithering pushes the rounding error onto unvisited neighbours:

```math
e = v - (0 \text{ if dark else } 255) \qquad \text{right } \tfrac{7}{16}e,\ \text{below-left } \tfrac{3}{16}e,\ \text{below } \tfrac{5}{16}e,\ \text{below-right } \tfrac{1}{16}e
```

The on-dots of a block are summed into one bit mask, and the character is `chr(0x2800 + mask)`:

| Sub-dot (column, row) | Braille dot | Bit value |
| --- | --- | --- |
| (0, 0) | 1 | 0x01 |
| (0, 1) | 2 | 0x02 |
| (0, 2) | 3 | 0x04 |
| (1, 0) | 4 | 0x08 |
| (1, 1) | 5 | 0x10 |
| (1, 2) | 6 | 0x20 |
| (0, 3) | 7 | 0x40 |
| (1, 3) | 8 | 0x80 |

If the most recent operation was Negative, the preview uses the current image directly. Otherwise it uses the negative of the current image, because Braille dots print in the terminal's text colour.