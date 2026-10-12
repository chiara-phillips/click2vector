## CHANGELOG
`0.11.3` : 2026-10-12
- Removed support for CARTO basemap options
- Switched from poetry to uv for dependency managemnt
- Switched Python linting, import sorting, and formatting to Ruff.

`0.11.2` : 2026-05-31
- Locked the app to light mode only.

`0.11.1` : 2026-05-30
- Fixed place search crashing on Streamlit Cloud when Nominatim rejected requests.
- Added Photon geocoding fallback and user-facing errors when geocoders are
  unreachable.

`0.11.0` : 2026-05-30
- Added optional location clustering with majority-color styling.
- Added auto-zoom to fit all points when the location set changes.
- Added a **Display settings** section for basemap, inset map, legend, clustering,
  and location coloring.
- Renamed **Point table** to **Location table** and separated it from display
  options.
- Moved basemap and inset map controls out of Advanced options.

`0.10.0` : 2026-05-30
- Added Google Sheets tab selection from `#gid=...` in the shared URL.
- Added informative import errors when coordinate headers are missing or below a
  title row.
- Added pin coloring by any Point Table column, with editable legend display names.
- Added optional category color legend on the map and Folium fullscreen control.
- Reorganized search, Advanced options, Point Table, and export layout.
- Added direct row deletion in the Point Table and Enter-to-search for place lookup.
- Removed separate point-management buttons and custom global button styling.
- Added more basemap options

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