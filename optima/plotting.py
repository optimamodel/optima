'''
PLOTTING

This file generates all the figure files -- either for use with the Python backend, or
for the frontend via MPLD3.

To add a new plot, you need to both add it to getplotselections so it will show up in the interface;
plotresults so it will be sent to the right spot; and then add the actual function to do the
polotting.

Version: 2016jan24
'''

from optima import OptimaException, Resultset, Multiresultset, odict, printv, gridcolormap, sigfig
from numpy import array, ndim, maximum, arange, zeros, mean
from pylab import isinteractive, ioff, ion, figure, plot, close, ylim, fill_between, scatter, gca, subplot

# Define allowable plot formats -- 3 kinds, but allow some flexibility for how they're specified
epiformatslist = array([['t', 'tot', 'total'], ['p', 'per', 'per population'], ['s', 'sta', 'stacked']])
epiformatsdict = odict([('tot',epiformatslist[0]), ('per',epiformatslist[1]), ('sta',epiformatslist[2])]) # WARNING, could be improved
datacolor = (0,0,0) # Define color for data point -- WARNING, should this be in settings.py?
defaultepiplots = ['prev-tot', 'prev-per', 'numplhiv-sta', 'numinci-sta', 'numdeath-sta', 'numdiag-sta', 'numtreat-sta'] # Default epidemiological plots
defaultplots = ['improvement', 'budget', 'cascade'] + defaultepiplots # Define the default plots available


