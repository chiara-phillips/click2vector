import streamlit as st
from datetime import datetime


def add_point(lat, lon, name=""):
    """Add a point to the session state"""
    point = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "name": name if name else f"Point {len(st.session_state.points) + 1}",
            "timestamp": datetime.now().isoformat()
        }
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