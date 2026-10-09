# python -m pytest test_image_editor.py

"""Unit tests for image_ops.py"""

from PIL import Image

from image_ops import (
    clamp,
    grayscale,
    negative,
    sepia,
    is_valid_cell_size,
    halftone,
    is_valid_braille_width,
    braille_dots,
    DEFAULT_GREEN_MARGIN,
    is_valid_green_margin,
    is_green_pixel,
    valid_region,
    simple_overlay,
    green_screen,
    rotate,
    is_valid_rotation,
    flip_horizontal,
    flip_vertical,
    is_valid_blend_strength,
    is_valid_position,
    DEFAULT_BRAILLE_WIDTH_CHARS,
    _luminosity,
    _rotate_90,
    _box_downsample_luminosity,
    _floyd_steinberg_dither,    
)

import session as session_ops

# --- clamp ---

def test_clamp_above_255():
    assert clamp(300) == 255

def test_clamp_below_zero():
    assert clamp(-20) == 0

def test_clamp_in_range():
    assert clamp(128) == 128

def test_clamp_lower_boundary():
    assert clamp(0) == 0

def test_clamp_upper_boundary():
    assert clamp(255) == 255


# --- grayscale ---

def test_grayscale_channels_equal():
    img = Image.new("RGB", (2, 2), (10, 100, 200))
    result = grayscale(img)
    r, g, b = result.getpixel((0, 0))
    assert r == g == b

def test_grayscale_white_stays_white():
    img = Image.new("RGB", (2, 2), (255, 255, 255))
    assert grayscale(img).getpixel((0, 0)) == (255, 255, 255)

def test_grayscale_black_stays_black():
    img = Image.new("RGB", (2, 2), (0, 0, 0))
    assert grayscale(img).getpixel((0, 0)) == (0, 0, 0)

def test_grayscale_keeps_size():
    img = Image.new("RGB", (5, 3), (50, 50, 50))
    assert grayscale(img).size == (5, 3)

def test_grayscale_does_not_modify_original():
    img = Image.new("RGB", (2, 2), (10, 20, 30))
    grayscale(img)
    assert img.getpixel((0, 0)) == (10, 20, 30)


# --- negative ---

def test_negative_inverts_red():
    img = Image.new("RGB", (2, 2), (255, 0, 0))
    assert negative(img).getpixel((0, 0)) == (0, 255, 255)

def test_negative_black_becomes_white():
    img = Image.new("RGB", (2, 2), (0, 0, 0))
    assert negative(img).getpixel((0, 0)) == (255, 255, 255)

def test_negative_inverts_arbitrary_pixel():
    img = Image.new("RGB", (2, 2), (10, 100, 200))
    assert negative(img).getpixel((0, 0)) == (245, 155, 55)

def test_negative_keeps_size():
    img = Image.new("RGB", (4, 6), (1, 2, 3))
    assert negative(img).size == (4, 6)

def test_negative_does_not_modify_original():
    img = Image.new("RGB", (2, 2), (10, 20, 30))
    negative(img)
    assert img.getpixel((0, 0)) == (10, 20, 30)


# --- sepia ---

def test_sepia_black_stays_black():
    img = Image.new("RGB", (2, 2), (0, 0, 0))
    assert sepia(img).getpixel((0, 0)) == (0, 0, 0)

def test_sepia_white_is_clamped():
    img = Image.new("RGB", (2, 2), (255, 255, 255))
    r, g, b = sepia(img).getpixel((0, 0))
    assert r == 255
    assert g == 255
    assert 0 <= b <= 255

def test_sepia_warm_tone_ordering():
    img = Image.new("RGB", (2, 2), (128, 128, 128))
    r, g, b = sepia(img).getpixel((0, 0))
    assert r >= g >= b

def test_sepia_keeps_size():
    img = Image.new("RGB", (3, 3), (100, 100, 100))
    assert sepia(img).size == (3, 3)


# --- is_valid_cell_size ---

def test_is_valid_cell_size_accepts_positive():
    assert is_valid_cell_size("10") is True

def test_is_valid_cell_size_rejects_zero():
    assert is_valid_cell_size("0") is False

