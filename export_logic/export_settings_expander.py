"""Export settings expander UI and download button."""

import streamlit as st

from export_logic.export import build_export_filename, export_data, get_base_filename
from points.session import points_to_gdf


def render_export_settings_expander() -> None:
    """Render export file options, preview, and download button."""
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

            if (
                custom_filename.strip()
                and custom_filename.strip() != get_base_filename()
            ):
                filename = custom_filename.strip()
            else:
                filename = get_base_filename()

            gdf = points_to_gdf(st.session_state.points)
            export_filename = build_export_filename(filename, export_type)

            if export_type == "GeoJSON":
                with st.expander(
                    "GeoJSON output", expanded=False, type="compact"
                ):
                    st.code(export_data(gdf, export_type), language="json")

        export_mime = {
            "GeoJSON": "application/geo+json",
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
