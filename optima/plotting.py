'''
PLOTTING

This file generates all the figure files -- either for use with the Python backend, or
for the frontend via MPLD3.

To add a new plot, you need to add it to getplotselections (in this file) so it will show up in the interface;
plotresults (in gui.py) so it will be sent to the right spot; and then add the actual function to do the
plotting to this file.

Version: 2017jun03
'''

from optima import OptimaException, Resultset, Multiresultset, Parameterset, Settings, ICER, odict, printv, gridcolors, vectocolor, alpinecolormap, makefilepath, sigfig, dcp, findinds, findnearest, promotetolist, saveobj, promotetoodict, promotetoarray, boxoff, getvalidinds
from optima import setylim, commaticks, SIticks
from numpy import array, ndim, maximum, arange, zeros, mean, shape, isnan, linspace, minimum, concatenate,invert, swapaxes, flip, abs,cumsum, logical_and, newaxis # Numeric functions
from pylab import gcf, get_fignums, close, ion, ioff, isinteractive, figure # Plotting functions
from matplotlib.backends.backend_agg import new_figure_manager_given_figure as nfmgf # Warning -- assumes user has agg on their system, but should be ok. Use agg since doesn't require an X server
from matplotlib.figure import Figure # This is the non-interactive version
from matplotlib import ticker
import textwrap

# Define allowable plot formats -- 4 kinds, but allow some flexibility for how they're specified
epiplottypes = ['total', 'stacked', 'population','population+stacked']
realdatacolor = (0,0,0) # Define color for data point -- WARNING, should this be in settings.py?
estimatecolor = (0.8,0.8,0.8) # Color of estimates rather than real data
fillzorder = 0 # The order in which to plot things -- fill at the back
datazorder = 100 # Then data
linezorder = 200 # Finally, lines
proghueshift = 0.05 # Slightly shift colors for programs

# Define global font sizes
globaltitlesize = 12
globallabelsize = 12
globalticksize = 10
globallegendsize = 10
globalfigsize = (8,4)
globalposition = [0.1,0.06,0.6,0.8]
interactiveposition = [0.15,0.1,0.55,0.75] # Use slightly larger margnis for interactive plots


def getdefaultplots(ismulti='both'):
    ''' Since these can get overwritten otherwise '''
    ''' These should always include the plottype ie "-stacked" etc to avoid ambiguity if needed'''
    ''' Note that if both 'numinci-stacked' and 'numinci-population' for example are included, there may be some bugs in the FE: make_mpld3_graph_dict()'''
    defaultplots = ['cascadebars', 'budgets', 'tvbudget', 'numplhiv-stacked', 'numinci-stacked', 'numdeath-stacked', 'numtreat-stacked', 'numnewdiag-stacked', 'prev-population', 'popsize-stacked', 'propdiag-total','proptreat-total','propsuppressed-total'] # Default epidemiological plots
    defaultmultiplots = ['budgets', 'tvbudget', 'numplhiv-total', 'numinci-total', 'numdeath-total', 'numtreat-total', 'numnewdiag-total', 'prev-population', 'popsize-stacked', 'propdiag-total','proptreat-total','propsuppressed-total'] # Default epidemiological plots
    if ismulti==False:  return defaultplots
    elif ismulti==True: return defaultmultiplots
    else:               return defaultplots,defaultmultiplots


def makefigure(figsize=None, facecolor=None, interactive=False, fig=None, newfig=None, **kwargs):
    ''' Decide whether to make an interactive figure() or a non-interactive Figure()'''
    if figsize is None:   figsize = globalfigsize
    if facecolor is None: facecolor = (1,1,1)
    if fig is None or newfig: # Create a new figure if one is not supplied
        if interactive:  fig = figure(facecolor=facecolor, figsize=figsize, **kwargs)
        else:            fig = Figure(facecolor=facecolor, figsize=figsize, **kwargs)
    naxes = len(fig.axes)+1 # Count the number of existing axes
    return fig, naxes


def setposition(ax=None, position=None, interactive=False):
    ''' A small helper function to decide how to position the axes '''
    if position is None:
        if interactive: position = interactiveposition
        else:           position = globalposition
    ax.set_position(position)
    return position
    

def getplotselections(results, advanced=False, includeadvancedtracking=False):
    ''' 
    From the inputted results structure, figure out what the available kinds of plots are. List results-specific
    plot types first (e.g., allocations), followed by the standard epi plots, and finally (if available) other
    plots such as the cascade.
    
    Version: 2017may29
    '''
    
    # Figure out what kind of result it is -- WARNING, copied from below
    if type(results)==Resultset: ismultisim = False
    elif type(results)==Multiresultset and results.nresultsets > 1:  ismultisim = True
    elif type(results)==Multiresultset and results.nresultsets == 1: ismultisim = False # A Multiresultset with only one Resultset can have stacked plots
    else: 
        errormsg = 'Results input to plotepi() must be either Resultset or Multiresultset, not "%s".' % type(results)
        raise OptimaException(errormsg)
    
    ## Set up output structure
    plotselections = dict()
    plotselections['keys'] = list()
    plotselections['names'] = list()
    plotselections['defaults'] = list()
    
    ## Add selections for outcome -- for autofit()- or minoutcomes()-generated results
    if hasattr(results, 'improvement') and results.improvement is not None:
        plotselections['keys'].append('improvement') # WARNING, maybe more standard to do append()...
        plotselections['names'].append('Improvement')
    
    ## Add selection for budget allocations and coverage
    budcovlist = [('budgets','budgets','Budget allocations'), ('coverage','coverages','Program coverages')]
    for bckey,bcattr,bclabel in budcovlist: # Loop over budget and coverage
        if hasattr(results, bcattr):
            budcovres = getattr(results, bcattr)
            if budcovres and all([item is not None for item in budcovres.values()]): # Make sure none of the individual budgets are none either
                plotselections['keys'].append(bckey) # e.g. 'budget'
                plotselections['names'].append(bclabel) # e.g. 'Budget allocation'
    
    ## Add time-varying budget results
    if hasattr(results, 'timevarying') and results.timevarying is not None:
        plotselections['keys'].append('tvbudget') # WARNING, maybe more standard to do append()...
        plotselections['names'].append('Budget (time-varying)')
        
    ## Cascade plot is always available, since epi is always available
    plotselections['keys'].append('cascade')
    plotselections['names'].append('Care cascade')
    if advanced:
        plotselections['keys'].append('cascadebars')
        plotselections['names'].append('Care cascade (bars) 95-95-95 targets')
        plotselections['keys'].append('cascadebars90')
        plotselections['names'].append('Care cascade (bars) 90-90-90 targets')
    else:
        plotselections['keys'].append('cascadebars')
        plotselections['names'].append('Care cascade (bars)')
    
#    ## Deaths by CD4 -- broken because no results.raw
#    if advanced:
#        plotselections['keys'].append('deathbycd4')
#        plotselections['names'].append('Deaths by CD4')
#    
#    ## People by CD4
#    if advanced:
#        plotselections['keys'].append('plhivbycd4')
#        plotselections['names'].append('PLHIV by CD4')
    
    ## Get plot selections for plotepi
    plotepikeys = list()
    plotepinames = list()
    
    epikeys = results.main.keys() # e.g. 'prev'
    epinames = [result.name for result in results.main.values()]
    
    if advanced: # Loop has to be written this way so order is correct
        for key in epikeys: # e.g. 'prev'
            for subkey in epiplottypes: # e.g. 'total'
                if not(ismultisim and subkey=='stacked'): # Stacked multisim plots don't make sense
                    if (not subkey=='population+stacked'): #disallow not population+stacked, make sure to disallow below as well
                        plotepikeys.append(key+'-'+subkey)
        for name in epinames: # e.g. 'HIV prevalence'
            for subname in epiplottypes: # e.g. 'total'
                if not(ismultisim and subname=='stacked'): # Stacked multisim plots don't make sense -- TODO: handle this better
                    if (not subname == 'population+stacked'):  # disallow not population+stacked, make sure to disallow above as well
                        plotepinames.append(name+' - '+subname)
        if includeadvancedtracking:
            advtrackkeys,advtracknames = getadvancedtrackingplotselections(results=results, advanced=advanced)
            if not ismultisim:
                plotepikeys.extend(advtrackkeys)
                plotepinames.extend(advtracknames)
            else: # if multisim don't include stacked or population+stacked plots
                for ik, key in enumerate(advtrackkeys):
                    if not key.endswith('stacked'):
                        plotepikeys.append(key)
                        plotepinames.append(advtracknames[ik])


    else:
        plotepikeys = dcp(epikeys)
        plotepinames = dcp(epinames)
    
    defaultplots = getdefaultplots(ismulti=ismultisim)
    if not advanced:
        for i in range(len(defaultplots)): defaultplots[i] = defaultplots[i].split('-')[0] # Discard second half of plot name
    plotselections['keys'] += plotepikeys
    plotselections['names'] += plotepinames
    for key in plotselections['keys']: # Loop over each key
        plotselections['defaults'].append(key in defaultplots) # Append True if it's in the defaults; False otherwise
    
    return plotselections


def getadvancedtrackingplotselections(results=None,advanced=False):
    '''
    Args:
        results: the Optima simulation Result object, currently not used
        advanced: whether or not advanced plots are selected

    Returns:
        A list (not dict) of full plot keys and a list of plot names
    '''
    if advanced: # These plots are only available in advanced plots
        plotkeys = ['changeinplhivallsources-population+stacked',
                     'numincimethods-stacked',
                     'numincimethods-population+stacked']
        plotnames = ['Change in PLHIV - population+stacked',
                    'Number of infections by method - stacked',
                    'Number of infections by method - population+stacked']
        return plotkeys,plotnames
    return [],[]


def checkifneedtorerunwithadvancedtracking(results=None, which=None):
    print(f' >> checkifneedtorerunwithadvancedtracking {type(results)=} {type(results.advancedtracking)=} {isinstance(results.advancedtracking, odict)=} {results.advancedtracking=}, {which=}')
    if results is not None:
        if not hasattr(results, 'parsetuid'):  # need it later, so results need refreshing
            return True
        if not hasattr(results, 'advancedtracking'): #might not really need it but the results need refreshing
            return True
        elif isinstance(results.advancedtracking, odict):
            alladvancedtracking = True
            for advancedtracking in results.advancedtracking.values():
                if not advancedtracking: alladvancedtracking = False
            if alladvancedtracking:  return False  # Already run with advancedtracking so don't need to rerun
        elif results.advancedtracking:  # Already run with advancedtracking so don't need to rerun
            return False

    if which is None:
        return False  # Don't need any graphs so don't need advanced tracking on

    advancedtrackingplots,plotnames = getadvancedtrackingplotselections(results=results, advanced=True)
    advancedtrackingsplit = tuple(w.split("-")[0] for w in advancedtrackingplots)
    whichsplit = [w.split("-")[0] for w in which]

    needtorerun = False
    for key in which:
        if key.startswith(advancedtrackingsplit):
            needtorerun = True

    return needtorerun


