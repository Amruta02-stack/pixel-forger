# ***I******m******a******g******e****** ******E******d******i******t******o******r*** ***Design Document | Program Design & Development***

## **1. Terminology**&#32;

### The session

The session is the one dictionary that holds everything the editor remembers. Every session function returns a NEW session and never changes the one it was given.

| Field | Meaning |
| --- | --- |
| current | The image being edited, or None when nothing is loaded |
| undo\_stack | List of (image, label) pairs, oldest first, at most 20 long (MAX\_UNDO\_STEPS) |
| redo\_stack | Same shape as undo\_stack; filled by Undo, emptied by any new edit |
| dirty | True when there are changes not yet saved |
| halftone\_cell\_size | Preference, default 10 |
| green\_margin | Preference, default 30 |
| braille\_width\_chars | Preference, default 67 |

### Labels

Each history entry carries a label naming the operation that was applied on top of the stored image. The label on the top of undo\_stack therefore names the last operation applied. The labels are: Grayscale, Negative, Sepia, Halftone, Simple Overlay, Green-Screen Key, Rotate 90 / 180 / 270, Flip Horizontal, Flip Vertical.

### Edits and preferences

An edit (filter, composite, rotate, flip) pushes a new state, clears redo\_stack and sets dirty. A preference (cell size, green margin, preview width) changes one field only: it is not undoable and does not set dirty.

### Undo cap

When undo\_stack grows past 20 entries, the oldest entry is dropped silently. This bounds memory, because every entry holds a full copy of the image.

### Reapply warning

Negative, Halftone, Sepia, Simple Overlay and Green-Screen Key change the image further when applied twice in a row. If the chosen label equals the label on top of undo\_stack, the user is asked "Continue? (y/n)" first. Grayscale, rotations and flips are exempt.

### Default save name

The default filename inside saved\_images is the first unused name in the order result.jpg, result\_1.jpg, result\_2.jpg, and so on. A filename the user types is always used exactly as given; if it already exists the user must confirm the overwrite.

## **2. Program Flow**

1. Create an empty session and print the IMAGE EDITOR banner.
2. Print the main menu.
3. Read a menu choice from 1 to 11, asking again until it is valid.
4. Run the handler for that choice and replace the session with what it returns:
   1. Load Image: if there are unsaved changes, run the discard warning first; then load by typed path or from saved\_images and start a brand-new session. If a load fails, the Load menu is shown again; Back returns to the main menu.
   2. Apply Filter: Grayscale, Negative, Sepia, or Halftone, then push the result onto the history.
   3. Apply Composite: Simple Overlay or Green-Screen Key, then push the result onto the history.
   4. Transform: Rotate or Flip, then push the result onto the history.
   5. Undo: restore the previous state, or report there is nothing to undo.
   6. Redo: restore the undone state, or report there is nothing to redo.
   7. Preview: open the image viewer or print the Braille dot preview.
   8. Save: write the current image into saved\_images and mark the session saved.
   9. Delete: clear the session, or delete a saved file.
   10. Show Images: list the files in saved\_images.
   11. Exit: if there are unsaved changes, run the discard warning first; then print Goodbye! and stop.
5. Options 2, 3, 4 and 7 stay inside their own submenu, so several operations can be applied in a row, until the user chooses Back.
6. Options 2, 3, 4, 7 and 8 print "Error: load an image first" and do nothing when no image is loaded.
7. Unless the user exited in step 4, go back to step 2.
8. End.

## **3. Function Signatures**

The code is split in three files: image\_ops.py (pure picture functions and validators, no input or output), session.py (pure history and preference functions), and main.py (menus, prompts and file handling). Image means PIL's Image.Image. session.py imports the green margin and preview width defaults (30 and 67) from image\_ops.py, so each default is defined in one place.

### image\_ops.py

