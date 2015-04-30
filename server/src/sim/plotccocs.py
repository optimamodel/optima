"""
Plots cost-coverage, coverage-outcome and cost-outcome curves

Version: 2015jan19 by robynstuart
"""
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, xlim, ylim, gca, scatter
from matplotlib.ticker import MaxNLocator
from numpy import nan
from mpld3 import plugins
from utils import OptimaTickFormatter

# Set defaults for testing makeccocs
default_progname = 'PWID programs'
default_effect = {'paramtype':'sex', 'param':'condomreg', 'popname':u'Male PWID'}
default_ccparams = {'saturation': .7,
                    'coveragelower': .4,
                    'coverageupper':.5,
                    'funding':9e6,
                    'scaleup':.2,
                    'nonhivdalys':nan,
                    'cpibaseyear':nan,
                    'perperson':nan}
default_coparams = [0.15, 0.3, 0.4, 0.55]
default_arteligcutoff = 'gt350'
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

###############################################################################
from makeccocs import makecc, makeco, makecco
###############################################################################
def plot_cost_coverage(plotdata, figsize=None):
    """ Plot the cost-coverage figure """

    cost_coverage_figure = None
    if figsize:
        cost_coverage_figure = figure(figsize=figsize, dpi=100)
    else:
        cost_coverage_figure = figure()

    cost_coverage_figure.hold(True)

    axis = cost_coverage_figure.gca()

    if 'xlinedata' in plotdata.keys():
        axis.plot(
            plotdata['xlinedata'],
            plotdata['ylinedata'][1],
            linestyle='--',
            linewidth=2,
            color='#000000')
        axis.plot(
            plotdata['xlinedata'],
            plotdata['ylinedata'][0],
            linestyle='-',
            linewidth=2,
            color='#a6cee3')
        axis.plot(
            plotdata['xlinedata'],
            plotdata['ylinedata'][2],
            linestyle='--',
            linewidth=2,
            color='#000000')
    axis.scatter(
        plotdata['xscatterdata'],
        plotdata['yscatterdata'],
        color='#666666')

    axis.set_xlim([plotdata['xlowerlim'], plotdata['xupperlim']])
    axis.set_ylim([plotdata['ylowerlim'], plotdata['yupperlim']])
    axis.tick_params(axis='both', which='major', labelsize=11)
    axis.set_xlabel(plotdata['xlabel'], fontsize=11)
    axis.set_ylabel(plotdata['ylabel'], fontsize=11)
    axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
    axis.set_title(plotdata['title'])

    # clear all plugins from the figure
    plugins.clear(cost_coverage_figure)
    plugins.connect(
        cost_coverage_figure,
        plugins.BoxZoom(button=False),
        plugins.Zoom(button=False),
        OptimaTickFormatter())

    return cost_coverage_figure


def plotcc(D, progname=default_progname, ccparams=default_ccparams, arteligcutoff=default_arteligcutoff):
    """ Generate cost-coverage data and plot it. """

    plotdata_cc, D = makecc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    return plot_cost_coverage(plotdata_cc)

###############################################################################
def plot_coverage_outcome(plotdata, figsize = None):
    """ Plot the coverage-outcome figure """
    coverage_outcome_figure = None
    if plotdata:
        if figsize:
            coverage_outcome_figure = figure(figsize = figsize, dpi=100)
        else:
            coverage_outcome_figure = figure()
        coverage_outcome_figure.hold(True)

        axis = coverage_outcome_figure.gca()

        if 'xlinedata' in plotdata.keys():
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata'][0],
                linestyle='-',
                linewidth=2,
                color='#a6cee3')
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata'][1],
                linestyle='--',
                linewidth=2,
                color='#000000')
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata'][2],
                linestyle='--',
                linewidth=2,
                color='#000000')
        axis.scatter(
            plotdata['xscatterdata'],
            plotdata['yscatterdata'],
            color='#666666')

        axis.set_title(plotdata['title'])
        axis.tick_params(axis='both', which='major', labelsize=11)
        axis.set_xlabel(plotdata['xlabel'], fontsize=11)
        axis.set_ylabel(plotdata['ylabel'], fontsize=11)
        axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
        axis.set_xlim([plotdata['xlowerlim'], plotdata['xupperlim']])
        axis.set_ylim([plotdata['ylowerlim'], plotdata['yupperlim']])

        # clear all plugins from the figure
        plugins.clear(coverage_outcome_figure)
        plugins.connect(
            coverage_outcome_figure,
            plugins.BoxZoom(button=False),
            plugins.Zoom(button=False),
            OptimaTickFormatter())

    return coverage_outcome_figure


def plotco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    """ Generate coverage-outcome data and plot it. """

    plotdata_co, effect = makeco(D=D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
    return plot_coverage_outcome(plotdata_co)

#################################################################################
def plot_cost_outcome(plotdata, figsize = None):
    """ Plot the cost-outcome figure """

    cost_outcome_figure = None
    if plotdata:
        if figsize:
            cost_outcome_figure = figure(figsize = figsize, dpi=100)
        else:
            cost_outcome_figure = figure()
        cost_outcome_figure.hold(True)

        axis = cost_outcome_figure.gca()

        if 'xlinedata' in plotdata.keys():
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata'][0],
                linestyle='-',
                linewidth=2,
                color='#a6cee3')
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata'][1],
                linestyle='--',
                linewidth=2,
                color='#000000')
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata'][2],
                linestyle='--',
                linewidth=2,
                color='#000000')
        axis.scatter(
            plotdata['xscatterdata'],
            plotdata['yscatterdata'],
            color='#666666')

        axis.set_title(plotdata['title'])
        axis.tick_params(axis='both', which='major', labelsize=11)
        axis.set_xlabel(plotdata['xlabel'], fontsize=11)
        axis.set_ylabel(plotdata['ylabel'], fontsize=11)
        axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
        axis.set_xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
        axis.set_ylim([plotdata['ylowerlim'],plotdata['yupperlim']])

        # clear all plugins from the figure
        plugins.clear(cost_outcome_figure)
        plugins.connect(
            cost_outcome_figure,
            plugins.BoxZoom(button=False),
            plugins.Zoom(button=False),
            OptimaTickFormatter())
    return cost_outcome_figure


def plotcco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, coparams=default_coparams, \
    arteligcutoff=default_arteligcutoff):
    """ Generate cost-outcome data and plot it. """

    plotdata_cco, plotdata_co, effect = makecco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)
    return plot_cost_outcome(plotdata_cco)

#################################################################################
def plotprogramcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    """ Plot all figures for a particular program """

    plotcc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number
    for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):
        plotco(D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
        plotcco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)

#################################################################################
def plotall(D, ccparams = default_ccparams, coparams = default_coparams):
    for program in D['programs']:
        plotdata_cc, D = makecc(D=D, progname=program['name'])
        plotprogramcurves(D=D, progname=program['name'])
