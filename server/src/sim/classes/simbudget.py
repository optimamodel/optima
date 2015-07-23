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
        
        

    def __repr__(self):
        return "SimBudget %s ('%s')" % (self.uuid,self.name) 