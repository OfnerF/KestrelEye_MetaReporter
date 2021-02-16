import re
from .utils_config import get_pattern, get_model_data_from_config


def check_name(name, pattern):
    regex = re.compile(pattern)
    return regex.match(name) is not None


def get_set_name(file_name, config_path):
    if check_name(file_name, get_pattern('train_set', config_path)):
        set_name = 'train'
    elif check_name(file_name, get_pattern('val_set', config_path)):
        set_name = 'val'
    elif check_name(file_name, get_pattern('test_set', config_path)):
        set_name = 'test'
    else:
        set_name = None
    return set_name


def nodes_to_list(data):
    def nodes_to_list_(nodes, node_list, current_nodes):
        if isinstance(nodes, dict):
            for key, value in nodes.items():
                temp_nodes = current_nodes.copy()
                temp_nodes.append(key)
                new_nodes = nodes_to_list_(value, node_list, temp_nodes)

            return new_nodes

        elif isinstance(nodes, list):
            for node in nodes:
                temp_nodes = current_nodes.copy()
                new_nodes = nodes_to_list_(node, node_list, temp_nodes)

            return new_nodes

        else:
            current_nodes.append(nodes)
            node_list.append(current_nodes)
            return node_list

    result = []
    for entry in data:
        result.extend(nodes_to_list_(entry, [], []))
    return result