def makeplots(results=None, toplot=None, die=False, verbose=2, plotstartyear=None, plotendyear=None, fig=None, newfig=False, **kwargs):
    ''' 
    Function that takes all kinds of plots and plots them -- this is the only plotting function the user should use 
    
    The keyword 'die' controls what it should do with an exception: if False, then carry on as if nothing happened;
    if True, then actually rase the exception.
    
    Note that if toplot='default', it will plot the default plots (defined in plotting.py).
    
    Version: 2016jan24    
    '''
    
    ## Initialize
    allplots = odict()
    if toplot is None: toplot = getdefaultplots(ismulti=False) # Go straight ahead and replace with defaults
    if not(isinstance(toplot, list)): toplot = [toplot] # Handle single entries, for example 
    if 'default' in toplot: # Special case for handling default plots
        toplot[0:0] = getdefaultplots(ismulti=False) # Very weird but valid syntax for prepending one list to another: http://stackoverflow.com/questions/5805892/how-to-insert-the-contents-of-one-list-into-another
    toplot = list(odict.fromkeys(toplot)) # This strange but efficient hack removes duplicates while preserving order -- see http://stackoverflow.com/questions/1549509/remove-duplicates-in-a-list-while-keeping-its-order-python
    results = sanitizeresults(results)
    
    
    ## Add improvement plot
    if 'improvement' in toplot:
        toplot.remove('improvement') # Because everything else is passed to plotepi()
        if hasattr(results, 'improvement') and results.improvement is not None: # WARNING, duplicated from getplotselections()
            allplots['improvement'] = plotimprovement(results, die=die, fig=fig, **kwargs)
    
    ## Add budget plot
    if 'budgets' in toplot:
        toplot.remove('budgets') # Because everything else is passed to plotepi()
        if hasattr(results, 'budgets') and results.budgets: # WARNING, duplicated from getplotselections()
            budgetplots = plotbudget(results, die=die, fig=fig, **kwargs)
            allplots.update(budgetplots)
    
    ## Add time-varying budget plot
    if 'tvbudget' in toplot:
        toplot.remove('tvbudget') # Because everything else is passed to plotepi()
        if hasattr(results, 'timevarying') and results.timevarying: # WARNING, duplicated from getplotselections()
            tvbudgetplots = plottvbudget(results, die=die, fig=fig, **kwargs)
            allplots.update(tvbudgetplots)
    
    ## Add coverage plot(s)
    if 'coverage' in toplot:
        toplot.remove('coverage') # Because everything else is passed to plotepi()
        if hasattr(results, 'coverages') and results.coverages: # WARNING, duplicated from getplotselections()
            coverageplots = plotcoverage(results, die=die, fig=fig, **kwargs)
            allplots.update(coverageplots)
    
    ## Add cascade plot(s)
    if 'cascade' in toplot:
        toplot.remove('cascade') # Because everything else is passed to plotepi()
        cascadeplots = plotcascade(results, die=die, plotstartyear=plotstartyear, plotendyear=plotendyear, fig=fig, newfig=newfig, **kwargs)
        allplots.update(cascadeplots)

    bothcascadebars = ('cascadebars' in toplot) and ('cascadebars90' in toplot)
    ## Add cascade plot(s) with bars
    if 'cascadebars' in toplot:
        toplot.remove('cascadebars') # Because everything else is passed to plotepi()
        titlesuffix = ' (95-95-95 targets)' if bothcascadebars else None
        cascadebarplots = plotcascade(results, die=die, fig=fig, asbars=True, newfig=newfig,titlesuffix=titlesuffix, **kwargs)
        allplots.update(cascadebarplots)

    ## Add cascade plot(s) with bars
    if 'cascadebars90' in toplot:
        toplot.remove('cascadebars90')  # Because everything else is passed to plotepi()
        titlesuffix = ' (90-90-90 targets)' if bothcascadebars else None
        cascadebarplots90 = plotcascade(results, targets=90, die=die, fig=fig, asbars=True, newfig=newfig,titlesuffix=titlesuffix, **kwargs)
        allplots.update(cascadebarplots90)
    
    ## Add deaths by CD4 plot -- WARNING, only available if results includes raw
    if 'deathbycd4' in toplot:
        toplot.remove('deathbycd4') # Because everything else is passed to plotepi()
        allplots['deathbycd4'] = plotbycd4(results, whattoplot='death', die=die, fig=fig, **kwargs)
    
    ## Add PLHIV by CD4 plot -- WARNING, only available if results includes raw
    if 'plhivbycd4' in toplot:
        toplot.remove('plhivbycd4') # Because everything else is passed to plotepi()
        allplots['plhivbycd4'] = plotbycd4(results, whattoplot='people', die=die, fig=fig, **kwargs)

    ## Plot new infections, transitions, deaths and other death, giving total change in PLHIV
    if 'changeinplhivallsources' in toplot:
        toplot.remove('changeinplhivallsources')
        plots = plotchangeinplhivallsources(results,which='changeinplhivallsources-population+stacked', die=die, fig=fig, **kwargs)
        allplots.update(plots)
    ## Plot new infections, transitions, deaths and other death, giving total change in PLHIV
    if 'changeinplhivallsources-population+stacked' in toplot:
        toplot.remove('changeinplhivallsources-population+stacked')
        plots = plotchangeinplhivallsources(results,which='changeinplhivallsources-population+stacked', die=die, fig=fig, **kwargs)
        allplots.update(plots)
    ## Plot new infections, transitions, deaths and other death, giving total change in PLHIV
    if 'changeinplhivallsources-stacked' in toplot:
        toplot.remove('changeinplhivallsources-stacked')
        plots = plotchangeinplhivallsources(results,which='changeinplhivallsources-stacked', die=die, fig=fig, **kwargs)
        allplots.update(plots)
    ## Plot new infections, transitions, deaths and other death, giving total change in PLHIV
    if 'plhivallsources' in toplot:
        toplot.remove('plhivallsources')
        plots = plotchangeinplhivallsources(results, which='plhivallsources-population+stacked', die=die, fig=fig,**kwargs)
        allplots.update(plots)
    if 'plhivallsources-population+stacked' in toplot:
        toplot.remove('plhivallsources-population+stacked')
        plots = plotchangeinplhivallsources(results, which='plhivallsources-population+stacked', die=die, fig=fig,**kwargs)
        allplots.update(plots)
    if 'plhivallsources-stacked' in toplot:
        toplot.remove('plhivallsources-stacked')
        plots = plotchangeinplhivallsources(results, which='plhivallsources-stacked', die=die, fig=fig,**kwargs)
        allplots.update(plots)

    ## Plot infections by method of transmission, and by population
    if 'numincimethods' in toplot:
        toplot.remove('numincimethods')  # Because everything else is passed to plotepi()
        plots = plotbymethod(results, toplot='numincimethods', die=die, fig=fig, **kwargs)
        allplots.update(plots)
    if 'numincimethods-population+stacked' in toplot:
        toplot.remove('numincimethods-population+stacked')  # Because everything else is passed to plotepi()
        plots = plotbymethod(results, toplot='numincimethods-population+stacked', die=die, fig=fig, **kwargs)
        allplots.update(plots)
    if 'numincimethods-stacked' in toplot:
        toplot.remove('numincimethods-stacked')  # Because everything else is passed to plotepi()
        plots = plotbymethod(results, toplot='numincimethods-stacked', die=die, fig=fig, **kwargs)
        allplots.update(plots)



    ## Add epi plots -- WARNING, I hope this preserves the order! ...It should...
    epiplots = plotepi(results, toplot=toplot, die=die, plotstartyear=plotstartyear, plotendyear=plotendyear, fig=fig, **kwargs)
    allplots.update(epiplots)
    
    return allplots

def plotchangeinplhivallsources(results,which='change',showdata=False,die=None,fig=None,eps=1,verbose=2,**kwargs):
    changekeys = ['change', 'changeinplhivallsources', 'changeinplhivallsources-population+stacked', 'changeinplhivallsources-stacked']
    plhivkeys = ['plhiv', 'plhivallsources', 'plhivallsources-population+stacked', 'plhivallsources-stacked']
    validplottypes = ['population+stacked', 'stacked']
    defaultplottype = {'changeinplhivallsources': 'population+stacked', 'plhivallsources': 'stacked'}
    if which is None: return {}
    which = promotetolist(which)
    plots = odict()
    for thiswhich in which:
        splitkey = thiswhich.split('-')
        plottype = None
        if len(splitkey) == 2:
            plottype = splitkey[-1]
            plotname = splitkey[0]
        if (thiswhich not in changekeys and thiswhich not in plhivkeys) or \
                (plottype is not None and plottype not in validplottypes):
            errmsg = f"Unexpected plot type '{thiswhich}'. Was expecting one of {changekeys} or {plhivkeys}."
            if die: raise OptimaException(errmsg)
            printv(errmsg, 2, verbose)
            continue
        if plottype is None:
            if thiswhich in changekeys:
                plotname = 'changeinplhivallsources'
            elif thiswhich in plhivkeys:
                plotname = 'plhivallsources'
            plottype = defaultplottype[plotname]

        dataisestimate = False

        if plotname == 'changeinplhivallsources':
            scen = 0  # 0th is best
            numdeath = results.main['numdeath'].pops[scen]
            numimmiplhiv = results.other['numimmiplhiv'].pops[scen]

            propdeath = results.other['numotherdeath'].pops[scen] / results.main['popsize'].pops[scen]
            numotherhivdeath = propdeath * results.main['numplhiv'].pops[scen]

            if plottype == 'population+stacked':
                numincionpopbypop = results.other['numincionpopbypop'].pops[scen]
                numtransitpopbypop = results.other['numtransitpopbypop'].pops[scen]

                stackedabove = [[numimmiplhiv, numincionpopbypop, numtransitpopbypop]]
                stackedbelow = [[-swapaxes(numtransitpopbypop, axis1=0, axis2=1), -numdeath, -numotherhivdeath]]

                stackedabovelabels = [
                    [['Immigrant HIV+ in: ' + pk for pk in results.popkeys],
                     ['Infection from: ' + pk for pk in results.popkeys],
                     ['Transition in: ' + pk for pk in results.popkeys]]]
                stackedbelowlabels = [
                    [['Transition out: ' + pk for pk in results.popkeys],
                     ['HIV-related death: ' + pk for pk in results.popkeys],
                     ['Other death + emigration: ' + pk for pk in results.popkeys]]]

                plottitle = 'Change in PLHIV'
                showoverall = True
                numplhiv = results.main['numplhiv'].pops[scen]
                diff = numplhiv[:,1:]-numplhiv[:,:-1]
                data = concatenate((zeros((numplhiv.shape[0],1)), diff), axis=1)
                data = [data for i in range(3)]
            elif plottype == 'stacked':
                numinci = results.main['numinci'].pops[scen]

                stackedabove = [[numimmiplhiv.sum(axis=0), numinci]]
                stackedbelow = [[-numdeath.sum(axis=0), -numotherhivdeath.sum(axis=0)]]

                stackedabovelabels = [
                    [['Immigrant HIV+'],
                     ['Infection in: ' + pk for pk in results.popkeys] ] ]
                stackedbelowlabels = [
                     [['HIV-related death'],
                     ['Other death + emigration'] ] ]

                plottitle = 'Change in PLHIV'
                showoverall = True
                numplhiv = results.main['numplhiv'].tot[scen]
                diff = numplhiv[1:] - numplhiv[:-1]
                data = concatenate(([0], diff), axis=0)
                data = [data for i in range(3)]
        elif plotname == 'plhivallsources':
            scen = 0  # 0th is best
            numincionpopbypop = results.other['numincionpopbypop'].pops[scen]
            numtransitpopbypop = results.other['numtransitpopbypop'].pops[scen]
            numdeath = results.main['numdeath'].pops[scen]
            numimmiplhiv = results.other['numimmiplhiv'].pops[scen]

            numplhiv = results.main['numplhiv'].pops[scen]
            numplhivdata = results.main['numplhiv'].datatot
            newplhiv = numimmiplhiv + numincionpopbypop.sum(axis=1) + numtransitpopbypop.sum(axis=1) # Inflows of PLHIV to that compartment
            existingplhiv = numplhiv - newplhiv


            negexistingindices = logical_and(existingplhiv < 0, existingplhiv > -eps) # Negative existing often happen near the start of the simulation: due to plhiv being the cumulative effect and the others are annualised rates
            existingplhiv[negexistingindices] = 0

            propdeath = results.other['numotherdeath'].pops[scen] / results.main['popsize'].pops[scen]
            numotherhivdeath = propdeath * results.main['numplhiv'].pops[scen]

            if plottype == 'population+stacked':
                stackedabove = [[numimmiplhiv, numincionpopbypop, existingplhiv, numtransitpopbypop]]
                stackedbelow = [[-swapaxes(numtransitpopbypop, axis1=0, axis2=1), -numdeath, -numotherhivdeath]]

                data = results.main['numplhiv'].pops[scen]
                data = [data for i in range(3)]
                stackedabovelabels = [
                    [['Immigrant HIV+ in: ' + pk for pk in results.popkeys], ['Infection from: ' + pk for pk in results.popkeys],
                     ['PLHIV retained: ' + pk for pk in results.popkeys], ['Transition in: ' + pk for pk in results.popkeys] ]]
                stackedbelowlabels = [
                    [['Transition out: ' + pk for pk in results.popkeys], ['HIV-related death: ' + pk for pk in results.popkeys],
                     ['Other death + emigration: ' + pk for pk in results.popkeys]]]
                stackedabovecolors = [[None] * len(results.popkeys), [None] * len(results.popkeys),
                                      ]
            elif plottype == 'stacked':

                stackedabove = [[numimmiplhiv.sum(axis=0), numincionpopbypop.sum(axis=(0,1)), existingplhiv.sum(axis=0), numtransitpopbypop.sum(axis=(0,1))]]
                stackedbelow = [[-numdeath.sum(axis=0), -numotherhivdeath.sum(axis=0)]]

                data = results.main['numplhiv'].datatot[:,0,:]
                showdata = True
                dataisestimate = True
                stackedabovelabels = [
                    [['Immigrant HIV+'],
                     ['New infections'],
                     ['PLHIV retained'],
                     ['PLHIV transition b/w populations']] ]
                stackedbelowlabels = [
                    [['HIV-related death'],
                     ['Other death + emigration']] ]


            plottitle = 'Number of PLHIV'
            showoverall = False

        thisplots = plotstackedabovestackedbelow(results, toplot=[(plotname, plottype)], data=[data], showdata=showdata,
                                                 stackedabove=stackedabove, stackedbelow=stackedbelow, showoverall=showoverall,
                                                 stackedabovelabels=stackedabovelabels, stackedbelowlabels=stackedbelowlabels,
                                                 plottitles=[plottitle], die=die, fig=fig, **kwargs)
        plots.update(thisplots)

    return plots


