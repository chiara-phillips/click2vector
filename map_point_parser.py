import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from click_to_geojson_functionality import add_point


def create_map_with_features():
    """Create a folium map with search and mini-map features.

    Returns
    -------
    folium.Map
        A configured folium map with search and mini-map features.
    """
    # Get the user's last map view, or use a reasonable default
    last_view = st.session_state.get("last_map_view", {"center": [0, 0], "zoom": 1})

    map_object = folium.Map(
        location=last_view["center"],
        zoom_start=last_view["zoom"],
        tiles="Cartodb Positron",
    )

    # Add search functionality (pan only, no markers)
    search = folium.plugins.Geocoder(
        collapsed=False,
        position="topright",
        placeholder="Search for a place...",
        add_marker=False,  # Don't add markers, just pan
        popup_text="Searched Location",
    )
    search.add_to(map_object)

    # Add an inset map (mini map)
    mini_map = folium.plugins.MiniMap(
        tile_layer="Cartodb Positron",
        position="bottomright",
        width=150,
        height=150,
        collapsed_width=25,
        collapsed_height=25,
        zoom_level_offset=-5,
    )
    map_object.add_child(mini_map)

    return map_object


def add_existing_points_to_map(map_object):
    """Add existing points from session state to the map.

    Parameters
    ----------
    map_object : folium.Map
        The folium map to add points to.

    Returns
    -------
    None
        Adds markers for all existing points to the map.
    """
    for point_index, point in enumerate(st.session_state.points):
        coords = point["geometry"]["coordinates"]

        folium.Marker(
            location=[coords[1], coords[0]],  # Note: folium uses [lat, lon]
            tooltip=f"Point {point_index + 1}: {point['properties']['name']}",
        ).add_to(map_object)


def handle_map_clicks(map_data):
    """Handle map click events and add new points.

    Parameters
    ----------
    map_data : dict
        The map data returned from st_folium containing click information.

    Returns
    -------
    bool
        True if a new point was added, False otherwise.
    """
    try:
        clicked_data = map_data["last_clicked"]
        clicked_lat = clicked_data["lat"]
        clicked_lon = clicked_data["lng"]

        # Check if this is a new click (avoid duplicate additions)
        last_click = st.session_state.get("last_click")
        if last_click != (clicked_lat, clicked_lon):
            add_point(clicked_lat, clicked_lon)
            st.session_state.last_click = (clicked_lat, clicked_lon)
            return True  # Indicate that a new point was added

    except (KeyError, TypeError):
        # No click data or invalid format
        pass

    return False  # No new point was added


def create_point_management_controls():
    """Create controls for managing points (remove last, clear all).

    Returns
    -------
    None
        Renders point management buttons in the Streamlit interface.
    """
    col1, col2, col3, col4 = st.columns([1.5, 2, 2, 1])

    with col2:
        if st.button("Remove Last Point", key="remove_last_point"):
            try:
                st.session_state.points.pop()
                st.rerun()
            except IndexError:
                # No points to remove
                pass

    with col3:
        if st.button("Clear All Points", key="clear_all_points_quick"):
            try:
                from click_to_geojson_functionality import reset_points

                reset_points()
                st.rerun()
            except Exception:
                # No points to clear or other error
                pass


def create_point_table():
    """Create an interactive table for viewing and managing points.

    Returns
    -------
    None
        Renders an interactive data table for point management.
    """
    with st.expander("Point Table", expanded=True):
        # Show points in a table
        points_data = []
        for point_index, point in enumerate(st.session_state.points):
            coords = point["geometry"]["coordinates"]
            # Start with basic info
            row_data = {
                "Name": point["properties"]["name"],
                "Latitude": coords[1],
                "Longitude": coords[0],
                "Index": point_index,
            }

            # Add all other properties
            for key, value in point["properties"].items():
                if key not in [
                    "name",
                    "timestamp",
                ]:  # Skip name (already shown) and timestamp
                    row_data[key] = value

            points_data.append(row_data)

        df = pd.DataFrame(points_data)

        # Show all columns except Index
        display_columns = [col for col in df.columns if col != "Index"]

        # Use data editor for interactive row selection and editing
        edited_df = st.data_editor(
            df[display_columns],
            use_container_width=True,
            key="points_table",
            column_config={
                "Name": st.column_config.TextColumn("Name", disabled=False),
                "Latitude": st.column_config.NumberColumn(
                    "Latitude", format="%.6f", disabled=True
                ),
                "Longitude": st.column_config.NumberColumn(
                    "Longitude", format="%.6f", disabled=True
                ),
            },
        )

        # Handle name changes
        if edited_df is not None:
            for i, row in edited_df.iterrows():
                try:
                    st.session_state.points[i]["properties"]["name"] = row["Name"]
                except IndexError:
                    # Skip if this is the extra "add row" row
                    pass

        # Handle row selection for deletion
        try:
            selected_rows = st.session_state.points_table.get("selected_rows", [])
            if selected_rows:
                # Delete selected points (in reverse order to maintain indices)
                for row in reversed(selected_rows):
                    try:
                        index_to_remove = row["Index"]
                        if 0 <= index_to_remove < len(st.session_state.points):
                            st.session_state.points.pop(index_to_remove)
                    except (KeyError, IndexError):
                        # Invalid row data or index
                        continue
                st.rerun()
        except (KeyError, AttributeError):
            # No points_table in session state or no selected_rows
            pass


def render_map_interface():
    """Main function to render the complete map interface.

    Returns
    -------
    dict
        The map data returned from st_folium for further processing.
    """
    # Create map with features
    map_object = create_map_with_features()

    # Add existing points to map
    add_existing_points_to_map(map_object)

    # Display the map and capture clicks
    map_data = st_folium(
        map_object,
        width=750,
        height=300,
        returned_objects=["last_clicked"],
        use_container_width=True,
    )

    # Store the current map view for next render
    if map_data and "center" in map_data and "zoom" in map_data:
        st.session_state.last_map_view = {
            "center": map_data["center"],
            "zoom": map_data["zoom"],
        }

    # Handle map clicks
    new_point_added = handle_map_clicks(map_data)
    if new_point_added:
        st.rerun()

    # Show point management controls if points exist
    if st.session_state.points:
        create_point_management_controls()
        create_point_table()

    return map_data
