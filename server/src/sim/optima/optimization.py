from sim import Sim
from simbox import SimBox
from simbudget2 import SimBudget2
from programset import ProgramSet
from collections import defaultdict
from liboptima.utils import printv,findinds
from liboptima.ballsd import ballsd
from liboptima.quantile import quantile
import liboptima.budget_utils as budget_utils
from copy import deepcopy
import numpy
# Note - the apparent sole purpose of the constraints is to come up with fundingchanges

# There are multiple types of optimization, currently: constant, timevarying, multiyear, multibudget
# Why have a single Optimization class? So that you can run different types of optimization
# on the same object without needing conversion
# The optimization delegates to optimize_<type>
# based on the key in the optimization

class Optimization(SimBox):

    def __init__(self,name,project,calibration=None,programset=None,sim=None,objectives=None,constraints=None,initial_alloc=None):
        # An Optimization can be initialized using
        # Optimization(name,project,calibration=cal,programset=pset)
        # Optimization(name,project,sim)
        # Providing a Sim is shorthand for specifiying the calibration and programset ONLY
        # If no alloc is provided, the Project data allocation will be used
        # If an input Sim is provided with a budget, it will be ignored!
        # After optimization, Optimization.initial_sim will be a *new* SimBudget2
        # i.e. if you construct an Optimization with an input Sim, it is NOT retained
        SimBox.__init__(self,name,project)

        if sim is not None and (calibration is not None or programset is not None):
            raise Exception('To avoid ambiguity, providing a Sim and providing calibrations/programsets are mutually exclusive')

        # Make sure calibration and programset are both UUIDs        
        if sim is not None:
            programset = sim.programset
            calibration = sim.calibration
        if isinstance(calibration,dict):
            calibration = calibration['uuid']
        if isinstance(programset,ProgramSet):
            programset = programset.uuid

        if initial_alloc is None:
            print 'Using original data allocation'
            self.initial_alloc = project.data['origalloc']
        else:
            self.initial_alloc = initial_alloc

        self.initial_sim = SimBudget2('Initial',project,self.initial_alloc,calibration,programset)
        self.objectives = objectives if objectives is not None else defaultobjectives(self.initial_sim.getprogramset())
        self.constraints = constraints if constraints is not None else defaultconstraints(self.initial_sim.getprogramset())
        self.optimized_sim = None
        self.optimized_alloc = None
        self.optimization_results = None # Store results that aren't contained within single Sims e.g. quantiles

    def load_dict(self, d):
        SimBox.load_dict(self,d)
        r = self.getproject()
        self.initial_alloc  = d['initial_alloc']
        self.initial_sim  = Sim.fromdict(d['initial_sim'],r)
        self.objectives  = d['objectives']
        self.constraints  = d['constraints']
        self.optimized_sim  = Sim.fromdict(d['optimized_sim'],r) if d['optimized_sim'] is not None else None
        self.optimized_alloc = d['optimized_alloc']
        self.optimization_results = d['optimization_results']

    def todict(self):
        d = SimBox.todict(self)
        d['type'] = 'Optimization'    # Overwrites SimBox type.
        d['initial_alloc']  = self.initial_alloc 
        d['initial_sim']  = self.initial_sim.todict()
        d['constraints']  = self.constraints 
        d['objectives']  = self.objectives 
        d['optimized_sim']  = self.optimized_sim.todict() if isinstance(self.optimized_sim,SimBudget2) else None
        d['optimized_alloc'] = self.optimized_alloc
        d['optimization_results'] = self.optimization_results

        return d

    def optimize(self,maxiters=1000,timelimit=30,verbose=1,stoppingfunc=None,batch=False):
        # Run the optimization and store the output in self.optimized_sim
        # Non-parallel by default, in case the user wants to parallelize at a different level
        # The idea is that the user explicitly specifies the level that they want to parallelize
        r = self.getproject()
        objectives = self.objectives

        # What type of optimization are we doing?
        if objectives['funding'] == 'constant' and objectives['timevarying'] == False:
            optimization_type = 'constant'
        elif objectives['funding'] == 'constant' and objectives['timevarying'] == True:
            optimization_type = 'timevarying'
        elif objectives['funding'] == 'variable':
            optimization_type = 'multiyear'
        elif objectives['funding'] == 'range':
            optimization_type = 'multibudget'

        ## Define indices, weights, and normalization factors
        initialindex = findinds(r.options['partvec'], objectives['year']['start'])
        finalparindex = findinds(r.options['partvec'], objectives['year']['end'])
        finaloutindex = findinds(r.options['partvec'], objectives['year']['until'])
        parindices = numpy.arange(initialindex,finalparindex)
        outindices = numpy.arange(initialindex,finaloutindex)
        weights = dict()
        normalizations = dict()
        outcomekeys = ['inci', 'death', 'daly', 'costann']
        if sum([objectives['outcome'][key] for key in outcomekeys])>1: # Only normalize if multiple objectives, since otherwise doesn't make a lot of sense
            for key in outcomekeys:
                thisweight = objectives['outcome'][key+'weight'] * objectives['outcome'][key] / 100.
                weights.update({key:thisweight}) # Get weight, and multiply by "True" or "False" and normalize from percentage
                if key!='costann': thisnormalization = origR[key]['tot'][0][outindices].sum()
                else: thisnormalization = origR[key]['total']['total'][0][outindices].sum() # Special case for costann
                normalizations.update({key:thisnormalization})
        else:
            for key in outcomekeys:
                weights.update({key:int(objectives['outcome'][key])}) # Weight of 1
                normalizations.update({key:1}) # Normalizatoin of 1

        # This should probably be cleaned up a bit
        ntimepm = 1 + int(objectives['timevarying'])*int(objectives['funding']=='constant') # Either 1 or 2, but only if funding==constant

        ###############################
        # DEFINE OPTIMPARAMS, FUNDINGCHANGES AND STEPSIZES
        stepsize = 100000
        growsize = 0.01
        if optimization_type in ['constant','timevarying','multibudget']:

            # Initial values of time-varying parameters
            growthrate = zeros(nprogs) if ntimepm >= 2 else []
            saturation = self.initial_alloc if ntimepm >= 3 else []
            inflection = ones(nprogs)*.5 if ntimepm >= 4 else []

            initial_optimparams = numpy.concatenate((self.initial_alloc, growthrate, saturation, inflection)) 
            opttrue = self.initial_sim.getprogramset().optimizable()
            nprogs = len(opttrue)

            fundingchanges = dict()
            keys1 = ['year','total']
            keys2 = ['dec','inc']
            abslims = {'dec':0, 'inc':1e9}
            rellims = {'dec':-1e9, 'inc':1e9}
            smallchanges = {'dec':1.0, 'inc':1.0} # WARNING BIZARRE
            for key1 in keys1:
                fundingchanges[key1] = dict()
                for key2 in keys2:
                    fundingchanges[key1][key2] = []
                    for p in xrange(nprogs):
                        fullkey = key1+key2+'rease'
                        this = self.constraints[fullkey][p] # Shorten name
                        if key1=='total':
                            if not(opttrue[p]): # Not an optimized parameter
                                fundingchanges[key1][key2].append(self.initial_alloc[p]*smallchanges[key2])
                            elif this['use'] and objectives['funding'] != 'variable': # Don't constrain variable-year-spend optimizations
                                newlim = this['by']/100.*self.initial_alloc[p]
                                fundingchanges[key1][key2].append(newlim)
                            else: 
                                fundingchanges[key1][key2].append(abslims[key2])
                        elif key1=='year':
                            if this['use'] and objectives['funding'] != 'variable': # Don't constrain variable-year-spend optimizations
                                newlim = this['by']/100.-1 # Relative change in funding
                                fundingchanges[key1][key2].append(newlim)
                            else: 
                                fundingchanges[key1][key2].append(rellims[key2])

            # Initiate probabilities of parameters being selected
            stepsizes = numpy.zeros(nprogs * ntimepm)
            
            # Easy access initial allocation indices and turn stepsizes into array
            ai = range(nprogs)
            gi = range(nprogs,   nprogs*2) if ntimepm >= 2 else []
            si = range(nprogs*2, nprogs*3) if ntimepm >= 3 else []
            ii = range(nprogs*3, nprogs*4) if ntimepm >= 4 else []
            
            # Turn stepsizes into array
            stepsizes[ai] = stepsize
            stepsizes[gi] = growsize if ntimepm > 1 else 0
            stepsizes[si] = stepsize
            stepsizes[ii] = growsize # Not sure that growsize is an appropriate starting point

        elif optimization_type == 'multiyear':
            # There are also modifications to fundingchanges
            nyears = len(objectivecalc_options['years'])
            initial_optimparams = array(origalloc.tolist()*nyears).flatten() # Duplicate parameters
            parammin = numpy.zeros(len(initial_optimparams))
            
            keys1 = ['year','total']
            keys2 = ['dec','inc']
            abslims = {'dec':0, 'inc':1e9}
            rellims = {'dec':-1e9, 'inc':1e9}
            for key1 in keys1:
                for key2 in keys2:
                    objectivecalc_options['fundingchanges'][key1][key2] *= nyears # I know this just points to the list rather than copies, but should be fine. I hope
            
            stepsizes = stepsize + numpy.zeros(len(initial_optimparams))

        ###############################
        # DEFINE ALLOCS/OPTIMPARAMS TO ITERATE OVER
        if optimization_type in ['constant','timevarying','multiyear']:
            initial_optimparams = [initial_optimparams]
        elif optimization_type == 'multibudget':
            allocs = numpy.arange(objectives['outcome']['budgetrange']['minval'], objectives['outcome']['budgetrange']['maxval']+objectives['outcome']['budgetrange']['step'], objectives['outcome']['budgetrange']['step'])
            closesttocurrent = argmin(abs(allocs-1)) + 1 # Find the index of the budget closest to current and add 1 since prepend current budget
            initial_optimparams = hstack([1,allocs]) # Include current budget

        ###############################
        # DEFINE METAPARAMETERS TO ITERATE OVER
        if optimization_type == 'constant':
            metaparameterlist = self.initial_sim.getcalibration()['metaparameters']
        elif optimization_type in ['timevarying','multiyear','multibudget']:
            metaparameterlist = [self.initial_sim.getcalibration()['metaparameters'][0]]

        ###############################
        # DEFINE OBJECTIVECALC_OPTIONS
        objectivecalc_options = dict()
        objectivecalc_options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        objectivecalc_options['normalizations'] = normalizations # Whether to normalize a parameter
        objectivecalc_options['weights'] = weights # Weights for each parameter
        objectivecalc_options['outcomekeys'] = outcomekeys # Names of outcomes, e.g. 'inci'
        objectivecalc_options['nprogs'] = nprogs # Number of programs
        objectivecalc_options['outindices'] = outindices # Indices for the outcome to be evaluated over
        objectivecalc_options['parindices'] = parindices # Indices for the parameters to be updated on

        objectivecalc_options['sim'] = self.initial_sim.make_standalone_copy() # Indices for the parameters to be updated on
        objectivecalc_options['optimization_type'] = optimization_type

        if optimization_type == 'constant':
            objectivecalc_options['ntimepm'] = ntimepm
            objectivecalc_options['totalspend'] = sum(self.initial_alloc) # Total budget
            objectivecalc_options['randseed'] = 0

        elif optimization_type == 'timevarying':
            objectivecalc_options['ntimepm'] = ntimepm
            objectivecalc_options['totalspend'] = sum(self.initial_alloc) # Total budget
            parammin = concatenate((fundingchanges['total']['dec'], ones(nprogs)*-1e9))  
            parammax = concatenate((fundingchanges['total']['inc'], ones(nprogs)*1e9))  
            objectivecalc_options['randseed'] = 1

        elif optimization_type == 'multiyear':
            objectivecalc_options['randseed'] = None # Death is enough randomness on its own
            objectivecalc_options['years'] = []
            objectivecalc_options['totalspends'] = []
            yearkeys = objectives['outcome']['variable'].keys()
            yearkeys.sort() # God damn I hate in-place methods
            for key in yearkeys: # Stored as a list of years:
                objectivecalc_options['years'].append(float(key)) # Convert from string to number
                objectivecalc_options['totalspends'].append(objectives['outcome']['variable'][key]) # Append this year

        elif optimization_type == 'multibudget':
            objectivecalc_options['ntimepm'] = 1 # Number of time-varying parameters -- always 1 in this case
            objectivecalc_options['totalspend'] = sum(self.initial_alloc) # Total budget
            objectivecalc_options['randseed'] = None
        
        ###############################
        # DEFINE BALLSD_OPTIONS
        ballsd_options = dict()
        ballsd_options['MaxIter']=maxiters
        ballsd_options['timelimit']=timelimit
        ballsd_options['fulloutput']=True
        ballsd_options['stoppingfunc']=stoppingfunc
        ballsd_options['verbose']=verbose

        if optimization_type == 'constant':
            ballsd_options['xmin'] = fundingchanges['total']['dec']
            ballsd_options['xmax']=fundingchanges['total']['inc']
            ballsd_options['absinitial']=stepsizes
       
        elif optimization_type == 'timevarying':
            ballsd_options['xmin'] = parammin
            ballsd_options['xmax'] = parammax
            ballsd_options['absinitial']=stepsizes
       
        elif optimization_type == 'multiyear':
            ballsd_options['xmin'] = fundingchanges['total']['dec']
            ballsd_options['xmax'] = fundingchanges['total']['inc']
            ballsd_options['absinitial']=None
       
        elif optimization_type == 'multibudget':
            ballsd_options['xmin'] = fundingchanges['total']['dec']
            ballsd_options['xmax'] = fundingchanges['total']['inc']
            ballsd_options['absinitial']=stepsizes

        ###############################
        # Now, enumerate the (alloc,metaparameters,objective_options,ballsd_options) tuples to iterate over
        iterations = []
        for opt_params in initial_optimparams:
            for metaparameters in metaparameterlist:
                iterations.append((opt_params,metaparameters,objectivecalc_options,ballsd_options))

        outputs = []
        if batch:
            raise Exception('Batch pool here')
        else:
            for inputs in iterations:
                outputs.append(parallel_ballsd_wrapper(inputs))

        # Make a SimBudget for the initial optimparams
        # For multibudget, this is assumed to be the first one
        initial_budget = objectivecalc(initial_optimparams[0],objectivecalc_options,getbudget=True)
        self.initial_sim.budget = initial_budget
        self.initial_sim.run(force_initialise=True)

        # Make a SimBudget for the optimal budget
        best_optimparams = min(outputs,key=lambda x: x[1])[0] # Return 
        self.optimized_alloc = best_optimparams # WARNING - this probably breaks if timevarying...
        best_budget = objectivecalc(best_optimparams,objectivecalc_options,getbudget=True)
        self.optimized_sim = SimBudget2('Optimized',self.getproject(),best_budget,self.initial_sim.calibration,self.initial_sim.programset)
        self.optimized_sim.run(force_initialise=True)

        # Finally, do the quantile analysis
        # WARNING - this *might* need to be structured differently for multibudget optimization?
        self.optimization_results = dict()
        self.optimization_results['allocarr'] = [] # List of allocations
        self.optimization_results['allocarr'].append(quantile([self.initial_alloc])) # Kludgy -- run fake quantile on duplicated origalloc just so it matches
        self.optimization_results['allocarr'].append(quantile([x[0] for x in iterations])) # Calculate allocation arrays 

    # Calculates objective values for certain multiplications of an alloc's variable costs (passed in as list of factors).
    # The idea is to spline a cost-effectiveness curve across several budget totals.
    # Note: We don't care about the allocations in detail. This is just a function between totals and the objective.
    def calculateeffectivenesscurve(self, sim, factors):
        raise Exception('This function need to be re-implemented for the new system')           

    # A custom built plotting function to roughly mirror legacy 'viewoptimresults'.
    def plot(self, plotasbar=False,show_wait=True):

        if self.optimized_sim is None:
            print('Optimization not run yet - doing it now')
            self.optimize()

        atleastoneplot = False
        for sim in self.simlist:
            if sim.isinitialised():
                atleastoneplot = True
                
        if not atleastoneplot:
            print('There is no optimisation data in this simulation container to plot.')
        else:
            r = self.project()
            
            from matplotlib.pylab import figure, subplot, plot, pie, bar, title, legend, xticks, ylabel, show
            from gridcolormap import gridcolormap
            from matplotlib import gridspec
        
            nprograms = len(r.data['origalloc'])
            colors = gridcolormap(nprograms)
            
            if plotasbar:
                figure(figsize=(len(self.simlist)*2+4,nprograms/2))
                gs = gridspec.GridSpec(1, 2, width_ratios=[len(self.simlist), 2]) 
                ind = xrange(len(self.simlist))
                width = 0.8       # the width of the bars: can also be len(x) sequence
                
                subplot(gs[0])
                bar(ind, [sim.alloc[-1] for sim in self.simlist], width, color=colors[-1])
                for p in xrange(2,nprograms+1):
                    bar(ind, [sim.alloc[-p] for sim in self.simlist], width, color=colors[-p], bottom=[sum(sim.alloc[1-p:]) for sim in self.simlist])
                xticks([index+width/2.0 for index in ind], [sim.getname() for sim in self.simlist])
                ylabel('Budget Allocation ($)')
                
                subplot(gs[1])
                for prog in xrange(nprograms): plot(0, 0, linewidth=3, color=colors[prog])
                legend(r.data['meta']['progs']['short'])
            else:
                figure(figsize=(12,4*(len(self.simlist)/3+1)))
                c = 0
                for p in xrange(len(self.simlist)):
                    sim = self.simlist[p]
                    if sim.isprocessed():
                        subplot(len(self.simlist)/3+1,3,p-c+1)
                        pie(sim.alloc, colors=colors, labels=r.data['meta']['progs']['short'])
                        title(sim.getname())
                    else:
                        c += 1
            if show_wait:
                show()

    def __repr__(self):
        return "Optimization %s ('%s')" % (self.uuid[0:4],self.name)


