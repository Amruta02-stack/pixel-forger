# ***Image Editor – Product Requirements Document (PRD)***



## 1. Problem Statement & Description

People who want a quick edit to a picture must install a full graphical editor or write throw-away scripts, and lightweight tools rarely protect against mistakes (no undo, no warning before unsaved work is lost). This product is a menu-driven Python command-line image editor: the user loads images, applies filters, combines images, transforms them, previews the result and saves it. All pixel processing is written by hand; Pillow is used only to open, hold, show and save images.

**Goals**

- Complete a load, edit, preview and save cycle from menus alone, with no documentation.
- Make editing safe: Undo/Redo (20 steps), reapply warnings and an unsaved-changes warning.
- Build a final composite from at least three source images and save it as `saved_images/result.jpg`.
- Keep processing logic free of input/output so every function can be unit tested.

**Target users:** students and hobbyists who want quick terminal edits, and developers who want a readable reference implementation of classic image algorithms.

---

## **2. User Interface**

The app runs from the command line with `python main.py`. Every choice is a whole number from the menu on screen; Filter, Composite, Transform and Preview submenus stay open until the user picks **Back**.

```python
Main Menu:
1. Load Image  2. Apply Filter  3. Apply Composite  4. Transform
5. Undo  6. Redo  7. Preview  8. Save  9. Delete  10. Show Images
11. Exit
```

| Menu | Options |
| --- | --- |
| Load Image | 1. Enter a file path · 2. Choose from saved images · 3. Back |
| Apply Filter | 1. Grayscale · 2. Negative · 3. Sepia · 4. Halftone · 5. Back |
| Apply Composite | 1. Simple Overlay · 2. Green-Screen Key · 3. Back |
| Transform | 1. Rotate · 2. Flip · 3. Back |
| Preview | 1. Open in image viewer · 2. Print dot preview in terminal · 3. Back |

| Input | Rule | Default (press Enter) |
| --- | --- | --- |
| Image path | Typed path, quotes stripped | None |
| Halftone cell size | Whole number ≥ 1 | Last used (10) |
| Overlay position | `x,y`, top-left of second image | `0,0` |
| Blend strength | Number 0–1 | 0.5 |
| Green-screen margin | Whole number ≥ 0 | Last used (30) |
| Rotation / flip | 90, 180, 270 / `h`, `v` | None |
| Preview width | Whole number ≥ 1 (characters) | Last used (67) |
| Save filename | Name with image extension | `result.jpg`, `result_1.jpg`, … |

Every action prints a confirmation (for example `Filter applied: Grayscale`, `Image saved to saved_images/result.jpg`) or a message starting with `Error:`. Confirmation prompts use `(y/n)`.

---

## **3. Functional Requirements**

**3.1 Functional requirements**

### FR1 — Load Source Images

*Priority: Must have · Edge cases: EC1, EC13, EC25*

The system shall load source images interactively. Choosing Load offers a choice between typing a file path and picking an image already in `saved_images`. Either way, the image is converted to RGB and starts a brand-new session (undo/redo history cleared, preferences reset to their defaults). If there are unsaved changes, the unsaved-changes warning (EC13) is shown first. An empty path, a missing file or a file that is not a readable image is reported and the Load menu is shown again, where the user can try another path or choose Back (EC1, EC25).

```python
Enter image path: sources/photo1.jpg
Image loaded: sources/photo1.jpg (800x600)
```

### FR2 — Apply Filters

*Priority: Must have · Edge cases: EC9, EC18, EC23*

The system shall provide Grayscale, Negative, Sepia and Halftone (Dot Pattern) filters, each implemented through manual pixel calculations. Grayscale produces a luminosity-weighted gray image, Negative inverts every colour channel, and Sepia produces a warm brown-toned image. Every filter returns a new image, leaves the original unchanged, and keeps each calculated value within 0–255 (EC9).

Halftone divides the image into square cells, calculates each cell's average brightness, and draws one black dot at the cell centre on a white background; darker cells give larger dots. The cell size must be a positive whole number (default 10), otherwise an error is shown and the prompt is repeated (EC18). The last cell size used is remembered as a session preference.

