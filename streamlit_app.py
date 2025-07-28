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
# Google Sheets URL input
sheets_url = st.text_input(
    "Public Google Sheets URL with `wkt_geom` or `Latitude` and `Longitude` columns:",
    placeholder="https://docs.google.com/spreadsheets/d/...",
    key="sheets_url_input",
)

# Check if URL was entered and is different from last time
if sheets_url and sheets_url != st.session_state.get("last_sheets_url", ""):
    # Store the current URL to detect changes
    st.session_state.last_sheets_url = sheets_url

    # Import from Google Sheets using the new module
    success = import_from_google_sheets(sheets_url)
    if success:
        st.rerun()

# Render the map interface using the new module
render_map_interface()


# Only show export options if points exist
if st.session_state.points:
    # Export file type selection
    export_type = st.radio(
        "Choose export file type:",
        options=["GeoJSON", "Esri Shapefile (.zip)", "FlatGeobuf"],
        index=0,
        horizontal=True,
        key="export_type_radio",
    )

    # Custom filename input
    default_filename = get_base_filename()
    custom_filename = st.text_input(
        "Filename (optional):",
        value=default_filename,
        placeholder="Enter custom filename or use default",
    )

    # Use custom filename if provided, otherwise use default
    if custom_filename.strip():
        filename = custom_filename.strip()
    else:
        filename = default_filename

    geojson_data = create_geojson()
    gdf = points_to_gdf(st.session_state.points)

    export_label = "Download Vector"

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
        if st.download_button(
            label=export_label,
            data=export_data(gdf, export_type),
            file_name=export_filename,
            mime=export_mime,
            type="primary",
        ):
            # This block executes when the button is clicked
            st.success("Export completed!")
