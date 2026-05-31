"""Map click and marker drag interaction handlers."""

import folium
import streamlit as st
from jinja2 import Template

from map_ui.view import get_default_map_view, set_map_view, update_map_view_from_data
from points.session import add_point

def add_draggable_marker_handlers(map_object: folium.Map) -> None:
    """Report marker drag events to streamlit-folium.

    Parameters
    ----------
    map_object : folium.Map
        The folium map to attach drag handlers to.

    Returns
    -------
    None
        Adds a JavaScript macro element to the map.
    """
    drag_handler = folium.MacroElement()
    drag_handler._template = Template(
        """
        {% macro script(this, kwargs) %}
        function bindMarkerDragUpdates() {
            if (!window.map || !window.__GLOBAL_DATA__) {
                return;
            }
            function bindMarkerDragOnLayer(layer) {
                if (layer instanceof L.MarkerClusterGroup) {
                    layer.eachLayer(bindMarkerDragOnLayer);
                    return;
                }
                if (layer instanceof L.Marker && !layer._dragUpdateBound) {
                    layer._dragUpdateBound = true;
                    layer.on("dragend", function(event) {
                        var latlng = event.target.getLatLng();
                        window.__GLOBAL_DATA__.last_object_clicked = latlng;
                        if (event.target.options.pointIndex !== undefined) {
                            window.__GLOBAL_DATA__.last_object_clicked_point_index =
                                event.target.options.pointIndex;
                        }
                        if (typeof debouncedUpdateComponentValue
                            === "function") {
                            debouncedUpdateComponentValue(window.map);
                        }
                    });
                }
            }
            window.map.eachLayer(bindMarkerDragOnLayer);
        }
        bindMarkerDragUpdates();
        if (window.map) {
            window.map.on("layeradd", bindMarkerDragUpdates);
        }
        {% endmacro %}
        """
    )
    drag_handler.add_to(map_object)

def handle_map_clicks(map_data):
    """Handle map click events and add new points.

    Parameters
    ----------
    map_data : dict
        The map data returned from st_folium containing click information.

    Returns
    -------
    bool
        True if a new point was added, False otherwise.
    """
    try:
        clicked_data = map_data["last_clicked"]
        clicked_lat = clicked_data["lat"]
        clicked_lon = clicked_data["lng"]

        # Check if this is a new click (avoid duplicate additions)
        last_click = st.session_state.get("last_click")
        if last_click != (clicked_lat, clicked_lon):
            add_point(clicked_lat, clicked_lon)
            st.session_state.last_click = (clicked_lat, clicked_lon)
            current_view = st.session_state.get(
                "last_map_view", get_default_map_view()
            )
            set_map_view(clicked_lat, clicked_lon, current_view["zoom"])
            return True

    except (KeyError, TypeError):
        # No click data or invalid format
        pass

    return False  # No new point was added


def handle_marker_drag(map_data: dict) -> bool:
    """Update a point when the user drags its marker.

    Parameters
    ----------
    map_data : dict
        The map data returned from st_folium.

    Returns
    -------
    bool
        True if a point moved, False otherwise.
    """
    try:
        clicked = map_data["last_object_clicked"]
        raw_index = map_data.get("last_object_clicked_point_index")
        if raw_index is None:
            return False
        point_index = int(raw_index)

        lat = clicked["lat"]
        lng = clicked["lng"]
        drag_key = (point_index, round(lat, 6), round(lng, 6))
        if st.session_state.get("last_drag") == drag_key:
            return False

        point = st.session_state.points[point_index]
        existing_lon, existing_lat = point["geometry"]["coordinates"]
        if (
            abs(existing_lon - lng) < 1e-8
            and abs(existing_lat - lat) < 1e-8
        ):
            return False

        point["geometry"]["coordinates"] = [lng, lat]
        st.session_state.last_drag = drag_key
        return True

    except (KeyError, TypeError, IndexError):
        return False


def process_map_state(map_state: dict) -> bool:
    """Update the map view and apply map interaction handlers.

    Parameters
    ----------
    map_state : dict
        Current st_folium component state.

    Returns
    -------
    bool
        True if map state changed, False otherwise.
    """
    if not map_state:
        return False

    update_map_view_from_data(map_state)
    if handle_map_clicks(map_state):
        return True
    return handle_marker_drag(map_state)
