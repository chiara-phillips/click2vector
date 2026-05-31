"""Map display: markers, legend, styling, table, and settings."""

from map_ui.display.legend import (
    add_map_color_legend,
    get_legend_display_name,
    sync_legend_display_names_from_inputs,
)
from map_ui.display.location_table_expander import render_location_table_expander
from map_ui.display.markers import add_existing_points_to_map
from map_ui.display.pin_colors import (
    sync_property_color_state,
    sync_property_colors_from_pickers,
)
from map_ui.display.properties import get_property_key
from map_ui.display.display_settings_expander import (
    render_display_settings_expander,
)
from map_ui.display.widget_key import map_widget_key

__all__ = [
    "add_existing_points_to_map",
    "add_map_color_legend",
    "render_location_table_expander",
    "get_legend_display_name",
    "get_property_key",
    "map_widget_key",
    "render_display_settings_expander",
    "sync_legend_display_names_from_inputs",
    "sync_property_color_state",
    "sync_property_colors_from_pickers",
]
