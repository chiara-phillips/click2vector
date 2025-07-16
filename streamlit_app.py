import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import json
import pandas as pd
from datetime import datetime
from click_to_geojson_functionality import add_point, create_geojson, reset_points
# Set page config
st.set_page_config(page_title="Map to GeoJSON Exporter", layout="centered")

# Initialize session state for storing points
if 'points' not in st.session_state:
    st.session_state.points = []
if 'last_click' not in st.session_state:
    st.session_state.last_click = None
if 'selected_basemap' not in st.session_state:
    st.session_state.selected_basemap = "Esri Satellite"


# Main app
st.title("Click to GeoJSON")
st.markdown("Drop pins on the map below to build your dataset, then export as GeoJSON!")

# Basemap options
basemap_options = {
    "Open Street Map": "OpenStreetMap", 
    "Esri Satellite": "Esri WorldImagery",
    "Simple Light": "CartoDB positron",
    "Simple Dark": "CartoDB dark_matter",
}

# Create a folium map
m = folium.Map(
    location=[52.5200, 13.4050],  # Default to Berlin
    zoom_start=10,
    tiles=basemap_options[st.session_state.selected_basemap]
)

# Add search functionality
search = folium.plugins.Geocoder(
    collapsed=False,
    position='topright',
    placeholder='Search for a place...',
    add_marker=True,
    popup_text='Searched Location'
)
search.add_to(m)

# Add an inset map (mini map)
mini_map = folium.plugins.MiniMap(
    tile_layer=basemap_options[st.session_state.selected_basemap],
    position="bottomright",
    width=150,
    height=150,
    collapsed_width=25,
    collapsed_height=25,
    zoom_level_offset=-5
)
m.add_child(mini_map)

# Add existing points to the map
for i, point in enumerate(st.session_state.points):
    coords = point["geometry"]["coordinates"]
    folium.Marker(
        location=[coords[1], coords[0]],  # Note: folium uses [lat, lon]
        popup=f"{point['properties']['name']}",
        tooltip=f"Point {i + 1}: {point['properties']['name']}"
    ).add_to(m)

# Display the map and capture clicks
map_data = st_folium(
    m,
    height=350,
    returned_objects=["last_clicked"],
    key="map"
)

# Handle map clicks
if map_data["last_clicked"]:
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]

    # Check if this is a new click (avoid duplicate additions)
    if (not st.session_state.get('last_click') or
            st.session_state.last_click != (clicked_lat, clicked_lon)):
        add_point(clicked_lat, clicked_lon)
        st.session_state.last_click = (clicked_lat, clicked_lon)
        st.success(f"Point added at {clicked_lat:.4f}, {clicked_lon:.4f}")
        st.rerun()

# Map style selector
col1, col2 = st.columns(2)
with col1:
    selected_basemap = st.radio(
        "Choose your map style:",
        options=list(basemap_options.keys()),
        index=list(basemap_options.keys()).index(st.session_state.selected_basemap)
    )
with col2:
    with st.form("coord_form", border=False):
        coord_text = st.text_area(
            "Enter one or more coordinates\n(format: lat,lon,optional name)",
            placeholder="52.5200,13.4050,Berlin\n52.5163,13.3777,Brandenburg Gate\n52.5244,13.4105,Alexanderplatz",
            height=120,
        )

        if st.form_submit_button("Add Points"):
            if coord_text.strip():
                lines = coord_text.strip().split('\n')
                added_count = 0
                errors = []
                
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            try:
                                lat = float(parts[0].strip())
                                lon = float(parts[1].strip())
                                name = parts[2].strip() if len(parts) > 2 else ""
                                add_point(lat, lon, name)
                                added_count += 1
                            except ValueError:
                                errors.append(f"Line {i}: Invalid coordinates - {line}")
                        else:
                            errors.append(f"Line {i}: Need at least lat,lon - {line}")
                
                if errors:
                    for error in errors:
                        st.error(error)
                
                if added_count > 0:
                    st.success(f"Added {added_count} point(s)!")
                    st.rerun()
            else:
                st.warning("Please enter at least one coordinate.")

            

# Update session state if selection changed
if selected_basemap != st.session_state.selected_basemap:
    st.session_state.selected_basemap = selected_basemap
    st.rerun()

# Only show Point Management if there are points
with st.expander("Point Viewer", expanded=True):
    st.write(f"**You have {len(st.session_state.points)} point(s) ready to export!**")

    if st.session_state.points:  # Only show table if there are points
        # Show points in a table
        points_data = []
        for i, point in enumerate(st.session_state.points):
            coords = point["geometry"]["coordinates"]
            points_data.append({
                "Name": point["properties"]["name"],
                "Latitude": coords[1],
                "Longitude": coords[0],
                "Index": i
            })

        df = pd.DataFrame(points_data)
        st.dataframe(df[["Name", "Latitude", "Longitude"]], use_container_width=True)

        # Remove specific point
        point_to_remove = st.selectbox(
            "Choose which point to delete:",
            options=range(len(st.session_state.points)),
            format_func=lambda x: f"{st.session_state.points[x]['properties']['name']}"
        )
        
        # Action buttons in a row
        cola, colb = st.columns(2)
        with cola:
            if st.button("🗑️ Delete This Point"):
                st.session_state.points.pop(point_to_remove)
                st.rerun()
        with colb:
            if st.button("🧹 Clear All Points", type="secondary"):
                reset_points()
                st.rerun()

# Always show download button
if st.session_state.points:
    geojson_data = create_geojson()
    st.download_button(
        label="📥 Download GeoJSON",
        data=json.dumps(geojson_data, indent=2),
        file_name=f"points_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
        mime="application/geo+json",
        type="primary"
    )
else:
    # Show disabled download button with error
    st.download_button(
        label="📥 Download GeoJSON",
        data="",
        file_name="no_data.geojson",
        disabled=True,
        type="primary"
    )
    st.warning("No data staged for download. Click or search on the map or use manual entry to add points.")