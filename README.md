# Click 2 Vector

An interactive Streamlit application for creating and exporting geographic points as multiple vector formats. Click on a map, import from Google Sheets, or enter coordinates manually to build your dataset, then export it for use in GIS software, web maps, or other spatial applications.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://click2vector.streamlit.app/)

## Installation & Setup

This project uses pip for dependency management.

### Prerequisites

- Python 3.9+ (excluding 3.9.7)
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd click2vector
   ```

2. **Install dependencies with pip**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open your browser** and navigate to the local URL (typically http://localhost:8501)

### Development Setup

For development, install additional dependencies and set up pre-commit hooks:

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

3. **Run pre-commit on all files (optional)**
   ```bash
   pre-commit run --all-files
   ```

## Usage

### Adding Points
- **Map Clicking**: Simply click anywhere on the interactive map to drop a pin
- **Location Search**: Use the search box in the top-right corner to find specific places
- **Google Sheets Import**: Paste a public Google Sheets URL with coordinate data

### Google Sheets Import
Your Google Sheet should have either:
- A column with 'wkt' or 'geom' in the name containing WKT Point format: `Point (longitude latitude)`
- OR separate columns with 'lat' and 'lon' (or 'lng') in their names

### Managing Your Data
- **View Points**: Expand the "Point Table" to see all your points in an interactive table
- **Delete Points**: Remove individual points by selecting rows in the table, or use the "Remove Last Point" and "Clear All Points" buttons
- **Export Data**: Choose from multiple formats and download your complete dataset

### Export Formats
- **GeoJSON**: Standard GeoJSON format for web applications and GIS software
- **Esri Shapefile (.zip)**: Compressed shapefile format for ArcGIS and other GIS applications
- **FlatGeobuf**: Efficient binary format for large datasets

## Dependencies

- **streamlit==1.47.0**: Web application framework
- **folium==0.20.0**: Interactive map creation with plugins
- **streamlit-folium==0.25.0**: Streamlit integration for folium maps
- **pandas==2.3.1**: Data manipulation and display
- **geopandas==0.13.2**: Geospatial data handling (includes fiona and shapely)

All dependencies are specified in `requirements.txt` for easy installation.

## Project Structure

```
├── streamlit_app.py                    # Main Streamlit application
├── click_to_geojson_functionality.py   # Core GeoJSON and export functions
├── google_sheets_parser.py             # Google Sheets import functionality
├── map_point_parser.py                 # Interactive map interface
├── styling.py                          # Custom UI styling and components
├── requirements.txt                    # Python dependencies
└── README.md                           # Project documentation
```

## CHANGELOG

`0.1.0` - 2024-01-16
- Initial release


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
