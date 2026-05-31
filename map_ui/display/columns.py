"""Color-by and label column session-state resolution."""

import streamlit as st

from map_ui.display.properties import get_colorable_columns


def _resolve_column(
    colorable_columns: list[str],
    session_key: str,
    picker_key: str,
    default: str,
    *,
    prefer_picker: bool,
) -> str:
    """Return a valid column from session state or picker widgets."""
    if prefer_picker:
        picker_value = st.session_state.get(picker_key)
        if picker_value in colorable_columns:
            return picker_value

    current = st.session_state.get(session_key, default)
    if current in colorable_columns:
        return current
    if default in colorable_columns:
        return default
    return colorable_columns[0]


def resolve_color_by_column(
    colorable_columns: list[str] | None = None,
    *,
    prefer_picker: bool = False,
) -> str:
    """Return a valid color-by column from session state.

    Parameters
    ----------
    colorable_columns : list of str or None, optional
        Column labels available for pin coloring. When ``None``, reads from
        the current points in session state.
    prefer_picker : bool, optional
        When ``True``, prefer the live picker widget value over the persisted
        session value. Used before display settings widgets render.

    Returns
    -------
    str
        Selected column label, falling back to ``Description`` when needed.
    """
    columns = colorable_columns or get_colorable_columns(st.session_state.points)
    return _resolve_column(
        columns,
        "color_by_column",
        "color_by_column_picker",
        "Description",
        prefer_picker=prefer_picker,
    )


def resolve_label_by_column(
    labelable_columns: list[str] | None = None,
    *,
    prefer_picker: bool = False,
) -> str:
    """Return a valid label column from session state.

    Parameters
    ----------
    labelable_columns : list of str or None, optional
        Column labels available for marker hover tooltips. When ``None``,
        reads from the current points in session state.
    prefer_picker : bool, optional
        When ``True``, prefer the live picker widget value over the persisted
        session value. Used before display settings widgets render.

    Returns
    -------
    str
        Selected column label, falling back to ``Name`` when needed.
    """
    columns = labelable_columns or get_colorable_columns(st.session_state.points)
    return _resolve_column(
        columns,
        "label_by_column",
        "label_by_column_picker",
        "Name",
        prefer_picker=prefer_picker,
    )
