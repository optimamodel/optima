"""
This module defines the classes for stores the results of a single simulation run.

Version: 2015jan12 by cliffk
"""

from optima import uuid, today, getdate, quantile, printv, odict, dcp, objrepr, defaultrepr
from numpy import array, nan, zeros, arange



class Result(object):
    ''' A tiny class just to hold overall and by-population results '''
    def __init__(self, name=None, isnumber=True, pops=None, tot=None, datapops=None, datatot=None):
        self.name = name # Name of this parameter
        self.isnumber = isnumber # Whether or not the result is a number (instead of a percentage)
        self.pops = pops # The model result by population, if available
        self.tot = tot # The model result total, if available
        self.datapops = datapops # The input data by population, if available
        self.datatot = datatot # The input data total, if available
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = defaultrepr(self)
        return output



class Resultset(object):
    ''' Lightweight structure to hold results -- use this instead of a dict '''
    def __init__(self, name=None, raw=None, simpars=None, project=None, data=None, parset=None, domake=True):
        # Basic info
        self.uid = uuid()
        self.created = today()
        self.name = name # May be blank if automatically generated, but can be overwritten
        
        # Turn inputs into lists if not already
        if raw is None: raise Exception('To generate results, you must feed in model output: none provided')
        if type(simpars)!=list: simpars = [simpars] # Force into being a list
        if type(raw)!=list: raw = [raw] # Force into being a list
        
        # Fundamental quantities -- populated by project.runsim()
        self.raw = raw
        self.simpars = simpars # ...and sim parameters
        self.tvec = raw[0]['tvec'] # Copy time vector
        self.dt   = self.tvec[1] - self.tvec[0] # And pull out dt since useful
        self.popkeys = raw[0]['popkeys']
        if project is not None:
            if parset is None:
                try: parset = project.parsets[simpars[0]['parsetname']] # Get parset if not supplied -- WARNING, UGLY
                except: pass # Don't really worry if the parset can't be populated
            if data is None: data = project.data # Copy data if not supplied -- DO worry if data don't exist!
        self.datayears = data['years'] if data is not None else None # Only get data years if data available
        self.project = project # ...and just store the whole project
        self.parset = parset # Store parameters
        self.data = data # Store data
        
        # Main results -- time series, by population
        self.main = odict() # For storing main results
        self.main['prev'] = Result('HIV prevalence (%)', isnumber=False)
        self.main['force'] = Result('Force-of-infection (%/year)', isnumber=False)
        self.main['numinci'] = Result('Number of new infections')
        self.main['numplhiv'] = Result('Number of PLHIV')
        self.main['numdeath'] = Result('Number of HIV-related deaths')
        self.main['numdiag'] = Result('Number of people diagnosed')
#        self.main['dalys'] = Result('Number of DALYs')
#        self.main['numtreat'] = Result('Number of people on treatment')
#        self.main['numnewtreat'] = Result('Number of people newly treated')
#        self.main['numnewdiag'] = Result('Number of new diagnoses')
        
        # Other quantities
#        self.other = odict() # For storing main results
#        self.births = Result()
#        self.mtct = Result()
#        self.newtreat = Result()
#        self.newcircum = Result()
#        self.numcircum = Result()
#        self.reqcircum = Result()
#        self.sexinci = Result()
        
        if domake: self.make()
