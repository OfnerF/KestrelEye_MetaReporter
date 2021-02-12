import pandas as pd
from .utils_files import generate_file_path


def generate_dataframes(paths_of_file, index_name, drop_rows):
    file_dataframes = []

    for file in paths_of_file:
        files = paths_of_file[file]
        file_data = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

        file_data.set_index(list(file_data.columns)[0], inplace=True)
        file_data.index.set_names(index_name, inplace=True)

        file_data.drop(index=drop_rows, inplace=True, errors='ignore')

        file_dataframes.append(file_data)
    return file_dataframes


def write_result(path, dataframes, file_names, nan_representation):
    for df, name in zip(dataframes, file_names):
        df.to_csv(generate_file_path(path, name), na_rep=nan_representation, mode='w')
    return True
