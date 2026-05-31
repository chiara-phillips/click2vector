"""Basemap tile discovery, labeling, and picker session state."""

import streamlit as st
import xyzservices.providers as xyz_providers

DEFAULT_BASEMAP = "CartoDB.Positron"
LEGACY_BASEMAP_NAMES = {
    "CartoDB Positron": "CartoDB.Positron",
    "OpenStreetMap": "CartoDB.Positron",
}
BASEMAP_PROVIDER_GROUPS = (
    "CartoDB",
    "Esri",
)
BASEMAP_EXCLUDED_NAME_PARTS = (
    "OnlyLabels",
    "LabelsUnder",
    "Lines",
    "Background",
    "overlay",
    "HillShading",
    "pistes",
    "Reference",
    "Arctic",
    "Antarctic",
    "LandLot",
)
BASEMAP_EXCLUDED_TILES = frozenset(
    {
        "Esri.NatGeoWorldMap",
        "Esri.WorldShadedRelief",
        "Esri.WorldTerrain",
    }
)
BASEMAP_URL_KEY_PARTS = ("{apikey}", "{access_token}", "{token}", "{key}")
BASEMAP_API_KEY_DOMAINS = (
    "stadiamaps.com",
    "jawg.io",
    "api.mapbox.com",
    "thunderforest.com",
    "maptiler.com",
    "geoapify.com",
    "locationiq.com",
    "hereapi.com",
)


def _is_excluded_basemap(name: str) -> bool:
    """Return whether a tile name should be omitted from the basemap list."""
    if name in BASEMAP_EXCLUDED_TILES:
        return True
    return any(part in name for part in BASEMAP_EXCLUDED_NAME_PARTS)


def _provider_requires_api_key(url: str) -> bool:
    """Return whether a tile URL likely requires an API key."""
    lowered = url.lower()
    if any(part in lowered for part in BASEMAP_URL_KEY_PARTS):
        return True
    return any(domain in lowered for domain in BASEMAP_API_KEY_DOMAINS)


def _collect_provider_tiles(provider_name: str) -> list[str]:
    """Return tile ids for one xyzservices provider group."""
    provider = getattr(xyz_providers, provider_name, None)
    if provider is None:
        return []
    if isinstance(provider, dict) and "url" in provider:
        name = provider.get("name", provider_name)
        if _is_excluded_basemap(name) or _provider_requires_api_key(provider["url"]):
            return []
        return [name]

    tiles = []
    for variant in provider.values():
        if not isinstance(variant, dict) or "url" not in variant:
            continue
        name = variant.get("name", provider_name)
        if _is_excluded_basemap(name):
            continue
        if _provider_requires_api_key(variant["url"]):
            continue
        tiles.append(name)
    return tiles


def build_basemap_options() -> list[str]:
    """Return free raster basemap tile ids supported by Folium."""
    options = []
    seen: set[str] = set()
    for provider_name in BASEMAP_PROVIDER_GROUPS:
        for tile_name in _collect_provider_tiles(provider_name):
            if tile_name in seen:
                continue
            options.append(tile_name)
            seen.add(tile_name)
    return options


BASEMAP_OPTIONS = build_basemap_options()


def format_basemap_label(tile_name: str) -> str:
    """Return a readable label for one basemap tile id."""
    provider, _, variant = tile_name.partition(".")
    if not variant:
        return tile_name

    provider_labels = {
        "CartoDB": "Carto",
    }
    provider_label = provider_labels.get(provider, provider)
    variant_label = (
        variant.replace("NoLabels", " (no labels)")
        .replace("DarkMatter", "Dark Matter")
        .replace("LabelsUnder", "Labels Under")
    )
    return f"{provider_label} · {variant_label}"


def normalize_basemap_name(name: str) -> str:
    """Return a valid basemap tile id, mapping legacy names when needed."""
    normalized = LEGACY_BASEMAP_NAMES.get(name, name)
    if normalized in BASEMAP_OPTIONS:
        return normalized
    return DEFAULT_BASEMAP


def sync_basemap_choice() -> None:
    """Persist basemap selection across reruns triggered before widgets render."""
    st.session_state.basemap_name = st.session_state.basemap_picker


def sync_map_style_from_pickers() -> None:
    """Copy widget values into persistent map style session state."""
    if "basemap_picker" in st.session_state:
        st.session_state.basemap_name = st.session_state.basemap_picker


def ensure_basemap_picker_state() -> None:
    """Initialize or repair the basemap picker session state value."""
    if "basemap_picker" not in st.session_state:
        st.session_state.basemap_picker = normalize_basemap_name(
            st.session_state.basemap_name
        )
    elif st.session_state.basemap_picker not in BASEMAP_OPTIONS:
        st.session_state.basemap_picker = normalize_basemap_name(
            st.session_state.basemap_picker
        )


def resolve_basemap_name() -> str:
    """Return the active basemap tile id from session state."""
    picker_value = st.session_state.get("basemap_picker")
    if picker_value in BASEMAP_OPTIONS:
        return picker_value
    return normalize_basemap_name(st.session_state.get("basemap_name", DEFAULT_BASEMAP))
