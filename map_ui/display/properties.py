"""Point property keys and column helpers."""

import streamlit as st

TABLE_COLUMN_TO_PROPERTY = {
    "Name": "name",
    "Description": "description",
}
COLOR_TABLE_COLUMNS = [2, 2, 1]

def get_property_key(column_name: str) -> str:
    """Return the point property key for a table column label.

    Parameters
    ----------
    column_name : str
        Display name from the point table.

    Returns
    -------
    str
        Property key stored on each point.
    """
    return TABLE_COLUMN_TO_PROPERTY.get(column_name, column_name)


def get_colorable_columns(points: list[dict]) -> list[str]:
    """Return table columns that can drive pin colors.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.

    Returns
    -------
    list of str
        Column labels shown in the color-by dropdown.
    """
    columns = ["Name", "Description"]
    seen = set(columns)
    for point in points:
        for key in point["properties"]:
            if key in ("name", "description", "timestamp"):
                continue
            if key not in seen:
                columns.append(key)
                seen.add(key)
    return columns


def get_point_property_value(point: dict, property_key: str) -> str:
    """Return one normalized property value from a point.

    Parameters
    ----------
    point : dict
        GeoJSON feature dictionary.
    property_key : str
        Property key to read from the point.

    Returns
    -------
    str
        Stripped string value for the property.
    """
    return str(point["properties"].get(property_key, "")).strip()


def get_unique_property_values(points: list[dict], property_key: str) -> list[str]:
    """Return sorted unique values for one property across all points.

    Parameters
    ----------
    points : list of dict
        GeoJSON feature dictionaries from session state.
    property_key : str
        Property key to collect values from.

    Returns
    -------
    list of str
        Sorted unique property values; empty string means no value set.
    """
    return sorted(
        {get_point_property_value(point, property_key) for point in points}
    )