def plotepi(results, toplot=None, uncertainty=True, die=True, showdata=True, verbose=2, figsize=globalfigsize, 
            alpha=0.2, lw=2, dotsize=30, titlesize=globaltitlesize, labelsize=globallabelsize, ticksize=globalticksize, 
            legendsize=globallegendsize, position=None, useSIticks=True, colors=None, reorder=None, plotstartyear=None, 
            plotendyear=None, interactive=None, fig=None, forreport=False, forceintegerxaxis=False, **kwargs):
        '''
        Render the plots requested and store them in a list. Argument "toplot" should be a list of form e.g.
        ['prev-tot', 'inci-pop']

        This function returns an odict of figures, which can then be saved as MPLD3, etc.
        
        NOTE: do not call this function directly; instead, call via plotresults().

        Version: 2017may22
        '''
        
        # Figure out what kind of result it is
        if type(results)==Resultset: ismultisim = False
        elif type(results)==Multiresultset and results.nresultsets == 1: ismultisim = False # A Multiresultset with only one Resultset can have stacked plots
        elif type(results)==Multiresultset:
            ismultisim = True
            labels = results.keys # Figure out the labels for the different lines
            nsims = len(labels) # How ever many things are in results
        else:
            errormsg = 'Results input to plotepi() must be either Resultset or Multiresultset, not "%s".' % type(results)
            raise OptimaException(errormsg)

        # Get year indices for producing plots
        startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die, verbose=verbose)
        
        # Initialize
        if toplot is None: # If toplot is None...
            toplot = getdefaultplots(ismulti=ismultisim) # ...get defaults...
            toremove = []
            for key in toplot: # ...then loop over them...
                if key.find('-')<0: 
                    toremove.append(key) # ...and collect keys that don't look like epi plots
            for key in toremove:
                toplot.remove(key) # Remove keys that don't look like epi plots -- note, can't do this in one loop :(
        toplot = promotetolist(toplot) # If single value, put inside list
        epiplots = odict()
        colorsarg = dcp(colors) # This is annoying, but it gets overwritten later and need to preserve it here

        ## Validate plot keys
        valid_plotkeys = results.main.keys() + results.other.keys() #['numincionpopbypop', 'numtransitpopbypop'] # allow all main keys + selected others
        for pk,plotkeys in enumerate(toplot):
            epikey = None # By default, don't make any assumptions
            plottype = 'stacked' # Assume stacked by default
            if type(plotkeys)!=str: 
                errormsg = 'Could not understand "%s": must a string, e.g. "numplhiv" or "numplhiv-stacked"' % str(plotkeys)
                raise OptimaException(errormsg)
            else:
                plotkeys = plotkeys.split('-') # Try splitting if it's a string, e.g. numplhiv-stacked
                epikey = plotkeys[0] # This must always exist, e.g. numplhiv
                if len(plotkeys)==2: plottype = plotkeys[1] # Use the one specified
                elif len(plotkeys)==1: # Otherwise, try to use the default
                    try: plottype = results.main[epikey].defaultplot # If it's just e.g. numplhiv, then use the default plotting type
                    except:
                        try: plottype = results.other[epikey].defaultplot
                        except:
                            errormsg = 'Unable to retrieve default plot type (total/population/stacked) for %s; falling back on %s'% (epikey,plottype)
                            if die: raise OptimaException(errormsg)
                            else: printv(errormsg, 2, verbose)
                else: # Give up
                    errormsg = 'Plotkeys must have length 1 or 2, but you have %s' % plotkeys
                    raise OptimaException(errormsg)
            if epikey not in valid_plotkeys:
                errormsg = 'Could not understand data type "%s"; should be one of:\n%s' % (epikey, valid_plotkeys)
                if die: raise OptimaException(errormsg)
                else: printv(errormsg, 2, verbose)
            if plottype not in epiplottypes: # Sum flattens a list of lists. Stupid.
                errormsg = 'Could not understand type "%s"; should be one of:\n%s' % (plottype, epiplottypes)
                if die: raise OptimaException(errormsg)
                else: printv(errormsg, 2, verbose)
            toplot[pk] = (epikey, plottype) # Convert to tuple for this index
        
        # Remove failed ones
        toplot = [thisplot for thisplot in toplot if None not in thisplot] # Remove a plot if datatype or plotformat is None

        # Check if the figure will be saved to insert into a presentation or report
        if forreport:
            forreport = True
            titlesize = 16
            labelsize = 14
        

        ################################################################################################################
        ## Loop over each plot
        ################################################################################################################
        for plotkey in toplot:
            
            # Unpack tuple
            datatype, plotformat = plotkey 

            # store result.main[datatype] as resultsmaindatatype, in order to allow selected other variables from results.other to be plotted
            if datatype in results.main.keys():
                resultsmaindatatype = results.main[datatype]
            else:
                resultsmaindatatype = results.other[datatype]

            ispercentage = resultsmaindatatype.ispercentage # Indicate whether result is a percentage
            isestimate = resultsmaindatatype.estimate # Indicate whether data is an estimate
            factor = 100.0 if ispercentage else 1.0 # Swap between number and percent
            datacolor = estimatecolor if isestimate else realdatacolor # Light grey for
            istotal   = (plotformat=='total')
            isstacked = (plotformat=='stacked')
            isperpop  = (plotformat=='population')
            isperpopandstacked = (plotformat == 'population+stacked')
            
            
            ################################################################################################################
            ## Process the plot data
            ################################################################################################################
            
            # Decide which attribute in results to pull -- doesn't map cleanly onto plot types
            if istotal or (isstacked and ismultisim): attrtype = 'tot' # Only plot total if it's a scenario and 'stacked' was requested
            else: attrtype = 'pops'
            if istotal or isstacked or isperpopandstacked: datattrtype = 'tot' # For pulling out total data
            else: datattrtype = 'pops'
            
            if ismultisim:  # e.g. scenario, no uncertainty
                best = list() # Initialize as empty list for storing results sets
                for s in range(nsims): best.append(getattr(resultsmaindatatype, attrtype)[s])
                lower = None
                upper = None
                databest = None
                uncertainty = False
            else: # Single results thing: plot with uncertainties and data
                best = getattr(resultsmaindatatype, attrtype)[0] # poptype = either 'tot' or 'pops'
                try: # If results were calculated with quantiles, these should exist
                    lower = getattr(resultsmaindatatype, attrtype)[1]
                    upper = getattr(resultsmaindatatype, attrtype)[2]
                except: # No? Just use the best estimates
                    lower = best
                    upper = best
                try: # Try loading actual data -- very likely to not exist
                    tmp = getattr(resultsmaindatatype, 'data'+datattrtype)
                    databest = tmp[0]
                    datalow = tmp[1]
                    datahigh = tmp[2]
                    if datatype in ['numincionpopbypop', 'numtransitpopbypop']: #because we are comparing numincionpopbypop to numinci, which has multiple possible resultsets
                        databest = databest[0] #take the first resultset for numinci as "data"
                        datalow = datalow[0]
                        datahigh = datahigh[0]
                except:# Don't worry if no data
                    databest = None
                    datalow = None
                    datahigh = None
            if not ismultisim and ndim(best)==1: # Wrap so right number of dimensions -- happens if not by population
                best  = array([best])
                lower = array([lower])
                upper = array([upper])
            
            
            ################################################################################################################
            ## Set up figure and do plot
            ################################################################################################################
            if isperpop or isperpopandstacked: pkeys = [str(plotkey)+'-'+key for key in results.popkeys] # Create list of plot keys (pkeys), one for each population
            else: pkeys = [plotkey] # If it's anything else, just go with the original, but turn into a list so can iterate
            
            for i,pk in enumerate(pkeys): # Either loop over individual population plots, or just plot a single plot, e.g. pk='prev-pop-FSW'
                
                epiplots[pk],naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig) # If it's anything other than HIV prevalence by population, create a single plot
                ax = epiplots[pk].add_subplot(naxes, 1, naxes)
                setposition(ax, position, interactive)
                allydata = [] # Keep track of the lowest value in the data
    
                if isstacked or ismultisim or isperpopandstacked: nlinesperplot = len(best) # There are multiple lines per plot for both pops poptype and for plotting multi results
                else: nlinesperplot = 1 # In all other cases, there's a single line per plot
                if colorsarg is None: colors = gridcolors(nlinesperplot) # This is needed because this loop gets run multiple times, so can't just set and forget
                

                ################################################################################################################
                # Plot model estimates with uncertainty -- different for each of the different possibilities
                ################################################################################################################
                
                xdata = results.tvec # Pull this out here for clarity
                
                # Make sure plots are in the correct order
                origorder = arange(nlinesperplot)
                plotorder = nlinesperplot-1-origorder
                if reorder: plotorder = [reorder[k] for k in plotorder]
                
                # e.g. single simulation, prev-tot: single line, single plot
                if not ismultisim and istotal:
                    ydata = factor*best[0]
                    allydata.append(ydata)
                    ax.plot(xdata, ydata, lw=lw, c=colors[0], zorder=linezorder) # Index is 0 since only one possibility
                
                # e.g. single simulation, prev-pop: single line, separate plot per population
                if not ismultisim and isperpop: 
                    ydata = factor*best[i]
                    allydata.append(ydata)
                    ax.plot(xdata, ydata, lw=lw, c=colors[0], zorder=linezorder) # Index is each individual population in a separate window
                
                # e.g. single simulation, prev-sta: either multiple lines or a stacked plot, depending on whether or not it's a number
                if not ismultisim and (isstacked or isperpopandstacked):
                    if ispercentage: # Multi-line plot
                        for k in plotorder:
                            ydata = factor*best[k]
                            allydata.append(ydata)
                            ax.plot(xdata, ydata, lw=lw, c=colors[k], zorder=linezorder, label=results.popkeys[k]) # Index is each different population
                    else: # Stacked plot
                        if isperpopandstacked:
                            beststored = dcp(best)
                            best = best[i]
                        bottom = 0*results.tvec # Easy way of setting to 0...
                        for k in plotorder: # Loop backwards so correct ordering -- first one at the top, not bottom
                            ylower = factor*bottom
                            yupper = factor*(bottom+best[k])
                            allydata.append(ylower)
                            allydata.append(yupper)
                            ax.fill_between(xdata, ylower, yupper, facecolor=colors[k], alpha=1, lw=0, label=results.popkeys[k], zorder=fillzorder)
                            bottom += best[k]
                        for l in range(nlinesperplot): # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly...
                            ax.plot((0, 0), (0, 0), color=colors[l], linewidth=10, zorder=linezorder)
                        if isperpopandstacked:
                            best = beststored
                
                # e.g. scenario, prev-tot; since stacked plots aren't possible with multiple lines, just plot the same in this case
                if ismultisim and (istotal or isstacked):
                    for l in range(nlinesperplot):
                        ind = nlinesperplot-1-l
                        thisxdata = results.setup[ind]['tvec']
                        ydata = factor*best[ind]
                        allydata.append(ydata)
                        ax.plot(thisxdata, ydata, lw=lw, c=colors[ind], zorder=linezorder, label=labels[l]) # Index is each different e.g. scenario
                
                if ismultisim and isperpop:
                    for l in range(nlinesperplot):
                        ind = nlinesperplot-1-l
                        thisxdata = results.setup[ind]['tvec']
                        ydata = factor*best[ind][i]
                        allydata.append(ydata)
                        ax.plot(thisxdata, ydata, lw=lw, c=colors[ind], zorder=linezorder, label=labels[l]) # Indices are different populations (i), then different e..g scenarios (l)



                ################################################################################################################
                # Plot data points with uncertainty
                ################################################################################################################
                
                # Plot uncertainty, but not for stacked plots
                if uncertainty and not isstacked and not isperpopandstacked: # It's not by population, except HIV prevalence, and uncertainty has been requested: plot bands
                    ylower = factor*lower[i]
                    yupper = factor*upper[i]
                    allydata.append(ylower)
                    allydata.append(yupper)
                    ax.fill_between(xdata, ylower, yupper, facecolor=colors[0], alpha=alpha, lw=0)
                    
                # Plot data points with uncertainty -- for total or perpop plots, but not if multisim
                if not ismultisim and databest is not None and showdata:
                    for y in range(len(results.datayears)):
                        ydata = factor*array([datalow[i][y], datahigh[i][y]])
                        allydata.append(ydata)
                        ax.plot(results.datayears[y]*array([1,1]), ydata, c=datacolor, lw=1)
                    ax.scatter(results.datayears, factor*databest[i], color=realdatacolor, s=dotsize, lw=0, zorder=datazorder) # Without zorder, renders behind the graph
                    if isestimate: # This is stupid, but since IE can't handle linewidths sensibly, plot a new point smaller than the other one
                        ydata = factor*databest[i]
                        allydata.append(ydata)
                        ax.scatter(results.datayears, ydata, color=estimatecolor, s=dotsize*0.6, lw=0, zorder=datazorder+1)



                
                ################################################################################################################
                # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
                ################################################################################################################
                
                # General configuration
                boxoff(ax)
                ax.yaxis.label.set_fontsize(labelsize)
                for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)
    
                # Configure plot specifics
                legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1,1), 'fontsize':legendsize, 'title':'', 'frameon':False, 'borderaxespad':2}
                plottitle = resultsmaindatatype.name
                if isperpop or isperpopandstacked:
                    plotylabel = plottitle
                    ax.set_ylabel(plotylabel)
                    try: plottitle = kwargs["popmapping"][results.popkeys[i]] # if popmapping was passed in as kwarg, use the title specified there for this population instead
                    except: plottitle = results.popkeys[i] # Add extra information to plot if by population
                    if forreport: ax.set_ylabel(plotylabel, fontsize=labelsize) # overwrites previously set ylabel
                ax.set_title(plottitle)
                if forreport:
                    ax.set_xlabel('Year', fontsize=labelsize)
                    ax.set_title(plottitle, fontsize=titlesize) # overwrites previously set title
                setylim(allydata, ax=ax)
                if forceintegerxaxis:
                    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
                ax.set_xlim((results.tvec[startind], results.tvec[endind]))
                if not ismultisim:
                    if isstacked or isperpopandstacked:
                        handles, legendlabels = ax.get_legend_handles_labels()
                        ax.legend(handles[::-1], legendlabels[::-1], **legendsettings) # Multiple entries, all populations
                else:
                    handles, legendlabels = ax.get_legend_handles_labels()
                    ax.legend(handles[::-1], legendlabels, **legendsettings) # Multiple simulations
                if useSIticks: SIticks(ax=ax)
                else:          commaticks(ax=ax)
        
        return epiplots





##################################################################
## Plot improvements
##################################################################
def plotimprovement(results=None, figsize=globalfigsize, lw=2, titlesize=globaltitlesize, labelsize=globallabelsize, ticksize=globalticksize, position=None, interactive=False, fig=None, **kwargs):
    ''' 
    Plot the result of an optimization or calibration -- WARNING, should not duplicate from plotepi()! 
    
    Accepts either a parset (generated from autofit) or an optimization result with a improvement attribute;
    failing that, it will try to treat the object as something that can be used directly, e.g.
        plotimprovement(results.improvement)
    also works.
    
    NOTE: do not call this function directly; instead, call via plotresults().
    
    Version: 2016jan23 
    '''

    if hasattr(results, 'improvement'): improvement = results.improvement # Get improvement attribute of object if it exists
    elif shape(results): improvement = results # Promising, has a length at least, but of course could still be wrong
    else: raise OptimaException('To plot the improvement, you must give either the improvement or an object containing the improvement as the first argument; try again')
    ncurves = len(improvement) # Try to figure to figure out how many there are
    
    # Set up figure and do plot
    sigfigs = 2 # Number of significant figures
    fig, naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig)
    ax = fig.add_subplot(naxes, 1, naxes)
    setposition(ax, position, interactive)
    colors = gridcolors(ncurves)
    
    # Plot model estimates with uncertainty
    absimprove = zeros(ncurves)
    relimprove = zeros(ncurves)
    maxiters = 0
    for i in range(ncurves): # Expect a list of 
        ax.plot(improvement[i], lw=lw, c=colors[i]) # Actually do the plot
        absimprove[i] = improvement[i][0]-improvement[i][-1]
        relimprove[i] = 100*(improvement[i][0]-improvement[i][-1])/improvement[i][0]
        maxiters = maximum(maxiters, len(improvement[i]))
    
    # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
    boxoff(ax)
    ax.title.set_fontsize(titlesize)
    ax.xaxis.label.set_fontsize(labelsize)
    for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)
    
    # Configure plot
    ax.set_xlabel('Iteration')
    abschange = sigfig(mean(absimprove), sigfigs)
    relchange = sigfig(mean(relimprove), sigfigs)
    ax.set_title('Change in outcome: %s (%s%%)' % (abschange, relchange)) # WARNING -- use mean or best?
    setylim(0, ax=ax)
    ax.set_xlim((0, maxiters))
    
    return fig






