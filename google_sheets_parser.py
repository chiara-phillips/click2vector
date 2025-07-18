"""
This module contains the functionality for importing data from Google Sheets.
"""

import pandas as pd
import streamlit as st

from click_to_geojson_functionality import add_point


def validate_google_sheets_url(sheets_url):
    """Validate Google Sheets URL format and extract sheet ID.

    Parameters
    ----------
    sheets_url : str
        The Google Sheets URL to validate.

    Returns
    -------
    str or None
        The extracted sheet ID if valid, None if invalid.
    """
    if "docs.google.com/spreadsheets/d/" not in sheets_url:
        st.error(
            "**Invalid Google Sheets URL format.** Please use a public URL that "
            "looks like: "
            "https://docs.google.com/spreadsheets/d/SHEET_ID/edit"
        )
        return None

    try:
        sheet_id = sheets_url.split("/d/")[1].split("/")[0]
        if not sheet_id or len(sheet_id) < 10:  # Basic validation
            st.error(
                "**Invalid Google Sheets ID:** Could not extract a valid sheet ID "
                "from the URL"
            )
            return None
        return sheet_id
    except IndexError:
        st.error(
            "**Invalid Google Sheets URL.** Please check the URL format and try again"
        )
        return None


def extract_sheet_id(sheets_url):
    """Extract sheet ID from Google Sheets URL.

    Parameters
    ----------
    sheets_url : str
        The Google Sheets URL to extract the ID from.

    Returns
    -------
    str
        The extracted sheet ID.
    """
    return sheets_url.split("/d/")[1].split("/")[0]


def get_csv_url(sheet_id):
    """Generate CSV export URL for Google Sheets.

    Parameters
    ----------
    sheet_id : str
        The Google Sheets ID.

    Returns
    -------
    str
        The CSV export URL for the sheet.
    """
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"


def load_sheet_data(csv_url):
    """Load data from Google Sheets CSV URL.

    Parameters
    ----------
    csv_url : str
        The CSV export URL for the Google Sheet.

    Returns
    -------
    pandas.DataFrame or None
        The loaded data as a DataFrame, None if loading failed.
    """
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as csv_error:
        st.error(
            "**Could not access Google Sheet.** Please check the URL is correct and "
            "the sheet is publicly shared (Anyone with link can view)"
        )
        return None


def find_coordinate_columns(df):
    """Find WKT geometry column or lat/lon columns in the dataframe.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to search for coordinate columns.

    Returns
    -------
    tuple
        A tuple containing (wkt_col, lat_col, lon_col) where each is either
        the column name or None if not found.
    """
    wkt_col = None
    lat_col = None
    lon_col = None

    for col in df.columns:
        if "wkt" in col.lower() or "geom" in col.lower():
            wkt_col = col
            break
        elif "lat" in col.lower():
            lat_col = col
        elif "lon" in col.lower() or "lng" in col.lower():
            lon_col = col

    return wkt_col, lat_col, lon_col


def parse_wkt_point(wkt_text):
    """Parse WKT Point format and return lat, lon coordinates.

    Parameters
    ----------
    wkt_text : str
        The WKT Point text to parse.

    Returns
    -------
    tuple
        A tuple containing (lat, lon) coordinates, or (None, None) if parsing failed.
    """
    wkt_text = str(wkt_text).strip()
    # Parse WKT Point format: "Point (lon lat)"
    if wkt_text.startswith("Point (") and wkt_text.endswith(")"):
        coords_text = wkt_text[7:-1]  # Remove "Point (" and ")"
        coords = coords_text.split()
        if len(coords) >= 2:
            try:
                lon = float(coords[0])
                lat = float(coords[1])
                return lat, lon
            except ValueError:
                return None, None
    return None, None


