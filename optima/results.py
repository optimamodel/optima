"""
This module defines the classes for stores the results of a single simulation run.

Version: 2017oct23
"""

from optima import OptimaException, Link, Settings, odict, pchip, plotpchip, sigfig # Classes/functions
from optima import uuid, today, makefilepath, getdate, printv, dcp, objrepr, defaultrepr, sanitizefilename, sanitize # Printing/file utilities
from optima import quantile, findinds, findnearest, promotetolist, promotetoarray, checktype # Numeric utilities
from numpy import array, nan, zeros, arange, shape, maximum, log
from numbers import Number
from xlsxwriter import Workbook





class Result(object):
    ''' Class to hold overall and by-population results '''
    def __init__(self, name=None, ispercentage=False, pops=None, tot=None, datapops=None, datatot=None, estimate=False, defaultplot=None):
        self.name = name # Name of this parameter
        self.ispercentage = ispercentage # Whether or not the result is a percentage
        self.pops = pops # The model result by population, if available
        self.tot = tot # The model result total, if available
        self.datapops = datapops # The input data by population, if available
        self.datatot = datatot # The input data total, if available
        self.estimate = estimate # Whether or not the "data" is actually a model-based output
        self.defaultplot = defaultplot if defaultplot is not None else 'stacked'
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = defaultrepr(self)
        return output






