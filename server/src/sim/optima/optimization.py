from sim import Sim
from simbox import SimBox
from simbudget2 import SimBudget2

# Note - the apparent sole purpose of the constraints is to come up with fundingchanges

# There are multiple types of optimization, currently: constant, timevarying, multiyear, multibudget
# Why have a single Optimization class? So that you can run different types of optimization
# on the same object without needing conversion
# The optimization delegates to optimize_<type>
# based on the key in the optimization



inputmaxiters = defaults.maxiters, inputtimelimit = defaults.timelimit


class Optimization(SimBox):

	def __init__(self,name,project,sim,objectives=default_objectives,constraints=default_constraints,alloc=None):
		# For this one, we can ignore the simlist
		SimBox.__init__(self,name,project)

		if not isinstance(sim,SimBudget2):
			raise Exception('Optimization container can only be created using a SimBudget2')

		self.initial_sim = sim 
		self.optimized_sim = None
		self.objectives = objectives
		self.constraints = constraints
		if alloc is None:
			print 'Using data original allocation'
			self.initial_alloc = project.data['origalloc']
		else:
			self.initial_alloc = alloc

    def load_dict(self, simboxdict):
    	SimBox.load_dict(self,simboxdict)
    	r = self.getproject()
    	self.optimized_sim  = Sim.fromdict(d['optimized_sim'],r) if d['optimized_sim'] is not None else None
    	self.initial_sim  = Sim.fromdict(d['initial_sim'],r)
    	self.objectives  = d['objectives']
    	self.constraints  = d['constraints']
    	self.initial_alloc  = d['initial_alloc']

    def todict(self):
        d = SimBox.todict(self)
        d['type'] = 'Optimization'    # Overwrites SimBox type.
		d['initial_sim']  = self.initial_sim.todict()
		d['optimized_sim']  = self.optimized_sim if isinstance(self.optimized_sim ,SimBudget2) else None
		d['options']  = self.options 
		d['constraints']  = self.constraints 
		d['initial_alloc']  = self.initial_alloc 
        return d

    def optimize(self,maxiters=1000,timelimit=None,verbose=5,stoppingfunc=None):
    	# Run the optimization and store the output in self.optimized_sim
        r = self.getproject()

        # What type of optimization are we doing?
        if objectives['funding'] == 'constant' and objectives['timevarying'] == False:
        	optimization_type = 'constant'
        elif objectives['funding'] == 'constant' and objectives['timevarying'] == True:
        	optimization_type = 'timevarying'
        elif objectives['funding'] == 'variable':
        	optimization_type = 'multiyear'
        elif objectives['funding'] == 'range':
        	optimization_type = 'multibudget'

        # What's the current epidemiology?
        self.initial_sim.alloc = self.initial_alloc
        self.initial_sim.run(force_initialise=True) # We might have changed the alloc, so re-initialize


        # Make the objectivecalc options and

        objectivecalc_options = dict()
        objectivecalc_options['D'] = deepcopy(D) # Main data structure
        objectivecalc_options['normalizations'] = normalizations # Whether to normalize a parameter
        objectivecalc_options['fundingchanges'] = fundingchanges # Constraints-based funding changes
        objectivecalc_options['weights'] = weights # Weights for each parameter
        objectivecalc_options['outcomekeys'] = outcomekeys # Names of outcomes, e.g. 'inci'
        objectivecalc_options['nprogs'] = nprogs # Number of programs
        objectivecalc_options['outindices'] = outindices # Indices for the outcome to be evaluated over
        objectivecalc_options['parindices'] = parindices # Indices for the parameters to be updated on

        if constant:
        	objectivecalc_options['ntimepm'] = ntimepm # Number of time-varying parameters
        	objectivecalc_options['totalspend'] = sum(origalloc) # Total budget
        	objectivecalc_options['randseed'] = 0
        	objectivecalc_options['tmpbestdata'] = []


        	# constant
        	ballsd_options['xmin'] = fundingchanges['total']['dec']
        	ballsd_options['xmax']=fundingchanges['total']['inc']
        	ballsd_options['absinitial']=stepsizes

        	metaparameterlist = all of them
        	run ballsd for each d.f

        if timevarying:
        	## Define objectivecalc_options structure
        	objectivecalc_options['ntimepm'] = ntimepm # Number of time-varying parameters
        	objectivecalc_options['totalspend'] = totalspend # Total budget
        	parammin = concatenate((fundingchanges['total']['dec'], ones(nprogs)*-1e9))  
        	parammax = concatenate((fundingchanges['total']['inc'], ones(nprogs)*1e9))  
        	objectivecalc_options['randseed'] = 1

        	# timevarying
        	ballsd_options['xmin'] = parammin
        	ballsd_options['xmax']=parammax
        	ballsd_options['absinitial']=stepsizes

        	metaparameterlist = (just one)
        	run ballsd

        if multiple year :
        	objectivecalc_options['randseed'] = None # Death is enough randomness on its own
        	objectivecalc_options['years'] = []
        	objectivecalc_options['totalspends'] = []
        	yearkeys = objectives['outcome']['variable'].keys()
        	yearkeys.sort() # God damn I hate in-place methods
        	for key in yearkeys: # Stored as a list of years:
        	    objectivecalc_options['years'].append(float(key)) # Convert from string to number
        	    objectivecalc_options['totalspends'].append(objectives['outcome']['variable'][key]) # Append this year

    	    # multiple year 
    	    ballsd_options['xmin'] = fundingchanges['total']['dec']
    	    ballsd_options['xmax'] = fundingchanges['total']['inc']

    	    ## Define optimization parameters
    	    nyears = len(options['years'])
    	    optimparams = array(origalloc.tolist()*nyears).flatten() # Duplicate parameters
    	    parammin = zeros(len(optimparams))
    	    stepsizes = stepsize + zeros(len(optimparams))
    	    keys1 = ['year','total']
    	    keys2 = ['dec','inc']
    	    abslims = {'dec':0, 'inc':1e9}
    	    rellims = {'dec':-1e9, 'inc':1e9}
    	    for key1 in keys1:
    	        for key2 in keys2:
    	            options['fundingchanges'][key1][key2] *= nyears # I know this just points to the list rather than copies, but should be fine. I hope

    	    metaparameterlist = (just one)
    	    run ballsd with the special fundingchanges

        if multiple allocs:
        	objectivecalc_options['ntimepm'] = 1 # Number of time-varying parameters -- always 1 in this case
        	objectivecalc_options['totalspend'] = totalspend # Total budget
        	objectivecalc_options['randseed'] = None


        	# multiple budgets
        	ballsd_options['xmin'] = fundingchanges['total']['dec']
        	ballsd_options['xmax']=fundingchanges['total']['inc']
        	ballsd_options['absinitial']=stepsizes


        	allocs = multiple_allocs(alloc)

        	metaparameterlist = (just one)
        	for alloc:
        		ballsd on each alloc

        # Now we have a list of allocs
        # and a list of *individual* calibrations (not calibrationsets)
        # Iterate over them and optimize each one
        # What we want to get back is - the parameters, and the fval, in a tuple
        # and then we just pick the best one
        for budget in budgets:
        	for metaparameters in metaparameterlist:
        		ballsd

        # Pick the best one, and keep it

     		put multiple budget simbudgets into 
        ballsd(objective,objective_options,ballsd_options)

       		- objective uses objective_options to
       			0. Convert the optimizationparams into a budget
       			1. initialize a SimBudget2
       			2. run the SimBudget2
       			3. compute the value of the objective and return it

        and it should be possible to run multiple ballsds in parallel. so accumulating output should not be done yet


        in all cases, the optimizationparams is the same?





	    ## Gather plot data
	    from gatherplotdata import gatheroptimdata
	    plot_result = gatheroptimdata(D, result, verbose=verbose)
	    if 'optim' not in D['plot']: D['plot']['optim'] = [] # Initialize list if required
	    D['plot']['optim'].append(plot_result) # In any case, append
	    
	    result_to_save = {'plot': [plot_result]}

	    ## Save optimization to D
	    D = saveoptimization(D, name, objectives, constraints, result_to_save, verbose=2)

	    printv('...done optimizing programs.', 2, verbose)
	    
	    # This is new code for the OOP structure. Legacy users will not run this line because returnresult is false by default.
	    if returnresult:
	#        D['result'] = result['Rarr'][-1]['R']
	        D['objective'] = result['fval']         # Note: Need to check this rigorously. Optimize is becoming a mess.
	        D['optalloc'] = [x for x in optparams]  # This works for default optimisation. It may not for any more-complicated options.
	    
	    return D


	def get_fundingchanges(self):
		# Define constraints on funding -- per year and total
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
		                    fundingchanges[key1][key2].append(origalloc[p]*smallchanges[key2])
		                elif this['use'] and objectives['funding'] != 'variable': # Don't constrain variable-year-spend optimizations
		                    newlim = this['by']/100.*origalloc[p]
		                    fundingchanges[key1][key2].append(newlim)
		                else: 
		                    fundingchanges[key1][key2].append(abslims[key2])
		            elif key1=='year':
		                if this['use'] and objectives['funding'] != 'variable': # Don't constrain variable-year-spend optimizations
		                    newlim = this['by']/100.-1 # Relative change in funding
		                    fundingchanges[key1][key2].append(newlim)
		                else: 
		                    fundingchanges[key1][key2].append(rellims[key2])






    # Calculates objective values for certain multiplications of an alloc's variable costs (passed in as list of factors).
    # The idea is to spline a cost-effectiveness curve across several budget totals.
    # Note: We don't care about the allocations in detail. This is just a function between totals and the objective.
    def calculateeffectivenesscurve(self, sim, factors):
        curralloc = sim.alloc
        
        totallocs = []
        objarr = []
        timelimit = defaults.timelimit