##################################################################
## Budget plot
##################################################################
    
    
def plotbudget(multires=None, die=True, figsize=globalfigsize, legendsize=globallegendsize, position=None,
               usepie=False, verbose=2, interactive=False, fig=None, **kwargs):
    ''' 
    Plot multiple allocations on bar or pie charts -- intended for scenarios and optimizations.

    Results object must be of Multiresultset type.
    
    Version: 2017oct29
    '''
    
    # Preliminaries: process inputs and extract needed data
    if type(multires)==Resultset: multires = Multiresultset([multires]) # Force it to be a multiresultset
    budgets = dcp(multires.budgets)
    for b,budget in enumerate(budgets.values()): # Loop over all budgets
        for p,prog in enumerate(budget.values()): # Loop over all programs in the budget
            if budgets[b][p] is not None:
                budgets[b][p] = mean(budgets[b][p]) # If it's over multiple years (or not!), take the mean
    for key in budgets.keys(): # Budgets is an odict
        for i,val in enumerate(budgets[key].values()):
            if isnan(val) or not val: 
                budgets[key][i] = 0.0 # Turn None, nan, etc. into 0.0 -- note that val>0 is no longer valid in Python 3!
    
    alloclabels = budgets.keys() # WARNING, will this actually work if some values are None?
    allprogkeys = [] # Create master list of all programs in all budgets
    nprogslist = []
    for budget in budgets.values():
        nprogslist.append(len(budget.keys())) # Get the number of programs in this budget
        for key in budget.keys():
            if key not in allprogkeys:
                allprogkeys.append(key)
    nallprogs = len(allprogkeys)
    nallocs = len(alloclabels)
    allprogcolors = gridcolors(nallprogs, hueshift=proghueshift)
    colordict = odict()
    for k,key in enumerate(allprogkeys):
        colordict[key] = allprogcolors[k]
    
    # Handle plotting
    budgetplots = odict()
    fig, naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig)
    ax = fig.add_subplot(naxes, 1, naxes)
    
    # Make pie plots
    if usepie:
        for i in range(nallocs):
            # Make a pie
            setposition(ax, position, interactive)
            ydata = budgets[i][:]
            piecolors = [colordict[key] for key in budgets[i].keys()]
            ax.pie(ydata, colors=piecolors)
            
            # Set up legend
            labels = dcp(allprogkeys)
            labels.reverse() # Wrong order otherwise, don't know why
            legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
            ax.legend(labels, **legendsettings) # Multiple entries, all populations
            
            budgetplots['budget-%s'%i] = fig
      
    # Make bar plots
    else:
        if position == globalposition: # If defaults, reset
            position = dcp(position)
            position[0] = 0.25 # More room on left side for y-tick labels
            position[2] = 0.5 # Make narrower
        setposition(ax, position, interactive)
        
        # Need to build up piece by piece since need to loop over budgets and then budgets
        for b,budget in enumerate(budgets.values()):
            for p in range(nprogslist[b]-1,-1,-1): # Loop in reverse order over programs
                progkey = budget.keys()[p]
                ydata = budget[p]
                xdata = b+0.6 # 0.6 is 1 minus 0.4, which is half the bar width
                bottomdata = sum(budget[:p])
                label = None
                if progkey in allprogkeys:
                    label = progkey # Only add legend if not already added
                    allprogkeys.remove(progkey) # Pop label so it doesn't get added to legend multiple times
                ax.barh(xdata, ydata, left=bottomdata, color=colordict[progkey], linewidth=0, label=label)
    
        # Set up legend
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.07, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
        handles, legendlabels = ax.get_legend_handles_labels()
        ax.legend(reversed(handles), reversed(legendlabels), **legendsettings)
    
        # Set up other things
        ax.set_xlabel('Spending')
        ax.set_yticks(arange(nallocs)+1)
        ax.set_yticklabels(alloclabels)
        ax.set_ylim(0,nallocs+1)
        ax.set_title('Budget')
        
        SIticks(ax=ax, axis='x')
        budgetplots['budget'] = fig
    
    return budgetplots



def plottvbudget(multires=None, die=True, figsize=globalfigsize, legendsize=globallegendsize, position=None,
               usepie=False, verbose=2, interactive=False, fig=None, **kwargs):
    ''' 
    Plot time-varying budget.
    
    Version: 2017oct29
    '''
    
    # Preliminaries: process inputs and extract needed data
    if type(multires)==Resultset: multires = Multiresultset([multires]) # Force it to be a multiresultset
    tv = multires.timevarying[-1] # Have to choose one -- assume it will be the last one
    tvyears  = tv['tvyears']
    progkeys = tv['tvbudgets'].keys()
    tvdata   = tv['tvbudgets'][:]
    nprogs = len(progkeys)
    allprogcolors = gridcolors(nprogs, hueshift=proghueshift)
    colordict = odict()
    for k,key in enumerate(progkeys):
        colordict[key] = allprogcolors[k]
    
    # Handle plotting
    tvbudgetplots = odict()
    fig, naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig)
    ax = fig.add_subplot(naxes, 1, naxes)
    setposition(ax, position, interactive)
    
    # Need to build up piece by piece since need to loop over budgets and then budgets
    legendkeys = []
    for y,year in enumerate(tvyears):
        for p in range(nprogs-1,-1,-1): # Loop in reverse order over programs
            progkey = progkeys[p]
            ydata = tvdata[p,y]
            xdata = year - 0.4
            bottomdata = sum(tvdata[:p,y])
            label = None
            if progkey not in legendkeys:
                label = progkey # Only add legend if not already added
                legendkeys.append(progkey) # Add label so it doesn't get added to legend multiple times
            ax.bar(xdata, ydata, bottom=bottomdata, color=colordict[progkey], linewidth=0, label=label)

    # Set up legend
    legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.07, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
    handles, legendlabels = ax.get_legend_handles_labels()
    ax.legend(handles, legendlabels, **legendsettings)

    # Set up other things
    ax.set_ylabel('Spending')
#    ax.set_xticks([1,nyears])
#    ax.set_xticklabels(['%i'%i for i in tvyears[[0,-1]]])
    ax.set_xlim(tvyears[0]-1,tvyears[-1]+1) # 0.6 is 1 minus 0.4, which is half the bar width
    ax.set_title('Time-varying budget')
    
    SIticks(ax=ax, axis='y')
    tvbudgetplots['tvbudget'] = fig
    
    return tvbudgetplots








##################################################################
## Coverage plot
##################################################################
    
    
def plotcoverage(multires=None, die=True, figsize=globalfigsize, legendsize=globallegendsize, position=None, verbose=2, interactive=False, fig=None, **kwargs):
    ''' 
    Plot multiple allocations on bar charts -- intended for scenarios and optimizations.

    Results object must be of Multiresultset type.
    
    Version: 2017mar09
    '''
    
    # Preliminaries: process inputs and extract needed data
    coverages = dcp(multires.coverages)
    toplot = [item for item in coverages.values() if item] # e.g. [budget for budget in multires.budget]
    budgetyearstoplot = [budgetyears for budgetyears in multires.budgetyears.values() if budgetyears]
    
    progkeylists = []
    for tp in toplot:
        progkeylists.append(tp.keys()) # A list of key lists
    alloclabels = [key for k,key in enumerate(coverages.keys()) if coverages.values()[k]] # WARNING, will this actually work if some values are None?
    nallocs = len(alloclabels)
    nprogslist = []
    for progkeylist in progkeylists:
        nprogslist.append(len(progkeylist))
    
    ax = []
    ymin = 0
    ymax = 0
    coverageplots = odict()
    
    for plt in range(nallocs):
        
        currfig, naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig)
        ax.append(currfig.add_subplot(naxes, 1, naxes))
        setposition(ax[-1], position, interactive)
        
        nprogs = nprogslist[plt]
        proglabels = progkeylists[plt]
        colors = gridcolors(nprogs, hueshift=proghueshift)
        nbudgetyears = len(budgetyearstoplot[plt])
        barwidth = .5/nbudgetyears
        for y in range(nbudgetyears):
            progdata = zeros(len(toplot[plt]))
            for i,x in enumerate(toplot[plt][:]):
                if hasattr(x, '__len__'): 
                    try: progdata[i] = x[y]
                    except:# TODO: May break in some circumstances
                        try: progdata[i] = x[-1] # If not enough data points, just use last 
                        except: progdata[i] = 0. 
                else:                     progdata[i] = x
            # progdata *= 100   # I think this line was a remnant from coverage % but this function now plots number covered not % coverage
            xbardata = arange(nprogs)+.75+barwidth*y
            for p in range(nprogs):
                if nbudgetyears>1: barcolor = colors[y] # More than one year? Color by year
                else: barcolor = colors[p] # Only one year? Color by program
                if p==nprogs-1: yearlabel = budgetyearstoplot[plt][y]
                else: yearlabel=None
                ax[-1].bar([xbardata[p]], [progdata[p]], label=yearlabel, width=barwidth, color=barcolor, linewidth=0)
        if nbudgetyears>1: ax[-1].legend(frameon=False)
        ax[-1].set_xticks(arange(nprogs)+1)
        ax[-1].set_xticklabels('')
        ax[-1].set_xlim(0,nprogs+1)
        
        ylabel = 'Coverage'
        ax[-1].set_ylabel(ylabel)
         
        if nallocs>1: thistitle = 'Coverage' % alloclabels[plt]
        else:         thistitle = 'Program coverage'
        ax[-1].set_title(thistitle)
        ymin = min(ymin, ax[-1].get_ylim()[0])
        ymax = max(ymax, ax[-1].get_ylim()[1])
        
        # Set up legend
        labels = dcp(proglabels)
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
        ax[-1].legend(labels, **legendsettings) # Multiple entries, all populations
        
        # Tidy up
        SIticks(ax=ax)
        coverageplots[thistitle] = currfig  # if fig=None, like it normally is (except gui),
                                            # then coverageplots is an odict of figures, each with only one subplot
    
    for thisax in ax: thisax.set_ylim(ymin,ymax) # So they all have the same scale
    
    return coverageplots











