import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import json
import pandas as pd
from datetime import datetime
from click_to_geojson_functionality import add_point, create_geojson, reset_points
import geopandas as gpd
import io
import zipfile
from pathlib import Path
# Set page config
st.set_page_config(page_title="Map to GeoJSON Exporter", layout="centered")

# Add custom CSS to reduce top margin
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        padding-left: 5rem;
        padding-right: 5rem;
        max-width: 1200px;
    }
    .main .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for storing points
if 'points' not in st.session_state:
    st.session_state.points = []
if 'last_click' not in st.session_state:
    st.session_state.last_click = None
if 'message' not in st.session_state:
    st.session_state.message = None
if 'user_zoom' not in st.session_state:
    st.session_state.user_zoom = 10  # Default zoom level



# Main app
st.title("Click 2 Vector")
st.markdown("Create and export spatial data from a few map clicks or a spreadsheet.")

# Google Sheets URL input
sheets_url = st.text_input(
    "Or, enter a public Google Sheets URL with `wkt_geom` or `latitude` and `longitude` columns:",
    placeholder="https://docs.google.com/spreadsheets/d/...",
    key="sheets_url_input"
)

# Check if URL was entered and is different from last time
if sheets_url and sheets_url != st.session_state.get('last_sheets_url', ''):

    # Store the current URL to detect changes
    st.session_state.last_sheets_url = sheets_url
    
    # Try Google Sheets if URL provided
    if sheets_url.strip():
        with st.spinner("Importing data from Google Sheets..."):
            try:
                # Validate Google Sheets URL format
                if "docs.google.com/spreadsheets/d/" not in sheets_url:
                    st.error("**Invalid Google Sheets URL format.** Please use a URL that looks like: https://docs.google.com/spreadsheets/d/SHEET_ID/edit")
                    st.stop()
                
                # Extract sheet ID from URL
                try:
                    sheet_id = sheets_url.split('/d/')[1].split('/')[0]
                    if not sheet_id or len(sheet_id) < 10:  # Basic validation
                        st.error("**Invalid Google Sheets ID:** Could not extract a valid sheet ID from the URL")
                        st.stop()
                except IndexError:
                    st.error("**Invalid Google Sheets URL.** Please check the URL format and try again")
                    st.stop()
                
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
                
                # Test if the sheet is accessible
                df = None
                try:
                    df = pd.read_csv(csv_url)
                except Exception as csv_error:
                    st.error("**Could not access Google Sheet.** Please check the URL is correct and the sheet is publicly shared (Anyone with link can view)")
                    st.stop()
                
                # Only process if we successfully loaded the CSV
                if df is not None:
                    # Process the dataframe
                    added_count = 0
                    errors = []
                    
                    # Check if sheet is empty
                    if df.empty:
                        st.error("**Empty Google Sheet.** Please add some data with coordinates")
                        st.stop()
                    
                    # Check if sheet has data
                    if len(df) == 0:
                        st.error("No data found in the Google Sheet")
                        st.stop()
                    
                    # Remove completely empty rows
                    df = df.dropna(how='all')
                    
                    # Check if we have any data after removing empty rows
                    if len(df) == 0:
                        st.error("**No valid data found.** The sheet contains only empty rows")
                        st.stop()
                    
                    # Debug info
                    st.info(f"📊 Found {len(df)} rows of data with columns: {', '.join(df.columns)}")
                    
                    # Find WKT geometry column or lat/lon columns
                    wkt_col = None
                    lat_col = None
                    lon_col = None
                    
                    for col in df.columns:
                        if 'wkt' in col.lower() or 'geom' in col.lower():
                            wkt_col = col
                            break
                        elif 'lat' in col.lower():
                            lat_col = col
                        elif 'lon' in col.lower() or 'lng' in col.lower():
                            lon_col = col
                    
                    # Show available columns for debugging
                    if not wkt_col and not (lat_col and lon_col):
                        st.error(f"**No coordinate columns found.** Available columns: {', '.join(df.columns)}. Looking for columns containing 'wkt', 'geom', 'lat', 'lon', or 'lng'")
                        st.stop()
                    else:
                        if wkt_col:
                            st.success(f"✅ Found WKT column: {wkt_col}")
                        if lat_col and lon_col:
                            st.success(f"✅ Found coordinate columns: {lat_col} and {lon_col}")
                    
                    if wkt_col is not None:
                        for i, row in df.iterrows():
                            wkt_text = str(row[wkt_col]).strip()
                            # Parse WKT Point format: "Point (lon lat)"
                            if wkt_text.startswith('Point (') and wkt_text.endswith(')'):
                                coords_text = wkt_text[7:-1]  # Remove "Point (" and ")"
                                coords = coords_text.split()
                                if len(coords) >= 2:
                                    try:
                                        lon = float(coords[0])
                                        lat = float(coords[1])
                                        
                                        # Create properties from all columns
                                        properties = {}
                                        for col in df.columns:
                                            properties[col] = str(row[col]).strip()
                                        
                                        # Add point with all properties
                                        add_point(lat, lon, properties)
                                        added_count += 1
                                        st.info(f"✅ Added point {added_count}: lat={lat}, lon={lon}")
                                    except ValueError:
                                        errors.append(f"Row {i+2}: Invalid coordinates in WKT - {wkt_text}")
                                else:
                                    errors.append(f"Row {i+2}: Invalid WKT format - {wkt_text}")
                            else:
                                errors.append(f"Row {i+2}: Not a Point geometry - {wkt_text}")
                    elif lat_col is not None and lon_col is not None:
                        # Process lat/lon columns
                        for i, row in df.iterrows():
                            try:
                                lat = float(row[lat_col])
                                lon = float(row[lon_col])
                                
                                # Create properties from all columns
                                properties = {}
                                for col in df.columns:
                                    properties[col] = str(row[col]).strip()
                                
                                # Add point with all properties
                                add_point(lat, lon, properties)
                                added_count += 1
                                st.info(f"✅ Added point {added_count}: lat={lat}, lon={lon}")
                            except ValueError:
                                errors.append(f"Row {i+2}: Invalid coordinates - lat: {row[lat_col]}, lon: {row[lon_col]}")
                    else:
                        st.error("**No WKT geometry column or latitude/longitude columns found.** Please ensure your sheet has either a column with 'wkt' or 'geom' in the name, OR columns with 'lat' and 'lon' in their names")
                        st.stop()
                    
                    if errors:
                        st.error("Some rows had errors")
                        for error in errors:
                            st.error(error)
                        if added_count > 0:
                            st.success(f"Successfully imported {added_count} point(s) despite some errors!")
                        else:
                            st.error("**No valid points could be imported.** Please check your data format and try again")
                    elif added_count > 0:
                        st.success(f"Successfully imported {added_count} point(s) from Google Sheets!")
                        st.info(f"Total points in session: {len(st.session_state.points)}")
                        st.rerun()
                    else:
                        st.error("**No points were imported.** Please check your data and ensure coordinates are in the correct format")
            except Exception as e:
                st.error(f"**Unexpected Error:** {str(e)}. Please check the URL and try again")
    else:
        st.warning("Please provide a Google Sheets URL")

