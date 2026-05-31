"""Display settings expander UI."""

import streamlit as st

from map_ui.basemap import (
    BASEMAP_OPTIONS,
    ensure_basemap_picker_state,
    format_basemap_label,
)
from map_ui.display.columns import resolve_color_by_column, resolve_label_by_column
from map_ui.display.legend import get_legend_display_names, legend_label_widget_key
from map_ui.display.pin_colors import (
    get_property_colors,
    property_color_widget_key,
    sync_property_color,
    sync_property_color_state,
)
from map_ui.display.properties import (
    COLOR_TABLE_COLUMNS,
    get_colorable_columns,
    get_property_key,
    get_unique_property_values,
)
from styling import DEFAULT_BUTTON_COLOR

def render_display_settings_expander() -> None:
    """Render map display options and optional location color settings."""
    ensure_basemap_picker_state()
    default_color = st.session_state.get("pin_color", DEFAULT_BUTTON_COLOR)

    cluster_help = (
        "Clusters merge nearby pins into a count circle. Each cluster uses the "
        "pin color that appears most often in that group; when two colors tie, "
        "the first dominant color is used."
    )
    with st.expander("Display settings", expanded=False, type="compact"):
        basemap_col, color_by_col, label_by_col = st.columns(
            COLOR_TABLE_COLUMNS, vertical_alignment="bottom"
        )
        with basemap_col:
            st.selectbox(
                "Basemap",
                options=BASEMAP_OPTIONS,
                format_func=format_basemap_label,
                key="basemap_picker",
            )
            st.session_state.basemap_name = st.session_state.basemap_picker

        if st.session_state.points:
            colorable_columns = get_colorable_columns(st.session_state.points)
            color_by_column = resolve_color_by_column(colorable_columns)
            label_by_column = resolve_label_by_column(colorable_columns)

            if "color_by_column_picker" not in st.session_state:
                st.session_state.color_by_column_picker = color_by_column
            elif st.session_state.color_by_column_picker not in colorable_columns:
                st.session_state.color_by_column_picker = color_by_column

            if "label_by_column_picker" not in st.session_state:
                st.session_state.label_by_column_picker = label_by_column
            elif st.session_state.label_by_column_picker not in colorable_columns:
                st.session_state.label_by_column_picker = label_by_column

            with color_by_col:
                st.selectbox(
                    "Group column",
                    options=colorable_columns,
                    key="color_by_column_picker",
                )

            with label_by_col:
                st.selectbox(
                    "Label column",
                    options=colorable_columns,
                    key="label_by_column_picker",
                )

            st.session_state.color_by_column = (
                st.session_state.color_by_column_picker
            )
            st.session_state.label_by_column = (
                st.session_state.label_by_column_picker
            )
            property_key = get_property_key(st.session_state.color_by_column)

            sync_property_color_state(
                st.session_state.points, property_key, default_color
            )

            unique_values = get_unique_property_values(
                st.session_state.points, property_key
            )
            colors = get_property_colors(property_key)
            column_label = st.session_state.color_by_column
            legend_names = get_legend_display_names(property_key)

            header_value, header_legend, header_color = st.columns(
                COLOR_TABLE_COLUMNS
            )
            with header_value:
                st.caption("Group value")
            with header_legend:
                st.caption("Legend display name")
            with header_color:
                st.caption("Group color")

            for value in unique_values:
                category_label = value or f"(No {column_label.lower()})"
                category_col, legend_col, color_col = st.columns(
                    COLOR_TABLE_COLUMNS
                )
                with category_col:
                    st.text(category_label)
                with legend_col:
                    label_key = legend_label_widget_key(property_key, value)
                    if label_key not in st.session_state:
                        st.session_state[label_key] = legend_names.get(
                            value, category_label
                        )
                    st.text_input(
                        "Legend Display Name",
                        key=label_key,
                        label_visibility="collapsed",
                    )
                    legend_names[value] = st.session_state[label_key]
                with color_col:
                    picker_key = property_color_widget_key(
                        property_key, value
                    )
                    if picker_key not in st.session_state:
                        st.session_state[picker_key] = colors[value]
                    st.color_picker(
                        category_label,
                        key=picker_key,
                        label_visibility="collapsed",
                        on_change=sync_property_color,
                        args=(property_key, value),
                    )
                    sync_property_color(property_key, value)

        with st.container(
            horizontal=True,
            vertical_alignment="center",
            gap="medium",
            width="content",
        ):
            st.checkbox("Inset map", key="show_inset_map")
            st.checkbox("Legend", key="show_map_legend")

        if st.session_state.points:
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap="small",
                width="content",
            ):
                st.caption("Points")
                st.toggle(
                    "Cluster overlapping pins as clusters",
                    key="cluster_overlapping_pins",
                    label_visibility="collapsed",
                    help=cluster_help,
                )
                st.caption("Clusters")
