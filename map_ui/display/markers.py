"""Folium map markers for stored points."""

import folium
import streamlit as st
from folium.plugins import MarkerCluster

from map_ui.display.cluster import (
    CLUSTER_DISABLE_AT_ZOOM,
    CLUSTER_MAX_RADIUS_PX,
    marker_cluster_icon_create_function,
)
from map_ui.display.columns import resolve_label_by_column_for_map
from map_ui.display.pin_colors import resolve_point_color
from map_ui.display.properties import get_point_property_value, get_property_key
from styling import DEFAULT_BUTTON_COLOR

def make_pin_div_icon(color: str) -> folium.DivIcon:
    """Create a circular map pin icon with the given fill color.

    Parameters
    ----------
    color : str
        CSS-compatible fill color for the pin.

    Returns
    -------
    folium.DivIcon
        Folium div icon for map markers.
    """
    return folium.DivIcon(
        html=f"""
        <div style="
            background-color:{color};
            width:16px;
            height:16px;
            border-radius:50%;
            border:2px solid white;">
        </div>
        """
    )
def point_tooltip_label(point: dict, label_column: str) -> str:
    """Return hover tooltip text for one map marker.

    Parameters
    ----------
    point : dict
        GeoJSON-like point feature.
    label_column : str
        Table column label whose value is shown on hover.

    Returns
    -------
    str
        Tooltip text from the selected column.
    """
    property_key = get_property_key(label_column)
    label_value = get_point_property_value(point, property_key)
    if not label_value:
        label_value = f"(No {label_column.lower()})"
    return label_value


def create_point_marker(
    point_index: int,
    point: dict,
    pin_color: str,
    label_column: str,
) -> folium.Marker:
    """Create a draggable map marker for one stored point.

    Parameters
    ----------
    point_index : int
        Zero-based index of the point in session state.
    point : dict
        GeoJSON-like point feature.
    pin_color : str
        CSS fill color for the pin icon.
    label_column : str
        Table column label used for the marker hover tooltip.

    Returns
    -------
    folium.Marker
        Configured folium marker with tooltip and color metadata.
    """
    coords = point["geometry"]["coordinates"]
    return folium.Marker(
        location=[coords[1], coords[0]],
        tooltip=point_tooltip_label(point, label_column),
        icon=make_pin_div_icon(pin_color),
        draggable=True,
        point_color=pin_color,
        point_index=point_index,
    )


def add_existing_points_to_map(map_object):
    """Add existing points from session state to the map.

    Parameters
    ----------
    map_object : folium.Map
        The folium map to add points to.

    Returns
    -------
    None
        Adds markers for all existing points to the map.
    """
    default_color = st.session_state.get("pin_color", DEFAULT_BUTTON_COLOR)
    color_by_column = st.session_state.get("color_by_column", "Description")
    property_key = get_property_key(color_by_column)
    label_by_column = resolve_label_by_column_for_map()
    use_cluster_bubbles = st.session_state.get("cluster_overlapping_pins", True)

    if use_cluster_bubbles:
        marker_cluster = MarkerCluster(
            max_cluster_radius=CLUSTER_MAX_RADIUS_PX,
            disable_clustering_at_zoom=CLUSTER_DISABLE_AT_ZOOM,
            icon_create_function=marker_cluster_icon_create_function(
                default_color
            ),
        )
        marker_target: folium.Map | MarkerCluster = marker_cluster
    else:
        marker_target = map_object

    for point_index, point in enumerate(st.session_state.points):
        value = get_point_property_value(point, property_key)
        pin_color = resolve_point_color(property_key, value, default_color)
        create_point_marker(
            point_index, point, pin_color, label_by_column
        ).add_to(marker_target)

    if use_cluster_bubbles:
        marker_cluster.add_to(map_object)
