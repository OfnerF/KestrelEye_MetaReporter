import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from .Plotter import Plotter
from ..utils.utils_visualization import get_color_map


class ViolinPlotter(Plotter):
    """Class for generating violin plots"""

    def __init__(self, dataframe, result_path, file_name, title):
        super().__init__(dataframe, result_path, file_name, title)

    def generate(self):
        columns = list(self.dataframe.columns)

        # remove Class column
        for column in ['Class']:
            columns.remove(column)

        # create figure as subplots
        fig = make_subplots(
            rows=len(columns),
            cols=1,
            shared_xaxes=False,
            subplot_titles=columns,
        )

        # colors for traces
        colors = px.colors.qualitative.Plotly

        # map color to class
        color_map = get_color_map(colors, self.dataframe['Class'])

        for column_idx, column in enumerate(columns):
            for clazz in self.dataframe['Class']:

                fig.add_trace(
                    go.Violin(
                        x=self.dataframe['Class'][self.dataframe['Class'] == clazz],
                        y=self.dataframe[column][self.dataframe['Class'] == clazz],
                        name=clazz,
                        marker={'color': color_map[clazz],
                                'symbol': 'x',
                                'opacity': 0.3},
                        points='all',
                        spanmode='soft'
                    ),
                    row=column_idx + 1,
                    col=1
                )

        # layout of all traces
        fig.update_traces(box_visible=False, showlegend=True, meanline_visible=True)

        # hide duplicate labels
        names = set()
        fig.for_each_trace(
            lambda trace:
            trace.update(showlegend=False) if (trace.name in names) else names.add(trace.name))

        # set specific layout
        fig.update_layout(
            showlegend=False,
            height=len(columns) * 200
        )

        return fig
