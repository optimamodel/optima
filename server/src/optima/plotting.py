from matplotlib.pylab import figure
from matplotlib.pyplot import close
from mpld3 import plugins, fig_to_dict
from sim.plotccocs import plot_cost_coverage, plot_cost_outcome, plot_coverage_outcome

class OptimaTickFormatter(plugins.PluginBase):
    """
    Optima Tick Formatter plugin

    Since tickFormatting is not working properly we patch & customise it only in
    the Front-end. See this issue for more information about the current status
    of tick customisation: https://github.com/jakevdp/mpld3/issues/22
    """

    def __init__(self):
        self.dict_ = {"type": "optimaTickFormatter"}

def generate_cost_coverage_chart(plotdata):
    """ Returns the cost-coverage chart as Mpld3 JSON format """

    blank_figure = figure(figsize=(3,2), dpi=100)
    cost_coverage_figure = plot_cost_coverage(plotdata, figure=blank_figure)

    # clear all plugins from the figure
    plugins.clear(cost_coverage_figure)
    plugins.connect(
        cost_coverage_figure,
        # Box zoom is needed to manually create a zoom button in the JS front-end
        plugins.BoxZoom(button=False, enabled=False),
        OptimaTickFormatter())

    result = fig_to_dict(cost_coverage_figure)

    # close figure
    axis = cost_coverage_figure.gca()
    axis.cla()
    cost_coverage_figure.clf()
    close(cost_coverage_figure)

    return result

def generate_coverage_outcome_chart(plotdata):
    """ Returns the coverage-outcome chart as Mpld3 JSON format """

    blank_figure = figure(figsize=(3,2), dpi=100)
    coverage_outcome_figure = plot_coverage_outcome(plotdata, figure=blank_figure)

    # clear all plugins from the figure
    plugins.clear(coverage_outcome_figure)
    plugins.connect(
        coverage_outcome_figure,
        # Box zoom is needed to manually create a zoom button in the JS front-end
        plugins.BoxZoom(button=False, enabled=False),
        OptimaTickFormatter())

    result = fig_to_dict(coverage_outcome_figure)

    # close figure
    axis = coverage_outcome_figure.gca()
    axis.cla()
    coverage_outcome_figure.clf()
    close(coverage_outcome_figure)

    return result

def generate_cost_outcome_chart(plotdata):
    """ Returns the cost-outcome chart as Mpld3 JSON format """

    blank_figure = figure(figsize=(3,2), dpi=100)
    cost_outcome_figure = plot_cost_outcome(plotdata, figure=blank_figure)

    # clear all plugins from the figure
    plugins.clear(cost_outcome_figure)
    plugins.connect(
        cost_outcome_figure,
        # Box zoom is needed to manually create a zoom button in the JS front-end
        plugins.BoxZoom(button=False, enabled=False),
        OptimaTickFormatter())

    result = fig_to_dict(cost_outcome_figure)

    # close figure
    axis = cost_outcome_figure.gca()
    axis.cla()
    cost_outcome_figure.clf()
    close(cost_outcome_figure)

    return result
