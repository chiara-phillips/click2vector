from typing import Optional

import folium
import hashlib
import html
import pandas as pd
import requests
import streamlit as st
from jinja2 import Template
from streamlit_folium import st_folium

from click_to_geojson_functionality import add_point
from google_sheets_parser import import_from_google_sheets
from styling import DEFAULT_BUTTON_COLOR

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "click2vector/0.9.1"
BASEMAP_OPTIONS = ["CartoDB Positron", "OpenStreetMap"]
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
TABLE_COLUMN_TO_PROPERTY = {
    "Name": "name",
    "Description": "description",
}
COLOR_TABLE_COLUMNS = [2, 2, 1]


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


def sync_basemap_choice() -> None:
    """Persist basemap selection across reruns triggered before widgets render."""
    st.session_state.basemap_name = st.session_state.basemap_picker


def sync_pin_color_choice() -> None:
    """Persist pin color across reruns triggered before widgets render."""
    st.session_state.pin_color = st.session_state.pin_color_picker


def sync_map_style_from_pickers() -> None:
    """Copy widget values into persistent map style session state."""
    if "basemap_picker" in st.session_state:
        st.session_state.basemap_name = st.session_state.basemap_picker
    if "pin_color_picker" in st.session_state:
        st.session_state.pin_color = st.session_state.pin_color_picker


def render_search_section() -> None:
    """Render place search and advanced map or import options."""
    with st.container(border=False):
        with st.form("place_search_form", border=False):
            query = st.text_input(
                "Search for a place to add",
                placeholder="e.g. Berlin",
            )
            submitted = st.form_submit_button("\u200b")

            if submitted and query.strip():
                place = geocode_place_name(query.strip())
                if place is None:
                    st.session_state.message = (
                        f"No results found for '{query.strip()}'."
                    )
                else:
                    add_searched_place(place["lat"], place["lng"], place["name"])
                    request_rerun()

        with st.expander("Advanced options", expanded=False, type="compact"):
            sheets_url = st.text_input(
                "Public Google Sheet URL with `lat` and `lon` columns:",
                placeholder="https://docs.google.com/spreadsheets/d/...#gid=0",
                key="sheets_url_input",
            )
            coordinate_format = st.radio(
                "Coordinate format to import from Google Sheet (if applicable):",
                options=["Lat/Long", "WKT Geometry"],
                index=0,
                horizontal=True,
            )
            use_wkt = coordinate_format == "WKT Geometry"
            if "basemap_picker" not in st.session_state:
                st.session_state.basemap_picker = st.session_state.basemap_name
            if "pin_color_picker" not in st.session_state:
                st.session_state.pin_color_picker = st.session_state.pin_color
            st.radio(
                "Basemap options:",
                options=BASEMAP_OPTIONS,
                horizontal=True,
                key="basemap_picker",
                on_change=sync_basemap_choice,
            )
            st.checkbox("Show inset map", key="show_inset_map")
            if not st.session_state.points:
                st.color_picker(
                    "Default pin color:",
                    key="pin_color_picker",
                    on_change=sync_pin_color_choice,
                )
            sync_map_style_from_pickers()

            if sheets_url and sheets_url != st.session_state.get(
                "last_sheets_url", ""
            ):
                st.session_state.last_sheets_url = sheets_url
                success = import_from_google_sheets(sheets_url, use_wkt)
                if success:
                    request_rerun()


def render_place_search() -> None:
    """Render a search field that geocodes a place and adds it as a point."""
    render_search_section()


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

    folium.plugins.Fullscreen(
        position="topright",
        force_separate_button=True,
    ).add_to(map_object)

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


def get_property_key(column_name: str) -> str:
    """Return the point property key for a table column label.

    Parameters
    ----------
    column_name : str
        Display name from the point table.

    Returns
    -------
    str
        Property key stored on each point.
    """
    return TABLE_COLUMN_TO_PROPERTY.get(column_name, column_name)