##################################################################
## Plot cascade
##################################################################
def plotcascade(results=None, aspercentage=False, cascadecolors=None, figsize=globalfigsize, lw=2, titlesize=globaltitlesize, 
                labelsize=globallabelsize, ticksize=globalticksize, legendsize=globallegendsize, position=None, useSIticks=True, 
                showdata=True, dotsize=50, plotstartyear=None, plotendyear=None, die=False, verbose=2, interactive=False, fig=None,
                asbars=False, allbars=True, blhind=None, newfig=None, targets=None, titlesuffix=None, **kwargs):

    ''' 
    Plot the treatment cascade.
    
    NOTE: do not call this function directly; instead, call via plotresults() using 'cascade' or 'cascadebars'.
    
    Example to show two bars for 2017 and 2020:
        import optima as op
        P = op.demo(0)
        op.plotresults(P, toplot='cascadebars', plotstartyear=2017, plotendyear=2020)
    
    Params:
        targets = 90 or 95 or any other % or a list of 3 strings eg: ['90%','81%','73%']
    '''
    
    # Set defaults
    if blhind is None: blhind = 0 # Just plot best for now - TODO, add errorbars
    
    # Figure out what kind of result it is
    if type(results)==Resultset: 
        ismultisim = False
        nsims = 1
    elif type(results)==Multiresultset:
        ismultisim = True
        titles = results.keys # Figure out the labels for the different lines
        nsims = len(titles) # How ever many things are in results
    else: 
        errormsg = 'Results input to plotcascade() must be either Resultset or Multiresultset, not "%s".' % type(results)
        raise OptimaException(errormsg)
        
    # Set up figure and do plot
    cascadeplots = odict()
    if asbars:
        if allbars: # Reset cascade labels for bar plot if plotting all bars
            casclabels  = ['PLHIV', 'Diagnosed', 'Linked', 'Retained', 'Treated', 'Suppressed']
            casckeys    = ['numplhiv',  'numdiag',  'numevercare', 'numincare', 'numtreat','numsuppressed']
        else:
            casclabels  = ['PLHIV', 'Diagnosed', 'Treated', 'Suppressed']
            casckeys    = ['numplhiv',  'numdiag', 'numtreat','numsuppressed']
        ncategories = len(casclabels)
        darken = array([1.0, 1.3, 1.3]) # Amount by which to darken succeeding cascade stages -- can't use 0.2 since goes negative!!
        targetcolor   = array([0,0,0])
        origbasecolor = array([0.5,0.60,0.9])
        origendcolor  = array([0.3,0.85,0.6])
        if plotendyear   is None: plotendyear   = results.tvec[-1]
        if plotstartyear is not None:
            startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die, verbose=verbose) # Get year indices for producing plots
        else:
            try: # Try making a plot with the last year of treatment data as the first year
                plotstartyear = results.pars['numtx'].t['tot'][-1]
                startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die, verbose=verbose) # Get year indices for producing plots
            except: # The above options won't work if, for example, the last year of treatment data is greater than or equal to the last sim year, so in that case we use alternative defaults
                plotstartyear = results.tvec[0]
                startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die, verbose=verbose) # Get year indices for producing plots

        cascinds = [startind, endind]
        baselabel = '%4i' % plotstartyear
        endlabel  = '%4i' % plotendyear
        if baselabel==endlabel: endlabel += ' ' # Small hack to avoid bug if both are the same
        labels = [baselabel, endlabel]
        casccolors = odict([(baselabel,[origbasecolor]), (endlabel, [origendcolor])])

        if targets is None: pass
        elif len(promotetoarray(targets)) == 3:
            target_strs = [str(target)+'%' if not isinstance(target,str) else target for target in targets] # If its an array of numbers, add a %
        elif len(promotetoarray(targets)) == 1:
            try:
                targets = float(promotetoarray(targets)[0])
                targets = targets*100 if targets < 1 else targets
                target_strs = [f'{int(targets**i/(100**i)*100)}%' for i in range(1,4)]
            except: targets = None
        else: targets = None

        if targets == None: target_strs = ['95%', '90%', '86%']  # Default to 95-95-95
        targets = [float(s[:-1]) if s.endswith('%') else float(s) for s in target_strs]
            
        for k in range(len(casckeys)-1):
            for label in casccolors.keys():
                darker = dcp(casccolors[label][-1]**darken) # Make each color slightly darker than the one before
                casccolors[label].append(darker)

    else:
        # Get year indices for producing plots
        startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die, verbose=verbose)
        cascadelist = ['numplhiv', 'numdiag', 'numevercare', 'numincare', 'numtreat', 'numsuppressed'] 
        cascadenames = ['Undiagnosed', 'Diagnosed', 'Linked to care', 'Retained in care', 'Treated', 'Virally suppressed']
            
        # Handle colors
        defaultcascadecolors = odict([ # Based on https://www.aids.gov/federal-resources/policies/care-continuum/
            ('undx',  [0.71, 0.26, 0.24]),
            ('dx',    [0.39, 0.48, 0.13]),
            ('care',  [0.49, 0.68, 0.23]),
            ('retain',[0.59, 0.78, 0.33]),
            ('unsupp',[0.38, 0.52, 0.64]),
            ('supp',  [0.43, 0.29, 0.62]),
            ]).reversed() # Colors get called in opposite order
        if cascadecolors is None:      colors = defaultcascadecolors[:]
        elif cascadecolors=='grid':    colors = gridcolors(len(cascadelist), reverse=True)
        elif cascadecolors=='alpine':  colors = vectocolor(arange(len(cascadelist)), cmap=alpinecolormap()) # Handle this as a special case
        elif type(cascadecolors)==str: colors = vectocolor(arange(len(cascadelist)+2), cmap=cascadecolors)[1:-1] # Remove first and last element
        else: colors = cascadecolors
    
    # Actually do the plotting
    for plt in range(nsims): # WARNING, copied from plotallocs()
    
        # Create the figure and axes
        currfig,naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig, newfig=newfig)
        ax = currfig.add_subplot(naxes, 1, naxes)
        setposition(ax, position, interactive)
            
        if asbars:
            dx = 1.0
            space = 4.0
            basex = arange(ncategories)*space
            for k,key in enumerate(casckeys):
                for i,ind in enumerate(cascinds):
                    if ismultisim:  # WARNING, is this needed?
                        thisbar = 100.*results.main[key].tot[plt][ind]/results.main['numplhiv'].tot[plt][ind] # If it's a multisim, need an extra index for the plot number
                    else:
                        thisbar = 100.*results.main[key].tot[0][ind]/results.main['numplhiv'].tot[0][ind] # Get the best estimate
                    if k==len(casckeys)-1: label = labels[i]
                    else:                  label = None
                    ax.bar(basex[k]+i*dx, thisbar, width=1., color=casccolors[i][k], linewidth=0, label=label)
            
            targetxpos = 2.0 # Length of the horizontal bar
            labelxpos  = 2.6 # Relative x position of the label
            labelypos = -1.5  # Relative y position of the label
            lineargs = {'c':targetcolor, 'linewidth':2}
            txtargs = {'fontsize':legendsize, 'color':targetcolor, 'horizontalalignment':'center'}
            dxind  = casckeys.index('numdiag')
            txind  = casckeys.index('numtreat')
            supind = casckeys.index('numsuppressed')
            ax.plot([basex[dxind]-0.5, basex[dxind]+targetxpos-0.5],   [targets[0],targets[0]], **lineargs)
            ax.plot([basex[txind]-0.5, basex[txind]+targetxpos-0.5],   [targets[1],targets[1]], **lineargs)
            ax.plot([basex[supind]-0.5, basex[supind]+targetxpos-0.5], [targets[2],targets[2]], **lineargs)

            ax.text(basex[dxind]+labelxpos,targets[0]+labelypos,target_strs[0], **txtargs)
            ax.text(basex[txind]+labelxpos,targets[1]+labelypos,target_strs[1], **txtargs)
            ax.text(basex[supind]+labelxpos,targets[2]+labelypos,target_strs[2], **txtargs)
            
            ax.set_xticks(basex+1.0)
            ax.set_xticklabels(casclabels)
            ax.set_ylabel('Percentage of PLHIV')
            ax.set_xlim((basex[0]-1,basex[-1]+space))
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')
            if titlesuffix is None: titlesuffix = ''
            if ismultisim: thistitle = 'Care cascade - %s' % titles[plt] + titlesuffix
            else:          thistitle = 'Care cascade' + titlesuffix
        
        else: # Not bars
            bottom = 0*results.tvec # Easy way of setting to 0...
            for k,key in enumerate(reversed(cascadelist)): # Loop backwards so correct ordering -- first one at the top, not bottom
                if ismultisim: 
                    thisdata = results.main[key].tot[plt] # If it's a multisim, need an extra index for the plot number
                    if aspercentage: thisdata *= 100./results.main['numplhiv'].tot[plt]
                else:
                    thisdata = results.main[key].tot[0] # Get the best estimate
                    if aspercentage: thisdata *= 100./results.main['numplhiv'].tot[0]
                ax.fill_between(results.tvec, bottom, thisdata, facecolor=colors[k], alpha=1, lw=0)
                bottom = dcp(thisdata) # Set the bottom so it doesn't overwrite
                ax.plot((0, 0), (0, 0), color=colors[len(colors)-k-1], linewidth=10, label=cascadenames[k]) # Colors are in reverse order
            if showdata and not aspercentage: # Don't try to plot if it's a percentage
                thisdata = results.main['numtreat'].datatot[0]
                ax.scatter(results.datayears, thisdata, c=(0,0,0), s=dotsize, lw=0)
            
            # Configure rest of the plot
            if aspercentage: ax.set_ylabel('Percentage of PLHIV')
            else:            ax.set_ylabel('Number of PLHIV')
                    
            if aspercentage: ax.set_ylim((0,100))
            else:            setylim(0, ax)
            ax.set_xlim((results.tvec[startind], results.tvec[endind]))
            
            if ismultisim: thistitle = 'Cascade - %s' % titles[plt]
            else:          thistitle = 'Cascade'
            
        ## General plotting fixes
        if useSIticks: SIticks(ax=ax)
        else:          commaticks(ax=ax)
        
        ## Configure plot -- WARNING, copied from plotepi()
        boxoff(ax)
        ax.title.set_fontsize(titlesize)
        ax.xaxis.label.set_fontsize(labelsize)
        ax.yaxis.label.set_fontsize(labelsize)
        for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)
        
        # Configure legend
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False, 'scatterpoints':1}
        ax.legend(**legendsettings) # Multiple entries, all populations
            
        ax.set_title(thistitle)
        cascadeplots[thistitle] = currfig
        
    return cascadeplots



def plotallocations(project=None, budgets=None, colors=None, factor=1e6, compare=True, plotfixed=False, interactive=False, **kwargs):
    ''' Plot allocations in bar charts -- not part of weboptima '''
    
    if budgets is None:
        try: budgets = project.results[-1].budget
        except: budgets = project # Maybe first argument is budget
    
    labels = budgets.keys()
    progs = budgets[0].keys()
    
    indices = None
    if not plotfixed:
        try: indices = findinds(project.progset().optimizable()) # Not possible if project not defined
        except: pass
    if indices is None: indices = arange(len(progs))
    nprogs = len(indices)
    progs = [progs[i] for i in indices] # Trim programs
    
    if colors is None:
        colors = gridcolors(nprogs)
            
    
    fig,naxes = makefigure(figsize=(10,10), interactive=interactive)
    fig.subplots_adjust(left=0.10) # Less space on left
    fig.subplots_adjust(right=0.98) # Less space on right
    fig.subplots_adjust(top=0.95) # Less space on bottom
    fig.subplots_adjust(bottom=0.35) # Less space on bottom
    fig.subplots_adjust(wspace=0.30) # More space between
    fig.subplots_adjust(hspace=0.40) # More space between
    
    ax = []
    xbardata = arange(nprogs)+0.5
    ymin = 0
    ymax = 0
    nplt = len(budgets)
    for plt in range(nplt):
        ax.append(fig.add_subplot(naxes+len(budgets)-1,1,naxes+plt))
        for p,ind in enumerate(indices):
            ax[-1].bar([xbardata[p]], [budgets[plt][ind]/factor], color=colors[p], linewidth=0)
            if plt==1 and compare:
                ax[-1].bar([xbardata[p]], [budgets[0][ind]/factor], color='None', linewidth=1)
        ax[-1].set_xticks(arange(nprogs)+1)
        if plt!=nplt: ax[-1].set_xticklabels('')
        if plt==nplt-1: 
            ax[-1].set_xticklabels(progs,rotation=90)
            ax[-1].plot([0,nprogs+1],[0,0],c=(0,0,0))
        ax[-1].set_xlim(0,nprogs+1)
        
        if factor==1:     ax[-1].set_ylabel('Spending (US$)')
        elif factor==1e3: ax[-1].set_ylabel("Spending (US$'000s)")
        elif factor==1e6: ax[-1].set_ylabel('Spending (US$m)')
        ax[-1].set_title(labels[plt])
        ymin = min(ymin, ax[-1].get_ylim()[0])
        ymax = max(ymax, ax[-1].get_ylim()[1])
    for a in ax:
        a.set_ylim([ymin,ymax])
    
    return fig


