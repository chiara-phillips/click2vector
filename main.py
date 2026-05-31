"""Click 2 Vector Streamlit app."""

import streamlit as st

APP_NAME = "Click 2 Vector"

from export_logic.export_settings_expander import render_export_settings_expander
from map_ui import (
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
if "label_by_column" not in st.session_state:
    st.session_state.label_by_column = "Name"
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
    render_export_settings_expander()

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
