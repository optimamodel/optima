from optima import Resultset, Multiresultset, odict, gridcolormap
from numpy import array, ndim, maximum, arange
from pylab import isinteractive, ioff, ion, figure, plot, close, ylim, fill_between, scatter, gca, subplot




def plotepi(results, which=None, uncertainty=True, verbose=2, figsize=(14,10), alpha=0.2, lw=2, dotsize=50,
            titlesize=14, labelsize=12, ticksize=10, legendsize=10):
        '''
        Render the plots requested and store them in a list. Argument "which" should be a list of form e.g.
        ['prev-tot', 'inci-pops']

        This function returns an odict of figures, which can then be saved as MPLD3, etc.

        Version: 2016jan18
        '''
        
        # Figure out what kind of result it is
        if type(results)==Resultset: kind='single'
        elif type(results)==Multiresultset: 
            kind='multi'
            best = list() # Initialize as empty list for storing results sets
            labels = results.keys # Figure out the labels for the different lines
            nlinesperplot = len(labels) # How ever many things are in results
        else: 
            errormsg = 'Results input to plotepi() must be either Resultset or Multiresultset, not "%s", you drongo' % type(results)
            raise Exception(errormsg)

        # Initialize
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures
        if which is None: which = [datatype+'-'+poptype for datatype in results.main.keys() for poptype in ['pops', 'sep', 'tot']] # Just plot everything if not specified
        elif type(which) in [str, tuple]: which = [which] # If single value, put inside list

        # Loop over each plot
        epiplots = odict()
        for plotkey in which:

            ################################################################################################################
            ## Parse user input
            ################################################################################################################
            try:
                if type(plotkey)==str: datatype, poptype = plotkey.split('-')
                elif type(plotkey) in [list, tuple]: datatype, poptype = plotkey[0], plotkey[1]
                else: 
                    errormsg = 'Could not understand "%s": must a string, e.g. "numplhiv-tot", or a list/tuple, e.g. ["numpliv","tot"]' % str(plotkey)
                    raise Exception(errormsg)
                if datatype not in results.main.keys():
                    errormsg = 'Could not understand plot "%s"; ensure keys are one of:\n' % datatype
                    errormsg += '%s' % results.main.keys()
                    raise Exception(errormsg)
                if poptype not in ['pops', 'sep', 'tot']:
                    errormsg = 'Type "%s" should be either "pops", "sep", or "tot"'
                    raise Exception(errormsg)
            except:
                errormsg = 'Could not parse plot key "%s"; please ensure format is e.g. "numplhiv-tot"' % plotkey
                raise Exception(errormsg)
            
            try:
                factor = 1.0 if results.main[datatype].isnumber else 100.0 # Swap between number and percent
            except:
                errormsg = 'Unable to find key "%s" in results' % datatype
                raise Exception(errormsg)
            
            
            ################################################################################################################
            ## Process the plot data
            ################################################################################################################
            datapoptype = 'pops' if poptype=='sep' else poptype # Replace 'sep' with 'pops' for extracting data
            if kind=='single': # Single results thing: plot with uncertainties and data
                best = getattr(results.main[datatype], datapoptype)[0] # poptype = either 'tot' or 'pops'
                try: # If results were calculated with quantiles, these should exist
                    lower = getattr(results.main[datatype], datapoptype)[1]
                    upper = getattr(results.main[datatype], datapoptype)[2]
                except: # No? Just use the best data
                    lower = best
                    upper = best
            elif kind=='multi':
                for l in range(nlinesperplot): best.append(getattr(results.main[datatype], datapoptype)[l])
                lower = None
                upper = None
            try: # Try loading actual data -- very likely to not exist
                tmp = getattr(results.main[datatype], 'data'+datapoptype)
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
            seppops = poptype=='sep' # Whether or not populations are separated
            if seppops: 
                pkeys = [str(plotkey)+'-'+key for key in results.popkeys] # Create list of plot keys (pkeys), one for each population
            else: pkeys = [plotkey] # If it's anything else, just go with the original, but turn into a list so can iterate
            
            for i,pk in enumerate(pkeys): # Either loop over individual population prevalence plots, or just plot a single plot
                
                epiplots[pk] = figure(figsize=figsize) # If it's anything other than HIV prevalence by population, create a single plot
    
                if kind=='single': nlinesperplot = len(best) # Either 1 or npops
                colors = gridcolormap(nlines)
                
                # Plot uncertainty
                if uncertainty: # It's not by population, except HIV prevalence, and uncertainty has been requested: plot bands
                    fill_between(results.tvec, factor*lower[i], factor*upper[i], facecolor=colors[i], alpha=alpha, lw=0)
    
                # Plot model estimates with uncertainty
                for l in range(nlines):
                    try: plot(results.tvec, factor*best[l], lw=lw, c=colors[l]) # Actually do the plot
                    except: import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                    
                # Plot data points with uncertainty
                for l in range(nlines):
                    if databest is not None:
                        scatter(results.datayears, factor*databest[l], c=colors[l], s=dotsize, lw=0)
                        for y in range(len(results.datayears)):
                            plot(results.datayears[y]*array([1,1]), factor*array([datalow[l][y], datahigh[l][y]]), c=colors[l], lw=1)
                
                
                ################################################################################################################
                # Configure axes -- from http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
                ################################################################################################################
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
                legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':''}
                ax.set_xlabel('Year')
                # ax.legend(loc='upper left', fancybox=True, title='')
                ax.set_title(results.main[datatype].name)
                ax.set_ylim((0,currentylims[1]))
                ax.set_xlim((results.tvec[0], results.tvec[-1]))
                if kind=='single':
                    if poptype=='pops': ax.legend(results.popkeys, **legendsettings)
                    if poptype=='tot':  ax.legend(['Total'], **legendsettings)
                elif kind=='multi':
                    ax.legend(labels, **legendsettings) # WARNING, cannot plot multiple populations here!
    
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
    else: raise Exception('To plot the mismatch, you must give either the mismatch or an object containing the mismatch as the first argument; try again')
    
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

def plotallocs(multires=None, compare=True):
    ''' Instead of stupid pie charts, make some nice bar charts '''
    
    # Preliminaries: extract needed data
    try: progset = multires.progset[0] # For multires, progset is an odict, but all entries should be the same, so it shouldn't matter which one you use
    except: raise Exception('Failed to extract program set; "multires" type = "%s", but "multires" should be a multiresults set' % type(multires))
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