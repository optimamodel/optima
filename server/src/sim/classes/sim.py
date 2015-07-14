# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 23:27:38 2015

@author: David Kedziora
"""

import weakref
import uuid
import defaults
from copy import deepcopy

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
        self.plotdataopt = None # TEMP DEBUG, DON'T COMMIT
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
        self.initialised = simdict['initialised']
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
        simdict['initialised']  = self.initialised
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
    
    def isinitialised(self):
        return self.initialised   
    
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
        
        # Make sure region D['P'] and generated D['P'] are equal.
        from extra_utils import dict_equal
        test = r.D['P']
        print [dict_equal(test[x1],self.parsdata[x2]) for (x1,x2) in zip(sorted(test.keys()), sorted(self.parsdata.keys()))]
        
        self.makemodelpars()
        
        # Hmm... should we just makefittedpars and calibrate later? Or calibrate here?
#        # Explicit construction of tempD, so that one day we know how to recode makefittedpars.
        
        if 'F' not in r.D.keys():
            import updatedata
            tempD = dict()
            tempD['opt'] = r.options
            tempD['G'] = r.metadata
            tempD['M'] = self.parsmodel
            tempD = updatedata.makefittedpars(tempD)
            self.parsfitted = tempD['F']
        else:
            self.parsfitted = r.D['F']      # Temporary solution. Remember, D should not be stored in region.
        
        self.initialised = True

    def makemodelpars(self):
        # SimParameter, SimBudget and SimCoverage differ in how they calculate D.M
        # but are otherwise almost identical. Thus this is the function that is
        # expected to be re-implemented in the derived classes
        from makemodelpars import makemodelpars
        r = self.getregion()

        self.parsmodel = makemodelpars(self.parsdata, r.options)
        
        # Make sure region D['M'] and generated D['M'] are equal.
        from extra_utils import dict_equal
        test = r.D['opt']
        print [dict_equal(test[x1],r.options[x2]) for (x1,x2) in zip(sorted(test.keys()), sorted(r.options.keys()))]
        
        # Make sure region D['M'] and generated D['M'] are equal.
        from extra_utils import dict_equal
        test = r.D['M']
        print [dict_equal(test[x1],self.parsmodel[x2]) for (x1,x2) in zip(sorted(test.keys()), sorted(self.parsmodel.keys()))]
        
        print

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


#------------------------------------------------------------------------------


# Derived Sim class that should store budget data.
class SimBudget(Sim):
    def __init__(self, name, region, budget = []):
        Sim.__init__(self, name, region)
        
        # This tag monitors if the simulation has been optimised (not whether it is the optimum).
        # Also different from standard processing.
        self.optimised = False        
        
        self.plotdataopt = None     # This used to be D['plot']['optim'][-1]. Be aware that it is not D['plot']!
        
        from timevarying import timevarying        
        
        if len(budget) == 0:    # If budget not provided, allocation is drawn from region data and budget is an extended array of allocation.
            self.alloc = deepcopy(self.getregion().data['origalloc'])
            self.budget = timevarying(self.alloc, ntimepm = 1, nprogs = len(self.alloc), tvec = self.getregion().options['partvec'])
        else:                   # If budget is provided, allocation is the first slice of this.
            self.budget = budget
            self.alloc = [alloclist[0] for alloclist in self.budget]
        
        self.obj = None                                             # The current objective function value for the origalloc budget.
            
        self.program_set = region.program_sets[0]   # Eventually modify to support multiple programs.


    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget'
        simdict['plotdataopt'] = self.plotdataopt
        simdict['alloc'] = self.alloc
        simdict['optimised'] = self.optimised
        simdict['objective'] = self.obj
        simdict['budget'] = self.budget
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.plotdataopt = simdict['plotdataopt']
        self.alloc = simdict['alloc']
        self.optimised = simdict['optimised']
        self.obj = simdict['objective']
        self.budget = simdict['budget']
        
    def isoptimised(self):
        return self.optimised
        
    def makemodelpars(self,randseed=0):
        Sim.makemodelpars(self)
        
#        r = self.getregion()
#        self.parsmodel = r.D['M']
        
        from makemodelpars import makemodelpars        
        
        r = self.getregion()
        
        tempD = dict()
        tempD['G'] = deepcopy(r.metadata)
        tempD['P'] = deepcopy(self.parsdata)
        tempD['data'] = deepcopy(r.data)
        tempD['opt'] = deepcopy(r.options)
        tempD['programs'] = deepcopy(r.metadata['programs'])
        
        from optimize import getcurrentbudget
        
        tempD, a, b = getcurrentbudget(tempD, alloc = self.budget, randseed = randseed)
        self.parsdata = tempD['P']
        P = self.parsdata
        
        tempparsmodel = makemodelpars(P, r.options, withwhat='c')
        
        from utils import findinds
        from numpy import arange
        
        # Hardcoded quick hack. Better to be linked to 'default objectives' function in optimize.
        obys = 2015 # "Year to begin optimization from"
        obye = 2030 # "Year to end optimization"
        initialindex = findinds(r.options['partvec'], obys)
        finalparindex = findinds(r.options['partvec'], obye) 
        parindices = arange(initialindex,finalparindex)
        
        # Hideous hack for ART to use linear unit cost
        try:
            from utils import sanitize
            artind = r.data['meta']['progs']['short'].index('ART')
            currcost = sanitize(r.data['costcov']['cost'][artind])[-1]
            currcov = sanitize(r.data['costcov']['cov'][artind])[-1]
            unitcost = currcost/currcov
            tempparsmodel['tx1'].flat[parindices] = self.alloc[artind]/unitcost
        except:
            print('Attempt to calculate ART coverage failed for an unknown reason')
        
        from optimize import partialupdateM        
        
        # Now update things
        self.parsmodel = partialupdateM(deepcopy(self.parsmodel), deepcopy(tempparsmodel), parindices)
        
        print        
        
#    def makemodelpars(self):
##        Sim.makemodelpars(self)        
#        
#        r = self.getregion()
#        npts = len(r.options['partvec']) # Number of time points
#
#        P = self.parsdata 
#        from numpy import nan, zeros
#        for param in P.keys():
#            if isinstance(P[param], dict) and 'p' in P[param].keys():
#                P[param]['c'] = nan+zeros((len(P[param]['p']), npts))
#
#        for prog, spending in zip(self.program_set['programs'], self.budget):
#            coverage = prog.get_coverage(spending) # Returns metamodality coverage
#            outcomes = prog.get_outcomes(coverage) # Returns program outcomes (for each effect)
#
#            for i in xrange(0,len(prog.effects['param'])): # For each of the effects
#                if prog.effects['iscoverageparam'][i]:
#                    P[prog.effects['param'][i]]['c'][:] = outcomes[i]
#                else:
#                    popnumber = r.get_popidx(prog.effects['popname'][i])-1 # Yes, get_popidx is 1-based rather than 0 based...cf. scenarios
#                    P[prog.effects['param'][i]]['c'][popnumber] = outcomes[i]
#
#        from makemodelpars import makemodelpars
#        
#        self.parsmodel = makemodelpars(P, r.options, withwhat='c')
##        tempparsmodel = makemodelpars(P, r.options, withwhat='c')
##        
##        from utils import findinds
##        from numpy import arange
##        
##        # Hardcoded quick hack. Better to be linked to 'default objectives' function in optimize.
##        obys = 2015 # "Year to begin optimization from"
##        obye = 2030 # "Year to end optimization"
##        initialindex = findinds(r.options['partvec'], obys)
##        finalparindex = findinds(r.options['partvec'], obye) 
##        parindices = arange(initialindex,finalparindex)
##        
##        # Hideous hack for ART to use linear unit cost
##        try:
##            from utils import sanitize
##            artind = r.data['meta']['progs']['short'].index('ART')
##            currcost = sanitize(r.data['costcov']['cost'][artind])[-1]
##            currcov = sanitize(r.data['costcov']['cov'][artind])[-1]
##            unitcost = currcost/currcov
##            tempparsmodel['tx1'].flat[parindices] = self.alloc[artind]/unitcost
##        except:
##            print('Attempt to calculate ART coverage failed for an unknown reason')
##        
##        from optimize import partialupdateM        
##        
##        # Now update things
##        self.parsmodel = partialupdateM(deepcopy(self.parsmodel), tempparsmodel, parindices)
    
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

        from timevarying import timevarying
        
        # The previous SimBudget's optimal allocation and objective become the initial values for this SimBudget.
        self.alloc = optalloc
        self.budget = timevarying(self.alloc, ntimepm = 1, nprogs = len(self.alloc), tvec = self.getregion().options['partvec'])
        self.obj = optobj
        
#        self.optalloc = None
#        self.optobj = None

    # Currently just optimises simulation according to defaults. As in... fixed initial budget!
    def optimise(self, makenew = True, inputmaxiters = defaults.maxiters, inputtimelimit = defaults.timelimit):
        r = self.getregion()

        from optimize import optimize
        
        tempD = dict()
        tempD['data'] = deepcopy(r.data)
        tempD['data']['origalloc'] = deepcopy(self.alloc)
        tempD['opt'] = deepcopy(r.options)
        tempD['programs'] = deepcopy(r.metadata['programs'])
        tempD['G'] = deepcopy(r.metadata)
        tempD['P'] = deepcopy(self.parsdata)
        tempD['M'] = deepcopy(self.parsmodel)
        tempD['F'] = deepcopy(self.parsfitted)
        tempD['R'] = deepcopy(self.debug['results'])      # Does this do anything?
        tempD['plot'] = dict()
        
        tempD['S'] = deepcopy(self.debug['structure'])     # Need to run simulation before optimisation!
        optimize(tempD, maxiters = inputmaxiters, timelimit = inputtimelimit, returnresult = True),        
        
        self.plotdataopt = tempD['plot']['optim'][-1]       # What's this -1 business about?
        
        # Let's try returning these rather than storing them...
#        optalloc = self.plotdataopt['alloc'][-1]['piedata']
#        optobj = tempD['objective'][-1]
#        resultopt = tempD['result']['debug']    # VERY temporary. Only until we understand how to regenerate parameters from new allocations.
#        newbudget = tempD['result']['debug']['newbudget']
#        print optalloc
#        print newbudget
        
        # If makenew is on, the optimisation results will be initialised in a new SimBudget.
        if makenew:
            self.optimised = True
        
#        # Optimisation returns an allocation and a (hopefully corresponding) objective function value.
#        # It also returns a resulting data structure (that we'll hopefully remove the need for eventually).
#        # Finally, it returns a boolean for whether a new SimBudget should be made.
#        return (optalloc, optobj, resultopt, makenew)
        
        # Maybe should avoid hardcoding the timevarying bit, but it works for default optimisation.
        from timevarying import timevarying          
        
        optalloc = tempD['optalloc']
        optbudget = timevarying(optalloc, ntimepm = 1, nprogs = len(optalloc), tvec = self.getregion().options['partvec'])        
        
        return (optbudget, makenew)
    
    # Calculates objective values for certain multiplications of an alloc's variable costs (passed in as list of factors).
    # The idea is to spline a cost-effectiveness curve across several budget totals.
    # Note: We don't care about the allocations in detail. This is just a function between totals and the objective.
    def calculateeffectivenesscurve(self, factors):
        curralloc = self.alloc
        
        totallocs = []
        objarr = []
        timelimit = defaults.timelimit
#        timelimit = 1.0
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        # These will be ignored when testing different allocations.
        fixedtrue = [1.0]*(len(curralloc))
        for i in xrange(len(curralloc)):
            if len(self.getregion().metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
        
        for factor in factors:
            try:
                print('Testing budget allocation multiplier of %f.' % factor)
                self.alloc = [curralloc[i]*(factor+(1-factor)*fixedtrue[i]) for i in xrange(len(curralloc))]
                betteralloc, currobj, b, c = self.optimise(makenew = False, inputtimelimit = timelimit)
                
                objarr.append(currobj)
                totallocs.append(sum(betteralloc))
            except:
                print('Multiplying pertinent budget allocation values by %f failed.' % factor)
            
        self.alloc = curralloc
        
        # Remember that total alloc includes fixed costs (e.g admin)!
        return (totallocs, objarr)
    
    # Scales the variable costs of an alloc so that the sum of the alloc equals newtotal.
    # Note: Can this be fused with the scaling on the Region level...?
    def scalealloctototal(self, newtotal):
        curralloc = self.alloc
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        # These will be ignored when testing different allocations.
        fixedtrue = [1.0]*(len(curralloc))
        for i in xrange(len(curralloc)):
            if len(self.getregion().metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
                
        # Extract the fixed costs from scaling.
        fixedtotal = sum([curralloc[i]*fixedtrue[i] for i in xrange(len(curralloc))])
        vartotal = sum([curralloc[i]*(1.0-fixedtrue[i]) for i in xrange(len(curralloc))])
        scaledtotal = newtotal - fixedtotal
        
        # Deal with a couple of possible errors.
        if scaledtotal < 0:
            print('Warning: You are attempting to generate an allocation for a budget total that is smaller than the sum of relevant fixed costs!')
            print('Continuing with the assumption that all non-fixed program allocations are zero.')
            print('This may invalidate certain analyses such as GPA.')
            scaledtotal = 0
        try:
            factor = scaledtotal/vartotal
        except:
            print("Possible 'divide by zero' error.")
            curralloc[0] = scaledtotal      # Shove all the budget into the first program.
        
        # Updates the alloc of this SimBudget according to the scaled values.
        self.alloc = [curralloc[i]*(factor+(1-factor)*fixedtrue[i]) for i in xrange(len(curralloc))]

    def __repr__(self):
        return "SimBudget %s ('%s')" % (self.uuid,self.name)   
   
   
#------------------------------------------------------------------------------


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