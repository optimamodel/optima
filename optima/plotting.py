'''
PLOTTING

This file generates all the figure files -- either for use with the Python backend, or
for the frontend via MPLD3.

To add a new plot, you need to add it to getplotselections (in this file) so it will show up in the interface;
plotresults (in gui.py) so it will be sent to the right spot; and then add the actual function to do the
plotting to this file.

Version: 2016jul06
'''

from optima import OptimaException, Resultset, Multiresultset, odict, printv, gridcolormap, vectocolor, alpinecolormap, sigfig, dcp, findinds, promotetolist
from numpy import array, ndim, maximum, arange, zeros, mean, shape
from pylab import isinteractive, ioff, ion, figure, plot, close, ylim, fill_between, scatter, gca, subplot, legend, barh, pie
from matplotlib import ticker

# Define allowable plot formats -- 3 kinds, but allow some flexibility for how they're specified
epiplottypes = ['total', 'stacked', 'population']
realdatacolor = (0,0,0) # Define color for data point -- WARNING, should this be in settings.py?
estimatecolor = 'none' # Color of estimates rather than real data
defaultplots = ['budgets', 'numplhiv-stacked', 'numinci-stacked', 'numdeath-stacked', 'numtreat-stacked', 'numnewdiag-stacked', 'prev-population', 'popsize-stacked'] # Default epidemiological plots
defaultmultiplots = ['budgets', 'numplhiv-total', 'numinci-total', 'numdeath-total', 'numtreat-total', 'numnewdiag-total', 'prev-population'] # Default epidemiological plots

# Define global font sizes
globaltitlesize = 10
globallabelsize = 10
globalticksize = 8
globallegendsize = 8


def SItickformatter(x, pos):  # formatter function takes tick label and tick position
    ''' Formats axis ticks so that e.g. 34,243 becomes 34K '''
    if abs(x)>=1e9:     output = str(x/1e9)+'B'
    elif abs(x)>=1e6:   output = str(x/1e6)+'M'
    elif abs(x)>=1e3:   output = str(x/1e3)+'K'
    else:               output = str(x)
    return output

def SIticks(figure, axis='y'):
    ''' Apply SI tick formatting to the y axis of a figure '''
    for ax in figure.axes:
        if axis=='x':   thisaxis = ax.xaxis
        elif axis=='y': thisaxis = ax.yaxis
        elif axis=='z': thisaxis = ax.zaxis
        else: raise OptimaException('Axis must be x, y, or z')
        thisaxis.set_major_formatter(ticker.FuncFormatter(SItickformatter))

def commaticks(figure, axis='y'):
    ''' Use commas in formatting the y axis of a figure -- see http://stackoverflow.com/questions/25973581/how-to-format-axis-number-format-to-thousands-with-a-comma-in-matplotlib '''
    for ax in figure.axes:
        if axis=='x':   thisaxis = ax.xaxis
        elif axis=='y': thisaxis = ax.yaxis
        elif axis=='z': thisaxis = ax.zaxis
        else: raise OptimaException('Axis must be x, y, or z')
        thisaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))


def getplotselections(results, advanced=False):
    ''' 
    From the inputted results structure, figure out what the available kinds of plots are. List results-specific
    plot types first (e.g., allocations), followed by the standard epi plots, and finally (if available) other
    plots such as the cascade.
    
    Version: 2017jan20
    '''
    
    # Figure out what kind of result it is -- WARNING, copied from below
    if type(results)==Resultset: ismultisim = False
    elif type(results)==Multiresultset: ismultisim = True
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
    
    ## Cascade plot is always available, since epi is always available
    plotselections['keys'].append('cascade')
    plotselections['names'].append('Treatment cascade')
    
#    ## Deaths by CD4
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
                    plotepikeys.append(key+'-'+subkey)
        for name in epinames: # e.g. 'HIV prevalence'
            for subname in epiplottypes: # e.g. 'total'
                if not(ismultisim and subname=='stacked'): # Stacked multisim plots don't make sense -- WARNING, this is clunky!!!
                    plotepinames.append(name+' -- '+subname)
    else:
        plotepikeys = dcp(epikeys)
        plotepinames = dcp(epinames)
    
    if not advanced:
        for i in range(len(defaultplots)): defaultplots[i] = defaultplots[i].split('-')[0] # Discard second half of plot name
        for i in range(len(defaultmultiplots)): defaultmultiplots[i] = defaultmultiplots[i].split('-')[0] # Discard second half of plot name
    plotselections['keys'] += plotepikeys
    plotselections['names'] += plotepinames
    for key in plotselections['keys']: # Loop over each key
        if ismultisim: plotselections['defaults'].append(key in defaultmultiplots)
        else:          plotselections['defaults'].append(key in defaultplots) # Append True if it's in the defaults; False otherwise
    
    return plotselections



