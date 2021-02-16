import pandas as pd
from .utils_files import generate_file_path
from .utils_config import get_data_from_config
from .utils import check_name, get_set_name
import os


def generate_dataframes(paths_of_file, index_name, drop_rows):
    file_dataframes = {file: None for file in paths_of_file.keys()}
    for file in paths_of_file.keys():
        files = paths_of_file[file]
        file_data = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

        file_data.set_index(list(file_data.columns)[0], inplace=True)
        file_data.index.set_names(index_name, inplace=True)

        file_data.drop(index=drop_rows, inplace=True, errors='ignore')
        file_dataframes[file] = file_data
    return file_dataframes


def calculate(dataframes, group_by, metrics):
    calculated = {name: None for name in dataframes.keys()}
    for name, df in dataframes.items():
        grouped_file_data = df.groupby(group_by, group_keys=False, as_index=True, sort=False)
        # calculate stats
        aggregated = grouped_file_data.agg(metrics)

        # set column names
        aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns]

        calculated[name] = aggregated

    return calculated


def write_result(path, dataframes, file_names, nan_representation):
    for df_name, name in zip(dataframes, file_names):
        dataframes[df_name].to_csv(generate_file_path(path, name), na_rep=nan_representation, mode='w')
    return True


def generate_dataframes_per_model(models, files_per_model, session_metrics, drop_rows, config_path):
    group_column = get_data_from_config("class_column_name", path=config_path)
    dataframes_of_models = {model: None for model in models}
    for model, files_by_name in files_per_model.items():
        dataframes = generate_dataframes(files_by_name, group_column, drop_rows)
        calculated_dataframes = calculate(dataframes, group_by=group_column, metrics=session_metrics)
        dataframes_of_models[model] = calculated_dataframes

    return dataframes_of_models


def write_session_meta_result(df, result_file, nan_representation, subset):
    if os.path.exists(result_file):
        existing_df = pd.read_csv(result_file)
        df = existing_df.append(df, ignore_index=True)
        df.drop_duplicates(subset=subset, inplace=True)
    df.to_csv(result_file, mode="w", index=False, header=True, na_rep=nan_representation)
    return True


def generate_dataframe_of_model(model_path, dataframes, config_path, session_metrics):
    data = {'Model': os.path.basename(model_path)}
    for file_name, dataframe in dataframes.items():
        set_name = get_set_name(file_name, config_path)

        if set_name is not None:
            for col in [col for col in dataframe.columns if
                        any([check_name(col, "".join([".+_", metric])) for metric in
                             session_metrics])]:
                tokens = str(col).split("_")

                for clazz in dataframe.index.values:
                    data["_".join([tokens[0], set_name, tokens[1], clazz])] = [dataframe.loc[clazz, col]]
    df = pd.DataFrame(data=data)
    return df
