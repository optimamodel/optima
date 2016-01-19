from optima import odict, gridcolormap
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

        # Initialize
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures
        if which is None: which = [datatype+'-'+poptype for datatype in results.main.keys() for poptype in ['pops', 'tot']] # Just plot everything if not specified
        elif type(which)==str: which = [which] # Convert to list

        # Loop over each plot
        epiplots = odict()
        for pl in which:

            # Parse user input
            try:
                datatype, poptype = pl.split('-')
                if datatype not in results.main.keys():
                    errormsg = 'Could not understand plot "%s"; ensure keys are one of:\n' % datatype
                    errormsg += '%s' % results.main.keys()
                    raise Exception(errormsg)
                if poptype not in ['pops', 'tot']:
                    errormsg = 'Type "%s" should be either "pops" or "tot"'
                    raise Exception(errormsg)
            except:
                errormsg = 'Could not parse plot "%s"\n' % pl
                errormsg += 'Please ensure format is e.g. "numplhiv-tot"'
                raise Exception(errormsg)

            # Process the plot data
            try: # This should only fail if the key is wrong
                best = getattr(results.main[datatype], poptype)[0] # poptype = either 'tot' or 'pops'
                factor = 1.0 if results.main[datatype].isnumber else 100 # Swap between number and percent
            except:
                errormsg = 'Unable to find key "%s" in results' % datatype
                raise Exception(errormsg)
            try: # If results were calculated with quantiles, these should exist
                lower = getattr(results.main[datatype], poptype)[1]
                upper = getattr(results.main[datatype], poptype)[2]
            except: # No? Just use the best data
                lower = best
                upper = best
            try: # Try loading actual data -- very likely to not exist
                tmp = getattr(results.main[datatype], 'data'+poptype)
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

            # Set up figure and do plot
            epiplots[pl] = figure(figsize=figsize)

            nlines = len(best) # Either 1 or npops
            colors = gridcolormap(nlines)

            # Plot model estimates with uncertainty
            for l in range(nlines):
                if uncertainty:
                    fill_between(results.tvec, factor*lower[l], factor*upper[l], facecolor=colors[l], alpha=alpha, lw=0)
                plot(results.tvec, factor*best[l], lw=lw, c=colors[l]) # Actually do the plot

            # Plot data points with uncertainty
            for l in range(nlines):
                if databest is not None:
                    scatter(results.datayears, factor*databest[l], c=colors[l], s=dotsize, lw=0)
                    for y in range(len(results.datayears)):
                        plot(results.datayears[y]*array([1,1]), factor*array([datalow[l][y], datahigh[l][y]]), c=colors[l], lw=1)

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
            legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':''}
            ax.set_xlabel('Year')
            # ax.legend(loc='upper left', fancybox=True, title='')
            ax.set_title(results.main[datatype].name)
            ax.set_ylim((0,currentylims[1]))
            ax.set_xlim((results.tvec[0], results.tvec[-1]))
            if poptype=='pops': ax.legend(results.popkeys, **legendsettings)
            if poptype=='tot':  ax.legend(['Total'], **legendsettings)


            close(epiplots[pl])



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
    
    Version: 2016jan18 by cliffk    
    '''

    if hasattr(results, 'mismatch'): mismatch = results.mismatch # Get mismatch attribute of object if it exists
    elif ndim(results)==1: mismatch = results # Promising, has the right dimensionality at least
    else: raise Exception('To plot the mismatch, you must give either the mismatch or an object containing the mismatch as the first argument, mister')
    
    # Set up figure and do plot
    fig = figure(figsize=figsize, facecolor=(1,1,1))
    
    # Plot model estimates with uncertainty
    plot(mismatch, lw=lw, c=(0,0,0)) # Actually do the plot
    
    
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
    ax.set_title('Outcome/mismatch')
    ax.set_ylim((0,currentylims[1]))
    ax.set_xlim((0, len(mismatch)))
    
    return fig








##################################################################
## Allocation plots
##################################################################

def plotallocs(multires=None, compare=True):
    ''' Instead of stupid pie charts, make some nice bar charts '''
    
    # Preliminaries: extract needed data
    progset = multires.progset[0] # Should be the same so shouldn't matter which one you get
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