def makeplots(results=None, toplot=None, die=False, verbose=2, **kwargs):
    ''' 
    Function that takes all kinds of plots and plots them -- this is the only plotting function the user should use 
    
    The keyword 'die' controls what it should do with an exception: if False, then carry on as if nothing happened;
    if True, then actually rase the exception.
    
    Note that if toplot='default', it will plot the default plots (defined in plotting.py).
    
    Version: 2016jan24    
    '''
    
    ## Initialize
    allplots = odict()
    wasinteractive = isinteractive() # Get current state of interactivity
    ioff() # Just in case, so we don't flood the user's screen with figures
    if toplot is None: toplot = defaultplots # Go straight ahead and replace with defaults
    if not(isinstance(toplot, list)): toplot = [toplot] # Handle single entries, for example 
    if 'default' in toplot: # Special case for handling default plots
        toplot[0:0] = defaultplots # Very weird but valid syntax for prepending one list to another: http://stackoverflow.com/questions/5805892/how-to-insert-the-contents-of-one-list-into-another
    toplot = list(odict.fromkeys(toplot)) # This strange but efficient hack removes duplicates while preserving order -- see http://stackoverflow.com/questions/1549509/remove-duplicates-in-a-list-while-keeping-its-order-python
    

    ## Add improvement plot
    if 'improvement' in toplot:
        toplot.remove('improvement') # Because everything else is passed to plotepi()
        try: 
            if hasattr(results, 'improvement') and results.improvement is not None: # WARNING, duplicated from getplotselections()
                allplots['improvement'] = plotimprovement(results, die=die, **kwargs)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot improvement: "%s"' % E.__repr__(), 1, verbose)
        
    
    ## Add budget plot
    if 'budgets' in toplot:
        toplot.remove('budgets') # Because everything else is passed to plotepi()
        try: 
            if hasattr(results, 'budgets') and results.budgets: # WARNING, duplicated from getplotselections()
                budgetplots = plotbudget(results, die=die, **kwargs)
                allplots.update(budgetplots)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot budgets: "%s"' % (E.__repr__()), 1, verbose)
    
    ## Add coverage plot(s)
    if 'coverage' in toplot:
        toplot.remove('coverage') # Because everything else is passed to plotepi()
        try: 
            if hasattr(results, 'coverages') and results.coverages: # WARNING, duplicated from getplotselections()
                coverageplots = plotcoverage(results, die=die, **kwargs)
                allplots.update(coverageplots)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot coverages: "%s"' % (E.__repr__()), 1, verbose)
    
    ## Add cascade plot(s)
    if 'cascade' in toplot:
        toplot.remove('cascade') # Because everything else is passed to plotepi()
        try: 
            cascadeplots = plotcascade(results, die=die, **kwargs)
            allplots.update(cascadeplots)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot cascade: "%s"' % E.__repr__(), 1, verbose)
    
    
    ## Add deaths by CD4 plot
    if 'deathbycd4' in toplot:
        toplot.remove('deathbycd4') # Because everything else is passed to plotepi()
        try: 
            allplots['deathbycd4'] = plotbycd4(results, whattoplot='death', die=die, **kwargs)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot deaths by CD4: "%s"' % E.__repr__(), 1, verbose)
    
    
    ## Add PLHIV by CD4 plot
    if 'plhivbycd4' in toplot:
        toplot.remove('plhivbycd4') # Because everything else is passed to plotepi()
        try: 
            allplots['plhivbycd4'] = plotbycd4(results, whattoplot='people', die=die, **kwargs)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot PLHIV by CD4: "%s"' % E.__repr__(), 1, verbose)
    
    
    ## Add epi plots -- WARNING, I hope this preserves the order! ...It should...
    epiplots = plotepi(results, toplot=toplot, die=die, **kwargs)
    allplots.update(epiplots)
    
    
    # Tidy up: turn interactivity back on
    if wasinteractive: ion() 
    
    return allplots





