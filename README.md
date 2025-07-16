# Click to GeoJSON

An interactive Streamlit application for creating and exporting geographic points as GeoJSON files. Click on a map, search for locations, or enter coordinates manually to build your dataset, then export it for use in GIS software, web maps, or other spatial applications.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

## Features

- **Interactive Map**: Click anywhere on the map to add points with multiple basemap options
- **Location Search**: Built-in geocoding search to find cities, landmarks, and addresses
- **Manual Coordinate Entry**: Input precise latitude/longitude coordinates in bulk
- **Point Management**: View, delete, and manage individual points in a data table
- **GeoJSON Export**: Download your points as a standard GeoJSON file with timestamps
- **Multiple Map Styles**: Choose from OpenStreetMap, Esri Satellite, and CartoDB themes
- **Mini Map**: Overview navigation with collapsible mini-map widget

## Installation & Setup

This project uses Poetry for dependency management.

### Prerequisites

- Python 3.9+ (excluding 3.9.7)
- Poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd click-to-geojson
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Run the application**
   ```bash
   poetry run streamlit run streamlit_app.py
   ```

4. **Open your browser** and navigate to the local URL (typically http://localhost:8501)

## 📖 Usage

### Adding Points
- **Map Clicking**: Simply click anywhere on the interactive map to drop a pin
- **Location Search**: Use the search box in the top-right corner to find specific places
- **Manual Entry**: Use the coordinate input form to add multiple points at once

### Managing Your Data
- **View Points**: Expand the "Point Viewer" to see all your points in a table format
- **Delete Points**: Remove individual points or clear all points at once
- **Export Data**: Download your complete dataset as a GeoJSON file

### Coordinate Format
When using manual entry, use this format:
```
52.5200,13.4050,Berlin
52.5163,13.3777,Brandenburg Gate
52.5244,13.4105,Alexanderplatz
```
Format: `latitude,longitude,optional_name`

## Dependencies

- **streamlit**: Web application framework
- **folium**: Interactive map creation with plugins
- **streamlit-folium**: Streamlit integration for folium maps
- **pandas**: Data manipulation and display
- **json**: GeoJSON file handling

## Project Structure

```
├── streamlit_app.py              # Main Streamlit application
├── click_to_geojson_functionality.py  # Core GeoJSON functions
├── pyproject.toml               # Poetry configuration
└── README.md                    # Project documentation
```

## Core Functions

### `add_point(lat, lon, name="")`
Adds a new point to the session state with automatic naming and timestamps.

### `create_geojson()`
Generates a GeoJSON FeatureCollection from all stored points.

### `reset_points()`
Clears all points and resets the session state.

## Configuration

The app includes several customizable basemap options:
- **Open Street Map**: Standard OpenStreetMap tiles
- **Esri Satellite**: High-resolution satellite imagery
- **Simple Light**: Clean CartoDB Positron theme
- **Simple Dark**: Dark CartoDB theme

## Changelog

### [0.1.0] - 2024-01-16
#### Added
- Initial release of Map to GeoJSON Exporter
- Interactive map interface using Folium with geocoding search
- Mini-map widget for better navigation
- Manual coordinate entry form with bulk input support
- Point management system (add, remove, clear) with data table view
- GeoJSON export functionality with timestamps
- Session state management for persistent data
- Multiple basemap options (OpenStreetMap, Esri Satellite, CartoDB themes)
- Enhanced UI layout with improved coordinate input

#### Technical
- Streamlit-based web interface
- Folium integration with plugins for interactive maps and search
- GeoJSON standard compliance for exports
- Responsive layout design

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:
1. Check the existing issues on GitHub
2. Create a new issue with detailed information
3. Include steps to reproduce any bugs

---

**Made with Streamlit and Folium**