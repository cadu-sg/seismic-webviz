import numpy.typing as npt
from bokeh.models import ColumnDataSource, GlyphRenderer, Model, Image, Switch
import numpy as np
from bokeh.plotting import figure
from time import perf_counter


MAX_TRACES_LINE_HAREA = 100


class SeismicVisualization:

    line_switch: Switch | None = None
    harea_switch: Switch | None = None

    def __init__(
        self,
        data: npt.NDArray,
        x_positions: npt.NDArray | None,
        interval_time_samples: float,
        time_unit="s",
        stretch_factor=0.15,
        color="black",
    ):
        init_start = perf_counter()
        # Input checks
        # ------------

        # Input check for stretch_factor
        if not isinstance(stretch_factor, (int, float)):
            raise TypeError("stretch_factor must be a number")

        # Input check for data
        if type(data).__module__ != np.__name__:
            raise TypeError("data must be a numpy array")
        if len(data.shape) != 2:
            raise ValueError("data must be a 2D array")

        num_time_samples = data.shape[0]
        num_traces = data.shape[1]
        print("num_traces:", num_traces)

        # Input check for x_positions
        if x_positions is None:
            x_positions = np.arange(start=1, stop=num_traces + 1)
        else:
            if type(x_positions).__module__ != np.__name__:
                raise TypeError("x_positions must be a numpy array")
            if len(x_positions.shape) != 1:
                raise ValueError("x_positions must be a 1D array")
            if x_positions.size != num_traces:
                raise ValueError(
                    "The size of x_positions must be equal to the number of "
                    "columns in data, that is, it must be equal to the number "
                    "of traces"
                )

        # Create and set up figure object
        # -------------------------------
        self.plot: figure = figure(
            x_axis_location="above",
            height=800,
            width=1000,
            sizing_mode="stretch_both",
        )

        # Adjust ranges
        self.plot.x_range.range_padding = 0.0
        self.plot.y_range.range_padding = 0.0
        self.plot.y_range.flipped = True

        # Adjust axes
        self.plot.xaxis.axis_label = "Offset (m)"
        if time_unit == "s":
            self.plot.yaxis.axis_label = "Time (s)"
        elif time_unit == "ms":
            self.plot.yaxis.axis_label = "Time (ms)"

        # Create ColumnDataSource objects and add renderers
        # -------------------------------------------------

        # Time sample instants (auxiliary data for all)
        first_time_sample = 0.0
        last_time_sample = first_time_sample + (num_time_samples - 1) * interval_time_samples
        time_sample_instants = np.linspace(
            start=first_time_sample, stop=last_time_sample, num=num_time_samples
        )

        # Create image source
        self.image_source = ColumnDataSource(data={"image": [data]})

        # Auxiliary data for image renderer parameters
        width_x_positions = np.abs(x_positions[0] - x_positions[-1])
        width_time_sample_instants = np.abs(time_sample_instants[0] - time_sample_instants[-1])
        distance_first_x_positions = x_positions[1] - x_positions[0]
        distance_last_x_positions = x_positions[-1] - x_positions[-2]

        # Add image renderer
        self.image_gl: GlyphRenderer = self.plot.image(
            image="image",
            source=self.image_source,
            x=x_positions[0] - distance_first_x_positions / 2,
            y=first_time_sample,
            dw=width_x_positions + (distance_first_x_positions + distance_last_x_positions) / 2,
            dh=width_time_sample_instants,
            palette="Greys256",
            anchor="bottom_left",
            origin="bottom_left",
        )

        # Amplitudes zeros
        amplitudes_zeros = np.zeros(shape=(num_time_samples,))

        # Minimum trace horizontal spacing
        trace_x_spacing = np.min(np.diff(x_positions))

        # Rescale data by trace_x_spacing and stretch_factor
        data_max_std = np.max(np.std(data, axis=0))
        data_rescaled = data / data_max_std * trace_x_spacing * stretch_factor

        xs_list = []
        ys_list = []
        self.harea_gl_list: list[GlyphRenderer] = []

        for trace_index in range(num_traces):
            x_position = x_positions[trace_index]
            amplitudes = data_rescaled[:, trace_index]

            # fill positive amplitudes
            amplitudes_positive = np.clip(amplitudes, a_min=0, a_max=None)
            # Call harea glyph renderer
            # self.harea_gl_list.append(

            # Add harea glyph renderer
            if num_traces <= MAX_TRACES_LINE_HAREA:
                self.plot.harea(
                    x1=amplitudes_zeros + x_position,
                    x2=amplitudes_positive + x_position,
                    y=time_sample_instants,
                    color="black",
                    name="H",
                )

            # construct CDS for multi_line render
            xs_list.append(amplitudes + x_position)
            ys_list.append(time_sample_instants)

        self.multi_line_source = ColumnDataSource(
            data={
                "xs": xs_list,
                "ys": ys_list,
            }
        )

        # Add multiline renderer
        self.multi_line_gl: GlyphRenderer = self.plot.multi_line(
            xs="xs",
            ys="ys",
            source=self.multi_line_source,
            color=color,
            visible=self.line_switch.active if self.line_switch else True,
        )

        self._set_up_renderers_on_trace_excess(num_traces)

        init_stop = perf_counter()
        print(f"\ninit time: {init_stop - init_start} seconds\n")

    def update_plot(
        self,
        data: npt.NDArray,
        x_positions: npt.NDArray | None,
        interval_time_samples: float,
        time_unit="s",
        stretch_factor=0.15,
        color="black",
    ):
        update_plot_start = perf_counter()
        # Input checks
        # ------------

        # Input check for stretch_factor
        if not isinstance(stretch_factor, (int, float)):
            raise TypeError("stretch_factor must be a number")

        # Input check for data
        if type(data).__module__ != np.__name__:
            raise TypeError("data must be a numpy array")
        if len(data.shape) != 2:
            raise ValueError("data must be a 2D array")

        num_time_samples = data.shape[0]
        num_traces = data.shape[1]
        print("num_traces:", num_traces)

        # Input check for x_positions
        if x_positions is None:
            x_positions = np.arange(start=1, stop=num_traces + 1)
        else:
            if type(x_positions).__module__ != np.__name__:
                raise TypeError("x_positions must be a numpy array")
            if len(x_positions.shape) != 1:
                raise ValueError("x_positions must be a 1D array")
            if x_positions.size != num_traces:
                raise ValueError(
                    "The size of x_positions must be equal to the number of "
                    "columns in data, that is, it must be equal to the number "
                    "of traces"
                )

        # Hold off all requests to repaint the plot
        self.plot.hold_render = True

        # Update ColumnDataSource objects for renderers
        # ---------------------------------------------
        self._remove_harea_renderers()

        # Time sample instants
        first_time_sample = 0.0
        last_time_sample = first_time_sample + (num_time_samples - 1) * interval_time_samples
        time_sample_instants = np.linspace(
            start=first_time_sample, stop=last_time_sample, num=num_time_samples
        )

        # Amplitudes zeros
        amplitudes_zeros = np.zeros(shape=(num_time_samples,))

        # Minimum trace horizontal spacing
        trace_x_spacing = np.min(np.diff(x_positions))

        # Rescale data by trace_x_spacing and stretch_factor
        data_max_std = np.max(np.std(data, axis=0))
        data_rescaled = data / data_max_std * trace_x_spacing * stretch_factor

        xs_list = []
        ys_list = []
        # self.harea_gl_list: list[GlyphRenderer] = []
        num_traces = data.shape[1]
        for trace_index in range(num_traces):
            x_position = x_positions[trace_index]
            amplitudes = data_rescaled[:, trace_index]

            # fill positive amplitudes
            amplitudes_positive = np.clip(amplitudes, a_min=0, a_max=None)

            # Add harea glyph renderer
            if num_traces <= MAX_TRACES_LINE_HAREA:
                self.plot.harea(
                    x1=amplitudes_zeros + x_position,
                    x2=amplitudes_positive + x_position,
                    y=time_sample_instants,
                    color="black",
                    name="H",
                )

            # construct CDS for line render
            xs_list.append(amplitudes + x_position)
            ys_list.append(time_sample_instants)

        # Update data sources
        # -------------------
        # image
        self.image_source.data = {"image": [data]}
        # multi_line
        self.multi_line_source.data = {"xs": xs_list, "ys": ys_list}

        # Update plot setup
        # -----------------
        # Adjust axes
        self.plot.xaxis.axis_label = "Offset (m)"
        if time_unit == "s":
            self.plot.yaxis.axis_label = "Time (s)"
        elif time_unit == "ms":
            self.plot.yaxis.axis_label = "Time (ms)"

        # Update image renderer's glyph
        # -----------------------------

        width_x_positions = np.abs(x_positions[0] - x_positions[-1])
        width_time_sample_instants = np.abs(time_sample_instants[0] - time_sample_instants[-1])
        distance_first_x_positions = x_positions[1] - x_positions[0]
        distance_last_x_positions = x_positions[-1] - x_positions[-2]

        image_glyph: Image = self.image_gl.glyph
        image_glyph.update(
            x=x_positions[0] - distance_first_x_positions / 2,
            dw=width_x_positions + (distance_first_x_positions + distance_last_x_positions) / 2,
            y=first_time_sample,
            dh=width_time_sample_instants,
        )

        self._set_up_renderers_on_trace_excess(num_traces)

        # Stop holding off requests to repaint the plot
        self.plot.hold_render = False

        update_plot_end = perf_counter()
        print(f"\nTIME update_plot: {update_plot_end - update_plot_start} seconds\n")

    def _remove_harea_renderers(self):
        """Remove all harea glyph renderers from this plot"""
        self.plot.renderers = list(filter(lambda gl: gl.name != "H", self.plot.renderers))

    def _set_up_renderers_on_trace_excess(self, num_traces: int):
        """If there are too many traces, don't allow the user to use the switch
        that enables harea renderer"""
        if num_traces > MAX_TRACES_LINE_HAREA:
            # hide line renderer by using its switch
            self.line_switch.active = False
            # harea is NOT allowed
            if self.harea_switch is not None:
                self.harea_switch.update(active=False, disabled=True)
        else:
            # harea is allowed
            if self.harea_switch is not None:
                self.harea_switch.update(disabled=False, active=True)

    def assign_line_switch(self, switch: Switch):
        """Link a Bokeh model property to the visibility of the wiggle lines"""
        self.line_switch = switch
        self.line_switch.active = self.multi_line_gl.visible
        self.line_switch.js_link("active", self.multi_line_gl, "visible")

    def assign_harea_switch(self, switch: Switch):
        """Link a Bokeh model property to the visibility of the wiggle areas"""

        def harea_switch_handler(attr, old, new: bool):
            self.harea_switch.disabled = True
            with self.plot.hold(render=True):
                for gl in filter(lambda gl: gl.name == "H", self.plot.renderers):
                    gl.visible = new
            self.harea_switch.disabled = False

        self.harea_switch = switch
        self.harea_switch.on_change("active", harea_switch_handler)

    def js_link_image_visible(self, model: Model, attr: str):
        """Link a Bokeh model property to the visibility of the image"""
        model.js_link(attr, self.image_gl, "visible")