def plotepi(results, toplot=None, uncertainty=True, die=True, doclose=True, plotdata=True, verbose=2, figsize=(14,10), alpha=0.2, lw=2, dotsize=50,
            titlesize=globaltitlesize, labelsize=globallabelsize, ticksize=globalticksize, legendsize=globallegendsize, useSIticks=True, colors=None, reorder=None, **kwargs):
        '''
        Render the plots requested and store them in a list. Argument "toplot" should be a list of form e.g.
        ['prev-tot', 'inci-pop']

        This function returns an odict of figures, which can then be saved as MPLD3, etc.
        
        NOTE: do not call this function directly; instead, call via plotresults().

        Version: 2016jan21
        '''
        
        # Figure out what kind of result it is
        if type(results)==Resultset: ismultisim = False
        elif type(results)==Multiresultset:
            ismultisim = True
            labels = results.keys # Figure out the labels for the different lines
            nsims = len(labels) # How ever many things are in results
        else: 
            errormsg = 'Results input to plotepi() must be either Resultset or Multiresultset, not "%s".' % type(results)
            raise OptimaException(errormsg)

        # Initialize
        toplot = promotetolist(toplot) # If single value, put inside list
        epiplots = odict()
        colorsarg = dcp(colors) # This is annoying, but it gets overwritten later and need to preserve it here


        ## Validate plot keys
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
                        errormsg = 'Unable to retrieve default plot type (total/population/stacked); falling back on %s'% plottype
                        if die: raise OptimaException(errormsg)
                        else: printv(errormsg, 2, verbose)
                else: # Give up
                    errormsg = 'Plotkeys must have length 1 or 2, but you have %s' % plotkeys
                    raise OptimaException(errormsg)
            if epikey not in results.main.keys():
                errormsg = 'Could not understand data type "%s"; should be one of:\n%s' % (epikey, results.main.keys())
                if die: raise OptimaException(errormsg)
                else: printv(errormsg, 2, verbose)
            if plottype not in epiplottypes: # Sum flattens a list of lists. Stupid.
                errormsg = 'Could not understand type "%s"; should be one of:\n%s' % (plottype, epiplottypes)
                if die: raise OptimaException(errormsg)
                else: printv(errormsg, 2, verbose)
            toplot[pk] = (epikey, plottype) # Convert to tuple for this index
        
        # Remove failed ones
        toplot = [thisplot for thisplot in toplot if None not in thisplot] # Remove a plot if datatype or plotformat is None


        ################################################################################################################
        ## Loop over each plot
        ################################################################################################################
        for plotkey in toplot:
            
            # Unpack tuple
            datatype, plotformat = plotkey 
            
            ispercentage = results.main[datatype].ispercentage # Indicate whether result is a percentage
            isestimate = results.main[datatype].estimate # Indicate whether result is a percentage
            factor = 100.0 if ispercentage else 1.0 # Swap between number and percent
            datacolor = estimatecolor if isestimate else realdatacolor # Light grey for
            istotal   = (plotformat=='total')
            isstacked = (plotformat=='stacked')
            isperpop  = (plotformat=='population')
            
            
            
            ################################################################################################################
            ## Process the plot data
            ################################################################################################################
            
            # Decide which attribute in results to pull -- doesn't map cleanly onto plot types
            if istotal or (isstacked and ismultisim): attrtype = 'tot' # Only plot total if it's a scenario and 'stacked' was requested
            else: attrtype = 'pops'
            if istotal or isstacked: datattrtype = 'tot' # For pulling out total data
            else: datattrtype = 'pops'
            
            if ismultisim:  # e.g. scenario, no uncertainty
                best = list() # Initialize as empty list for storing results sets
                for s in range(nsims): best.append(getattr(results.main[datatype], attrtype)[s])
                lower = None
                upper = None
                databest = None
                uncertainty = False
            else: # Single results thing: plot with uncertainties and data
                best = getattr(results.main[datatype], attrtype)[0] # poptype = either 'tot' or 'pops'
                try: # If results were calculated with quantiles, these should exist
                    lower = getattr(results.main[datatype], attrtype)[1]
                    upper = getattr(results.main[datatype], attrtype)[2]
                except: # No? Just use the best estimates
                    lower = best
                    upper = best
                try: # Try loading actual data -- very likely to not exist
                    tmp = getattr(results.main[datatype], 'data'+datattrtype)
                    databest = tmp[0]
                    datalow = tmp[1]
                    datahigh = tmp[2]
                except:# Don't worry if no data
                    databest = None
                    datalow = None
                    datahigh = None
            if ndim(best)==1: # Wrap so right number of dimensions -- happens if not by population
                best  = array([best])
                lower = array([lower])
                upper = array([upper])
            
            
            ################################################################################################################
            ## Set up figure and do plot
            ################################################################################################################
            if isperpop: pkeys = [str(plotkey)+'-'+key for key in results.popkeys] # Create list of plot keys (pkeys), one for each population
            else: pkeys = [plotkey] # If it's anything else, just go with the original, but turn into a list so can iterate
            
            for i,pk in enumerate(pkeys): # Either loop over individual population plots, or just plot a single plot, e.g. pk='prev-pop-FSW'
                
                epiplots[pk] = figure(facecolor=(1,1,1), figsize=figsize) # If it's anything other than HIV prevalence by population, create a single plot
    
                if isstacked or ismultisim: nlinesperplot = len(best) # There are multiple lines per plot for both pops poptype and for plotting multi results
                else: nlinesperplot = 1 # In all other cases, there's a single line per plot
                if colorsarg is None: colors = gridcolormap(nlinesperplot) # This is needed because this loop gets run multiple times, so can't just set and forget
                

                ################################################################################################################
                # Plot model estimates with uncertainty -- different for each of the different possibilities
                ################################################################################################################
                
                # e.g. single simulation, prev-tot: single line, single plot
                if not ismultisim and istotal:
                    plot(results.tvec, factor*best[0], lw=lw, c=colors[0]) # Index is 0 since only one possibility
                
                # e.g. single simulation, prev-pop: single line, separate plot per population
                if not ismultisim and isperpop: 
                    plot(results.tvec, factor*best[i], lw=lw, c=colors[0]) # Index is each individual population in a separate window
                
                # e.g. single simulation, prev-sta: either multiple lines or a stacked plot, depending on whether or not it's a number
                if not ismultisim and isstacked:
                    if ispercentage: # Multi-line plot
                        for l in range(nlinesperplot):
                            plot(results.tvec, factor*best[l], lw=lw, c=colors[l]) # Index is each different population
                    else: # Stacked plot
                        bottom = 0*results.tvec # Easy way of setting to 0...
                        origorder = arange(nlinesperplot)
                        plotorder = nlinesperplot-1-origorder
                        if reorder: plotorder = [reorder[k] for k in plotorder]
                        for k in plotorder: # Loop backwards so correct ordering -- first one at the top, not bottom
                            fill_between(results.tvec, factor*bottom, factor*(bottom+best[k]), facecolor=colors[k], alpha=1, lw=0, label=results.popkeys[k])