def objectivecalc(optimparams, objective_options, getbudget = False):
    """ Calculate the objective function """

    # This function has the special option that if getbudget = True, the budget will be computed
    # and then returned as the outcome without running the simulation

    # First, constrain the alloc
    optimparams = constrain_alloc(optimparams, total=objective_options['totalspend'], limits=objective_options['fundingchanges']['total'])
    s = objective_options['sim']

    # Next, turn it into a budget and put it into the sim
    if objective_options['optimization_type'] in ['constant','timevarying','multibudget']:
        budget = budget_utils.timevarying(optimparams, ntimepm=objective_options['ntimepm'], nprogs=objective_options['nprogs'], tvec=s.project.options['partvec'], totalspend=objective_options['totalspend'], fundingchanges=objective_options['fundingchanges']) 
    elif objective_options['optimization_type'] == 'multiyear':
        budget = budget_utils.multiyear(optimparams, years=objective_options['years'], totalspends=objective_options['totalspends'], nprogs=objective_options['nprogs'], tvec=s.project.options['partvec']) 
    else:
        raise Exception('Cannot figure out what kind of allocation this is since neither objective_options[\'ntimepm\'] nor objective_options[\'years\'] is defined')
    
    if getbudget:
        return budget

    s.budget = budget

    # Run the simulation
    S,R = s.run(force_initialise=True)

    # Compute the objective value and return it
    outcome = 0 # Preallocate objective value 
    for key in objective_options['outcomekeys']:
        if objective_options['weights'][key]>0: # Don't bother unless it's actually used
            if key!='costann': 
                thisoutcome = R[key]['tot'][0][objective_options['outindices']].sum()
            else: 
                thisoutcome = R[key]['total']['total'][0][objective_options['outindices']].sum() # Special case for costann
            outcome += thisoutcome * objective_options['weights'][key] / float(objective_options['normalizations'][key]) * s.project.options['dt'] # Calculate objective
    
    return outcome

