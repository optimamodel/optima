"""
This module defines the classes for stores the results of a single simulation run.

Version: 2016jul06 by cliffk
"""

from optima import OptimaException, Settings, uuid, today, getdate, quantile, printv, odict, dcp, objrepr, defaultrepr, sigfig, pchip, plotpchip
from numpy import array, nan, zeros, arange, shape, maximum
from numbers import Number





class Result(object):
    ''' Class to hold overall and by-population results '''
    def __init__(self, name=None, ispercentage=False, pops=None, tot=None, datapops=None, datatot=None):
        self.name = name # Name of this parameter
        self.ispercentage = ispercentage # Whether or not the result is a percentage
        self.pops = pops # The model result by population, if available
        self.tot = tot # The model result total, if available
        self.datapops = datapops # The input data by population, if available
        self.datatot = datatot # The input data total, if available
        self.estimate = False # If the input data is an estimate rather than real data
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = defaultrepr(self)
        return output






class Resultset(object):
    ''' Structure to hold results '''
    def __init__(self, raw=None, name=None, pars=None, simpars=None, project=None, settings=None, data=None, parset=None, progset=None, budget=None, coverage=None, budgetyears=None, domake=True):
        # Basic info
        self.uid = uuid()
        self.created = today()
        self.name = name # May be blank if automatically generated, but can be overwritten
        
        # Turn inputs into lists if not already
        if raw is None: raise OptimaException('To generate results, you must feed in model output: none provided')
        if type(simpars)!=list: simpars = [simpars] # Force into being a list
        if type(raw)!=list: raw = [raw] # Force into being a list
        
        # Read things in from the project if defined
        if project is not None:
            if parset is None:
                try: parset = project.parsets[simpars[0]['parsetname']] # Get parset if not supplied -- WARNING, UGLY
                except: pass # Don't really worry if the parset can't be populated
            if progset is None:
                try: progset = project.progset[simpars[0]['progsetname']] # Get parset if not supplied -- WARNING, UGLY
                except: pass # Don't really worry if the parset can't be populated
            if data is None: data = project.data # Copy data if not supplied -- DO worry if data don't exist!
            if settings is None: settings = project.settings
        
        # Fundamental quantities -- populated by project.runsim()
        self.raw = raw
        self.pars = pars # Keep pars
        self.simpars = simpars # ...and sim parameters
        self.popkeys = raw[0]['popkeys']
        self.datayears = data['years'] if data is not None else None # Only get data years if data available
        self.project = project # ...and just store the whole project
        self.parset = dcp(parset) # Store parameters
        self.progset = dcp(progset) # Store programs
        self.data = dcp(data) # Store data
        if self.parset is not None:  self.parset.project  = project # Replace copy of project with reference to project
        if self.progset is not None: self.progset.project = project # Replace copy of project with reference to project
        self.budget = budget if budget is not None else odict() # Store budget
        self.coverage = coverage if coverage is not None else odict()  # Store coverage
        self.budgetyears = budgetyears if budgetyears is not None else odict()  # Store budget
        self.settings = settings if settings is not None else Settings()
        
        # Main results -- time series, by population
        self.main = odict() # For storing main results
        self.main['numinci']            = Result('Number of new infections')
        self.main['numdeath']           = Result('Number of HIV-related deaths')
        
        self.main['numplhiv']           = Result('Number of PLHIV')
        self.main['numdiag']            = Result('Number of diagnosed PLHIV')
        self.main['numevercare']        = Result('Number of PLHIV initially linked to care')
        self.main['numincare']          = Result('Number of PLHIV in care')
        self.main['numtreat']           = Result('Number of PLHIV on treatment')
        self.main['numsuppressed']      = Result('Number of virally suppressed PLHIV')
        
        self.main['propdiag']           = Result('PLHIV who are diagnosed (%)', ispercentage=True)
        self.main['propevercare']       = Result('Diagnosed PLHIV initially linked to care (%)', ispercentage=True)
        self.main['propincare']         = Result('Diagnosed PLHIV retained in care (%)', ispercentage=True)
        self.main['proptreat']          = Result('PLHIV in care who are on treatment (%)', ispercentage=True)
        self.main['propsuppressed']     = Result('Treated PLHIV who are virally suppressed (%)', ispercentage=True)
        
        self.main['prev']               = Result('HIV prevalence (%)', ispercentage=True)
        self.main['force']              = Result('Incidence (per 100 p.y.)', ispercentage=True)
        self.main['numnewdiag']         = Result('Number of new diagnoses')
        self.main['nummtct']            = Result('Number of HIV+ births')
        self.main['numhivbirths']       = Result('Number of births to HIV+ women')
        self.main['numpmtct']           = Result('Number of HIV+ women receiving PMTCT')
        self.main['popsize']            = Result('Population size')
        
        if domake: self.make()
    
    
    def __repr__(self):
        ''' Print out useful information when called -- WARNING, add summary stats '''
        output = '============================================================\n'
        output += '      Project name: %s\n'    % (self.project.name if self.project is not None else None)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
        
    
    def __add__(self, R2):
        ''' Define how to add two Resultsets '''
        if type(R2)!=Resultset: raise OptimaException('Can only add results sets with other results sets')
        for attr in ['tvec','popkeys']:
            if any(array(getattr(self,attr))!=array(getattr(R2,attr))):
                raise OptimaException('Cannot add Resultsets that have dissimilar "%s"' % attr)
        R1 = dcp(self) # Keep the properties of this first one
        R1.name += ' + ' + R2.name
        R1.uid = uuid()
        R1.created = today()
        keys = R1.main.keys()
        main1 = dcp(R1.main)
        main2 = dcp(R2.main)
        popsize1 = main1['popsize']
        popsize2 = main2['popsize']
        R1.main = odict()
        for key in keys:
            res1 = main1[key]
            res2 = main2[key]
            R1.main[key] = Result(name=res1.name, ispercentage=res1.ispercentage)
            
            # It's a number, can just sum the arrays
            if res1.ispercentage:
                for attr in ['pops', 'tot']:
                    this = getattr(res1, attr) + getattr(res2, attr)
                    setattr(R1.main[key], attr, this)
            
            # It's a percentage, average by population size
            else: 
                R1.main[key].tot  = 0*res1.tot  # Reset
                R1.main[key].pops = 0*res1.pops # Reset
                for t in range(shape(res1.tot)[-1]):
                    R1.main[key].tot[:,t] = (res1.tot[:,t]*popsize1.tot[0,t] + res2.tot[:,t]*popsize2.tot[0,t]) / (popsize1.tot[0,t] + popsize2.tot[0,t])
                    for p in range(len(R1.popkeys)):
                        R1.main[key].pops[:,p,t] = (res1.pops[:,p,t]*popsize1.pops[0,p,t] + res2.pops[:,p,t]*popsize2.pops[0,p,t]) / (popsize1.pops[0,p,t] + popsize2.pops[0,p,t])
        return R1
            
            
    
    
    
    def make(self, quantiles=None, annual=True, verbose=2):
        """ Gather standard results into a form suitable for plotting with uncertainties. """
        # WARNING: Should use indexes retrieved from project settings!
        
        printv('Making derived results...', 3, verbose)
        
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
        
        # Initialize
        if quantiles is None: quantiles = [0.5, 0.25, 0.75] # Can't be a kwarg since mutable
        tvec = dcp(self.raw[0]['tvec'])
        eps = self.settings.eps
        if annual is False: # Decide what to do with the time vector
            indices = arange(len(tvec)) # Use all indices
            self.tvec = tvec
        else: 
            indices = arange(0, len(tvec), int(round(1.0/(tvec[1]-tvec[0])))) # Subsample results vector -- WARNING, should dt be taken from e.g. Settings()?
            self.tvec = tvec[indices] # Subsample time vector too
        self.dt = self.tvec[1] - self.tvec[0] # Reset results.dt as well
        allpeople = dcp(array([self.raw[i]['people'] for i in range(len(self.raw))]))
        allinci   = dcp(array([self.raw[i]['inci'] for i in range(len(self.raw))]))
        alldeaths = dcp(array([self.raw[i]['death'] for i in range(len(self.raw))]))
        alldiag   = dcp(array([self.raw[i]['diag'] for i in range(len(self.raw))]))
        allmtct   = dcp(array([self.raw[i]['mtct'] for i in range(len(self.raw))]))
        allhivbirths = dcp(array([self.raw[i]['hivbirths'] for i in range(len(self.raw))]))
        allreceivepmtct = dcp(array([self.raw[i]['receivepmtct'] for i in range(len(self.raw))]))
        allplhiv = self.settings.allplhiv
        alldx = self.settings.alldx
        allevercare = self.settings.allevercare
        allcare = self.settings.allcare
        alltx = self.settings.alltx
        svl = self.settings.svl
        data = self.data
        
        self.main['prev'].pops = quantile(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1) / allpeople[:,:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['prev'].tot = quantile(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)) / allpeople[:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        if data is not None: 
            self.main['prev'].datapops = processdata(data['hivprev'], uncertainty=True)
            self.main['prev'].datatot = processdata(data['optprev'])
        
        self.main['force'].pops = quantile(allinci[:,:,indices] / allpeople[:,:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['force'].tot = quantile(allinci[:,:,indices].sum(axis=1) / allpeople[:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations

        self.main['numinci'].pops = quantile(allinci[:,:,indices], quantiles=quantiles)
        self.main['numinci'].tot = quantile(allinci[:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        if data is not None: 
            self.main['numinci'].datatot = processdata(data['optnuminfect'])
            self.main['numinci'].estimate = True # It's not real data, just an estimate
        
        self.main['nummtct'].pops = quantile(allmtct[:,:,indices], quantiles=quantiles)
        self.main['nummtct'].tot = quantile(allmtct[:,:,indices].sum(axis=1), quantiles=quantiles)

        self.main['numhivbirths'].pops = quantile(allhivbirths[:,:,indices], quantiles=quantiles)
        self.main['numhivbirths'].tot = quantile(allhivbirths[:,:,indices].sum(axis=1), quantiles=quantiles)

        self.main['numpmtct'].pops = quantile(allreceivepmtct[:,:,indices], quantiles=quantiles)
        self.main['numpmtct'].tot = quantile(allreceivepmtct[:,:,indices].sum(axis=1), quantiles=quantiles)

        self.main['numnewdiag'].pops = quantile(alldiag[:,:,indices], quantiles=quantiles)
        self.main['numnewdiag'].tot = quantile(alldiag[:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        if data is not None: 
            self.main['numnewdiag'].datatot = processdata(data['optnumdiag'])
            self.main['numnewdiag'].estimate = True # It's not real data, just an estimate
        
        self.main['numdeath'].pops = quantile(alldeaths[:,:,:,indices].sum(axis=1), quantiles=quantiles)
        self.main['numdeath'].tot = quantile(alldeaths[:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 1 is populations
        if data is not None: 
            self.main['numdeath'].datatot = processdata(data['optdeath'])
            self.main['numdeath'].estimate = True # It's not real data, just an estimate
        
        self.main['numplhiv'].pops = quantile(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['numplhiv'].tot = quantile(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        if data is not None: 
            self.main['numplhiv'].datatot = processdata(data['optplhiv'])
            self.main['numplhiv'].estimate = True # It's not real data, just an estimate
        
        self.main['numdiag'].pops = quantile(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1), quantiles=quantiles) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
        self.main['numdiag'].tot = quantile(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 1 is populations
        
        self.main['propdiag'].pops = quantile(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=1),eps), quantiles=quantiles) 
        self.main['propdiag'].tot = quantile(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,allplhiv,:,:][:,:,:,indices].sum(axis=(1,2)),eps), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['propdiag'].datatot = processdata(data['optpropdx'])
        
        self.main['numevercare'].pops = quantile(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=1), quantiles=quantiles) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
        self.main['numevercare'].tot = quantile(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 1 is populations

        self.main['propevercare'].pops = quantile(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1),eps), quantiles=quantiles) 
        self.main['propevercare'].tot = quantile(allpeople[:,allevercare,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), quantiles=quantiles) # Axis 1 is populations

        self.main['numincare'].pops = quantile(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=1), quantiles=quantiles) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
        self.main['numincare'].tot = quantile(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 1 is populations

        self.main['propincare'].pops = quantile(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=1),eps), quantiles=quantiles) 
        self.main['propincare'].tot = quantile(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alldx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['propincare'].datatot = processdata(data['optpropcare'])

        self.main['numtreat'].pops = quantile(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1), quantiles=quantiles) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
        self.main['numtreat'].tot = quantile(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['numtreat'].datatot = processdata(data['numtx'])

        self.main['proptreat'].pops = quantile(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=1),eps), quantiles=quantiles) 
        self.main['proptreat'].tot = quantile(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,allcare,:,:][:,:,:,indices].sum(axis=(1,2)),eps), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['proptreat'].datatot = processdata(data['optproptx'])

        self.main['numsuppressed'].pops = quantile(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=1), quantiles=quantiles) # WARNING, this is ugly, but allpeople[:,txinds,:,indices] produces an error
        self.main['numsuppressed'].tot = quantile(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 1 is populations

#        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        self.main['propsuppressed'].pops = quantile(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=1)/maximum(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=1),eps), quantiles=quantiles) 
        self.main['propsuppressed'].tot = quantile(allpeople[:,svl,:,:][:,:,:,indices].sum(axis=(1,2))/maximum(allpeople[:,alltx,:,:][:,:,:,indices].sum(axis=(1,2)),eps), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['propsuppressed'].datatot = processdata(data['optpropsupp'])

        self.main['popsize'].pops = quantile(allpeople[:,:,:,indices].sum(axis=1), quantiles=quantiles) 
        self.main['popsize'].tot = quantile(allpeople[:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles)
        if data is not None: self.main['popsize'].datapops = processdata(data['popsize'], uncertainty=True)



        

# WARNING, need to implement
#        disutils = [D[self.pars['const']['disutil'][key] for key in D['G['healthstates']]
#        tmpdalypops = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=1) * D['P['const['disutil['tx']
#        tmpdalytot = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=(1,2)) * D['P['const['disutil['tx']
#        for h in xrange(len(disutils)): # Loop over health states
#            healthstates = array([D['G['undx'][h], D['G['dx'][h], D['G['fail'][h]])
#            tmpdalypops += allpeople[:,healthstates,:,:].sum(axis=1) * disutils[h]
#            tmpdalytot += allpeople[:,healthstates,:,:].sum(axis=(1,2)) * disutils[h]
#        self.daly.pops = quantile(tmpdalypops, quantiles=quantiles)
#        self.daly.tot = quantile(tmpdalytot, quantiles=quantiles)
        
        return None # make()
        
        
    def export(self, filestem=None, bypop=False, sep=',', ind=0, sigfigs=3, writetofile=True, verbose=2):
        ''' Method for exporting results to a CSV file '''
        if filestem is None:  # Doesn't include extension, hence filestem
            if self.name is not None: filestem = self.project.name+'-'+self.name
            else: filestem = str(self.uid)
        filename = filestem + '.csv'
        npts = len(self.tvec)
        keys = self.main.keys()
        output = sep.join(['Indicator','Population'] + ['%i'%t for t in self.tvec]) # Create header and years
        for key in keys:
            if bypop: output += '\n' # Add a line break between different indicators
            if bypop: popkeys = ['tot']+self.popkeys # include total even for bypop -- WARNING, don't try to change this!
            else:     popkeys = ['tot']
            for pk,popkey in enumerate(popkeys):
                output += '\n'
                if bypop and popkey!='tot': data = self.main[key].pops[ind][pk-1,:] # WARNING, assumes 'tot' is always the first entry
                else:                       data = self.main[key].tot[ind][:]
                output += self.main[key].name+sep+popkey+sep
                for t in range(npts):
                    if self.main[key].ispercentage: output += ('%s'+sep) % sigfig(data[t])
                    else:                           output += ('%i'+sep) % data[t]
       
        if len(self.budget)>ind: # WARNING, does not support multiple years
            output += '\n\n\n'
            output += 'Budget\n'
            output += sep.join(self.budget[ind].keys()) + '\n'
            output += sep.join([str(val) for val in self.budget[ind].values()]) + '\n'
        
        if len(self.coverage)>ind: # WARNING, does not support multiple years
            output += '\n\n\n'
            output += 'Coverage\n'
            output += sep.join(self.coverage[ind].keys()) + '\n'
            output += sep.join([str(val) for val in self.coverage[ind].values()]) + '\n' # WARNING, should have this val[0] but then dies with None entries
            
        if writetofile: 
            with open(filename, 'w') as f: f.write(output)
            printv('Results exported to "%s"' % filename, 2, verbose)
            return None
        else:
            return output
        
                    
            
        





class Multiresultset(Resultset):
    ''' Structure for holding multiple kinds of results, e.g. from an optimization, or scenarios '''
    def __init__(self, resultsetlist=None, name=None):
        # Basic info
        self.name = name
        self.uid = uuid()
        self.created = today()
        self.nresultsets = len(resultsetlist)
        self.keys = []
        self.budget = odict()
        self.coverage = odict()
        self.budgetyears = odict() 
        if type(resultsetlist)==list: pass # It's already a list, carry on
        elif type(resultsetlist) in [odict, dict]: resultsetlist = resultsetlist.values() # Convert from odict to list
        elif resultsetlist is None: raise OptimaException('To generate multi-results, you must feed in a list of result sets: none provided')
        else: raise OptimaException('Resultsetlist type "%s" not understood' % str(type(resultsetlist)))
                
        
        # Fundamental quantities -- populated by project.runsim()
        sameattrs = ['tvec', 'dt', 'popkeys'] # Attributes that should be the same across all results sets
        commonattrs = ['project', 'data', 'datayears', 'settings'] # Uhh...same as sameattrs, not sure my logic in separating this out, but hesitant to remove because it made sense at the time :)
        diffattrs = ['parset', 'progset', 'raw', 'simpars'] # Things that differ between between results sets
        for attr in sameattrs+commonattrs: setattr(self, attr, None) # Shared attributes across all resultsets
        for attr in diffattrs: setattr(self, attr, odict()) # Store a copy for each resultset

        # Main results -- time series, by population -- get right structure, but clear out results -- WARNING, must match format above!
        self.main = dcp(resultsetlist[0].main) # For storing main results -- get the format from the first entry, since should be the same for all
        for key in self.main.keys():
            for at in ['pops', 'tot']:
                setattr(self.main[key], at, odict()) # Turn all of these into an odict -- e.g. self.main['prev'].pops = odict()

        for i,rset in enumerate(resultsetlist):
            key = rset.name if rset.name is not None else str(i)
            self.keys.append(key)
            
            # First, loop over shared attributes, and ensure they match
            for attr in sameattrs+commonattrs:
                orig = getattr(self, attr)
                new = getattr(rset, attr)
                if orig is None: setattr(self, attr, new) # Pray that they match, since too hard to compare
            
            # Loop over different attributes and append to the odict
            for attr in diffattrs:
                getattr(self, attr)[key] = getattr(rset, attr) # Super confusing, but boils down to e.g. self.raw['foo'] = rset.raw -- WARNING, does this even work?
            
            # Now, the real deal: fix self.main
            for key2 in self.main.keys():
                for at in ['pops', 'tot']:
                    getattr(self.main[key2], at)[key] = getattr(rset.main[key2], at)[0] # Add data: e.g. self.main['prev'].pops['foo'] = rset.main['prev'].pops[0] -- WARNING, the 0 discards uncertainty data
            
            # Finally, process the budget and budgetyears
            if getattr(rset,'budget'): # If it has a budget, overwrite coverage information by calculating from budget
                self.budget[key]      = rset.budget
                self.budgetyears[key] = rset.budgetyears
                self.coverage[key]    = rset.progset.getprogcoverage(budget=rset.budget, t=rset.budgetyears, parset=rset.parset, results=rset, proportion=True) # Set proportion TRUE here, because coverage will be outputted as PERCENT covered
            elif getattr(rset,'coverage'): # If no budget, compute budget from coverage
                self.coverage[key]      = rset.coverage
                self.budgetyears[key] = rset.budgetyears
                self.budget[key]    = rset.progset.getprogbudget(coverage=rset.coverage, t=rset.budgetyears, parset=rset.parset, results=rset, proportion=False) # Set proportion FALSE here, because coverage will be inputted as NUMBER covered    
        
        
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '      Project name: %s\n'    % (self.project.name if self.project is not None else None)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '      Results sets: %s\n'    % self.keys
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def export(self, filestem=None, ind=None, writetofile=True, verbose=2, **kwargs):
        ''' A method to export each multiresult to a different file...not great, but not sure of what's better '''
        if filestem is None: # Filestem rather than filename since doesn't include extension
            if self.name is not None: filestem = self.project.name+'-'+self.name
            else: filestem = str(self.uid)
        output = ''
        for k,key in enumerate(self.keys):
            thisfilestem = filestem+'-'+key
            output += '%s\n\n' % key
            output += Resultset.export(self, filestem=thisfilestem, ind=k, writetofile=False, **kwargs)
            output += '\n'*5
        
        if writetofile: 
            filename = filestem+'.csv'
            with open(filename, 'w') as f: f.write(output)
            printv('Results exported to "%s"' % filename, 2, verbose)
            return None
        else:
            return output






class BOC(object):
    ''' Structure to hold a budget and outcome array for geospatial analysis'''
    
    def __init__(self, name='unspecified', x=None, y=None, objectives=None):
        self.uid = uuid()
        self.created = today()
        self.x = x if x else [] # A list of budget totals
        self.y = y if y else [] # A corresponding list of 'maximally' optimised outcomes
        self.objectives = objectives # Specification for what outcome y represents (objectives['budget'] excluded)
        
        self.name = name # Required by rmresult in Project.

    def __repr__(self):
        ''' Print out summary stats '''
        output = '============================================================\n'
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
        
    def getoutcome(self, budgets):
        ''' Get interpolated outcome for a corresponding list of budgets '''
        return pchip(self.x, self.y, budgets)
        
    def getoutcomederiv(self, budgets):
        ''' Get interpolated outcome derivatives for a corresponding list of budgets '''
        return pchip(self.x, self.y, budgets, deriv = True)
        
    def plot(self, deriv = False, returnplot = False, initbudget = None, optbudget = None, baseline=0):
        ''' Plot the budget-outcome curve '''
        from pylab import xlabel, ylabel, show
        
        ax = plotpchip(self.x, self.y, deriv = deriv, returnplot = True, initbudget = initbudget, optbudget = optbudget)                 # Plot interpolation
        xlabel('Budget')
        if not deriv: ylabel('Outcome')
        else: ylabel('Marginal outcome')
        if baseline==0: ax.set_ylim((0,ax.get_ylim()[1])) # Reset baseline
        
        if returnplot: return ax
        else: show()
        return None







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