def get_colorable_columns(points: list[dict]) -> list[str]:
    """Return table columns that can drive pin colors.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.

    Returns
    -------
    list of str
        Column labels shown in the color-by dropdown.
    """
    columns = ["Name", "Description"]
    seen = set(columns)
    for point in points:
        for key in point["properties"]:
            if key in ("name", "description", "timestamp"):
                continue
            if key not in seen:
                columns.append(key)
                seen.add(key)
    return columns


def get_point_property_value(point: dict, property_key: str) -> str:
    """Return one normalized property value from a point.

    Parameters
    ----------
    point : dict
        GeoJSON feature dictionary.
    property_key : str
        Property key to read from the point.

    Returns
    -------
    str
        Stripped string value for the property.
    """
    return str(point["properties"].get(property_key, "")).strip()


def get_unique_property_values(points: list[dict], property_key: str) -> list[str]:
    """Return sorted unique values for one property across all points.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.
    property_key : str
        Property key to collect values from.

    Returns
    -------
    list of str
        Sorted unique property values; empty string means no value set.
    """
    return sorted(
        {get_point_property_value(point, property_key) for point in points}
    )


def _get_property_colors(property_key: str) -> dict[str, str]:
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
    colors = _get_property_colors(property_key)
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
    colors = _get_property_colors(property_key)
    for value in get_unique_property_values(points, property_key):
        picker_key = _property_color_widget_key(property_key, value)
        if picker_key in st.session_state:
            colors[value] = st.session_state[picker_key]


def _property_color_widget_key(property_key: str, value: str) -> str:
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


def _get_legend_display_names(property_key: str) -> dict[str, str]:
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
    stored = _get_legend_display_names(property_key).get(value)
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
    names = _get_legend_display_names(property_key)
    unique_values = get_unique_property_values(points, property_key)
    for value in unique_values:
        widget_key = _legend_label_widget_key(property_key, value)
        if widget_key in st.session_state:
            names[value] = st.session_state[widget_key]
    for stale_value in set(names) - set(unique_values):
        del names[stale_value]


def _legend_label_widget_key(property_key: str, value: str) -> str:
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
    color_by_column = st.session_state.get("color_by_column", "Description")
    property_key = get_property_key(color_by_column)

    for point_index, point in enumerate(st.session_state.points):
        coords = point["geometry"]["coordinates"]
        value = get_point_property_value(point, property_key)
        pin_color = resolve_point_color(property_key, value, default_color)

        folium.Marker(
            location=[coords[1], coords[0]],  # Note: folium uses [lat, lon]
            tooltip=f"Point {point_index + 1}: {point['properties']['name']}",
            icon=make_pin_div_icon(pin_color),
            draggable=True,
        ).add_to(map_object)


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
    color_by_column = st.session_state.get("color_by_column", "Description")
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
            f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
            f'<span style="background:{color};width:12px;height:12px;'
            f"border-radius:50%;border:1px solid #ccc;flex-shrink:0;"
            f'margin-right:8px;"></span>'
            f'<span style="font-size:12px;line-height:1.2;">{safe_label}</span>'
            f"</div>"
        )

    if not legend_rows:
        return

    legend_html = (
        '<div style="position:absolute;bottom:24px;left:10px;z-index:1000;'
        "background:white;border:1px solid #ccc;border-radius:4px;"
        'padding:8px 10px;max-width:220px;">'
        f'{"".join(legend_rows)}</div>'
    )
    map_object.get_root().html.add_child(Element(legend_html))


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


def _sync_points_table_changes() -> None:
    """Apply row deletions and edits from the point table data editor."""
    state = st.session_state.get("points_table")
    if not state:
        return

    changed = False

    for idx in sorted(state.get("deleted_rows", []), reverse=True):
        if 0 <= idx < len(st.session_state.points):
            st.session_state.points.pop(idx)
            changed = True

    for idx, updates in state.get("edited_rows", {}).items():
        point_idx = int(idx)
        if 0 <= point_idx < len(st.session_state.points):
            properties = st.session_state.points[point_idx]["properties"]
            if "Name" in updates:
                properties["name"] = str(updates["Name"])
            if "Description" in updates:
                properties["description"] = str(updates["Description"])
            changed = True

    if changed:
        request_rerun()