############################################################################################################
## Plot infections from each population and transitions of PLHIV to and from each population
############################################################################################################
def plotstackedabovestackedbelow(results, toplot=None, stackedabove=None, stackedbelow=None, showoverall=None,
                                 stackedabovelabels=None, stackedbelowlabels=None, plottitles=None, data=None, dataisestimate=True,
                                 uncertainty=True, die=True, showdata=True, eps=0.01, verbose=2, figsize=globalfigsize,
                                 alpha=0.2, lw=2, dotsize=30, titlesize=globaltitlesize, labelsize=globallabelsize,
                                 ticksize=globalticksize,
                                 legendsize=globallegendsize, position=None, useSIticks=True, colors=None, reorder=None,
                                 plotstartyear=None,
                                 plotendyear=None, interactive=None, fig=None, forreport=False, forceintegerxaxis=False, **kwargs):
        '''
        Used for plots which have multiple things stacked above and below the x-axis. The overall height of the
        positive stack and the height of the negative stack can be subtracted and plotted through the showoverall.

        At the moment it is designed for 'changeinplhivallcauses' with 'population+stacked' plottype.

        Could theoretically plot a single plot not split by population ie 'stacked' but I haven't tested -
        it may need to be modified / fixed.

        This function cannot extract the results itself, you must pass them in through stackedabove and stackedbelow

        WARNING copied from plotepi() optima version 2.10.13, commit: a3062175a5550b87edb55fba0f74072bdfa4bebe
        with some things REMOVED and a lot changed
        NOTE: do not call this function directly; instead, call via plotresults().

        :param: toplot: list of tuples of the form (plotname, plottype), the length defines the number of main plots.
        :param: stackedabove: follow the shape given by the implementation in makeplots but should have length=len(toplot)

        population+stacked: data: (k,3,npops,npts)  For the 3: 0 best, 1 low, 2 high
        stacked:            data: (k,3,npts)        For the 3: 0 best, 1 low, 2 high
        '''

        # Figure out what kind of result it is
        if type(results) == Resultset:
            ismultisim = False
        elif type(results)==Multiresultset and results.nresultsets == 1: ismultisim = False # A Multiresultset with only one Resultset can have stacked plots
        elif type(results) == Multiresultset:  # not implemented at the moment
            errormsg = 'Results input to plotfulltransandinfections() must be Resultset, not "%s".' % type(results)
            raise OptimaException(errormsg)

            # ismultisim = True
            # labels = results.keys  # Figure out the labels for the different lines
            # nsims = len(labels)  # How ever many things are in results
        else:
            errormsg = 'Results input to plotbymethod() must be Resultset, not "%s".' % type(results)
            raise OptimaException(errormsg)

        # Get year indices for producing plots
        startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die, verbose=verbose)

        # This function must have toplot given
        if toplot is None:
            errormsg = 'toplot was None for plotstackedabovestackedbelow() so could not continue.'
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 2, verbose)
                return

        # Initialize
        if stackedabove is None and stackedbelow is None:
            errormsg = 'stackedabove was None and stackedbelow was None for plotstackedabovestackedbelow() so could not continue.'
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 2, verbose)
                return

        toplot = promotetolist(toplot)  # If single value, put inside list
        epiplots = odict()
        colorsarg = dcp(colors)  # This is annoying, but it gets overwritten later and need to preserve it here

        if showoverall is None:
            showoverall = True

        if stackedabovelabels is None:
            stackedabovelabels = [None]*len(stackedabove)
        if stackedbelowlabels is None:
            stackedbelowlabels = [None]*len(stackedbelow)

        # ## Validate plot keys
        ## REMOVED -- validate keys outside of calling this function

        # Remove failed ones

        toplot = [thisplot for thisplot in toplot if None not in thisplot]  # Remove a plot if datatype or plotformat is None

        # Check if the figure will be saved to insert into a presentation or report
        if forreport:
            forreport = True
            titlesize = 16
            labelsize = 14

        ################################################################################################################
        ## Loop over each plot
        ################################################################################################################
        for mainplotindex, plotkey in enumerate(toplot): # probably only works if toplot contains one item
            # Unpack tuple
            datatype, plotformat = plotkey

            ispercentage = False  # Indicate whether result is a percentage
            #dataisestimate = False  # Indicate whether data is an estimate
            factor = 100.0 if ispercentage else 1.0  # Swap between number and percent
            datacolor = estimatecolor if dataisestimate else realdatacolor  # Light grey for
            # istotal = (plotformat == 'total') # only stacked or population+stacked implemented
            isstacked = (plotformat == 'stacked')
            # isperpop = (plotformat == 'population') # only stacked or population+stacked implemented
            isperpopandstacked = (plotformat == 'population+stacked')

            ################################################################################################################
            ## Process the plot data
            ################################################################################################################

            # REMOVED, too hard to process multiple sources of data within this function,
            # data is passed in through stackedabove and stackedbelow


            ################################################################################################################
            ## Set up figure and do plot
            ################################################################################################################
            if isperpopandstacked:
                pkeys = [str(plotkey) + '-' + key for key in
                         results.popkeys]  # Create list of plot keys (pkeys), one for each population
            else:
                pkeys = [plotkey]  # If it's anything else, just go with the original, but turn into a list so can iterate

            if stackedabovelabels[mainplotindex] is None:
                print(f'Warning stackedabovelabels[{mainplotindex}] is None. This will probably cause the labels to not be right.')
                stackedabovelabels[mainplotindex] = [[key for key in
                                       results.popkeys] for above in range(len(stackedabove[mainplotindex]))]  # Assume one for each population

            if stackedbelowlabels[mainplotindex] is None:
                print(f'Warning stackedbelowlabels[{mainplotindex}] is None. This will probably cause the labels to not be right.')
                stackedbelowlabels[mainplotindex] = [[key for key in
                                       results.popkeys] for below in range(len(stackedbelow[mainplotindex]))]  # Assume one for each population

            for i, pk in enumerate(pkeys):  # Either loop over individual population plots, or just plot a single plot, e.g. pk='prev-pop-FSW'
                epiplots[pk], naxes = makefigure(figsize=figsize, interactive=interactive, fig=fig)  # If it's anything other than HIV prevalence by population, create a single plot
                ax = epiplots[pk].add_subplot(naxes, 1, naxes)
                setposition(ax, position, interactive)
                allydata = []  # Keep track of the lowest value in the data

                if isperpopandstacked:
                    currentstackedabove = concatenate(tuple(arr[i] if len(arr.shape)==3 else [arr[i]] for arr in stackedabove[mainplotindex]), axis=0)
                    currentstackedbelow = concatenate(tuple(arr[i] if len(arr.shape)==3 else [arr[i]] for arr in stackedbelow[mainplotindex]), axis=0)
                    currentlabelsabove = concatenate(tuple(arr if len(stackedabove[mainplotindex][j].shape)==3 else [arr[i]] for j,arr in enumerate(stackedabovelabels[mainplotindex])), axis=0)
                    currentlabelsbelow = concatenate(tuple(arr if len(stackedbelow[mainplotindex][j].shape)==3 else [arr[i]] for j,arr in enumerate(stackedbelowlabels[mainplotindex])), axis=0)
                else: # only stacked
                    currentstackedabove = concatenate(tuple(arr if len(arr.shape)==2 else arr[newaxis,:] for arr in stackedabove[mainplotindex]), axis=0)
                    currentstackedbelow = concatenate(tuple(arr if len(arr.shape)==2 else arr[newaxis,:] for arr in stackedbelow[mainplotindex]), axis=0)
                    currentlabelsabove = concatenate(tuple(arr for arr in stackedabovelabels[mainplotindex]), axis=0)
                    currentlabelsbelow = concatenate(tuple(arr for arr in stackedbelowlabels[mainplotindex]), axis=0)

                nlinesabove = shape(currentstackedabove)[0]
                nlinesbelow = shape(currentstackedbelow)[0]

                ################################################################################################################
                ## Validate the plot data
                ################################################################################################################

                for ir,row in enumerate(currentstackedabove):
                    if not (row >= 0).all():
                        if (row <= 0).all():
                            print(f'WARNING with plot {plotkey} in plotstackedabovestackedbelow(): row in stackedabove are all non-positive - should be all non-negative')
                            print('Flipping them all to be positive')
                            currentstackedabove[ir] = - row
                        else:
                            if max(abs(row[row<0])) / max(abs(currentstackedabove).sum(axis=0)) < eps:
                                row[row<0] = 0
                            else:
                                print(f'WARNING with plot {plotkey} in plotstackedabovestackedbelow(): row in stackedabove aren\'t all >=0. This shouldn\'t happen - check your inputs.')
                                print(row)

                    for ir,row in enumerate(currentstackedbelow):
                        if not (row <= 0).all():
                            if (row >= 0).all():
                                print(f'WARNING with plot {plotkey} in plotstackedabovestackedbelow(): row in stackedbelow are all non-negative - should be all non-positive')
                                print('Flipping them all to be negative')
                                currentstackedbelow[ir] = - row
                            else:
                                if max(abs(row[row>0])) / max(abs(currentstackedbelow).sum(axis=0)) < eps: # If the positives are less than 1% of the overall negatives
                                    row[row>0] = 0
                                else:
                                    print(f'WARNING with plot {plotkey} in plotstackedabovestackedbelow(): row in stackedbelow aren\'t all <=0. This shouldn\'t happen - check your inputs.')
                                    print(row)
                ################################################################################################################
                # Plot model estimates with uncertainty -- different for each of the different possibilities
                ################################################################################################################

                xdata = results.tvec  # Pull this out here for clarity

                plotorderabove = []
                origorderabove = arange(nlinesabove)
                plotorderbelow = []
                origorderbelow = arange(nlinesbelow)

                for k in flip(origorderbelow):  # Loop backwards so correct ordering -- first one at the top, not bottom
                    if not (currentstackedbelow[k] > -eps).all():
                        plotorderbelow.append(k)
                for k in flip(origorderabove):  # Loop backwards so correct ordering -- first one at the top, not bottom
                    if not (currentstackedabove[k] < eps).all():
                        plotorderabove.append(k)

                origorderbelow = flip(plotorderbelow)
                origorderabove = flip(plotorderabove)

                nlinesbelow = len(origorderbelow)
                nlinesabove = len(origorderabove)

                if colorsarg is None:
                    if nlinesabove + nlinesbelow <= 8:  # number of colorbrewercolors
                          colors = gridcolors(nlinesabove + nlinesbelow)[:]
                    else: colors = gridcolors(nlinesabove + nlinesbelow+2)[2:]  # skip black and white
                # print(nlinesabove + nlinesbelow)
                # print([tuple(c*255 for c in col) for col in colors])
                # if reorder: plotordermethod = [reorder[k] for k in plotorder]


                # e.g. single simulation, prev-sta: either multiple lines or a stacked plot, depending on whether or not it's a number
                if not ismultisim and (isstacked or isperpopandstacked):  # Always in here
                    if ispercentage:  # Not implemented here, relic from plotepi()
                        pass
                    else:  # Stacked plot
                        bottom = 0 * results.tvec  # Easy way of setting to 0...

                        # go to the very bottom
                        for k in origorderbelow:
                            yupper = factor * bottom
                            ylower = factor * (bottom + currentstackedbelow[k]) #stacked below should all be negative or 0
                            bottom += currentstackedbelow[k]
                        bottombottom = dcp(bottom)

                        # from the bottom, work upwards
                        for indexcolour, k in enumerate(plotorderbelow):  # Loop backwards so correct ordering -- first one at the top, not bottom
                            yupper = factor * bottom
                            ylower = factor * (bottom - currentstackedbelow[k]) #stacked below should all be negative or 0
                            allydata.append(ylower)
                            allydata.append(yupper)
                            ax.fill_between(xdata, ylower, yupper, facecolor=colors[indexcolour+nlinesabove], alpha=1, lw=0, label=currentlabelsbelow[k], zorder=fillzorder)
                            bottom -= currentstackedbelow[k]
                        for indexcolour, l in enumerate(plotorderbelow):  # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly...
                            ax.plot((0, 0), (0, 0), color=colors[indexcolour+nlinesabove], linewidth=10, zorder=linezorder)

                        bottomofabove = 0 * results.tvec  # Easy way of setting to 0...
                        for indexcolour, k in enumerate(plotorderabove):  # Loop backwards so correct ordering -- first one at the top, not bottom
                            ylower = factor * bottomofabove
                            yupper = factor * (bottomofabove + currentstackedabove[k])
                            allydata.append(ylower)
                            allydata.append(yupper)
                            ax.fill_between(xdata, ylower, yupper, facecolor=colors[nlinesabove-indexcolour-1], alpha=1, lw=0,
                                            label=currentlabelsabove[k], zorder=fillzorder)
                            bottomofabove += currentstackedabove[k]
                        for indexcolour, k in enumerate(plotorderabove):  # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly...
                            ax.plot((0, 0), (0, 0), color=colors[indexcolour], linewidth=10, zorder=linezorder)

                        if showoverall:
                            # overall = bottombottom+bottomofabove # bottomofabove is actually the (positive) height of the top, bottombottom is actually the (negative) height of the bottom
                            #print(f'{pk}:overall increase in PLHIV: {None}, {list(zip(cumsum(overall),results.main["numplhiv"].pops[0][i]))}')#list(zip(xdata,overall))

                            overall = currentstackedabove.sum(axis=0) + currentstackedbelow.sum(axis=0)
                            ax.plot(xdata, overall, color=realdatacolor, linewidth=2,
                                       zorder=datazorder+1, label='Overall change')  # Without zorder, renders behind the graph

                        ax.plot(xdata,xdata*0, color='k',linewidth=1, zorder=datazorder)

                # REMOVED other things - not implemented in this function

                ################################################################################################################
                # Plot data points with uncertainty
                ################################################################################################################
                databest = None
                if data is not None:
                    if isperpopandstacked:
                        databest = data[mainplotindex][0][i]
                        datalow  = data[mainplotindex][1][i]
                        datahigh = data[mainplotindex][2][i]
                    elif isstacked:
                        databest = data[mainplotindex][0]
                        datalow  = data[mainplotindex][1]
                        datahigh = data[mainplotindex][2]
                    datax = xdata if len(xdata)==len(databest) else results.datayears
                ## Plot data points with uncertainty -- for total or perpop plots, but not if multisim
                if not ismultisim and databest is not None and showdata:
                    for y in range(len(datax)): # WARNING: hope that the data has the same years as the graph does
                        ydata = factor*array([datalow[y], datahigh[y]])
                        allydata.append(ydata)
                        ax.plot(datax[y]*array([1,1]), ydata, c=datacolor, lw=1)
                    ax.scatter(datax, factor*databest, color=realdatacolor, s=dotsize, lw=0, zorder=datazorder) # Without zorder, renders behind the graph
                    if dataisestimate: # This is stupid, but since IE can't handle linewidths sensibly, plot a new point smaller than the other one
                        ydata = factor*databest
                        allydata.append(ydata)
                        ax.scatter(datax, ydata, color=estimatecolor, s=dotsize*0.6, lw=0, zorder=datazorder+1)


                ################################################################################################################
                # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
                ################################################################################################################

                # General configuration
                boxoff(ax)
                ax.yaxis.label.set_fontsize(labelsize)
                for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)

                # Configure plot specifics
                legendsettings = {'loc': 'upper left', 'bbox_to_anchor': (1, 1), 'fontsize': legendsize, 'title': '',
                                  'frameon': False, 'borderaxespad': 2}

                plottitle = plottitles[mainplotindex]
                if isperpopandstacked:
                    plotylabel = plottitle
                    ax.set_ylabel(plotylabel)
                    try:
                        plottitle = kwargs["popmapping"][results.popkeys[i]]  # if popmapping was passed in as kwarg, use the title specified there for this population instead
                    except:
                        plottitle = results.popkeys[i]  # Add extra information to plot if by population
                    if forreport: ax.set_ylabel(plotylabel, fontsize=labelsize)  # overwrites previously set ylabel
                ax.set_title(plottitle)
                if forreport:
                    ax.set_xlabel('Year', fontsize=labelsize)
                    ax.set_title(plottitle, fontsize=titlesize)  # overwrites previously set title
                setylim(allydata, ax=ax)
                if forceintegerxaxis:
                    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
                ax.set_xlim((results.tvec[startind], results.tvec[endind]))
                if not ismultisim:
                    if isstacked or isperpopandstacked:
                        handles, legendlabels = ax.get_legend_handles_labels()
                        ax.legend(handles[::-1], legendlabels[::-1],
                                  **legendsettings)  # Multiple entries, all populations
                else:
                    handles, legendlabels = ax.get_legend_handles_labels()
                    ax.legend(handles[::-1], legendlabels, **legendsettings)  # Multiple simulations
                if useSIticks:
                    SIticks(ax=ax)
                else:
                    commaticks(ax=ax)

        return epiplots


