"""
CALIBRATION

Functions to perform calibration.
"""

from optima import Parameterset, Par, dcp, perturb, runmodel, asd, printv, findinds
from numpy import median, zeros, array, mean



def sensitivity(orig=None, ncopies=5, what='force', span=0.5, ind=0):
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
    
    Version: 2015dec29 by cliffk
    '''
    
    # Validate input
    if span>1 or span<0:
        print('WARNING: span argument must be a scalar in the interval [0,1], resetting...')
        span = median([0,1,span])
    if type(orig)!=Parameterset:
        raise Exception('First argument to sensitivity() must be a parameter set')
    
    # Copy things
    parset = dcp(orig) # Copy the original parameter set
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
        raise Exception('Sorry, only "force" is implemented currently')
    
    return parset
























def autofit(project=None, name=None, what=None, maxtime=None, niters=100, inds=0, verbose=2):
    ''' 
    Function to automatically fit parameters.
    
    Version: 2016jan05 by cliffk
    '''
    
    # Initialization
    parset = project.parsets[name] # Copy the original parameter set
    origparlist = dcp(parset.pars)
    lenparlist = len(origparlist)
    if what is None: what = ['force'] # By default, automatically fit force-of-infection only
    if type(inds)==int or type(inds)==float: inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise Exception('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    parset.pars = [] # Clear out in preparation for fitting
    pars = origparlist[0] # Just get a copy of the pars for parsing
    
    
    
    ## WARNING -- the following two functions must be updated together! Annoying, I know...
    
    
    # Populate lists of what to fit
    def makeparlist(pars, what):
        ''' 
        This uses the "auto" attribute to decide whether or not to automatically calibrate it, and
        if so, it uses the "fittable" attribute to decide what to calibrate (e.g., just the metaparameter
        or all the values.
        
        "what" options (see parameters.py, especially listparattributes()): 
        ['init','popsize','test','treat','force','other','const']
        '''
        parlist = []
        for parname in pars: # Just use first one, since all the same
            par = pars[parname]
            if issubclass(type(par), Par): # Check if it's a parameter
                if par.auto in what: # It's in the list of things to fit
                    if par.fittable=='meta':
                        parlist.append({'name':par.short, 'type':par.fittable, 'limits':par.limits, 'ind':None})
                    elif par.fittable=='pop':
                        for i in range(len(par.y)): parlist.append({'name':par.short, 'type':par.fittable, 'limits':par.limits, 'ind':i})
                    elif par.fittable=='exp':
                        for i in range(len(par.p)): parlist.append({'name':par.short, 'type':par.fittable, 'limits':par.limits, 'ind':i})
                    else:
                        raise Exception('Parameter "fittable" type "%s" not understood' % par.fittable)
            elif parname=='const' and 'const' in what: # Or check if it's a constant
                for constname in pars['const']:
                    for i in range(len(pars['const'])): parlist.append({'name':par.short, 'type':'const', 'ind':constname})
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
            elif thistype=='popsize': 
                if tv: parvec[i] = pars[thisname].p[thisind]
                else:  pars[thisname].p[thisind] = parvec[i]
            elif thistype=='meta': 
                if tv: parvec[i] = pars[thisname].m
                else:  pars[thisname].m = parvec[i]
            elif thistype=='const': 
                if tv: parvec[i] = pars['const'][thisind].y
                else:  pars['const'][thisind].y = parvec[i]
            else: raise Exception('Parameter type "%s" not understood' % thistype)
        
        # Decide which to return
        if tv: return parvec
        else:  return pars
    


    def errorcalc(parvec, options):
        ''' 
        Calculate the mismatch between the model and the data -- may or may not be
        related to the likelihood. Either way, it's very uncertain what this function
        does.
        '''
        
        bestindex = 0 # WARNING, KLUDGY -- discard upper and lower limits for the data
        eps = 0.001 # Absolute error -- can't be larger than ~0.001 because then general population prevalence might get screwed
        
        def extractdata(xdata, ydata):
            ''' Return the x and y data values for non-nan y data '''
            from numpy import isnan, array
            nonnanx = array(xdata)[~isnan(array(ydata))]
            nonnany = array(ydata)[~isnan(array(ydata))]
            return nonnanx, nonnany

        printv(parvec, 4, verbose)
        
        pars = options['pars']
        parlist = options['parlist']
        pars = convert(pars, parlist, parvec)
        results = runmodel(pars=pars, start=project.data['years'][0], end=project.data['years'][-1], verbose=verbose)
        
        ## Loop over all results
        allmismatches = []
        mismatch = 0
        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        for key in results.main: # The results! e.g. key='prev'
            this = results.main[key] 
            for attr in ['tot', 'pops']: # Loop over either total or by population denominators
                tmpdata = getattr(this, 'data'+attr) # Get this data, e.g. results.main['prev'].datatot
                if tmpdata is not None: # If it actually exists, proceed
                    tmpmodel = getattr(this, attr) # Get this result, e.g. results.main['prev'].tot
                    datarows = tmpdata[bestindex] # Pull out data without uncertainty
                    modelrows = tmpmodel[bestindex] # Pull out just the best result (likely only 1 index)
                    for row in range(len(datarows)): # Loop over each available row
                        datax, datay = extractdata(results.datayears, datarows) # Pull out the not-NaN values
                        for col in datax: # Loop over each data point available
                            modelx = findinds(results.tvec, col) # Find the index of the corresponding time point
                            modely = modelrows[modelx] # Finally, extract the model result!
                            thismismatch = abs(modely - datay) / mean(datay+eps)
                            allmismatches.append(thismismatch)
                            mismatch += thismismatch
        
        printv('Current mismatch: %s' % array(thismismatch).flatten(), 5, verbose=verbose)
        return mismatch






    
    # Create the list of parameters to be fitted and set the limits
    parlist = makeparlist(pars, what)
    parlower  = array([item['limits'][0] for item in parlist])
    parhigher = array(project.settings.setmaxes([item['limits'][1] for item in parlist])) # Replace text labels with numeric values
    
    # Loop over each pars
    for ind in inds:
        
        # Get this set of parameters
        try: pars = origparlist[ind]
        except: raise Exception('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Perform fit
        parvec = convert(pars, parlist)
        options = {'pars':pars, 'parlist':parlist}
        parvecnew, fval, exitflag, output = asd(errorcalc, parvec, options=options, xmin=parlower, xmax=parhigher, timelimit=maxtime, MaxIter=niters, verbose=verbose)
        
        # Save
        pars = convert(pars, parlist, parvecnew)        
        parset.pars.append(pars)
    
    return parset