If Negative, Sepia or Halftone was the last operation applied and the user selects it again, the system asks `Continue? (y/n)` before reapplying it, because a second application compounds the effect (EC23). Declining prints `<Operation> cancelled.` and leaves the image and history unchanged. Grayscale is exempt.

```python
Choice: 2
Apply Filter:
1. Grayscale  2. Negative  3. Sepia  4. Halftone (Dot Pattern)  5. Back
Choice: 1
Filter applied: Grayscale
```

### FR3 — Apply Composite

*Priority: Must have · Edge cases: EC4, EC5, EC6, EC23, EC27, EC28*

The system shall copy or blend a second image onto the current image using manual pixel logic, chosen from Simple Overlay or Green-Screen Key. PIL's `paste()` and `merge()` are not used.

The position `(x, y)` is where the top-left corner of the second image lands. It defaults to `0,0`, must be entered as `x,y` (EC28), and may be negative. The placed image must overlap the current image by at least one pixel; otherwise `Error: overlay position is out of bounds` is shown and the user returns to the Composite menu (EC6). Only the overlapping area is processed. If the second image cannot be loaded, an error is shown, the Composite menu is shown again and no composite is applied (EC4).

Simple Overlay blends using a strength from 0 to 1 (default 0.5); values outside that range are rejected (EC5). Green-Screen Key treats the second image's predominantly green pixels as transparent; the margin must be a non-negative whole number (default 30, remembered as a session preference) and a higher margin removes fewer pixels (EC27). Selecting the same composite twice in a row asks for confirmation, as in FR2 (EC23). Composites return a new image and never modify their inputs.

```
Choice: 3
Apply Composite:
1. Simple Overlay  2. Green-Screen Key  3. Back
Choice: 1
Enter second image path: sources/photo2.jpg
Enter position (x,y) (default 0,0): 50,50
Enter blend strength (0-1): 0.7
Composite applied: Simple Overlay
```

### FR4 — Transform (Rotate & Flip)

*Priority: Must have · Edge cases: EC15*

The system shall rotate the image clockwise by 90°, 180° or 270°, and flip it horizontally (left to right) or vertically (top to bottom). Both are available from the Transform submenu and can be applied repeatedly without returning to the main menu. Any other rotation angle is rejected with an error and requested again (EC15).

### FR5 — Preview Image

*Priority: Must have · Edge cases: EC3*

The system shall show the current image in the system image viewer using the `show()` method.

### FR6 — Undo / Redo

*Priority: Should have · Edge cases: EC11, EC12*

Undo shall restore the previous image state when one exists; Redo shall restore the most recently undone state. The undo history is capped at 20 steps and the oldest state is silently discarded when the cap is exceeded. Session preferences (Halftone cell size, green-screen margin, preview width) are not part of the history.

```python
Choice: 5
Undo successful. Reverted to previous state.
Choice: 6
Redo successful.
```

### FR7 — Save Image

*Priority: Must have · Edge cases: EC14, EC20, EC24*

The system shall save the current image into the `saved_images` folder, creating it if needed. The prompt offers an auto-incrementing default name (`result.jpg`, then `result_1.jpg`, `result_2.jpg`, and so on), which advances only when the user accepts it by pressing Enter (EC20). A typed filename is used exactly as given and must include an image extension the system can save, such as `.jpg`; otherwise, or if the location cannot be written, an error is shown and nothing is saved (EC14). If a typed filename already exists, the system asks `<filename> already exists. Overwrite? (y/n)` and cancels the save on `n` (EC24). A successful save marks the session as having no unsaved changes.

```python
Choice: 8
Enter save filename in image_name.jpg (default result_2.jpg):
Image saved to saved_images/result_2.jpg
```

### FR8 — Delete / Clear Session

*Priority: Should have · Edge cases: EC13, EC21, EC22*