| Functions | What it's for |
| --- | --- |
| def clamp(value: int) -> int: | Restricts a channel value to 0–255. |
| def \_luminosity(r: int, g: int, b: int) -> float: | Returns the luminosity-weighted brightness of one pixel, unrounded. |
| def grayscale(image: Image) -> Image: | Returns a new image where every pixel is its luminosity gray. |
| def negative(image: Image) -> Image: | Returns a new image with every channel inverted. |
| def sepia(image: Image) -> Image: | Returns a new image with the sepia matrix applied, clamped. |
| def is\_valid\_cell\_size(text: str) -> bool: | Returns True if the text is a whole number of 1 or more. |
| def halftone(image: Image, cell\_size: int) -> Image: | Returns a new black-and-white dot-pattern image, one dot per cell. |
| def is\_valid\_braille\_width(text: str) -> bool: | Returns True if the text is a whole number of 1 or more. |
| def \_box\_downsample\_luminosity(image: Image, target\_width: int, target\_height: int) -> list: | Shrinks the image by hand to a grid of average luminosity per cell. |
| def \_floyd\_steinberg\_dither(grid: list, width: int, height: int) -> list: | Turns a luminosity grid into a grid of on/off dots with error diffusion. |
| def braille\_dots(image: Image, max\_width\_chars: int = 67) -> str: | Returns the image as multi-line Braille text for the terminal preview. |
| def is\_valid\_green\_margin(text: str) -> bool: | Returns True if the text is a whole number of 0 or more. |
| def is\_green\_pixel(r: int, g: int, b: int, margin: int = 30) -> bool: | Returns True if the pixel counts as keyed green. |
| def valid\_region(bg\_w: int, bg\_h: int, fg\_w: int, fg\_h: int, x: int, y: int) -> tuple: | Returns (x0, y0, x1, y1), the rectangle both images share. |
| def is\_valid\_position(bg\_w: int, bg\_h: int, fg\_w: int, fg\_h: int, x: int, y: int) -> bool: | Returns True if the placed foreground overlaps the background by at least one pixel. |
| def is\_valid\_blend\_strength(text: str) -> bool: | Returns True if the text is a number from 0 to 1 inclusive. |
| def simple\_overlay(background: Image, foreground: Image, x: int, y: int, alpha: float) -> Image: | Returns a new image with the foreground blended onto the background. |
| def green\_screen(background: Image, foreground: Image, x: int, y: int, margin: int = 30) -> Image: | Returns a new image with the non-green foreground pixels placed over the background. |
| def \_rotate\_90(image: Image) -> Image: | Returns a new image turned one quarter-turn clockwise. |
| def is\_valid\_rotation(degrees: int) -> bool: | Returns True only for 90, 180 or 270. |
| def rotate(image: Image, degrees: int) -> Image: | Returns a new image rotated clockwise by 90, 180 or 270 degrees. |
| def flip\_horizontal(image: Image) -> Image: | Returns a new image mirrored left to right. |
| def flip\_vertical(image: Image) -> Image: | Returns a new image mirrored top to bottom. |

### session.py

| Functions | What it's for |
| --- | --- |
| def new\_session(image: Image) -> dict: | Returns the starting session for a freshly loaded image. |
| def push\_state(session: dict, image: Image, label: str) -> dict: | Returns a new session with the new image as current and the old one pushed onto undo\_stack. |
| def undo(session: dict) -> dict \| None: | Returns a new session one step back, or None if there is nothing to undo. |
| def redo(session: dict) -> dict \| None: | Returns a new session one step forward, or None if there is nothing to redo. |
| def mark\_saved(session: dict) -> dict: | Returns a new session with dirty set to False. |
| def has\_unsaved\_changes(session: dict) -> bool: | Returns the dirty flag. |
| def set\_cell\_size(session: dict, cell\_size: int) -> dict: | Returns a new session with the Halftone cell size preference updated. |
| def set\_green\_margin(session: dict, margin: int) -> dict: | Returns a new session with the green margin preference updated. |
| def set\_braille\_width(session: dict, width\_chars: int) -> dict: | Returns a new session with the preview width preference updated. |
| def clear\_session() -> dict: | Returns a fresh empty session with default preferences. |

