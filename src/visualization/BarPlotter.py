import plotly.graph_objs as go
import plotly.express as px
from .Plotter import Plotter


class BarPlotter(Plotter):
    """Class for generating bar plots"""
    def __init__(self, dataframe, result_path, file_name, title):
        super().__init__(dataframe, result_path, file_name, title)

    def generate(self):
        columns = [col for col in self.dataframe.columns if 'max' in col]
        colors = px.colors.qualitative.Plotly
        traces = []
        color_map = {}

        for idx, cl in enumerate(self.dataframe.index):
            # fill color map
            if cl not in color_map:
                color_map[cl] = colors[idx % len(colors)]
            # get data
            y = self.dataframe.loc[cl, columns]

            # append new trace to figure
            traces.append(
                go.Bar(
                    name=cl,
                    x=columns,
                    y=y,
                    hovertemplate='%{y:.4f}',
                    marker=dict(color=color_map[cl])
                )
            )

        # sort traces
        sort_by = columns[0]
        sorted_traces = sorted(traces, key=lambda item: item.y[item.x.index(sort_by)], reverse=True)

        # create figure
        fig = go.Figure(data=sorted_traces)

        # set specific layout
        fig.update_layout(
            barmode="group"
        )

        return fig
