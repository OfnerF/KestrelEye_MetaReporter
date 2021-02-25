import pandas as pd
from colour import Color
import plotly.graph_objs as go

from .Plotter import Plotter
from ..utils.utils_pandas import get_interval_index


class TablePlotter(Plotter):
    """Class for generating tables"""
    def __init__(self, dataframe, result_path, file_name, title):
        self.precision = 6
        super().__init__(dataframe, result_path, file_name, title)

    def generate(self):
        columns = list(self.dataframe.columns)
        # put std to the end
        columns.sort(key=lambda x: 'std' in x)
        self.dataframe = self.dataframe[columns]

        # create intervals for coloring
        # ---- interval 1 for all but std
        closed_on = 'right'
        lower_bound = 0.3
        upper_bound = 0.9
        mid_periods = 15

        intervals1 = pd.IntervalIndex.from_breaks([0, lower_bound], closed=closed_on)
        intervals2 = pd.interval_range(lower_bound, upper_bound, periods=mid_periods, closed=closed_on)
        intervals3 = pd.IntervalIndex.from_breaks([upper_bound, 1], closed=closed_on)

        interval_list_1 = intervals1.append([intervals2, intervals3])

        # ---- interval 2 for std
        closed_on = 'right'
        lower_bound = 0.05
        upper_bound = 0.1
        mid_periods = 15

        intervals1 = pd.IntervalIndex.from_breaks([0, lower_bound], closed=closed_on)
        intervals2 = pd.interval_range(lower_bound, upper_bound, periods=mid_periods, closed=closed_on)
        intervals3 = pd.IntervalIndex.from_breaks([upper_bound, 1], closed=closed_on)

        interval_list_2 = intervals1.append([intervals2, intervals3])

        # interval matrix, exclude first column (Class)
        interval_dataframe = self.dataframe.iloc[:, 1:]
        for column in self.dataframe.select_dtypes(exclude=['object']):
            if 'std' in column:
                interval_list = interval_list_2
            else:
                interval_list = interval_list_1

            interval_dataframe[column] = self.dataframe[column].map(
                lambda value: get_interval_index(interval_list, value))

        # colors
        color_low = Color('#e60000')  # red
        color_lower_bound = Color('#ffa31a')  # orange
        color_upper_bound = Color('#248f24')  # green
        color_mid = Color('#ffcc00')  # yellow
        color_high = Color('#006622')  # dark green

        colors = list(color_lower_bound.range_to(color_mid, (mid_periods // 2) if mid_periods % 2 == 0 else (
                mid_periods // 2 + 1)))
        colors.extend(
            list(color_mid.range_to(color_upper_bound, mid_periods // 2 + 1)))  # +1 because first one has to be deleted

        # get unique hex values of colors
        unique_colors = []
        for color in colors:
            if color.hex in unique_colors:
                continue
            else:
                unique_colors.append(color.hex)

        colors = [color_low.hex]
        colors.extend(unique_colors)
        colors.append(color_high.hex)

        # fill color matrix
        color_matrix = [['#808080' for _ in range(len(interval_dataframe))]]  # Class column, gray

        # reversed colors for low=good and high=bad
        colors_reversed = colors.copy()
        colors_reversed.reverse()

        # fill color matrix
        for column in interval_dataframe.columns:
            colors = colors_reversed if 'std' in column else colors
            color_matrix.append([colors[value] for value in interval_dataframe[column]])

        # round values, except first column (Class)
        values = self.dataframe
        values.iloc[:, 1:] = values.iloc[:, 1:].applymap(lambda x: round(x, self.precision))

        # create figure
        fig = go.Figure(
            data=[go.Table(
                header=dict(
                    values=values.columns,
                    line_color='white', fill_color='white',
                    align='center', font=dict(color='black', size=9)
                ),

                cells=dict(
                    values=values.T,
                    fill_color=color_matrix,
                    line_color=color_matrix,
                    align='center', font=dict(color='white', size=8)
                )
            )]
        )

        # set layout
        fig.update_layout(
            width=len(self.dataframe.columns) * 100
        )

        return fig
