"""
CALIBRATION

Functions to perform calibration.
"""

from optima import OptimaException, Parameterset, Par, dcp, perturb, runmodel, asd, printv, findinds, isnumber, odict
from numpy import median, zeros, array, mean



def sensitivity(project=None, orig=None, ncopies=5, what='force', span=0.5, ind=0, verbose=2):
    ''' 
    Function to perturb the parameters to get "uncertainties".
    
    Inputs:
        orig = parset to perturb
        ncopies = number of perturbed copies of pars to produce
        what = which parameters to perturb
        span = how much to perturb
        ind = index of pars to start from
    Outputs:
        parset = perturbed parameter set with ncopies sets of pars
    
    Version: 2016jan19 by cliffk
    '''
    
    printv('Performing sensitivity analysis...', 1, verbose)
    
    # Validate input
    if type(orig)!=Parameterset:
        raise OptimaException('First argument to sensitivity() must be a parameter set')
    if span>1 or span<0:
        print('WARNING: span argument must be a scalar in the interval [0,1], resetting...')
        span = median([0,1,span])
    
    # Copy things
    parset = dcp(orig) # Copy the original parameter set
    parset.project = project # Keep original project information
    origpars = dcp(parset.pars[ind])
    parset.pars = []
    for n in range(ncopies):
        parset.pars.append(dcp(origpars))
    popkeys = origpars['popkeys']
    
    if what=='force':
        for n in range(ncopies):
            for key in popkeys:
                parset.pars[n]['force'].y[key] = perturb(n=1, span=span)[0] # perturb() returns array, so need to index -- WARNING, could make more efficient and remove loop
    else:
        raise OptimaException('Sorry, only "force" is implemented currently')
    
    return parset
