def test_is_valid_cell_size_rejects_negative():
    assert is_valid_cell_size("-5") is False

def test_is_valid_cell_size_rejects_text():
    assert is_valid_cell_size("abc") is False


# --- halftone ---

def test_halftone_output_is_black_or_white():
    img = Image.new("RGB", (30, 30), (100, 100, 100))
    result = halftone(img, 10)
    for y in range(30):
        for x in range(30):
            assert result.getpixel((x, y)) in [(0, 0, 0), (255, 255, 255)]

def test_halftone_white_image_has_no_black_dots():
    """Fully white input should produce a fully white output, no dots."""
    img = Image.new("RGB", (20, 20), (255, 255, 255))
    result = halftone(img, 10)
    pixels = [result.getpixel((x, y)) for y in range(20) for x in range(20)]
    assert all(p == (255, 255, 255) for p in pixels)

def test_halftone_black_image_has_black_dots():
    img = Image.new("RGB", (20, 20), (0, 0, 0))
    result = halftone(img, 10)
    pixels = [result.getpixel((x, y)) for y in range(20) for x in range(20)]
    assert any(p == (0, 0, 0) for p in pixels)

def test_halftone_keeps_size():
    img = Image.new("RGB", (25, 17), (80, 80, 80))
    assert halftone(img, 10).size == (25, 17)


# --- is_valid_braille_width ---

def test_is_valid_braille_width_accepts_positive():
    assert is_valid_braille_width("67") is True

def test_is_valid_braille_width_rejects_zero():
    assert is_valid_braille_width("0") is False

def test_is_valid_braille_width_rejects_text():
    assert is_valid_braille_width("wide") is False


# --- braille_dots ---

def test_braille_dots_returns_string():
    img = Image.new("RGB", (20, 20), (128, 128, 128))
    assert isinstance(braille_dots(img), str)

def test_braille_dots_output_not_empty():
    img = Image.new("RGB", (20, 20), (128, 128, 128))
    assert len(braille_dots(img)) > 0

def test_braille_dots_has_multiple_lines_for_tall_image():
    img = Image.new("RGB", (20, 40), (128, 128, 128))
    assert "\n" in braille_dots(img)


# --- is_valid_green_margin ---

def test_is_valid_green_margin_accepts_zero():
    assert is_valid_green_margin("0") is True

def test_is_valid_green_margin_accepts_positive():
    assert is_valid_green_margin("30") is True

def test_is_valid_green_margin_rejects_negative():
    assert is_valid_green_margin("-1") is False

def test_is_valid_green_margin_rejects_text():
    assert is_valid_green_margin("green") is False


# --- is_green_pixel ---

def test_is_green_pixel_pure_green_true():
    assert is_green_pixel(0, 255, 0) is True

def test_is_green_pixel_pure_red_false():
    assert is_green_pixel(255, 0, 0) is False

def test_is_green_pixel_respects_custom_margin():
    # g is only 10 higher than r/b; default margin 30 rejects it,
    # a smaller margin accepts it
    assert is_green_pixel(100, 110, 100, margin=30) is False
    assert is_green_pixel(100, 110, 100, margin=5) is True


# --- valid_region ---

def test_valid_region_fully_inside():
    assert valid_region(800, 600, 100, 100, 50, 50) == (50, 50, 150, 150)

def test_valid_region_clips_bottom_right():
    assert valid_region(800, 600, 300, 300, 700, 500) == (700, 500, 800, 600)

def test_valid_region_clips_negative_position():
    assert valid_region(800, 600, 100, 100, -20, -30) == (0, 0, 80, 70)

def test_valid_region_empty_when_out_of_bounds():
    x0, y0, x1, y1 = valid_region(800, 600, 100, 100, 900, 700)
    assert x1 <= x0 or y1 <= y0


# --- simple_overlay ---

def test_overlay_keeps_background_size():
    bg = Image.new("RGB", (10, 10), (0, 0, 0))
    fg = Image.new("RGB", (4, 4), (255, 255, 255))
    result = simple_overlay(bg, fg, 2, 2, 0.5)
    assert result.size == (10, 10)

