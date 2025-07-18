import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
from click_to_geojson_functionality import add_point


def initialize_map_state():
    """Initialize session state variables for map functionality"""
    if 'user_zoom' not in st.session_state:
        st.session_state.user_zoom = 10  # Default zoom level
    if 'last_map_center' not in st.session_state:
        st.session_state.last_map_center = (52.5200, 13.4050)  # Default to Berlin


def get_map_center_and_zoom():
    """Determine map center and zoom level based on existing points or defaults"""
    if st.session_state.points:
        # If a new point was just added, zoom to it
        if 'last_added_point' in st.session_state:
            center_lat, center_lon = st.session_state.last_added_point
            zoom_level = st.session_state.user_zoom  # Use user's preferred zoom
            # Clear the flag so we don't keep zooming to the same point
            del st.session_state.last_added_point
        else:
            # Calculate center from all existing points
            lats = [point["geometry"]["coordinates"][1] for point in st.session_state.points]
            lons = [point["geometry"]["coordinates"][0] for point in st.session_state.points]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            zoom_level = st.session_state.user_zoom  # Use user's preferred zoom
    else:
        # Use last known map center or default to Berlin
        if 'last_map_center' in st.session_state:
            center_lat, center_lon = st.session_state.last_map_center
        else:
            center_lat, center_lon = 52.5200, 13.4050  # Default to Berlin
        zoom_level = st.session_state.user_zoom  # Use user's preferred zoom
    
    return center_lat, center_lon, zoom_level


def create_map_with_features(center_lat, center_lon, zoom_level):
    """Create a folium map with search and mini-map features"""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles="OpenStreetMap"
    )

    # Add search functionality (pan only, no markers)
    search = folium.plugins.Geocoder(
        collapsed=False,
        position='topright',
        placeholder='Search for a place...',
        add_marker=False,  # Don't add markers, just pan
        popup_text='Searched Location'
    )
    search.add_to(m)

    # Add an inset map (mini map)
    mini_map = folium.plugins.MiniMap(
        tile_layer="OpenStreetMap",
        position="bottomright",
        width=150,
        height=150,
        collapsed_width=25,
        collapsed_height=25,
        zoom_level_offset=-5
    )
    m.add_child(mini_map)
    
    return m


def add_existing_points_to_map(m):
    """Add existing points from session state to the map"""
    for i, point in enumerate(st.session_state.points):
        coords = point["geometry"]["coordinates"]
        
        folium.Marker(
            location=[coords[1], coords[0]],  # Note: folium uses [lat, lon]
            tooltip=f"Point {i + 1}: {point['properties']['name']}"
        ).add_to(m)


def handle_map_interactions(map_data):
    """Handle map interactions like zoom changes and center updates"""
    # Store user's zoom level and center
    if map_data.get("zoom") and map_data["zoom"] != st.session_state.user_zoom:
        st.session_state.user_zoom = map_data["zoom"]

    # Store the current map center
    if map_data.get("center"):
        current_center = (map_data["center"]["lat"], map_data["center"]["lng"])
        if current_center != st.session_state.last_map_center:
            st.session_state.last_map_center = current_center


def handle_map_clicks(map_data):
    """Handle map click events and add new points"""
    if map_data["last_clicked"]:
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]

        # Check if this is a new click (avoid duplicate additions)
        if (not st.session_state.get('last_click') or
                st.session_state.last_click != (clicked_lat, clicked_lon)):
            add_point(clicked_lat, clicked_lon)
            st.session_state.last_click = (clicked_lat, clicked_lon)
            
            # Store the new point location for zooming
            st.session_state.last_added_point = (clicked_lat, clicked_lon)
            return True  # Indicate that a new point was added
    
    return False  # No new point was added


def create_point_management_controls():
    """Create controls for managing points (remove last, clear all)"""
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
    """Create an interactive table for viewing and managing points"""
    with st.expander("Point Table", expanded=True):
        # Show points in a table
        points_data = []
        for i, point in enumerate(st.session_state.points):
            coords = point["geometry"]["coordinates"]
            # Start with basic info
            row_data = {
                "Name": point["properties"]["name"],
                "Latitude": coords[1],
                "Longitude": coords[0],
                "Index": i
            }
            
            # Add all other properties
            for key, value in point["properties"].items():
                if key not in ["name", "timestamp"]:  # Skip name (already shown) and timestamp
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
                "Latitude": st.column_config.NumberColumn("Latitude", format="%.6f", disabled=True),
                "Longitude": st.column_config.NumberColumn("Longitude", format="%.6f", disabled=True),
            }
        )
        
        # Handle row selection for deletion
        if 'points_table' in st.session_state:
            selected_rows = st.session_state.points_table.get('selected_rows', [])
            if selected_rows:
                # Delete selected points (in reverse order to maintain indices)
                for row in reversed(selected_rows):
                    if 'Index' in row:
                        index_to_remove = row['Index']
                        if 0 <= index_to_remove < len(st.session_state.points):
                            st.session_state.points.pop(index_to_remove)
                st.rerun()


def render_map_interface():
    """Main function to render the complete map interface"""
    # Initialize map state
    initialize_map_state()
    
    # Get map center and zoom
    center_lat, center_lon, zoom_level = get_map_center_and_zoom()
    
    # Create map with features
    m = create_map_with_features(center_lat, center_lon, zoom_level)
    
    # Add existing points to map
    add_existing_points_to_map(m)
    
    # Display the map and capture clicks
    map_data = st_folium(
        m,
        width=750,
        height=300,
        returned_objects=["last_clicked", "zoom", "center"],
        key="map",
        use_container_width=True
    )
    
    # Handle map interactions
    handle_map_interactions(map_data)
    
    # Handle map clicks
    new_point_added = handle_map_clicks(map_data)
    if new_point_added:
        st.rerun()
    
    # Show point management controls if points exist
    if st.session_state.points:
        create_point_management_controls()
        create_point_table()
    
    return map_data 