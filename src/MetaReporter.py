import os

import pandas as pd

from .utils import nodes_to_list, check_name, get_set_name
from .utils.utils_config import get_data_from_config, get_pattern, get_patterns_to_look_for, get_model_config_data
from .utils.utils_files import find_files_per_pattern, remove_files_not_in_runs, get_sub_directories, \
    get_model_config_files_per_model, get_number_of_runs, \
    generate_file_path, get_paths_per_run_of_name, get_meta_files_per_model, get_base_name
from .utils.utils_pandas import dataframes_to_csv, calculate, generate_dataframe_of_file_per_model, \
    write_session_meta_result, generate_summary_dataframe_of_model, generate_dataframes_with_run, \
    get_dataframes_per_file_for_table_plot
from .visualization.BarPlotter import BarPlotter
from .visualization.TablePlotter import TablePlotter
from .visualization.ViolinPlotter import ViolinPlotter


class MetaReporter:
    """
    Class for generating meta report files and plots.
    for generating on model level (with same parameters), set level to 0 and path is the path to the model.
    for generating over models with different parameters, set level to 1 and path is the path of the session.
    """

    def __init__(self, path, result_path, config_path=None, metrics=None, drop_rows=None, level=1, plot_format=None):
        self.path = path
        self.result_path = result_path
        self.config_path = config_path

        if metrics is None:
            metrics = get_data_from_config('metrics', path=self.config_path)
        self.model_metrics = metrics['model']
        self.session_metrics = metrics['session']

        if drop_rows is not None:
            self.drop_rows = drop_rows
        else:
            self.drop_rows = get_data_from_config('drop', path=self.config_path)

        if plot_format is not None:
            self.plot_format = plot_format
        else:
            self.plot_format = get_data_from_config("plot_format", path=self.config_path)

        if level == 0:
            self.generate_per_model()
        elif level == 1:
            self.generate_per_session()

    def __str__(self):
        return "MetaReporter(model_path: {} | result_path: {} | model_metrics: {} | session_metrics: {} |" \
               " drop: {})".format(self.path,
                                   self.result_path,
                                   self.model_metrics,
                                   self.session_metrics,
                                   self.drop_rows)

    def generate_per_model(self, model_path=None, generate_plots=True):
        """ generates the meta report for each model in the session with the same parameters"""
        if model_path is None:
            model_path = self.path
            result_path = self.result_path
        else:
            result_path = model_path

        run_pattern = get_pattern('run_directory', self.config_path)
        group_column = get_data_from_config("class_column_name", path=self.config_path)

        # get files
        file_patterns = get_patterns_to_look_for(self.config_path)
        files = find_files_per_pattern(model_path, file_patterns)
        files = remove_files_not_in_runs(files, run_pattern, model_path)

        # {filename: {run: path}}
        paths_per_run_of_file = get_paths_per_run_of_name(files, run_pattern, self.path)

        # {filename: {dataframe}}, dataframe has column Run
        dataframes_per_file = generate_dataframes_with_run(paths_per_run_of_file, group_column, self.drop_rows)

        # calculate metrics
        # {filename: dataframe}
        calculated_dfs_per_file = calculate(dataframes_per_file, group_by=group_column, metrics=self.model_metrics,
                                            drop_columns=['Run'])

        meta_file_prefix = get_data_from_config('file_prefix', path=self.config_path)
        meta_file_names = ['_'.join([meta_file_prefix, name]) for name in dataframes_per_file.keys()]

        # generate result csv files
        nan_repr = get_data_from_config('nan_representation', path=self.config_path)
        is_generated = dataframes_to_csv(result_path, calculated_dfs_per_file, meta_file_names, nan_repr)

        if generate_plots:
            # generate bar plots
            bar_plot_per_file = dict()
            for file_name in meta_file_names:
                title = file_name.split('.')[0]
                output_file_name = '_'.join(['bar', title])

                plot = self.generate_bar_plot(calculated_dfs_per_file[file_name.replace("meta_", "")], output_file_name,
                                              title)
                bar_plot_per_file[file_name] = plot

            # generate violin plots
            for file_name, dataframe in dataframes_per_file.items():
                title = file_name.split('.')[0]
                output_file_name = '_'.join(['violin', title])

                # sort violin chart corresponding to bar plot
                meta_file_name = '_'.join([meta_file_prefix, file_name])
                sorted_classes = [trace.name for trace in bar_plot_per_file[meta_file_name].figure.data]

                self.generate_violin_plot(dataframe, output_file_name, title, sorted_classes, drop_columns=['Run'])

            # generate table plots
            # calculated dataframes usable for meta columns
            dataframes_per_file_for_tables = get_dataframes_per_file_for_table_plot(dataframes_per_file,
                                                                                    calculated_dfs_per_file)
            for file_name, dataframe in dataframes_per_file_for_tables.items():
                file_name = file_name.split('.')[0]
                output_file_name = '_'.join(['table', file_name])

                self.generate_table_plot(dataframe, output_file_name, title=file_name)

        return is_generated

    def generate_per_session(self):
        """ generates the meta report from all models in the session """
        self.generate_collection_of_session()

        model_paths = get_sub_directories(self.path)
        for model in model_paths:
            self.generate_per_model(model, generate_plots=False)

        meta_files_per_model = get_meta_files_per_model(model_paths, self.config_path)

        dfs_of_meta_file_per_model = generate_dataframe_of_file_per_model(model_paths, meta_files_per_model,
                                                                          self.drop_rows,
                                                                          self.config_path)

        meta_file_prefix = get_data_from_config('file_prefix', path=self.config_path)
        result_file_name = '_'.join([meta_file_prefix, '.'.join([os.path.basename(self.path), 'csv'])])
        result_file_path = generate_file_path(self.result_path, result_file_name)

        nan_rep = get_data_from_config('nan_representation', path=self.config_path)
        duplicated_entry_identifiers = get_data_from_config("duplicates_identifier", path=self.config_path)
        run_pattern = get_pattern('run_directory', path=self.config_path)
        multiple_entries_in = get_data_from_config("multiple_entries_in", path=self.config_path)

        # get the nodes from the config file and transform them into a list
        nodes = get_data_from_config("config_data", path=self.config_path)
        node_list = nodes_to_list(nodes)

        # config_files_per_model = {model_path: [config_file_paths]}
        config_files_per_model = get_model_config_files_per_model(model_paths, self.config_path)

        is_generated = True
        for model_path, df_per_file_name in dfs_of_meta_file_per_model.items():
            number_of_runs = get_number_of_runs(model_path, run_pattern)

            data = {'model': os.path.basename(model_path), 'runs': number_of_runs}
            config_data = get_model_config_data(config_files_per_model[model_path], node_list, multiple_entries_in)
            data.update(config_data)

            model_data = generate_summary_dataframe_of_model(df_per_file_name, self.config_path, self.session_metrics,
                                                             data)

            is_generated = is_generated and write_session_meta_result(model_data, result_file_path, nan_rep,
                                                                      duplicated_entry_identifiers)

        return is_generated

    def generate_bar_plot(self, dataframe, output_file_name, title):
        column_identifiers = get_data_from_config('bar_plot_columns', path=self.config_path)

        plot = BarPlotter(dataframe=dataframe, result_path=self.result_path, file_name=output_file_name, title=title,
                          column_identifiers=column_identifiers)
        plot.save_as(self.plot_format)
        return plot

    def generate_violin_plot(self, dataframe, output_file_name, title, order, drop_columns=[]):
        df = dataframe.reset_index(drop=False)
        df = df[[column for column in df.columns if column not in drop_columns]]
        plot = ViolinPlotter(df, self.result_path, output_file_name, title)

        # sort traces with bar order
        ordered_traces = []
        for clazz in order:
            for violin in plot.figure.data:
                if violin.name == clazz:
                    ordered_traces.append(violin)

        plot.figure.data = ordered_traces
        plot.save_as(self.plot_format)

    def generate_table_plot(self, dataframe, output_file_name, title):
        df = dataframe.reset_index(drop=False, inplace=False)
        plot = TablePlotter(dataframe=df, result_path=self.result_path,
                            file_name=output_file_name, title=title)
        plot.save_as(self.plot_format)
        return plot

    def generate_collection_of_session(self):
        """Generates a file containing each value of the run per model"""

        # get dict of the form {model_path: {run: [files]}}
        model_paths = get_sub_directories(self.path)
        run_pattern = get_pattern('run_directory', path=self.config_path)
        files_of_run_per_model = {model: dict() for model in model_paths}
        file_patterns = get_patterns_to_look_for(self.config_path)
        for model in model_paths:
            sub_directories = get_sub_directories(model)
            for sub_directory in sub_directories:
                sub_directory_name = get_base_name(sub_directory)
                if check_name(sub_directory_name, run_pattern):
                    files = find_files_per_pattern(sub_directory, file_patterns)
                    files_of_run_per_model[model][sub_directory_name] = files

        data = dict()

        for model_path, files_per_run in files_of_run_per_model.items():
            model_name = get_base_name(model_path)

            # fill data dict from dataframes
            for run, files in files_per_run.items():
                path_name = '_'.join([model_name, run])
                data[path_name] = dict()
                for file in files:
                    dataframe = pd.read_csv(file)
                    dataframe.set_index(list(dataframe.columns)[0], inplace=True)

                    set_name = get_set_name(get_base_name(file), self.config_path, pattern='set')
                    if set_name is None:
                        continue

                    for column in dataframe.columns:
                        for clazz in dataframe.index:
                            column_name = '_'.join([set_name, column, clazz])
                            data[path_name].update({column_name: dataframe.loc[clazz, column]})

        df = pd.DataFrame(data)
        df = df.T

        df.index.set_names(get_data_from_config("collected_data_index_name", path=self.config_path), inplace=True)

        path = generate_file_path(self.result_path, get_data_from_config("collection_file_name", path=self.config_path))
        df.to_csv(path)
        return True
