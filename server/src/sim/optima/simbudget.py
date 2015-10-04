from sim import Sim

import defaults
from liboptima.utils import findinds
from numpy import arange 
from copy import deepcopy

# Derived Sim class that should store budget data.
class SimBudget(Sim):
    def __init__(self, name, project, budget = []):
        Sim.__init__(self, name, project)
        
        # This tag monitors if the simulation has been optimised (not whether it is the optimum).
        # Also different from standard processing.
        self.optimised = False        
        
        self.plotdataopt = None     # This used to be D['plot']['optim'][-1]. Be aware that it is not D['plot']!
        
        from timevarying import timevarying        
        
        if len(budget) == 0:    # If budget not provided, allocation is drawn from project data and budget is an extended array of allocation.
            self.alloc = deepcopy(self.getproject().data['origalloc'])
            self.budget = timevarying(self.alloc, ntimepm = 1, nprogs = len(self.alloc), tvec = self.getproject().options['partvec'])
        else:                   # If budget is provided, allocation is the first slice of this.
            self.budget = budget
            self.alloc = [alloclist[0] for alloclist in self.budget]
        
        self.obj = None                                             # The current objective function value for the origalloc budget.

        self.normalisations = dict()
        

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
        Sim.run(self)   # The first run produces the Sim structure required to produce a SimBudget model.
        
        Sim.initialise(self, forcebasicmodel = False)
        Sim.run(self)   # The second run produces the actual SimBudget model required for optimisation.
        
        # Normalisations for multiple objective aims are calculated from the unoptimised SimBudget's epidemiological results.
        # As they are not updated later, it is wise only to use the original unoptimised SimBudget as an outcome-calculating 'normaliser'.
        self.normalisations = self.calculatenormalisations(['inci', 'death', 'daly', 'costann'])    
    
    # Warning: Be careful about running this and then processing the simulation multiple times.
    # It is not clear if modified D.M and D.S structures will produce different D.M and D.S structures the next time around.
    def makemodelpars(self,randseed=0):
        Sim.makemodelpars(self)
        
#        r = self.getproject()
#        self.parsmodel = r.D['M']
        
        from makemodelpars import makemodelpars        
        
        r = self.getproject()
        calibration = self.getcalibration()

        tempD = dict()
        tempD['G'] = deepcopy(r.metadata)
        tempD['P'] = deepcopy(self.parsdata)
        tempD['M'] = deepcopy(self.parsmodel)
        tempD['S'] = deepcopy(self.debug['structure'])
        tempD['data'] = deepcopy(r.data)
        tempD['opt'] = deepcopy(r.options)
        tempD['programs'] = deepcopy(r.metadata['programs'])
        
        from optimize import getcurrentbudget
        
        tempD = getcurrentbudget(tempD, alloc = self.budget, randseed = randseed)
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
        
        # Hardcoded quick hack. Better to be linked to 'default objectives' function in optimize.
        obys = 2015 # "Year to begin optimization from"
        obye = 2030 # "Year to end optimization"
        initialindex = findinds(r.options['partvec'], obys)
        finalparindex = findinds(r.options['partvec'], obye) 
        parindices = arange(initialindex,finalparindex)
        # Note: If the range of indices do not cover enough of the data, you will get strange tx1 problems.
        
        # Hideous hack for ART to use linear unit cost
        from liboptima.utils import sanitize
        artind = r.data['meta']['progs']['short'].index('ART')
        currcost = sanitize(r.data['costcov']['cost'][artind])[-1]
        currcov = sanitize(r.data['costcov']['cov'][artind])[-1]
        unitcost = currcost/currcov
        tempparsmodel['tx1'].flat[parindices] = self.alloc[artind]/unitcost

        from optimize import partialupdateM        
        
        self.parsmodel = partialupdateM(deepcopy(self.parsmodel), deepcopy(tempparsmodel), parindices)

    # Work out the objective value of this SimBudget and its allocation.
    # WARNING: Currently bugged for multiple aims as normalisation values always reflect the final totals.
    def calculateobjectivevalue(self, normaliser = None):
        if not self.isprocessed():
            print('Need to simulate and produce results to calculate objective value.')
            self.run()
        
        r = self.getproject()
        
        # Objectives are currently hard coded and mimic defaultobjectives in optimize.py. Needs to change.
        objectives = dict()
        objectives['year'] = dict()
        objectives['year']['start'] = defaults.startenduntil[0]              # "Year to begin optimization from".
        objectives['year']['end'] = defaults.startenduntil[1]                # "Year to end optimization".
        objectives['year']['until'] = defaults.startenduntil[2]              # "Year to project outcomes to".
        objectives['outcome'] = dict()
        objectives['outcome']['inci'] = defaults.incidalydeathcost[0]                   # "Minimize cumulative HIV incidence".
        objectives['outcome']['inciweight'] = defaults.incidalydeathcostweight[0]       # "Incidence weighting".
        objectives['outcome']['daly'] = defaults.incidalydeathcost[1]                   # "Minimize cumulative DALYs".
        objectives['outcome']['dalyweight'] = defaults.incidalydeathcostweight[1]       # "DALY weighting".
        objectives['outcome']['death'] = defaults.incidalydeathcost[2]                  # "Minimize cumulative AIDS-related deaths".
        objectives['outcome']['deathweight'] = defaults.incidalydeathcostweight[2]      # "Death weighting".
        objectives['outcome']['costann'] = defaults.incidalydeathcost[3]                # "Minimize cumulative DALYs".
        objectives['outcome']['costannweight'] = defaults.incidalydeathcostweight[3]    # "Cost weighting".
        
        initialindex = findinds(r.options['partvec'], objectives['year']['start'])
        finalparindex = findinds(r.options['partvec'], objectives['year']['end'])
        finaloutindex = findinds(r.options['partvec'], objectives['year']['until'])
        parindices = arange(initialindex,finalparindex)
        outindices = arange(initialindex,finaloutindex)        
        
        # Unnecessary with defaults, but normalise and weight objectives if there are multiple options.
        weights = dict()
