"""st_folium component key generation."""

import hashlib

import streamlit as st

from map_ui.basemap import resolve_basemap_name
from map_ui.display.columns import resolve_color_by_column
from map_ui.display.legend import get_legend_display_name
from map_ui.display.pin_colors import resolve_point_color
from map_ui.display.properties import get_property_key, get_unique_property_values
from styling import DEFAULT_BUTTON_COLOR

def map_widget_key() -> str:
    """Return a st_folium key that changes when map layers need to refresh.

    ``st_folium`` hashes only the Leaflet script when choosing a component key,
    so HTML legend overlays and similar basemap variants can fail to update
    unless the key changes too.
    """
    basemap = resolve_basemap_name()
    inset_enabled = st.session_state.get("show_inset_map", False)
    cluster_bubbles = st.session_state.get("cluster_overlapping_pins", True)
    label_column = st.session_state.get("label_by_column", "Name")
    key = (
        f"click2vector_map_{basemap}_{inset_enabled}_{cluster_bubbles}_"
        f"{label_column}"
    )

    if not st.session_state.get("show_map_legend", False):
        return key

    default_color = st.session_state.get("pin_color", DEFAULT_BUTTON_COLOR)
    color_by_column = resolve_color_by_column(prefer_picker=True)
    property_key = get_property_key(color_by_column)
    legend_parts = []
    for value in get_unique_property_values(st.session_state.points, property_key):
        default_label = value or f"(No {color_by_column.lower()})"
        label = get_legend_display_name(property_key, value, default_label)
        color = resolve_point_color(property_key, value, default_color)
        legend_parts.append(f"{label}:{color}")
    fingerprint = hashlib.sha256("|".join(legend_parts).encode()).hexdigest()[:12]
    return f"{key}_legend_{fingerprint}"