def create_point_table():
    """Create an interactive table for viewing and managing points.

    Returns
    -------
    None
        Renders an interactive data table for point management.
    """
    with st.expander("Point Table", expanded=True, type="compact"):
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
            num_rows="delete",
            on_change=_sync_points_table_changes,
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

        if edited_df is not None:
            for i, row in edited_df.iterrows():
                try:
                    st.session_state.points[i]["properties"]["name"] = row["Name"]
                    st.session_state.points[i]["properties"]["description"] = row[
                        "Description"
                    ]
                except IndexError:
                    pass

        render_property_color_table()


def _sync_property_color(property_key: str, value: str) -> None:
    """Persist one property color picker value in session state."""
    picker_key = _property_color_widget_key(property_key, value)
    colors = _get_property_colors(property_key)
    colors[value] = st.session_state[picker_key]


def _sync_color_by_column() -> None:
    """Persist the selected color-by column across reruns."""
    st.session_state.color_by_column = st.session_state.color_by_column_picker


def _resolve_color_by_column(colorable_columns: list[str]) -> str:
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


def render_property_color_table() -> None:
    """Render the color-by column selector and pin color pickers."""
    default_color = st.session_state.get("pin_color", DEFAULT_BUTTON_COLOR)
    colorable_columns = get_colorable_columns(st.session_state.points)
    color_by_column = _resolve_color_by_column(colorable_columns)

    if "color_by_column_picker" not in st.session_state:
        st.session_state.color_by_column_picker = color_by_column
    elif st.session_state.color_by_column_picker not in colorable_columns:
        st.session_state.color_by_column_picker = color_by_column

    color_by_col, legend_toggle_col, _ = st.columns(
        COLOR_TABLE_COLUMNS, vertical_alignment="bottom"
    )
    with color_by_col:
        st.selectbox(
            "Color points by:",
            options=colorable_columns,
            key="color_by_column_picker",
            on_change=_sync_color_by_column,
        )
    with legend_toggle_col:
        st.checkbox("Show legend on map", key="show_map_legend")

    st.session_state.color_by_column = st.session_state.color_by_column_picker
    property_key = get_property_key(st.session_state.color_by_column)

    sync_property_color_state(st.session_state.points, property_key, default_color)

    unique_values = get_unique_property_values(
        st.session_state.points, property_key
    )
    colors = _get_property_colors(property_key)
    column_label = st.session_state.color_by_column
    legend_names = _get_legend_display_names(property_key)

    header_value, header_legend, header_color = st.columns(COLOR_TABLE_COLUMNS)
    with header_value:
        st.caption("Value")
    with header_legend:
        st.caption("Legend Display Name")
    with header_color:
        st.caption("Point Color")

    for value in unique_values:
        category_label = value or f"(No {column_label.lower()})"
        category_col, legend_col, color_col = st.columns(COLOR_TABLE_COLUMNS)
        with category_col:
            st.text(category_label)
        with legend_col:
            label_key = _legend_label_widget_key(property_key, value)
            if label_key not in st.session_state:
                st.session_state[label_key] = legend_names.get(
                    value, category_label
                )
            st.text_input(
                "Legend Display Name",
                key=label_key,
                label_visibility="collapsed",
            )
            legend_names[value] = st.session_state[label_key]
        with color_col:
            picker_key = _property_color_widget_key(property_key, value)
            if picker_key not in st.session_state:
                st.session_state[picker_key] = colors[value]
            st.color_picker(
                category_label,
                key=picker_key,
                label_visibility="collapsed",
                on_change=_sync_property_color,
                args=(property_key, value),
            )
            _sync_property_color(property_key, value)


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

    return map_data


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
    render_search_section()

    map_data = _render_interactive_map(basemap_name)

    # Show point management controls if points exist
    if st.session_state.points:
        create_point_table()

    return map_data
