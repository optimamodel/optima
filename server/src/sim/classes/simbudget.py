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
        
    # SimBudget actually needs to run once as a standard Sim so as to generate a default D.S structure (for getcurrentbudget purposes).
    def initialise(self):
        Sim.initialise(self, forcebasicmodel = True)
        Sim.run(self)
        
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
    
    
    # Work out the objective value of this SimBudget and its allocation.
    # WARNING: Hard-coded. Derived from default option of legacy optimize function.
    def calculateobjectivevalue(self):
        if not self.isprocessed():
            print('Need to simulate and produce results to calculate objective value.')
            self.run()
        
        r = self.getregion()
        
        # Objectives are currently hard coded and mimic defaultobjectives in optimize.py. Needs to change.
        objectives = dict()
        objectives['year'] = dict()
        objectives['year']['start'] = 2015              # "Year to begin optimization from".
        objectives['year']['end'] = 2030                # "Year to end optimization".
        objectives['year']['until'] = 2030              # "Year to project outcomes to".
        objectives['outcome'] = dict()
        objectives['outcome']['inci'] = True            # "Minimize cumulative HIV incidence"
        objectives['outcome']['inciweight'] = 100       # "Incidence weighting"
        objectives['outcome']['daly'] = False           # "Minimize cumulative DALYs"
        objectives['outcome']['dalyweight'] = 100       # "DALY weighting"
        objectives['outcome']['death'] = False          # "Minimize cumulative AIDS-related deaths"
        objectives['outcome']['deathweight'] = 100      # "Death weighting"
        objectives['outcome']['costann'] = False        # "Minimize cumulative DALYs"
        objectives['outcome']['costannweight'] = 100    # "Cost weighting"        
        
        from utils import findinds
        from numpy import arange        
        
        initialindex = findinds(r.options['partvec'], objectives['year']['start'])
        finalparindex = findinds(r.options['partvec'], objectives['year']['end'])
        finaloutindex = findinds(r.options['partvec'], objectives['year']['until'])
        parindices = arange(initialindex,finalparindex)
        outindices = arange(initialindex,finaloutindex)        
        
        # Unnecessary with defaults, but normalise and weight objectives if there are multiple options.
        weights = dict()
        normalizations = dict()
        outcomekeys = ['inci', 'death', 'daly', 'costann']
        if sum([objectives['outcome'][key] for key in outcomekeys])>1:      # Only normalize if multiple objectives, since otherwise doesn't make a lot of sense.
            for key in outcomekeys:
                thisweight = objectives['outcome'][key+'weight'] * objectives['outcome'][key] / 100.
                weights.update({key:thisweight})    # Get weight, and multiply by "True" or "False" and normalize from percentage.
                if key!='costann': thisnormalization = self.debug['results'][key]['tot'][0][outindices].sum()
                else: thisnormalization = self.debug['results'][key]['total']['total'][0][outindices].sum()     # Special case for costann.
                normalizations.update({key:thisnormalization})
        else:
            for key in outcomekeys:
                weights.update({key:int(objectives['outcome'][key])}) # Weight of 1
                normalizations.update({key:1}) # Normalizatoin of 1        
                
        ## Define options structure
        options = dict()
        options['outcomekeys'] = outcomekeys
        options['weights'] = weights # Weights for each parameter
        options['outindices'] = outindices # Indices for the outcome to be evaluated over
        options['parindices'] = parindices # Indices for the parameters to be updated on
        options['normalizations'] = normalizations # Whether to normalize a parameter
        options['randseed'] = 0  
        
        outcome = 0 # Preallocate objective value 
        for key in options['outcomekeys']:
            if options['weights'][key]>0: # Don't bother unless it's actually used
                if key!='costann': thisoutcome = self.debug['results'][key]['tot'][0][options['outindices']].sum()
                else: thisoutcome = self.debug['results'][key]['total']['total'][0][options['outindices']].sum() # Special case for costann
                outcome += thisoutcome * options['weights'][key] / float(options['normalizations'][key]) * r.options['dt'] # Calculate objective
        
        return outcome

    def __repr__(self):
        return "SimBudget %s ('%s')" % (self.uuid,self.name) 