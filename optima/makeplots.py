from optima import odict, gridcolormap
from pylab import isinteractive, ioff, ion, figure, plot, xlabel, title, close, xlim, ylim, legend, ndim, fill_between, scatter

def epiplot(results, whichplots=None, uncertainty=True, verbose=2, figsize=(8,6), alpha=0.5, lw=2, dotsize=50):
        ''' Render the plots requested and store them in a list '''
        
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures
        if whichplots is None: whichplots = [datatype+'-'+poptype for datatype in results.main.keys() for poptype in ['pops', 'tot']] # Just plot everything if not specified
        elif type(whichplots)==str: whichplots = [whichplots] # Convert to list
        epiplots = odict()
        for pl in whichplots:
            
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
                data = getattr(results.main[datatype], 'data'+poptype)[0] # TEMP
            except:# Don't worry if no data
                data = None
            
            if ndim(best)==1: # Wrap so right number of dimensions
                best = [best]
                lower = [lower]
                upper = [upper]
                data = [data]
            
            # Set up figure and do plot
            epiplots[pl] = figure(figsize=figsize)
            nlines = len(best)
            colors = gridcolormap(nlines)
            for l in range(nlines):
                if uncertainty:
                    fill_between(results.tvec, factor*lower[l], factor*upper[l], facecolor=colors[l], alpha=alpha)
                plot(results.tvec, factor*best[l], lw=lw, c=colors[l]) # Actually do the plot
                try: 
                    if data is not None: 
                        scatter(results.datayears, factor*data[l], c=colors[l], s=dotsize, lw=0)
                except: print('FAILED') # import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            
            xlabel('Year')
            title(results.main[datatype].name)
            currentylims = ylim()
            ylim((0,currentylims[1]))
            xlim((results.tvec[0], results.tvec[-1]))
            legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.05, 1), 'fontsize':'small'}
            if poptype=='pops': legend(results.popkeys, **legendsettings)
            if poptype=='tot':  legend(['Total'], **legendsettings)
            close(epiplots[pl])
        
        if wasinteractive: ion() # Turn interactivity back on
        return epiplots