def getplotselections(results):
    ''' 
    From the inputted results structure, figure out what the available kinds of plots are. List results-specific
    plot types first (e.g., allocations), followed by the standard epi plots, and finally (if available) other
    plots such as the cascade.
    
    Version: 2016jan28
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
        plotselections['keys'] += ['improvement'] # WARNING, maybe more standard to do append()...
        plotselections['names'] += ['Improvement']
    
    
    ## Add selection for budget allocations and coverage
    budcovdict = odict([('budget','Budget allocation'), ('coverage','Program coverage')])
    for budcov in budcovdict.keys():
        if hasattr(results, budcov) and getattr(results, budcov) is not None:
            if all([item is not None for item in getattr(results, budcov).values()]): # Make sure none of the individual budgets are none either
                plotselections['keys'] += [budcov] # e.g. 'budget'
                plotselections['names'] += [budcovdict[budcov]] # e.g. 'Budget allocation'
    
    ## Cascade plot is always available, since epi is always available
    plotselections['keys'] += ['cascade']
    plotselections['names'] += ['Treatment cascade']
    
    ## Get plot selections for plotepi
    plotepikeys = list()
    plotepinames = list()
    
    epikeys = results.main.keys() # e.g. 'prev'
    epinames = [thing.name for thing in results.main.values()]
    episubkeys = epiformatslist[:,1] # 'tot' = single overall value; 'per' = separate figure for each plot; 'sta' = stacked or multiline plot
    episubnames = epiformatslist[:,2] # e.g. 'per population'
    
    for key in epikeys: # e.g. 'prev'
        for subkey in episubkeys: # e.g. 'tot'
            if not(ismultisim and subkey=='sta'): # Stacked multisim plots don't make sense
                plotepikeys.append(key+'-'+subkey)
    for name in epinames: # e.g. 'HIV prevalence'
        for subname in episubnames: # e.g. 'total'
            if not(ismultisim and subname=='stacked'): # Stacked multisim plots don't make sense -- WARNING, this is clunky!!!
                plotepinames.append(name+' -- '+subname)
    
    
    plotselections['keys'] += plotepikeys
    plotselections['names'] += plotepinames
    for key in plotselections['keys']: # Loop over each key
        plotselections['defaults'].append(key in defaultplots) # Append True if it's in the defaults; False otherwise
    
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
            allplots['improvement'] = plotimprovement(results, die=die, **kwargs)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot improvement: "%s"' % E.message, 1, verbose)
        
    
    ## Add budget and coverage plots
    for budcov in ['budget', 'coverage']:
        if budcov in toplot:
            toplot.remove(budcov) # Because everything else is passed to plotepi()
            try: 
                allplots[budcov] = plotallocs(results, which=budcov, die=die, **kwargs)
            except OptimaException as E: 
                if die: raise E
                else: printv('Could not plot "%s" allocation: "%s"' % (budcov, E.message), 1, verbose)
    
    ## Add cascade plot
    if 'cascade' in toplot:
        toplot.remove('cascade') # Because everything else is passed to plotepi()
        try: 
            allplots['cascade'] = plotcascade(results, die=die, **kwargs)
        except OptimaException as E: 
            if die: raise E
            else: printv('Could not plot cascade: "%s"' % E.message, 1, verbose)
    
    
    ## Add epi plots -- WARNING, I hope this preserves the order! ...It should...
    epiplots = plotepi(results, toplot=toplot, die=die, **kwargs)
    allplots.update(epiplots)
    
    # Tidy up: turn interactivity back on
    if wasinteractive: ion() 
    
    return allplots





def plotepi(results, toplot=None, uncertainty=False, die=True, verbose=2, figsize=(14,10), alpha=0.2, lw=2, dotsize=50,
            titlesize=14, labelsize=12, ticksize=10, legendsize=10, **kwargs):
        '''
        Render the plots requested and store them in a list. Argument "toplot" should be a list of form e.g.
        ['prev-tot', 'inci-per']

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
        if toplot is None: toplot = defaultepiplots # If not specified, plot default plots
        elif type(toplot) in [str, tuple]: toplot = [toplot] # If single value, put inside list
        epiplots = odict()


        ## Validate plot keys
        for pk,plotkey in enumerate(toplot):
            datatype, plotformat = None, None
            if type(plotkey) not in [str, list, tuple]: 
                errormsg = 'Could not understand "%s": must a string, e.g. "numplhiv-tot", or a list/tuple, e.g. ["numpliv","tot"]' % str(plotkey)
                raise OptimaException(errormsg)
            else:
                try:
                    if type(plotkey)==str: datatype, plotformat = plotkey.split('-')
                    elif type(plotkey) in [list, tuple]: datatype, plotformat = plotkey[0], plotkey[1]
                except:
                    errormsg = 'Could not parse plot key "%s"; please ensure format is e.g. "numplhiv-tot"' % plotkey
                    if die: raise OptimaException(errormsg)
                    else: printv(errormsg, 4, verbose)
            if datatype not in results.main.keys():
                errormsg = 'Could not understand data type "%s"; should be one of:\n%s' % (datatype, results.main.keys())
                if die: raise OptimaException(errormsg)
                else: printv(errormsg, 4, verbose)
            plotformat = plotformat[0] # Do this because only really care about the first letter of e.g. 'total' -- WARNING, flexible but could cause subtle bugs
            if plotformat not in epiformatslist.flatten():
                errormsg = 'Could not understand type "%s"; should be one of:\n%s' % (plotformat, epiformatslist)
                if die: raise OptimaException(errormsg)
                else: printv(errormsg, 4, verbose)
            toplot[pk] = (datatype, plotformat) # Convert to tuple for this index
        
        # Remove failed ones
        toplot = [thisplot for thisplot in toplot if None not in thisplot] # Remove a plot if datatype or plotformat is None


        ################################################################################################################
        ## Loop over each plot
        ################################################################################################################
        for plotkey in toplot:
            
            # Unpack tuple
            datatype, plotformat = plotkey 
            
            isnumber = results.main[datatype].isnumber # Distinguish between e.g. HIV prevalence and number PLHIV
            factor = 1.0 if isnumber else 100.0 # Swap between number and percent
            istotal   = (plotformat=='t') # Only using first letter, see above...
            isperpop  = (plotformat=='p')
            isstacked = (plotformat=='s')
            
            
            ################################################################################################################
            ## Process the plot data
            ################################################################################################################
            
            # Decide which attribute in results to pull -- doesn't map cleanly onto plot types
            if istotal or (isstacked and ismultisim): attrtype = 'tot' # Only plot total if it's a scenario and 'stacked' was requested
            else: attrtype = 'pops'
            
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
                except: # No? Just use the best data
                    lower = best
                    upper = best
                try: # Try loading actual data -- very likely to not exist
                    tmp = getattr(results.main[datatype], 'data'+attrtype)
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
            
            for i,pk in enumerate(pkeys): # Either loop over individual population plots, or just plot a single plot, e.g. pk='prev-per-FSW'
                
                epiplots[pk] = figure(figsize=figsize) # If it's anything other than HIV prevalence by population, create a single plot
    
                if isstacked or ismultisim: nlinesperplot = len(best) # There are multiple lines per plot for both pops poptype and for plotting multi results
                else: nlinesperplot = 1 # In all other cases, there's a single line per plot
                colors = gridcolormap(nlinesperplot)
                
                # Plot uncertainty, but not for stacked plots
                if uncertainty and not isstacked: # It's not by population, except HIV prevalence, and uncertainty has been requested: plot bands
                    try: fill_between(results.tvec, factor*lower[i], factor*upper[i], facecolor=colors[0], alpha=alpha, lw=0)
                    except: print('Plotting uncertainty failed and/or not yet implemented')
                    
                # Plot data points with uncertainty -- for total or perpop plots, but not if multisim
                if not isstacked and not ismultisim and databest is not None:
                    scatter(results.datayears, factor*databest[i], c=datacolor, s=dotsize, lw=0)
                    for y in range(len(results.datayears)):
                        plot(results.datayears[y]*array([1,1]), factor*array([datalow[i][y], datahigh[i][y]]), c=datacolor, lw=1)



                ################################################################################################################
                # Plot model estimates with uncertainty -- different for each of the different possibilities
                ################################################################################################################
                
                # e.g. single simulation, prev-tot: single line, single plot
                if not ismultisim and istotal:
                    plot(results.tvec, factor*best[0], lw=lw, c=colors[0]) # Index is 0 since only one possibility
                
                # e.g. single simulation, prev-per: single line, separate plot per population
                if not ismultisim and isperpop: 
                    plot(results.tvec, factor*best[i], lw=lw, c=colors[0]) # Index is each individual population in a separate window
                
                # e.g. single simulation, prev-sta: either multiple lines or a stacked plot, depending on whether or not it's a number
                if not ismultisim and isstacked:
                    if isnumber: # Stacked plot
                        bottom = 0*results.tvec # Easy way of setting to 0...
                        for l in range(nlinesperplot): # Loop backwards so correct ordering -- first one at the top, not bottom
                            k = nlinesperplot-1-l # And in reverse order
                            fill_between(results.tvec, factor*bottom, factor*(bottom+best[k]), facecolor=colors[k], alpha=1, lw=0)
                            bottom += best[k]
                        for l in range(nlinesperplot): # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly...
                            plot((0, 0), (0, 0), color=colors[l], linewidth=10)
                    else: # Multi-line plot
                        for l in range(nlinesperplot):
                            plot(results.tvec, factor*best[l], lw=lw, c=colors[l]) # Index is each different population
                
                # e.g. scenario, prev-tot; since stacked plots aren't possible with multiple lines, just plot the same in this case
                if ismultisim and (istotal or isstacked):
                    for l in range(nlinesperplot):
                        plot(results.tvec, factor*best[l], lw=lw, c=colors[l]) # Index is each different e.g. scenario
                
                if ismultisim and isperpop:
                    for l in range(nlinesperplot):
                        plot(results.tvec, factor*best[l][i], lw=lw, c=colors[l]) # Indices are different populations (i), then different e..g scenarios (l)

                
                
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
                for item in ax.get_xticklabels() + ax.get_yticklabels(): item.set_fontsize(ticksize)
    
                # Configure plot specifics
                currentylims = ylim()
                legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':''}
                ax.set_xlabel('Year')
                plottitle = results.main[datatype].name
                if istotal:   plottitle += ' -- total'
                if isperpop:  plottitle += ' -- ' + results.popkeys[i]
                if isstacked: plottitle += ' -- by population'
                ax.set_title(plottitle)
                ax.set_ylim((0,currentylims[1]))
                ax.set_xlim((results.tvec[0], results.tvec[-1]))
                if not ismultisim:
                    if istotal:  ax.legend(['Total'], **legendsettings) # Single entry, "Total"
                    if isperpop: ax.legend([results.popkeys[i]], **legendsettings) # Single entry, this population
                    if isstacked: ax.legend(results.popkeys, **legendsettings) # Multiple entries, all populations
                else:
                    ax.legend(labels, **legendsettings) # Multiple simulations
                
                close(epiplots[pk]) # Wouldn't want this guy hanging around like a bad smell
        
        return epiplots