##################################################################
## Plot by method of transmission (sex, injection, MTCT)
##################################################################
def plotbymethod(results, toplot=None, uncertainty=True, die=True, showdata=True, verbose=2, figsize=globalfigsize,
                alpha=0.2, lw=2, dotsize=30, titlesize=globaltitlesize, labelsize=globallabelsize,
                ticksize=globalticksize,
                legendsize=globallegendsize, position=None, useSIticks=True, colors=None, reorder=None,
                plotstartyear=None,
                plotendyear=None, interactive=None, fig=None, forreport=False, forceintegerxaxis=False, **kwargs):
        '''
        Used for plots that are stacked by method of transmission - namely 'numincimethods'
        Only setup for population+stacked graphs at the moment

        Messy copying from plotepi(), could be cleaned up if there are other
        types of graphs that want to be stacked by method and implemented here.

        WARNING copied from plotepi() optima version 2.10.13, commit: a3062175a5550b87edb55fba0f74072bdfa4bebe
        NOTE: do not call this function directly; instead, call via plotresults().
        '''

        # Figure out what kind of result it is
        if type(results) == Resultset:
            ismultisim = False
        elif type(results) == Multiresultset and results.nresultsets == 1: ismultisim = False # A Multiresultset with only one Resultset can have stacked plots
        elif type(results) == Multiresultset: # not implemented at the moment
            errormsg = 'Results input to plotbymethod() must be Resultset, not "%s".' % type(results)
            raise OptimaException(errormsg)

            # ismultisim = True
            # labels = results.keys  # Figure out the labels for the different lines
            # nsims = len(labels)  # How ever many things are in results
        else:
            errormsg = 'Results input to plotbymethod() must be Resultset, not "%s".' % type(results)
            raise OptimaException(errormsg)

        # Get year indices for producing plots
        startind, endind = getplotinds(plotstartyear=plotstartyear, plotendyear=plotendyear, tvec=results.tvec, die=die,
                                       verbose=verbose)

        # Initialize
        if toplot is None:  # If toplot is None...
            toplot = 'numincimethods'
        toplot = promotetolist(toplot)  # If single value, put inside list
        epiplots = odict()
        colorsarg = dcp(colors)  # This is annoying, but it gets overwritten later and need to preserve it here

        ## Validate plot keys
        valid_plotkeys = ['numincimethods']  # only allow selected things
        valid_plottypes = ['population+stacked','stacked'] # only allow population+stacked
        for pk, plotkeys in enumerate(toplot):
            epikey = None  # By default, don't make any assumptions
            plottype = 'population+stacked'  # Assume population+stacked by default
            if type(plotkeys) != str:
                errormsg = 'Could not understand "%s": must a string, e.g. "numplhiv" or "numplhiv-stacked"' % str(
                    plotkeys)
                raise OptimaException(errormsg)
            else:
                plotkeys = plotkeys.split('-')  # Try splitting if it's a string, e.g. numplhiv-stacked
                epikey = plotkeys[0]  # This must always exist, e.g. numplhiv
                if len(plotkeys) == 2:
                    plottype = plotkeys[1]  # Use the one specified
                elif len(plotkeys) == 1:  # Otherwise, try to use the default
                    try:
                        plottype = results.main[epikey].defaultplot  # If it's just e.g. numplhiv, then use the default plotting type
                    except:
                        try:
                            plottype = results.other[epikey].defaultplot
                        except:
                            errormsg = 'Unable to retrieve default plot type (total/population/stacked) for %s; falling back on %s' % (
                            epikey, plottype)
                            if die:
                                raise OptimaException(errormsg)
                            else:
                                printv(errormsg, 2, verbose)
                else:  # Give up
                    errormsg = 'Plotkeys must have length 1 or 2, but you have %s' % plotkeys
                    raise OptimaException(errormsg)
            if epikey not in valid_plotkeys:
                errormsg = 'Could not understand data type "%s"; should be one of:\n%s' % (epikey, valid_plotkeys)
                if die:
                    raise OptimaException(errormsg)
                else:
                    printv(errormsg, 2, verbose)
            if plottype not in valid_plottypes:  # Sum flattens a list of lists. Stupid.
                errormsg = 'Could not understand type "%s"; should be one of:\n%s' % (plottype, valid_plottypes)
                if die:
                    raise OptimaException(errormsg)
                else:
                    printv(errormsg, 2, verbose)
            toplot[pk] = (epikey, plottype)  # Convert to tuple for this index

        # Remove failed ones
        toplot = [thisplot for thisplot in toplot if None not in thisplot]  # Remove a plot if datatype or plotformat is None

        # Check if the figure will be saved to insert into a presentation or report
        if forreport:
            forreport = True
            titlesize = 16
            labelsize = 14

        ################################################################################################################
        ## Loop over each plot
        ################################################################################################################
        for plotkey in toplot:

            # Unpack tuple
            datatype, plotformat = plotkey

            # store result.main[datatype] as resultsmaindatatype, in order to allow selected other variables from results.other to be plotted
            if datatype in results.main.keys():
                resultsmaindatatype = results.main[datatype]
            else:
                resultsmaindatatype = results.other[datatype]

            ispercentage = resultsmaindatatype.ispercentage  # Indicate whether result is a percentage
            isestimate = resultsmaindatatype.estimate  # Indicate whether data is an estimate
            factor = 100.0 if ispercentage else 1.0  # Swap between number and percent
            datacolor = estimatecolor if isestimate else realdatacolor  # Light grey for
            istotal = (plotformat == 'total')
            isstacked = (plotformat == 'stacked')
            isperpop = (plotformat == 'population')
            isperpopandstacked = (plotformat == 'population+stacked')

            ################################################################################################################
            ## Process the plot data
            ################################################################################################################

            # Decide which attribute in results to pull -- doesn't map cleanly onto plot types
            if istotal or (isstacked):
                attrtype = 'tot'  # Only plot total if it's a scenario and 'stacked' was requested
            else:
                attrtype = 'pops'
            if istotal or isstacked or isperpopandstacked:
                datattrtype = 'tot'  # For pulling out total data
            else:
                datattrtype = 'pops'

            if ismultisim:  # e.g. scenario, no uncertainty
                best = list()  # Initialize as empty list for storing results sets
                for s in range(nsims): best.append(getattr(resultsmaindatatype, attrtype)[s])
                lower = None
                upper = None
                databest = None
                uncertainty = False
            else:  # Single results thing: plot with uncertainties and data
                best = getattr(resultsmaindatatype, attrtype)[0]  # poptype = either 'tot' or 'pops'
                try:  # If results were calculated with quantiles, these should exist
                    lower = getattr(resultsmaindatatype, attrtype)[1]
                    upper = getattr(resultsmaindatatype, attrtype)[2]
                except:  # No? Just use the best estimates
                    lower = best
                    upper = best
                try:  # Try loading actual data -- very likely to not exist
                    tmp = getattr(resultsmaindatatype, 'data' + datattrtype)
                    databest = tmp[0]
                    datalow = tmp[1]
                    datahigh = tmp[2]
                    if datatype in valid_plotkeys:  # because we are comparing numincionpopbypop to numinci, which has multiple possible resultsets
                        databest = databest[0]  # take the first resultset for numinci as "data"
                        datalow = datalow[0]
                        datahigh = datahigh[0]
                except:  # Don't worry if no data
                    databest = None
                    datalow = None
                    datahigh = None
            if not ismultisim and ndim(best) == 1:  # Wrap so right number of dimensions -- happens if not by population
                best = array([best])
                lower = array([lower])
                upper = array([upper])

            ################################################################################################################
            ## Set up figure and do plot
            ################################################################################################################
            if isperpop or isperpopandstacked:
                pkeys = [str(plotkey) + '-' + key for key in results.popkeys]  # Create list of plot keys (pkeys), one for each population
            else:
                pkeys = [plotkey]  # If it's anything else, just go with the original, but turn into a list so can iterate

            for i, pk in enumerate(pkeys):  # Either loop over individual population plots, or just plot a single plot, e.g. pk='prev-pop-FSW'
                epiplots[pk], naxes = makefigure(figsize=figsize, interactive=interactive,fig=fig)  # If it's anything other than HIV prevalence by population, create a single plot
                ax = epiplots[pk].add_subplot(naxes, 1, naxes)
                setposition(ax, position, interactive)
                allydata = []  # Keep track of the lowest value in the data

                if ismultisim or isperpopandstacked:
                    # print('SHAPE',best.shape)
                    # nplots = len(best)     # first axis is population acquired
                    nlinesperplot = len(best[i])    # second axis is causes, if population+stacked
                elif isstacked:
                    nlinesperplot = len(best)       # First axis is causes if stacked
                else:
                    nlinesperplot = 1               # In all other cases, there's a single line per plot
                if colorsarg is None: colors = gridcolors(nlinesperplot)  # This is needed because this loop gets run multiple times, so can't just set and forget

                ################################################################################################################
                # Plot model estimates with uncertainty -- different for each of the different possibilities
                ################################################################################################################

                xdata = results.tvec  # Pull this out here for clarity

                # Make sure plots are in the correct order

                origordermethod = arange(nlinesperplot)
                plotordermethod = nlinesperplot - 1 - origordermethod
                # if reorder: plotordermethod = [reorder[k] for k in plotorder]

                labels = results.settings.methodnames

                # # e.g. single simulation, prev-tot: single line, single plot
                # if not ismultisim and istotal:
                #     ydata = factor * best[0]
                #     allydata.append(ydata)
                #     ax.plot(xdata, ydata, lw=lw, c=colors[0],
                #             zorder=linezorder)  # Index is 0 since only one possibility
                #
                # # e.g. single simulation, prev-pop: single line, separate plot per population
                # if not ismultisim and isperpop:
                #     ydata = factor * best[i]
                #     allydata.append(ydata)
                #     ax.plot(xdata, ydata, lw=lw, c=colors[0],
                #             zorder=linezorder)  # Index is each individual population in a separate window

                # e.g. single simulation, prev-sta: either multiple lines or a stacked plot, depending on whether or not it's a number
                if not ismultisim and (isstacked or isperpopandstacked): # Always in here
                    if ispercentage:  # Multi-line plot THIS PROBABLY WON'T WORK
                        for k in plotorder:
                            ydata = factor * best[k]
                            allydata.append(ydata)
                            ax.plot(xdata, ydata, lw=lw, c=colors[k], zorder=linezorder,
                                    label=labels[k])  # Index is each different population
                    else:  # Stacked plot
                        if isperpopandstacked:
                            beststored = dcp(best)
                            best = best[i]
                        bottom = 0 * results.tvec  # Easy way of setting to 0...
                        for k in plotordermethod:  # Loop backwards so correct ordering -- first one at the top, not bottom
                            ylower = factor * bottom
                            yupper = factor * (bottom + best[k])
                            allydata.append(ylower)
                            allydata.append(yupper)
                            ax.fill_between(xdata, ylower, yupper, facecolor=colors[k], alpha=1, lw=0,
                                            label=labels[k], zorder=fillzorder)
                            bottom += best[k]
                        for l in range(nlinesperplot):  # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly...
                            ax.plot((0, 0), (0, 0), color=colors[l], linewidth=10, zorder=linezorder)
                        if isperpopandstacked:
                            best = beststored

                # e.g. scenario, prev-tot; since stacked plots aren't possible with multiple lines, just plot the same in this case
                if ismultisim and (istotal or isstacked):
                    for l in range(nlinesperplot):
                        ind = nlinesperplot - 1 - l
                        thisxdata = results.setup[ind]['tvec']
                        ydata = factor * best[ind]
                        allydata.append(ydata)
                        ax.plot(thisxdata, ydata, lw=lw, c=colors[ind], zorder=linezorder,label=labels[l])  # Index is each different e.g. scenario

                if ismultisim and isperpop:
                    for l in range(nlinesperplot):
                        ind = nlinesperplot - 1 - l
                        thisxdata = results.setup[ind]['tvec']
                        ydata = factor * best[ind][i]
                        allydata.append(ydata)
                        ax.plot(thisxdata, ydata, lw=lw, c=colors[ind], zorder=linezorder, label=labels[l])  # Indices are different populations (i), then different e..g scenarios (l)

                ################################################################################################################
                # Plot data points with uncertainty
                ################################################################################################################

                # Plot uncertainty, but not for stacked plots
                if uncertainty and not isstacked and not isperpopandstacked:  # It's not by population, except HIV prevalence, and uncertainty has been requested: plot bands
                    ylower = factor * lower[i]
                    yupper = factor * upper[i]
                    allydata.append(ylower)
                    allydata.append(yupper)
                    ax.fill_between(xdata, ylower, yupper, facecolor=colors[0], alpha=alpha, lw=0)

                # Plot data points with uncertainty -- for total or perpop plots, but not if multisim
                if not ismultisim and databest is not None and showdata:
                    for y in range(len(results.datayears)):
                        ydata = factor * array([datalow[i][y], datahigh[i][y]])
                        allydata.append(ydata)
                        ax.plot(results.datayears[y] * array([1, 1]), ydata, c=datacolor, lw=1)
                    ax.scatter(results.datayears, factor * databest[i], color=realdatacolor, s=dotsize, lw=0,
                               zorder=datazorder)  # Without zorder, renders behind the graph
                    if isestimate:  # This is stupid, but since IE can't handle linewidths sensibly, plot a new point smaller than the other one
                        ydata = factor * databest[i]
                        allydata.append(ydata)
                        ax.scatter(results.datayears, ydata, color=estimatecolor, s=dotsize * 0.6, lw=0,
                                   zorder=datazorder + 1)

                ################################################################################################################
                # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
                ################################################################################################################

                # General configuration
                boxoff(ax)
                ax.yaxis.label.set_fontsize(labelsize)
                for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)

                # Configure plot specifics
                legendsettings = {'loc': 'upper left', 'bbox_to_anchor': (1, 1), 'fontsize': legendsize, 'title': '',
                                  'frameon': False, 'borderaxespad': 2}
                plottitle = resultsmaindatatype.name
                if isperpop or isperpopandstacked:
                    plotylabel = plottitle
                    ax.set_ylabel(plotylabel)
                    try:
                        plottitle = kwargs["popmapping"][results.popkeys[i]]  # if popmapping was passed in as kwarg, use the title specified there for this population instead
                    except:
                        plottitle = results.popkeys[i]  # Add extra information to plot if by population
                    if forreport: ax.set_ylabel(plotylabel, fontsize=labelsize)  # overwrites previously set ylabel
                ax.set_title(plottitle)
                if forreport:
                    ax.set_xlabel('Year', fontsize=labelsize)
                    ax.set_title(plottitle, fontsize=titlesize)  # overwrites previously set title
                setylim(allydata, ax=ax)
                if forceintegerxaxis:
                    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
                ax.set_xlim((results.tvec[startind], results.tvec[endind]))
                if not ismultisim:
                    if isstacked or isperpopandstacked:
                        handles, legendlabels = ax.get_legend_handles_labels()
                        ax.legend(handles[::-1], legendlabels[::-1], **legendsettings)  # Multiple entries, all populations
                else:
                    handles, legendlabels = ax.get_legend_handles_labels()
                    ax.legend(handles[::-1], legendlabels, **legendsettings)  # Multiple simulations
                if useSIticks:
                    SIticks(ax=ax)
                else:
                    commaticks(ax=ax)

        return epiplots


##################################################################
## Plot things by CD4
##################################################################
def plotbycd4(results=None, whattoplot='people', figsize=globalfigsize, lw=2, titlesize=globaltitlesize, labelsize=globallabelsize, 
                ticksize=globalticksize, legendsize=globallegendsize, ind=0, interactive=False, **kwargs):
    ''' 
    Plot deaths or people by CD4
    NOTE: do not call this function directly; instead, call via plotresults().
    
    Warning, broken due to results.raw being removed
    '''
    
    # Figure out what kind of result it is
    if type(results)==Resultset: 
        ismultisim = False
        nsims = 1
    elif type(results)==Multiresultset and results.nresultsets == 1:
        ismultisim = False # A Multiresultset with only one Resultset can have stacked plots
        nsims = 1
    elif type(results)==Multiresultset:
        ismultisim = True
        titles = results.keys # Figure out the labels for the different lines
        nsims = len(titles) # How ever many things are in results
    else: 
        errormsg = 'Results input to plotbycd4() must be either Resultset or Multiresultset, not "%s".' % type(results)
        raise OptimaException(errormsg)

    # Set up figure and do plot
    fig,naxes = makefigure(figsize=figsize, interactive=interactive)
    ax = []
    
    titlemap = {'people': 'PLHIV', 'death': 'Deaths'}
    settings = results.projectref().settings
    hivstates = settings.hivstates
    indices = arange(0, len(results.raw[ind]['tvec']), int(round(1.0/(results.raw[ind]['tvec'][1]-results.raw[ind]['tvec'][0]))))
    colors = gridcolors(len(hivstates))
    
    for plt in range(nsims): # WARNING, copied from plotallocs()
        bottom = 0.*results.tvec # Easy way of setting to 0...
        thisdata = 0.*results.tvec # Initialise
        allydata = []
        
        ## Do the plotting
        ax.append(fig.add_subplot(nsims,1,plt+1))
        for s,state in enumerate(reversed(hivstates)): # Loop backwards so correct ordering -- first one at the top, not bottom
            if ismultisim: thisdata += results.raw[plt][ind][whattoplot][getattr(settings,state),:,:].sum(axis=(0,1))[indices] # If it's a multisim, need an extra index for the plot number
            else:          thisdata += results.raw[ind][whattoplot][getattr(settings,state),:,:].sum(axis=(0,1))[indices] # Get the best estimate
            ax[-1].fill_between(results.tvec, bottom, thisdata, facecolor=colors[s], alpha=1, lw=0)
            bottom = dcp(thisdata) # Set the bottom so it doesn't overwrite
            ax[-1].plot((0, 0), (0, 0), color=colors[len(colors)-s-1], linewidth=10) # Colors are in reverse order
            allydata.append(thisdata)
        
        ## Configure plot -- WARNING, copied from plotepi()
        boxoff(ax[-1])
        ax[-1].title.set_fontsize(titlesize)
        ax[-1].xaxis.label.set_fontsize(labelsize)
        for item in ax[-1].get_xticklabels() + ax[-1].get_yticklabels(): item.set_fontsize(ticksize)

        # Configure plot specifics
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'',
                          'frameon':False}
        if ismultisim: ax[-1].set_title(titlemap[whattoplot]+'- %s' % titles[plt])
        else: ax[-1].set_title(titlemap[whattoplot])
        setylim(allydata, ax[-1])
        ax[-1].set_xlim((results.tvec[0], results.tvec[-1]))
        ax[-1].legend(results.settings.hivstatesfull, **legendsettings) # Multiple entries, all populations
        
    SIticks(ax=ax)
    
    return fig    




