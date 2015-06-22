# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 23:27:38 2015

@author: David Kedziora
"""

import weakref
import uuid
import defaults

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
        #self.plotdataopt  = simdict['plotdataopt']      # Note: A method of a base class should not refer to derived class members. Overload instead.
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
        #simdict['plotdataopt']  = self.plotdataopt      # Note: A method of a base class should not refer to derived class members. Overload instead.
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
            raise Exception('The parent region has been garbage-collected and the reference is no longer valid.')
        else:
            return r

    def setname(self, name):
        self.name = name
        
    def getname(self):
        return self.name
        
    def isprocessed(self):
        return self.processed
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
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
        
        # Hmm... should we just makefittedpars and calibrate later? Or calibrate here?
#        # Explicit construction of tempD, so that one day we know how to recode makefittedpars.
#        tempD = dict()
#        tempD['opt'] = r.options
#        tempD['G'] = r.metadata
#        tempD['M'] = self.parsmodel
        
#        tempD = makefittedpars(tempD)
        self.parsfitted = r.D['F']      # Temporary solution. Remember, D should not be stored in region.
        
        self.initialised = True

    def makemodelpars(self):
        # SimParameter, SimBudget and SimCoverage differ in how they calculate D.M
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
        
        # Note: Work out what we're looping through. There may be a more sensible alternative...?
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
        
        # Explicit construction of tempD, so that one day we know how to recode gatheruncerdata.
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
        
        # I hope SimBudget always has a region attached...         
        self.alloc = self.getregion().data['origalloc']     # The budget allocations before optimisation.
        self.obj = None                                     # The current objective function value for the origalloc budget.
        
#        self.optalloc = None        # The resulting budget allocations after optimisation.
#        self.optobj = None          # The resulting objective function value for the optalloc budget.


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
    def specialoptload(self, sim, optalloc, optobj, resultopt):
        self.setregion(sim.getregion())     # Did optimisation change D['G']? Is it important? If so, this could be dangerous!        
        
#        from copy import deepcopy
#        sim = deepcopy(insim)        
        
        self.setname((sim.name[:-8] if sim.name.endswith('-initial') else sim.name)+'-opt')
        self.processed = False
        self.initialised = True    # This special loading is considered initialisation.

        self.parsdata = sim.parsdata
        self.parsmodel = resultopt['M']         # New D['M'].
        self.parsfitted = resultopt['F']        # New D['F'].
        
        # Will need to run to get these.
        self.debug = {}
        self.debug['results'] = None
        self.debug['structure'] = None
        
        self.plotdata = None
        
        self.plotdataopt = None
        
        # The previous SimBudget's optimal allocation and objective become the initial values for this SimBudget.
        self.alloc = optalloc
        self.obj = optobj
        
#        self.optalloc = None
#        self.optobj = None

    # Currently just optimises simulation according to defaults. As in... fixed budget!
    def optimise(self, makenew = True):
        r = self.getregion()

        from optimize import optimize
        
        tempD = dict()
        tempD['data'] = r.data
        tempD['data']['origalloc'] = self.alloc
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
        optimize(tempD, maxiters=defaults.maxiters, timelimit=defaults.timelimit, returnresult = True),        
        
        self.plotdataopt = tempD['plot']['optim'][-1]       # What's this -1 business about?
        
#        # Saves optimisation results to this Sim. New 'G', 'M', 'F', 'S'.
#        # self.debug['results'] = tempD['result']       # Maybe store just the results of a normal run in self.debug.
#        self.resultopt = tempD['result']['debug']       # Optimisation results are kept separate from debug['results'].
#        self.optobj = tempD['objective'][-1]            # This assumes that the last objective value in an optimisation cycle is best. Is that safe...?
#        
#        # The new optimised allocations will be derived from the pie chart plotting data.
#        # Let's hope it's always there...
#        self.optalloc = self.plotdataopt['alloc'][-1]['piedata']
        
        # Let's try returning these rather than storing them...
        optalloc = self.plotdataopt['alloc'][-1]['piedata']
        optobj = tempD['objective'][-1]
        resultopt = tempD['result']['debug']    # VERY temporary. Only until we understand how to regenerate parameters from new allocations.
        
        # If makenew is on, the optimisation results will be initialised in a new SimBudget.
        if makenew:
            self.optimised = True
        
        # Optimisation returns an allocation, (hopefully corresponding) objective function value and whether a new SimBudget should be made.
        return (optalloc, optobj, resultopt, makenew)
    
    # Calculates objective values for certain multiplications of a total budget.
    # The idea is to spline a cost-effectiveness curve for varying budget totals.
    def calculateeffectivenesscurve(self):
        curralloc = self.alloc
        totalloc = sum(curralloc)
        
        factors = [0.1, 0.2, 0.5, 1, 2, 5]
        objarr = []
        
        for factor in factors:
            self.alloc = [x*factor for x in curralloc]
            a, currobj, b, c = self.optimise(makenew = False)
            objarr.append(currobj)            
            
        self.alloc = curralloc
        
        # factors,objarr = ([0.1, 0.2, 0.5, 1, 2, 5],[7420.5665291930309,6895.5487199112631,3774.2076700271682,3708.4290662398462,3618.188538137224,3503.5918712593821])
            
        return ([x*totalloc for x in factors], objarr)

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
    def __init__(self, name, region,budget):
        # budget and alloc are the same thing i.e. an 'alloc' *is* actually a budget
        Sim.__init__(self, name, region)
        self.budget = budget # This contains spending values for all of the modalities for the simulation timepoints i.e. there are len(D['opt']['partvec']) spending values
        self.program_set = region.program_sets[0] # Eventually modify to support multiple programs

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
        npts = len(r.options['partvec']) # Number of time points

        P = self.parsdata 
        from numpy import nan, zeros
        for param in P.keys():
            if isinstance(P[param], dict) and 'p' in P[param].keys():
                P[param]['c'] = nan+zeros((len(P[param]['p']), npts))

        for prog, spending in zip(self.program_set['programs'], self.budget):
            coverage = prog.get_coverage(spending) # Returns metamodality coverage
            outcomes = prog.get_outcomes(coverage) # Returns program outcomes (for each effect)

            print '--- SIM'
            print 'Coverage: ', coverage[0][0][0]
            print 'Outcome: ', [x[0][0] for x in outcomes]
            for i in xrange(0,len(prog.effects['param'])): # For each of the effects
                if prog.effects['iscoverageparam'][i]:
                    P[prog.effects['param'][i]]['c'][:] = outcomes[i]
                else:
                    popnumber = r.get_popidx(prog.effects['popname'][i])-1 # Yes, get_popidx is 1-based rather than 0 based...cf. scenarios
                    P[prog.effects['param'][i]]['c'][popnumber] = outcomes[i]

        from makemodelpars import makemodelpars
        self.parsmodel = makemodelpars(P, r.options, withwhat='c')

    def __repr__(self):
        return "SimBudget2 %s ('%s')" % (self.uuid,self.name)    