"""Map viewport state and folium map construction."""

import hashlib
import math

import folium
import streamlit as st

MAP_HEIGHT = 500


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
    return {"center": [20, 0], "zoom": 2}


BOUNDS_PADDING = 0.08
BOUNDS_MIN_SPAN = 0.05
MAP_VIEW_HEIGHT_PX = 300


def get_points_bounds(points: list[dict]) -> list[list[float]] | None:
    """Return southwest and northeast corners that contain all points.

    Parameters
    ----------
    points : list of dict
        GeoJSON-like point features from session state.

    Returns
    -------
    list of list of float or None
        Bounds as ``[[south, west], [north, east]]``, or ``None`` when empty.
    """
    if not points:
        return None

    lats: list[float] = []
    lons: list[float] = []
    for point in points:
        lon, lat = point["geometry"]["coordinates"]
        lats.append(lat)
        lons.append(lon)

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    if max_lat - min_lat < BOUNDS_MIN_SPAN:
        mid_lat = (min_lat + max_lat) / 2
        min_lat = mid_lat - BOUNDS_MIN_SPAN / 2
        max_lat = mid_lat + BOUNDS_MIN_SPAN / 2
    if max_lon - min_lon < BOUNDS_MIN_SPAN:
        mid_lon = (min_lon + max_lon) / 2
        min_lon = mid_lon - BOUNDS_MIN_SPAN / 2
        max_lon = mid_lon + BOUNDS_MIN_SPAN / 2

    lat_pad = (max_lat - min_lat) * BOUNDS_PADDING
    lon_pad = (max_lon - min_lon) * BOUNDS_PADDING
    return [
        [min_lat - lat_pad, min_lon - lon_pad],
        [max_lat + lat_pad, max_lon + lon_pad],
    ]


def bounds_to_map_view(bounds: list[list[float]]) -> dict:
    """Convert map bounds to a folium center and zoom level.

    Parameters
    ----------
    bounds : list of list of float
        Bounds as ``[[south, west], [north, east]]``.

    Returns
    -------
    dict
        Map view with ``center`` and ``zoom`` keys.
    """
    south, west = bounds[0]
    north, east = bounds[1]
    center_lat = (south + north) / 2
    center_lon = (west + east) / 2

    lat_span = max(north - south, 1e-6)
    lon_span = max(east - west, 1e-6)
    lat_rad = math.radians(center_lat)
    effective_lon_span = max(lon_span * math.cos(lat_rad), 1e-6)
    max_span = max(lat_span, effective_lon_span)

    zoom = math.log2(MAP_VIEW_HEIGHT_PX * 360 / (256 * max_span))
    return {
        "center": [center_lat, center_lon],
        "zoom": int(max(1, min(18, zoom))),
    }


def _points_view_fingerprint(points: list[dict]) -> str:
    """Return a stable hash for the current point locations."""
    if not points:
        return "empty"

    parts = sorted(
        f"{round(lon, 4)},{round(lat, 4)}"
        for point in points
        for lon, lat in [point["geometry"]["coordinates"]]
    )
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{len(points)}:{digest}"


def sync_map_view_to_points() -> None:
    """Fit the map view when the stored point locations change."""
    points = st.session_state.points
    fingerprint = _points_view_fingerprint(points)
    if st.session_state.get("points_view_fingerprint") == fingerprint:
        return

    st.session_state.points_view_fingerprint = fingerprint
    if not points:
        st.session_state.last_map_view = get_default_map_view()
        return

    bounds = get_points_bounds(points)
    if bounds is not None:
        st.session_state.last_map_view = bounds_to_map_view(bounds)


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
    """Create a folium map with optional mini-map overlay.

    Parameters
    ----------
    basemap_name : str
        The name of the basemap to use.

    Returns
    -------
    folium.Map
        A configured folium map.
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
