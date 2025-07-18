import folium
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium

from click_to_geojson_functionality import add_point


def create_map_with_features():
    """Create a folium map with search and mini-map features.

    Returns
    -------
    folium.Map
        A configured folium map with search and mini-map features.
    """
    # Default to Berlin, but the map will maintain user's position
    map_object = folium.Map(
        location=[52.5200, 13.4050],  # Default center
        zoom_start=10,  # Default zoom
        tiles="OpenStreetMap",
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
        tile_layer="OpenStreetMap",
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
    if map_data["last_clicked"]:
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]

        # Check if this is a new click (avoid duplicate additions)
        if not st.session_state.get("last_click") or st.session_state.last_click != (
            clicked_lat,
            clicked_lon,
        ):
            add_point(clicked_lat, clicked_lon)
            st.session_state.last_click = (clicked_lat, clicked_lon)
            return True  # Indicate that a new point was added

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
            if st.session_state.points:
                removed_point = st.session_state.points.pop()
                st.rerun()

    with col3:
        if st.button("Clear All Points", key="clear_all_points_quick"):
            if st.session_state.points:
                from click_to_geojson_functionality import reset_points

                reset_points()
            st.rerun()


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

        import pandas as pd

        df = pd.DataFrame(points_data)

        # Show all columns except Index
        display_columns = [col for col in df.columns if col != "Index"]

        # Use data editor for interactive row selection
        edited_df = st.data_editor(
            df[display_columns],
            use_container_width=True,
            num_rows="dynamic",
            key="points_table",
            column_config={
                "Name": st.column_config.TextColumn("Name", disabled=True),
                "Latitude": st.column_config.NumberColumn(
                    "Latitude", format="%.6f", disabled=True
                ),
                "Longitude": st.column_config.NumberColumn(
                    "Longitude", format="%.6f", disabled=True
                ),
            },
        )

        # Handle row selection for deletion
        if "points_table" in st.session_state:
            selected_rows = st.session_state.points_table.get("selected_rows", [])
            if selected_rows:
                # Delete selected points (in reverse order to maintain indices)
                for row in reversed(selected_rows):
                    if "Index" in row:
                        index_to_remove = row["Index"]
                        if 0 <= index_to_remove < len(st.session_state.points):
                            st.session_state.points.pop(index_to_remove)
                st.rerun()


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
        key="map",
        use_container_width=True,
    )

    # Handle map clicks
    new_point_added = handle_map_clicks(map_data)
    if new_point_added:
        st.rerun()

    # Show point management controls if points exist
    if st.session_state.points:
        create_point_management_controls()
        create_point_table()

    return map_data
