"""
This module defines the classes for stores the results of a single simulation run.

Version: 2015dec25 by cliffk -- merry christmas!
"""

from optima import uuid, today, getdate, quantile, printv, odict, objectid, objectatt, objectmeth, dcp
from numpy import array, nan, zeros, arange


def getresults(project=None, pointer=None):
    '''
    A tiny function for returning the results associated with something. 'pointer' can eiher be a UID,
    a string representation of the UID, the actual pointer to the results, or a function to return the
    results.
    
    Example:
        results = P.parsets[0].results()
        calls
        getresults(P, P.parsets[0].resultsref)
        which returns
        P.results[P.parsets[0].resultsref]
    
    Version: 2016jan11
    '''
    if type(pointer)==str: return project.results[pointer]
    elif type(pointer)==type(uuid()): return project.results[str(pointer)]
    elif type(pointer)==Resultset: return pointer
    else:
        try: 
            return pointer() # Try calling as function
        except:
            errormsg = 'Could not understand results pointer "%s" for project "%s"' % (pointer, project.name)
            raise Exception(errormsg)



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
        output = objectid(self)
        output += '============================================================\n'
        output += objectatt(self)
        output += '============================================================\n'
        return output



class Resultset(object):
    ''' Lightweight structure to hold results -- use this instead of a dict '''
    def __init__(self, raw=None, simpars=None, project=None, data=None, parset=None, domake=True):
        # Basic info
        self.uid = uuid()
        self.created = today()
        
        # Turn inputs into lists if not already
        if raw is None: raise Exception('To generate results, you must feed in model output: none provided')
        if type(simpars)!=list: simpars = [simpars] # Force into being a list
        if type(raw)!=list: raw = [raw] # Force into being a list
        
        # Fundamental quantities -- populated by project.runsim()
        self.raw = raw
        self.simpars = simpars # ...and sim parameters
        self.tvec = raw[0]['tvec']
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
        output = objectid(self)
        output += '============================================================\n'
        output += '      Project name: %s\n'    % (self.project.name if self.project is not None else None)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objectatt(self)
        output += '============================================================\n'
        output += objectmeth(self)
        output += '============================================================\n'
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
        ## Define options for graph selection
        truebydefault = 2
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