def process_wkt_column(df, wkt_col):
    """Process dataframe with WKT geometry column.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame containing WKT geometry data.
    wkt_col : str
        The name of the WKT geometry column.

    Returns
    -------
    tuple
        A tuple containing (added_count, errors) where added_count is the number
        of successfully added points and errors is a list of error messages.
    """
    added_count = 0
    errors = []

    for row_index, row in df.iterrows():
        lat, lon = parse_wkt_point(row[wkt_col])

        if lat is not None and lon is not None:
            # Create properties from all columns
            properties = {}
            for col in df.columns:
                properties[col] = str(row[col]).strip()

            # Add point with all properties
            add_point(lat, lon, properties)
            added_count += 1
            st.info(f"Added point {added_count}: lat={lat}, lon={lon}")
        else:
            errors.append(f"Row {row_index+2}: Invalid WKT format - {row[wkt_col]}")

    return added_count, errors


def process_lat_lon_columns(df, lat_col, lon_col):
    """Process dataframe with latitude and longitude columns.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame containing latitude and longitude data.
    lat_col : str
        The name of the latitude column.
    lon_col : str
        The name of the longitude column.

    Returns
    -------
    tuple
        A tuple containing (added_count, errors) where added_count is the number
        of successfully added points and errors is a list of error messages.
    """
    added_count = 0
    errors = []

    for row_index, row in df.iterrows():
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
            st.info(f"Added point {added_count}: lat={lat}, lon={lon}")
        except ValueError:
            errors.append(
                f"Row {row_index+2}: Invalid coordinates - lat: {row[lat_col]}, "
                f"lon: {row[lon_col]}"
            )

    return added_count, errors


def import_from_google_sheets(sheets_url):
    """Main function to import data from Google Sheets.

    Parameters
    ----------
    sheets_url : str
        The Google Sheets URL to import data from.

    Returns
    -------
    bool
        True if import was successful, False otherwise.
    """
    if not sheets_url.strip():
        st.warning("Please provide a Google Sheets URL")
        return False

    with st.spinner("Importing data from Google Sheets..."):
        try:
            # Validate URL and extract sheet ID
            sheet_id = validate_google_sheets_url(sheets_url)
            if not sheet_id:
                return False

            # Load data from Google Sheets
            csv_url = get_csv_url(sheet_id)
            df = load_sheet_data(csv_url)
            if df is None:
                return False

            # Check if sheet is empty
            if df.empty:
                st.error(
                    "**Empty Google Sheet.** Please add some data with coordinates"
                )
                return False

            # Remove completely empty rows
            df = df.dropna(how="all")

            # Find coordinate columns
            wkt_col, lat_col, lon_col = find_coordinate_columns(df)

            # Show available columns for debugging
            if not wkt_col and not (lat_col and lon_col):
                st.error(
                    f"**No coordinate columns found.** Available columns: "
                    f"{', '.join(df.columns)}. Looking for columns containing "
                    "'wkt', 'geom', 'lat', 'lon', or 'lng'"
                )
                return False
            else:
                if wkt_col:
                    st.success(f"Found WKT column: {wkt_col}")
                if lat_col and lon_col:
                    st.success(f"Found coordinate columns: {lat_col} and {lon_col}")

            # Process data based on column type
            added_count = 0
            errors = []

            if wkt_col is not None:
                added_count, errors = process_wkt_column(df, wkt_col)
            elif lat_col is not None and lon_col is not None:
                added_count, errors = process_lat_lon_columns(df, lat_col, lon_col)
            else:
                st.error(
                    "**No WKT geometry column or latitude/longitude columns found.** "
                    "Please ensure your sheet has either a column with 'wkt' or 'geom' "
                    "in the name, OR columns with 'lat' and 'lon' in their names"
                )
                return False

            # Handle results
            if errors:
                st.error("Some rows had errors")
                for error in errors:
                    st.error(error)
                if added_count > 0:
                    st.success(f"Successfully imported {added_count} point(s)")
                else:
                    st.error(
                        "**No valid points could be imported.** Please check your "
                        "data format and try again"
                    )
                    return False
            elif added_count > 0:
                st.success(
                    f"Successfully imported {added_count} point(s) from Google Sheets!"
                )
                st.info(f"Total points in session: {len(st.session_state.points)}")
                return True
            else:
                st.error(
                    "**No points were imported.** Please check your data and ensure "
                    "coordinates are in the correct format"
                )
                return False

        except Exception as import_error:
            st.error(
                f"**Unexpected Error:** {str(import_error)}. Please check the URL "
                "and try again"
            )
            return False