#        timelimit = 1.0
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        # These will be ignored when testing different allocations.
        fixedtrue = [1.0]*(len(curralloc))
        for i in xrange(len(curralloc)):
            if len(self.getproject().metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
        
        for factor in factors:
            try:
                print('Testing budget allocation multiplier of %f.' % factor)
                sim.alloc = [curralloc[i]*(factor+(1-factor)*fixedtrue[i]) for i in xrange(len(curralloc))]
                betterbudget, betterobj, a = self.optimise(sim, makenew = False, inputtimelimit = timelimit)
                
                betteralloc = [alloclist[0] for alloclist in betterbudget]
                
                objarr.append(betterobj)
                totallocs.append(sum(betteralloc))
            except:
                print('Multiplying pertinent budget allocation values by %f failed.' % factor)
            
        sim.alloc = curralloc
        
        # Remember that total alloc includes fixed costs (e.g admin)!
        return (totallocs, objarr)
            

    
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


    

    # Scales the variable costs of an alloc so that the sum of the alloc equals newtotal.
    # Note: Can this be fused with the scaling on the Project level...?
    
    

    def __repr__(self):
        return "SimBoxOpt %s ('%s')" % (self.uuid[0:4],self.name)



def defaultobjectives(D, verbose=2):
    """
    Define default objectives for the optimization.
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    ob = dict() # Dictionary of all objectives
    ob['year'] = dict() # Time periods for objectives
    ob['year']['start'] = defaults.startenduntil[0] # "Year to begin optimization from"
    ob['year']['end'] = defaults.startenduntil[1] # "Year to end optimization"
    ob['year']['until'] = defaults.startenduntil[2] # "Year to project outcomes to"
    ob['what'] = 'outcome' # Alternative is "['money']"
    
    ob['outcome'] = dict()
    ob['outcome']['fixed'] = sum(D['data']['origalloc']) # "With a fixed amount of ['money'] available"
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

    ob['money']['costs'] = []
    for p in xrange(D['G']['nprogs']):
        ob['money']['costs'].append(100) # By default, use a weighting of 100%

    return ob

def defaultconstraints(D, verbose=2):
    """
    Define default constraints for the optimization.
    """

    printv('Defining default constraints...', 3, verbose=verbose)

    con = dict()
    con['txelig'] = 4 # 4 = "All people diagnosed with HIV"
    con['dontstopart'] = True # "No one who initiates treatment is to stop receiving ART"
    con['yeardecrease'] = []
    con['yearincrease'] = []
    for p in xrange(D['G']['nprogs']): # Loop over all defined programs
        con['yeardecrease'].append(dict())
        con['yeardecrease'][p]['use'] = False # Tick box: by default don't use
        con['yeardecrease'][p]['by'] = 80 # Text entry box: 0.5 = 50% per year
        con['yearincrease'].append(dict())
        con['yearincrease'][p]['use'] = False # Tick box: by default don't use
        con['yearincrease'][p]['by'] = 120 # Text entry box: 0.5 = 50% per year
    con['totaldecrease'] = []
    con['totalincrease'] = []
    for p in xrange(D['G']['nprogs']): # Loop over all defined programs
        con['totaldecrease'].append(dict())
        con['totaldecrease'][p]['use'] = False # Tick box: by default don't use
        con['totaldecrease'][p]['by'] = 50 # Text entry box: 0.5 = 50% per total
        con['totalincrease'].append(dict())
        con['totalincrease'][p]['use'] = False # Tick box: by default don't use
        con['totalincrease'][p]['by'] = 200 # Text entry box: 0.5 = 50% total
    
    con['coverage'] = []
    for p in xrange(D['G']['nprogs']): # Loop over all defined programs
        con['coverage'].append(dict())
        con['coverage'][p]['use'] = False # Tick box: by default don't use
        con['coverage'][p]['level'] = 0 # First text entry box: default no limit
        con['coverage'][p]['year'] = 2030 # Year to reach coverage level by
        
    return con








