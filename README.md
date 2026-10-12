# Click 2 Vector

Click 2 Vector is an interactive Streamlit app for creating and exporting geographic
points as multiple vector formats. Click on a map, import from Google Sheets, or search
for a place to build your dataset, then export it for GIS software, web maps, or other
spatial applications.

[Open in Streamlit](https://click2vector.streamlit.app/)

## Installation & Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd click2vector
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync --group dev
   ```

3. **Run the application**
   ```bash
   uv run streamlit run src/app.py
   ```

4. **Open your browser** and navigate to the local URL (typically http://localhost:8501)

### Development Setup

For development, install additional dependencies and set up pre-commit hooks:

1. **Install all dependencies (including dev)**
   ```bash
   uv sync --group dev
   ```

2. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

3. **Run pre-commit on all files (optional)**
   ```bash
   uv run pre-commit run --all-files
   ```

Ruff handles Python linting, import sorting, and formatting:

```bash
uv run ruff check .
uv run ruff format .
```

Run complexity and dead-code analysis with Radon and Vulture:

```bash
uv run radon cc src -s -a
uv run radon mi src -s
uv run vulture src --min-confidence 80
uv run pytest
```

## Usage

### Adding Points
- **Map Clicking**: Click anywhere on the map to drop a pin; drag pins to adjust
  their location
- **Place Search**: Search for a place above the map and press Enter to geocode it
  as a pin (works when deployed on Streamlit Cloud via a Photon fallback if
  Nominatim is unavailable)
- **Google Sheets Import**: Paste a public Google Sheets URL with coordinate data
  (under Advanced options)

### Google Sheets Import
Paste a public Google Sheet URL with `lat` and `lon` columns under Advanced
options (or choose WKT Geometry below the URL). Include `#gid=...` in the URL when
your data is on another tab. If headers are missing, the app shows an error with
guidance on title rows and header placement.

### Managing Your Data
- **View Points**: Expand the **Location table** to see and edit points
- **Descriptions**: Add an optional description per point; descriptions are included
  in exports
- **Display Settings**: Configure basemap, inset map, legend, and pin clustering;
  choose a column to color locations by and edit legend labels and colors
- **Pin Clustering**: Toggle **Points** vs **Clusters** to show individual pins or
  merge overlapping pins into count bubbles (colored by the most common pin color
  in each group)
- **Auto-zoom**: The map fits all points when locations are added, imported, or
  removed
- **Delete Points**: Delete rows directly in the Location table using the row delete
  control
- **Export Data**: Choose export format and filename, then download; exports include
  `lat` and `lon` attribute columns


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
