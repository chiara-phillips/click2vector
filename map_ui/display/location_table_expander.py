"""Location table expander UI."""

import pandas as pd
import streamlit as st

from map_ui.view import request_rerun

def sync_points_table_changes() -> None:
    """Apply row deletions and edits from the point table data editor."""
    state = st.session_state.get("points_table")
    if not state:
        return

    changed = False

    for idx in sorted(state.get("deleted_rows", []), reverse=True):
        if 0 <= idx < len(st.session_state.points):
            st.session_state.points.pop(idx)
            changed = True

    for idx, updates in state.get("edited_rows", {}).items():
        point_idx = int(idx)
        if 0 <= point_idx < len(st.session_state.points):
            properties = st.session_state.points[point_idx]["properties"]
            if "Name" in updates:
                properties["name"] = str(updates["Name"])
            if "Description" in updates:
                properties["description"] = str(updates["Description"])
            changed = True

    if changed:
        request_rerun()


def render_location_table_expander() -> None:
    """Render an interactive table for viewing and managing points.

    Returns
    -------
    None
        Renders an interactive data table for point management.
    """
    with st.expander("Location table", expanded=False, type="compact"):
        # Show points in a table
        points_data = []
        for point_index, point in enumerate(st.session_state.points):
            coords = point["geometry"]["coordinates"]
            # Start with basic info
            row_data = {
                "Name": point["properties"]["name"],
                "Description": point["properties"].get("description", ""),
                "Latitude": coords[1],
                "Longitude": coords[0],
                "Index": point_index,
            }

            # Add all other properties
            for key, value in point["properties"].items():
                if key not in [
                    "name",
                    "description",
                    "timestamp",
                ]:
                    row_data[key] = value

            points_data.append(row_data)

        df = pd.DataFrame(points_data)

        # Show all columns except Index
        display_columns = [col for col in df.columns if col != "Index"]

        # Use data editor for interactive row selection and editing
        edited_df = st.data_editor(
            df[display_columns],
            width="stretch",
            key="points_table",
            num_rows="delete",
            on_change=sync_points_table_changes,
            column_config={
                "Name": st.column_config.TextColumn("Name", disabled=False),
                "Description": st.column_config.TextColumn(
                    "Description", disabled=False
                ),
                "Latitude": st.column_config.NumberColumn(
                    "Latitude", format="%.6f", disabled=True
                ),
                "Longitude": st.column_config.NumberColumn(
                    "Longitude", format="%.6f", disabled=True
                ),
            },
        )

        if edited_df is not None:
            for i, row in edited_df.iterrows():
                try:
                    st.session_state.points[i]["properties"]["name"] = row["Name"]
                    st.session_state.points[i]["properties"]["description"] = row[
                        "Description"
                    ]
                except IndexError:
                    pass
