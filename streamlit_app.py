"""Click 2 Vector Streamlit app."""

import streamlit as st

APP_NAME = "Click 2 Vector"

from click_to_geojson_functionality import (
    build_export_filename,
    export_data,
    get_base_filename,
    points_to_gdf,
)
from map_point_parser import (
    DEFAULT_BASEMAP,
    get_property_key,
    render_map_interface,
    sync_legend_display_names_from_inputs,
    sync_property_color_state,
    sync_property_colors_from_pickers,
)
from styling import DEFAULT_BUTTON_COLOR, inject_global_css

st.set_page_config(page_title=APP_NAME, layout="centered")
inject_global_css()

# Initialize session state for storing points
if "points" not in st.session_state:
    st.session_state.points = []
if "last_click" not in st.session_state:
    st.session_state.last_click = None
if "message" not in st.session_state:
    st.session_state.message = None
if "basemap_name" not in st.session_state:
    st.session_state.basemap_name = DEFAULT_BASEMAP
if "pin_color" not in st.session_state:
    st.session_state.pin_color = DEFAULT_BUTTON_COLOR
if "color_by_column" not in st.session_state:
    st.session_state.color_by_column = "Description"
if "property_value_colors" not in st.session_state:
    st.session_state.property_value_colors = {}
if "legend_display_names" not in st.session_state:
    st.session_state.legend_display_names = {}
if "show_inset_map" not in st.session_state:
    st.session_state.show_inset_map = False
if "show_map_legend" not in st.session_state:
    st.session_state.show_map_legend = False
if "cluster_overlapping_pins" not in st.session_state:
    st.session_state.cluster_overlapping_pins = True


if st.session_state.points:
    color_property_key = get_property_key(
        st.session_state.get("color_by_column", "Description")
    )
    sync_property_color_state(
        st.session_state.points,
        color_property_key,
        st.session_state.pin_color,
    )
    sync_property_colors_from_pickers(
        st.session_state.points, color_property_key
    )
    sync_legend_display_names_from_inputs(
        st.session_state.points, color_property_key
    )

# Main app
render_map_interface()

if st.session_state.message:
    if (
        "error" in st.session_state.message.lower()
        or "no points" in st.session_state.message.lower()
    ):
        st.error(st.session_state.message)
    else:
        st.success(st.session_state.message)
    st.session_state.message = None

if st.session_state.points:
    if "custom_filename" not in st.session_state:
        st.session_state.custom_filename = get_base_filename()

    with st.container(border=False):
        with st.expander(
            "Export settings", expanded=False, type="compact"
        ):
            type_col, name_col = st.columns(2)
            with type_col:
                st.caption("Export file type:")
                export_type = st.radio(
                    "Export file type:",
                    options=["GeoJSON", "Esri Shapefile (.zip)", "FlatGeobuf"],
                    index=0,
                    key="export_type_radio",
                    label_visibility="collapsed",
                )
            with name_col:
                st.caption("Export filename:")
                custom_filename = st.text_input(
                    "Export filename:",
                    value=st.session_state.custom_filename,
                    placeholder="Enter export filename",
                    key="filename_input",
                    label_visibility="collapsed",
                )

            st.session_state.custom_filename = custom_filename

            if custom_filename.strip() and custom_filename.strip() != get_base_filename():
                filename = custom_filename.strip()
            else:
                filename = get_base_filename()

            gdf = points_to_gdf(st.session_state.points)
            export_filename = build_export_filename(filename, export_type)

            if export_type == "GeoJSON":
                with st.expander("GeoJSON output", expanded=False, type="compact"):
                    st.code(export_data(gdf, export_type), language="json")

        export_mime = {
            "GeoJSON": "application/geo+json",
            "GeoJSON.io": "text/plain",
            "Esri Shapefile (.zip)": "application/zip",
            "FlatGeobuf": "application/octet-stream",
        }[export_type]

        _, download_col, _ = st.columns([1, 1, 1])
        with download_col:
            st.download_button(
                label="Download Vector",
                data=export_data(gdf, export_type),
                file_name=export_filename,
                mime=export_mime,
                type="primary",
                use_container_width=True,
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
