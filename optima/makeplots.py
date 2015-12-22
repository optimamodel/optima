from optima import odict, gridcolormap
from pylab import isinteractive, ioff, ion, figure, plot, xlabel, ylabel, close, xlim, ylim, legend, ndim

def epiplot(results, whichplots=None, uncertainty=False, verbose=2, figsize=(8,6)):
        ''' Render the plots requested and store them in a list '''
        
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures
        if type(whichplots)==str: whichplots = [whichplots] # Convert to list
        epiplots = odict()
        for pl in whichplots:
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
            if not uncertainty: thisdata = getattr(results.main[datatype], poptype)[0] # Either 'tot' or 'pops'
            else: raise Exception('WARNING, uncertainty in plots not implemented yet')
            
            epiplots[pl] = figure(figsize=figsize)
            if ndim(thisdata)==1: thisdata = [thisdata] # Wrap so right number of dimensions
            nlines = len(thisdata)
            colors = gridcolormap(nlines)
            for l in range(nlines):
                plot(results.tvec, thisdata[l], lw=2, c=colors[l]) # Actually do the plot
            xlabel('Year')
            ylabel(results.main[datatype].name)
            currentylims = ylim()
            ylim((0,currentylims[1]))
            xlim((results.tvec[0], results.tvec[-1]))
            if poptype=='pops': legend(results.parset.popkeys, loc=(1,0))
            if poptype=='tot':  legend(['Total'], loc=(1,0))
            close(epiplots[pl])
        
        if wasinteractive: ion() # Turn interactivity back on
        return epiplots