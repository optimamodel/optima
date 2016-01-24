'''
MAKEPLOTS

This file generates all the figure files -- either for use with the Python backend, or
for the frontend via MPLD3.
'''

from optima import Resultset, Multiresultset, odict, gridcolormap
from numpy import array, ndim, maximum, arange
from pylab import isinteractive, ioff, ion, figure, plot, close, ylim, fill_between, scatter, gca, subplot

# Define allowable plot formats -- 3 kinds, but allow some flexibility for how they're specified
plotformatslist = array([['t', 'tot', 'total'], ['p', 'per', 'per population'], ['s', 'sta', 'stacked']])
plotformatsdict = odict({'tot':plotformatslist[0], 'per':plotformatslist[1], 'sta':plotformatslist[2]})
datacolor = (0,0,0) # Define color for data point -- WARNING, should this be in settings.py?


def plotepi(results, which=None, uncertainty=False, verbose=2, figsize=(14,10), alpha=0.2, lw=2, dotsize=50,
            titlesize=14, labelsize=12, ticksize=10, legendsize=10):
        '''
        Render the plots requested and store them in a list. Argument "which" should be a list of form e.g.
        ['prev-tot', 'inci-pops']

        This function returns an odict of figures, which can then be saved as MPLD3, etc.

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
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures
        if which is None: which = [datatype+'-'+plotformat for datatype in results.main.keys() for plotformat in ['p', 's', 't']] # Just plot everything if not specified
        elif type(which) in [str, tuple]: which = [which] # If single value, put inside list

        # Loop over each plot
        epiplots = odict()
        for plotkey in which:

            ################################################################################################################
            ## Parse user input
            ################################################################################################################
            if type(plotkey) not in [str, list, tuple]: 
                errormsg = 'Could not understand "%s": must a string, e.g. "numplhiv-tot", or a list/tuple, e.g. ["numpliv","tot"]' % str(plotkey)
                raise OptimaException(errormsg)
            else:
                try:
                    if type(plotkey)==str: datatype, plotformat = plotkey.split('-')
                    elif type(plotkey) in [list, tuple]: datatype, plotformat = plotkey[0], plotkey[1]
                except:
                    errormsg = 'Could not parse plot key "%s"; please ensure format is e.g. "numplhiv-tot"' % plotkey
                    raise OptimaException(errormsg)
            if datatype not in results.main.keys():
                errormsg = 'Could not understand data type "%s"; should be one of:\n%s' % (datatype, results.main.keys())
                raise OptimaException(errormsg)
            if plotformat not in plotformatslist.flatten():
                errormsg = 'Could not understand type "%s"; should be one of:\n%s' % (plotformat, plotformatslist)
                raise OptimaException(errormsg)
            
            try:
                isnumber = results.main[datatype].isnumber # Distinguish between e.g. HIV prevalence and number PLHIV
                factor = 1.0 if isnumber else 100.0 # Swap between number and percent
            except:
                errormsg = 'Unable to find key "%s" in results' % datatype
                raise OptimaException(errormsg)
                
            istotal   = (plotformat in plotformatsdict['tot'])
            isperpop  = (plotformat in plotformatsdict['per'])
            isstacked = (plotformat in plotformatsdict['sta'])
            
            
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
    
                # Tidy up: close plots that were opened
                close(epiplots[pk])


        if wasinteractive: ion() # Turn interactivity back on
        return epiplots





##################################################################
## Plot mismatches
##################################################################
def plotmismatch(results=None, verbose=2, figsize=(10,6), lw=2, dotsize=50, titlesize=14, labelsize=12, ticksize=10, legendsize=10):
    ''' 
    Plot the result of an optimization or calibration -- WARNING, should not duplicate from plotepi()! 
    
    Accepts either a parset (generated from autofit) or an optimization result with a mismatch attribute;
    failing that, it will try to treat the object as something that can be used directly, e.g.
        plotmismatch(results.mismatch)
    also works.
    
    Version: 2016jan19 by cliffk    
    '''

    if hasattr(results, 'mismatch'): mismatch = results.mismatch # Get mismatch attribute of object if it exists
    elif ndim(results)==1: mismatch = results # Promising, has the right dimensionality at least, but of course could still be wrong
    else: raise OptimaException('To plot the mismatch, you must give either the mismatch or an object containing the mismatch as the first argument; try again')
    
    # Set up figure and do plot
    fig = figure(figsize=figsize, facecolor=(1,1,1))
    
    # Plot model estimates with uncertainty
    plot(mismatch, lw=lw, c=(0,0,0)) # Actually do the plot
    absimprove = mismatch[0]-mismatch[-1]
    relimprove = 100*(mismatch[0]-mismatch[-1])/mismatch[0]
    
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
    ax.set_title('Absolute change: %f  Relative change: %2f%%' % (absimprove, relimprove))
    ax.set_ylim((0,currentylims[1]))
    ax.set_xlim((0, len(mismatch)))
    
    return fig








##################################################################
## Allocation plots
##################################################################

def plot2allocs(multires=None, compare=True):
    ''' Plot 2 allocations on bar charts - intended for optimisations '''
    
    # Preliminaries: extract needed data
    try: progset = multires.progset[0] # For multires, progset is an odict, but all entries should be the same, so it shouldn't matter which one you use
    except: raise OptimaException('Failed to extract program set; "multires" type = "%s", but "multires" should be a multiresults set' % type(multires))
    proglabels = progset.programs.keys()
    nprogs = len(proglabels)
    labels = multires.keys
    progdata = [multires.budget['orig'], multires.budget['optim']]
    
    fig = figure(figsize=(10,6))
    fig.subplots_adjust(left=0.10) # Less space on left
    fig.subplots_adjust(right=0.98) # Less space on right
    fig.subplots_adjust(bottom=0.30) # Less space on bottom
    fig.subplots_adjust(wspace=0.30) # More space between
    fig.subplots_adjust(hspace=0.40) # More space between
    
    colors = gridcolormap(nprogs)
    
    ax = []
    xbardata = arange(nprogs)+0.5
    ymax = 0
    for plt in range(len(progdata)):
        ax.append(subplot(len(progdata),1,plt+1))
        ax[-1].hold(True)
        for p in range(nprogs):
            ax[-1].bar([xbardata[p]], [progdata[plt][p]], color=colors[p], linewidth=0)
            if plt==1 and compare:
                ax[-1].bar([xbardata[p]], [progdata[0][p]], color='None', linewidth=1)
        ax[-1].set_xticks(arange(nprogs)+1)
        if plt==0: ax[-1].set_xticklabels('')
        if plt==1: ax[-1].set_xticklabels(proglabels,rotation=90)
        ax[-1].set_xlim(0,nprogs+1)
        
        ax[-1].set_ylabel('Spending (US$)')
        ax[-1].set_title(labels[plt])
        ymax = maximum(ymax, ax[-1].get_ylim()[1])
    for plt in range(len(progdata)):
        if compare: ax[plt].set_ylim((0,ymax))
    
    return fig
    
    
def plotmultiallocs(multires=None, compare=True):
    ''' Plot multiple allocations on bar charts - intended for scenarios '''
    
    ### NOT READY YET
