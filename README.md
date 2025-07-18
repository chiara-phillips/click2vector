# Click 2 Vector

An interactive Streamlit application for creating and exporting geographic points as multiple vector formats. Click on a map, import from Google Sheets, or enter coordinates manually to build your dataset, then export it for use in GIS software, web maps, or other spatial applications.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

## Features

- **Interactive Map**: Click anywhere on the map to add points with search functionality
- **Google Sheets Import**: Import point data directly from public Google Sheets with WKT geometry or lat/lon columns
- **Location Search**: Built-in geocoding search to find cities, landmarks, and addresses
- **Point Management**: View, delete, and manage individual points in an interactive data table
- **Multiple Export Formats**: Download your points as GeoJSON, Esri Shapefile (.zip), or FlatGeobuf
- **Custom Filenames**: Option to specify custom filenames for exports
- **Modern UI**: Clean, responsive interface with custom styling
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
   cd blank-app
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
- **Google Sheets Import**: Paste a public Google Sheets URL with coordinate data

### Google Sheets Import
Your Google Sheet should have either:
- A column with 'wkt' or 'geom' in the name containing WKT Point format: `Point (longitude latitude)`
- OR separate columns with 'lat' and 'lon' (or 'lng') in their names

Example formats:
```
wkt_geom,name,description
Point (-122.4194 37.7749),San Francisco,Golden Gate City
Point (-74.0060 40.7128),New York,Big Apple
```

OR

```
latitude,longitude,name,description
37.7749,-122.4194,San Francisco,Golden Gate City
40.7128,-74.0060,New York,Big Apple
```

### Managing Your Data
- **View Points**: Expand the "Point Table" to see all your points in an interactive table
- **Delete Points**: Remove individual points by selecting rows in the table, or use the "Remove Last Point" and "Clear All Points" buttons
- **Export Data**: Choose from multiple formats and download your complete dataset

### Export Formats
- **GeoJSON**: Standard GeoJSON format for web applications and GIS software
- **Esri Shapefile (.zip)**: Compressed shapefile format for ArcGIS and other GIS applications
- **FlatGeobuf**: Efficient binary format for large datasets

## Dependencies

- **streamlit**: Web application framework
- **folium**: Interactive map creation with plugins
- **streamlit-folium**: Streamlit integration for folium maps
- **pandas**: Data manipulation and display
- **geopandas**: Geospatial data handling
- **fiona**: Vector data format support
- **shapely**: Geometric operations

## Project Structure

```
├── streamlit_app.py                    # Main Streamlit application
├── click_to_geojson_functionality.py   # Core GeoJSON and export functions
├── google_sheets_parser.py             # Google Sheets import functionality
├── map_point_parser.py                 # Interactive map interface
├── styling.py                          # Custom UI styling and components
├── pyproject.toml                      # Poetry configuration
└── README.md                           # Project documentation
```

## Core Functions

### `add_point(lat, lon, name_or_properties="")`
Adds a new point to the session state with automatic naming and timestamps.

### `create_geojson()`
Generates a GeoJSON FeatureCollection from all stored points.

### `export_data(gdf, export_type)`
Exports GeoDataFrame to the specified format (GeoJSON, Shapefile, or FlatGeobuf).

### `import_from_google_sheets(sheets_url)`
Imports point data from a public Google Sheets URL.

## Configuration

The app includes several customizable features:
- **Interactive Map**: OpenStreetMap tiles with search and mini-map
- **Export Options**: Multiple vector formats for different use cases
- **Custom Styling**: Modern UI with consistent button styling
- **Session Management**: Persistent data across app interactions

## Changelog

### [0.1.0] - 2024-01-16
#### Added
- Initial release of Click 2 Vector
- Interactive map interface using Folium with geocoding search
- Google Sheets import functionality with WKT and lat/lon support
- Multiple export formats (GeoJSON, Shapefile, FlatGeobuf)
- Mini-map widget for better navigation
- Point management system with interactive data table
- Custom filename support for exports
- Modern UI with custom styling
- Session state management for persistent data
- Modular architecture with separated concerns

#### Technical
- Streamlit-based web interface
- Folium integration with plugins for interactive maps and search
- GeoPandas for geospatial data handling
- Fiona for vector format support
- Responsive layout design with custom CSS

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

**Made with Streamlit, Folium, and GeoPandas**