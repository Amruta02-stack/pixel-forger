"""
 image_ops.py - functional core.

 Every function here is PURE: it takes an Image (and whatever
 parameters it needs) as arguments and returns a NEW image or value.
 No input(), no print(), no file access, no in-place mutation of the
 image passed in. This is the file the design doc calls out as
 unit-testable.

 Pixel access goes through getpixel()/putpixel()-style manual loops
 rather than PIL's convenience filters (ImageOps, ImageFilter, etc.),
 so the manual-calculation requirement (FR2/FR3) is met even though
 PIL.Image is used as the pixel container.
 """

import math

from PIL import Image


# ---------------------------------------------------------------------------
# Clamping
# ---------------------------------------------------------------------------

def clamp(value: int) -> int:
    """Restrict a computed channel value to the closed range 0-255 (EC9)."""
    if value < 0:
        return 0
    if value > 255:
        return 255
    return value


def _luminosity(r: int, g: int, b: int) -> float:
     """Luminosity-weighted brightness of one pixel (unrounded)."""
     return 0.299 * r + 0.587 * g + 0.114 * b


 # ---------------------------------------------------------------------------
 # FR2 - Filters
 # ---------------------------------------------------------------------------

def grayscale(image: Image.Image) -> Image.Image:
    """Return a NEW image with every pixel replaced by its luminosity gray."""
    src = image.convert("RGB")
    width, height = src.size
    out = Image.new("RGB", (width, height))
    src_px, out_px = src.load(), out.load()

    for y in range(height):
        for x in range(width):
            r, g, b = src_px[x, y]
            gray = clamp(round(_luminosity(r, g, b)))
            out_px[x, y] = (gray, gray, gray)
    return out


def negative(image: Image.Image) -> Image.Image:
    """Return a NEW image with every channel of every pixel inverted."""
    src = image.convert("RGB")
    width, height = src.size
    out = Image.new("RGB", (width, height))
    src_px, out_px = src.load(), out.load()

    for y in range(height):
        for x in range(width):
           r, g, b = src_px[x, y]
           out_px[x, y] = (255 - r, 255 - g, 255 - b)
    return out


def sepia(image: Image.Image) -> Image.Image:
    """Return a NEW image with the sepia matrix applied per pixel, clamped."""
    src = image.convert("RGB")
    width, height = src.size
    out = Image.new("RGB", (width, height))
    src_px, out_px = src.load(), out.load()

    for y in range(height):
        for x in range(width):
            r, g, b = src_px[x, y]
            new_r = clamp(round(0.393 * r + 0.769 * g + 0.189 * b))
            new_g = clamp(round(0.349 * r + 0.686 * g + 0.168 * b))
            new_b = clamp(round(0.272 * r + 0.534 * g + 0.131 * b))
            out_px[x, y] = (new_r, new_g, new_b)
    return out


def is_valid_cell_size(text: str) -> bool:
    """True if text parses as a positive integer (EC19)."""
    try:
        value = int(text)
    except (TypeError, ValueError):
        return False
    return value >= 1


def halftone(image: Image.Image, cell_size: int) -> Image.Image:
    """
    Return a NEW black-and-white dot-pattern image. The image is
    divided into cell_size x cell_size cells; each cell's average
    brightness sets the radius of a single black dot drawn at its
    center (darker cells -> bigger dots, up to half the cell size).

    cell_size is assumed already validated by is_valid_cell_size
    before this is called (EC19). The last row/column of cells may be
    smaller than cell_size x cell_size when the dimensions don't
    divide evenly; only pixels actually inside the image are read.
    """
    src = image.convert("RGB")
    width, height = src.size
    src_px = src.load()
    out = Image.new("RGB", (width, height), (255, 255, 255))
    out_px = out.load()

    for cell_top in range(0, height, cell_size):

        cell_bottom = min(cell_top + cell_size, height)

        for cell_left in range(0, width, cell_size):
            cell_right = min(cell_left + cell_size, width)

            total = 0.0
            count = 0
            for y in range(cell_top, cell_bottom):
                for x in range(cell_left, cell_right):
                    r, g, b = src_px[x, y]
                    total += _luminosity(r, g, b)
                    count += 1
            brightness = total / count if count else 255.0

            radius = round((255 - brightness) / 255 * (cell_size / 2))
            center_x = (cell_left + cell_right - 1) / 2
            center_y = (cell_top + cell_bottom - 1) / 2

            if radius > 0:
                for y in range(cell_top, cell_bottom):
                    for x in range(cell_left, cell_right):
                        if math.hypot(x - center_x, y - center_y) <= radius:
                            out_px[x, y] = (0, 0, 0)
    return out