##################################################################
## Plot improvements
##################################################################
def plotimprovement(results=None, figsize=(14,10), lw=2, titlesize=14, labelsize=12, ticksize=10, **kwargs):
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
    elif hasattr(results, '__len__'): improvement = results # Promising, has a length at least, but of course could still be wrong
    else: raise OptimaException('To plot the improvement, you must give either the improvement or an object containing the improvement as the first argument; try again')
    ncurves = len(improvement) # Try to figure to figure out how many there are
    
    # Set up figure and do plot
    sigfigs = 2 # Number of significant figures
    fig = figure(figsize=figsize)
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
## Allocation plots
##################################################################
    
    
def plotallocs(multires=None, which=None, die=True, figsize=(14,10), verbose=2, **kwargs):
    ''' 
    Plot multiple allocations on bar charts -- intended for scenarios and optimizations.

    Results object must be of Multiresultset type.
    
    "which" should be either 'budget' or 'coverage'
    
    Version: 2016jan27
    '''
    
    # Preliminaries: process inputs and extract needed data
    try: 
        toplot = [item for item in getattr(multires, which).values() if item] # e.g. [budget for budget in multires.budget]
    except: 
        errormsg = 'Unable to plot allocations: no attribute "%s" found for this multiresults object:\n%s' % (which, multires)
        if die: raise OptimaException(errormsg)
        else: printv(errormsg, 1, verbose)
    budgetyearstoplot = [budgetyears for budgetyears in multires.budgetyears.values() if budgetyears]
    
    proglabels = toplot[0].keys() 
    alloclabels = [key for k,key in enumerate(getattr(multires, which).keys()) if getattr(multires, which).values()[k]] # WARNING, will this actually work if some values are None?
    nprogs = len(proglabels)
    nallocs = len(alloclabels)
    
    fig = figure(figsize=figsize)
    fig.subplots_adjust(bottom=0.30) # Less space on bottom
    fig.subplots_adjust(hspace=0.50) # More space between
    colors = gridcolormap(nprogs)
    ax = []
    ymax = 0
    
    for plt in range(nallocs):
        nbudgetyears = len(budgetyearstoplot[plt])
        ax.append(subplot(nallocs,1,plt+1))
        ax[-1].hold(True)
        barwidth = .5/nbudgetyears
        for y in range(nbudgetyears):
            progdata = array([x[y] for x in toplot[plt][:]]) # Otherwise, multiplication simply duplicates the array
            if which=='coverage': progdata *= 100 
            xbardata = arange(nprogs)+.75+barwidth*y
            for p in range(nprogs):
                if nbudgetyears>1: barcolor = colors[y] # More than one year? Color by year
                else: barcolor = colors[p] # Only one year? Color by program
                if p==nprogs-1: yearlabel = budgetyearstoplot[plt][y]
                else: yearlabel=None
                ax[-1].bar([xbardata[p]], [progdata[p]], label=yearlabel, width=barwidth, color=barcolor)
        if nbudgetyears>1: ax[-1].legend()
        ax[-1].set_xticks(arange(nprogs)+1)
        if plt<nprogs: ax[-1].set_xticklabels('')
        if plt==nallocs-1: ax[-1].set_xticklabels(proglabels,rotation=90)
        ax[-1].set_xlim(0,nprogs+1)
        
        ylabel = 'Spending (US$)' if which=='budget' else 'Coverage (% of targeted)'
        ax[-1].set_ylabel(ylabel)
        ax[-1].set_title(alloclabels[plt])
        ymax = maximum(ymax, ax[-1].get_ylim()[1])
        
    close(fig)
    
    return fig





