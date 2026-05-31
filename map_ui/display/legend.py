"""Legend labels and on-map color legend overlay."""

import hashlib
import html

import folium
import streamlit as st

from map_ui.display.columns import resolve_color_by_column
from map_ui.display.pin_colors import resolve_point_color
from map_ui.display.properties import get_property_key, get_unique_property_values
from styling import DEFAULT_BUTTON_COLOR

def get_legend_display_names(property_key: str) -> dict[str, str]:
    """Return the legend label map for one property, creating it if needed.

    Parameters
    ----------
    property_key : str
        Property key used for pin coloring.

    Returns
    -------
    dict of str to str
        Mapping from property value to custom legend label.
    """
    if "legend_display_names" not in st.session_state:
        st.session_state.legend_display_names = {}
    return st.session_state.legend_display_names.setdefault(property_key, {})


def get_legend_display_name(
    property_key: str, value: str, default_label: str
) -> str:
    """Return the legend label for one property value.

    Parameters
    ----------
    property_key : str
        Property key used for pin coloring.
    value : str
        Property value for the point.
    default_label : str
        Fallback label when no custom name is stored.

    Returns
    -------
    str
        Label shown in the map legend.
    """
    stored = get_legend_display_names(property_key).get(value)
    if stored is not None and stored.strip():
        return stored.strip()
    return default_label


def sync_legend_display_names_from_inputs(
    points: list[dict], property_key: str
) -> None:
    """Copy legend label widget values into ``legend_display_names``.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.
    property_key : str
        Property key used for pin coloring.

    Returns
    -------
    None
        Updates ``legend_display_names`` in session state.
    """
    names = get_legend_display_names(property_key)
    unique_values = get_unique_property_values(points, property_key)
    for value in unique_values:
        widget_key = legend_label_widget_key(property_key, value)
        if widget_key in st.session_state:
            names[value] = st.session_state[widget_key]
    for stale_value in set(names) - set(unique_values):
        del names[stale_value]


def legend_label_widget_key(property_key: str, value: str) -> str:
    """Return a stable widget key suffix for one legend label input.

    Parameters
    ----------
    property_key : str
        Property key used for pin coloring.
    value : str
        Property value assigned a legend label.

    Returns
    -------
    str
        Streamlit widget key for the legend label input.
    """
    digest = hashlib.sha256(
        f"legend:{property_key}:{value}".encode()
    ).hexdigest()[:16]
    return f"legend_label_{digest}"
def add_map_color_legend(map_object: folium.Map) -> None:
    """Add a categorical color legend to the map when enabled.

    Parameters
    ----------
    map_object : folium.Map
        The folium map to add the legend to.

    Returns
    -------
    None
        Adds a legend element to the map when ``show_map_legend`` is enabled.
    """
    from folium import Element

    if not st.session_state.get("show_map_legend", False):
        return
    if not st.session_state.points:
        return

    default_color = st.session_state.get("pin_color", DEFAULT_BUTTON_COLOR)
    color_by_column = resolve_color_by_column(prefer_picker=True)
    property_key = get_property_key(color_by_column)
    unique_values = get_unique_property_values(
        st.session_state.points, property_key
    )
    legend_rows = []
    for value in unique_values:
        default_label = value or f"(No {color_by_column.lower()})"
        label = get_legend_display_name(property_key, value, default_label)
        color = resolve_point_color(property_key, value, default_color)
        safe_label = html.escape(label)
        legend_rows.append(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="background:{color};width:12px;height:12px;min-width:12px;'
            f"border-radius:50%;border:1px solid #ccc;display:inline-block;"
            f'box-sizing:border-box;flex-shrink:0;"></span>'
            f'<span style="font-size:12px;line-height:12px;margin:0;">'
            f"{safe_label}</span>"
            f"</div>"
        )

    if not legend_rows:
        return

    legend_html = (
        '<div style="position:fixed;bottom:24px;left:10px;z-index:10000;'
        "background:white;border:1px solid #ccc;border-radius:4px;"
        "padding:8px 10px;max-width:220px;display:flex;"
        'flex-direction:column;gap:4px;">'
        f'{"".join(legend_rows)}</div>'
    )
    map_object.get_root().html.add_child(Element(legend_html))
