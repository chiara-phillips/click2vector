"""
This module contains the styling for the Streamlit app.
"""

import streamlit as st

DEFAULT_BUTTON_COLOR = "#f75f61"


def create_styled_title(
    text: str, level: int = 1, color: str = "#f75f61", align: str = "left"
) -> None:
    """Render a styled HTML heading in Streamlit using Seqana's design conventions.

    Parameters
    ----------
    text : str
        The text to display as a heading.
    level : int, optional
        Heading level from 1 (largest) to 6 (smallest). Defaults to 1.
    color : str, optional
        CSS-compatible color code for the heading text. Defaults to Seqana's
        primary color.
    align : str, optional
        Text alignment: "left", "center", or "right". Defaults to "left".

    Returns
    -------
    None
        Outputs the styled heading directly to the Streamlit app.
    """
    if not 1 <= level <= 6:
        raise ValueError("Heading level must be between 1 and 6")

    st.markdown(
        f"<h{level} style='text-align: {align}; color: {color};'>" f"{text}</h{level}>",
        unsafe_allow_html=True,
    )


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
