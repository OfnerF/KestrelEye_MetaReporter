import json


def get_data_from_config(*nodes, path):
    with open(path) as config_file:
        data = json.load(config_file)
        for value in nodes:
            data = data[value]
        return data


def get_pattern(name, path):
    return get_data_from_config("pattern", name, path=path)


def get_patterns(names, path):
    return [get_pattern(name, path) for name in names]


def get_patterns_to_look_for(path):
    with open(path) as config_file:
        data = json.load(config_file)
        return get_patterns(data['look_for'], path)
