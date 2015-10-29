"""
Plots cost-coverage, coverage-outcome and cost-outcome curves

Version: 2015jan19 by robynstuart
"""
from matplotlib.pylab import figure
from matplotlib.pyplot import close
from matplotlib.ticker import MaxNLocator
from numpy import nan

# Set defaults for testing makeccocs
default_progname = 'VMMC'
default_effect = {'paramtype':'sex', 'param':'circum', 'popname':u'Males 15-24'}
default_ccparams = {'saturation': .7,
                    'coveragelower': .4,
                    'coverageupper':.5,
                    'funding':9e5,
                    'scaleup':.2,
                    'nonhivdalys':nan,
                    'xupperlim':2e7,
                    'cpibaseyear':nan,
                    'perperson':nan}
default_coparams = [0.15, 0.3, 0.4, 0.55]
default_arteligcutoff = 'gt350'
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

###############################################################################
from makeccocs import makecc, makeco, makecco
###############################################################################
<<<<<<< HEAD:optima/legacy/plotccocs.py
def plot_cost_coverage(plotdata, figsize=None, doclose=True):
=======
def plot_cost_coverage(plotdata, existingFigure=None):
>>>>>>> develop:server/src/sim/plotccocs.py
    """ Plot the cost-coverage figure """

    cost_coverage_figure = existingFigure if existingFigure else figure()
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

<<<<<<< HEAD:optima/legacy/plotccocs.py
    # clear all plugins from the figure
    plugins.clear(cost_coverage_figure)
    plugins.connect(
        cost_coverage_figure,
        # Box zoom is needed to manually create a zoom button in the JS front-end
        plugins.BoxZoom(button=False, enabled=False),
        OptimaTickFormatter())

    result = fig_to_dict(cost_coverage_figure)
    if doclose: 
        cost_coverage_figure.clf()
        axis.cla()
        close(cost_coverage_figure)

    return result
=======
    return cost_coverage_figure
>>>>>>> develop:server/src/sim/plotccocs.py


def plotcc(D, progname=default_progname, ccparams=default_ccparams, arteligcutoff=default_arteligcutoff, doclose=True):
    """ Generate cost-coverage data and plot it. """

    plotdata_cc, D = makecc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    plot_cost_coverage(plotdata_cc, doclose=doclose)

###############################################################################
<<<<<<< HEAD:optima/legacy/plotccocs.py
def plot_coverage_outcome(plotdata, figsize = None, doclose=True):
    """ Plot the coverage-outcome figure """
    result = None
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
            # Box zoom is needed to manually create a zoom button in the JS front-end
            plugins.BoxZoom(button=False, enabled=False),
            OptimaTickFormatter())

        result = fig_to_dict(coverage_outcome_figure)
        if doclose: 
            coverage_outcome_figure.clf()
            axis.cla()
            close(coverage_outcome_figure)
    return result
=======
def plot_coverage_outcome(plotdata, existingFigure=None):
    """ Plot the coverage-outcome figure """

    if not plotdata:
        return None

    coverage_outcome_figure = existingFigure if existingFigure else figure()
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

    return coverage_outcome_figure
>>>>>>> develop:server/src/sim/plotccocs.py


def plotco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, arteligcutoff=default_arteligcutoff, doclose=True):
    """ Generate coverage-outcome data and plot it. """

    plotdata_co, effect = makeco(D=D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
    plot_coverage_outcome(plotdata_co, doclose=doclose)

#################################################################################
<<<<<<< HEAD:optima/legacy/plotccocs.py
def plot_cost_outcome(plotdata, figsize = None, doclose=True):
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
        if doclose:
            cost_outcome_figure.clf()
            axis.cla()
            close(cost_outcome_figure)
    return result
=======
def plot_cost_outcome(plotdata, existingFigure=None):
    """ Plot the cost-outcome figure """

    if not plotdata:
        return None

    cost_outcome_figure = existingFigure if existingFigure else figure()
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

    return cost_outcome_figure
>>>>>>> develop:server/src/sim/plotccocs.py


def plotcco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, coparams=default_coparams, \
    arteligcutoff=default_arteligcutoff, doclose=True):
    """ Generate cost-outcome data and plot it. """

    plotdata_cco, plotdata_co, effect = makecco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)
    plot_cost_outcome(plotdata_cco, doclose=doclose)

#################################################################################
def plotprogramcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, arteligcutoff=default_arteligcutoff, doclose=True):
    """ Plot all figures for a particular program """

    plotcc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff, doclose=doclose)
    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number
    for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):
        plotco(D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff, doclose=doclose)
        plotcco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff, doclose=doclose)

#################################################################################
def plotall(D, ccparams = default_ccparams, coparams = default_coparams, doclose=True):
    for program in D['programs']:
        plotdata_cc, D = makecc(D=D, progname=program['name'])
        plotprogramcurves(D=D, progname=program['name'], doclose=doclose)