Choosing Delete asks whether to clear the current in-memory session or permanently delete a file from `saved_images`. Clearing the session removes the image and its history and resets preferences to their defaults. Deleting a saved file lists the files, asks `Delete <file>? (y/n)` and removes the file only on `y` (EC22); if there are no saved files, `No saved images to delete` is shown (EC21). Before Load, Delete or Exit with unsaved changes, the system warns and lets the user save first (EC13).

```python
Choice: 9
Enter (1) Delete image or (2) existing saved image? 1
You have unsaved changes. Save before continuing? (y/n): n
Image session cleared.
```

### FR9 — Produce the Final Composite

*Priority: Must have · Edge cases: EC3–EC6, EC9*

Through its menus, the program shall let the user combine at least three source images into one polished composite, and the same composite can be recreated by repeating the same menu steps on the same sources. The result is saved with FR7 (`result.jpg` by default).

### FR10 — Terminal Dot Preview

*Priority: Should have · Edge cases: EC19, EC26*

In addition to the image-viewer preview (FR5), the system shall print a black-and-white preview of the current image in the terminal using Braille characters, each encoding a 2×4 grid of sub-dots. No colour or ANSI styling is used. The preview is generated manually from the image's brightness, reduced to the requested width and dithered. It is available whenever an image is loaded, whether or not Halftone has been applied (EC19). The width must be a positive whole number (default 67, remembered as a session preference) (EC26). The preview uses the negative of the current image, since Braille dots print in the terminal's text colour, unless the last operation was Negative. Printing the preview does not save any file.

### FR11 — Show Images

*Priority: Should have · Edge cases: EC21*

The system shall list the filenames currently in `saved_images`, numbered, independent of the loaded image and unaffected by Undo, Redo or Clear Session. If none exist, it reports `No saved images yet.`

```python
Choice: 10
Saved Images:
1. result.jpg
2. result_1.jpg
```

---

## **4. Image Processing Functions**

At least six picture functions are required. Formulas are specified in the Product Design Document; the shared brightness measure is `L = 0.299R + 0.587G + 0.114B`.

| Function | Purpose | Status |
| --- | --- | --- |
| `grayscale()` | Every pixel becomes its luminosity gray. | Filter |
| `negative()` | Inverts each channel (255 minus value). | Filter |
| `sepia()` | Applies the sepia colour matrix, rounded and clamped. | Filter |
| `halftone()` | Average brightness per square cell sets the radius of one black dot on white. | Filter |
| `simple_overlay()` | Blends the second image onto the first with strength α. | Composite |
| `green_screen()` | Skips foreground pixels where G exceeds R and B by more than the margin. | Composite |
| `rotate()` | Repositions every pixel for a clockwise 90, 180 or 270 degree turn. | Transform |
| `flip_horizontal()`, `flip_vertical()` | Mirror every pixel left to right or top to bottom. | Transform |
| `braille_dots()` | Box-downsamples, dithers (Floyd–Steinberg) and encodes the image as Braille text. | Optional (FR10) |
| `is_valid_*`, `valid_region()`, `clamp()` | Validate input and keep values in range. | Supporting |

---

## **5. Edge Cases**

IDs are stable references used by the functional requirements and test cases, so gaps are intentional. EC7 and EC8 (mismatched and partly off-edge overlay sizes) are covered by EC6; EC10 was withdrawn with cropping; EC16 and EC17 (image size and format conversion) are covered under Constraints & Assumptions.