# Create a folium map
# Set initial location based on existing points or default to Berlin
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
    center_lat, center_lon = 52.5200, 13.4050  # Default to Berlin
    zoom_level = st.session_state.user_zoom  # Use user's preferred zoom

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=zoom_level,
    tiles="OpenStreetMap"
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
    tile_layer="OpenStreetMap",
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
        tooltip=f"Point {i + 1}: {point['properties']['name']}"
    ).add_to(m)

# Display the map and capture clicks
map_data = st_folium(
    m,
    width=750,
    height=300,
    returned_objects=["last_clicked", "zoom"],
    key="map",
    use_container_width=True
)

# Handle map interactions
# Store user's zoom level
if map_data.get("zoom") and map_data["zoom"] != st.session_state.user_zoom:
    st.session_state.user_zoom = map_data["zoom"]

# Handle map clicks
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
        st.rerun()

# Only show controls if points exist
if st.session_state.points:
    # Quick removal buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Remove Last Point", key="remove_last_point"):
            if st.session_state.points:
                removed_point = st.session_state.points.pop()
                st.rerun()

    with col2:
        if st.button("Clear All Points", key="clear_all_points_quick"):
            if st.session_state.points:
                reset_points()
            st.rerun()

    # Point viewer
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

def points_to_gdf(points):
    """Convert session points (GeoJSON features) to a GeoDataFrame."""
    if not points:
        return gpd.GeoDataFrame()
    
    # Always use the Shapely approach to avoid numpy compatibility issues
    from shapely.geometry import Point
    
    geometries = []
    properties_list = []
    
    for pt in points:
        lon, lat = pt["geometry"]["coordinates"]
        geometries.append(Point(lon, lat))
        properties_list.append(pt["properties"].copy())
    
    gdf = gpd.GeoDataFrame(
        properties_list,
        geometry=geometries,
        crs="EPSG:4326"
    )
    
    return gdf