def autofit(project=None, name=None, fitwhat=None, fitto=None, maxtime=None, maxiters=1000, inds=0, verbose=2, doplot=False):
    ''' 
    Function to automatically fit parameters.
    
    Version: 2016feb06 by cliffk
    '''
    if doplot: # Store global information for debugging
        global autofitfig, autofitresults
        autofitfig, autofitresults = [None]*2
    
    printv('Performing automatic fitting...', 1, verbose)
    
    # Validate input
    if project is None: raise OptimaException('autofit() requires a project in order to run')
    if type(name)!=str: raise OptimaException('%s must be the name or index of a paramete set' % name)
    
    # Initialization
    parset = project.parsets[name] # Shorten the original parameter set
    parset.project = project # Try to link the parset back to the project -- WARNING, seems fragile
    origparlist = dcp(parset.pars)
    lenparlist = len(origparlist)
    if fitwhat is None: fitwhat = ['force'] # By default, automatically fit force-of-infection only
    if type(fitwhat)==str: fitwhat = [fitwhat]
    if type(fitto)==str: fitto = [fitto]
    if isnumber(inds): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise OptimaException('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    parset.pars = [] # Clear out in preparation for fitting
    parset.improvement = [] # For storing the improvement for each fit
    pars = origparlist[0] # Just get a copy of the pars for parsing
    
    
    
    ## WARNING -- the following two functions must be updated together! Annoying, I know...
    
    
    # Populate lists of what to fit
    def makeparlist(pars, fitwhat):
        ''' 
        This uses the "auto" attribute to decide whether or not to automatically calibrate it, and
        if so, it uses the "fittable" attribute to decide what to calibrate (e.g., just the metaparameter
        or all the values.
        
        "fitwhat" options (see parameters.py, especially listparattributes()): 
        ['init','popsize','test','treat','force','other','const']
        '''
        parlist = []
        for parname in pars: # Just use first one, since all the same
            par = pars[parname]
            if issubclass(type(par), Par): # Check if it's a parameter
                if par.auto in fitwhat: # It's in the list of things to fit
                    if par.fittable=='meta':
                        parlist.append({'name':par.short, 'type':par.fittable, 'limits':par.limits, 'ind':None})
                    elif par.fittable=='pop':
                        for i in range(len(par.y)): parlist.append({'name':par.short, 'type':par.fittable, 'limits':par.limits, 'ind':i})
                    elif par.fittable=='exp':
                        for i in range(len(par.p)): parlist.append({'name':par.short, 'type':par.fittable, 'limits':par.limits, 'ind':i})
                    elif par.fittable=='const':
                        parlist.append({'name':par.short, 'type':'const', 'limits':par.limits, 'ind':None})
                    else:
                        raise OptimaException('Parameter "fittable" type "%s" not understood' % par.fittable)
            else: pass # It's like popkeys or something -- don't worry, be happy
        return parlist
    
    
    def convert(pars, parlist, parvec=None):
        ''' 
        If parvec is not supplied:
            Take a parameter set (e.g. P.parsets[0].pars[0]), a list of "types" 
            (e.g. 'force'), and a list of keys (e.g. 'hivtest'), and return a
            vector of values, e.g. "dehydrate" them.
        
        If parvec is supplied:
            Take a vector of parameter values and "hydrate" them into a pars object
            using a list of "types" (e.g. 'force'), and a list of keys (e.g. 'hivtest').
        
        Relies on the structure of makeparlist() above...
        '''
        
        # Handle inputs
        nfitpars = len(parlist)
        if parvec is None: 
            tv = True # to vector
            parvec = zeros(nfitpars)
        else: tv = False
        
        # Do the loop
        for i in range(nfitpars):
            thistype = parlist[i]['type'] # Should match up with par.fittable
            thisname = parlist[i]['name']
            thisind = parlist[i]['ind']
            if thistype in ['force', 'pop']: 
                if tv: parvec[i] = pars[thisname].y[thisind]
                else:  pars[thisname].y[thisind] = parvec[i]
            elif thistype=='exp': 
                if tv: parvec[i] = pars[thisname].p[thisind][0] # Don't change growth rates
                else:  pars[thisname].p[thisind][0] = parvec[i]
            elif thistype=='meta': 
                if tv: parvec[i] = pars[thisname].m
                else:  pars[thisname].m = parvec[i]
            elif thistype=='const': 
                if tv: parvec[i] = pars[thisname].y
                else:  pars[thisname].y = parvec[i]
            else: raise OptimaException('Parameter type "%s" not understood' % thistype)
        
        # Decide which to return
        if tv: return parvec
        else:  return pars
    


    def errorcalc(parvec=None, pars=None, parlist=None, project=None, fitto=None, bestindex=0, doplot=False, verbose=2):
        ''' 
        Calculate the mismatch between the model and the data -- may or may not be
        related to the likelihood. Either way, it's very uncertain what this function
        does.
        
        WARNING, 'bestindex' is kludgy -- discard upper and lower limits for the data
        '''
        
        if doplot: # Store global information for debugging -- WARNING, is this the best way of doing this?
            global autofitfig, autofitresults
            from pylab import figure, ceil, sqrt, subplot, scatter, xlabel, ylabel, plot, show, pause, ylim, bar, arange
            if autofitfig is None: 
                autofitfig = figure(figsize=(16,12), facecolor=(1,1,1))
                autofitfig.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.95, wspace=0.3, hspace=0.4)
            if autofitresults is None: autofitresults = {'count':[], 'mismatch':[], 'allmismatches':[]}
        
        # Validate input -- check everything in one go
        if any([arg is None for arg in [parvec, pars, parlist, project]]): 
            raise OptimaException('errorcalc() requires parvec, pars, parlist, and project inputs')
        
        def extractdata(xdata, ydata):
            ''' Return the x and y data values for non-nan y data '''
            from numpy import isnan, array
            nonnanx = array(xdata)[~isnan(array(ydata))]
            nonnany = array(ydata)[~isnan(array(ydata))]
            return nonnanx, nonnany

        printv(parvec, 4, verbose)
        
        eps = project.settings.eps # 'eps' is also kludgy -- specify absolute error -- can't be larger than ~0.001 because then general population prevalence might get screwed
        pars = convert(pars, parlist, parvec)
        results = runmodel(pars=pars, start=project.data['years'][0], end=project.data['years'][-1], project=project, verbose=0)
        
        ## Loop over all results
        allmismatches = []
        count = 0
        mismatch = 0
        if doplot: debugdata = odict()
        if fitto is None: fitto = results.main # If not specified, use everything
        for key in fitto: # The results! e.g. key='prev'
            try: this = results.main[key]
            except: 
                errormsg = 'autofit(): Key to fit "%s" not found; valid keys are:\n%s' % (key, results.main.keys())
                raise OptimaException(errormsg)
            for attr in ['tot', 'pops']: # Loop over either total or by population denominators
                tmpdata = getattr(this, 'data'+attr) # Get this data, e.g. results.main['prev'].datatot
                if tmpdata is not None: # If it actually exists, proceed
                    tmpmodel = getattr(this, attr) # Get this result, e.g. results.main['prev'].tot
                    datarows = tmpdata[bestindex] # Pull out data without uncertainty
                    modelrows = tmpmodel[bestindex] # Pull out just the best result (likely only 1 index) -- WARNING, should be another index!
                    nrows = len(datarows)
                    if doplot: debugdata[key] = odict()
                    for row in range(nrows): # Loop over each available row
                        datarow = datarows[row]
                        if nrows==1: modelrow = modelrows # WARNING, kludgy, should have the same shape!
                        else: modelrow = modelrows[row]
                        datax, datay = extractdata(results.datayears, datarow) # Pull out the not-NaN values
                        if doplot and len(datax): 
                            rowname = 'total' if nrows==1 else pars['popkeys'][row]
                            debugdata[key][rowname] = odict([('name',key), ('row',row), ('x',[]), ('modely',[]), ('datay',[])])
                        for i,year in enumerate(datax): # Loop over each data point available
                            count += 1
                            modelx = findinds(results.tvec, year) # Find the index of the corresponding time point
                            modely = modelrow[modelx] # Finally, extract the model result!
                            thismismatch = abs(modely - datay[i]) / mean(datay+eps)
                            allmismatches.append(thismismatch)
                            mismatch += thismismatch
                            
                            if doplot:
                                printv('#%i. Key="%s" pop="%s" year=%f datay=%f modely=%f thismis=%f totmis=%f' % (count, key, rowname, year, datay[i], modely, thismismatch, mismatch), 4, verbose)
                                debugdata[key][rowname]['x'].append(year)
                                debugdata[key][rowname]['datay'].append(datay[i])
                                debugdata[key][rowname]['modely'].append(modely)
                            
        
        if doplot:
            autofitresults['count'].append(len(autofitresults['count'])) #  Append new count
            autofitresults['mismatch'].append(mismatch) #  Append mismatch
            autofitresults['allmismatches'].append(array(allmismatches).flatten()) #  Append mismatch
            
            autofitfig.clear()
            nplots = sum([len(debugdata[key]) for key in debugdata.keys()])+2 # 1 is the mismatch
            rowscols = ceil(sqrt(nplots))
            rows = rowscols
            cols = rows-1 if rows*(rows-1)>=nplots else rows
            
            subplot(rows,cols,1)
            scatter(autofitresults['count'], autofitresults['mismatch'])
            xlabel('Count')
            ylabel('Mismatch')
            ylim((0,ylim()[1]))
            
            subplot(rows,cols,2)
            allmis = autofitresults['allmismatches'][-1] # Shorten
            bar(arange(len(allmis)), allmis)
            xlabel('Data point')
            ylabel('Mismatch')
            ylim((0,ylim()[1]))
            
            count = 0
            for key1,tmp1 in debugdata.items():
                for key2,tmp2 in tmp1.items():
                    count += 1
                    print('    key=%s row=%s count=%i' % (key1, key2, count))
                    subplot(rows, cols, count+2)
                    scatter(tmp2['x'], tmp2['datay'])
                    plot(tmp2['x'], tmp2['modely'])
                    xlabel('Year')
                    ylabel(key1+' - '+key2)
                    ylim((0,ylim()[1]))
            
            show()
            pause(0.001)
            
            
            
            
            
        
        printv('Current mismatch: %s' % array(mismatch), 4, verbose=verbose)
        return mismatch






    
    # Create the list of parameters to be fitted and set the limits
    parlist = makeparlist(pars, fitwhat)
    parlower  = array([item['limits'][0] for item in parlist])
    parhigher = array(project.settings.convertlimits([item['limits'][1] for item in parlist])) # Replace text labels with numeric values
    
    # Loop over each pars
    for ind in inds:
        
        # Get this set of parameters
        try: pars = origparlist[ind]
        except: raise OptimaException('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Perform fit
        parvec = convert(pars, parlist)
        args = {'pars':pars, 'parlist':parlist, 'project':project, 'fitto':fitto, 'doplot':doplot, 'verbose':verbose}
        parvecnew, fval, exitflag, output = asd(errorcalc, parvec, args=args, xmin=parlower, xmax=parhigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
        
        # Save
        pars = convert(pars, parlist, parvecnew)        
        parset.pars.append(pars)
        parset.improvement.append(output.fval) # Store improvement history
    
    return parset