### main.py

| Functions | What it's for |
| --- | --- |
| def load\_image() -> Image: | Asks for an image path once and returns the image, or None if the path is empty or cannot be opened. |
| def load\_image\_from\_saved() -> Image \| None: | Lists saved images and returns the chosen one, or None if there are none or the user backs out. |
| def handle\_load(session: dict) -> dict: | Runs the Load submenu and returns a brand-new session, or the same session if the user backs out. |
| def render\_menu(session: dict) -> str: | Returns the main menu text. |
| def require\_loaded\_image(session: dict) -> bool: | Returns True if an image is loaded; otherwise prints the error and returns False. |
| def confirm\_reapply(session: dict, label: str) -> bool: | Asks for confirmation if the same compounding operation was just applied; returns True to go ahead. |
| def read\_menu\_choice(valid: set, prompt: str = "Choice: ") -> int: | Reads a whole number until it is in the valid set. |
| def handle\_filter\_menu(session: dict) -> dict: | Runs the Filter submenu and returns the updated session. |
| def handle\_composite\_menu(session: dict) -> dict: | Runs the Composite submenu and returns the updated session. |
| def handle\_transform\_menu(session: dict) -> dict: | Runs the Transform submenu and returns the updated session. |
| def handle\_preview(session: dict) -> dict: | Runs the Preview submenu and returns the updated session. |
| def \_next\_default\_save\_name(folder: str) -> str: | Returns the first unused name among result.jpg, result\_1.jpg, and so on. |
| def handle\_save(session: dict) -> dict: | Saves the current image into saved\_images and returns the updated session. |
| def list\_saved\_images() -> list: | Returns the sorted filenames in saved\_images, possibly empty. |
| def handle\_show\_images() -> None: | Prints the saved filenames numbered, or says there are none. |
| def handle\_undo(session: dict) -> dict: | Undoes one step and prints the result. |
| def handle\_redo(session: dict) -> dict: | Redoes one step and prints the result. |
| def confirm\_discard(session: dict) -> dict: | Warns about unsaved changes, saves first if the user says y, and returns the session (marked saved if the save worked). |
| def handle\_delete(session: dict) -> dict: | Clears the session or deletes a saved file, as chosen. |
| def main() -> None: | Runs the menu loop until the user exits. |

## **4. Function-Level Algorithm**

### image\_ops.py

**clamp(value)**

1. If value is below 0, return 0.
2. If value is above 255, return 255.
3. Return value.

**\_luminosity(r, g, b)**

1. Return 0.299 × r + 0.587 × g + 0.114 × b.

**grayscale(image)**

1. Convert image to RGB, read its width and height, and make a new blank RGB image of the same size.
2. For each row y, then each column x:
3. Read (r, g, b) at (x, y).
4. Set gray to clamp(round(\_luminosity(r, g, b))).
5. Write (gray, gray, gray) to the new image at (x, y).
6. Return the new image.

**negative(image)**

1. Convert image to RGB and make a new blank RGB image of the same size.
2. For each pixel (x, y), read (r, g, b).
3. Write (255 − r, 255 − g, 255 − b) to the new image at (x, y).
4. Return the new image.

**sepia(image)**

1. Convert image to RGB and make a new blank RGB image of the same size.
2. For each pixel (x, y), read (r, g, b).
3. Set new\_r to clamp(round(0.393r + 0.769g + 0.189b)).
4. Set new\_g to clamp(round(0.349r + 0.686g + 0.168b)).
5. Set new\_b to clamp(round(0.272r + 0.534g + 0.131b)).
6. Write (new\_r, new\_g, new\_b) to the new image at (x, y).
7. Return the new image.

**is\_valid\_cell\_size(text)**

1. Try to convert text to a whole number; if that fails, return False.
2. Return True if the number is at least 1, otherwise False.

**halftone(image, cell\_size)**

