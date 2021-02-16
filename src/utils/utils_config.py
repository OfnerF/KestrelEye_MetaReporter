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


def get_model_data_from_config(node_list, model_config_path):
    data = {}
    for nodes in node_list:
        config_data = get_data_from_config(*nodes, path=model_config_path)
        if isinstance(config_data, dict):
            for key, value in config_data.items():
                data_key = "_".join([*nodes, key])
                data[data_key] = value
        else:
            data_key = "_".join(nodes)
            data[data_key] = config_data
    return data


def get_model_config_data(model_config_paths, node_list, different_values_in):
    data = dict()
    for model_config in model_config_paths:
        new_data = get_model_data_from_config(node_list, model_config)
        for key, value in new_data.items():
            if key not in data.keys():
                data[key] = value
            else:
                if key in different_values_in:
                    current_values = list(set(str(data[key]).split('/')))
                    data[key] = '/'.join([*current_values, str(value)])
    return data
