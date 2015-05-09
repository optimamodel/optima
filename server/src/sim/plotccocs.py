"""
Plots cost-coverage, coverage-outcome and cost-outcome curves

Version: 2015jan19 by robynstuart
"""
from matplotlib.pylab import figure
from matplotlib.pyplot import close
from matplotlib.ticker import MaxNLocator
from numpy import nan
from mpld3 import plugins, fig_to_dict
from utils import OptimaTickFormatter

# Set defaults for testing makeccocs
default_progname = 'NSP'
default_effect = {'paramtype':'inj', 'param':'sharing', 'popname':u'Male PWID'}
default_ccparams = {'saturation': .7,
                    'coveragelower': .4,
                    'coverageupper':.5,
                    'funding':9e5,
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
def plot_cost_coverage(plotdata, figure=None, closeFigure=True):
    """ Plot the cost-coverage figure """

    cost_coverage_figure = figure if figure else figure()
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

    if closeFigure:
        cost_coverage_figure.clf()
        axis.cla()
        close(cost_coverage_figure)

    return cost_coverage_figure


def plotcc(D, progname=default_progname, ccparams=default_ccparams, arteligcutoff=default_arteligcutoff):
    """ Generate cost-coverage data and plot it. """

    plotdata_cc, D = makecc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    plot_cost_coverage(plotdata_cc)

###############################################################################
def plot_coverage_outcome(plotdata, figure=None, closeFigure=True):
    """ Plot the coverage-outcome figure """

    if plotdata == None:
        return None

    coverage_outcome_figure = figure if figure else figure()
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

    if closeFigure:
        coverage_outcome_figure.clf()
        axis.cla()
        close(coverage_outcome_figure)

    return coverage_outcome_figure


def plotco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    """ Generate coverage-outcome data and plot it. """

    plotdata_co, effect = makeco(D=D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
    plot_coverage_outcome(plotdata_co)

#################################################################################
def plot_cost_outcome(plotdata, figsize = None):
    """ Plot the cost-outcome figure """

    cost_outcome_figure = None
    result = None
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
        axis.scatter(
            plotdata['xcurrentdata'],
            plotdata['ycurrentdata'],
            color='#d22c2c')

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
            # Box zoom is needed to manually create a zoom button in the JS front-end
            plugins.BoxZoom(button=False, enabled=False),
            OptimaTickFormatter())
        result = fig_to_dict(cost_outcome_figure)
        cost_outcome_figure.clf()
        axis.cla()
        close(cost_outcome_figure)
    return result


def plotcco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, coparams=default_coparams, \
    arteligcutoff=default_arteligcutoff):
    """ Generate cost-outcome data and plot it. """

    plotdata_cco, plotdata_co, effect = makecco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)
    plot_cost_outcome(plotdata_cco)

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
