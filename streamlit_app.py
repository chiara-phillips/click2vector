"""
This is the main Streamlit app that combines all the functionality.
"""

import streamlit as st

from click_to_geojson_functionality import (
    build_export_filename,
    export_data,
    get_base_filename,
    points_to_gdf,
)
from google_sheets_parser import import_from_google_sheets
from map_point_parser import (
    render_map_interface,
    sync_description_color_state,
    sync_description_colors_from_pickers,
)
from styling import DEFAULT_BUTTON_COLOR, create_styled_title, inject_global_css

BASEMAP_OPTIONS = ["CartoDB Positron", "OpenStreetMap"]


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
if "basemap_name" not in st.session_state:
    st.session_state.basemap_name = "CartoDB Positron"
if "pin_color" not in st.session_state:
    st.session_state.pin_color = DEFAULT_BUTTON_COLOR
if "description_colors" not in st.session_state:
    st.session_state.description_colors = {}
if "show_inset_map" not in st.session_state:
    st.session_state.show_inset_map = False


if st.session_state.points:
    sync_description_color_state(
        st.session_state.points,
        st.session_state.pin_color,
    )
    sync_description_colors_from_pickers(st.session_state.points)

# Main app
render_map_interface(st.session_state.basemap_name)

with st.expander("Advanced options", expanded=False):
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
        column_text = (
            "a `wkt_geom` column" if use_wkt else "`lat` and `long` columns"
        )
    with col1:
        sheets_url = st.text_input(
            f"Public Google Sheet URL with {column_text} (if applicable):",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            key="sheets_url_input",
        )
    with col3:
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

    if sheets_url and sheets_url != st.session_state.get("last_sheets_url", ""):
        st.session_state.last_sheets_url = sheets_url
        success = import_from_google_sheets(sheets_url, use_wkt)
        if success:
            st.rerun()

    if st.session_state.points:
        export_type = st.radio(
            "Export file type:",
            options=["GeoJSON", "Esri Shapefile (.zip)", "FlatGeobuf"],
            index=0,
            horizontal=True,
            key="export_type_radio",
        )
        if export_type == "GeoJSON":
            gdf = points_to_gdf(st.session_state.points)
            with st.expander("GeoJSON output", expanded=False):
                st.code(export_data(gdf, export_type), language="json")


# Only show export options if points exist
if st.session_state.points:
    export_type = st.session_state.get("export_type_radio", "GeoJSON")

    if "custom_filename" not in st.session_state:
        st.session_state.custom_filename = get_base_filename()

    custom_filename = st.text_input(
        "Export filename:",
        value=st.session_state.custom_filename,
        placeholder="Enter export filename",
        key="filename_input",
    )

    st.session_state.custom_filename = custom_filename

    if custom_filename.strip() and custom_filename.strip() != get_base_filename():
        filename = custom_filename.strip()
    else:
        filename = get_base_filename()

    gdf = points_to_gdf(st.session_state.points)

    export_filename = build_export_filename(filename, export_type)

    export_mime = {
        "GeoJSON": "application/geo+json",
        "GeoJSON.io": "text/plain",
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
        # Single download button for all formats
        st.download_button(
            label="Download Vector",
            data=export_data(gdf, export_type),
            file_name=export_filename,
            mime=export_mime,
            type="primary",
        )

    st.markdown(
        """
    <style>

           /* Remove blank space at bottom */
           .block-container {
               padding-bottom: 0.2rem;
            }

    </style>
    """,
        unsafe_allow_html=True,
    )

if st.session_state.get("pending_rerun"):
    st.session_state.pending_rerun = False
    st.rerun()
