"""Color-by and label column session-state resolution."""

import streamlit as st

from map_ui.display.properties import get_colorable_columns

def resolve_color_by_column_for_map() -> str:
    """Return the active color-by column before Location table widgets render."""
    colorable_columns = get_colorable_columns(st.session_state.points)
    picker_value = st.session_state.get("color_by_column_picker")
    if picker_value in colorable_columns:
        return picker_value
    return resolve_color_by_column(colorable_columns)


def resolve_label_by_column_for_map() -> str:
    """Return the active label column before Location table widgets render."""
    labelable_columns = get_colorable_columns(st.session_state.points)
    picker_value = st.session_state.get("label_by_column_picker")
    if picker_value in labelable_columns:
        return picker_value
    return resolve_label_by_column(labelable_columns)

def sync_color_by_column() -> None:
    """Persist the selected color-by column across reruns."""
    st.session_state.color_by_column = st.session_state.color_by_column_picker


def sync_label_by_column() -> None:
    """Persist the selected label column across reruns."""
    st.session_state.label_by_column = st.session_state.label_by_column_picker


def resolve_color_by_column(colorable_columns: list[str]) -> str:
    """Return a valid color-by column from session state.

    Parameters
    ----------
    colorable_columns : list of str
        Column labels available for pin coloring.

    Returns
    -------
    str
        Selected column label, falling back to ``Description`` when needed.
    """
    current = st.session_state.get("color_by_column", "Description")
    if current in colorable_columns:
        return current
    if "Description" in colorable_columns:
        return "Description"
    return colorable_columns[0]


def resolve_label_by_column(labelable_columns: list[str]) -> str:
    """Return a valid label column from session state.

    Parameters
    ----------
    labelable_columns : list of str
        Column labels available for marker hover tooltips.

    Returns
    -------
    str
        Selected column label, falling back to ``Name`` when needed.
    """
    current = st.session_state.get("label_by_column", "Name")
    if current in labelable_columns:
        return current
    if "Name" in labelable_columns:
        return "Name"
    return labelable_columns[0]