def parallel_ballsd_wrapper(inputs):
    # inputs are (alloc,metaparameters,objective_options,ballsd_options)
    # SINGLE ones of each of these
    # The idea is that we define the objective 
    optimparams = inputs[0]
    metaparameters = inputs[1]
    objective_options = inputs[2]
    ballsd_options = inputs[3]

    # Overwrite the calibration metaparameters in the standalone sim
    # TODO: This step will change when we have a more solid plan for dealing with calibrations vs calibrationsets
    objective_options['sim'].project.calibrations[0]['metaparameters'] = [metaparameters]

    optparams, fval, exitflag, output = ballsd(objectivecalc,optimparams,options=objective_options,xmin=ballsd_options['xmin'],xmax=ballsd_options['xmax'],absinitial=ballsd_options['absinitial'],MaxIter=ballsd_options['MaxIter'],timelimit=ballsd_options['timelimit'],fulloutput=ballsd_options['fulloutput'],stoppingfunc=ballsd_options['stoppingfunc'],verbose=ballsd_options['verbose'])

    return (optparams,output.fval)

def constrain_alloc(origalloc,total, limits):
    """ Take an unnormalized/unconstrained alloc and normalize and constrain it """
    # this used to be constrainalloc
    normalloc = deepcopy(origalloc)
    
    eps = 1e-3 # Don't try to make an exact match, I don't have that much faith in my algorithm
    
    if total < sum(limits['dec']) or total > sum(limits['inc']):
        raise Exception('Budget cannot be constrained since the total %f is outside the low-high limits [%f, %f]' % (total, sum(limits['dec']), sum(limits['inc'])))
    
    nprogs = len(normalloc)
    proginds = numpy.arange(nprogs)
    limlow = numpy.zeros(nprogs, dtype=bool)
    limhigh = numpy.zeros(nprogs, dtype=bool)
    for p in proginds:
        if normalloc[p] <= limits['dec'][p]:
            normalloc[p] = limits['dec'][p]
            limlow[p] = 1
        if normalloc[p] >= limits['inc'][p]:
            normalloc[p] = limits['inc'][p]
            limhigh[p] = 1
    
    # Too high
    while sum(normalloc) > total+eps:
        overshoot = sum(normalloc) - total
        toomuch = sum(normalloc[~limlow]) / (sum(normalloc[~limlow]) - overshoot)
        for p in proginds[~limlow]:
            proposed = normalloc[p] / toomuch
            if proposed <= limits['dec'][p]:
                proposed = limits['dec'][p]
                limlow[p] = 1
            normalloc[p] = proposed
        
    # Too low
    while sum(normalloc) < total-eps:
        undershoot = total - sum(normalloc)
        toolittle = (sum(normalloc[~limhigh]) + undershoot) / sum(normalloc[~limhigh])
        for p in proginds[~limhigh]:
            proposed = normalloc[p] * toolittle
            if proposed >= limits['inc'][p]:
                proposed = limits['inc'][p]
                limhigh[p] = 1
            normalloc[p] = proposed
    
    return normalloc