1. Convert image to RGB and make a new RGB image of the same size, filled white.
2. For each cell, stepping down by cell\_size rows and across by cell\_size columns:
3. Set the cell's bottom and right edges to the cell size, cut off at the image edge.
4. Add \_luminosity of every pixel inside the cell and count the pixels.
5. Set brightness to the total divided by the count (255 if the count is 0).
6. Set radius to round((255 − brightness) / 255 × cell\_size / 2).
7. Set the centre to the middle of the cell, ((left + right − 1) / 2, (top + bottom − 1) / 2).
8. If radius is greater than 0, write black to every pixel in the cell whose distance from the centre is at most radius.
9. Return the new image.

**is\_valid\_braille\_width(text)**

1. Try to convert text to a whole number; if that fails, return False.
2. Return True if the number is at least 1, otherwise False.

**\_box\_downsample\_luminosity(image, target\_width, target\_height)**

1. Convert image to RGB and make an empty target\_height × target\_width grid.
2. For each target cell (tx, ty):
3. Set y0 to ty × source\_height // target\_height, and y1 to the larger of y0 + 1 and (ty + 1) × source\_height // target\_height.
4. Set x0 and x1 the same way using the widths.
5. Set the cell to the average \_luminosity of the source pixels in x0..x1 by y0..y1.
6. Return the grid.

**\_floyd\_steinberg\_dither(grid, width, height)**

1. Copy the grid into work, so the caller's grid is not changed, and make an all-False grid called on.
2. For each row y, then each column x:
3. Set old\_value to work\[y\]\[x\].
4. Set dark to True if old\_value is below 128, and store it in on\[y\]\[x\].
5. Set error to old\_value minus 0 if dark, or minus 255 if not.
6. Add error × 7/16 to the pixel on the right, if it exists.
7. If a row below exists, add error × 3/16 to the pixel below-left (if it exists), × 5/16 to the pixel below, and × 1/16 to the pixel below-right (if it exists).
8. Return on.

**braille\_dots(image, max\_width\_chars)**

1. Convert image to RGB and read its width and height.
2. Set target\_width to the larger of 2 and max\_width\_chars × 2.
3. Set target\_height to the larger of 4 and round(source\_height × target\_width / source\_width), then round it down to a multiple of 4 (use 4 if that gives 0).
4. Call \_box\_downsample\_luminosity to get the luminosity grid.
5. Call \_floyd\_steinberg\_dither on that grid to get the on/off dots.
6. For each block of 4 rows, and within it each block of 2 columns:
7. Set bitmask to 0.
8. For each of the 8 sub-dot positions, skip it if it lies past the grid edge; otherwise, if its dot is on, add its bit value to bitmask.
9. Add the character chr(0x2800 + bitmask) to the current row.
10. Join each row's characters into a line, join the lines with newlines, and return the text.

**is\_valid\_green\_margin(text)**

1. Try to convert text to a whole number; if that fails, return False.
2. Return True if the number is at least 0, otherwise False.

**is\_green\_pixel(r, g, b, margin)**

1. Return True if g is greater than r + margin and g is greater than b + margin; otherwise return False.

**valid\_region(bg\_w, bg\_h, fg\_w, fg\_h, x, y)**

1. Set x0 to the larger of 0 and x, and y0 to the larger of 0 and y.
2. Set x1 to the smaller of bg\_w and x + fg\_w, and y1 to the smaller of bg\_h and y + fg\_h.
3. Return (x0, y0, x1, y1).

**is\_valid\_position(bg\_w, bg\_h, fg\_w, fg\_h, x, y)**

1. Call valid\_region to get (x0, y0, x1, y1).
2. Return True if x1 > x0 and y1 > y0, otherwise False.

**is\_valid\_blend\_strength(text)**

1. Try to convert text to a decimal number; if that fails, return False.
2. Return True if the number is from 0 to 1 inclusive, otherwise False.

**simple\_overlay(background, foreground, x, y, alpha)**

