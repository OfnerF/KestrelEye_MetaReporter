import pandas as pd
from .utils_files import generate_file_path
from .utils_config import get_data_from_config
from .utils import check_name, get_set_name
import os
from functools import reduce


def generate_dataframe_per_file_name(paths_per_file, index_name, drop_rows):
    """Generates dataframes per file name by concatenating the dataframes of each file."""
    file_dataframes = {file_name: None for file_name in paths_per_file.keys()}
    for file in paths_per_file.keys():
        files = paths_per_file[file]
        file_data = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

        file_data.set_index(list(file_data.columns)[0], inplace=True)
        file_data.index.set_names(index_name, inplace=True)

        file_data.drop(index=drop_rows, inplace=True, errors='ignore')
        file_dataframes[file] = file_data
    return file_dataframes


def generate_dataframes_with_run(paths_per_run_of_file, index_name, drop_rows):
    file_dataframes = {file_name: None for file_name in paths_per_run_of_file.keys()}

    for file_name, runs in paths_per_run_of_file.items():
        dataframes = []
        for run, file_path in runs.items():
            dataframe = pd.read_csv(file_path)
            dataframe['Run'] = run.replace('run', '')
            dataframes.append(dataframe)

        dataframes = pd.concat(dataframes, ignore_index=True)

        dataframes.set_index(list(dataframes.columns)[0], inplace=True)
        dataframes.index.set_names(index_name, inplace=True)

        dataframes.drop(index=drop_rows, inplace=True, errors='ignore')

        file_dataframes[file_name] = dataframes

    return file_dataframes


def calculate(dataframes, drop_columns, group_by, metrics):
    calculated = {name: None for name in dataframes.keys()}
    for name, df in dataframes.items():
        columns = [column for column in df.columns if column not in drop_columns]
        df = df[columns]
        grouped_file_data = df.groupby(group_by, group_keys=False, as_index=True, sort=False)
        # calculate stats
        aggregated = grouped_file_data.agg(metrics)

        # set column names
        aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns]

        calculated[name] = aggregated

    return calculated


def dataframes_to_csv(path, dataframes_per_file, output_file_names, nan_representation):
    for df_name, name in zip(dataframes_per_file, output_file_names):
        dataframes_per_file[df_name].to_csv(generate_file_path(path, name), na_rep=nan_representation, mode='w')
    return True


def generate_dataframes_per_model(models, files_per_model, session_metrics, drop_rows, config_path):
    group_column = get_data_from_config("class_column_name", path=config_path)
    dataframes_of_models = {model: None for model in models}
    for model, files_by_name in files_per_model.items():
        dataframes = generate_dataframe_per_file_name(files_by_name, group_column, drop_rows)
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


def generate_dataframe_of_model(dataframes, config_path, session_metrics, data):
    for file_name, dataframe in dataframes.items():

        set_name = get_set_name(file_name, config_path)
        if set_name is not None:
            # create columns
            for column in [col for col in dataframe.columns if
                           any([check_name(col, "".join([".+_", metric])) for metric in
                                session_metrics])]:
                tokens = str(column).split("_")
                # add value into data
                for clazz in dataframe.index.values:
                    data["_".join([tokens[0], set_name, tokens[1], clazz])] = [dataframe.loc[clazz, column]]

    df = pd.DataFrame(data=data)
    return df


def csv_to_dataframe(path, index, drop=[]):
    df = pd.read_csv(path, index_col=index)
    rows = [row for row in df.index if row not in drop]
    return df.loc[rows]


def get_interval_index(interval, value):
    matched_intervals = [idx for idx, x in enumerate(interval.contains(value)) if x]
    return matched_intervals[0] if len(matched_intervals) > 0 else 0


def add_run_to_column_names(dataframes_per_file, run_column='Run'):
    """Add the run, given as Series in the Dataframe, to the column names -> dataframe is reshaped"""
    dataframes_per_files_with_run = {file_name: None for file_name in dataframes_per_file.keys()}

    for file_name, dataframe in dataframes_per_file.items():
        df_groups = dataframe.groupby(run_column)
        # prepare dataframe
        dfs = []
        for name, group in df_groups:
            tmp = group.copy()
            tmp.drop(run_column, axis='columns', inplace=True)
            tmp.columns = ['_'.join([col, str(name)]) for col in tmp.columns]
            dfs.append(tmp)

        # merge prepared dataframes
        merged_dfs = reduce(lambda df1, df2: pd.merge(df1, df2, on='Class'), dfs)
        dataframes_per_files_with_run[file_name] = merged_dfs

    return dataframes_per_files_with_run


def get_dataframes_per_file_for_table_plot(dataframes_per_file, calculated_dataframes_per_file):
    """Writes the run to the column name and adds the calculation result."""
    dataframes_per_file_new = add_run_to_column_names(dataframes_per_file, 'Run')

    # add calculation dataframe to dataframe with runs in column name
    for file_name, dataframe in dataframes_per_file_new.items():
        dataframes_per_file_new[file_name] = pd.concat([dataframe, calculated_dataframes_per_file[file_name]],
                                                       axis='columns')

    return dataframes_per_file_new
