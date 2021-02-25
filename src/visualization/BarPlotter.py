import plotly.graph_objs as go
import plotly.express as px
from .Plotter import Plotter


class BarPlotter(Plotter):
    """Class for generating bar plots"""

    def __init__(self, dataframe, result_path, file_name, title):
        super().__init__(dataframe, result_path, file_name, title)

    def generate(self):
        # get max columns
        columns = [column for column in self.dataframe.columns if 'max' in column]

        colors = px.colors.qualitative.Plotly
        traces = []
        color_map = {}

        for idx, clazz in enumerate(self.dataframe.index):
            # fill color map
            if clazz not in color_map:
                color_map[clazz] = colors[idx % len(colors)]

            # get data
            y = self.dataframe.loc[clazz, columns]

            # append new trace
            traces.append(
                go.Bar(
                    name=clazz,
                    x=columns,
                    y=y,
                    hovertemplate='%{y:.4f}',
                    marker=dict(color=color_map[clazz])
                )
            )

        # sort all traces by first column
        sort_by = columns[0]
        sorted_traces = sorted(traces, key=lambda trace: trace.y[trace.x.index(sort_by)], reverse=True)

        # create figure
        fig = go.Figure(data=sorted_traces)

        # set specific layout
        fig.update_layout(
            barmode="group"
        )

        return fig