1. Convert both images to RGB and make out as a copy of the background.
2. Call valid\_region to get the shared rectangle.
3. For each background pixel (bx, by) inside that rectangle:
4. Find the matching foreground pixel at (bx − x, by − y).
5. For each of the three channels, write clamp(round(bg × (1 − alpha) + fg × alpha)) into out.
6. Return out.

**green\_screen(background, foreground, x, y, margin)**

1. Convert both images to RGB and make out as a copy of the background.
2. Call valid\_region to get the shared rectangle.
3. For each background pixel (bx, by) inside that rectangle:
4. Read the matching foreground pixel (r, g, b) at (bx − x, by − y).
5. If is\_green\_pixel(r, g, b, margin) is False, write (r, g, b) into out at (bx, by).
6. Return out.

**\_rotate\_90(image)**

1. Read the width and height and make a new RGB image of size height × width.
2. For each pixel (x, y), write it to the new image at (height − 1 − y, x).
3. Return the new image.

**is\_valid\_rotation(degrees)**

1. Return True if degrees is 90, 180 or 270, otherwise False.

**rotate(image, degrees)**

1. Convert image to RGB.
2. Set turns to 1 for 90, 2 for 180, or 3 for 270.
3. Repeat turns times: replace the result with \_rotate\_90 of the result.
4. Return the result.

**flip\_horizontal(image)**

1. Convert image to RGB and make a new RGB image of the same size.
2. For each pixel (x, y), write it to the new image at (width − 1 − x, y).
3. Return the new image.

**flip\_vertical(image)**

1. Convert image to RGB and make a new RGB image of the same size.
2. For each pixel (x, y), write it to the new image at (x, height − 1 − y).
3. Return the new image.

### session.py

**new\_session(image)**

1. Return a session with current set to image, empty undo\_stack and redo\_stack, dirty False, and the three preferences at their defaults (10, 30, 67).

**push\_state(session, image, label)**

1. Make new\_undo\_stack from undo\_stack plus the pair (current, label).
2. If new\_undo\_stack has more than 20 entries, keep only the newest 20.
3. Return a copy of the session with current set to image, undo\_stack set to new\_undo\_stack, redo\_stack emptied, and dirty True. Preferences are unchanged.

**undo(session)**

1. If undo\_stack is empty, return None.
2. Take the last pair (prev\_image, label) from undo\_stack.
3. Return a copy of the session with current set to prev\_image, that pair removed from undo\_stack, the pair (old current, label) added to redo\_stack, and dirty True.

**redo(session)**

1. If redo\_stack is empty, return None.
2. Take the last pair (next\_image, label) from redo\_stack.
3. Return a copy of the session with current set to next\_image, that pair removed from redo\_stack, the pair (old current, label) added to undo\_stack, and dirty True.

**mark\_saved(session)**

1. Return a copy of the session with dirty set to False.

**has\_unsaved\_changes(session)**

1. Return session\["dirty"\].

**set\_cell\_size(session, cell\_size)**

1. Return a copy of the session with halftone\_cell\_size set to cell\_size. Nothing else changes.

**set\_green\_margin(session, margin)**

1. Return a copy of the session with green\_margin set to margin. Nothing else changes.

**set\_braille\_width(session, width\_chars)**

1. Return a copy of the session with braille\_width\_chars set to width\_chars. Nothing else changes.

**clear\_session()**

1. Return a session with current set to None, empty undo\_stack and redo\_stack, dirty False, and the three preferences at their defaults.

### main.py

**read\_menu\_choice(valid, prompt)**

1. Read a line of text with the prompt.
2. If it is not a whole number, print "Error: invalid menu choice" and go back to step 1.
3. If the number is not in valid, print the same error and go back to step 1.
4. Return the number.

**require\_loaded\_image(session)**

1. If current is None, print "Error: load an image first" and return False.
2. Return True.

**render\_menu(session)**

1. Return the main menu text.

**confirm\_reapply(session, label)**