# ---------------------------------------------------------------------------
# FR10 - Terminal Braille dot preview
# ---------------------------------------------------------------------------

_BRAILLE_BASE = 0x2800
# Standard Unicode Braille dot numbering mapped onto a 2 (wide) x 4
# (tall) sub-pixel block: column, row -> bit.
_BIT_FOR_OFFSET = {
    (0, 0): 0x01,  # dot 1
    (0, 1): 0x02,  # dot 2
    (0, 2): 0x04,  # dot 3
    (0, 3): 0x40,  # dot 7
    (1, 0): 0x08,  # dot 4
    (1, 1): 0x10,  # dot 5
    (1, 2): 0x20,  # dot 6
    (1, 3): 0x80,  # dot 8
}
_BRIGHTNESS_THRESHOLD = 128  # below this luminosity, a sub-dot is "on"

# Default output width in Braille characters. Chosen to sit safely
# inside a normal terminal window (most terminals default to 80
# columns) without the caller having to know or query anything about
# the terminal itself.
DEFAULT_BRAILLE_WIDTH_CHARS = 67


def is_valid_braille_width(text: str) -> bool:
    """True if text parses as a positive integer character width."""
    try:
        value = int(text)
    except (TypeError, ValueError):
        return False
    return value >= 1



def _box_downsample_luminosity(image: Image.Image, target_width: int, target_height: int)-> list : 
    """
    Manually resize image down to (target_width, target_height),
    returning a 2D list (row-major) of average luminosity per output
    pixel. Each output pixel is the average of every source pixel that
    falls inside its block (a box filter) - implemented by hand since
    PIL's resize() is a convenience function that is out of scope here.

    Averaging a block is what actually fixes moire: if the source
    image already has its own dot pattern (e.g. after Halftone has
    been applied), averaging a whole block of it back down smooths it
    into continuous gray, so the Braille sampling below has clean
    brightness data instead of a second dot grid to fight against.
    """
    src = image.convert("RGB")
    src_w, src_h = src.size
    src_px = src.load()

    grid = [[0.0] * target_width for _ in range(target_height)]

    for ty in range(target_height):
        y0 = ty * src_h // target_height
        y1 = max(y0 + 1, (ty + 1) * src_h // target_height)
        for tx in range(target_width):
            x0 = tx * src_w // target_width
            x1 = max(x0 + 1, (tx + 1) * src_w // target_width)

            total = 0.0
            count = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b = src_px[x, y]
                    total += _luminosity(r, g, b)
                    count += 1
            grid[ty][tx] = total / count if count else 255.0
    return grid


def _floyd_steinberg_dither(grid, width: int, height: int):
    """
    Return a NEW 2D list of booleans (True = dot "on") produced by
    Floyd-Steinberg error-diffusion dithering over a luminosity grid.

    Each pixel is thresholded to on/off same as before, but the
    rounding error that introduces is pushed onto the neighbours that
    haven't been visited yet (right, and the row below), weighted
    7/16, 3/16, 5/16, 1/16. Spreading the error like this makes smooth
    gradients read as dot texture instead of hard blotches.
    """
    work = [row[:] for row in grid]  # don't mutate the caller's grid
    on = [[False] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            old_value = work[y][x]
            dark = old_value < _BRIGHTNESS_THRESHOLD
            on[y][x] = dark
            error = old_value - (0.0 if dark else 255.0)

            if x + 1 < width:
                work[y][x + 1] += error * 7 / 16  #right
            if y + 1 < height:
                if x - 1 >= 0:
                    work[y + 1][x - 1] += error * 3 / 16 # bottom-left
                work[y + 1][x] += error * 5 / 16 # straight below
                if x + 1 < width:
                    work[y + 1][x + 1] += error * 1 / 16# diagonally down bottom right
    return on


def braille_dots(image: Image.Image, max_width_chars: int = DEFAULT_BRAILLE_WIDTH_CHARS) -> str:
    """
    Return a multi-line string of Braille Unicode characters
    approximating the image's brightness (FR10). No ANSI color/styling
    is ever added.

    The image is first manually box-downsampled so the output is
    max_width_chars characters wide (proportional height), which keeps
    the preview inside a normal terminal window regardless of the
    source image's resolution. Floyd-Steinberg dithering is then
    applied so gradients read as texture rather than flat blotches.

    Works on the image exactly as currently loaded - it reads
    grayscale luminosity directly rather than depending on Halftone
    having been applied first, which is what lets EC20 fall back to a
    plain brightness approximation instead of an error.
    """
    src = image.convert("RGB")
    src_w, src_h = src.size

    # Each Braille char samples a 2 (wide) x 4 (tall) block, which is
    # roughly square once you account for a terminal character cell
    # normally being about twice as tall as it is wide - so scaling
    # the pixel width directly by max_width_chars * 2 keeps the aspect
    # ratio looking right without any extra correction factor.
    target_width = max(2, max_width_chars * 2)
    target_height = max(4, round(src_h * (target_width / src_w)))
    target_height = (target_height // 4) * 4 or 4  # whole number of Braille rows

    luminosity_grid = _box_downsample_luminosity(src, target_width, target_height)
    on = _floyd_steinberg_dither(luminosity_grid, target_width, target_height)

    rows = []
    for block_top in range(0, target_height, 4):
        row_chars = []
        for block_left in range(0, target_width, 2):
            bitmask = 0
            for (dx, dy), bit in _BIT_FOR_OFFSET.items():
                x, y = block_left + dx, block_top + dy
                if x >= target_width or y >= target_height:
                    continue  # past the edge -> bit stays off, never out of bounds
                if on[y][x]:
                    bitmask |= bit
            row_chars.append(chr(_BRAILLE_BASE + bitmask))
        rows.append("".join(row_chars))
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# FR3 - Composite / copy / blend
# ---------------------------------------------------------------------------

DEFAULT_GREEN_MARGIN = 30  # used unless the user picks a different threshold


def is_valid_green_margin(text: str) -> bool:
    """True if text parses as a non-negative integer margin."""
    try:
        value = int(text)
    except (TypeError, ValueError):
        return False
    return value >= 0


def is_green_pixel(r: int, g: int, b: int, margin: int = DEFAULT_GREEN_MARGIN) -> bool:
    """True if this pixel counts as keyed green under the threshold rule."""
    return g > r + margin and g > b + margin


def valid_region(bg_w: int, bg_h: int, fg_w: int, fg_h: int, x: int, y: int) -> tuple:
    """Return (x0, y0, x1, y1), the rectangle both images can safely share."""
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(bg_w, x + fg_w)
    y1 = min(bg_h, y + fg_h)
    return (x0, y0, x1, y1)


def simple_overlay(background: Image.Image, foreground: Image.Image,
                    x: int, y: int, alpha: float) -> Image.Image:
    """Return a NEW image: foreground blended onto background at (x, y)."""
    bg = background.convert("RGB")
    fg = foreground.convert("RGB")
    out = bg.copy()
    bg_px, fg_px, out_px = bg.load(), fg.load(), out.load()

    x0, y0, x1, y1 = valid_region(bg.width, bg.height, fg.width, fg.height, x, y)
    for by in range(y0, y1):
        for bx in range(x0, x1):
            fx, fy = bx - x, by - y
            br, bgn, bb = bg_px[bx, by]
            fr, fgn, fb = fg_px[fx, fy]
            out_px[bx, by] = (
                clamp(round(br * (1 - alpha) + fr * alpha)),
                clamp(round(bgn * (1 - alpha) + fgn * alpha)),
                clamp(round(bb * (1 - alpha) + fb * alpha)),
            )
    return out


def green_screen(background: Image.Image, foreground: Image.Image,
                  x: int, y: int, margin: int = DEFAULT_GREEN_MARGIN) -> Image.Image:
    """Return a NEW image: non-green foreground pixels placed over background."""
    bg = background.convert("RGB")
    fg = foreground.convert("RGB")
    out = bg.copy()
    fg_px, out_px = fg.load(), out.load()

    x0, y0, x1, y1 = valid_region(bg.width, bg.height, fg.width, fg.height, x, y)
    for by in range(y0, y1):
        for bx in range(x0, x1):
            fx, fy = bx - x, by - y
            r, g, b = fg_px[fx, fy]
            if not is_green_pixel(r, g, b, margin):
                out_px[bx, by] = (r, g, b)
    return out


# ---------------------------------------------------------------------------
# FR4 - Orientation
# ---------------------------------------------------------------------------

def _rotate_90(image: Image.Image) -> Image.Image:
    """One manual 90-degree clockwise turn, producing a NEW image."""
    width, height = image.size
    src_px = image.load()
    out = Image.new("RGB", (height, width))
    out_px = out.load()

    for y in range(height):
        for x in range(width):
            out_px[height - 1 - y, x] = src_px[x, y]
    return out


def rotate(image: Image.Image, degrees: int) -> Image.Image:
    """
    Return a NEW image rotated by 90, 180, or 270 degrees, built from
    composed 90-degree turns. Assumes the caller already validated
    degrees with is_valid_rotation (EC15).
    """
    src = image.convert("RGB")
    turns = {90: 1, 180: 2, 270: 3}[degrees]
    result = src
    for _ in range(turns):
        result = _rotate_90(result)
    return result


def is_valid_rotation(degrees: int) -> bool:
    """True only if degrees is exactly 90, 180, or 270 (EC15)."""
    return degrees in (90, 180, 270)


def flip_horizontal(image: Image.Image) -> Image.Image:
    """Return a NEW image mirrored left-right (manual pixel copy)."""
    src = image.convert("RGB")
    width, height = src.size
    src_px = src.load()
    out = Image.new("RGB", (width, height))
    out_px = out.load()

    for y in range(height):
        for x in range(width):
            out_px[width - 1 - x, y] = src_px[x, y]
    return out


def flip_vertical(image: Image.Image) -> Image.Image:
    """Return a NEW image mirrored top-bottom (manual pixel copy)."""
    src = image.convert("RGB")
    width, height = src.size
    src_px = src.load()
    out = Image.new("RGB", (width, height))
    out_px = out.load()

    for y in range(height):
        for x in range(width):
            out_px[x, height - 1 - y] = src_px[x, y]
    return out



def is_valid_blend_strength(text: str) -> bool:
    """True if text parses as a float in the closed range 0-1 (EC5)."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return False
    return 0.0 <= value <= 1.0


def is_valid_position(bg_w: int, bg_h: int, fg_w: int, fg_h: int, x: int, y: int) -> bool:
    """True if the placed foreground overlaps the background by >=1 pixel."""
    x0, y0, x1, y1 = valid_region(bg_w, bg_h, fg_w, fg_h, x, y)
    return x1 > x0 and y1 > y0

