"""
Plots cost-coverage, coverage-outcome and cost-outcome curves
    
Version: 2015jan19 by robynstuart
"""
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, xlim, ylim
from printv import printv

default_progname = 'MSM programs'
default_ccparams = [0.9, 0.5, 0.7, 335260.2878916174, None, None] #
default_ccplot = [1e6, None, 0]
default_coparams = [0.3, 0.5, 0.7, 0.9] 
default_effect = [['sex', 'condomcas'], [u'MSM']] # D.programs[default_progname]['effects'][0] 
default_artelig = range(6,31)
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

###############################################################################
def plotcc(D, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot):
    '''
    Plot a single cost-coverage curve
    '''
    
    from makeccocs import makecc
    
    plotdata, D = makecc(D, progname=progname, ccparams=ccparams, ccplot=ccplot, artelig=default_artelig, verbose=2, nxpts = 1000)

    printv("plotting cc for program %s" % progname, 4, 2)   
    figure()
    hold(True)
    if 'xlinedata' in plotdata.keys():
        plot(plotdata['xlinedata'], plotdata['ylinedata'][0], 'k--', lw = 2)
        plot(plotdata['xlinedata'], plotdata['ylinedata'][1], 'b-', lw = 2)
        plot(plotdata['xlinedata'], plotdata['ylinedata'][2], 'k--', lw = 2)
    plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')
    title(plotdata['title'])
    xlabel(plotdata['xlabel'])
    ylabel(plotdata['ylabel'])
    xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
    ylim([plotdata['ylowerlim'],plotdata['yupperlim']])

###############################################################################
def plotco(D, progname=default_progname, effect=default_effect, coparams=default_coparams):
    '''
    Plot a single coverage-outcome curve
    '''

    from makeccocs import makeco

    plotdata, effect = makeco(D, progname=progname, effect=effect, coparams=coparams, verbose=2,nxpts = 1000)

    # Plot results                           
    figure()
    hold(True)
    if 'xlinedata' in plotdata.keys():
        plot(plotdata['xlinedata'], plotdata['ylinedata1'], color = 'b', lw = 2)
        plot(plotdata['xlinedata'], plotdata['ylinedata2'], 'k--', lw = 2)
        plot(plotdata['xlinedata'], plotdata['ylinedata3'], 'k--', lw = 2)
    plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')
    title(plotdata['title'])
    xlabel(plotdata['xlabel'])
    ylabel(plotdata['ylabel'])
    xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
    ylim([plotdata['ylowerlim'],plotdata['yupperlim']])

###############################################################################
def plotcco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams):
    '''
    Plot a single cost-outcome curve
    '''

    from makeccocs import makecco
    
    plotdata, plotdata_co, effect = makecco(D, progname=progname, effect=effect, ccparams=ccparams, ccplot=ccplot, coparams=coparams, verbose=2, nxpts=1000)

    # Plot results 
    figure()
    hold(True)
    if 'xlinedata' in plotdata.keys():
        plot(plotdata['xlinedata'], plotdata['ylinedata1'], color = 'b', lw = 2)
        plot(plotdata['xlinedata'], plotdata['ylinedata2'], 'k--', lw = 2)
        plot(plotdata['xlinedata'], plotdata['ylinedata3'], 'k--', lw = 2)
    plot(plotdata['xscatterdata'], plotdata['yscatterdata'], 'ro')                
    title(plotdata['title'])
    xlabel(plotdata['xlabel'])
    ylabel(plotdata['ylabel'] )
    xlim([plotdata['xlowerlim'],plotdata['xupperlim']])
    ylim([plotdata['ylowerlim'],plotdata['yupperlim']])
    
###############################################################################
def plotprogramcco(D, progname=default_progname, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams):
    '''
    Plot all cost-coverage, coverage-outcome and cost-outcome curves for a single program
    '''
    
    plotcc(D, progname=progname, ccparams=ccparams, ccplot=ccplot)
    for effectnumber, effect in enumerate(D.programs[progname]['effects']):
        parname = effect[0][1]
        if parname not in coverage_params:
            plotco(D, progname=progname, effect=effect, coparams=coparams)
            plotcco(D, progname=progname, effect=effect, ccparams=ccparams, ccplot=ccplot, coparams=coparams)

###############################################################################
def plotallcco(D, ccparams=default_ccparams, ccplot=default_ccplot, coparams=default_coparams):
    '''
    Plot all cost-coverage, coverage-outcome and cost-outcome curves for all programs
    '''

    for progname in D.programs.keys():
        plotprogramcco(D, progname=progname, ccparams=ccparams, ccplot=ccplot, coparams=coparams)

###############################################################################


