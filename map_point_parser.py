from typing import Optional

import folium
import hashlib
import pandas as pd
import requests
import streamlit as st
from jinja2 import Template
from streamlit_folium import st_folium

from click_to_geojson_functionality import add_point
from styling import DEFAULT_BUTTON_COLOR

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "click2vector/0.9.0"
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


def request_rerun() -> None:
    """Defer rerun until after widgets below the map have rendered."""
    st.session_state.pending_rerun = True


def get_default_map_view() -> dict:
    """Return a sensible initial map center and zoom level.

    Returns
    -------
    dict
        Map view with ``center`` and ``zoom`` keys.
    """
    if st.session_state.points:
        lon, lat = st.session_state.points[-1]["geometry"]["coordinates"]
        return {"center": [lat, lon], "zoom": 14}

    return {"center": [20, 0], "zoom": 2}


def update_map_view_from_data(map_data: dict) -> None:
    """Persist the current map center and zoom from st_folium output.

    Parameters
    ----------
    map_data : dict
        The map data returned from st_folium.

    Returns
    -------
    None
        Updates ``last_map_view`` in session state.
    """
    if not map_data:
        return

    center = map_data.get("center")
    zoom = map_data.get("zoom")
    if center is None or zoom is None:
        return

    st.session_state.last_map_view = {
        "center": [center["lat"], center["lng"]],
        "zoom": zoom,
    }


def set_map_view(lat: float, lon: float, zoom: int = 14) -> None:
    """Set the map view to a specific location and zoom level.

    Parameters
    ----------
    lat : float
        Latitude for the map center.
    lon : float
        Longitude for the map center.
    zoom : int, optional
        Zoom level to use. Defaults to 14.

    Returns
    -------
    None
        Updates ``last_map_view`` in session state.
    """
    st.session_state.last_map_view = {"center": [lat, lon], "zoom": zoom}


def geocode_place_name(query: str) -> Optional[dict]:
    """Look up a place name using the Nominatim geocoding API.

    Parameters
    ----------
    query : str
        Place name or address to search for.

    Returns
    -------
    dict or None
        Dictionary with ``lat``, ``lng``, and ``name`` keys, or None if not found.
    """
    response = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "jsonv2", "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None

    place = results[0]
    return {
        "lat": float(place["lat"]),
        "lng": float(place["lon"]),
        "name": place.get("display_name", query),
    }


def add_searched_place(lat: float, lng: float, name: str) -> None:
    """Add a geocoded place to the map and point table.

    Parameters
    ----------
    lat : float
        Latitude of the place.
    lng : float
        Longitude of the place.
    name : str
        Display name for the new point.

    Returns
    -------
    None
        Updates session state with the new point and map view.
    """
    add_point(lat, lng, name)
    st.session_state.last_click = (lat, lng)
    set_map_view(lat, lng)


