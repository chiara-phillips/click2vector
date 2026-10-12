"""
This module contains the styling for the Streamlit app.
"""

import streamlit as st

DEFAULT_BUTTON_COLOR = "#f75f61"


def inject_global_css() -> None:
    """Inject custom global CSS styles into the Streamlit app.

    Returns
    -------
    None
        CSS is injected directly into the Streamlit app via ``st.markdown``.
    """
    st.markdown(
        """
            <link href="https://fonts.googleapis.com/css?family=Inter:400,500,600"
                  rel="stylesheet">
            <style>
                html, body, [class*="css"] {
                    font-family: 'Inter', system-ui, 'Segoe UI', Arial, sans-serif;
                }
                /* Hide the zero-width place-search submit control; Enter submits */
                div[data-testid="stForm"]:has(
                    input[aria-label="Search for a place to add"]
                ) div[data-testid="stFormSubmitButton"] {
                    display: none;
                }
            </style>
            """,
        unsafe_allow_html=True,
    )