def defaultobjectives(programset,verbose=2):
    """
    Define default objectives for the optimization.
    """
    import defaults
    printv('Defining default objectives...', 3, verbose=verbose)

    ob = dict() # Dictionary of all objectives
    ob['year'] = dict() # Time periods for objectives
    ob['year']['start'] = defaults.startenduntil[0] # "Year to begin optimization from"
    ob['year']['end'] = defaults.startenduntil[1] # "Year to end optimization"
    ob['year']['until'] = defaults.startenduntil[2] # "Year to project outcomes to"
    ob['what'] = 'outcome' # Alternative is "['money']"
    
    ob['outcome'] = dict()
    ob['outcome']['inci'] = defaults.incidalydeathcost[0] # "Minimize cumulative HIV incidence"
    ob['outcome']['inciweight'] = defaults.incidalydeathcostweight[0] # "Incidence weighting"
    ob['outcome']['daly'] = defaults.incidalydeathcost[1] # "Minimize cumulative DALYs"
    ob['outcome']['dalyweight'] = defaults.incidalydeathcostweight[1] # "DALY weighting"
    ob['outcome']['death'] = defaults.incidalydeathcost[2] # "Minimize cumulative AIDS-related deaths"
    ob['outcome']['deathweight'] = defaults.incidalydeathcostweight[2] # "Death weighting"
    ob['outcome']['costann'] = defaults.incidalydeathcost[3] # "Minimize cumulative DALYs"
    ob['outcome']['costannweight'] = defaults.incidalydeathcostweight[3] # "Cost weighting"
    ob['outcome']['variable'] = [] # No variable budgets by default
    ob['outcome']['budgetrange'] = dict() # For running multiple budgets
    ob['outcome']['budgetrange']['minval'] = None
    ob['outcome']['budgetrange']['maxval'] = None
    ob['outcome']['budgetrange']['step'] = None
    ob['funding'] = "constant" #that's how it works on FE atm

    # Other settings
    ob['timevarying'] = False # Do not use time-varying parameters
    ob['artcontinue'] = 1 # No one currently on ART stops
    ob['otherprograms'] = "remain" # Other programs remain constant after optimization ends

    ob['money'] = dict()
    ob['money']['objectives'] = dict()
    for objective in ['inci', 'incisex', 'inciinj', 'mtct', 'mtctbreast', 'mtctnonbreast', 'death', 'dalys']:
        ob['money']['objectives'][objective] = dict()
        # Checkbox: by default it's False meaning the objective is not applied
        ob['money']['objectives'][objective]['use'] = False
        # If "By" is not active "To" is used. "By" is active by default. 
        ob['money']['objectives'][objective]['by_active'] = True
        # "By" text entry box: 0.5 means a 50% reduction
        ob['money']['objectives'][objective]['by'] = 0.5
        # "To" text entry box: an absolute value e.g. reduce deaths to <500
        ob['money']['objectives'][objective]['to'] = 0
    ob['money']['objectives']['inci']['use'] = True # Set incidence to be on by default

    ob['money']['costs'] = [] # By default, use a weighting of 100%
    for p in xrange(len(programset.programs)):
        ob['money']['costs'].append(100) # By default, use a weighting of 100%
    return ob

