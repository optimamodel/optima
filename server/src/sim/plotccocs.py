"""
Plots cost-coverage, coverage-outcome and cost-outcome curves

Version: 2015jan19 by robynstuart
"""
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title, xlim, ylim

# Set defaults for testing makeccocs
default_progname = 'OST'
default_effect = [['sex', 'condomcas'], [u'FSW']] # D.programs[default_prognumber]['effects'][0]
default_ccparams = {'saturation': 0.9, 'coveragelower': 0.25, 'coverageupper':0.4, 'funding':200000.0, 'scaleup':.5, 'nonhivdalys':None, 'xupperlim':None, 'cpibaseyear':None, 'perperson':0}
default_coparams = [0.3, 0.5, 0.7, 0.9] 
default_arteligcutoff = 'gt350'
coverage_params = ['numost','numpmtct','numfirstline','numsecondline']

###############################################################################
from makeccocs import makecc, makeco, makecco
###############################################################################

def plotcc(D, progname=default_progname, ccparams=default_ccparams, arteligcutoff=default_arteligcutoff):
    ''' Plot cost-coverage curve'''

    plotdata_cc, D = makecc(D=D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    figure()
    hold(True)
    if 'xlinedata' in plotdata_cc.keys():
        plot(plotdata_cc['xlinedata'], plotdata_cc['ylinedata'][1], 'k--', lw = 2)
        plot(plotdata_cc['xlinedata'], plotdata_cc['ylinedata'][0], 'b-', lw = 2)
        plot(plotdata_cc['xlinedata'], plotdata_cc['ylinedata'][2], 'k--', lw = 2)
    plot(plotdata_cc['xscatterdata'], plotdata_cc['yscatterdata'], 'ro')
    title(plotdata_cc['title'])
    xlabel(plotdata_cc['xlabel'])
    ylabel(plotdata_cc['ylabel'])
    xlim([plotdata_cc['xlowerlim'],plotdata_cc['xupperlim']])
    ylim([plotdata_cc['ylowerlim'],plotdata_cc['yupperlim']])

###############################################################################
def plotco(D, progname=default_progname, effect=default_effect, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    ''' Plot coverage-outcome curve'''
    
    plotdata_co, effect = makeco(D=D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
    if plotdata_co:
        figure()
        hold(True)
        if 'xlinedata' in plotdata_co.keys():
            plot(plotdata_co['xlinedata'], plotdata_co['ylinedata'][0], color = 'b', lw = 2)
            plot(plotdata_co['xlinedata'], plotdata_co['ylinedata'][1], 'k--', lw = 2)
            plot(plotdata_co['xlinedata'], plotdata_co['ylinedata'][2], 'k--', lw = 2)
        plot(plotdata_co['xscatterdata'], plotdata_co['yscatterdata'], 'ro')
        title(plotdata_co['title'])
        xlabel(plotdata_co['xlabel'])
        ylabel(plotdata_co['ylabel'])
        xlim([plotdata_co['xlowerlim'],plotdata_co['xupperlim']])
        ylim([plotdata_co['ylowerlim'],plotdata_co['yupperlim']])

#################################################################################
def plotcco(D, progname=default_progname, effect=default_effect, ccparams=default_ccparams, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    ''' Plot cost-outcome curve'''

    plotdata_cco, plotdata_co, effect = makecco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)
    if plotdata_co:
        figure()
        hold(True)
        if 'xlinedata' in plotdata_cco.keys():
            plot(plotdata_cco['xlinedata'], plotdata_cco['ylinedata'][0], color = 'b', lw = 2)
            plot(plotdata_cco['xlinedata'], plotdata_cco['ylinedata'][1], 'k--', lw = 2)
            plot(plotdata_cco['xlinedata'], plotdata_cco['ylinedata'][2], 'k--', lw = 2)
        plot(plotdata_cco['xscatterdata'], plotdata_cco['yscatterdata'], 'ro')
        title(plotdata_cco['title'])
        xlabel(plotdata_cco['xlabel'])
        ylabel(plotdata_cco['ylabel'] )
        xlim([plotdata_cco['xlowerlim'],plotdata_cco['xupperlim']])
        ylim([plotdata_cco['ylowerlim'],plotdata_cco['yupperlim']])

#################################################################################
def plotprogramcurves(D, progname=default_progname, ccparams=default_ccparams, coparams=default_coparams, arteligcutoff=default_arteligcutoff):
    ''' Plot all curves for a particular program '''

    plotcc(D, progname=progname, ccparams=ccparams, arteligcutoff=arteligcutoff)
    prognumber = [p['name'] for p in D['programs']].index(progname) # get program number    
    for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):
        plotco(D, progname=progname, effect=effect, coparams=coparams, arteligcutoff=arteligcutoff)
        plotcco(D, progname=progname, effect=effect, ccparams=ccparams, coparams=coparams, arteligcutoff=arteligcutoff)            

#################################################################################
def plotall(D):
    for program in D['programs']:
        plotdata_cc, D = makecc(D=D, progname=program['name'])
        plotprogramcurves(D=D, progname=program['name'])
