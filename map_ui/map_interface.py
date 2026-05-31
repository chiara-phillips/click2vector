"""Map UI orchestration: search, map, table, and display settings."""

import streamlit as st
from streamlit_folium import st_folium

from map_ui.basemap import ensure_basemap_picker_state, resolve_basemap_name
from map_ui.display import (
    add_existing_points_to_map,
    add_map_color_legend,
    render_location_table_expander,
    map_widget_key,
    render_display_settings_expander,
)
from map_ui.geocoding import render_search_section
from map_ui.map_interactions import (
    add_draggable_marker_handlers,
    process_map_state,
)
from map_ui.view import (
    MAP_HEIGHT,
    create_map_with_features,
    get_default_map_view,
    request_rerun,
    sync_map_view_to_points,
)


def _render_interactive_map(basemap_name: str) -> dict | None:
    """Build and display the folium map, returning st_folium output.

    Parameters
    ----------
    basemap_name : str
        The name of the basemap to use.

    Returns
    -------
    dict or None
        The map data returned from st_folium for further processing.
    """
    map_object = create_map_with_features(basemap_name)
    map_view = st.session_state.get("last_map_view", get_default_map_view())

    add_existing_points_to_map(map_object)
    add_map_color_legend(map_object)
    add_draggable_marker_handlers(map_object)

    map_data = st_folium(
        map_object,
        height=MAP_HEIGHT,
        center=map_view["center"],
        zoom=map_view["zoom"],
        returned_objects=[
            "last_clicked",
            "last_object_clicked",
            "last_object_clicked_point_index",
        ],
        use_container_width=True,
        key=map_widget_key(),
    )

    if map_data and process_map_state(map_data):
        request_rerun()

    return map_data


def render_map_interface() -> dict | None:
    """Main function to render the complete map interface.

    Returns
    -------
    dict or None
        The map data returned from st_folium for further processing.
    """
    render_search_section()

    ensure_basemap_picker_state()
    sync_map_view_to_points()
    map_data = _render_interactive_map(resolve_basemap_name())

    if st.session_state.points:
        render_location_table_expander()
    render_display_settings_expander()

    return map_data