#                            fill_between(results.tvec, factor*bottom, factor*(bottom+best[k]), facecolor=gridcolormap(nlinesperplot)[k], alpha=1, lw=0, label=results.popkeys[k])
                            bottom += best[k]
                        for l in range(nlinesperplot): # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly...
                            plot((0, 0), (0, 0), color=colors[l], linewidth=10)
                
                # e.g. scenario, prev-tot; since stacked plots aren't possible with multiple lines, just plot the same in this case
                if ismultisim and (istotal or isstacked):
                    for l in range(nlinesperplot):
                        try: plot(results.tvec, factor*best[nlinesperplot-1-l], lw=lw, c=colors[nlinesperplot-1-l]) # Index is each different e.g. scenario
                        except: import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                
                if ismultisim and isperpop:
                    for l in range(nlinesperplot):
                        plot(results.tvec, factor*best[nlinesperplot-1-l][i], lw=lw, c=colors[nlinesperplot-1-l]) # Indices are different populations (i), then different e..g scenarios (l)



                ################################################################################################################
                # Plot data points with uncertainty
                ################################################################################################################
                
                # Plot uncertainty, but not for stacked plots
                if uncertainty and not isstacked: # It's not by population, except HIV prevalence, and uncertainty has been requested: plot bands
                    try: fill_between(results.tvec, factor*lower[i], factor*upper[i], facecolor=colors[0], alpha=alpha, lw=0)
                    except: print('Plotting uncertainty failed and/or not yet implemented')
                    
                # Plot data points with uncertainty -- for total or perpop plots, but not if multisim
                if not ismultisim and databest is not None and plotdata:
                    for y in range(len(results.datayears)):
                        plot(results.datayears[y]*array([1,1]), factor*array([datalow[i][y], datahigh[i][y]]), c=datacolor, lw=1)
                    scatter(results.datayears, factor*databest[i], c=datacolor, s=dotsize, lw=int(isestimate))



                
                ################################################################################################################
                # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
                ################################################################################################################
                
                # General configuration
                ax = gca()
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.get_xaxis().tick_bottom()
                ax.get_yaxis().tick_left()
                ax.title.set_fontsize(titlesize)
                ax.xaxis.label.set_fontsize(labelsize)
                ax.yaxis.label.set_fontsize(labelsize)
                for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)
    
                # Configure plot specifics
                currentylims = ylim()
                legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1,1), 'fontsize':legendsize, 'title':'', 'frameon':False, 'borderaxespad':2}
                plottitle = results.main[datatype].name
                if isperpop:  
                    plotylabel = plottitle
                    plottitle  = results.popkeys[i] # Add extra information to plot if by population
                    ax.set_ylabel(plotylabel)
                ax.set_title(plottitle)
                ax.set_ylim((0,currentylims[1]))
                ax.set_xlim((results.tvec[0], results.tvec[-1]))
                if not ismultisim:
#                    if istotal:  legend(['Model'], **legendsettings) # Single entry, "Total" # Feedback is that this isn't so useful, but keeping as placeholder for now
#                    if isperpop: legend(['Model'], **legendsettings) # Single entry, this population
                    if isstacked: 
                        handles, labels = ax.get_legend_handles_labels()
                        ax.legend(handles[::-1], labels[::-1], **legendsettings) # Multiple entries, all populations
                else:
                    legend(labels[::-1], **legendsettings) # Multiple simulations
                if useSIticks: SIticks(epiplots[pk])
                else:          commaticks(epiplots[pk])
                if doclose: close(epiplots[pk]) # Wouldn't want this guy hanging around like a bad smell
        
        return epiplots