def get_base_filename():
    """Generate base filename with timestamp."""
    return f"points_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def export_data(gdf, export_type):
    """Export GeoDataFrame to the specified format."""
    if export_type == "GeoJSON":
        return json.dumps(create_geojson(), indent=2)
    elif export_type == "Esri Shapefile (.zip)":
        try:
            import tempfile
            import fiona
            from shapely.geometry import Point
            
            shp_buffer = io.BytesIO()
            with zipfile.ZipFile(shp_buffer, mode="w") as zf:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir)
                    
                    # Create schema for shapefile
                    schema = {
                        'geometry': 'Point',
                        'properties': {}
                    }
                    
                    # Add properties to schema
                    if st.session_state.points:
                        sample_props = st.session_state.points[0]["properties"]
                        for key, value in sample_props.items():
                            if isinstance(value, str):
                                schema['properties'][key] = 'str:255'
                            elif isinstance(value, (int, float)):
                                schema['properties'][key] = 'float'
                            else:
                                schema['properties'][key] = 'str:255'
                    
                    # Write shapefile using fiona directly
                    with fiona.open(
                        tmp_path / "points.shp",
                        'w',
                        driver='ESRI Shapefile',
                        schema=schema,
                        crs='EPSG:4326'
                    ) as dst:
                        for point in st.session_state.points:
                            lon, lat = point["geometry"]["coordinates"]
                            feature = {
                                'geometry': {
                                    'type': 'Point',
                                    'coordinates': [lon, lat]
                                },
                                'properties': point["properties"]
                            }
                            dst.write(feature)
                    
                    # Add all shapefile files to zip
                    for file_path in tmp_path.iterdir():
                        zf.write(file_path, arcname=file_path.name)
            
            shp_buffer.seek(0)
            return shp_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting Shapefile: {str(e)}")
            return b""
    elif export_type == "FlatGeobuf":
        try:
            import tempfile
            import fiona
            
            fgb_buffer = io.BytesIO()
            
            # Create schema for flatgeobuf
            schema = {
                'geometry': 'Point',
                'properties': {}
            }
            
            # Add properties to schema
            if st.session_state.points:
                sample_props = st.session_state.points[0]["properties"]
                for key, value in sample_props.items():
                    if isinstance(value, str):
                        schema['properties'][key] = 'str:255'
                    elif isinstance(value, (int, float)):
                        schema['properties'][key] = 'float'
                    else:
                        schema['properties'][key] = 'str:255'
            
            # Write flatgeobuf using temporary file then read into buffer
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / "points.fgb"
                
                with fiona.open(
                    str(tmp_path),
                    'w',
                    driver='FlatGeobuf',
                    schema=schema,
                    crs='EPSG:4326'
                ) as dst:
                    for point in st.session_state.points:
                        lon, lat = point["geometry"]["coordinates"]
                        feature = {
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [lon, lat]
                            },
                            'properties': point["properties"]
                        }
                        dst.write(feature)
                
                # Read the file back into the buffer
                with open(tmp_path, 'rb') as f:
                    fgb_buffer.write(f.read())
            
            fgb_buffer.seek(0)
            return fgb_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting FlatGeobuf: {str(e)}")
            return b""
    else:
        return b""

# Only show export options if points exist
if st.session_state.points:
    # Export file type selection
    export_type = st.radio(
        "Choose export file type:",
        options=["GeoJSON", "Esri Shapefile (.zip)", "FlatGeobuf"],
        index=0,
        horizontal=True,
        key="export_type_radio"
    )

    geojson_data = create_geojson()
    gdf = points_to_gdf(st.session_state.points)

    export_label = "Download Vector"

    base_filename = get_base_filename()
    export_filename = {
        "GeoJSON": f"{base_filename}.geojson",
        "Esri Shapefile (.zip)": f"{base_filename}.zip",
        "FlatGeobuf": f"{base_filename}.fgb"
    }[export_type]

    export_mime = {
        "GeoJSON": "application/geo+json",
        "Esri Shapefile (.zip)": "application/zip",
        "FlatGeobuf": "application/octet-stream"
    }[export_type]

    # Display any pending messages
    if st.session_state.message:
        if "error" in st.session_state.message.lower() or "no points" in st.session_state.message.lower():
            st.error(st.session_state.message)
        else:
            st.success(st.session_state.message)
        st.session_state.message = None  # Clear the message

    # Show download button
    if st.download_button(
        label=export_label,
        data=export_data(gdf, export_type),
        file_name=export_filename,
        mime=export_mime,
        type="primary"
    ):
        # This block executes when the button is clicked
        st.success("Export completed!")