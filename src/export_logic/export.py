"""Vector export logic: download filenames and format encoding."""

import io
import json
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import streamlit as st

EXPORT_EXTENSIONS: dict[str, str] = {
    "GeoJSON": ".geojson",
    "Esri Shapefile (.zip)": ".zip",
    "FlatGeobuf": ".fgb",
}

_KNOWN_EXPORT_SUFFIXES = frozenset({".geojson", ".json", ".zip", ".fgb"})


def get_base_filename() -> str:
    """Generate base filename with timestamp.

    Returns
    -------
    str
        A filename with format 'click2vector_YYYYMMDD_HHMMSS'.
    """
    return f"click2vector_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def build_export_filename(filename: str, export_type: str) -> str:
    """Return a download filename with the extension for ``export_type``.

    Parameters
    ----------
    filename : str
        User-provided filename, with or without an extension.
    export_type : str
        Selected export format key.

    Returns
    -------
    str
        Filename including the appropriate extension.
    """
    stem = filename.strip() or get_base_filename()
    path = Path(stem)
    if path.suffix.lower() in _KNOWN_EXPORT_SUFFIXES:
        stem = path.stem

    return f"{stem}{EXPORT_EXTENSIONS[export_type]}"


def _export_shapefile(gdf: gpd.GeoDataFrame) -> bytes:
    """Export data as shapefile.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.

    Returns
    -------
    bytes
        The shapefile data as bytes.
    """
    try:
        shp_buffer = io.BytesIO()
        with zipfile.ZipFile(shp_buffer, mode="w") as shapefile_zip:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / "points.shp"
                gdf.to_file(tmp_path, driver="ESRI Shapefile")

                for file_path in Path(tmpdir).iterdir():
                    shapefile_zip.write(file_path, arcname=file_path.name)

        shp_buffer.seek(0)
        return shp_buffer.getvalue()

    except Exception as export_error:
        st.error(f"Error exporting Shapefile: {str(export_error)}")
        return b""


def _export_flatgeobuf(gdf: gpd.GeoDataFrame) -> bytes:
    """Export data as FlatGeobuf.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.

    Returns
    -------
    bytes
        The FlatGeobuf data as bytes.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "points.fgb"
            gdf.to_file(tmp_path, driver="FlatGeobuf")
            return tmp_path.read_bytes()

    except Exception as export_error:
        st.error(f"Error exporting FlatGeobuf: {str(export_error)}")
        return b""


def _export_geojson_display(gdf: gpd.GeoDataFrame) -> str:
    """Export data as GeoJSON in pretty-printed format for display.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.

    Returns
    -------
    str
        The GeoJSON data as a formatted string ready for display.
    """
    geojson_data = json.loads(gdf.to_json())
    return json.dumps(geojson_data, indent=2)


def export_data(gdf: gpd.GeoDataFrame, export_type: str) -> str | bytes:
    """Export GeoDataFrame to the specified format.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to export.
    export_type : str
        The export format: "GeoJSON", "Esri Shapefile (.zip)", or "FlatGeobuf".

    Returns
    -------
    str or bytes
        The exported data as a string (GeoJSON) or bytes (Shapefile/FlatGeobuf).
    """
    export_functions = {
        "GeoJSON": _export_geojson_display,
        "Esri Shapefile (.zip)": _export_shapefile,
        "FlatGeobuf": _export_flatgeobuf,
    }

    return export_functions[export_type](gdf)
