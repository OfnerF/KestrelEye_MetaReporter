from .utils.utils_files import find_files_per_pattern, remove_files_not_in_runs, get_files_per_name, get_model_paths, \
    remove_children
from .utils.utils_pandas import generate_dataframes, write_result, calculate
from .utils.utils_config import get_data_from_config, get_pattern, get_patterns_to_look_for


class MetaReporter:
    """ class for generating meta report files """

    def __init__(self, path, result_path, config_path=None, metrics=None, drop_rows=None, level=1):
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
        """ generates the meta report for each model in the session """
        if model_path is None:
            model_path = self.path
            result_path = self.result_path
        else:
            result_path = model_path
        # get run pattern
        run_pattern = get_pattern('run', self.config_path)

        # get files
        file_patterns = get_patterns_to_look_for(self.config_path)
        files = find_files_per_pattern(model_path, file_patterns)
        files = remove_files_not_in_runs(files, run_pattern, model_path)

        paths_of_file = get_files_per_name(files)

        # generate dataframes per filename (concatenated)
        group_column = get_data_from_config("class_column_name", path=self.config_path)
        datasets = generate_dataframes(paths_of_file, group_column, self.drop_rows)

        calculated_dataframes = calculate(datasets, group_by=group_column, metrics=self.model_metrics)

        meta_file_prefix = get_data_from_config('file_prefix', path=self.config_path)
        meta_file_names = ['_'.join([meta_file_prefix, name]) for name in paths_of_file.keys()]

        is_generated = write_result(result_path,
                                    calculated_dataframes,
                                    meta_file_names,
                                    get_data_from_config('nan_representation', path=self.config_path))

        return is_generated

    def generate_per_session(self):
        """ generates the meta report from all models in the session """
        # get meta files pattern
        meta_pattern = get_pattern('meta', path=self.config_path)

        # get files
        for model in get_model_paths(self.path):
            self.generate_per_model(model)
        files = find_files_per_pattern(self.path, [meta_pattern])

        files = remove_children(self.path, files)
        files_per_name = get_files_per_name(files)

        # generate dataframes
        group_column = get_data_from_config("class_column_name", path=self.config_path)

        dataframes = generate_dataframes(files_per_name, group_column, self.drop_rows)
        # calculate
        calculated_dataframes = calculate(dataframes, group_column, metrics=self.session_metrics)

        # write files
        is_generated = write_result(self.result_path,
                                    calculated_dataframes,
                                    files_per_name.keys(),
                                    get_data_from_config('nan_representation', path=self.config_path))

        return is_generated
