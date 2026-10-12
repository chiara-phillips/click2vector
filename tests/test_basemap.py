from map_ui.basemap import BASEMAP_OPTIONS, DEFAULT_BASEMAP, normalize_basemap_name


def test_invalid_basemap_falls_back_to_default():
    assert normalize_basemap_name("not-a-basemap") == DEFAULT_BASEMAP
