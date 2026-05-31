"""Overlapping pin cluster styling."""

CLUSTER_MIN_SIZE_PX = 22
CLUSTER_SIZE_PER_POINT_PX = 3
CLUSTER_MAX_SIZE_PX = 40
CLUSTER_MAX_RADIUS_PX = 20
CLUSTER_DISABLE_AT_ZOOM = 16


def marker_cluster_icon_create_function(fallback_color: str) -> str:
    """Return Leaflet ``iconCreateFunction`` JS for sized count cluster icons.

    Cluster fill color is the most common ``pointColor`` among child markers.

    Parameters
    ----------
    fallback_color : str
        CSS fill color when child markers have no ``pointColor`` option.

    Returns
    -------
    str
        JavaScript function body assigned to MarkerCluster icon creation.
    """
    return f"""
    function(cluster) {{
        var count = cluster.getChildCount();
        var colorCounts = {{}};
        var dominantColor = "{fallback_color}";
        var maxColorCount = 0;
        cluster.getAllChildMarkers().forEach(function(marker) {{
            var color = marker.options.pointColor || "{fallback_color}";
            colorCounts[color] = (colorCounts[color] || 0) + 1;
            if (colorCounts[color] > maxColorCount) {{
                maxColorCount = colorCounts[color];
                dominantColor = color;
            }}
        }});
        var size = Math.min(
            {CLUSTER_MAX_SIZE_PX},
            {CLUSTER_MIN_SIZE_PX} + (count - 1) * {CLUSTER_SIZE_PER_POINT_PX}
        );
        var half = Math.floor(size / 2);
        var fontSize = Math.max(10, Math.min(14, Math.floor(size / 2)));
        return L.divIcon({{
            html: '<div style="background-color:' + dominantColor +
                ';width:' + size + 'px;height:' + size + 'px;border-radius:50%;' +
                'border:2px solid white;display:flex;align-items:center;' +
                'justify-content:center;color:white;font-weight:700;font-size:' +
                fontSize + 'px;line-height:1;box-shadow:0 1px 4px rgba(0,0,0,0.35);' +
                'box-sizing:border-box;">' + count + '</div>',
            className: '',
            iconSize: [size, size],
            iconAnchor: [half, half]
        }});
    }}
    """
