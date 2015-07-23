# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 21:26:39 2015

@author: David Kedziora
"""

from sim import Sim

import defaults
from copy import deepcopy

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
        calibration = self.getcalibration()

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
        
        # Here, we just need a hack to get SimBudget to work
        # SimBudget2 will do it all properly
        # So as a hack, overwrite P with the values in the calibration which is what is supposed
        # to be referenced directly (c.f., Sim.makemodelpars())
        # No need for deepcopy here, because we are working with the tempD parsdata
        P['pships'] = calibration['pships']
        P['hivprev'] = calibration['hivprev']
        P['popsize'] = calibration['popsize']
        P['transit'] = calibration['transit']
        P['const'] = calibration['const']

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
        optobj = tempD['objective'][-1]
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
        
        return (optbudget, optobj, makenew)
    
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
                betterbudget, betterobj, a = self.optimise(makenew = False, inputtimelimit = timelimit)
                
                betteralloc = [alloclist[0] for alloclist in betterbudget]
                
                objarr.append(betterobj)
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