##################################################################
## Plot improvements
##################################################################
def plotimprovement(results=None, figsize=(14,10), lw=2, titlesize=globaltitlesize, labelsize=globallabelsize, ticksize=globalticksize, **kwargs):
    ''' 
    Plot the result of an optimization or calibration -- WARNING, should not duplicate from plotepi()! 
    
    Accepts either a parset (generated from autofit) or an optimization result with a improvement attribute;
    failing that, it will try to treat the object as something that can be used directly, e.g.
        plotimprovement(results.improvement)
    also works.
    
    NOTE: do not call this function directly; instead, call via plotresults().
    
    Version: 2016jan23 by cliffk    
    '''

    if hasattr(results, 'improvement'): improvement = results.improvement # Get improvement attribute of object if it exists
    elif shape(results): improvement = results # Promising, has a length at least, but of course could still be wrong
    else: raise OptimaException('To plot the improvement, you must give either the improvement or an object containing the improvement as the first argument; try again')
    ncurves = len(improvement) # Try to figure to figure out how many there are
    
    # Set up figure and do plot
    sigfigs = 2 # Number of significant figures
    fig = figure(facecolor=(1,1,1), figsize=figsize)
    colors = gridcolormap(ncurves)
    
    # Plot model estimates with uncertainty
    absimprove = zeros(ncurves)
    relimprove = zeros(ncurves)
    maxiters = 0
    for i in range(ncurves): # Expect a list of 
        plot(improvement[i], lw=lw, c=colors[i]) # Actually do the plot
        absimprove[i] = improvement[i][0]-improvement[i][-1]
        relimprove[i] = 100*(improvement[i][0]-improvement[i][-1])/improvement[i][0]
        maxiters = maximum(maxiters, len(improvement[i]))
    
    # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
    ax = gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    ax.title.set_fontsize(titlesize)
    ax.xaxis.label.set_fontsize(labelsize)
    for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)
    
    # Configure plot
    currentylims = ylim()
    ax.set_xlabel('Iteration')
    
    abschange = sigfig(mean(absimprove), sigfigs)
    relchange = sigfig(mean(relimprove), sigfigs)
    ax.set_title('Change in outcome: %s (%s%%)' % (abschange, relchange)) # WARNING -- use mean or best?
    ax.set_ylim((0,currentylims[1]))
    ax.set_xlim((0, maxiters))
    
    close(fig)
    
    return fig






##################################################################
## Coverage plot
##################################################################
    
    
def plotbudget(multires=None, die=True, figsize=(14,10), legendsize=globallegendsize, usepie=True, verbose=2, **kwargs):
    ''' 
    Plot multiple allocations on bar charts -- intended for scenarios and optimizations.

    Results object must be of Multiresultset type.
    
    Version: 2017mar09
    '''
    
    # Preliminaries: process inputs and extract needed data
    budgets = dcp(multires.budgets)
    for b,budget in enumerate(budgets.values()): # Loop over all budgets
        for p,prog in enumerate(budget.values()): # Loop over all programs in the budget
            if budgets[b][p] is not None:
                budgets[b][p] = mean(budgets[b][p]) # If it's over multiple years (or not!), take the mean
    for key in budgets.keys(): # Budgets is an odict
        for i,val in enumerate(budgets[key].values()):
            if not(val>0): budgets[key][i] = 0.0 # Turn None, nan, etc. into 0.0
    
    alloclabels = budgets.keys() # WARNING, will this actually work if some values are None?
    proglabels = budgets[0].keys() 
    nprogs = len(proglabels)
    nallocs = len(alloclabels)
    progcolors = gridcolormap(nprogs)
    
    budgetplots = odict()
    
    # Make pie plots
    if usepie:
        for i in range(nallocs):
            fig = figure(facecolor=(1,1,1), figsize=figsize)
            
            # Make a pie
            ydata = budgets[i][:]
            pie(ydata, colors=progcolors)
            
            # Set up legend
            labels = dcp(proglabels)
            labels.reverse() # Wrong order otherwise, don't know why
            legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
            legend(labels, **legendsettings) # Multiple entries, all populations
            
            budgetplots['budget-%s'%i] = fig
      
    # Make bar plots
    else:
        fig = figure(facecolor=(1,1,1), figsize=figsize)
        ax = subplot(1,1,1)
        fig.subplots_adjust(bottom=0.50) # Less space on bottom
        
        for i in range(nprogs-1,-1,-1):
            xdata = arange(nallocs)+1
            ydata = array([budget[i] for budget in budgets.values()])
            bottomdata = array([sum(budget[:i]) for budget in budgets.values()])
            barh(xdata, ydata, left=bottomdata, color=progcolors[i], linewidth=0)
    
        # Set up legend
        labels = dcp(proglabels)
        labels.reverse() # Wrong order otherwise, don't know why
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
        ax.legend(labels, **legendsettings) # Multiple entries, all populations
        
        # Set up other things
        ax.set_xlabel('Spending')
        ax.set_yticks(arange(nallocs)+1)
        ax.set_yticklabels(alloclabels)
        ax.set_ylim(0,nallocs+1)
        
        SIticks(fig, axis='x')
        budgetplots['budget'] = fig
        close(fig)
    
    return budgetplots