class Resultset(object):
    ''' Structure to hold results '''
    def __init__(self, raw=None, name=None, pars=None, simpars=None, project=None, settings=None, data=None, parsetname=None, progsetname=None, budget=None, coverage=None, budgetyears=None, domake=True, quantiles=None, keepraw=False, verbose=2, doround=True):
        # Basic info
        self.uid = uuid()
        self.created = today()
        self.name = name if name else 'default' # May be blank if automatically generated, but can be overwritten
        self.main = odict() # For storing main results
        self.other = odict() # For storing other results -- not available in the interface
        self.keys = [0] # Used for comparison with multiresultsets -- 0 corresponds to e.g. self.main[<key>].tot[0]
        self.parsetname = parsetname
        self.progsetname = progsetname
        
        # Turn inputs into lists if not already
        if raw is None: raise OptimaException('To generate results, you must feed in model output: none provided')
        simpars = promotetolist(simpars) # Force into being a list
        raw = promotetolist(raw) # Force into being a list
        
        # Read things in from the project if defined
        if project is not None:
            if data is None: data = project.data # Copy data if not supplied -- DO worry if data don't exist!
            if settings is None: settings = project.settings
        
        # Fundamental quantities -- populated by project.runsim()
        if keepraw: self.raw = raw # Keep raw, but only if asked
        if keepraw: self.simpars = simpars # ...likewise sim parameters
        self.popkeys = raw[0]['popkeys']
        self.datayears = data['years'] if data is not None else None # Only get data years if data available
        self.projectref = Link(project) # ...and just store the whole project
        self.projectinfo = project.getinfo() # Store key info from the project separately in case the link breaks
        if pars is not None:
            self.pars = pars # Keep pars
        else: # Try various other ways of getting pars
            if parsetname is not None and parsetname in self.projectref().parsets.keys():
                self.pars = self.projectref().parsets[parsetname].pars
            else: raise OptimaException('To generate results, you must feed in a parset or pardict: none provided')
        self.data = dcp(data) # Store data
        self.budget = budget if budget is not None else odict() # Store budget
        self.coverage = coverage if coverage is not None else odict()  # Store coverage
        self.budgetyears = budgetyears if budgetyears is not None else odict()  # Store budget
        self.settings = settings if settings is not None else Settings()
        
        # Main results -- time series, by population
        self.main['numinci']        = Result('New HIV infections')
        self.main['numdeath']       = Result('HIV-related deaths')
        self.main['numincibypop']   = Result('New HIV infections caused')
        
        self.main['numplhiv']       = Result('PLHIV')
        self.main['numaids']        = Result('People with AIDS')
        self.main['numdiag']        = Result('Diagnosed PLHIV')
        self.main['numevercare']    = Result('PLHIV initially linked to care')
        self.main['numincare']      = Result('PLHIV in care')
        self.main['numtreat']       = Result('PLHIV on treatment')
        self.main['numsuppressed']  = Result('Virally suppressed PLHIV')
        
        self.main['propdiag']       = Result('Diagnosed PLHIV (%)',                      ispercentage=True, defaultplot='total')
        self.main['propplhivtreat'] = Result('Treated PLHIV (%)',                        ispercentage=True, defaultplot='total')
        self.main['propplhivsupp']  = Result('Virally suppressed PLHIV (%)',             ispercentage=True, defaultplot='total')
        self.main['propevercare']   = Result('Diagnosed PLHIV linked to care (%)',       ispercentage=True, defaultplot='total')
        self.main['propincare']     = Result('Diagnosed PLHIV retained in care (%)',     ispercentage=True, defaultplot='total')
        self.main['proptreat']      = Result('Diagnosed PLHIV on treatment (%)',         ispercentage=True, defaultplot='total')
        self.main['propsuppressed'] = Result('Treated PLHIV with viral suppression (%)', ispercentage=True, defaultplot='total')
        
        self.main['prev']           = Result('HIV prevalence (%)',       ispercentage=True, defaultplot='population')
        self.main['force']          = Result('Incidence (per 100 p.y.)', ispercentage=True, defaultplot='population')
        self.main['numnewdiag']     = Result('New diagnoses')
        self.main['nummtct']        = Result('HIV+ births')
        self.main['numhivbirths']   = Result('Births to HIV+ women')
        self.main['numpmtct']       = Result('HIV+ women receiving PMTCT')
        self.main['popsize']        = Result('Population size')
        self.main['numdaly']        = Result('HIV-related DALYs')
        self.main['costtreat']      = Result('Annual treatment spend', defaultplot='total')

        self.other['adultprev']     = Result('Adult HIV prevalence (%)', ispercentage=True)
        self.other['childprev']     = Result('Child HIV prevalence (%)', ispercentage=True)
        self.other['numotherdeath'] = Result('Non-HIV-related deaths)')
        self.other['numbirths']     = Result('Total births)')
        
        # Add all health states
        for healthkey,healthname in zip(self.settings.healthstates, self.settings.healthstatesfull): # Health keys: ['susreg', 'progcirc', 'undx', 'dx', 'care', 'lost', 'usvl', 'svl']
            self.other['only'+healthkey]   = Result(healthname) # Pick out only people in these health states
            
        if domake: self.make(raw, verbose=verbose, quantiles=quantiles, doround=doround)
    
    
    def __repr__(self):
        ''' Print out useful information when called -- WARNING, add summary stats '''
        output = objrepr(self)
        output += '      Project name: %s\n'    % self.projectinfo['name']
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '              Name: %s\n'    % self.name
        output += '============================================================\n'
        return output
    
    
    def _checkresultset(self, R2):
        ''' A small method to make sure two resultsets are compatible, and return a copy of the first one. '''
        if type(R2)!=Resultset: raise OptimaException('Can only add results sets with other results sets')
        for attr in ['tvec','popkeys']:
            if len(getattr(self,attr))!=len(array(getattr(R2,attr))):
                raise OptimaException('Cannot add Resultsets that have dissimilar "%s"' % attr)
            else:
                if any(array(getattr(self,attr))!=array(getattr(R2,attr))):
                    raise OptimaException('Cannot add Resultsets that have dissimilar "%s"' % attr)

        
        # Keep the properties of this first one
        R1 = dcp(self) 
        R1.name += ' + ' + R2.name
        R1.uid = uuid()
        R1.created = today()
        
        return R1
    
    
    def _combine(self, R2, operation='add'):
        ''' Method to handle __add__ and __sub__ since they're almost identical '''
        
        if operation not in ['add', 'sub']:
            errormsg = 'Operation must be either "add" or "sub", not "%s"' % operation
            raise OptimaException(errormsg)
        
        R = self._checkresultset(R2)
        popsize1 = dcp(R.main['popsize'])
        popsize2 = dcp(R2.main['popsize'])
        if   operation=='add': R.name += ' + ' + R2.name
        elif operation=='sub': R.name += ' - ' + R2.name

        R.projectref = self.projectref # ...and just store the whole project
        
        # Collect all results objects, making use of the fact that they're mutable
        resultsobjs = odict() # One entry of these is e.g. R.main['prev']
        resultsobjs1 = odict()
        resultsobjs2 = odict()
        for typekey in R.main.keys():
            resultsobjs[typekey]  = R.main[typekey]
            resultsobjs1[typekey] = dcp(R.main[typekey])
            resultsobjs2[typekey] = dcp(R2.main[typekey])
        for typekey in R.other.keys():
            resultsobjs[typekey]  = R.other[typekey]
            resultsobjs1[typekey] = dcp(R.other[typekey])
            resultsobjs2[typekey] = dcp(R2.other[typekey])
        typekeys = R.main.keys()+R.other.keys()

        # Handle results
        for typekey in typekeys:
            res1 = resultsobjs1[typekey]
            res2 = resultsobjs2[typekey]
            if res1.ispercentage: # It's a percentage, average by population size
                resultsobjs[typekey].tot  = 0*res1.tot  # Reset
                resultsobjs[typekey].pops = 0*res1.pops # Reset
                for t in range(shape(res1.tot)[-1]):
                    resultsobjs[typekey].tot[:,t] = (res1.tot[:,t]*popsize1.tot[0,t] + res2.tot[:,t]*popsize2.tot[0,t]) / (popsize1.tot[0,t] + popsize2.tot[0,t])
                    for p in range(len(R.popkeys)):
                        resultsobjs[typekey].pops[:,p,t] = (res1.pops[:,p,t]*popsize1.pops[0,p,t] + res2.pops[:,p,t]*popsize2.pops[0,p,t]) / (popsize1.pops[0,p,t] + popsize2.pops[0,p,t])
            else: # It's a number, can just sum the arrays
                for attr in ['pops', 'tot']:
                    if   operation=='add': this = getattr(res1, attr) + getattr(res2, attr)
                    elif operation=='sub': this = getattr(res1, attr) - getattr(res2, attr)
                    setattr(resultsobjs[typekey], attr, this)
        return R
    
    
    def __add__(self, R2):
        ''' Define how to add two Resultsets '''
        R = self._combine(R2, operation='add')
        return R
        
        
    def __sub__(self, R2):
        ''' Define how to subtract two Resultsets '''
        R = self._combine(R2, operation='sub')
        return R
            
        
    def make(self, raw, quantiles=None, annual=True, verbose=2, doround=True, lifeexpectancy=None, discountrate=None):
        """
        Gather standard results into a form suitable for plotting with uncertainties.
        Life expectancy is measured in years, and the discount rate is in absolute
        values (e.g., 0.03).        
        """
        
        printv('Making derived results...', 3, verbose)
        
        
        # Initialize
        if quantiles      is None: quantiles      = [0.5, 0.25, 0.75] # Can't be a kwarg since mutable
        if lifeexpectancy is None: lifeexpectancy = 80 # 80 year life expectancy
        if discountrate   is None: discountrate   = 0.03 # Discounting of 3% for YLL only
        tvec = dcp(raw[0]['tvec'])
        eps = self.settings.eps
        if annual is False: # Decide what to do with the time vector
            indices = arange(len(tvec)) # Use all indices
            self.tvec = tvec
        else: 
            indices = arange(0, len(tvec), int(round(1.0/(tvec[1]-tvec[0])))) # Subsample results vector -- WARNING, should dt be taken from e.g. Settings()?
            self.tvec = tvec[indices] # Subsample time vector too
        self.dt = self.tvec[1] - self.tvec[0] # Reset results.dt as well
        nraw = len(raw) # Number of raw results sets
        
        # Define functions
        def process(rawdata, percent=False):
            ''' Process the outputs -- sort into quantiles and optionally round if it's a number '''
            processed = quantile(rawdata, quantiles=quantiles) # Calculate the quantiles
            if doround and not percent: processed = processed.round() # Optionally round
            return processed
        
        def processdata(rawdata, uncertainty=False):
            ''' Little method to turn the data into a form suitable for plotting -- basically, replace assumptions with nans '''
            if uncertainty: 
                best = dcp(rawdata[0])
                low = dcp(rawdata[1])
                high = dcp(rawdata[2])
            else:
                best = dcp(rawdata)
                low = dcp(rawdata)
                high = dcp(rawdata)
            for thisdata in [best, low, high]: # Combine in loop, but actual operate on these -- thanks, pass-by-reference!
                for p in range(len(thisdata)):
                    if len(array(thisdata[p]))!=len(self.datayears):
                        thisdata[p] = nan+zeros(len(self.datayears)) # Replace with NaN if an assumption
            processed = array([best, low, high]) # For plotting uncertainties
            return processed
        
        def processtotalpopsizedata(self, rawdata):
            ''' Little method to calculate total population size from data using nearest neighbor interpolation '''
            nyears = len(self.datayears) # Count how many years there are
            preprocessed = processdata(rawdata, uncertainty=True) # Preprocess raw population size data by population
            processed = zeros((3,1,nyears)) # Zero out # Initialize
            for blh in range(3): # Iterate over best, high, low
                validinds = [] # Store valid indices in any population
                for p in range(self.data['npops']):
                    sanitized,inds = sanitize(preprocessed[blh][p], replacenans=True, die=False, returninds=True) # Replace nans with nearest neighbors
                    processed[blh][0] += sanitized # Add this population to the running total
                    validinds += list(inds) # Append valid indices
                naninds = list(set(range(nyears)) - set(validinds))
                processed[blh][0][naninds] = nan # Convert back to nan if no data entered for any population
            return processed
        
        
        def assemble(key):
            ''' Assemble results into an array '''
            output = dcp(array([raw[i][key] for i in range(nraw)]))
            return output
        
        # Initialize arrays
        allpeople    = assemble('people')
        allinci      = assemble('inci')
        allincibypop = assemble('incibypop')
        alldeaths    = assemble('death')
        otherdeaths  = assemble('otherdeath') 
        alldiag      = assemble('diag')
        allmtct      = assemble('mtct')
        allhivbirths = assemble('hivbirths')
        allbirths    = assemble('births')
        allpmtct     = assemble('pmtct')
        allcosttreat = assemble('costtreat')
        allplhiv     = self.settings.allplhiv
        allsus       = self.settings.sus
        allaids      = self.settings.allaids
        alldx        = self.settings.alldx
        allevercare  = self.settings.allevercare
        allcare      = self.settings.allcare
        alltx        = self.settings.alltx
        svl          = self.settings.svl
        data         = self.data

        # Actually do calculations
        self.main['prev'].pops = process(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1) / (eps+allpeople[:,:,:,indices].sum(axis=1)), percent=True) # Axis 1 is health state
        self.main['prev'].tot  = process(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)) / (eps+allpeople[:,:,:,indices].sum(axis=(1,2))), percent=True) # Axis 2 is populations
        if data is not None: 
            self.main['prev'].datapops = processdata(data['hivprev'], uncertainty=True)
            self.main['prev'].datatot  = processdata(data['optprev'])
        
