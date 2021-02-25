def get_color_map(colors, keys):
    """Returns a map in the form of {key: color}"""
    color_map = dict()
    for idx, key in enumerate(keys):
        if key not in color_map:
            color_map[key] = colors[idx % len(colors)]
    return color_map