##################################################################
## Coverage plot
##################################################################
    
    
def plotcoverage(multires=None, die=True, figsize=(14,10), legendsize=globallegendsize, verbose=2, **kwargs):
    ''' 
    Plot multiple allocations on bar charts -- intended for scenarios and optimizations.

    Results object must be of Multiresultset type.
    
    Version: 2017mar09
    '''
    
    # Preliminaries: process inputs and extract needed data
    coverages = dcp(multires.coverages)
    toplot = [item for item in coverages.values() if item] # e.g. [budget for budget in multires.budget]
    budgetyearstoplot = [budgetyears for budgetyears in multires.budgetyears.values() if budgetyears]
    
    proglabels = toplot[0].keys() 
    alloclabels = [key for k,key in enumerate(coverages.keys()) if coverages.values()[k]] # WARNING, will this actually work if some values are None?
    nprogs = len(proglabels)
    nallocs = len(alloclabels)
    
    
    colors = gridcolormap(nprogs)
    ax = []
    ymax = 0
    
    coverageplots = odict()
    
    for plt in range(nallocs):
        
        fig = figure(facecolor=(1,1,1), figsize=figsize)
        
        nbudgetyears = len(budgetyearstoplot[plt])
        ax.append(subplot(1,1,1))
        ax[-1].hold(True)
        barwidth = .5/nbudgetyears
        for y in range(nbudgetyears):
            progdata = zeros(len(toplot[plt]))
            for i,x in enumerate(toplot[plt][:]):
                if hasattr(x, '__len__'): 
                    try: progdata[i] = x[y]
                    except: 
                        try: progdata[i] = x[-1] # If not enough data points, just use last -- WARNING, KLUDGY
                        except: progdata[i] = 0. # If not enough data points, just use last -- WARNING, KLUDGY
                else:                     progdata[i] = x
            progdata *= 100 
            xbardata = arange(nprogs)+.75+barwidth*y
            for p in range(nprogs):
                if nbudgetyears>1: barcolor = colors[y] # More than one year? Color by year
                else: barcolor = colors[p] # Only one year? Color by program
                if p==nprogs-1: yearlabel = budgetyearstoplot[plt][y]
                else: yearlabel=None
                ax[-1].bar([xbardata[p]], [progdata[p]], label=yearlabel, width=barwidth, color=barcolor)
        if nbudgetyears>1: ax[-1].legend(frameon=False)
        ax[-1].set_xticks(arange(nprogs)+1)
        ax[-1].set_xticklabels('')
        ax[-1].set_xlim(0,nprogs+1)
        
        ylabel = 'Coverage (%)'
        ax[-1].set_ylabel(ylabel)
        if nallocs>1: ax[-1].set_title('Coverage -- %s' % alloclabels[plt])
        else:         ax[-1].set_title('Program coverage')
        ymax = maximum(ymax, ax[-1].get_ylim()[1])
        
        # Set up legend
        labels = dcp(proglabels)
        labels.reverse() # Wrong order otherwise, don't know why
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False}
        ax[-1].legend(labels, **legendsettings) # Multiple entries, all populations
        
        # Tidy up
        SIticks(fig)
        coverageplots['coverages-%s'%plt] = fig
        close(fig)
    
    for thisax in ax: thisax.set_ylim(0,ymax) # So they all have the same scale
    
    return coverageplots











##################################################################
## Plot cascade
##################################################################
def plotcascade(results=None, aspercentage=False, doclose=True, colors=None, figsize=(14,10), lw=2, titlesize=globaltitlesize, labelsize=globallabelsize, 
                ticksize=globalticksize, legendsize=globallegendsize, useSIticks=True, plotdata=True, **kwargs):
    ''' 
    Plot the treatment cascade.
    
    NOTE: do not call this function directly; instead, call via plotresults().
    
    Version: 2016sep28    
    '''
    
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
    cascadelist = ['numplhiv', 'numdiag', 'numevercare', 'numincare', 'numtreat', 'numsuppressed'] 
    cascadenames = ['Undiagnosed', 'Diagnosed', 'Linked to care', 'Retained in care', 'Treated', 'Virally suppressed']
        
    # Handle colors
    if colors is None: colors = gridcolormap(len(cascadelist))
    elif colors=='alpine': colors = vectocolor(arange(len(cascadelist)), cmap=alpinecolormap()) # Handle this as a special case
    elif type(colors)==str: colors = vectocolor(arange(len(cascadelist)+2), cmap=colors)[1:-1] # Remove first and last element
    else: raise OptimaException('Can''t figure out color %s' % colors)
    
    for plt in range(nsims): # WARNING, copied from plotallocs()
        bottom = 0*results.tvec # Easy way of setting to 0...
        
        ## Do the plotting
        fig = figure(facecolor=(1,1,1), figsize=figsize)
        for k,key in enumerate(reversed(cascadelist)): # Loop backwards so correct ordering -- first one at the top, not bottom
            if ismultisim: 
                thisdata = results.main[key].tot[plt] # If it's a multisim, need an extra index for the plot number
                if aspercentage: thisdata *= 100./results.main['numplhiv'].tot[plt]
            else:
                thisdata = results.main[key].tot[0] # Get the best estimate
                if aspercentage: thisdata *= 100./results.main['numplhiv'].tot[0]
            fill_between(results.tvec, bottom, thisdata, facecolor=colors[k], alpha=1, lw=0)
            bottom = dcp(thisdata) # Set the bottom so it doesn't overwrite
            plot((0, 0), (0, 0), color=colors[len(colors)-k-1], linewidth=10, label=cascadenames[k]) # Colors are in reverse order
        if plotdata and not aspercentage: # Don't try to plot if it's a percentage
            thisdata = results.main['numtreat'].datatot[0]
            scatter(results.datayears, thisdata, c=(0,0,0), label='Treatment data')
        
        ## Configure plot -- WARNING, copied from plotepi()
        ax = gca()
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()
        ax.title.set_fontsize(titlesize)
        ax.xaxis.label.set_fontsize(labelsize)
        ax.yaxis.label.set_fontsize(labelsize)
        for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)

        # Configure legend
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'', 'frameon':False, 'scatterpoints':1}
        ax.legend(**legendsettings) # Multiple entries, all populations
        
        # Configure rest of the plot
        if ismultisim: ax.set_title('Cascade -- %s' % titles[plt])
        else:          ax.set_title('Cascade')
        if aspercentage: ax.set_ylabel('Percentage of PLHIV')
        else:            ax.set_ylabel('Number of PLHIV')
                
        if aspercentage: ax.set_ylim((0,100))
        else:            ax.set_ylim((0,ylim()[1]))
        ax.set_xlim((results.tvec[0], results.tvec[-1]))
        
        if useSIticks: SIticks(fig)
        else:          commaticks(fig)
        if doclose: close(fig)
        
        cascadeplots['cascade-%s'%plt] = fig
    
    return cascadeplots