##################################################################
## Plot improvements
##################################################################
def plotcascade(results=None, figsize=(14,10), lw=2, titlesize=14, labelsize=12, ticksize=10, legendsize=10, **kwargs):
    ''' 
    Plot the treatment cascade.
    
    NOTE: do not call this function directly; instead, call via plotresults().
    
    Version: 2016jan28    
    '''
    
    # Figure out what kind of result it is -- WARNING, copied from 
    if type(results)==Resultset: 
        ismultisim = False
        nsims = 1
        titles = ['PLHIV'] # WARNING, not sure what label this should be, if any
    elif type(results)==Multiresultset:
        ismultisim = True
        titles = results.keys # Figure out the labels for the different lines
        nsims = len(titles) # How ever many things are in results
    else: 
        errormsg = 'Results input to plotcascade() must be either Resultset or Multiresultset, not "%s".' % type(results)
        raise OptimaException(errormsg)

    # Set up figure and do plot
    fig = figure(figsize=figsize)
    
    cascadelist = ['numplhiv', 'numdiag', 'numtreat'] 
    cascadenames = []
    colors = gridcolormap(len(cascadelist))
    
    
    bottom = 0*results.tvec # Easy way of setting to 0...
    for plt in range(nsims): # WARNING, copied from plotallocs()
        
        ## Do the plotting
        subplot(nsims,1,plt+1)
        for k,key in enumerate(cascadelist): # Loop backwards so correct ordering -- first one at the top, not bottom
            if ismultisim: thisdata = results.main[key][plt].tot[0] # If it's a multisim, need an extra index for the plot number
            else:          thisdata = results.main[key].tot[0]
            fill_between(results.tvec, bottom, thisdata, facecolor=colors[k], alpha=1, lw=0)
            cascadenames.append(results.main[key].name) # Store the name for the legend later
        
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
        
        legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':''}
        ax.set_title('Cascade -- %s' % titles[plt])
        ax.set_xlabel('Year')
        ax.set_ylim((0,ylim()[1]))
        ax.set_xlim((results.tvec[0], results.tvec[-1]))
        ax.legend(cascadenames, **legendsettings) # Multiple entries, all populations
        
    close(fig)
    
    return fig