from icecream import ic

from .utils.utils_files import find_files_per_pattern, remove_redundant_files, get_files_per_name
from .utils.utils_pandas import generate_dataframes, write_result
from .utils.utils_config import get_data_from_config, get_pattern, get_patterns_to_look_for

ic.configureOutput(includeContext=True)


class MetaReporter:
    """ class for generating meta report files """

    def __init__(self, model_path, result_path, config_path=None, metrics=None, drop_rows=None):
        self.model_path = model_path
        self.result_path = result_path
        self.config_path = config_path

        if metrics is not None:
            self.metrics = metrics
        else:
            self.metrics = get_data_from_config('metrics', path=self.config_path)

        if drop_rows is not None:
            self.drop_rows = drop_rows
        else:
            self.drop_rows = get_data_from_config('drop', path=self.config_path)

    def __str__(self):
        return "MetaReporter(model_path: {} | result_path: {} | metrics: {} | drop: {})".format(self.model_path,
                                                                                                self.result_path,
                                                                                                self.metrics,
                                                                                                self.drop_rows)

    def generate(self):
        """ generates the meta report files """
        # get run pattern
        run_pattern = get_pattern('run', self.config_path)

        # get files
        file_patterns = get_patterns_to_look_for(self.config_path)
        files = find_files_per_pattern(self.model_path, file_patterns)
        files = remove_redundant_files(files, run_pattern, self.model_path)

        paths_of_file = get_files_per_name(files)

        # generate dataframes per filename (concatenated)
        group_column = get_data_from_config("class_column_name", path=self.config_path)
        datasets = generate_dataframes(paths_of_file, group_column, self.drop_rows)

        calculated_dataframes = self.calculate(datasets, group_by=group_column)

        meta_file_prefix = get_data_from_config('file_prefix', path=self.config_path)
        meta_file_names = ['_'.join([meta_file_prefix, name]) for name in paths_of_file.keys()]

        files_written = write_result(self.result_path,
                                     calculated_dataframes,
                                     meta_file_names,
                                     get_data_from_config('nan_representation', path=self.config_path))

        return files_written

    def calculate(self, dataframes, group_by):
        calculated = []
        for df in dataframes:
            grouped_file_data = df.groupby(group_by, group_keys=False, as_index=True, sort=False)
            # calculate stats
            aggregated = grouped_file_data.agg(self.metrics)

            # set column names
            aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns]

            calculated.append(aggregated)

        return calculated
