"""Pin colors grouped by property value."""

import hashlib

import streamlit as st

from map_ui.display.properties import get_unique_property_values

DESCRIPTION_COLOR_PALETTE = [
    "#4363d8",
    "#3cb44b",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#469990",
    "#9A6324",
    "#800000",
    "#000075",
]

def get_property_colors(property_key: str) -> dict[str, str]:
    """Return the color map for one property, creating it if needed.

    Parameters
    ----------
    property_key : str
        Property key whose value-to-color map is requested.

    Returns
    -------
    dict of str to str
        Mapping from property value to hex color.
    """
    if "property_value_colors" not in st.session_state:
        st.session_state.property_value_colors = {}
    return st.session_state.property_value_colors.setdefault(property_key, {})


def sync_property_color_state(
    points: list[dict], property_key: str, default_color: str
) -> None:
    """Assign default colors to new property values and drop stale entries.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.
    property_key : str
        Property key used for pin coloring.
    default_color : str
        Default pin color used when assigning palette colors.

    Returns
    -------
    None
        Updates ``property_value_colors`` in session state.
    """
    colors = get_property_colors(property_key)
    unique_values = get_unique_property_values(points, property_key)
    palette = [
        color
        for color in DESCRIPTION_COLOR_PALETTE
        if color.lower() != default_color.lower()
    ]
    if not palette:
        palette = DESCRIPTION_COLOR_PALETTE

    for index, value in enumerate(unique_values):
        if value not in colors:
            if len(unique_values) == 1:
                colors[value] = default_color
            else:
                colors[value] = palette[index % len(palette)]

    for stale_value in set(colors) - set(unique_values):
        del colors[stale_value]


def sync_property_colors_from_pickers(
    points: list[dict], property_key: str
) -> None:
    """Copy color picker widget values into ``property_value_colors``.

    Streamlit updates widget session state before the script runs, but the map
    is rendered above the pickers. Syncing here ensures marker colors reflect
    the latest picker values on the same rerun.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.
    property_key : str
        Property key used for pin coloring.

    Returns
    -------
    None
        Updates ``property_value_colors`` in session state.
    """
    colors = get_property_colors(property_key)
    for value in get_unique_property_values(points, property_key):
        picker_key = property_color_widget_key(property_key, value)
        if picker_key in st.session_state:
            colors[value] = st.session_state[picker_key]


def property_color_widget_key(property_key: str, value: str) -> str:
    """Return a stable widget key suffix for one property value.

    Parameters
    ----------
    property_key : str
        Property key used for pin coloring.
    value : str
        Property value assigned a pin color.

    Returns
    -------
    str
        Streamlit widget key for the value's color picker.
    """
    digest = hashlib.sha256(f"{property_key}:{value}".encode()).hexdigest()[:16]
    return f"prop_color_picker_{digest}"


def resolve_point_color(
    property_key: str, value: str, default_color: str
) -> str:
    """Return the marker color for a point from one property value.

    Parameters
    ----------
    property_key : str
        Property key used for pin coloring.
    value : str
        Property value for the point.
    default_color : str
        Fallback color when no mapping exists yet.

    Returns
    -------
    str
        Hex color code for the marker.
    """
    normalized = (value or "").strip()
    colors = st.session_state.get("property_value_colors", {}).get(property_key, {})
    return colors.get(normalized, default_color)
def sync_property_color(property_key: str, value: str) -> None:
    """Persist one property color picker value in session state."""
    picker_key = property_color_widget_key(property_key, value)
    colors = get_property_colors(property_key)
    colors[value] = st.session_state[picker_key]