def test_overlay_full_strength_shows_foreground():
    bg = Image.new("RGB", (10, 10), (0, 0, 0))
    fg = Image.new("RGB", (4, 4), (200, 100, 50))
    result = simple_overlay(bg, fg, 2, 2, 1.0)
    assert result.getpixel((3, 3)) == (200, 100, 50)

def test_overlay_zero_strength_shows_background():
    bg = Image.new("RGB", (10, 10), (10, 20, 30))
    fg = Image.new("RGB", (4, 4), (200, 100, 50))
    result = simple_overlay(bg, fg, 2, 2, 0.0)
    assert result.getpixel((3, 3)) == (10, 20, 30)

def test_overlay_outside_foreground_area_unchanged():
    bg = Image.new("RGB", (10, 10), (10, 20, 30))
    fg = Image.new("RGB", (4, 4), (255, 255, 255))
    result = simple_overlay(bg, fg, 2, 2, 1.0)
    assert result.getpixel((0, 0)) == (10, 20, 30)

def test_overlay_partially_off_edge_does_not_crash():
    bg = Image.new("RGB", (10, 10), (0, 0, 0))
    fg = Image.new("RGB", (6, 6), (255, 255, 255))
    result = simple_overlay(bg, fg, 7, 7, 1.0)
    assert result.size == (10, 10)
    assert result.getpixel((9, 9)) == (255, 255, 255)

def test_overlay_does_not_modify_originals():
    bg = Image.new("RGB", (10, 10), (0, 0, 0))
    fg = Image.new("RGB", (4, 4), (255, 255, 255))
    simple_overlay(bg, fg, 2, 2, 0.5)
    assert bg.getpixel((0, 0)) == (0, 0, 0)
    assert fg.getpixel((0, 0)) == (255, 255, 255)


# --- green_screen ---

def test_green_screen_replaces_green_with_background():
    fg = Image.new("RGB", (4, 4), (0, 255, 0))
    bg = Image.new("RGB", (4, 4), (0, 0, 255))
    result = green_screen(bg, fg, 0, 0)
    assert result.getpixel((0, 0)) == (0, 0, 255)

def test_green_screen_keeps_non_green_foreground():
    fg = Image.new("RGB", (4, 4), (255, 0, 0))
    bg = Image.new("RGB", (4, 4), (0, 0, 255))
    result = green_screen(bg, fg, 0, 0)
    assert result.getpixel((0, 0)) == (255, 0, 0)

def test_green_screen_keeps_size():
    fg = Image.new("RGB", (4, 4), (0, 255, 0))
    bg = Image.new("RGB", (4, 4), (0, 0, 255))
    assert green_screen(bg, fg, 0, 0).size == (4, 4)

def test_green_screen_custom_margin():
    # near-green pixel: only caught as green with a small margin
    fg = Image.new("RGB", (4, 4), (100, 110, 100))
    bg = Image.new("RGB", (4, 4), (0, 0, 255))
    result_default = green_screen(bg, fg, 0, 0, DEFAULT_GREEN_MARGIN)
    result_tight = green_screen(bg, fg, 0, 0, margin=5)
    assert result_default.getpixel((0, 0)) == (100, 110, 100)  # not keyed out
    assert result_tight.getpixel((0, 0)) == (0, 0, 255)        # keyed out


# --- rotate / is_valid_rotation ---

def test_is_valid_rotation_accepts_90_180_270():
    assert is_valid_rotation(90) is True
    assert is_valid_rotation(180) is True
    assert is_valid_rotation(270) is True

def test_is_valid_rotation_rejects_other_values():
    assert is_valid_rotation(45) is False
    assert is_valid_rotation(0) is False
    assert is_valid_rotation(360) is False

def test_rotate_90_swaps_dimensions():
    img = Image.new("RGB", (4, 3), (0, 0, 0))
    assert rotate(img, 90).size == (3, 4)

def test_rotate_180_keeps_dimensions():
    img = Image.new("RGB", (4, 3), (0, 0, 0))
    assert rotate(img, 180).size == (4, 3)