| ID | Scenario | Expected behaviour |
| --- | --- | --- |
| EC1 | Load: empty path, missing file or not an image | `Error: image path cannot be empty`, `Error: file not found`, `Error: file is not a valid image` or `Error: cannot read that file`; the Load menu is shown again. |
| EC2 | Menu choice not in the list | `Error: invalid menu choice`; ask again. |
| EC3 | Filter, composite, transform, preview or save with no image loaded | `Error: load an image first`; nothing is done. |
| EC4 | Second composite image missing or unreadable | Same error messages as EC1; the Composite menu is shown again and no composite is applied. |
| EC5 | Blend strength outside 0–1 | `Error: blend strength must be between 0 and 1`. |
| EC6 | Overlay position with no overlap, for example (900, 700) on 800 × 600 | `Error: overlay position is out of bounds`; back to the Composite menu. Partial overlap, or images of different sizes, processes only the shared pixels. |
| EC9 | A calculated channel is outside 0–255 | The value is clamped before it is written. |
| EC11 | Undo with empty history | `Error: nothing to undo`. |
| EC12 | Redo with nothing undone | `Error: nothing to redo`. |
| EC13 | Load, Delete or Exit with unsaved changes | `You have unsaved changes. Save before continuing? (y/n)`; `y` saves first (asked again if the save fails), `n` continues. |
| EC14 | Save fails: bad folder, or filename without a savable extension | `Error: cannot save to <path>`; nothing is written and the session stays unsaved. |
| EC15 | Rotation other than 90, 180 or 270 | `Error: invalid rotation`; ask again. |
| EC18 | Cell size 0, negative or not a whole number | `Error: cell size must be a positive integer`; ask again. |
| EC19 | Dot preview before Halftone is applied | A brightness-based preview is printed (or EC3 if no image). |
| EC20 | Default save accepted twice in a row | `result.jpg`, then `result_1.jpg`; typed names are never auto-incremented. |
| EC21 | Show Images or Delete with an empty `saved_images` | `No saved images yet.` / `No saved images to delete`. |
| EC22 | Delete a saved file | Ask `y/n`; `n` prints `Delete cancelled` and keeps the file. |
| EC23 | Negative, Sepia, Halftone, Simple Overlay or Green-Screen Key applied twice in a row | `Continue? (y/n)`; `n` cancels and leaves image and history unchanged. Grayscale, rotate and flip are exempt. |
| EC24 | Typed save filename already exists | `Overwrite? (y/n)`; `n` prints `Save cancelled.` and writes nothing. |
| EC25 | Load from saved images while `saved_images` is empty | `No saved images yet.`; the Load menu is shown again. |
| EC26 | Preview width 0, negative or not a whole number | `Error: width must be a positive integer`; ask again. |
| EC27 | Green-screen margin negative or not a whole number | `Error: margin must be a non-negative integer`; 0 is allowed. |
| EC28 | Position not entered as `x,y` | `Error: invalid position. Use format x,y`; ask again. |

---

## **6. Constraints, Assumptions & Scope**

**Constraints**

- Python with Pillow; Pillow only opens, holds, shows and saves images. `ImageOps`, `ImageFilter`, `paste()`, `merge()` and `resize()` are not used for pixel processing.
- Command-line only, one image session at a time; images are handled as 8-bit RGB.
- Source files are never modified; results are written only to `saved_images`.
- Edits never change an image in place; undo history holds at most 20 full copies.
- The dot preview needs a terminal and font that support Braille characters.

**Assumptions**

- Users have an interactive terminal and write access to the working directory.
- Source images are common formats Pillow can read (JPEG, PNG, BMP) and are small enough for manual pixel processing.
- A system image viewer is available for the image-viewer preview.
- History and preferences live in memory only and are lost on exit.

**In scope**

- Load by path or from `saved_images`; filters (Grayscale, Negative, Sepia, Halftone); composites (Simple Overlay, Green-Screen Key); rotate and flip.
- Image-viewer and terminal dot preview; Undo/Redo; save, list and delete saved images; clear session.
- A final composite built from at least three source images.

**Out of scope**

- Cropping, resizing or scaling; rotation by arbitrary angles.
- A graphical interface or batch processing.
- Transparency (alpha) support.
- Saving history or preferences between runs.

---

## **7. Test Cases**

Each test traces to a functional requirement (FR) or edge case (EC).

