"""
This module contains the functionality for importing data from Google Sheets.
"""

import pandas as pd
import streamlit as st

from click_to_geojson_functionality import add_point


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

    Raises
    ------
    ValueError
        If the URL format is invalid or sheet ID cannot be extracted.
    """
    try:
        if "docs.google.com/spreadsheets/d/" not in sheets_url:
            raise ValueError("Invalid Google Sheets URL format")

        sheet_id = sheets_url.split("/d/")[1].split("/")[0]
        if not sheet_id or len(sheet_id) < 10:
            raise ValueError("Invalid sheet ID extracted from URL")

        return sheet_id
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid Google Sheets URL: {e}")


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
    pandas.DataFrame
        The loaded data as a DataFrame.

    Raises
    ------
    Exception
        If the sheet cannot be accessed or loaded.
    """
    try:
        df = pd.read_csv(csv_url)
        if df.empty:
            raise ValueError("Google Sheet is empty")
        return df
    except Exception as e:
        raise Exception(f"Could not access Google Sheet: {e}")


def find_coordinate_columns(df, use_wkt=True):
    """Find WKT geometry column or lat/lon columns in the dataframe.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to search for coordinate columns.
    use_wkt : bool
        If True, search for WKT geometry column. If False, search for lat/lon columns.

    Returns
    -------
    tuple
        A tuple containing (wkt_col, lat_col, lon_col) where each is either
        the column name or None if not found.
    """
    if use_wkt:
        # Only look for WKT geometry column
        wkt_col = next(
            (
                col
                for col in df.columns
                if "wkt" in col.lower() or "geom" in col.lower()
            ),
            None,
        )
        return wkt_col, None, None
    else:
        # Only look for lat/lon columns
        lat_col = next((col for col in df.columns if "lat" in col.lower()), None)
        lon_col = next(
            (col for col in df.columns if "lon" in col.lower() or "lng" in col.lower()),
            None,
        )
        return None, lat_col, lon_col


def parse_wkt_point(wkt_text):
    """Parse WKT Point format and return lat, lon coordinates.

    Parameters
    ----------
    wkt_text : str
        The WKT Point text to parse.

    Returns
    -------
    tuple
        A tuple containing (lat, lon) coordinates.

    Raises
    ------
    ValueError
        If the WKT format is invalid or cannot be parsed.
    """
    wkt_text = str(wkt_text).strip()

    try:
        if not (wkt_text.startswith("Point (") and wkt_text.endswith(")")):
            raise ValueError("Not a valid WKT Point format")

        coords_text = wkt_text[7:-1]  # Remove "Point (" and ")"
        coords = coords_text.split()

        if len(coords) < 2:
            raise ValueError("Insufficient coordinates in WKT Point")

        lon, lat = float(coords[0]), float(coords[1])
        return lat, lon

    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid WKT Point format: {e}")


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
        try:
            lat, lon = parse_wkt_point(row[wkt_col])

            # Create properties from all columns
            properties = {col: str(row[col]).strip() for col in df.columns}

            # Add point with all properties
            add_point(lat, lon, properties)
            added_count += 1
            st.info(f"Added point {added_count}: lat={lat}, lon={lon}")

        except ValueError as e:
            errors.append(f"Row {row_index+2}: {e} - {row[wkt_col]}")

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
            lat, lon = float(row[lat_col]), float(row[lon_col])

            # Create properties from all columns
            properties = {col: str(row[col]).strip() for col in df.columns}

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


def import_from_google_sheets(sheets_url, use_wkt=True):
    """Main function to import data from Google Sheets.

    Parameters
    ----------
    sheets_url : str
        The Google Sheets URL to import data from.
    use_wkt : bool
        If True, expect WKT geometry column. If False, expect lat/lon columns.

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
            # Extract sheet ID and load data
            sheet_id = extract_sheet_id(sheets_url)
            csv_url = get_csv_url(sheet_id)
            df = load_sheet_data(csv_url)

            # Remove completely empty rows
            df = df.dropna(how="all")

            # Find coordinate columns
            wkt_col, lat_col, lon_col = find_coordinate_columns(df, use_wkt)

            # Validate we have the expected coordinate columns
            if use_wkt:
                if not wkt_col:
                    st.error(
                        f"**No WKT geometry column found.** Available columns: "
                        f"{', '.join(df.columns)}. Looking for columns containing "
                        "'wkt' or 'geom'. "
                        "Please ensure your sheet has a WKT geometry column "
                        "or toggle to use lat/lon columns instead."
                    )
                    return False
                st.success(f"Found WKT column: {wkt_col}")
            else:
                if not lat_col or not lon_col:
                    st.error(
                        f"**No lat/lon columns found.** Available columns: "
                        f"{', '.join(df.columns)}. Looking for columns containing "
                        "'lat' and 'lon' or 'lng'. "
                        "Please ensure your sheet has latitude "
                        "and longitude columns or use WKT geometry instead."
                    )
                    return False
                st.success(f"Found coordinate columns: {lat_col} and {lon_col}")

            # Process data based on column type
            if use_wkt:
                added_count, errors = process_wkt_column(df, wkt_col)
            else:
                added_count, errors = process_lat_lon_columns(df, lat_col, lon_col)

            # Handle results
            if errors:
                st.error("Some rows had errors")
                for error in errors:
                    st.error(error)

            if added_count > 0:
                st.success(
                    f"Successfully imported {added_count} point(s) from Google Sheets!"
                )
                st.info(f"Total points in session: {len(st.session_state.points)}")
                return True
            else:
                st.error(
                    "**No valid points could be imported.** Please check your "
                    "data format and try again"
                )
                return False

        except ValueError as e:
            st.error(f"**Invalid URL or Data:** {e}")
            return False
        except Exception as e:
            st.error(f"**Unexpected Error:** {e}. Please check the URL and try again")
            return False