def test_rotate_180_moves_corner_pixel():
    img = Image.new("RGB", (4, 3), (0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0))
    result = rotate(img, 180)
    assert result.getpixel((3, 2)) == (255, 0, 0)

def test_rotate_does_not_modify_original():
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    rotate(img, 90)
    assert img.getpixel((0, 0)) == (10, 20, 30)
    assert img.size == (4, 3)


# --- flip_horizontal / flip_vertical ---

def test_flip_horizontal_keeps_size():
    img = Image.new("RGB", (5, 3), (0, 0, 0))
    assert flip_horizontal(img).size == (5, 3)

def test_flip_horizontal_moves_left_pixel_to_right():
    img = Image.new("RGB", (4, 2), (0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0))
    result = flip_horizontal(img)
    assert result.getpixel((3, 0)) == (255, 0, 0)

def test_flip_vertical_keeps_size():
    img = Image.new("RGB", (5, 3), (0, 0, 0))
    assert flip_vertical(img).size == (5, 3)

def test_flip_vertical_moves_top_pixel_to_bottom():
    img = Image.new("RGB", (2, 4), (0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0))
    result = flip_vertical(img)
    assert result.getpixel((0, 3)) == (255, 0, 0)

def test_flip_horizontal_twice_restores_original():
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    img.putpixel((1, 1), (99, 88, 77))
    result = flip_horizontal(flip_horizontal(img))
    assert result.getpixel((1, 1)) == (99, 88, 77)

def test_flip_does_not_modify_original():
    img = Image.new("RGB", (4, 3), (10, 20, 30))
    flip_horizontal(img)
    flip_vertical(img)
    assert img.getpixel((0, 0)) == (10, 20, 30)


# --- is_valid_blend_strength ---

def test_is_valid_blend_strength_accepts_0():
    assert is_valid_blend_strength("0") is True

def test_is_valid_blend_strength_accepts_1():
    assert is_valid_blend_strength("1") is True

def test_is_valid_blend_strength_accepts_mid_value():
    assert is_valid_blend_strength("0.5") is True

def test_is_valid_blend_strength_rejects_above_1():
    assert is_valid_blend_strength("1.5") is False

def test_is_valid_blend_strength_rejects_below_0():
    assert is_valid_blend_strength("-0.1") is False

def test_is_valid_blend_strength_rejects_text():
    assert is_valid_blend_strength("half") is False


# --- is_valid_position ---

def test_is_valid_position_overlap_true():
    assert is_valid_position(800, 600, 100, 100, 50, 50) is True

def test_is_valid_position_no_overlap_false():
    assert is_valid_position(800, 600, 100, 100, 900, 700) is False

def test_is_valid_position_touching_edge_false():
    assert is_valid_position(800, 600, 100, 100, 800, 0) is False



def test_halftone_white_image_no_dots_odd_cell_size():
    img = Image.new("RGB", (25, 25), (255, 255, 255))
    result = halftone(img, 5)
    pixels = [result.getpixel((x, y)) for y in range(25) for x in range(25)]
    assert all(p == (255, 255, 255) for p in pixels)


def _img(color=(10, 20, 30), size=(2, 2)):
       return Image.new("RGB", size, color)


# --- session: new_session ---

def test_new_session_starts_clean():
    img = _img()
    s = session_ops.new_session(img)
    assert s["current"] is img
    assert s["undo_stack"] == []
    assert s["redo_stack"] == []
    assert s["dirty"] is False

def test_new_session_has_default_preferences():
    s = session_ops.new_session(_img())
    assert s["halftone_cell_size"] == session_ops.DEFAULT_CELL_SIZE
    assert s["green_margin"] == DEFAULT_GREEN_MARGIN
    assert s["braille_width_chars"] == DEFAULT_BRAILLE_WIDTH_CHARS


# --- session: push_state ---

def test_push_state_replaces_current_and_saves_old_with_label():
    a, b = _img((1, 1, 1)), _img((2, 2, 2))
    s = session_ops.push_state(session_ops.new_session(a), b, "Negative")
    assert s["current"] is b
    assert len(s["undo_stack"]) == 1
    assert s["undo_stack"][0][0] is a
    assert s["undo_stack"][0][1] == "Negative"

