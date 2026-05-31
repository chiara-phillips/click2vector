"""Point session-state management and GeoDataFrame conversion."""

from datetime import datetime

import geopandas as gpd
import streamlit as st
from shapely.geometry import Point


def add_point(
    lat: float,
    lon: float,
    name_or_properties: str | dict = "",
) -> None:
    """Add a point to the session state.

    Parameters
    ----------
    lat : float
        The latitude coordinate of the point.
    lon : float
        The longitude coordinate of the point.
    name_or_properties : str or dict, optional
        Either a string name for the point or a dictionary of properties.
        Defaults to empty string.

    Returns
    -------
    None
        Adds the point to st.session_state.points.
    """
    try:
        properties = name_or_properties.copy()
        properties["timestamp"] = datetime.now().isoformat()
        if "name" not in properties:
            properties["name"] = f"Point {len(st.session_state.points) + 1}"
    except AttributeError:
        properties = {
            "name": (
                name_or_properties
                if name_or_properties
                else f"Point {len(st.session_state.points) + 1}"
            ),
            "description": "",
            "timestamp": datetime.now().isoformat(),
        }

    point = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties,
    }
    st.session_state.points.append(point)


def points_to_gdf(points: list[dict]) -> gpd.GeoDataFrame:
    """Convert session points (GeoJSON features) to a GeoDataFrame.

    Parameters
    ----------
    points : list of dict
        List of GeoJSON feature dictionaries.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing the points with their properties.
    """
    if not points:
        return gpd.GeoDataFrame()

    geometries = []
    properties_list = []

    for pt in points:
        lon, lat = pt["geometry"]["coordinates"]
        geometries.append(Point(lon, lat))
        properties = {
            key: value
            for key, value in pt["properties"].items()
            if key not in ("lat", "lon")
        }
        properties_list.append({"lat": lat, "lon": lon, **properties})

    gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs="EPSG:4326")

    return gdf