def defaultconstraints(programset,verbose=2):
    """
    Define default constraints for the optimization.
    """

    printv('Defining default constraints...', 3, verbose=verbose)

    con = dict()
    con['txelig'] = 4 # 4 = "All people diagnosed with HIV"
    con['dontstopart'] = True # "No one who initiates treatment is to stop receiving ART"
    con['yeardecrease'] = []
    con['yearincrease'] = []
    for p in xrange(len(programset.programs)): # Loop over all defined programs
        con['yeardecrease'].append(dict())
        con['yeardecrease'][p]['use'] = False # Tick box: by default don't use
        con['yeardecrease'][p]['by'] = 80 # Text entry box: 0.5 = 50% per year
        con['yearincrease'].append(dict())
        con['yearincrease'][p]['use'] = False # Tick box: by default don't use
        con['yearincrease'][p]['by'] = 120 # Text entry box: 0.5 = 50% per year
    con['totaldecrease'] = []
    con['totalincrease'] = []
    for p in xrange(len(programset.programs)): # Loop over all defined programs
        con['totaldecrease'].append(dict())
        con['totaldecrease'][p]['use'] = False # Tick box: by default don't use
        con['totaldecrease'][p]['by'] = 50 # Text entry box: 0.5 = 50% per total
        con['totalincrease'].append(dict())
        con['totalincrease'][p]['use'] = False # Tick box: by default don't use
        con['totalincrease'][p]['by'] = 200 # Text entry box: 0.5 = 50% total
    
    con['coverage'] = []
    for p in xrange(len(programset.programs)): # Loop over all defined programs
        con['coverage'].append(dict())
        con['coverage'][p]['use'] = False # Tick box: by default don't use
        con['coverage'][p]['level'] = 0 # First text entry box: default no limit
        con['coverage'][p]['year'] = 2030 # Year to reach coverage level by
        
    return con








