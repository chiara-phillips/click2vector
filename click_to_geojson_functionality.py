import streamlit as st
from datetime import datetime
import geopandas as gpd
import json
import io
import zipfile
from pathlib import Path
import tempfile
import fiona
from shapely.geometry import Point


def add_point(lat, lon, name_or_properties=""):
    """Add a point to the session state"""
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
            "name": name_or_properties if name_or_properties else f"Point {len(st.session_state.points) + 1}",
            "timestamp": datetime.now().isoformat()
        }
    
    point = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": properties
    }
    st.session_state.points.append(point)


def create_geojson():
    """Create a GeoJSON FeatureCollection from stored points"""
    return {
        "type": "FeatureCollection",
        "features": st.session_state.points
    }


def reset_points():
    """Clear all points"""
    st.session_state.points = []
    st.session_state.last_click = None


def points_to_gdf(points):
    """Convert session points (GeoJSON features) to a GeoDataFrame."""
    if not points:
        return gpd.GeoDataFrame()
    
    # Always use the Shapely approach to avoid numpy compatibility issues
    from shapely.geometry import Point
    
    geometries = []
    properties_list = []
    
    for pt in points:
        lon, lat = pt["geometry"]["coordinates"]
        geometries.append(Point(lon, lat))
        properties_list.append(pt["properties"].copy())
    
    gdf = gpd.GeoDataFrame(
        properties_list,
        geometry=geometries,
        crs="EPSG:4326"
    )
    
    return gdf


def get_base_filename():
    """Generate base filename with timestamp."""
    return f"click2vector_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def export_data(gdf, export_type):
    """Export GeoDataFrame to the specified format."""
    if export_type == "GeoJSON":
        return json.dumps(create_geojson(), indent=2)
    elif export_type == "Esri Shapefile (.zip)":
        try:
            shp_buffer = io.BytesIO()
            with zipfile.ZipFile(shp_buffer, mode="w") as zf:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir)
                    
                    # Create schema for shapefile
                    schema = {
                        'geometry': 'Point',
                        'properties': {}
                    }
                    
                    # Add properties to schema
                    if st.session_state.points:
                        sample_props = st.session_state.points[0]["properties"]
                        for key, value in sample_props.items():
                            if isinstance(value, str):
                                schema['properties'][key] = 'str:255'
                            elif isinstance(value, (int, float)):
                                schema['properties'][key] = 'float'
                            else:
                                schema['properties'][key] = 'str:255'
                    
                    # Write shapefile using fiona directly
                    with fiona.open(
                        tmp_path / "points.shp",
                        'w',
                        driver='ESRI Shapefile',
                        schema=schema,
                        crs='EPSG:4326'
                    ) as dst:
                        for point in st.session_state.points:
                            lon, lat = point["geometry"]["coordinates"]
                            feature = {
                                'geometry': {
                                    'type': 'Point',
                                    'coordinates': [lon, lat]
                                },
                                'properties': point["properties"]
                            }
                            dst.write(feature)
                    
                    # Add all shapefile files to zip
                    for file_path in tmp_path.iterdir():
                        zf.write(file_path, arcname=file_path.name)
            
            shp_buffer.seek(0)
            return shp_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting Shapefile: {str(e)}")
            return b""
    elif export_type == "FlatGeobuf":
        try:
            fgb_buffer = io.BytesIO()
            
            # Create schema for flatgeobuf
            schema = {
                'geometry': 'Point',
                'properties': {}
            }
            
            # Add properties to schema
            if st.session_state.points:
                sample_props = st.session_state.points[0]["properties"]
                for key, value in sample_props.items():
                    if isinstance(value, str):
                        schema['properties'][key] = 'str:255'
                    elif isinstance(value, (int, float)):
                        schema['properties'][key] = 'float'
                    else:
                        schema['properties'][key] = 'str:255'
            
            # Write flatgeobuf using temporary file then read into buffer
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / "points.fgb"
                
                with fiona.open(
                    str(tmp_path),
                    'w',
                    driver='FlatGeobuf',
                    schema=schema,
                    crs='EPSG:4326'
                ) as dst:
                    for point in st.session_state.points:
                        lon, lat = point["geometry"]["coordinates"]
                        feature = {
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [lon, lat]
                            },
                            'properties': point["properties"]
                        }
                        dst.write(feature)
                
                # Read the file back into the buffer
                with open(tmp_path, 'rb') as f:
                    fgb_buffer.write(f.read())
            
            fgb_buffer.seek(0)
            return fgb_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting FlatGeobuf: {str(e)}")
            return b""
    else:
        return b""