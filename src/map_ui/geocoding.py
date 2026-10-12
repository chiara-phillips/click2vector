"""Place search and geocoding."""

from typing import Optional

import requests
import streamlit as st

from points.session import add_point
from map_ui.display.advanced_import_expander import render_advanced_import_expander

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PHOTON_URL = "https://photon.komoot.io/api/"
GEOCODER_APP_URL = "https://click2vector.streamlit.app/"
USER_AGENT = f"click2vector/0.11.2 ({GEOCODER_APP_URL})"


def _geocode_request_params() -> dict:
    """Shared HTTP settings for geocoding providers."""
    return {"headers": {"User-Agent": USER_AGENT}, "timeout": 10}


def _geocode_with_nominatim(query: str) -> tuple[Optional[dict], bool]:
    """Look up a place name using the Nominatim geocoding API.

    Parameters
    ----------
    query : str
        Place name or address to search for.

    Returns
    -------
    tuple[dict or None, bool]
        Place data and whether the service returned a successful HTTP response.
    """
    response = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "jsonv2", "limit": 1},
        **_geocode_request_params(),
    )
    if not response.ok:
        return None, False

    results = response.json()
    if not results:
        return None, True

    place = results[0]
    return {
        "lat": float(place["lat"]),
        "lng": float(place["lon"]),
        "name": place.get("display_name", query),
    }, True


def _geocode_with_photon(query: str) -> tuple[Optional[dict], bool]:
    """Look up a place name using the Photon geocoding API.

    Parameters
    ----------
    query : str
        Place name or address to search for.

    Returns
    -------
    tuple[dict or None, bool]
        Place data and whether the service returned a successful HTTP response.
    """
    response = requests.get(
        PHOTON_URL,
        params={"q": query, "limit": 1},
        **_geocode_request_params(),
    )
    if not response.ok:
        return None, False

    features = response.json().get("features") or []
    if not features:
        return None, True

    feature = features[0]
    coordinates = feature["geometry"]["coordinates"]
    properties = feature.get("properties") or {}
    name = properties.get("name") or query
    return {
        "lat": float(coordinates[1]),
        "lng": float(coordinates[0]),
        "name": name,
    }, True


def geocode_place_name(query: str) -> tuple[Optional[dict], Optional[str]]:
    """Look up a place name using public geocoding APIs.

    Nominatim is tried first; Photon is used as a fallback when Nominatim is
    unreachable (common on shared cloud hosting IPs).

    Parameters
    ----------
    query : str
        Place name or address to search for.

    Returns
    -------
    tuple[dict or None, str or None]
        Place data with ``lat``, ``lng``, and ``name`` keys, plus an optional
        user-facing error when no geocoder could be reached.
    """
    had_successful_response = False
    for geocoder in (_geocode_with_nominatim, _geocode_with_photon):
        try:
            place, responded = geocoder(query)
        except requests.RequestException:
            continue
        if responded:
            had_successful_response = True
        if place is not None:
            return place, None

    if not had_successful_response:
        return None, (
            "Error: Place search is temporarily unavailable. "
            "Try again later or click the map to add a pin."
        )
    return None, None


def add_searched_place(lat: float, lng: float, name: str) -> None:
    """Add a geocoded place to the map and point table.

    Parameters
    ----------
    lat : float
        Latitude of the place.
    lng : float
        Longitude of the place.
    name : str
        Display name for the new point.

    Returns
    -------
    None
        Updates session state with the new point and map view.
    """
    from map_ui.view import set_map_view

    add_point(lat, lng, name)
    st.session_state.last_click = (lat, lng)
    set_map_view(lat, lng)


def render_search_section() -> None:
    """Render place search and advanced map or import options."""
    from map_ui.view import request_rerun

    with st.container(border=False):
        with st.form("place_search_form", border=False):
            query = st.text_input(
                "Search for a place to add",
                placeholder="e.g. Berlin",
            )
            submitted = st.form_submit_button("\u200b")

            if submitted and query.strip():
                place, error = geocode_place_name(query.strip())
                if error is not None:
                    st.session_state.message = error
                elif place is None:
                    st.session_state.message = (
                        f"No results found for '{query.strip()}'."
                    )
                else:
                    add_searched_place(place["lat"], place["lng"], place["name"])
                    request_rerun()

        render_advanced_import_expander()