1. If label is not Negative, Halftone, Sepia, Simple Overlay or Green-Screen Key, return True.
2. If undo\_stack is empty, or the label on its top entry is not label, return True.
3. Ask "\<label> was just applied — applying it again will change the image (not just remove it). Continue? (y/n)".
4. If the answer is not y, print "\<label> cancelled." and return False.
5. Return True.

**load\_image()**

1. Ask for an image path, trim it, and remove any surrounding quote marks.
2. If it is empty, print "Error: image path cannot be empty" and return None.
3. Try to open it, load the pixels and convert to RGB. If that fails, print "Error: file not found", "Error: file is not a valid image" or "Error: cannot read that file" (whichever applies) and return None.
4. Print "Image loaded: \<path> (\<width>x\<height>)" and return the image.

**load\_image\_from\_saved()**

1. Get the filenames from list\_saved\_images.
2. If there are none, print "No saved images yet." and return None.
3. Print the filenames numbered, followed by a Back option numbered one higher.
4. Read a choice. If it is Back, return None.
5. Try to open the chosen file in saved\_images and convert to RGB. If that fails, print "Error: cannot load \<path>" and return None.
6. Print "Image loaded: \<path> (\<width>x\<height>)" and return the image.

**handle\_load(session)**

1. Print the Load menu and read a choice from 1 to 3.
2. If the choice is 3, return the session unchanged.
3. If the choice is 1, call load\_image; otherwise call load\_image\_from\_saved.
4. If no image came back, go back to step 1 (the Load menu is shown again).
5. Return new\_session(image).

**handle\_filter\_menu(session)**

1. If no image is loaded, return the session.
2. Print the Filter menu and read a choice from 1 to 5.
3. If the choice is 5, return the session.
4. For choices 1 to 3, call grayscale, negative or sepia on current and set the label to Grayscale, Negative or Sepia.
5. For choice 4, ask for a cell size, offering the stored preference as the default. Pressing Enter keeps the default; a value that fails is\_valid\_cell\_size prints "Error: cell size must be a positive integer" and asks again.
6. Store the cell size with set\_cell\_size, call halftone on current, and set the label to Halftone.
7. If confirm\_reapply returns False, go back to step 2.
8. Replace the session with push\_state(session, new\_image, label).
9. Print "Filter applied: \<label>" and go back to step 2.

**handle\_composite\_menu(session)**

1. If no image is loaded, return the session.
2. Print the Composite menu and read a choice from 1 to 3. If it is 3, return the session.
3. Ask for the second image path once. If it cannot be opened, print "Error: file not found", "Error: file is not a valid image" or "Error: cannot read that file" (whichever applies) and go back to step 2.
4. Ask for the position as x,y. Pressing Enter gives 0,0; text that is not two whole numbers separated by a comma prints "Error: invalid position. Use format x,y" and asks again.
5. If is\_valid\_position is False, print "Error: overlay position is out of bounds" and go back to step 2.
6. If the choice is Simple Overlay: ask for blend strength (Enter gives 0.5; reject values failing is\_valid\_blend\_strength with "Error: blend strength must be between 0 and 1"), then call simple\_overlay and set the label to Simple Overlay.
7. Otherwise (Green-Screen Key): ask for the margin, offering the stored preference as the default (reject values failing is\_valid\_green\_margin with "Error: margin must be a non-negative integer"), store it with set\_green\_margin, call green\_screen, and set the label to Green-Screen Key.
8. If confirm\_reapply returns False, go back to step 2.
9. Replace the session with push\_state(session, new\_image, label).
10. Print "Composite applied: \<label>" and go back to step 2.

**handle\_transform\_menu(session)**

1. If no image is loaded, return the session.
2. Print the Transform menu and read a choice from 1 to 3. If it is 3, return the session.
3. If the choice is Rotate: ask for 90, 180 or 270 until the answer is a whole number that passes is\_valid\_rotation ("Error: invalid rotation" otherwise), call rotate, and set the label to "Rotate \<degrees>".
4. If the choice is Flip: ask for h or v until one is entered ("Error: enter h or v" otherwise), call flip\_horizontal or flip\_vertical, and set the label to Flip Horizontal or Flip Vertical.
5. Replace the session with push\_state(session, new\_image, label).
6. Print the success message and go back to step 2.