##################################################################
## Plot things by CD4
##################################################################
def ploticers(results=None, figsize=globalfigsize, lw=2, dotsize=30, titlesize=globaltitlesize, labelsize=globallabelsize, 
             ticksize=globalticksize, legendsize=globallegendsize, position=None, interactive=False, **kwargs):
    ''' 
    Plot ICERs. Not part of weboptima yet.
    '''
    
    # Figure out what kind of result it is
    if not(type(results)==ICER): 
        errormsg = 'Results input to ploticers() must be an ICER result, not "%s".' % type(results)
        raise OptimaException(errormsg)

    # Set up figure and do plot
    fig,naxes = makefigure(figsize=figsize, interactive=interactive)
    ax = fig.add_subplot(naxes, 1, naxes)
    position = dcp(position)
    if position is None: # If defaults, reset
        if interactive: position = dcp(interactiveposition)
        else:           position = dcp(globalposition)
        position[1] += 0.05 # More room on bottom for x-axis label
    setposition(ax, position, interactive)
    keys = results.keys
    icer = results.icer
    x    = results.x*100.0 # Convert to percent
    nkeys = len(keys)
    colors = gridcolors(nkeys, hueshift=proghueshift)
    if   results.objective == 'death': objectivestr = 'death'
    elif results.objective == 'inci':  objectivestr = 'new infection'
    elif results.objective == 'daly':  objectivestr = 'DALY'
    else:
        errormsg = 'Cannot plot ICERs: objective "%s" is unknown' % results.objective
        raise OptimaException(errormsg)
    
    # Figure out y-axis limits
    minicer  = icer[:].min()
    maxicer  = icer[:].max()
    meanicer = icer[:].mean()
    totalbudget = results.defaultbudget[:].sum()
    upperlim = min([maxicer, totalbudget, 10*meanicer, 50*minicer]) # Set the y limit based on the minimum of each of these different options
    
    # Do the plotting
    sizeratio = 1.5
    ax.plot([100,100], [0,upperlim], color=(0.7,0.7,0.7), linewidth=1, linestyle=':') # Mark the current spending
    hitupper = 0 # Count the number of programs that hit the upper limit
    newupper = upperlim
    for k,key in enumerate(keys): # Loop backwards so correct ordering -- first one at the top, not bottom
        newupper = upperlim*(1.0+0.01*hitupper) # Make it so lines are distinguishable
        thisicer = minimum(icer[key], newupper) # Cap the ICERs with maximum value
        goodinds = findinds(thisicer<upperlim)
        badinds  = findinds(thisicer>=upperlim)
        if len(badinds)>0:  hitupper += 1
        ax.plot(x, thisicer, color=colors[k], lw=lw*sizeratio, label=key) # Colors are in reverse order
        ax.scatter(x[goodinds], thisicer[goodinds], s=dotsize*sizeratio, facecolor=colors[k], lw=0)
        ax.scatter(x[badinds],  thisicer[badinds],  s=dotsize*sizeratio, facecolor=(0,0,0), lw=1, marker='x', zorder=1000)
    
    # Configure plot
    boxoff(ax)
    ax.title.set_fontsize(titlesize)
    ax.xaxis.label.set_fontsize(labelsize)
    for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)

    # Configure plot specifics
    ax.set_title('ICERs')
    ax.set_ylabel('Cost per %s averted' % objectivestr)
    ax.set_xlabel('Program spending relative to baseline (%)')
    ax.set_ylim(0, newupper*1.05)
    dx = (x[-1]-x[0])*0.01
    ax.set_xlim(x[0]-dx, x[-1]+dx)
    legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
    ax.legend(**legendsettings) # Multiple entries, all populations
    SIticks(ax=ax)
    
    return fig    




def plotcostcov(program=None, year=None, parset=None, results=None, plotoptions=None, existingFigure=None, plotbounds=True, npts=100, maxupperlim=1e8, interactive=False, proportion=False, **kwargs):
    ''' Plot the cost-coverage curve for a single program'''
    
    # Put plotting imports here so fails at the last possible moment
    if year is None: 
        year = program.costcovfn.ccopars['t'] # Populate with default
    if not isinstance(parset, Parameterset):
        raise OptimaException('Please supply a parset, not "%s"' % parset)
    year = promotetoarray(year)
    colors = gridcolors(len(year))
    plotdata = odict()
    
    # Get caption & scatter data 
    caption = plotoptions['caption'] if plotoptions and plotoptions.get('caption') else ''
    costdata = dcp(program.costcovdata['cost']) if program.costcovdata.get('cost') else []
    covdata  = dcp(program.costcovdata['coverage']) if program.costcovdata.get('coverage') else []
    timedata = dcp(program.costcovdata['t']) if program.costcovdata.get('t') else []
    
    # Sanitize for nans
    costdata = promotetoarray(costdata)
    covdata = promotetoarray(covdata)
    timedata = promotetoarray(timedata)
    validindices = getvalidinds(costdata, covdata)
    costdata = costdata[validindices]
    covdata = covdata[validindices]
    timedata = timedata[validindices]

    # Make x data... 
    if plotoptions and plotoptions.get('xupperlim') and ~isnan(plotoptions['xupperlim']):
        xupperlim = plotoptions['xupperlim']
    else:
        if len(costdata): xupperlim = 1.5*max(costdata)
        else: xupperlim = maxupperlim
    xlinedata = linspace(0,xupperlim,npts)

    if plotoptions and plotoptions.get('perperson'):
        xlinedata = linspace(0,xupperlim*program.gettargetpopsize(year[-1],parset),npts)

    # Create x line data and y line data
    try:
        y_l = program.getcoverage(x=xlinedata, t=year, parset=parset, results=results, total=True, proportion=proportion, toplot=True, sample='l')
        y_m = program.getcoverage(x=xlinedata, t=year, parset=parset, results=results, total=True, proportion=proportion, toplot=True, sample='best')
        y_u = program.getcoverage(x=xlinedata, t=year, parset=parset, results=results, total=True, proportion=proportion, toplot=True, sample='u')
    except Exception as E:
        y_l,y_m,y_u = None,None,None
        print('Warning, could not get program coverage: %s' % repr(E))
    plotdata['ylinedata_l'] = y_l
    plotdata['ylinedata_m'] = y_m
    plotdata['ylinedata_u'] = y_u
    plotdata['xlabel'] = 'Spending'
    plotdata['ylabel'] = 'Number covered'

    # Flag to indicate whether we will adjust by population or not
    if plotoptions and plotoptions.get('perperson'):
        if len(costdata):
            for yrno,yr in enumerate(timedata):
                targetpopsize = program.gettargetpopsize(t=yr, parset=parset, results=results)
                costdata[yrno] /= targetpopsize[0]
        if not (plotoptions and plotoptions.get('xupperlim') and ~isnan(plotoptions['xupperlim'])):
            if len(costdata): xupperlim = 1.5*max(costdata) 
            else: xupperlim = 1e3
        plotdata['xlinedata'] = linspace(0,xupperlim,npts)
    else:
        plotdata['xlinedata'] = xlinedata

    fig,naxes = makefigure(figsize=None, interactive=interactive, fig=existingFigure)
    ax = fig.add_subplot(111)
    
    ax.set_position((0.1, 0.35, .8, .6)) # to make a bit of room for extra text
    fig.text(.1, .05, textwrap.fill(caption))
    
    if y_m is not None:
        for yr in range(y_m.shape[0]):
            ax.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata_m'][yr],
                linestyle='-',
                linewidth=2,
                color=colors[yr],
                label=year[yr])
            if plotbounds:
                ax.fill_between(plotdata['xlinedata'],
                                  plotdata['ylinedata_l'][yr],
                                  plotdata['ylinedata_u'][yr],
                                  facecolor=colors[yr],
                                  alpha=.1,
                                  lw=0)
    
    ax.scatter(costdata, covdata, color='#666666')
    
    setylim(0, ax) # Equivalent to ax.set_ylim(bottom=0)
    ax.set_xlim([0, xupperlim])
    ax.tick_params(axis='both', which='major', labelsize=11)
    ax.set_xlabel(plotdata['xlabel'], fontsize=11)
    ax.set_ylabel(plotdata['ylabel'], fontsize=11)
    ax.get_xaxis().set_major_locator(ticker.MaxNLocator(nbins=3))
    ax.set_title(program.short)
    ax.get_xaxis().get_major_formatter().set_scientific(False)
    ax.get_yaxis().get_major_formatter().set_scientific(False)
    if len(year)>1: ax.legend(loc=4)
    
    return fig




def saveplots(results=None, toplot=None, filetype=None, filename=None, folder=None, savefigargs=None, index=None, verbose=2, plots=None, **kwargs):
    '''
    Save the requested plots to disk.
    
    Arguments:
        results -- either a Resultset, Multiresultset, or a Project
        toplot -- either a plot key or a list of plot keys
        filetype -- the file type; can be 'fig', 'singlepdf' (default), or anything supported by savefig()
        folder -- the folder to save the file(s) in
        filename -- the file to save to (only uses path if multiple files)
        savefigargs -- dictionary of arguments passed to savefig()
        index -- optional argument to only save the specified plot index
        kwargs -- passed to makeplots()
    
    Example usages:
        import optima as op
        P = op.demo(0)
        op.saveplots(P) # Save everything to one PDF file
        op.saveplots(P, 'cascade', 'png', filename='mycascade.png', savefigargs={'dpi':200})
        op.saveplots(P, ['numplhiv','cascade'], filepath='/home/me', filetype='svg')
        op.saveplots(P, 'cascade', position=[0.3,0.3,0.5,0.5])
    
    If saved as 'fig', then can load and display the plot using op.loadplot().
    
    Version: 2017mar15    
    '''
    
    # Preliminaries
    wasinteractive = isinteractive() # You might think you can get rid of this...you can't!
    if wasinteractive: ioff()
    if filetype is None: filetype = 'singlepdf' # This ensures that only one file is created
    results = sanitizeresults(results)
    
    # Either take supplied plots, or generate them
    if plots is None: # NB, this is actually a figure or a list of figures
        plots = makeplots(results=results, toplot=toplot, **kwargs)
    plots = promotetoodict(plots)
    nplots = len(plots)
    
    # Handle file types
    filenames = []
    if filetype=='singlepdf': # See http://matplotlib.org/examples/pylab_examples/multipage_pdf.html
        from matplotlib.backends.backend_pdf import PdfPages
        defaultname = results.projectinfo['name']+'-'+'figures.pdf'
        fullpath = makefilepath(filename=filename, folder=folder, default=defaultname, ext='pdf')
        pdf = PdfPages(fullpath)
        filenames.append(fullpath)
        printv('PDF saved to %s' % fullpath, 2, verbose)
    for p,item in enumerate(plots.items()):
        key,plt = item
        if index is None or index==p:
            # Handle filename
            if filename and nplots==1: # Single plot, filename supplied -- use it
                fullpath = makefilepath(filename=filename, folder=folder, default='optima-figure', ext=filetype) # NB, this filename not used for singlepdf filetype, so it's OK
            else: # Any other case, generate a filename
                keyforfilename = ''.join(filter(str.isalnum, str(key))) # Strip out non-alphanumeric stuff for key
                defaultname = results.projectinfo['name']+'-'+keyforfilename
                fullpath = makefilepath(filename=filename, folder=folder, default=defaultname, ext=filetype)
            
            # Do the saving
            if savefigargs is None: savefigargs = {}
            defaultsavefigargs = {'dpi':200, 'bbox_inches':'tight'} # Specify a higher default DPI and save the figure tightly
            defaultsavefigargs.update(savefigargs) # Update the default arguments with the user-supplied arguments
            if filetype == 'fig':
                saveobj(fullpath, plt)
                filenames.append(fullpath)
                printv('Figure object saved to %s' % fullpath, 2, verbose)
            else:
                reanimateplots(plt)
                if filetype=='singlepdf':
                    pdf.savefig(figure=plt, **defaultsavefigargs) # It's confusing, but defaultsavefigargs is correct, since we updated it from the user version
                else:
                    plt.savefig(fullpath, **defaultsavefigargs)
                    filenames.append(fullpath)
                    printv('%s plot saved to %s' % (filetype.upper(),fullpath), 2, verbose)
                close(plt)

    if filetype=='singlepdf': pdf.close()
    if wasinteractive: ion()
    return filenames


def reanimateplots(plots=None):
    ''' Reconnect plots (actually figures) to the Matplotlib backend. plots must be an odict of figure objects. '''
    if len(get_fignums()): fignum = gcf().number # This is the number of the current active figure, if it exists
    else: fignum = 1
    plots = promotetoodict(plots) # Convert to an odict
    for plt in plots.values(): nfmgf(fignum, plt) # Make sure each figure object is associated with the figure manager -- WARNING, is it correct to associate the plot with an existing figure?
    return None


def sanitizeresults(results):
    ''' Allow for flexible input -- a results structure, a list, or a project file '''
    if type(results)==list: output = Multiresultset(results) # Convert to a multiresults set if it's a list of results
    elif type(results) not in [Resultset, Multiresultset]:
        try: output = results.results[-1] # Maybe it's actually a project? Pull out results
        except: raise OptimaException('Could not figure out how to get results from:\n%s' % results)
    else: output = results # Just use directly
    return output


def getplotinds(plotstartyear=None, plotendyear=None, tvec=None, die=False, verbose=2):
    ''' Little function to convert the requested start and end years to indices '''
    if plotstartyear is not None:
        try: startind = findnearest(tvec,plotstartyear) # Get the index of the year to start the plots
        except: 
            errormsg = 'Unable to find year %s in resultset; falling back on %s'% (plotstartyear, tvec[0])
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 3, verbose)
                startind = 0
    else: startind = 0

    if plotendyear is not None:
        try: endind = findnearest(tvec,plotendyear) # Get the index of the year to end the plots
        except: 
            errormsg = 'Unable to find year %s in resultset; falling back on %s'% (plotendyear, tvec[-1])
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 3, verbose)
                endind = -1
    else: endind = -1
    
    return startind, endind