def render_place_search() -> None:
    """Render a search field that geocodes a place and adds it as a point."""
    with st.form("place_search_form"):
        search_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
        with search_col:
            query = st.text_input(
                "Search for a place to add",
                placeholder="e.g. University of California, Los Angeles",
            )
        with button_col:
            submitted = st.form_submit_button("Add pin", type="primary")

        if submitted and query.strip():
            place = geocode_place_name(query.strip())
            if place is None:
                st.session_state.message = (
                    f"No results found for '{query.strip()}'."
                )
            else:
                add_searched_place(place["lat"], place["lng"], place["name"])
                request_rerun()


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
            window.map.eachLayer(function(layer) {
                if (layer instanceof L.Marker && !layer._dragUpdateBound) {
                    layer._dragUpdateBound = true;
                    layer.on("dragend", function(event) {
                        var latlng = event.target.getLatLng();
                        window.__GLOBAL_DATA__.last_object_clicked = latlng;
                        try {
                            if (
                                event.target.getTooltip &&
                                event.target._tooltip
                            ) {
                                var content = event.target.getTooltip()
                                    .getContent();
                                if (typeof content === "function") {
                                    content = content(event.target);
                                }
                                if (typeof extractContent === "function") {
                                    window.__GLOBAL_DATA__
                                        .last_object_clicked_tooltip =
                                        extractContent(content);
                                }
                            }
                        } catch (error) {}
                        if (typeof debouncedUpdateComponentValue
                            === "function") {
                            debouncedUpdateComponentValue(window.map);
                        }
                    });
                }
            });
        }
        bindMarkerDragUpdates();
        if (window.map) {
            window.map.on("layeradd", bindMarkerDragUpdates);
        }
        {% endmacro %}
        """
    )
    drag_handler.add_to(map_object)


def add_compact_attribution_style(map_object: folium.Map) -> None:
    """Use a smaller Leaflet attribution control on the map.

    Parameters
    ----------
    map_object : folium.Map
        The folium map to style.

    Returns
    -------
    None
        Injects compact-attribution CSS into the map HTML.
    """
    from folium import Element

    map_object.get_root().html.add_child(
        Element(
            """
            <style>
                .leaflet-control-attribution {
                    font-size: 9px !important;
                    padding: 0 4px !important;
                    line-height: 1.1 !important;
                }
                .leaflet-control-attribution a {
                    font-size: 9px !important;
                }
            </style>
            """
        )
    )


def create_map_with_features(basemap_name):
    """Create a folium map with search and mini-map features.

    Parameters
    ----------
    basemap_name : str
        The name of the basemap to use.

    Returns
    -------
    folium.Map
        A configured folium map with search and mini-map features.
    """
    # Get the user's last map view, or use a reasonable default
    last_view = st.session_state.get("last_map_view", get_default_map_view())

    map_object = folium.Map(
        location=last_view["center"],
        zoom_start=last_view["zoom"],
        tiles=basemap_name,
    )

    # Add an inset map (mini map) when enabled
    if st.session_state.get("show_inset_map", False):
        mini_map = folium.plugins.MiniMap(
            tile_layer=basemap_name,
            position="bottomright",
            width=150,
            height=150,
            collapsed_width=25,
            collapsed_height=25,
            zoom_level_offset=-5,
        )
        map_object.add_child(mini_map)

    add_compact_attribution_style(map_object)

    return map_object


def get_unique_descriptions(points: list[dict]) -> list[str]:
    """Return sorted unique description values across all points.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.

    Returns
    -------
    list of str
        Sorted unique descriptions; empty string means no description.
    """
    return sorted(
        {
            point["properties"].get("description", "").strip()
            for point in points
        }
    )


def sync_description_color_state(points: list[dict], default_color: str) -> None:
    """Assign default colors to new descriptions and drop stale entries.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.
    default_color : str
        Default pin color used when assigning palette colors.

    Returns
    -------
    None
        Updates ``description_colors`` in session state.
    """
    if "description_colors" not in st.session_state:
        st.session_state.description_colors = {}

    unique_descriptions = get_unique_descriptions(points)
    palette = [
        color
        for color in DESCRIPTION_COLOR_PALETTE
        if color.lower() != default_color.lower()
    ]
    if not palette:
        palette = DESCRIPTION_COLOR_PALETTE

    for index, description in enumerate(unique_descriptions):
        if description not in st.session_state.description_colors:
            if len(unique_descriptions) == 1:
                st.session_state.description_colors[description] = default_color
            else:
                st.session_state.description_colors[description] = palette[
                    index % len(palette)
                ]

    for stale_description in set(st.session_state.description_colors) - set(
        unique_descriptions
    ):
        del st.session_state.description_colors[stale_description]


def sync_description_colors_from_pickers(points: list[dict]) -> None:
    """Copy color picker widget values into ``description_colors``.

    Streamlit updates widget session state before the script runs, but the map
    is rendered above the pickers. Syncing here ensures marker colors reflect
    the latest picker values on the same rerun.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.

    Returns
    -------
    None
        Updates ``description_colors`` in session state.
    """
    if "description_colors" not in st.session_state:
        st.session_state.description_colors = {}

    for description in get_unique_descriptions(points):
        picker_key = f"desc_color_picker_{_description_color_widget_key(description)}"
        if picker_key in st.session_state:
            st.session_state.description_colors[description] = st.session_state[
                picker_key
            ]


def _description_color_widget_key(description: str) -> str:
    """Return a stable widget key suffix for a description value.

    Parameters
    ----------
    description : str
        Point description text.

    Returns
    -------
    str
        Short hash string safe for Streamlit widget keys.
    """
    return hashlib.sha256(description.encode()).hexdigest()[:16]


def resolve_point_color(description: str, default_color: str) -> str:
    """Return the marker color for a point from its description.

    Parameters
    ----------
    description : str
        Point description text.
    default_color : str
        Fallback color when no mapping exists yet.

    Returns
    -------
    str
        Hex color code for the marker.
    """
    normalized = (description or "").strip()
    return st.session_state.get("description_colors", {}).get(
        normalized, default_color
    )


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

    for point_index, point in enumerate(st.session_state.points):
        coords = point["geometry"]["coordinates"]
        description = point["properties"].get("description", "")
        pin_color = resolve_point_color(description, default_color)

        folium.Marker(
            location=[coords[1], coords[0]],  # Note: folium uses [lat, lon]
            tooltip=f"Point {point_index + 1}: {point['properties']['name']}",
            icon=make_pin_div_icon(pin_color),
            draggable=True,
        ).add_to(map_object)


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


def _point_index_from_tooltip(tooltip: str) -> Optional[int]:
    """Parse a point index from a marker tooltip label.

    Parameters
    ----------
    tooltip : str
        Marker tooltip text in the form ``Point N: name``.

    Returns
    -------
    int or None
        Zero-based point index, or None if parsing fails.
    """
    if not tooltip.startswith("Point "):
        return None

    try:
        point_number = int(tooltip.split(":", maxsplit=1)[0].replace("Point ", ""))
    except ValueError:
        return None

    return point_number - 1


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
        tooltip = map_data.get("last_object_clicked_tooltip") or ""
        point_index = _point_index_from_tooltip(tooltip)
        if point_index is None:
            return False

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


def handle_map_interactions(map_data: dict) -> bool:
    """Handle click and drag interactions on the map.

    Parameters
    ----------
    map_data : dict
        The map data returned from st_folium.

    Returns
    -------
    bool
        True if map state changed, False otherwise.
    """
    if handle_map_clicks(map_data):
        return True
    return handle_marker_drag(map_data)


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
    return handle_map_interactions(map_state)


def create_point_management_controls():
    """Create controls for managing points (remove last, clear all).

    Returns
    -------
    None
        Renders point management buttons in the Streamlit interface.
    """
    col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1])

    with col2:
        if st.button("Remove Last Point", key="remove_last_point"):
            try:
                st.session_state.points.pop()
                request_rerun()
            except IndexError:
                # No points to remove
                pass

    with col3:
        if st.button("Clear All Points", key="clear_all_points_quick"):
            try:
                from click_to_geojson_functionality import reset_points

                reset_points()
                request_rerun()
            except Exception:
                # No points to clear or other error
                pass


def create_point_table():
    """Create an interactive table for viewing and managing points.

    Returns
    -------
    None
        Renders an interactive data table for point management.
    """
    with st.expander("Point Table", expanded=True):
        # Show points in a table
        points_data = []
        for point_index, point in enumerate(st.session_state.points):
            coords = point["geometry"]["coordinates"]
            # Start with basic info
            row_data = {
                "Name": point["properties"]["name"],
                "Description": point["properties"].get("description", ""),
                "Latitude": coords[1],
                "Longitude": coords[0],
                "Index": point_index,
            }

            # Add all other properties
            for key, value in point["properties"].items():
                if key not in [
                    "name",
                    "description",
                    "timestamp",
                ]:
                    row_data[key] = value

            points_data.append(row_data)

        df = pd.DataFrame(points_data)

        # Show all columns except Index
        display_columns = [col for col in df.columns if col != "Index"]

        # Use data editor for interactive row selection and editing
        edited_df = st.data_editor(
            df[display_columns],
            width="stretch",
            key="points_table",
            column_config={
                "Name": st.column_config.TextColumn("Name", disabled=False),
                "Description": st.column_config.TextColumn(
                    "Description", disabled=False
                ),
                "Latitude": st.column_config.NumberColumn(
                    "Latitude", format="%.6f", disabled=True
                ),
                "Longitude": st.column_config.NumberColumn(
                    "Longitude", format="%.6f", disabled=True
                ),
            },
        )

        # Handle name and description changes
        if edited_df is not None:
            for i, row in edited_df.iterrows():
                try:
                    st.session_state.points[i]["properties"]["name"] = row["Name"]
                    st.session_state.points[i]["properties"]["description"] = row[
                        "Description"
                    ]
                except IndexError:
                    # Skip if this is the extra "add row" row
                    pass

        render_description_color_table()

        # Handle row selection for deletion
        try:
            selected_rows = st.session_state.points_table.get("selected_rows", [])
            if selected_rows:
                # Delete selected points (in reverse order to maintain indices)
                for row in reversed(selected_rows):
                    try:
                        index_to_remove = row["Index"]
                        if 0 <= index_to_remove < len(st.session_state.points):
                            st.session_state.points.pop(index_to_remove)
                    except (KeyError, IndexError):
                        # Invalid row data or index
                        continue
                request_rerun()
        except (KeyError, AttributeError):
            # No points_table in session state or no selected_rows
            pass


def _sync_description_color(description: str) -> None:
    """Persist one description color picker value in session state."""
    picker_key = f"desc_color_picker_{_description_color_widget_key(description)}"
    st.session_state.description_colors[description] = st.session_state[picker_key]


def render_description_color_table() -> None:
    """Render unique descriptions and a pin color picker for each."""
    default_color = st.session_state.get("pin_color", DEFAULT_BUTTON_COLOR)
    sync_description_color_state(st.session_state.points, default_color)

    unique_descriptions = get_unique_descriptions(st.session_state.points)
    st.markdown("**Pin colors by description**")
    header_desc, header_color = st.columns([3, 1])
    with header_desc:
        st.markdown("Description")
    with header_color:
        st.markdown("Pin color")

    for description in unique_descriptions:
        label = description or "(No description)"
        desc_col, color_col = st.columns([3, 1])
        with desc_col:
            st.text(label)
        with color_col:
            picker_key = (
                f"desc_color_picker_{_description_color_widget_key(description)}"
            )
            if picker_key not in st.session_state:
                st.session_state[picker_key] = st.session_state.description_colors[
                    description
                ]
            st.color_picker(
                label,
                key=picker_key,
                label_visibility="collapsed",
                on_change=_sync_description_color,
                args=(description,),
            )
            _sync_description_color(description)


def render_map_interface(basemap_name):
    """Main function to render the complete map interface.

    Parameters
    ----------
    basemap_name : str
        The name of the basemap to use.

    Returns
    -------
    dict
        The map data returned from st_folium for further processing.
    """
    # Create map with features
    render_place_search()

    map_object = create_map_with_features(basemap_name)
    map_view = st.session_state.get("last_map_view", get_default_map_view())

    # Add existing points to map
    add_existing_points_to_map(map_object)
    add_draggable_marker_handlers(map_object)

    # Display the map and capture clicks
    map_data = st_folium(
        map_object,
        height=300,
        center=map_view["center"],
        zoom=map_view["zoom"],
        returned_objects=[
            "last_clicked",
            "last_object_clicked",
            "last_object_clicked_tooltip",
        ],
        use_container_width=True,
        key="click2vector_map",
    )

    if map_data and process_map_state(map_data):
        request_rerun()

    # Show point management controls if points exist
    if st.session_state.points:
        create_point_management_controls()
        create_point_table()

    return map_data