def plotallocations(project=None, budgets=None, colors=None, factor=1e6, compare=True, plotfixed=False):
    ''' Plot allocations in bar charts '''
    
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
        colors = gridcolormap(nprogs)
            
    
    fig = figure(facecolor=(1,1,1), figsize=(10,10))
    fig.subplots_adjust(left=0.10) # Less space on left
    fig.subplots_adjust(right=0.98) # Less space on right
    fig.subplots_adjust(top=0.95) # Less space on bottom
    fig.subplots_adjust(bottom=0.35) # Less space on bottom
    fig.subplots_adjust(wspace=0.30) # More space between
    fig.subplots_adjust(hspace=0.40) # More space between
    
    ax = []
    xbardata = arange(nprogs)+0.5
    ymax = 0
    nplt = len(budgets)
    for plt in range(nplt):
        ax.append(subplot(len(budgets),1,plt+1))
        ax[-1].hold(True)
        for p,ind in enumerate(indices):
            ax[-1].bar([xbardata[p]], [budgets[plt][ind]/factor], color=colors[p], linewidth=0)
            if plt==1 and compare:
                ax[-1].bar([xbardata[p]], [budgets[0][ind]/factor], color='None', linewidth=1)
        ax[-1].set_xticks(arange(nprogs)+1)
        if plt!=nplt: ax[-1].set_xticklabels('')
        if plt==nplt-1: 
            ax[-1].set_xticklabels(progs,rotation=90)
            plot([0,nprogs+1],[0,0],c=(0,0,0))
        ax[-1].set_xlim(0,nprogs+1)
        
        if factor==1: ax[-1].set_ylabel('Spending (US$)')
        elif factor==1e3: ax[-1].set_ylabel("Spending (US$'000s)")
        elif factor==1e6: ax[-1].set_ylabel('Spending (US$m)')
        ax[-1].set_title(labels[plt])
        ymax = maximum(ymax, ax[-1].get_ylim()[1])
    for a in ax:
        a.set_ylim([0,ymax])
    
    return fig
    
    
##################################################################
## Plot things by CD4
##################################################################
def plotbycd4(results=None, whattoplot='people', figsize=(14,10), lw=2, titlesize=globaltitlesize, labelsize=globallabelsize, 
                ticksize=globalticksize, legendsize=globallegendsize, ind=0, **kwargs):
    ''' 
    Plot deaths or people by CD4
    NOTE: do not call this function directly; instead, call via plotresults().
    '''
    
    # Figure out what kind of result it is
    if type(results)==Resultset: 
        ismultisim = False
        nsims = 1
    elif type(results)==Multiresultset:
        ismultisim = True
        titles = results.keys # Figure out the labels for the different lines
        nsims = len(titles) # How ever many things are in results
    else: 
        errormsg = 'Results input to plotbycd4() must be either Resultset or Multiresultset, not "%s".' % type(results)
        raise OptimaException(errormsg)

    # Set up figure and do plot
    fig = figure(figsize=figsize)
    
    titlemap = {'people': 'PLHIV', 'death': 'Deaths'}
    settings = results.projectref().settings
    hivstates = settings.hivstates
    indices = arange(0, len(results.raw[ind]['tvec']), int(round(1.0/(results.raw[ind]['tvec'][1]-results.raw[ind]['tvec'][0]))))
    colors = gridcolormap(len(hivstates))
    
    for plt in range(nsims): # WARNING, copied from plotallocs()
        bottom = 0.*results.tvec # Easy way of setting to 0...
        thisdata = 0.*results.tvec # Initialise
        
        ## Do the plotting
        subplot(nsims,1,plt+1)
        for s,state in enumerate(reversed(hivstates)): # Loop backwards so correct ordering -- first one at the top, not bottom
            if ismultisim: thisdata += results.raw[plt][ind][whattoplot][getattr(settings,state),:,:].sum(axis=(0,1))[indices] # If it's a multisim, need an extra index for the plot number
            else:          thisdata += results.raw[ind][whattoplot][getattr(settings,state),:,:].sum(axis=(0,1))[indices] # Get the best estimate
            fill_between(results.tvec, bottom, thisdata, facecolor=colors[s], alpha=1, lw=0)
            bottom = dcp(thisdata) # Set the bottom so it doesn't overwrite
            plot((0, 0), (0, 0), color=colors[len(colors)-s-1], linewidth=10) # Colors are in reverse order
        
        ## Configure plot -- WARNING, copied from plotepi()
        ax = gca()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()
        ax.title.set_fontsize(titlesize)
        ax.xaxis.label.set_fontsize(labelsize)
        for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)

        # Configure plot specifics
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':'',
                          'frameon':False}
        if ismultisim: ax.set_title(titlemap[whattoplot]+'-- %s' % titles[plt])
        else: ax.set_title(titlemap[whattoplot])
        ax.set_ylim((0,ylim()[1]))
        ax.set_xlim((results.tvec[0], results.tvec[-1]))
        ax.legend(results.settings.hivstatesfull, **legendsettings) # Multiple entries, all populations
        
    SIticks(fig)
    close(fig)
    
    return fig    


