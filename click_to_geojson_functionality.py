"""
This module contains the functionality for adding points to the session state
and creating a GeoJSON FeatureCollection.
"""

import io
import json
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import streamlit as st
from shapely.geometry import Point


def add_point(lat, lon, name_or_properties=""):
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
    # Handle both string names and dictionary properties
    try:
        # Try to use as dictionary first
        properties = name_or_properties.copy()
        properties["timestamp"] = datetime.now().isoformat()
        # Add a name if not present
        if "name" not in properties:
            properties["name"] = f"Point {len(st.session_state.points) + 1}"
    except AttributeError:
        # Not a dict, treat as string
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


def create_geojson():
    """Create a GeoJSON FeatureCollection from stored points.

    Returns
    -------
    dict
        A GeoJSON FeatureCollection containing all stored points.
    """
    return {"type": "FeatureCollection", "features": st.session_state.points}


def reset_points():
    """Clear all points from the session state.

    Returns
    -------
    None
        Clears st.session_state.points and resets last_click.
    """
    st.session_state.points = []
    st.session_state.last_click = None


def points_to_gdf(points):
    """Convert session points (GeoJSON features) to a GeoDataFrame.

    Parameters
    ----------
    points : list
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
        properties_list.append(pt["properties"].copy())

    gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs="EPSG:4326")

    return gdf


def get_base_filename():
    """Generate base filename with timestamp.

    Returns
    -------
    str
        A filename with format 'click2vector_YYYYMMDD_HHMMSS'.
    """
    return f"click2vector_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def _export_shapefile(gdf: gpd.GeoDataFrame) -> bytes:
    """Export data as shapefile.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.

    Returns
    -------
    bytes
        The shapefile data as bytes.
    """
    try:
        shp_buffer = io.BytesIO()
        with zipfile.ZipFile(shp_buffer, mode="w") as shapefile_zip:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / "points.shp"
                gdf.to_file(tmp_path, driver="ESRI Shapefile")

                for file_path in Path(tmpdir).iterdir():
                    shapefile_zip.write(file_path, arcname=file_path.name)

        shp_buffer.seek(0)
        return shp_buffer.getvalue()

    except Exception as export_error:
        st.error(f"Error exporting Shapefile: {str(export_error)}")
        return b""


def _export_flatgeobuf(gdf: gpd.GeoDataFrame) -> bytes:
    """Export data as FlatGeobuf.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.

    Returns
    -------
    bytes
        The FlatGeobuf data as bytes.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "points.fgb"
            gdf.to_file(tmp_path, driver="FlatGeobuf")
            return tmp_path.read_bytes()

    except Exception as export_error:
        st.error(f"Error exporting FlatGeobuf: {str(export_error)}")
        return b""


def _export_geojson_display():
    """Export data as GeoJSON in pretty-printed format for display.

    Returns
    -------
    str
        The GeoJSON data as a formatted string ready for display.
    """
    # Create the GeoJSON with pretty formatting for display
    geojson_data = create_geojson()
    # Use pretty formatting for easy reading
    return json.dumps(geojson_data, indent=2)


def export_data(gdf, export_type):
    """Export GeoDataFrame to the specified format.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.
    export_type : str
        The export format: "GeoJSON", "Esri Shapefile (.zip)", or "FlatGeobuf".

    Returns
    -------
    str or bytes
        The exported data as a string (GeoJSON) or bytes (Shapefile/FlatGeobuf).
    """
    # Use a mapping instead of if/elif chains
    export_functions = {
        "GeoJSON": lambda _: _export_geojson_display(),
        "Esri Shapefile (.zip)": _export_shapefile,
        "FlatGeobuf": _export_flatgeobuf,
    }

    try:
        return export_functions[export_type](gdf)
    except KeyError:
        # Unknown export type
        return b""