| ID | Traces to | Input / action | Expected result |
| --- | --- | --- | --- |
| TC01 | FR1 | Load each source image by typed path | `Image loaded: <path> (WxH)`; a new session starts. |
| TC02 | FR1, EC1 | Load `nonexistent.jpg`, then an empty path | `Error: file not found` / `Error: image path cannot be empty`; the Load menu is shown again. |
| TC03 | FR1, EC25 | Load from saved images, with and without saved files | Chosen file loads as a new session; with none, `No saved images yet.` and the Load menu is shown again. |
| TC04 | FR2 | Apply Grayscale, Negative and Sepia | Each result comes from manual pixel logic and the original is unchanged. |
| TC05 | FR2 | Apply Halftone with the default cell size | Black-and-white dot image; darker areas have larger dots. |
| TC06 | FR2, EC23 | Apply Negative twice in a row | `Continue? (y/n)` appears; `n` leaves image and history unchanged. |
| TC07 | FR2, EC18 | Enter Halftone cell size 0, then `abc` | Both rejected with an error and asked again; Enter accepts the default. |
| TC08 | FR3 | Simple Overlay with a second image, position `50,50`, strength 0.7 | Blended result; `Composite applied: Simple Overlay`. |
| TC09 | FR3 | Green-Screen Key with a green-background foreground | Green pixels are skipped and the background shows through. |
| TC10 | FR3, EC4 | Enter a missing second-image path | Error shown, the Composite menu is shown again, no composite applied. |
| TC11 | FR3, EC5 | Enter blend strength 2 | `Error: blend strength must be between 0 and 1`. |
| TC12 | FR3, EC6 | Position (900, 700) on an 800 × 600 image; then (−20, −20) | First is rejected as out of bounds; second blends only the overlapping area. |
| TC13 | FR3, EC27 | Enter margin −5, then 0 | −5 is rejected; 0 is accepted. |
| TC14 | FR3, EC28 | Enter position `50 50` | `Error: invalid position. Use format x,y`; asked again. |
| TC15 | FR4, EC15 | Rotate 90, 180 and 270; then enter 45 | Each turn is correct; 45 gives `Error: invalid rotation` and asks again. |
| TC16 | FR4 | Flip horizontally, then vertically | Image is mirrored left to right, then top to bottom. |
| TC17 | FR5 | Preview, option 1 | The image opens in the system image viewer. |
| TC18 | FR6 | Apply a filter, Undo, then Redo | `Undo successful. Reverted to previous state.` then `Redo successful.` |
| TC19 | FR6, EC11, EC12 | Undo with empty history; Redo with nothing undone | `Error: nothing to undo` / `Error: nothing to redo`. |
| TC20 | FR7 | Save with the typed name `myphoto.jpg` | `Image saved to saved_images/myphoto.jpg`. |
| TC21 | FR7, EC20 | Save twice, accepting the default both times | `result.jpg`, then `result_1.jpg`; the first file is not overwritten. |
| TC22 | FR7, EC24 | Save with a typed name that already exists | Overwrite prompt; `n` prints `Save cancelled.` and writes nothing. |
| TC23 | FR7, EC14 | Save with the name `photo` (no extension) | `Error: cannot save to <path>`; session stays unsaved. |
| TC24 | FR8, EC13 | Delete (clear session) with unsaved changes, answer `n` | Session cleared; main menu shows with no image loaded. |
| TC25 | FR8, EC21, EC22 | Delete a saved file and confirm; repeat with an empty folder | File is removed and no longer listed; with none, `No saved images to delete`. |
| TC26 | FR10 | Print the dot preview after Halftone, and on an un-halftoned image | Black-and-white Braille text, no colour codes, no error. |
| TC27 | FR10, EC26 | Enter preview width 0, then `abc` | Both rejected with an error and asked again; Enter accepts the default. |
| TC28 | FR11, EC21 | Show Images with and without saved files | Numbered filenames, or `No saved images yet.` |
| TC29 | FR9 | Combine three source images through the menus, then repeat the same steps | A final composite is saved; the repeat produces the same result. |
| TC30 | EC3 | Choose Apply Filter before loading an image | `Error: load an image first`; nothing is done. |
| TC31 | EC9 | A calculation gives (300, −20, 260) | Only values clamped to 0–255 are written. |
