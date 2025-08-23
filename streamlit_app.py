"""
This is the main Streamlit app that combines all the functionality.
"""

import streamlit as st

from click_to_geojson_functionality import (
    create_geojson,
    export_data,
    get_base_filename,
    points_to_gdf,
)
from google_sheets_parser import import_from_google_sheets
from map_point_parser import render_map_interface
from styling import create_styled_title, inject_global_css

# Set page config
st.set_page_config(page_title="Map to GeoJSON Exporter", layout="centered")
inject_global_css()

# Initialize session state for storing points
if "points" not in st.session_state:
    st.session_state.points = []
if "last_click" not in st.session_state:
    st.session_state.last_click = None
if "message" not in st.session_state:
    st.session_state.message = None


# Main app
# Coordinate format selection
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    coordinate_format = st.radio(
        "Coordinate format to import from Google Sheet (if applicable):",
        options=["Lat/Long", "WKT Geometry"],
        index=0,  # Default to Lat/Long
        horizontal=True,
    )

    # Convert radio selection to boolean for the function
    use_wkt = coordinate_format == "WKT Geometry"
    column_text = "a `wkt_geom` column" if use_wkt else "`lat` and `long` columns"
with col1:
    # Google Sheets URL input
    sheets_url = st.text_input(
        f"Public Google Sheet URL with {column_text} (if applicable):",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        key="sheets_url_input",
    )


# Check if URL was entered and is different from last time
if sheets_url and sheets_url != st.session_state.get("last_sheets_url", ""):
    # Store the current URL to detect changes
    st.session_state.last_sheets_url = sheets_url

    # Import from Google Sheets using the new module
    success = import_from_google_sheets(sheets_url, use_wkt)
    if success:
        st.rerun()
with col3:
    basemap_name = st.radio(
        "Basemap options:",
        options=["CartoDB Positron", "OpenStreetMap"],
        index=0,
        horizontal=True,
    )

# Render the map interface using the new module
render_map_interface(basemap_name)


# Only show export options if points exist
if st.session_state.points:
    # Export file type selection
    col1, col2 = st.columns([1.5, 1])
    with col1:
        export_type = st.radio(
            "Export file type:",
            options=["GeoJSON", "Esri Shapefile (.zip)", "FlatGeobuf"],
            index=0,
            horizontal=True,
            key="export_type_radio",
        )
    # Custom filename input - store in session state to persist across reruns
    if "custom_filename" not in st.session_state:
        st.session_state.custom_filename = get_base_filename()
    with col2:
        custom_filename = st.text_input(
            "Export file name:",
            value=st.session_state.custom_filename,
            placeholder="Enter export file name",
            key="filename_input",
        )

    # Update session state with the current input value
    st.session_state.custom_filename = custom_filename

    # Use custom filename if provided and different from default, otherwise use default
    if custom_filename.strip() and custom_filename.strip() != get_base_filename():
        filename = custom_filename.strip()
    else:
        filename = get_base_filename()

    geojson_data = create_geojson()
    gdf = points_to_gdf(st.session_state.points)

    export_filename = {
        "GeoJSON": f"{filename}.geojson",
        "Esri Shapefile (.zip)": f"{filename}.zip",
        "FlatGeobuf": f"{filename}.fgb",
    }[export_type]

    export_mime = {
        "GeoJSON": "application/geo+json",
        "Esri Shapefile (.zip)": "application/zip",
        "FlatGeobuf": "application/octet-stream",
    }[export_type]

    # Display any pending messages
    if st.session_state.message:
        if (
            "error" in st.session_state.message.lower()
            or "no points" in st.session_state.message.lower()
        ):
            st.error(st.session_state.message)
        else:
            st.success(st.session_state.message)
        st.session_state.message = None  # Clear the message

    # Show download button
    col1, col2, col3 = st.columns([2, 2, 1])
    with col2:
        st.download_button(
            label="Download Vector",
            data=export_data(gdf, export_type),
            file_name=export_filename,
            mime=export_mime,
            type="primary",
        )
