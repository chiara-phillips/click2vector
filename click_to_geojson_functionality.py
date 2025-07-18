import streamlit as st
from datetime import datetime


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