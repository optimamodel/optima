# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 23:27:38 2015

@author: David Kedziora
"""

import weakref
import uuid

class Sim:
    def __init__(self, name, region):
        self.name = name
        self.initialised = False    # This tag monitors if the simulation has been initialised.        
        self.processed = False      # This tag monitors if the simulation has been run.
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality

        self.parsdata = None        # This used to be D['P'].
        self.parsmodel = None       # This used to be D['M'].
        self.parsfitted = None      # This used to be D['F'].
        
        self.debug = {}             # This stores the (large) output from running the simulation
        self.debug['results'] = None         # This used to be D['R'].
        self.debug['structure'] = None       # This used to be D['S'].
        
        self.plotdata = None        # This used to be D['plot']['E']. Be aware that it is not D['plot']!        
    
        self.setregion(region)

    @classmethod
    def fromdict(Sim,simdict,region):
        # This function instantiates the correct subtype based on simdict['type']
        assert(simdict['region_uuid'] == region.uuid)
        print simdict['type']
        if simdict['type'] == 'Sim':
            s = Sim(simdict['name'],region)
        if simdict['type'] == 'SimParameter':
            s = SimParameter(simdict['name'],region)
        if simdict['type'] == 'SimBudget':
            s = SimBudget(simdict['name'],region)
        s.setregion(region)
        s.load_dict(simdict)
        return s

    def load_dict(self,simdict):
        self.processed  = simdict['processed']  
        self.parsdata  = simdict['parsdata']  
        self.parsmodel  = simdict['parsmodel']  
        self.parsfitted  = simdict['parsfitted']  
        self.debug  = simdict['debug']   
        self.plotdata  = simdict['plotdata']  
        self.plotdataopt  = simdict['plotdataopt']  
        self.uuid = simdict['uuid']

    def todict(self):
        simdict = {}
        simdict['type'] = 'Sim'
        simdict['name'] = self.name
        simdict['processed']  = self.processed 
        simdict['parsdata']  = self.parsdata 
        simdict['parsmodel']  = self.parsmodel 
        simdict['parsfitted']  = self.parsfitted 
        simdict['debug']   = self.debug 
        simdict['plotdata']  = self.plotdata 
        simdict['plotdataopt']  = self.plotdataopt 
        simdict['region_uuid'] = self.getregion().uuid
        simdict['uuid'] = self.uuid
        return simdict
    
    def setregion(self,region):
        self.region = weakref.ref(region)

    def getregion(self):
        # self.region is a weakref object, which means to get
        # the region you need to do self.region() rather than
        # self.region. This function abstracts away this 
        # implementation detail in case it changes in future
        r = self.region()
        if r is None:
            raise Exception('The parent region has been garbage-collected and the reference is no longer valid')
        else:
            return r

    def setname(self, name):
        self.name = name
        
    def getname(self):
        return self.name
        
    def isprocessed(self):
        return self.processed
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
    # Region defaults can be overwritten by passing in parameters, e.g. in the case of creating a new optimised Sim Budget.
    def initialise(self):
        r = self.getregion()

        from makedatapars import makedatapars
        from numpy import arange

        # Explicit construction of tempD, so that one day we know how to recode makedatapars.
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        tempD['G']['datayears'] = arange(r.metadata['datastart'], r.metadata['dataend']+1)
        tempD['G']['npops'] = len(r.metadata['populations'])
        tempD['G']['nprogs'] = len(r.metadata['programs'])

        tempD = makedatapars(tempD)
        self.parsdata = tempD['P']
        
        self.makemodelpars()
        
        # from updatedata import makefittedpars
        
        # Explicit construction of tempD, so that one day we know how to recode makefittedpars.
        tempD = dict()
        tempD['opt'] = r.options
        tempD['G'] = r.metadata
        tempD['M'] = self.parsmodel
        
        #tempD = makefittedpars(tempD)
        # CALIBRATION SHOULD GO HERE. MAYBE.
        self.parsfitted = r.D['F']      # Temporary solution. Remember, D should not be stored in region.
        
        self.initialised = True

    def makemodelpars(self):
        # SimParameter, SimBudget and SimCoverge differ in how they calculate D.M
        # but are otherwise almost identical. Thus this is the function that is
        # expected to be re-implemented in the derived classes
        from makemodelpars import makemodelpars
        r = self.getregion()

        self.parsmodel = makemodelpars(self.parsdata, r.options)

    # Runs model given all the initialised parameters.
    def run(self):
        if not self.initialised:
            self.initialise()

        r = self.getregion()

        from model import model

        allsims = []
        for s in range(len(self.parsfitted)):   # Parallelise eventually.
            S = model(r.metadata, self.parsmodel, self.parsfitted[s], r.options)
            allsims.append(S)
        self.debug['structure'] = allsims[0]     # Save one full sim structure for troubleshooting and... funsies?
    
        # Calculate results.
        from makeresults import makeresults
        
        # Explicit construction of tempD, so that one day we know how to recode makeresults.
        tempD = dict()
        tempD['G'] = r.metadata
        tempD['P'] = self.parsdata
        tempD['S'] = self.debug['structure']
        
        # Input that only the financialanalysis subfunction in makeresults wants.
        # It would be a good idea to somehow separate the two...
        tempD['data'] = r.data
        tempD['opt'] = r.options
        tempD['programs'] = r.metadata['programs']
        
        self.debug['results'] = makeresults(tempD, allsims, r.options['quantiles'])
    
        # Gather plot data.
        from gatherplotdata import gatheruncerdata
        
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        
        self.plotdata = gatheruncerdata(tempD, self.debug['results'])
        
        self.processed = True        
        
    def plotresults(self):
        
        from viewresults import viewuncerresults
        
        viewuncerresults(self.plotdata, show_wait = True)

    def __repr__(self):
        return "Sim %s ('%s')" % (self.uuid,self.name)

# Derived Sim class that should store budget data.
class SimBudget(Sim):
    def __init__(self, name, region):
        Sim.__init__(self, name, region)
        
        # This tag monitors if the simulation has been optimised (not whether it is the optimum).
        # Also different from standard processing.
        self.optimised = False        
        
        self.plotdataopt = None     # This used to be D['plot']['optim'][-1]. Be aware that it is not D['plot']!
        self.resultopt = None       # The resulting data structures after optimisation.
        
        # I hope SimBudget always has a region attached...         
        self.origalloc = self.getregion().data['origalloc']     # The budget allocations before optimisation.
        self.origobj = None                                     # The current objective function value for the origalloc budget.
        
        self.optalloc = None        # The resulting budget allocations after optimisation.
        self.optobj = None          # The resulting objective function value for the optalloc budget.


    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget'
        simdict['plotdataopt'] = self.plotdataopt
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.plotdataopt = simdict['plotdataopt']
        
    def isoptimised(self):
        return self.optimised
    
    # Essentially copies old SimBudget into new SimBudget, except overwriting where applicable with sim.resultopt.
    # This will need to be monitored carefully! Every additional data structure in Sim+SimBudget must be written here.
    def specialoptload(self, sim):
        self.setregion(sim.getregion())     # Did optimisation change D['G']? Is it important? If so, this could be dangerous!        
        
#        from copy import deepcopy
#        sim = deepcopy(insim)        
        
        self.setname((sim.name[:-8] if sim.name.endswith('-initial') else sim.name)+'-opt')
        self.processed = False
        self.initialised = True    # This special loading is considered initialisation.

        self.parsdata = sim.parsdata
        self.parsmodel = sim.resultopt['M']         # New D['M'].
        self.parsfitted = sim.resultopt['F']        # New D['F'].
        
        # Will need to run to get these.
        self.debug = {}
        self.debug['results'] = None
        self.debug['structure'] = None
        
        self.plotdata = None
        
        self.plotdataopt = None
        self.resultopt = None
        
        # The previous SimBudget's optimal allocation and objective become the initial values for this SimBudget.
        self.origalloc = sim.optalloc
        self.origobj = sim.optobj
        
        self.optalloc = None
        self.optobj = None

    # Currently just optimises simulation according to defaults. As in... fixed budget!
    def optimise(self, test = False):
        r = self.getregion()

        from optimize import optimize
        
        tempD = dict()
        tempD['data'] = r.data
        tempD['data']['origalloc'] = self.origalloc
        tempD['opt'] = r.options
        tempD['programs'] = r.metadata['programs']
        tempD['G'] = r.metadata
        tempD['P'] = self.parsdata
        tempD['M'] = self.parsmodel
        tempD['F'] = self.parsfitted
        tempD['R'] = self.debug['results']      # Does this do anything?
        tempD['plot'] = dict()
        
        tempD['S'] = self.debug['structure']     # Need to run simulation before optimisation!
        #optimize(tempD, maxiters = 3, returnresult = True)   # Temporary restriction on iterations. Not meant to be hardcoded!
        optimize(tempD, maxiters=1e3, timelimit=5, returnresult = True),        
        
        self.plotdataopt = tempD['plot']['optim'][-1]       # What's this -1 business about?
        
        # Saves optimisation results to this Sim. New 'G', 'M', 'F', 'S'.
        # self.debug['results'] = tempD['result']       # Maybe store just the results of a normal run in self.debug.
        self.resultopt = tempD['result']['debug']       # Optimisation results are kept separate from debug['results'].
        self.optobj = tempD['objective'][-1]            # This assumes that the last objective value in an optimisation cycle is best. Is that safe...?
        
        # The new optimised allocations will be derived from the pie chart plotting data.
        # Let's hope it's always there...
        self.optalloc = self.plotdataopt['alloc'][-1]['piedata']
        
        # If test is on, the optimisation results will be stored, but SimBudget can be re-optimised.
        if not test:
            self.optimised = True
    
    # Calculates the objective function value for (1-factor)*alloc and (1+factor)*alloc. Make sure factor<1.
    # Converts into discretised derivatives for alloc- and alloc+. (Note that both VALUES should be the same sign, i.e. -ve for DALYs.)
    # Involves three optimisations. Useful for GPA, where rates need to be compared between regions.
    def calculateobjectivegradients(self,factor):
        curralloc = self.origalloc
        
        self.optimise(test = True)
        currobj = self.optobj
        
        self.origalloc = [x*(1-factor) for x in curralloc]
        self.optimise(test = True)
        gradneg = (currobj - self.optobj)/factor
        
        self.origalloc = [x*(1+factor) for x in curralloc]
        self.optimise(test = True)
        gradpos = (self.optobj - currobj)/factor
        
        return (gradneg, gradpos)

    def __repr__(self):
        return "SimBudget %s ('%s')" % (self.uuid,self.name)   

# Derived Sim class that should store parameter overwrites.
class SimParameter(Sim):
    def __init__(self, name, region):
        Sim.__init__(self, name, region)
        self.parameter_overrides = []

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimParameter'
        simdict['parameter_overrides'] = self.parameter_overrides
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.parameter_overrides = simdict['parameter_overrides'] 

    def create_override(self,parname,pop,startyear,endyear,startval,endval):
        # Create override for a single parameter, preserving the current dictionary representation of scenarios
        # pop can be a population index, or a population shortname. 'all' is a valid shortname
        #
        # Also need to validate the parameter name
        if type(pop) is str:
            r = self.getregion()
            poplist = [x['short_name'] for x in r.metadata['populations']] + ['all']
            try:
                popidx = poplist.index(pop) + 1 # For some reason (frontend?) these indexes are 1-based rather than 0-based
            except:
                print 'Population not found! Valid populations are:'
                print poplist
                raise Exception('InvalidPopulation')
        else:
            popidx = pop

        assert(type(parname) is list)

        override = {}
        override['names'] = parname # This can be a list e.g. [u'condom', u'com']??
        override['pops'] = popidx
        override['startval'] = startval
        override['startyear'] = startyear
        override['endval'] = endval
        override['endyear'] = endyear
        self.parameter_overrides.append(override)

    def makemodelpars(self):
        from numpy import linspace, ndim
        from nested import getnested, setnested
        from utils import findinds

        # First, get the base model parameters
        Sim.makemodelpars(self) 

        # Now compute the overrides as per scenarios.py -> makescenarios()
        r = self.getregion()
        for thesepars in self.parameter_overrides:
            data = getnested(self.parsmodel, thesepars['names'])
            if ndim(data)>1:
                if thesepars['pops'] < len(data):
                    newdata = data[thesepars['pops']] # If it's more than one dimension, use population data too
                else:
                    newdata = data[:] # Get all populations
            else:
                newdata = data # If it's not, just use the whole thing
            
            # Get current values
            initialindex = findinds(r.options['partvec'], thesepars['startyear'])
            finalindex = findinds(r.options['partvec'], thesepars['endyear'])
            
            if thesepars['startval'] == -1:
                if ndim(newdata)==1: 
                    initialvalue = newdata[initialindex]
                else: 
                    initialvalue = newdata[:,initialindex].mean(axis=0) # Get the mean if multiple populations
            else:
                initialvalue = thesepars['startval']
            
            if thesepars['endval'] == -1:
                if ndim(newdata)==1: 
                    finalvalue = newdata[finalindex]
                else: 
                    finalvalue = newdata[:,finalindex].mean() # Get the mean if multiple populations
            else:
                finalvalue = thesepars['endval'] 
            
            # Set new values
            npts = finalindex-initialindex
            newvalues = linspace(initialvalue, finalvalue, npts)
            if ndim(newdata)==1:
                newdata[initialindex:finalindex] = newvalues
                newdata[finalindex:] = newvalues[-1] # Fill in the rest of the array with the last value
                if ndim(data)==1:
                    data = newdata
                else:
                    data[thesepars['pops']] = newdata
            else:
                for p in xrange(len(newdata)):
                    newdata[p,initialindex:finalindex] = newvalues
                    newdata[p,finalindex:] = newvalues[-1] # Fill in the rest of the array with the last value
            
            # Update data
            if ndim(data)>1 and ndim(newdata)==1:
                data[thesepars['pops']] = newdata # Data is multiple populations, but we're only resetting one
            else:
                data = newdata # In all other cases, reset the whole thing (if both are 1D, or if both are 2D

            setnested(self.parsmodel, thesepars['names'], data)

    def __repr__(self):
        return "SimParameter %s ('%s')" % (self.uuid,self.name)    

# Derived Sim class that should store parameter overwrites.
class SimBudget2(Sim):
    def __init__(self, name, region):
        Sim.__init__(self, name, region)
        self.budget = region.data['current_budget'] # After running sanitize(), this is alloc 

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget2'
        simdict['budget'] = self.budget
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.budget = simdict['budget'] 

    def makemodelpars(self):
        r = self.getregion()
        from copy import deepcopy
        tempD = deepcopy(r.D)
        import getcurrentbudget
        # alloc (i.e. budget) goes in here
        tempD = getcurrentbudget.getcurrentbudget(D)

        import makemodelpars
        self.parsmodel = makemodelpars.makemodelpars(tempD['P'],r.options,withwhat='c')

    def __repr__(self):
        return "SimBudget2 %s ('%s')" % (self.uuid,self.name)    