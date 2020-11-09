"""A collection of models for producing plots using the plotly library.

Notes
-----
* The fields of the models in this module may not follow the standard PEP8 guidelines.
  Instead, field names are chosen to match the JSON input consumed by plotly.
"""
import abc
import json
from io import StringIO
from typing import TYPE_CHECKING, List, Optional, Union

import numpy
from pydantic import BaseModel, Field, root_validator
from typing_extensions import Literal

if TYPE_CHECKING:
    from plotly.graph_objs import Figure as PlotlyFigure


SymbolType = Literal[
    "circle",
    "circle-open",
    "x",
    "diamond",
    "cross",
    "square",
    "star-diamond",
    "triangle-up",
    "star-square",
    "triangle-down",
    "pentagon",
    "hexagon",
]


class ErrorBar(BaseModel):
    """Stores information about the error bars on each data point in a series."""

    type: Literal["data"] = Field("data")

    symmetric: bool = Field(
        ..., description="Whether the error bars are symmetric around the data points."
    )

    array: List[Optional[float]] = Field(
        ...,
        description="The array of error bar values if `symmetric` is, otherwise an "
        "array of the plus error bar values (i.e. those added to the series values).",
    )
    arrayminus: Optional[List[Optional[float]]] = Field(
        ...,
        description="The array of the minus error bar values (i.e. those subtracted "
        "from the series values). This must be set if `symmetric` is true.",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        symmetric = values.get("symmetric")
        array_minus = values.get("arrayminus")

        assert (symmetric and array_minus is None) or (
            not symmetric and array_minus is not None
        )

        return values


class BaseStyle(BaseModel, abc.ABC):
    """A base class for plotly styles."""

    color: str = Field(..., description="The color of the marker.")


class LineStyle(BaseStyle):
    """Stores properties about markers on a plot."""


class MarkerStyle(BaseStyle):
    """Stores properties about markers on a plot."""

    symbol: SymbolType = Field(
        "circle", description="The symbol to use for the marker."
    )


class Trace(BaseModel, abc.ABC):
    """The base class for plotted data traces."""

    name: str = Field(..., description="The name of the trace.")

    x: List[Union[float, str]] = Field(..., description="The x-values of the data.")
    y: List[float] = Field(..., description="The y-values of the data.")

    error_x: Optional[ErrorBar] = Field(
        None, description="The x-error bars associated with the data."
    )
    error_y: Optional[ErrorBar] = Field(
        None, description="The y-error bars associated with the data."
    )

    marker: Optional[MarkerStyle] = Field(None, description="The marker style.")
    # line: Optional[LineStyle] = Field(None, description="The line style.")

    legendgroup: str = Field(
        ..., description="The group which this trace belongs to in the legend."
    )
    showlegend: bool = Field(..., description="Whether to display the legend.")

    hoverinfo: Optional[Literal["text", "name", "all", "none", "skip"]] = Field(
        None,
        description="The trace information to show when hovering over a data point.",
    )


class BarTrace(Trace):
    """Stores information about data to display as a bar chart."""

    type: Literal["bar"] = Field(
        "bar", description="The type of chart the data will be displayed on."
    )


class ScatterTrace(Trace):
    """Stores information about data to display as a scatter chart.

    Notes
    -----
    * Scatter traces can also be used to produce line plots by setting the mode
      to `lines`, `lines+markers` or `lines+markers+text`.
    """

    type: Literal["scatter"] = Field(
        "scatter", description="The type of chart the data will be displayed on."
    )
    mode: Literal["lines", "markers", "lines+markers", "lines+markers+text"] = Field(
        "markers", description="The scatter display mode."
    )


class Subplot(BaseModel):
    """Store information about a subplot, including the traces to plot and the titles
    to include.

    Notes
    -----
    * This model does not conform to any plotly schemas. Rather, it provides enough
      information to populate the `layout` section of a figures schema.
    """

    title: Optional[str] = Field(None, description="The title for this sub-plot.")

    x_axis_label: Optional[str] = Field(None, description="The x-axis label.")
    y_axis_label: Optional[str] = Field(None, description="The y-axis label.")

    show_x_ticks: bool = Field(
        True, description="Whether to show the x ticks and labels."
    )
    show_y_ticks: bool = Field(
        True, description="Whether to show the y ticks and labels."
    )

    traces: List[Union[BarTrace, ScatterTrace]] = Field(
        [], description="The traces to include in the subplot."
    )


class Legend(BaseModel):
    """Stores settings about a figures legend."""

    orientation: Literal["h", "v"] = Field(
        "h",
        description="Whether the legend should be placed to the right of (v) or below "
        "(h) the figure.",
    )


class Figure(BaseModel):
    """A collection of subplots to draw in the same figure."""

    subplots: List[Subplot] = Field(
        ..., description="The subplots to include in a figure."
    )
    legend: Optional[Legend] = Field(
        ..., description="Settings for the figures legend."
    )

    shared_axes: bool = Field(
        False,
        description="Whether all axes (both x and y) should have the same limits.",
    )

    def _generate_layout(
        self,
        subplot_width: float = 350.0,
        subplot_height: float = 350.0,
        subplots_per_row: Optional[int] = None,
    ):
        """Generate the layout spec for a plotly figure.

        Parameters
        ----------
        subplot_width
            The width of each subplot.
        subplot_height
            The height of each subplot.
        subplots_per_row
            The maximum subplots per row. If none, all subplots will be drawn on a
            single row.

        Notes
        -----
        * This function is mainly available only for debug purposes.
        """
        n_subplots = len(self.subplots)

        if subplots_per_row is None:
            subplots_per_row = n_subplots

        n_cols = int(max(1, min(subplots_per_row, n_subplots)))
        n_rows = int(max(1, numpy.ceil(n_subplots / n_cols)))

        # Define any plot sub-titles.
        annotations = [
            {
                "font": {"size": 16},
                "showarrow": False,
                "text": subplot.title,
                "x": 0.5,
                "xanchor": "center",
                "xref": f"x{i + 1} domain" if i > 0 else "x domain",
                "y": 1.05,
                "yanchor": "bottom",
                "yref": f"y{i + 1} domain" if i > 0 else "y domain",
            }
            for i, subplot in enumerate(self.subplots)
            if subplot.title is not None
        ]

        # Define any x-axis titles.
        x_axes = {
            f"xaxis{i + 1}": {
                "title": subplot.x_axis_label,
                "showticklabels": subplot.show_x_ticks,
            }
            for i, subplot in enumerate(self.subplots)
        }

        # Define any y-axis titles.
        y_axes = {
            f"yaxis{i + 1}": {
                "title": subplot.y_axis_label if (i % n_cols) == 0 else None,
                "showticklabels": subplot.show_y_ticks,
            }
            for i, subplot in enumerate(self.subplots)
        }

        if self.shared_axes:

            for x_axis in x_axes.values():
                x_axis["matches"] = "x1"
            for y_axis in y_axes.values():
                y_axis["matches"] = "x1"

        return {
            # Client set.
            "grid": {"rows": n_rows, "columns": n_cols, "pattern": "independent"},
            "legend": None
            if self.legend is None
            else {"orientation": self.legend.orientation},
            "width": subplot_width * n_cols,
            "height": subplot_height * n_rows,
            "annotations": annotations,
            "margin": {
                "t": 50,
                "b": 50,
            },
            # Server set.
            **x_axes,
            **y_axes,
        }

    def to_plotly(
        self,
        subplot_width: float = 350.0,
        subplot_height: float = 350.0,
        subplots_per_row: Optional[int] = None,
    ) -> "PlotlyFigure":
        """Converts the pydantic representation of a plotly figure to an actual
        plotly figure object.

        Parameters
        ----------
        subplot_width
            The width of each subplot.
        subplot_height
            The height of each subplot.
        subplots_per_row
            The maximum subplots per row. If none, all subplots will be drawn on a
            single row.

        Notes
        -----
        * This function is mainly available only for debug purposes.
        """
        from plotly.io import read_json

        # Build up the rest of the JSON dictionary.
        figure_dictionary = {
            "data": [
                {**trace.dict(), "xaxis": f"x{i + 1}", "yaxis": f"y{i + 1}"}
                for i, subplot in enumerate(self.subplots)
                for trace in subplot.traces
            ],
            "layout": self._generate_layout(
                subplot_width, subplot_height, subplots_per_row
            ),
            "config": {"displayModeBar": False},
        }

        figure = read_json(StringIO(json.dumps(figure_dictionary)))
        return figure