#        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        self.main['force'].pops = process(allinci[:,:,indices] / (eps+allpeople[:,allsus,:,:][:,:,:,indices].sum(axis=1)), percent=True) # Axis 1 is health state
        self.main['force'].tot  = process(allinci[:,:,indices].sum(axis=1) / (eps+allpeople[:,allsus,:,:][:,:,:,indices].sum(axis=(1,2))), percent=True) # Axis 2 is populations

        self.main['numinci'].pops = process(allinci[:,:,indices])
        self.main['numinci'].tot  = process(allinci[:,:,indices].sum(axis=1)) # Axis 1 is populations
        if data is not None: 
            self.main['numinci'].datatot = processdata(data['optnuminfect'])
            self.main['numinci'].estimate = True # It's not real data, just an estimate
        
        self.main['numincibypop'].pops = process(allincibypop[:,:,indices])
        self.main['numincibypop'].tot  = process(allincibypop[:,:,indices].sum(axis=1)) # Axis 1 is populations
        if data is not None: 
            self.main['numincibypop'].datatot = processdata(data['optnuminfect'])
            self.main['numincibypop'].estimate = True # It's not real data, just an estimate
        
        self.main['nummtct'].pops = process(allmtct[:,:,indices])
        self.main['nummtct'].tot  = process(allmtct[:,:,indices].sum(axis=1))

        self.main['numhivbirths'].pops = process(allhivbirths[:,:,indices])
        self.main['numhivbirths'].tot  = process(allhivbirths[:,:,indices].sum(axis=1))

        self.main['numpmtct'].pops = process(allpmtct[:,:,indices])
        self.main['numpmtct'].tot  = process(allpmtct[:,:,indices].sum(axis=1))

        self.main['numnewdiag'].pops = process(alldiag[:,:,indices])
        self.main['numnewdiag'].tot  = process(alldiag[:,:,indices].sum(axis=1)) # Axis 1 is populations
        if data is not None: 
            self.main['numnewdiag'].datatot = processdata(data['optnumdiag'])
            self.main['numnewdiag'].estimate = False # It's real data, not just an estimate
        
        self.main['numdeath'].pops = process(alldeaths[:,:,:,indices].sum(axis=1))
        self.main['numdeath'].tot  = process(alldeaths[:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations
        if data is not None: 
            self.main['numdeath'].datatot = processdata(data['optdeath'])
            self.main['numdeath'].estimate = True # It's not real data, just an estimate
        
        self.main['numplhiv'].pops = process(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1)) # Axis 1 is health state
        self.main['numplhiv'].tot  = process(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 2 is populations
        if data is not None: 
            self.main['numplhiv'].datatot = processdata(data['optplhiv'])
            self.main['numplhiv'].estimate = True # It's not real data, just an estimate
        
        self.main['numaids'].pops = process(allpeople[:,allaids,:,:][:,:,:,indices].sum(axis=1)) # Axis 1 is health state
        self.main['numaids'].tot  = process(allpeople[:,allaids,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 2 is populations

        self.main['numdiag'].pops = process(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1)) # Note that allpeople[:,txinds,:,indices] produces an error
        self.main['numdiag'].tot = process(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations
        
        self.main['propdiag'].pops = process(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['propdiag'].tot  = process(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations
        if data is not None: self.main['propdiag'].datatot = processdata(data['optpropdx'])
        
        self.main['numevercare'].pops = process(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=1)) #  Note that allpeople[:,txinds,:,indices] produces an error
        self.main['numevercare'].tot  = process(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations

        self.main['propevercare'].pops = process(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['propevercare'].tot  = process(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations

        self.main['numincare'].pops = process(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=1)) #  Note that allpeople[:,txinds,:,indices] produces an error
        self.main['numincare'].tot  = process(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations

        self.main['propincare'].pops = process(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['propincare'].tot  = process(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations
        if data is not None: self.main['propincare'].datatot = processdata(data['optpropcare'])

        self.main['numtreat'].pops = process(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1)) #  Note that allpeople[:,txinds,:,indices] produces an error
        self.main['numtreat'].tot = process(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations
        if data is not None: self.main['numtreat'].datatot = processdata(data['numtx'])

        self.main['costtreat'].pops = process(allcosttreat[:,:,indices])
        self.main['costtreat'].tot  = process(allcosttreat[:,:,indices].sum(axis=1)) # Axis 1 is populations

        self.main['proptreat'].pops = process(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['proptreat'].tot  = process(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations
        if data is not None: self.main['proptreat'].datatot = processdata(data['optproptx'])

        self.main['propplhivtreat'].pops = process(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['propplhivtreat'].tot = process(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations

        self.main['numsuppressed'].pops = process(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=1)) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
        self.main['numsuppressed'].tot = process(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations

        self.main['propsuppressed'].pops = process(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['propsuppressed'].tot = process(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations
        if data is not None: self.main['propsuppressed'].datatot = processdata(data['optpropsupp'])

        self.main['propplhivsupp'].pops = process(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1),eps), percent=True) 
        self.main['propplhivsupp'].tot = process(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)),eps), percent=True) # Axis 1 is populations

        self.main['popsize'].pops = process(allpeople[:,:,:,indices].sum(axis=1))
        self.main['popsize'].tot = process(allpeople[:,:,:,indices].sum(axis=(1,2)))
        if data is not None: 
            self.main['popsize'].datatot  = processtotalpopsizedata(self, data['popsize'])
            self.main['popsize'].datapops = processdata(data['popsize'], uncertainty=True)

        
        # Calculate DALYs
        
        ## Years of life lost
        yllpops = alldeaths.sum(axis=1) # Total deaths per population, sum over health states
        for pk,popkey in enumerate(self.popkeys): # Loop over each population
            meanage = self.pars['age'][pk].mean()
            potentialyearslost = max(0,lifeexpectancy-meanage) # Don't let this go negative!
            if discountrate>0 and discountrate<1: # Make sure it has reasonable bounds
                denominator = log(1-discountrate) # Start calculating the integral of (1-discountrate)**potentialyearslost
                numerator = (1-discountrate)**potentialyearslost - 1 # Minus 1 for t=0
                discountedyearslost = numerator/denominator # See https://en.wikipedia.org/wiki/Lists_of_integrals#Exponential_functions
            elif discountrate==0: # Nothing to discount
                discountedyearslost = potentialyearslost
            else:
                raise OptimaException('Invalid discount rate (%s)' % discountrate)
            yllpops[:,pk,:] *= discountedyearslost # Multiply by the number of potential years of life lost
        ylltot = yllpops.sum(axis=1) # Sum over populations
        
        ## Years lived with disability
        disutiltx = self.pars['disutiltx'].y
        disutils = [self.pars['disutil'+key].y for key in self.settings.hivstates]
        yldpops = allpeople[:,alltx,:,:].sum(axis=1)     * disutiltx
        yldtot  = allpeople[:,alltx,:,:].sum(axis=(1,2)) * disutiltx
        notonart = set(self.settings.notonart)
        for h,key in enumerate(self.settings.hivstates): # Loop over health states
            hivstateindices = set(getattr(self.settings,key))
            healthstates = array(list(hivstateindices & notonart)) # Find the intersection of this HIV state and not on ART states
            yldpops += allpeople[:,healthstates,:,:].sum(axis=1) * disutils[h]
            yldtot += allpeople[:,healthstates,:,:].sum(axis=(1,2)) * disutils[h]
        
        ## Add them up
        dalypops = yllpops + yldpops
        dalytot  = ylltot + yldtot
        self.main['numdaly'].pops = process(dalypops[:,:,indices])
        self.main['numdaly'].tot  = process(dalytot[:,indices])
        
        
        ## Other indicators
        upperagelims = self.pars['age'][:,1] # All populations, but upper range
        adultpops = findinds(upperagelims>=15)
        childpops = findinds(upperagelims<15)
        if len(adultpops): self.other['adultprev'].tot = process(allpeople[:,allplhiv,:,:][:,:,adultpops,:][:,:,:,indices].sum(axis=(1,2)) / (eps+allpeople[:,:,adultpops,:][:,:,:,indices].sum(axis=(1,2))), percent=True) # Axis 2 is populations
        else:              self.other['adultprev'].tot = self.main['prev'].tot # In case it's not available, use population average
        if len(childpops): self.other['childprev'].tot = process(allpeople[:,allplhiv,:,:][:,:,childpops,:][:,:,:,indices].sum(axis=(1,2)) / (eps+allpeople[:,:,childpops,:][:,:,:,indices].sum(axis=(1,2))), percent=True) # Axis 2 is populations
        else:              self.other['childprev'].tot = self.main['prev'].tot
        self.other['adultprev'].pops = self.main['prev'].pops # This is silly, but avoids errors from a lack of consistency of these results not having pop attributes
        self.other['childprev'].pops = self.main['prev'].pops
        
        self.other['numotherdeath'].pops = process(otherdeaths[:,:,indices])
        self.other['numotherdeath'].tot = process(otherdeaths[:,:,indices].sum(axis=1)) # Axis 1 is populations
        
        self.other['numbirths'].pops = process(allbirths[:,:,indices])
        self.other['numbirths'].tot = process(allbirths[:,:,indices].sum(axis=1))
        
        # Add in each health state
        for healthkey in self.settings.healthstates: # Health keys: ['susreg', 'progcirc', 'undx', 'dx', 'care', 'lost', 'usvl', 'svl']
            healthinds = getattr(self.settings, healthkey)
            self.other['only'+healthkey].pops = process(allpeople[:,healthinds,:,:][:,:,:,indices].sum(axis=1)) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
            self.other['only'+healthkey].tot =  process(allpeople[:,healthinds,:,:][:,:,:,indices].sum(axis=(1,2))) # Axis 1 is populations

        return None
        
        
    def export(self, filename=None, folder=None, bypop=True, sep=',', ind=None, key=None, sigfigs=3, writetofile=True, asexcel=True, verbose=2):
        ''' Method for exporting results to an Excel or CSV file '''

        # Handle export by either index or key -- WARNING, still inelegant at best! Accepts key or ind, not both
        if key is not None: # Key overrides ind -- find the index corresponding to this key
            try:    
                ind = self.keys.index(key)
            except:
                errormsg = 'Results key "%s" not found; choices are: %s' % (key, self.keys)
                raise OptimaException(errormsg)
        if ind is None: ind = 0 # If not supplied, just assume 'best'/default/etc.
        if key is None: key = 0 # Likewise -- WARNING, inelegant
        
        npts = len(self.tvec)
        mainkeys = self.main.keys()
        outputstr = sep.join(['Indicator','Population'] + ['%i'%t for t in self.tvec]) # Create header and years
        for mainkey in mainkeys:
            if bypop: outputstr += '\n' # Add a line break between different indicators
            if bypop: popkeys = ['tot']+self.popkeys # include total even for bypop -- WARNING, don't try to change this!
            else:     popkeys = ['tot']
            for pk,popkey in enumerate(popkeys):
                outputstr += '\n'
                if bypop and popkey!='tot': data = self.main[mainkey].pops[ind][pk-1,:] # WARNING, assumes 'tot' is always the first entry
                else:                       data = self.main[mainkey].tot[ind][:]
                outputstr += self.main[mainkey].name+sep+popkey+sep
                for t in range(npts):
                    if self.main[mainkey].ispercentage: outputstr += ('%s'+sep) % sigfig(data[t], sigfigs=sigfigs)
                    else:                           outputstr += ('%i'+sep) % data[t]
       
        # Handle budget and coverage
        thisbudget = []
        thiscoverage = []
        tvbudget = []
        try:    thisbudget = self.budgets[key]
        except: pass
        try:    thiscoverage = self.coverages[key]
        except: pass
        try:    tvbudget = self.timevarying[key]
        except: pass
        
        if len(thisbudget): # WARNING, does not support multiple years
            outputstr += '\n\n\n'
            outputstr += sep*2+'Budget\n'
            outputstr += sep*2+sep.join(thisbudget.keys()) + '\n'
            outputstr += sep*2+sep.join([str(val) for val in thisbudget.values()]) + '\n'
        
        if len(thiscoverage): # WARNING, does not support multiple years
            covvals = thiscoverage.values()
            for c in range(len(covvals)):
                if checktype(covvals[c], 'arraylike'):
                    covvals[c] = covvals[c][0] # Only pull out the first element if it's an array/list
                if covvals[c] is None: covvals[c] = 0 # Just reset
            outputstr += '\n\n\n'
            outputstr += sep*2+'Coverage\n'
            outputstr += sep*2+sep.join(thiscoverage.keys()) + '\n'
            outputstr += sep*2+sep.join([str(val) for val in covvals]) + '\n' # WARNING, should have this val[0] but then dies with None entries

        if len(tvbudget):
            tvyears  = tvbudget['tvyears']
            progkeys = tvbudget['tvbudgets'].keys()
            tvdata   = tvbudget['tvbudgets'][:]
            outputstr += '\n\n\n'
            outputstr += sep*2+'Time-varying' + '\n'
            outputstr += sep+sep.join(['Year']+progkeys) + '\n'
            for y,year in enumerate(tvyears): # Loop over years as rows
                outputstr += sep+str(year)+sep+sep.join([str(val) for val in tvdata[:,y]]) + '\n' # Join together programs as columns
            
        if writetofile: 
            ext = 'xlsx' if asexcel else 'csv'
            defaultname = self.projectinfo['name']+'-'+self.name # Default filename if none supplied
            fullpath = makefilepath(filename=filename, folder=folder, default=defaultname, ext=ext, sanitize=True)
            if asexcel:
                outputdict = {'Results':outputstr}
                exporttoexcel(fullpath, outputdict)
            else:
                with open(fullpath, 'w') as f: f.write(outputstr)
            printv('Results exported to "%s"' % fullpath, 2, verbose)
            return fullpath
        else:
            return outputstr
        
    
    def get(self, what=None, year=None, key=None, pop=None, dosum=False, blhkey=None):
        '''
        A small function to make it easier to access results. For example, to 
        get the number of deaths in the current year, just do
        
        P = demo(0)
        P.result().get('numinci')
        
        To get multiple years, simply enter a pair of years, or 'all', e.g.
        P.result().get('numinci', [2015,2030])
        P.result().get('numinci', 'all')
        
        To return a sum, set dosum=True:
        P.result().get('numinci', [2015,2030], dosum=True)
        
        The "key" kwarg is mostly used for multiresultsets to choose which simulation result to get.
        For non-multiresultsets, [0,1,2] will choose [best, low, high].
        '''
        # If kwargs aren't specified, use now
        if key    is None: key  = 0
        if year   is None: year = self.projectref().settings.now
        if pop    is None: pop = 'tot'
        if blhkey is None: blhkey = 0
        
        # Figure out which dictionary to use
        if   what in self.main.keys():   resultobj = self.main[what]
        elif what in self.other.keys():  resultobj = self.other[what]
        else:
            errormsg = 'Key %s not found; must be one of:\n%s' % (what, self.main.keys()+self.other.keys())
            raise OptimaException(errormsg)
            
        # Use either total (by default) or a given population
        if pop=='tot':
            timeseries = resultobj.tot[key]
        else:
            if isinstance(pop,str): 
                try:
                    pop = self.popkeys.index(pop) # Convert string to number
                except:
                    errormsg = 'Population key %s not found; must be one of: %s' % (pop, self.popkeys)
                    raise OptimaException(errormsg)
            timeseries = resultobj.pops[key][pop,:]
        
        # Get the index and return the result
        if checktype(year, 'number'):
            index = findnearest(self.tvec, year)
            result = timeseries[index]
        elif checktype(year, 'arraylike'):
            startind = findnearest(self.tvec, year[0])
            finalind = findnearest(self.tvec, year[1])
            result = timeseries[startind:finalind+1]
        elif year=='all':
            result = timeseries[:]
        else:
            errormsg = 'Year argument must be a number, pair of years, or "all", not "%s"' % year
            raise OptimaException(errormsg)
        
        if dosum:
            result = promotetoarray(result).sum()
        
        return result
    
    
    def summary(self, year=None, key=None, blhkey=None, doprint=True):
        '''
        Get a text summary of key results for a given year.
        
        Example:
            import optima as op
            P = op.demo(0)
            P.result().summary() # Show default results for current year
            P.result().summary(year=2020) # Show default results for 2020
            P.defaultscenarios(doplot=False) # Run a multi sim
            P.result().summary(year=2020) # For a multiresultset, show default results for current year for all simulations
            P.result().summary(year=[2015,2020], key=['Baseline', 'Zero budget']) # Show multiple results for multiple years
        '''
        if key    is None: key  = dcp(self.keys)
        if year   is None: year = self.projectref().settings.now
        if blhkey is None: blhkey = 0 # Only get best result
        yearlist = promotetolist(year)
        keylist  = promotetolist(key)
        nyears = len(yearlist)
        nkeys  = len(keylist)
        
        # Define settings
        padlen = 2 # How much space to have at beginning and between columns
        headerlen = 8 # Default header length
        epikeylist = ['prev', None, 'numinci', 'numdeath', 'numplhiv', 'numtreat', None, 'propdiag', 'propplhivtreat', 'propplhivsupp', None, 'proptreat', 'propsuppressed'] # Define what to include -- "None" is a spacer
        
        # Figure out how to make the labels
        if   keylist==[0]:            keystr = '' # Skip adding here, since don't need or will add later
        elif (nkeys>1 and nyears==1): keystr = ', year %s' % yearlist[0] # Show year
        elif (nkeys>1 and nyears>1):  keystr = ', keys "%s"' % ('", "'.join(keylist)) # Multiple keys and multiple years, show them here since can't show them in headers
        else:                         keystr = ', key "%s"' % keylist[0] # Add sngle key information, if nontrivial
        output = 'Summary of results for "%s"%s:\n\n' % (self.name, keystr) # Create output
        pad = ' '*padlen
        labellen = max([len(res.name) for res in self.main.values()]) # Figure out how long the label needs to be
        labelctrl = '%%%is: ' % labellen # e.g. '%30s'
        
        # Year or key header
        if nkeys>nyears: headerlen = padlen+max([len(tmpkey) for tmpkey in keylist]) # Find out the maximum length required
        headerctrl  = '%%%is'   % headerlen # Format for header, e.g.'%8s'
        percentctrl = '%%%i.2f' % headerlen # Format for percentages, e.g.'%8.2f'
        numberctrl  = '%%%i.0f' % headerlen # Format for numbers, e.g.'%8.0f'
        output += pad + labelctrl % '' # Add a blank space of the right length
        for year in yearlist:
            for key in keylist: # Loop over here too to duplicate if required
                if nyears>=nkeys: output += numberctrl % year # The header is the year
                else:             output += headerctrl % key # The header is the key
        output += '\n'
        
        # Get standard indicators
        for epikey in epikeylist:
            if epikey is None:
                output += '\n' # Add a space
            else:
                thisresult = self.main[epikey]
                label = labelctrl % thisresult.name
                output += pad + label
                for year in yearlist:
                    for key in keylist:
                        thisnumber = self.get(what=epikey, year=year, key=key, blhkey=blhkey)
                        if thisresult.ispercentage: resultstr = percentctrl % (thisnumber*100.0)
                        else:                       resultstr = numberctrl  % (thisnumber)
                        output += resultstr
                output += '\n'
        
        maxlinelen = max([len(line) for line in output.splitlines()])
        divider = '-'*maxlinelen + '\n'
        output = divider + output + divider
        if doprint: 
            print(output)
            return None
        else:
            return output
        
            
        



class Multiresultset(Resultset):
    ''' Structure for holding multiple kinds of results, e.g. from an optimization, or scenarios '''
    def __init__(self, resultsetlist=None, name=None):
        # Basic info
        self.name = name if name else 'default'
        self.uid = uuid()
        self.created = today()
        self.nresultsets = len(resultsetlist)
        self.resultsetnames = [result.name for result in resultsetlist] # Pull the names of the constituent resultsets
        self.keys = []
        self.budgets = odict()
        self.coverages = odict()
        self.budgetyears = odict() 
        self.setup = odict() # For storing the setup attributes (e.g. tvec)
        if type(resultsetlist)==list: pass # It's already a list, carry on
        elif type(resultsetlist) in [odict, dict]: resultsetlist = resultsetlist.values() # Convert from odict to list
        elif resultsetlist is None: raise OptimaException('To generate multi-results, you must feed in a list of result sets: none provided')
        else: raise OptimaException('Resultsetlist type "%s" not understood' % str(type(resultsetlist)))
        
        # Fundamental quantities -- populated by project.runsim()
        setupattrs = ['tvec', 'dt', 'popkeys', 'projectinfo', 'projectref', 'parsetname', 'progsetname', 'pars', 'data', 'datayears', 'settings'] # Attributes that should be the same across all results sets
        for attr in setupattrs: setattr(self, attr, None) # Shared attributes across all resultsets

        # Main and other results -- time series, by population -- get right structure, but clear out results -- WARNING, must match format above!
        self.main  = dcp(resultsetlist[0].main) # For storing main results -- get the format from the first entry, since should be the same for all
        self.other = dcp(resultsetlist[0].other) 
        for poptot in ['pops', 'tot']:
            for key in self.main.keys():
                setattr(self.main[key], poptot, odict()) # Turn all of these into an odict -- e.g. self.main['prev'].pops = odict()
            for key in self.other.keys():
                setattr(self.other[key], poptot, odict()) # Turn all of these into an odict -- e.g. self.main['prev'].pops = odict()

        for i,rset in enumerate(resultsetlist):
            while rset.name is None or rset.name in self.keys:
                if rset.name is None: rset.name = str(i)
                if rset.name in self.keys: rset.name += '-new'
            key = rset.name
            self.keys.append(key)
            self.setup[key] = odict() # For storing the setup attributes (e.g. tvec)
            
            # First, loop over (presumably) shared setup attributes, and hope they match, but store them separately if they don't
            for attr in setupattrs:
                orig = getattr(self, attr)
                new = getattr(rset, attr)
                self.setup[key][attr] = new # Copy here too
                if orig is None: setattr(self, attr, new) # For most purposes, only need one copy of these things since won't differ
            
            # Now, the real deal: fix self.main and self.other
            best = 0 # Key for best data -- discard uncertainty
            for at in ['pops', 'tot']:
                for key2 in self.main.keys():
                    getattr(self.main[key2], at)[key] = getattr(rset.main[key2], at)[best] # Add data: e.g. self.main['prev'].pops['foo'] = rset.main['prev'].pops[0] -- WARNING, the 0 discards uncertainty data
                for key2 in self.other.keys():
                    getattr(self.other[key2], at)[key] = getattr(rset.other[key2], at)[best] # Add data: e.g. self.main['prev'].pops['foo'] = rset.main['prev'].pops[0] -- WARNING, the 0 discards uncertainty data

            # Finally, process the budget and budgetyears -- these  are only needed for the budget/coverage conversions
            if len(rset.budget) or len(rset.coverage):
                parset  = rset.projectref().parsets[rset.parsetname]
                progset = rset.projectref().progsets[rset.progsetname]
            if len(rset.budget):       # If it has a budget, overwrite coverage information by calculating from budget
                self.budgets[key]      = rset.budget
                self.budgetyears[key]  = rset.budgetyears
                self.coverages[key]    = progset.getprogcoverage(budget=rset.budget, t=rset.budgetyears, parset=parset, results=rset, proportion=True) # Set proportion TRUE here, because coverage will be outputted as PERCENT covered
            elif len(rset.coverage):   # If no budget, compute budget from coverage
                self.coverages[key]    = rset.coverage
                self.budgetyears[key]  = rset.budgetyears
                self.budgets[key]      = progset.getprogbudget(coverage=rset.coverage, t=rset.budgetyears, parset=parset, results=rset, proportion=False) # Set proportion FALSE here, because coverage will be inputted as NUMBER covered    
            
        # Handle any keys that haven't been handled already, including the barber's hair
        missingattrs = odict() # Create an odict for storing the attributes to be populated
        for i,rset in enumerate(resultsetlist): # Loop over the results being combined
            rsetattrs = rset.__dict__.keys() # Get all attributes
            for rsetattr in rsetattrs:
                if not(hasattr(self, rsetattr)): # If it hasn't been processed already, make an empty odict
                    if rsetattr not in missingattrs.keys(): # Add to the list if it's not there already
                        missingattrs[rsetattr] = [i] # It doesn't exist: create a list of indices to loop over
                    else:
                        missingattrs[rsetattr].append(i) # It exists already: append this index
        for attr,indlist in missingattrs.items(): # Loop over all of the attributes identified as missing
            setattr(self, attr, odict()) # Create a new odict -- e.g. self.rawoutcomes = odict()
            for ind in indlist: # Loop over each of the stored indices
                key = self.keys[ind] # Get the key for this index
                thisattr = getattr(resultsetlist[ind], attr) # e.g. resultsetlist[0].rawoutcomes
                getattr(self, attr)[key] = thisattr # e.g. self.rawoutcomes['init'] = resultsetlist[0].rawoutcomes
        
        
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '      Project name: %s\n'    % self.projectinfo['name']
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '      Results sets: %s\n'    % self.keys
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def diff(self, base=None):
        '''
        Calculate the difference between the first (usually default) set of results in a multiresultset and others.
        
        Use this method to calculate the impact of scenarios, e.g.
            import optima as op
            P = op.demo(0)
            P.defaultscenarios(doplot=False)
            resultsdiff = P.result().diff()
            resultsdiff.get('numplhiv', key='Zero budget', year='all')
        
        Use the "base" kwarg (which can be a key or an index) to set the baseline:
            resultsdiff = P.result().diff(base='Zero budget')
            resultsdiff.get('numplhiv', key='Baseline conditions')
        '''
        
        if base is None: base = 0
        
        resultsdiff = dcp(self)
        resultsdiff.projectref = Link(self.projectref()) # Restore link
        resultsdiff.name += ' difference' # Update the name
        
        # Collect all results objects
        resultsobjs = []
        for typekey in resultsdiff.main.keys():
            resultsobjs.append(resultsdiff.main[typekey])
        if hasattr(resultsdiff,'other'):
            for typekey in resultsdiff.other.keys():
                resultsobjs.append(resultsdiff.other[typekey])
        
        # Calculate the differences
        for resultsobj in resultsobjs:
            basetot = dcp(resultsobj.tot[base]) # Need to dcp since mutable
            basepop = dcp(resultsobj.pops[base])
            for simkey in resultsdiff.resultsetnames:
                resultsobj.tot[simkey]  -= basetot
                resultsobj.pops[simkey] -= basepop
        
        return resultsdiff
    
    
    def export(self, filename=None, folder=None, ind=None, writetofile=True, verbose=2, asexcel=True, **kwargs):
        ''' A method to export each multiresult to a different sheet in Excel (or to a single large text file) '''
        
        if asexcel: outputdict = odict()
        else:       outputstr = ''
        for key in self.keys:
            thisoutput = Resultset.export(self, ind=ind, key=key, writetofile=False, **kwargs)
            if asexcel:
                outputdict[key] = thisoutput
            else:
                outputstr += '%s\n\n' % key
                outputstr += thisoutput
                outputstr += '\n'*5
        
        if writetofile: 
            ext = 'xlsx' if asexcel else 'csv'
            defaultname = self.projectinfo['name']+'-'+self.name # Default filename if none supplied
            fullpath = makefilepath(filename=filename, folder=folder, default=defaultname, ext=ext)
            if asexcel:
                exporttoexcel(fullpath, outputdict)
            else:
                with open(fullpath, 'w') as f: f.write(outputstr)
            printv('Results exported to "%s"' % fullpath, 2, verbose)
            return fullpath
        else:
            if asexcel: return outputdict
            else:       return outputstr






class BOC(object):
    ''' Structure to hold a budget and outcome array for geospatial analysis'''
    
    def __init__(self, name='boc', x=None, y=None, budgets=None, defaultbudget=None, objectives=None, constraints=None, parsetname=None, progsetname=None):
        self.uid = uuid()
        self.created = today()
        self.x = x if x else [] # A list of budget totals
        self.y = y if y else [] # A corresponding list of 'maximally' optimised outcomes
        self.yinf = None # Store the outcome for infinite money to be plotted separately if desired
        self.parsetname = parsetname
        self.progsetname = progsetname
        self.ybaseline = None # Outcome for baseline
        self.yregionoptim = None # Outcome for within-region optimization -- calculated by project.runBOC()
        self.ygaoptim = None # Outcome for GA optimization -- calculated by portfolio.runGA()
        self.budgets = budgets if budgets else odict() # A list of actual budgets
        self.defaultbudget = defaultbudget # The initial budget, pre-optimization
        self.regionoptimbudget = None # The region-optimized budget, pre-GA
        self.gaoptimbudget = None # The optimized budget, assigned by GA
        self.objectives = objectives # Specification for what outcome y represents (objectives['budget'] excluded)
        self.constraints = constraints # Likewise...
        self.name = name # Required by rmresult in Project.

    def __repr__(self):
        ''' Print out summary stats '''
        output = defaultrepr(self)
        return output
        
    def getoutcome(self, budgets, deriv=False, method=None, smoothness=None):
        ''' Get interpolated outcome for a corresponding list of budgets '''
        x = dcp(self.x)
        y = dcp(self.y)
        x.append(1e15+max(self.x))  # Big number
        y.append(self.yinf)
        output = pchip(x, y, budgets, deriv=deriv, method=method, smoothness=smoothness)
        return output
        
    def plot(self, deriv=False, returnplot=False, initbudget=None, optbudget=None, baseline=0):
        ''' Plot the budget-outcome curve '''
        from pylab import xlabel, ylabel, show
        
        x = dcp(self.x)
        y = dcp(self.y)
        x.append(1e15+max(self.x))  # Big number
        y.append(min(self.y))
        
        ax = plotpchip(x, y, deriv = deriv, returnplot = True, initbudget = initbudget, optbudget = optbudget)                 # Plot interpolation
        xlabel('Budget')
        ax.set_xlim((ax.get_xlim()[0],max(self.x+[optbudget]))) # Do not bother plotting the large x value, even though its effect on interpolation is visible
        if not deriv: ylabel('Outcome')
        else: ylabel('Marginal outcome')
        if baseline==0: ax.set_ylim((0,ax.get_ylim()[1])) # Reset baseline
        
        if returnplot: return ax
        else: show()
        return None


class ICER(object):
    ''' Structure to hold the results of an ICER run; similar to the BOC class '''
    
    def __init__(self, name='icer', objective=None, startyear=None, endyear=None, rawx=None, rawy=None, x=None, icer=None, summary=None, baseline=None, keys=None, defaultbudget=None, parsetname=None, progsetname=None):
        self.name          = name        # Required by rmresult in Project.
        self.uid           = uuid()      # Unique identifier
        self.created       = today()     # When created
        self.objective     = objective   # The objective to calculate the ICER for
        self.startyear     = startyear   # The year to start the budget and the outcome calculation
        self.endyear       = endyear     # Ditto, to end
        self.parsetname    = parsetname  # The parset used
        self.progsetname   = progsetname # The progset used
        self.rawx          = rawx if rawx is not None else odict() # An odict of budgets
        self.rawy          = rawy if rawy is not None else odict() # A corresponding odict of absolute outcomes
        self.x             = x    if x    is not None else []      # A list/array of budget ratios
        self.icer          = icer if icer is not None else odict() # Store the actual ICERs
        self.summary       = summary       # Store a summary of the results -- ICERs for each program at baseline
        self.baseline      = baseline      # The outcome given baseline conditions
        self.keys          = keys          # The program keys
        self.defaultbudget = defaultbudget # The baseline budget used
        

    def __repr__(self):
        ''' Print out summary stats '''
        output = defaultrepr(self)
        return output
    
    



def getresults(project=None, pointer=None, die=True):
    '''
    Function for returning the results associated with something. 'pointer' can eiher be a UID,
    a string representation of the UID, the actual pointer to the results, or a function to return the
    results.
    
    Example:
        results = P.parsets[0].getresults()
        calls
        getresults(P, P.parsets[0].resultsref)
        which returns
        P.results[P.parsets[0].resultsref]
    
    The "die" keyword lets you choose whether a failure to retrieve results returns None or raises an exception.    
    
    Version: 1.2 (2016feb06)
    '''
    # Nothing supplied, don't try to guess
    if pointer is None: 
        return None 
    
    # Normal usage, e.g. getresults(P, 3) will retrieve the 3rd set of results
    elif isinstance(pointer, (str, unicode, Number, type(uuid()))):
        if project is not None:
            resultnames = [res.name for res in project.results.values()]
            resultuids = [str(res.uid) for res in project.results.values()]
        else: 
            if die: raise OptimaException('To get results using a key or index, getresults() must be given the project')
            else: return None
        try: # Try using pointer as key -- works if name
            results = project.results[pointer]
            return results
        except: # If that doesn't match, keep going
            if pointer in resultnames: # Try again to extract it based on the name
                results = project.results[resultnames.index(pointer)]
                return results
            elif str(pointer) in resultuids: # Next, try extracting via the UID
                results = project.results[resultuids.index(str(pointer))]
                return results
            else: # Give up
                validchoices = ['#%i: name="%s", uid=%s' % (i, resultnames[i], resultuids[i]) for i in range(len(resultnames))]
                errormsg = 'Could not get result "%s": choices are:\n%s' % (pointer, '\n'.join(validchoices))
                if die: raise OptimaException(errormsg)
                else: return None
    
    # The pointer is the results object
    elif isinstance(pointer, (Resultset, Multiresultset, BOC)):
        return pointer # Return pointer directly if it's already a results set
    
    # It seems to be some kind of function, so try calling it -- might be useful for the database or something
    elif callable(pointer): 
        try: 
            return pointer()
        except:
            if die: raise OptimaException('Results pointer "%s" seems to be callable, but call failed' % str(pointer))
            else: return None
    
    # Could not figure out what to do with it
    else: 
        if die: raise OptimaException('Could not retrieve results \n"%s"\n from project \n"%s"' % (pointer, project))
        else: return None



def exporttoexcel(filename=None, outdict=None):
    '''
    Little function to format an output results string nicely for Excel
    Expects an odict of output strings.
    '''
    workbook = Workbook(filename)
    
    for key,outstr in outdict.items():
        worksheet = workbook.add_worksheet(sanitizefilename(key)) # A valid filename should also be a valid Excel key
        
        # Define formatting
        budcovformats = ['Budget', 'Coverage', 'Time-varying']
        colors = {'gentlegreen':'#3c7d3e', 'fadedstrawberry':'#ffeecb', 'edgyblue':'#bcd5ff','accountantgrey':'#f6f6f6', 'white':'#ffffff'}
        formats = dict()
        formats['plain'] = workbook.add_format({})
        formats['bold'] = workbook.add_format({'bg_color': colors['edgyblue'], 'bold': True})
        formats['number'] = workbook.add_format({'bg_color': colors['fadedstrawberry'], 'num_format':0x04})
        formats['header'] = workbook.add_format({'bg_color': colors['gentlegreen'], 'color': colors['white'], 'bold': True})
        
        # Convert from a string to a 2D array
        outlist = []
        for line in outstr.split('\n'):
            outlist.append([])
            for cell in line.split(','):
                if cell=='tot': cell = 'Total' # Hack to replace internal key with something more user-friendly
                outlist[-1].append(str(cell)) # If unicode, doesn't work
        
        # Iterate over the data and write it out row by row.
        row, col = 0, 0
        maxcol = 0
        for row in range(len(outlist)):
            for col in range(len(outlist[row])):
                maxcol = max(col,maxcol)
                thistxt = outlist[row][col]
                thisformat = 'plain'
                emptycell = not(thistxt)
                try: 
                    thistxt = float(thistxt)
                    numbercell = True
                except:
                    numbercell = False
                if row==0:                             thisformat = 'header'
                elif str(thistxt) in budcovformats:    thisformat = 'header'
                elif not emptycell and not numbercell: thisformat = 'bold'
                elif col<2 and not emptycell:          thisformat = 'bold'
                elif numbercell:                       thisformat = 'number'
                worksheet.write(row, col, thistxt, formats[thisformat])
        
        worksheet.set_column(2, maxcol, 15) # Make wider
        worksheet.set_column(1, 1, 20) # Make wider
        worksheet.set_column(0, 0, 50) # Make wider
        worksheet.freeze_panes(1, 2) # Freeze first row, first two columns
        
    workbook.close()
    
    return None
