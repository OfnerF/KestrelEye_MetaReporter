import os
from .utils import check_name
from .utils_config import get_pattern, get_patterns_to_look_for


def find_files_per_pattern(path, look_for):
    if not os.path.exists(path):
        return None

    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if any([check_name(file, pattern) for pattern in look_for]):
                file_paths.append(os.path.join(root, file))
    return file_paths


def get_run_of_file(path, pattern, stop_path):
    parent = os.path.dirname(path)
    while not check_name(os.path.basename(parent), pattern):
        if parent == stop_path:
            return None
        parent = os.path.dirname(parent)
    return os.path.basename(parent)


def extract_file_names(files):
    file_names = [get_file_name(file) for file in files]
    return sorted(list(set(file_names)))


def get_file_name(file):
    return os.path.basename(file)


def get_files_per_name(files):
    # found file names
    file_names = extract_file_names(files)
    # generate hashmap with file name as key and files as value
    paths_of_file = {file_name: [] for file_name in file_names}
    for file in files:
        file_name = get_file_name(file)
        paths_of_file[file_name].append(file)
    return paths_of_file


def remove_files_not_in_runs(files, run_pattern, root_dir):
    for file in files:
        if not get_run_of_file(file, run_pattern, root_dir):
            files.remove(file)
    return files


def generate_file_path(path, file_name):
    return os.path.join(path, file_name)


def get_sub_directories(path):
    return [f.path for f in os.scandir(path) if f.is_dir()]


def remove_children(parent, files):
    files_ = files.copy()
    for file in files_:
        if os.path.normpath(os.path.dirname(file)) == os.path.normpath(parent):
            files.remove(file)
    return files


def get_files_per_model(path, models, config_path):
    # get patterns
    run_pattern = get_pattern('run_directory', config_path)
    file_patterns = get_patterns_to_look_for(config_path)
    files_per_model = {model: [] for model in models}
    # get files
    for model in models:
        files = find_files_per_pattern(model, file_patterns)
        files = remove_files_not_in_runs(files, run_pattern, path)
        files_per_model[model] = get_files_per_name(files)
    return files_per_model


def get_model_config_files_per_model(models, config_path):
    config_files_per_model = {}
    config_pattern = get_pattern("model_config", path=config_path)
    model_dir_pattern = get_pattern("model_directory", path=config_path)
    for model in models:
        files = find_files_per_pattern(model, [config_pattern])
        files_ = files.copy()
        for file in files_:
            if not check_name(os.path.basename(os.path.dirname(file)), model_dir_pattern):
                files.remove(file)
        config_files_per_model[model] = files
    return config_files_per_model


def check_directory_basename(path, pattern):
    return check_name(os.path.basename(path), pattern)


def get_number_of_runs(model_path, run_pattern):
    number_of_runs = 0
    for sub in get_sub_directories(model_path):
        if check_directory_basename(sub, run_pattern):
            number_of_runs += 1
    return number_of_runs