def test_push_state_marks_dirty():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "Sepia")
    assert s["dirty"] is True

def test_push_state_clears_redo_stack():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "A")
    s = session_ops.undo(s)
    assert len(s["redo_stack"]) == 1
    s = session_ops.push_state(s, _img(), "B")
    assert s["redo_stack"] == []

def test_push_state_keeps_preferences():
    s = session_ops.set_cell_size(session_ops.new_session(_img()), 7)
    s = session_ops.push_state(s, _img(), "Grayscale")
    assert s["halftone_cell_size"] == 7

def test_push_state_does_not_modify_original_session():
    original = session_ops.new_session(_img())
    session_ops.push_state(original, _img(), "Negative")
    assert original["undo_stack"] == []
    assert original["dirty"] is False

def test_push_state_caps_undo_stack_at_max_steps():
    s = session_ops.new_session(_img())
    for i in range(session_ops.MAX_UNDO_STEPS + 5):
        s = session_ops.push_state(s, _img(), f"op{i}")
    assert len(s["undo_stack"]) == session_ops.MAX_UNDO_STEPS
    assert s["undo_stack"][0][1] == "op5"   # oldest 5 were dropped


# --- session: undo ---

def test_undo_returns_none_when_nothing_to_undo():
    assert session_ops.undo(session_ops.new_session(_img())) is None

def test_undo_restores_previous_image():
    a, b = _img((1, 1, 1)), _img((2, 2, 2))
    s = session_ops.push_state(session_ops.new_session(a), b, "Negative")
    result = session_ops.undo(s)
    assert result["current"] is a
    assert result["undo_stack"] == []

def test_undo_moves_current_to_redo_stack():
    a, b = _img((1, 1, 1)), _img((2, 2, 2))
    s = session_ops.push_state(session_ops.new_session(a), b, "Negative")
    result = session_ops.undo(s)
    assert result["redo_stack"][0][0] is b
    assert result["redo_stack"][0][1] == "Negative"

def test_undo_does_not_modify_original_session():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "A")
    session_ops.undo(s)
    assert len(s["undo_stack"]) == 1
    assert s["redo_stack"] == []


# --- session: redo ---

def test_redo_returns_none_when_nothing_to_redo():
    assert session_ops.redo(session_ops.new_session(_img())) is None

def test_redo_restores_undone_image():
    a, b = _img((1, 1, 1)), _img((2, 2, 2))
    s = session_ops.push_state(session_ops.new_session(a), b, "Negative")
    result = session_ops.redo(session_ops.undo(s))
    assert result["current"] is b
    assert result["redo_stack"] == []
    assert result["undo_stack"][0][0] is a

def test_undo_then_redo_round_trip_matches_original_state():
    a, b = _img((1, 1, 1)), _img((2, 2, 2))
    s = session_ops.push_state(session_ops.new_session(a), b, "Sepia")
    result = session_ops.redo(session_ops.undo(s))
    assert result["current"] is s["current"]
    assert result["undo_stack"][0][1] == "Sepia"


# --- session: mark_saved / has_unsaved_changes ---

def test_mark_saved_clears_dirty_flag():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "A")
    assert s["dirty"] is True
    assert session_ops.mark_saved(s)["dirty"] is False

def test_mark_saved_does_not_modify_original_session():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "A")
    session_ops.mark_saved(s)
    assert s["dirty"] is True

def test_has_unsaved_changes_false_for_new_session():
    assert session_ops.has_unsaved_changes(session_ops.new_session(_img())) is False

def test_has_unsaved_changes_true_after_edit():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "A")
    assert session_ops.has_unsaved_changes(s) is True


# --- session: preferences ---

def test_set_cell_size_updates_value():
    s = session_ops.set_cell_size(session_ops.new_session(_img()), 25)
    assert s["halftone_cell_size"] == 25

def test_set_green_margin_updates_value():
    s = session_ops.set_green_margin(session_ops.new_session(_img()), 55)
    assert s["green_margin"] == 55

