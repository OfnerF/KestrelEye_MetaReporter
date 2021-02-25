from abc import ABC, abstractmethod
from ..utils.utils_files import generate_file_path


class Plotter(ABC):
    def __init__(self, dataframe, result_path, file_name, title):
        self.dataframe = dataframe
        self.result_path = result_path
        self.file_name = file_name
        self.title = title
        self.figure = self.generate()

        # set layout for all plotters
        self.figure.update_layout(
            title=self.title
        )

    @abstractmethod
    def generate(self):
        """Generates and returns the plot."""
        pass

    def save_as(self, file_format):
        """Saves the plot in the given format."""
        if file_format == 'html':
            """html files are interactive"""
            self.figure.write_html(file=generate_file_path(self.result_path, '.'.join([self.file_name, "html"])))
        elif file_format in ['pdf', 'svg', 'png', 'jpg', 'jpeg']:
            self.figure.write_image(
                file=generate_file_path(self.result_path, '.'.join([self.file_name, file_format])))
        else:
            raise ValueError(f"'{file_format}' is not specified as file format.")