**handle\_preview(session)**

1. If no image is loaded, return the session.
2. Print the Preview menu and read a choice from 1 to 3. If it is 3, return the session.
3. If the choice is 1, show the current image in the image viewer and go back to step 2.
4. If the label on top of undo\_stack is Negative, use current as the preview image; otherwise use negative(current).
5. Ask for the width in characters, offering the stored preference as the default (reject values failing is\_valid\_braille\_width with "Error: width must be a positive integer").
6. Store the width with set\_braille\_width, then print braille\_dots(preview image, width).
7. Go back to step 2.

**\_next\_default\_save\_name(folder)**

1. If result.jpg does not exist in folder, return "result.jpg".
2. Set counter to 1.
3. If result\_\<counter>.jpg does not exist in folder, return that name.
4. Add 1 to counter and go back to step 3.

**handle\_save(session)**

1. If no image is loaded, return the session.
2. Make the saved\_images folder if it does not exist.
3. Set default\_name to \_next\_default\_save\_name(saved\_images).
4. Ask for a filename, offering default\_name. Pressing Enter uses default\_name.
5. If the user typed a name and that file already exists, ask "\<filename> already exists. Overwrite? (y/n)". If the answer is not y, print "Save cancelled." and return the session.
6. Try to save current to the path. If that fails, print "Error: cannot save to \<path>" and return the session.
7. Replace the session with mark\_saved(session), print "Image saved to \<path>", and return it.

**list\_saved\_images()**

1. If the saved\_images folder does not exist, return an empty list.
2. Return the folder's filenames, sorted.

**handle\_show\_images()**

1. Get the filenames from list\_saved\_images.
2. If there are none, print "No saved images yet." and return.
3. Print the filenames numbered.

**handle\_undo(session)**

1. Call undo(session).
2. If it returned None, print "Error: nothing to undo" and return the session.
3. Print "Undo successful. Reverted to previous state." and return the result.

**handle\_redo(session)**

1. Call redo(session).
2. If it returned None, print "Error: nothing to redo" and return the session.
3. Print "Redo successful." and return the result.

**confirm\_discard(session)**

1. If there are no unsaved changes, return the session.
2. Ask "You have unsaved changes. Save before continuing? (y/n)".
3. If the answer is y: call handle\_save. If the session is still unsaved, print "Save was unsuccessful. Let's try again." and go back to step 2. Otherwise return the session.
4. If the answer is n, return the session unchanged.
5. For any other answer, print "Error: please answer y or n" and go back to step 2.

**handle\_delete(session)**

1. Read a choice of 1 (delete image) or 2 (delete a saved file).
2. If the choice is 1: set session to confirm\_discard(session), print "Image session cleared.", and return clear\_session().
3. If the choice is 2: get the saved filenames. If there are none, print "No saved images to delete" and return the session.
4. Print the filenames numbered and read a choice for the file.
5. Ask "Delete \<file>? (y/n)" until the answer is y or n.
6. If y, try to remove the file and print "Deleted \<file>" (or "Error: cannot delete \<file>" on failure). If n, print "Delete cancelled".
7. Return the session unchanged.

**main()**

1. Set session to clear\_session() and print the banner.
2. Print the main menu and read a choice from 1 to 11.
3. If the choice is 1, set session to confirm\_discard(session), then set session to handle\_load(session).
4. If the choice is 2, 3, 4, 5, 6, 7, 8 or 9, set session to the result of handle\_filter\_menu, handle\_composite\_menu, handle\_transform\_menu, handle\_undo, handle\_redo, handle\_preview, handle\_save or handle\_delete.
5. If the choice is 10, call handle\_show\_images.
6. If the choice is 11, set session to confirm\_discard(session), then print "Goodbye!" and end.
7. Go back to step 2.

