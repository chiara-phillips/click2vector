# Click 2 Vector

An interactive Streamlit application for creating and exporting geographic points as
multiple vector formats. Click on a map, import from Google Sheets, or enter coordinates
 manually to build your dataset, then export it for use in GIS software, web maps, or
 other spatial applications.

[Open in Streamlit](https://click2vector.streamlit.app/)

## Installation & Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd click2vector
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

### Development Setup

For development, install additional dependencies and set up pre-commit hooks:

1. **Install all dependencies (including dev)**
   ```bash
   poetry install
   ```

2. **Install pre-commit hooks**
   ```bash
   poetry run pre-commit install
   ```

3. **Run pre-commit on all files (optional)**
   ```bash
   poetry run pre-commit run --all-files
   ```

## Usage

### Adding Points
- **Map Clicking**: Click anywhere on the map to drop a pin; drag pins to adjust
  their location
- **Place Search**: Search for a place above the map and click **Add pin** to
  geocode it
- **Google Sheets Import**: Paste a public Google Sheets URL with coordinate data
  (under Advanced options)

### Google Sheets Import
Your Google Sheet should have either:
- A column with 'wkt' or 'geom' in the name containing WKT Point format: `Point (longitude latitude)`
- OR separate columns with 'lat' and 'lon' (or 'lng') in their names

### Managing Your Data
- **View Points**: Expand the "Point Table" to see all points in an editable table
- **Descriptions**: Add an optional description per point; descriptions are included
  in exports
- **Pin Colors**: Map pins are colored by description; set a color for each unique
  description in the Point Table
- **Delete Points**: Select rows in the table to remove points, or use **Remove Last
  Point** and **Clear All Points**
- **Advanced Options**: Basemap, default pin color, inset map toggle, Google Sheets
  import, export format, and GeoJSON preview
- **Export Data**: Choose GeoJSON, Esri Shapefile (.zip), or FlatGeobuf and download
  your dataset; exports include `lat` and `lon` attribute columns


## CHANGELOG
`0.9.1` : 2026-05-30
- Added `lat` and `lon` attribute columns to all export formats.
- Added export filename extension inference from the selected format.

`0.9.0` : 2026-05-30
- Added optional description column per point, included in exports.
- Added pin colors by description with per-value color pickers in the Point Table.
- Added place search above the map with geocoded **Add pin** workflow.
- Added draggable map pins.
- Added Advanced options for basemap, pin color, inset map, Google Sheets import,
  export format, and GeoJSON preview.
- Added inset map toggle (off by default).
- Raised minimum Python version to 3.11 for `streamlit-folium` compatibility.

`0.8.0` : 2025-10-13
- Remove extra below app with HTML.

`0.7.0` : 2025-08-24
- Added GeoJSON pretty print format with GeoJSON export option.

`0.6.0` : 2025-08-23
- Added columns to input and output UI to shorten scroll space in the app.

`0.5.0` : 2025-08-23
- Added ability for the user to select different basemap options (CartoDB Positron,
OpenStreetMap)

`0.4.0` : 2025-08-23
- Created custom point marker based on branding.

`0.3.1` : 2025-08-23
- Fixed bug that ignored user filename input.

`0.3.0` : 2025-08-23
- Adjusted basemap tiles from `OpenStreetMap` to `Cartodb Positron`

`0.2.0` : 2025-08-23
- Added radio button for specifying which coordinate type to import from Google Sheets.

`0.1.0` : 2025-07-16
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
