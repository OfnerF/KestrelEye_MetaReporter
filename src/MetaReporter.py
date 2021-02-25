import os
from functools import reduce
import pandas as pd

from .utils import nodes_to_list
from .utils.utils_config import get_data_from_config, get_pattern, get_patterns_to_look_for, get_model_config_data
from .utils.utils_files import find_files_per_pattern, remove_files_not_in_runs, get_files_per_name, \
    get_sub_directories, get_files_per_model, get_model_config_files_per_model, get_number_of_runs, \
    generate_file_path, get_run_of_file
from .utils.utils_pandas import generate_dataframe_per_file_name, dataframes_to_csv, calculate, generate_dataframes_per_model, \
    write_session_meta_result, generate_dataframe_of_model, generate_dataframes_with_run
from .visualization.BarPlotter import BarPlotter
from .visualization.ViolinPlotter import ViolinPlotter
from .visualization.TablePlotter import TablePlotter

from . import ic


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

    def generate_per_model(self, model_path=None):
        """ generates the meta report for each model in the session with the same parameters"""
        if model_path is None:
            model_path = self.path
            result_path = self.result_path
        else:
            result_path = model_path

        # get run pattern
        run_pattern = get_pattern('run_directory', self.config_path)

        # get files
        file_patterns = get_patterns_to_look_for(self.config_path)
        files = find_files_per_pattern(model_path, file_patterns)
        files = remove_files_not_in_runs(files, run_pattern, model_path)

        # {filename: [paths]}
        paths_per_file = get_files_per_name(files)

        group_column = get_data_from_config("class_column_name", path=self.config_path)
        # {filename: dataframe(containing each file)}
        dataframes_per_file = generate_dataframe_per_file_name(paths_per_file, group_column, self.drop_rows)

        # calculate metrics
        # {filename: dataframe}
        calculated_dfs_per_file = calculate(dataframes_per_file, group_by=group_column, metrics=self.model_metrics)

        meta_file_prefix = get_data_from_config('file_prefix', path=self.config_path)
        meta_file_names = ['_'.join([meta_file_prefix, name]) for name in paths_per_file.keys()]

        # generate result csv files
        nan_repr = get_data_from_config('nan_representation', path=self.config_path)
        is_generated = dataframes_to_csv(result_path, calculated_dfs_per_file, meta_file_names, nan_repr)

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
            dataframe.reset_index(drop=False, inplace=True)
            self.generate_violin_plot(dataframe, output_file_name, title, sorted_classes)


        # calculated dataframes usable for meta columns
        # add run to dataframes per file
        paths_per_run_of_file = {name: dict() for name in paths_per_file.keys()}
        for file_name, file_paths in paths_per_file.items():
            for path in file_paths:
                run = get_run_of_file(path, run_pattern, self.path)
                paths_per_run_of_file[file_name].update({run: path})

        dataframes_per_file_with_run = generate_dataframes_with_run(paths_per_run_of_file, group_column, self.drop_rows)

        dataframes_per_file_run_added = {file_name: None for file_name in dataframes_per_file_with_run.keys()}
        for file_name, dataframe in dataframes_per_file_with_run.items():
            df_groups = dataframe.groupby('Run')
            # prepare dataframe
            dfs = []
            for name, group in df_groups:
                tmp = group.copy()
                tmp.drop('Run', axis='columns', inplace=True)
                tmp.columns = ['_'.join([col, str(name)]) if col != 'Class' else 'Class' for col in tmp.columns]
                dfs.append(tmp)

            # merge prepared dataframes
            df_run_test_testresult = reduce(lambda df1, df2: pd.merge(df1, df2, on='Class'), dfs)
            dataframes_per_file_run_added[file_name] = df_run_test_testresult
        #####################################

        for file_name, dataframe in dataframes_per_file_run_added.items():
            dataframes_per_file_run_added[file_name] = pd.concat([dataframe, calculated_dfs_per_file[file_name]],
                                                                 axis='columns')

        for file_name, dataframe in dataframes_per_file_run_added.items():
            file_name = file_name.split('.')[0]
            output_file_name = '_'.join(['table', file_name])
            dataframe.reset_index(drop=False, inplace=True)
            self.generate_table_plot(dataframe, output_file_name, title=file_name)

        return is_generated

    def generate_per_session(self):
        """ generates the meta report from all models in the session """

        model_paths = get_sub_directories(self.path)

        # files_per_model = {model_path: {file_name: file_paths}}
        files_per_model = get_files_per_model(self.path, model_paths, self.config_path)

        # dataframe_of_models = {model_path: {file_name: dataframe}}
        dataframes_of_models = generate_dataframes_per_model(model_paths, files_per_model, self.session_metrics,
                                                             self.drop_rows, self.config_path)

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
        for model_path, dataframes in dataframes_of_models.items():
            number_of_runs = get_number_of_runs(model_path, run_pattern)

            data = {'model': os.path.basename(model_path), 'runs': number_of_runs}
            config_data = get_model_config_data(config_files_per_model[model_path], node_list, multiple_entries_in)
            data.update(config_data)

            model_data = generate_dataframe_of_model(dataframes, self.config_path, self.session_metrics, data)
            is_generated = is_generated and write_session_meta_result(model_data, result_file_path, nan_rep,
                                                                      duplicated_entry_identifiers)

        return is_generated

    def generate_bar_plot(self, dataframe, output_file_name, title):
        plot = BarPlotter(dataframe=dataframe, result_path=self.result_path, file_name=output_file_name, title=title)
        plot.save_as(self.plot_format)
        return plot

    def generate_violin_plot(self, dataframe, output_file_name, title, order):
        plot = ViolinPlotter(dataframe, self.result_path, output_file_name, title)

        # sort traces with bar order
        ordered_traces = []
        for clazz in order:
            for violin in plot.figure.data:
                if violin.name == clazz:
                    ordered_traces.append(violin)

        plot.figure.data = ordered_traces
        plot.save_as(self.plot_format)

    def generate_table_plot(self, dataframe, output_file_name, title):
        plot = TablePlotter(dataframe=dataframe, result_path=self.result_path, file_name=output_file_name, title=title)
        plot.save_as(self.plot_format)
        return plot
