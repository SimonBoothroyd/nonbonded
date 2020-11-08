def unique_markers(n_markers):
    """Returns a unique list of distinguishable markers. These are predominantly based
    on the default seaborn markers.

    Parameters
    ----------
    n_markers
        The number of markers to return (max=11).
    """

    markers = [
        "circle",
        "x",
        "diamond",
        "cross",
        "square",
        "star-diamond",
        "triangle-up",
        "star-square",
        "triangle-down",
        "pentagon",
        "hexagon",
    ]

    assert n_markers <= len(markers)
    return markers[:n_markers]


def unique_colors(n_colors):
    """Returns a unique list of distinguishable colors. These are taken from the
    default seaborn `colorblind` color palette.

    Parameters
    ----------
    n_colors
        The number of colors to return (max=10).
    """

    colors = [
        (0.004, 0.451, 0.698),
        (0.871, 0.561, 0.020),
        (0.008, 0.620, 0.451),
        (0.835, 0.369, 0.000),
        (0.800, 0.471, 0.737),
        (0.792, 0.569, 0.380),
        (0.984, 0.686, 0.894),
        (0.580, 0.580, 0.580),
        (0.925, 0.882, 0.200),
        (0.337, 0.706, 0.914),
    ]

    assert n_colors <= len(colors)
    return colors[:n_colors]
