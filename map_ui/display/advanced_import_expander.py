"""Advanced import options expander UI."""

import streamlit as st

from import_logic import import_from_google_sheets
from map_ui.view import request_rerun


def render_advanced_import_expander() -> None:
    """Render Google Sheets import options inside an expander."""
    with st.expander("Advanced import options", expanded=False, type="compact"):
        import_col, format_col = st.columns(2)
        with import_col:
            st.caption("Public Google Sheet URL with `lat` and `lon` columns:")
            sheets_url = st.text_input(
                "Public Google Sheet URL with `lat` and `lon` columns:",
                placeholder="https://docs.google.com/spreadsheets/d/...#gid=0",
                key="sheets_url_input",
                label_visibility="collapsed",
            )
        with format_col:
            st.caption(
                "Coordinate format to import from Google Sheet (if applicable):"
            )
            coordinate_format = st.radio(
                "Coordinate format to import from Google Sheet (if applicable):",
                options=["Lat/Long", "WKT Geometry"],
                index=0,
                label_visibility="collapsed",
            )
        use_wkt = coordinate_format == "WKT Geometry"

        if sheets_url and sheets_url != st.session_state.get(
            "last_sheets_url", ""
        ):
            st.session_state.last_sheets_url = sheets_url
            success = import_from_google_sheets(sheets_url, use_wkt)
            if success:
                request_rerun()