from optima import promotetoarray
from pylab import isnan, linspace

def plotcostcov(program=None, year=None, parset=None, results=None, plotoptions=None, existingFigure=None, plotbounds=True, npts=100, maxupperlim=1e8, doplot=False):
    """ Plot the cost-coverage curve for a single program"""
    
    # Put plotting imports here so fails at the last possible moment
    from pylab import figure, figtext, isinteractive, ioff, ion, close, show
    from matplotlib.ticker import MaxNLocator
    import textwrap
    
    wasinteractive = isinteractive() # Get current state of interactivity
    ioff() # Just in case, so we don't flood the user's screen with figures

    year = promotetoarray(year)
    colors = gridcolormap(len(year))
    plotdata = odict()
    
    # Get caption & scatter data 
    caption = plotoptions['caption'] if plotoptions and plotoptions.get('caption') else ''
    costdata = dcp(program.costcovdata['cost'])

    # Make x data... 
    if plotoptions and plotoptions.get('xupperlim') and ~isnan(plotoptions['xupperlim']):
        xupperlim = plotoptions['xupperlim']
    else:
        if costdata: xupperlim = 1.5*max(costdata)
        else: xupperlim = maxupperlim
    xlinedata = linspace(0,xupperlim,npts)

    if plotoptions and plotoptions.get('perperson'):
        xlinedata = linspace(0,xupperlim*program.gettargetpopsize(year[-1],parset),npts)

    # Create x line data and y line data
    try:
        y_l = program.getcoverage(x=xlinedata, year=year, parset=parset, results=results, total=True, proportion=False, toplot=True, sample='l')
        y_m = program.getcoverage(x=xlinedata, year=year, parset=parset, results=results, total=True, proportion=False, toplot=True, sample='best')
        y_u = program.getcoverage(x=xlinedata, year=year, parset=parset, results=results, total=True, proportion=False, toplot=True, sample='u')
    except:
        y_l,y_m,y_u = None,None,None
    plotdata['ylinedata_l'] = y_l
    plotdata['ylinedata_m'] = y_m
    plotdata['ylinedata_u'] = y_u
    plotdata['xlabel'] = 'Spending'
    plotdata['ylabel'] = 'Number covered'

    # Flag to indicate whether we will adjust by population or not
    if plotoptions and plotoptions.get('perperson'):
        if costdata:
            for yrno, yr in enumerate(program.costcovdata['t']):
                targetpopsize = program.gettargetpopsize(t=yr, parset=parset, results=results)
                costdata[yrno] /= targetpopsize[0]
        if not (plotoptions and plotoptions.get('xupperlim') and ~isnan(plotoptions['xupperlim'])):
            if costdata: xupperlim = 1.5*max(costdata) 
            else: xupperlim = 1e3
        plotdata['xlinedata'] = linspace(0,xupperlim,npts)
    else:
        plotdata['xlinedata'] = xlinedata
        
    cost_coverage_figure = existingFigure if existingFigure else figure()
    cost_coverage_figure.hold(True)
    axis = cost_coverage_figure.gca()

    axis.set_position((0.1, 0.35, .8, .6)) # to make a bit of room for extra text
    figtext(.1, .05, textwrap.fill(caption))
    
    if y_m is not None:
        for yr in range(y_m.shape[0]):
            axis.plot(
                plotdata['xlinedata'],
                plotdata['ylinedata_m'][yr],
                linestyle='-',
                linewidth=2,
                color=colors[yr],
                label=year[yr])
            if plotbounds:
                axis.fill_between(plotdata['xlinedata'],
                                  plotdata['ylinedata_l'][yr],
                                  plotdata['ylinedata_u'][yr],
                                  facecolor=colors[yr],
                                  alpha=.1,
                                  lw=0)
    axis.scatter(
        costdata,
        program.costcovdata['coverage'],
        color='#666666')
    

    axis.set_xlim([0, xupperlim])
    axis.set_ylim(bottom=0)
    axis.tick_params(axis='both', which='major', labelsize=11)
    axis.set_xlabel(plotdata['xlabel'], fontsize=11)
    axis.set_ylabel(plotdata['ylabel'], fontsize=11)
    axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
    axis.set_title(program.short)
    axis.get_xaxis().get_major_formatter().set_scientific(False)
    axis.get_yaxis().get_major_formatter().set_scientific(False)
    if len(year)>1: axis.legend(loc=4)
    
    # Tidy up
    if not doplot: close(cost_coverage_figure)
    if wasinteractive: ion()
    if doplot: show()

    return cost_coverage_figure