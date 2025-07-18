"""
This module contains the styling for the Streamlit app.
"""

import streamlit as st


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
    """Inject custom global CSS styles into Streamlit app to standardize buttons look.

    This function applies consistent styling to all `st.button` and `st.download_button`
    elements across all pages in the app, including background color, text color,
    border radius, padding, and hover/click effects.

    Returns
    -------
    None
        CSS is injected directly into the Streamlit app via `st.markdown`.
    """
    st.markdown(
        f"""
            <link href="https://fonts.googleapis.com/css?family=Inter:400,500,600"
                  rel="stylesheet">
            <style>
                /* Default Style for ALL Buttons (Generate & Download) */
                div.stButton > button,
                div.stDownloadButton > button {{
                    background-color: #f75f61 !important;
                    color: white !important;
                    border-radius: 100px !important;
                    border: none;
                    padding: 8px 16px;
                    font-size: 16px;
                    transition: 0.3s;
                    font-family: 'Inter', system-ui, 'Segoe UI', Arial, sans-serif
                    !important;
                }}

                /* Hover Effect for ALL Buttons */
                div.stButton > button:hover,
                div.stDownloadButton > button:hover {{
                    background-color: #f97f81 !important;
                    color: white !important;
                }}

                /* Clicked (Active) Effect for ALL Buttons */
                div.stButton > button:focus,
                div.stButton > button:active,
                div.stDownloadButton > button:focus,
                div.stDownloadButton > button:active {{
                    background-color: #f75f61 !important;
                    color: white !important;
                    outline: none !important;
                    border: none !important;
                }}
                </style>
            """,
        unsafe_allow_html=True,
    )
