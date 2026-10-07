"""
session.py - data layer.

Pure functions that operate on a session dict:
    {current, undo_stack, redo_stack, dirty,
     halftone_cell_size, green_margin, braille_width_chars}

Every function here takes a session and returns a NEW session (or
None) - never a mutation in place - so history and preference
management behave identically whether the change came from a filter,
a composite, or a rotation.
"""

DEFAULT_CELL_SIZE = 10
from image_ops import DEFAULT_GREEN_MARGIN, DEFAULT_BRAILLE_WIDTH_CHARS

# Caps how many steps back Undo can go. Each entry holds a full copy
# of the image, so this bounds memory use for long editing sessions
# instead of letting the stack grow without limit.
MAX_UNDO_STEPS = 20


def new_session(image) -> dict:
    """Return the starting session state for a freshly loaded image."""
    return {
        "current": image,
        "undo_stack": [],
        "redo_stack": [],
        "dirty": False,
        "halftone_cell_size": DEFAULT_CELL_SIZE,
        "green_margin": DEFAULT_GREEN_MARGIN,
        "braille_width_chars": DEFAULT_BRAILLE_WIDTH_CHARS,
    }


def push_state(session: dict, image, label: str) -> dict:
    """
    Return a NEW session: current pushed onto undo_stack tagged with
    label, redo_stack cleared (a fresh action invalidates old redo
    history), current replaced by image, dirty set True. Preferences
    (halftone_cell_size, green_margin, braille_width_chars) pass
    through unchanged. undo_stack is capped at MAX_UNDO_STEPS -
    the oldest entry is dropped once the cap is exceeded.
    """
    new_undo_stack = session["undo_stack"] + [(session["current"], label)]
    if len(new_undo_stack) > MAX_UNDO_STEPS:
        new_undo_stack = new_undo_stack[-MAX_UNDO_STEPS:]

    return {
        **session,
        "current": image,
        "undo_stack": new_undo_stack,
        "redo_stack": [],
        "dirty": True,
    }


def undo(session: dict):
    """
    Return a NEW session with the top of undo_stack restored as
    current (the old current pushed onto redo_stack), or None if
    undo_stack is empty (EC11).
    """
    if not session["undo_stack"]:
        return None
    prev_image, label = session["undo_stack"][-1]
    return {
        **session,
        "current": prev_image,
        "undo_stack": session["undo_stack"][:-1],
        "redo_stack": session["redo_stack"] + [(session["current"], label)],
        "dirty": True,
    }


def redo(session: dict):
    """
    Return a NEW session with the top of redo_stack restored as
    current (the old current pushed onto undo_stack), or None if
    redo_stack is empty (EC12).
    """
    if not session["redo_stack"]:
        return None
    next_image, label = session["redo_stack"][-1]
    return {
        **session,
        "current": next_image,
        "undo_stack": session["undo_stack"] + [(session["current"], label)],
        "redo_stack": session["redo_stack"][:-1],
        "dirty": True,
    }


def mark_saved(session: dict) -> dict:
    """Return a NEW session with dirty set False."""
    return {**session, "dirty": False}


def has_unsaved_changes(session: dict) -> bool:
    """Return session['dirty'] as-is."""
    return session["dirty"]


def set_cell_size(session: dict, cell_size: int) -> dict:
    """
    Return a NEW session with halftone_cell_size updated. current,
    undo_stack, redo_stack, and dirty are left untouched - a
    resolution preference is not an image edit, so it must not be
    undoable and must not trigger the unsaved-changes warning by itself.
    """
    return {**session, "halftone_cell_size": cell_size}


def set_green_margin(session: dict, margin: int) -> dict:
    """
    Return a NEW session with green_margin updated. Like
    halftone_cell_size, this is a preference, not an image edit - it
    is not undoable and does not mark the session dirty.
    """
    return {**session, "green_margin": margin}


def set_braille_width(session: dict, width_chars: int) -> dict:
    """
    Return a NEW session with braille_width_chars updated. Like the
    other preferences above, this is not undoable and does not mark
    the session dirty.
    """
    return {**session, "braille_width_chars": width_chars}


def clear_session() -> dict:
    """Return a fresh, empty session state for the Delete/Clear option."""
    return {
        "current": None,
        "undo_stack": [],
        "redo_stack": [],
        "dirty": False,
        "halftone_cell_size": DEFAULT_CELL_SIZE,
        "green_margin": DEFAULT_GREEN_MARGIN,
        "braille_width_chars": DEFAULT_BRAILLE_WIDTH_CHARS,
    }
