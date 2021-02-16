import re
from .utils_config import get_pattern


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