## **5****.****Formulas**** **

### Clamping and luminosity

Every computed channel is clamped to 0–255 before it is written (EC9). Brightness is always the luminosity-weighted value below, never a plain average.

```latex
\mathrm{clamp}(v) = \min(255,\ \max(0,\ v)) \qquad L = 0.299\,R + 0.587\,G + 0.114\,B
```

### Filters

Grayscale gives every pixel the same value g in all three channels. Negative inverts each channel.

```latex
g = \mathrm{clamp}(\mathrm{round}(L)) \qquad (R',G',B') = (255-R,\ 255-G,\ 255-B)
```

Sepia applies this matrix, rounds, and clamps each result:

```latex
\begin{aligned}
R' &= 0.393R + 0.769G + 0.189B \\
G' &= 0.349R + 0.686G + 0.168B \\
B' &= 0.272R + 0.534G + 0.131B
\end{aligned}
```

Halftone splits the image into cell\_size × cell\_size cells (edge cells may be smaller). For each cell, the average luminosity B sets the radius of one black dot on a white background. Darker cells give bigger dots, up to half the cell size. A pixel is black if its distance from the cell centre is at most the radius.

```latex
B = \frac{1}{n}\sum L \qquad r = \mathrm{round}\!\left(\frac{255-B}{255}\cdot\frac{\mathrm{cell\_size}}{2}\right) \qquad c = \left(\frac{left+right-1}{2},\ \frac{top+bottom-1}{2}\right)
```

### Composites

The position (x, y) is where the top-left corner of the second image lands. Only the rectangle shared by both images is processed; the position is valid only if that rectangle has at least one pixel.

```latex
x_0=\max(0,x),\ y_0=\max(0,y),\ x_1=\min(W_{bg},\ x+W_{fg}),\ y_1=\min(H_{bg},\ y+H_{fg}) \qquad \text{valid if } x_1>x_0 \text{ and } y_1>y_0
```

Simple Overlay blends each channel with blend strength α (0 to 1, default 0.5). Green-Screen Key treats a foreground pixel as green when its green channel beats both other channels by more than the margin m (default 30); non-green foreground pixels replace the background, green ones are skipped.

```latex
out = \mathrm{clamp}(\mathrm{round}(bg\,(1-\alpha) + fg\,\alpha)) \qquad \text{green if } G > R+m \ \text{and}\ G > B+m
```

### Transforms

For an image W wide and H tall, a pixel at (x, y) moves as follows. Rotation is clockwise; 180° is two quarter-turns and 270° is three.

```latex
\text{rotate 90°: } (x,y)\to(H-1-y,\ x) \qquad \text{flip horizontal: } (x,y)\to(W-1-x,\ y) \qquad \text{flip vertical: } (x,y)\to(x,\ H-1-y)
```

### Terminal dot preview

The preview is built from Braille characters. Each character covers a 2-wide by 4-tall block of sub-dots, so the working grid is twice as wide as the requested width in characters. The height is scaled to keep the aspect ratio, then rounded down to a multiple of 4 (minimum 4).

```latex
W_t = \max(2,\ 2\cdot\mathrm{chars}) \qquad H_t = 4\left\lfloor \tfrac{1}{4}\,\mathrm{round}\!\left(H\cdot\tfrac{W_t}{W}\right)\right\rfloor \text{ (at least 4)}
```

Each grid cell is the average luminosity of its block of source pixels (box filter). A cell is dark (dot on) when its value is below 128. Floyd–Steinberg dithering pushes the rounding error onto unvisited neighbours:

```latex
e = v - (0 \text{ if dark else } 255) \qquad \text{right } \tfrac{7}{16}e,\ \text{below-left } \tfrac{3}{16}e,\ \text{below } \tfrac{5}{16}e,\ \text{below-right } \tfrac{1}{16}e
```

The on-dots of a block are summed into one bit mask, and the character is chr(0x2800 + mask):

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