#        normalizations = dict()
        outcomekeys = ['inci', 'death', 'daly', 'costann']
        if sum([objectives['outcome'][key] for key in outcomekeys])>1:      # Only normalize if multiple objectives, since otherwise doesn't make a lot of sense.
            for key in outcomekeys:
                thisweight = objectives['outcome'][key+'weight'] * objectives['outcome'][key] / 100.
                weights.update({key:thisweight})    # Get weight, and multiply by "True" or "False" and normalize from percentage.
#                if key!='costann': thisnormalization = self.debug['results'][key]['tot'][0][outindices].sum()
#                else: thisnormalization = self.debug['results'][key]['total']['total'][0][outindices].sum()     # Special case for costann.
#                normalizations.update({key:thisnormalization})
        else:
            for key in outcomekeys:
                weights.update({key:int(objectives['outcome'][key])}) # Weight of 1
#                normalizations.update({key:1}) # Normalizatoin of 1     
                
        ## Define options structure
        options = dict()
        options['outcomekeys'] = outcomekeys
        options['weights'] = weights # Weights for each parameter
        options['outindices'] = outindices # Indices for the outcome to be evaluated over
        options['parindices'] = parindices # Indices for the parameters to be updated on
        
        # Decides which SimBudget normalises the outcomes.
        if normaliser == None:
            options['normalizations'] = self.normalisations # Whether to normalize a parameter
        else:
            options['normalizations'] = normaliser.normalisations
        options['randseed'] = 0  
        
        outcome = 0 # Preallocate objective value 
        for key in options['outcomekeys']:
            if options['weights'][key]>0: # Don't bother unless it's actually used
                if key!='costann': thisoutcome = self.debug['results'][key]['tot'][0][options['outindices']].sum()
                else: thisoutcome = self.debug['results'][key]['total']['total'][0][options['outindices']].sum() # Special case for costann
                outcome += thisoutcome * options['weights'][key] / float(options['normalizations'][key]) * r.options['dt'] # Calculate objective
        
        return outcome
    
    # Calculates normalisations used for objectives with multiple aims.
    def calculatenormalisations(self, outcomekeys):
        r = self.getproject()        
        
        initialindex = findinds(r.options['partvec'], defaults.startenduntil[0])
        finaloutindex = findinds(r.options['partvec'], defaults.startenduntil[2])
        outindices = arange(initialindex,finaloutindex)        
        
        normalizations = dict()
        if sum(defaults.incidalydeathcost)>1:
            for key in outcomekeys:
                if key!='costann':
                    thisnormalization = self.debug['results'][key]['tot'][0][outindices].sum()
                else:
                    thisnormalization = self.debug['results'][key]['total']['total'][0][outindices].sum()     # Special case for costann.
                normalizations.update({key:thisnormalization})
        else:
            for key in outcomekeys:
                normalizations.update({key:1})
            
        return normalizations
        

    def __repr__(self):
        return "SimBudget %s ('%s')" % (self.uuid,self.name) 