def test_set_braille_width_updates_value():
    s = session_ops.set_braille_width(session_ops.new_session(_img()), 40)
    assert s["braille_width_chars"] == 40

def test_preference_changes_do_not_touch_history_or_dirty():
    s = session_ops.push_state(session_ops.new_session(_img()), _img(), "A")
    s = session_ops.mark_saved(s)
    result = session_ops.set_cell_size(s, 9)
    assert result["dirty"] is False
    assert result["undo_stack"] == s["undo_stack"]
    assert result["redo_stack"] == s["redo_stack"]

def test_set_cell_size_does_not_modify_original_session():
    s = session_ops.new_session(_img())
    session_ops.set_cell_size(s, 99)
    assert s["halftone_cell_size"] == session_ops.DEFAULT_CELL_SIZE


# --- session: clear_session ---

def test_clear_session_is_empty_with_default_preferences():
    s = session_ops.clear_session()
    assert s["current"] is None
    assert s["undo_stack"] == [] and s["redo_stack"] == []
    assert s["dirty"] is False
    assert s["halftone_cell_size"] == session_ops.DEFAULT_CELL_SIZE
    assert s["green_margin"] == DEFAULT_GREEN_MARGIN
    assert s["braille_width_chars"] == DEFAULT_BRAILLE_WIDTH_CHARS


# --- image_ops private helpers ---

def test_luminosity_white_and_black():
    assert round(_luminosity(255, 255, 255)) == 255
    assert _luminosity(0, 0, 0) == 0

def test_luminosity_weights_green_over_red_over_blue():
    assert _luminosity(0, 255, 0) > _luminosity(255, 0, 0) > _luminosity(0, 0, 255)

def test_rotate_90_swaps_width_and_height():
    assert _rotate_90(_img(size=(3, 2))).size == (2, 3)

def test_rotate_90_moves_top_left_pixel_to_top_right():
    img = _img((0, 0, 0), (3, 2))
    img.putpixel((0, 0), (255, 0, 0))
    assert _rotate_90(img).getpixel((1, 0)) == (255, 0, 0)

def test_rotate_90_four_times_restores_original():
    img = _img((0, 0, 0), (3, 2))
    img.putpixel((0, 0), (255, 0, 0))
    result = img
    for _ in range(4):
        result = _rotate_90(result)
    assert result.tobytes() == img.tobytes()

def test_box_downsample_returns_requested_grid_size():
    grid = _box_downsample_luminosity(_img(size=(8, 8)), 4, 2)
    assert len(grid) == 2
    assert all(len(row) == 4 for row in grid)

def test_box_downsample_white_image_is_all_bright():
    grid = _box_downsample_luminosity(_img((255, 255, 255), (4, 4)), 2, 2)
    assert all(round(v) == 255 for row in grid for v in row)

def test_box_downsample_averages_black_and_white_block():
    img = _img((0, 0, 0), (2, 1))
    img.putpixel((1, 0), (255, 255, 255))
    grid = _box_downsample_luminosity(img, 1, 1)
    assert abs(grid[0][0] - 127.5) < 1e-6

def test_dither_returns_grid_of_requested_size():
    on = _floyd_steinberg_dither([[100.0] * 5 for _ in range(3)], 5, 3)
    assert len(on) == 3
    assert all(len(row) == 5 for row in on)

def test_dither_all_black_grid_is_all_dots():
    on = _floyd_steinberg_dither([[0.0] * 3 for _ in range(3)], 3, 3)
    assert all(all(row) for row in on)

def test_dither_all_white_grid_has_no_dots():
    on = _floyd_steinberg_dither([[255.0] * 3 for _ in range(3)], 3, 3)
    assert not any(any(row) for row in on)

def test_dither_mid_gray_gives_mixed_pattern():
    on = _floyd_steinberg_dither([[128.0] * 4 for _ in range(4)], 4, 4)
    flat = [v for row in on for v in row]
    assert True in flat and False in flat

def test_dither_does_not_modify_input_grid():
    grid = [[128.0] * 4 for _ in range(4)]
    _floyd_steinberg_dither(grid, 4, 4)
    assert grid == [[128.0] * 4 for _ in range(4)]