#    
    
    
    def __repr__(self):
        ''' Print out useful information when called -- WARNING, add summary stats '''
        output = '============================================================\n'
        output += '      Project name: %s\n'    % (self.project.name if self.project is not None else None)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    
    def make(self, quantiles=None, annual=True, verbose=2):
        """ Gather standard results into a form suitable for plotting with uncertainties. """
        
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
        if annual is False:
            indices = arange(len(self.tvec)) # Use all indices
        else: 
            indices = arange(0, len(self.tvec), int(round(1.0/(self.tvec[1]-self.tvec[0])))) # Subsample results vector -- WARNING, should dt be taken from e.g. Settings()?
            self.tvec = self.tvec[indices] # Subsample time vector too
        allpeople = array([self.raw[i]['people'] for i in range(len(self.raw))])
        allinci   = array([self.raw[i]['inci'] for i in range(len(self.raw))])
        alldeaths = array([self.raw[i]['death'] for i in range(len(self.raw))])
        alldiag   = array([self.raw[i]['diag'] for i in range(len(self.raw))])
        data = self.data
        
        self.main['prev'].pops = quantile(allpeople[:,1:,:,indices].sum(axis=1) / allpeople[:,:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['prev'].tot = quantile(allpeople[:,1:,:,indices].sum(axis=(1,2)) / allpeople[:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        if data is not None: 
            self.main['prev'].datapops = processdata(data['hivprev'], uncertainty=True)
            self.main['prev'].datatot = processdata(data['optprev'])
        
        self.main['numplhiv'].pops = quantile(allpeople[:,1:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['numplhiv'].tot = quantile(allpeople[:,1:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        if data is not None: self.main['numplhiv'].datatot = processdata(data['optplhiv'])
        
        self.main['numinci'].pops = quantile(allinci[:,:,indices], quantiles=quantiles)
        self.main['numinci'].tot = quantile(allinci[:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['numinci'].datatot = processdata(data['optnuminfect'])

        self.main['force'].pops = quantile(allinci[:,:,indices] / allpeople[:,:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['force'].tot = quantile(allinci[:,:,indices].sum(axis=1) / allpeople[:,:,:,indices].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        
        self.main['numdeath'].pops = quantile(alldeaths[:,:,indices], quantiles=quantiles)
        self.main['numdeath'].tot = quantile(alldeaths[:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['numdeath'].datatot = processdata(data['optdeath'])

        self.main['numdiag'].pops = quantile(alldiag[:,:,indices], quantiles=quantiles)
        self.main['numdiag'].tot = quantile(alldiag[:,:,indices].sum(axis=1), quantiles=quantiles) # Axis 1 is populations
        if data is not None: self.main['numdiag'].datatot = processdata(data['optnumdiag'])
        

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
        


    def make_graph_selectors(self, which = None):
        ''' WARNING -- this was added by StarterSquad and probably shouldn't be here '''
        ## Define options for graph selection
        self.graph_selectors = {'keys':[], 'names':[], 'checks':[]}
        checkboxes = self.graph_selectors['keys'] # e.g. 'prev-tot'
        checkboxnames = self.graph_selectors['names'] # e.g. 'HIV prevalence (%) -- total'
        defaultchecks = self.graph_selectors['checks']
        epikeys = self.main.keys()
        epinames = [thing.name for thing in self.main.values()]
        episubkeys = ['tot', 'pops'] # Would be best not to hard-code this...
        episubnames = ['total', 'by population']

        if which is None:  # assume there is at least one epikey )
            which = ["{}-{}".format(epikeys[0], subkey) for subkey in episubkeys]

        for key in epikeys: # e.g. 'prev'
            for subkey in episubkeys: # e.g. 'tot'
                boxkey = "{}-{}".format(key, subkey)
                checkboxes.append(boxkey)
                defaultchecks.append(boxkey in which)
        for name in epinames: # e.g. 'HIV prevalence'
            for subname in episubnames: # e.g. 'total'
                checkboxnames.append(name+' -- '+subname)

        return self.graph_selectors




class Multiresultset(Resultset):
    ''' Structure for holding multiple kinds of results, e.g. from an optimization, or scenarios '''
    def __init__(self, resultsetlist=None):
        # Basic info
        self.uid = uuid()
        self.created = today()
        self.nresultsets = len(resultsetlist)
        if type(resultsetlist)==list: pass # It's already a list, carry on
        if type(resultsetlist) in [odict, dict]: resultsetlist = resultsetlist.values() # Convert from odict to list
        if resultsetlist is None: raise Exception('To generate multi-results, you must feed in a list of result sets: none provided')
        else: raise Exception('Resultsetlist type "%s" not understood' % str(type(resultsetlist)))
        
        # Fundamental quantities -- populated by project.runsim()
        sameattrs = ['tvec', 'dt', 'popkeys']
        commonattrs = ['project', 'data', 'datayears']
        diffattrs = ['parset', 'raw', 'simpars']
        for attr in sameattrs+commonattrs: setattr(self, attr, None) # Shared attributes across all resultsets
        for attr in diffattrs: setattr(self, attr, odict()) # Store a copy for each resultset
        
        # Main results -- time series, by population -- get right structure, but clear out results -- WARNING, must match format above!
        self.main = dcp(resultsetlist[0].main) # For storing main results -- get the format from the first entry, since should be the same for all
        for key in self.main.keys():
            for at in ['pops', 'tot']:
                setattr(self.main[key], at, odict()) # Turn all of these into an odict -- e.g. self.main['prev'].pops = odict()

        for i,rset in enumerate(resultsetlist):
            key = rset.name if rset.name is not None else str(i)
            
            # First, loop over shared attributes, and ensure they match
            for attr in sameattrs+commonattrs:
                orig = getattr(self, attr)
                new = getattr(rset, attr)
                if orig is None: setattr(self, attr, new)
                elif orig!=new and attr in sameattrs: # It's only an issue if they must be the same: for something like a project, OK if they differ
                    errormsg = 'In generating multi-results, all results must have same attribute "%s": key "%s" differs' % (attr, key)
                    raise Exception(errormsg)
            
            # Loop over different attributes and append to the odict
            for attr in diffattrs:
                getattr(self, attr)[key] = getattr(rset, attr) # Super confusing, but boils down to e.g. self.raw['foo'] = rset.raw -- WARNING, does this even work?
            
            # Now, the real deal: fix self.main
            for key2 in self.main.keys():
                for at in ['pops', 'tot']:
                    getattr(self.main[key2], at)[key2] = getattr(rset.main[key2], at)[0] # Add data: e.g. self.main['prev'].pops['foo'] = rset.main['prev'].pops[0] -- WARNING, the 0 discards uncertainty data
            
                
            
        
        
        
    def __repr__(self):
        ''' Print out useful information when called '''
        output = defaultrepr(self)
        return output