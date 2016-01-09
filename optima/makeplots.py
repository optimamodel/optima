from optima import odict, gridcolormap
from pylab import array, isinteractive, ioff, ion, figure, plot, close, ylim, ndim, fill_between, scatter, gca

def epiplot(results, which=None, uncertainty=True, verbose=2, figsize=(14,10), alpha=0.2, lw=2, dotsize=50,
            titlesize=14, labelsize=12, ticksize=10, legendsize=10):
        '''
        Render the plots requested and store them in a list. Argument "which" should be a list of form e.g.
        ['prev-tot', 'inci-pops']

        This function returns an odict of figures, which can then be saved as MPLD3, etc.

        Version: 2015dec29
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
            legendsettings = {'loc':'upper right', 'bbox_to_anchor':(1.05, 1), 'fontsize':legendsize, 'title':''}
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
