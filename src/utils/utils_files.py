import os
from .utils import check_name


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


def remove_redundant_files(files, run_pattern, root_dir):
    for file in files:
        if not get_run_of_file(file, run_pattern, root_dir):
            files.remove(file)
    return files


def generate_file_path(path, file_name):
    return os.path.join(path, file_name)
