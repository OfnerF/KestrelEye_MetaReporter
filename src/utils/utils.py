import re
from .utils_config import get_pattern


def check_name(name, pattern):
    regex = re.compile(pattern)
    return regex.match(name) is not None


def get_set_name(file_name, config_path):
    regex = re.compile(get_pattern('set', config_path))
    matches = regex.search(file_name)
    set_name = matches.group(1) if matches else None
    return set_name


def nodes_to_list(data):
    """transforms the json nodes in a list of nodes"""
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
