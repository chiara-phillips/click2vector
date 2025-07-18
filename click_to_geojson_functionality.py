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

import fiona
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
    if isinstance(name_or_properties, dict):
        # Use provided properties, add timestamp
        properties = name_or_properties.copy()
        properties["timestamp"] = datetime.now().isoformat()
        # Add a name if not present
        if "name" not in properties:
            properties["name"] = f"Point {len(st.session_state.points) + 1}"
    else:
        # Use string as name
        properties = {
            "name": (
                name_or_properties
                if name_or_properties
                else f"Point {len(st.session_state.points) + 1}"
            ),
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
    if export_type == "GeoJSON":
        return json.dumps(create_geojson(), indent=2)
    elif export_type == "Esri Shapefile (.zip)":
        try:
            shp_buffer = io.BytesIO()
            with zipfile.ZipFile(shp_buffer, mode="w") as shapefile_zip:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir)

                    # Create schema for shapefile
                    schema = {"geometry": "Point", "properties": {}}

                    # Add properties to schema
                    if st.session_state.points:
                        sample_props = st.session_state.points[0]["properties"]
                        for key, value in sample_props.items():
                            if isinstance(value, str):
                                schema["properties"][key] = "str:255"
                            elif isinstance(value, (int, float)):
                                schema["properties"][key] = "float"
                            else:
                                schema["properties"][key] = "str:255"

                    # Write shapefile using fiona directly
                    with fiona.open(
                        tmp_path / "points.shp",
                        "w",
                        driver="ESRI Shapefile",
                        schema=schema,
                        crs="EPSG:4326",
                    ) as dst:
                        for point in st.session_state.points:
                            lon, lat = point["geometry"]["coordinates"]
                            feature = {
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [lon, lat],
                                },
                                "properties": point["properties"],
                            }
                            dst.write(feature)

                    # Add all shapefile files to zip
                    for file_path in tmp_path.iterdir():
                        shapefile_zip.write(file_path, arcname=file_path.name)

            shp_buffer.seek(0)
            return shp_buffer.getvalue()

        except Exception as export_error:
            st.error(f"Error exporting Shapefile: {str(export_error)}")
            return b""
    elif export_type == "FlatGeobuf":
        try:
            fgb_buffer = io.BytesIO()

            # Create schema for flatgeobuf
            schema = {"geometry": "Point", "properties": {}}

            # Add properties to schema
            if st.session_state.points:
                sample_props = st.session_state.points[0]["properties"]
                for key, value in sample_props.items():
                    if isinstance(value, str):
                        schema["properties"][key] = "str:255"
                    elif isinstance(value, (int, float)):
                        schema["properties"][key] = "float"
                    else:
                        schema["properties"][key] = "str:255"

            # Write flatgeobuf using temporary file then read into buffer
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / "points.fgb"

                with fiona.open(
                    str(tmp_path),
                    "w",
                    driver="FlatGeobuf",
                    schema=schema,
                    crs="EPSG:4326",
                ) as dst:
                    for point in st.session_state.points:
                        lon, lat = point["geometry"]["coordinates"]
                        feature = {
                            "geometry": {"type": "Point", "coordinates": [lon, lat]},
                            "properties": point["properties"],
                        }
                        dst.write(feature)

                # Read the file back into the buffer
                with open(tmp_path, "rb") as fgb_file:
                    fgb_buffer.write(fgb_file.read())

            fgb_buffer.seek(0)
            return fgb_buffer.getvalue()

        except Exception as export_error:
            st.error(f"Error exporting FlatGeobuf: {str(export_error)}")
            return b""
    else:
        return b""
