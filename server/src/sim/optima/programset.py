import uuid
from operator import mul
import defaults
from collections import defaultdict
import ccocs
from copy import deepcopy
import liboptima.dataio_binary as dataio_binary
import liboptima
import pylab
import numpy
import simbudget2

#### TODO LIST
# - Ignore data when plotting if there is a mismatch (i.e. if programset has been moved to a different region and a program with the same name exists but has different effects or reaches a different population)
# - Add perturbations to CCOCs
# - Examine auto fitting
# - Incorporate metamodality reflow
# - Add metamodality tests
# - How should plotting work with time-varying CCOCs? Will need to decide on the plotting routines first

coverage_params = ['numcircum','numost','numpmtct','numfirstline','numsecondline'] # This list is copied from makeccocs.py
# What about aidstest, sharing, and breast?

class ProgramSet(object):
    # This class is a collection of programs/modalities
    def __init__(self,name):
        self.name = name
        self.uuid = str(uuid.uuid4())
        self.programs = []
        self.default_reachability_interaction = 'random' # These are the options on slide 7 of the proposal
        assert(self.default_reachability_interaction in ['random','additive','nested']) # Supported reachability types
        self.specific_reachability_interaction = defaultdict(dict) # Override reachability e.g. self.specific_reachability_interaction['FSW']['testing'] = 'additive'

        self.current_version = 1

    @classmethod
    def load(ProgramSet,filename,name=None):
        # Use this function to load a ProgramSet saved with ProgramSet.save
        r = ProgramSet(name)
        psetdict = dataio_binary.load(filename)
        r.uuid = psetdict['uuid'] # Loading a ProgramSet restores the original UUID
        r.fromdict(psetdict)
        return r

    def save(self,filename):
        dataio_binary.save(self.todict(),filename)

    @classmethod
    def fromdict(ProgramSet,psetdict):

        p = ProgramSet(None)
        psetdict = p.upgrade_version(psetdict)
        
        p.name = psetdict['name']
        p.uuid = psetdict['uuid']
        p.programs = [Program.fromdict(x) for x in psetdict['programs']]
        p.default_reachability_interaction = psetdict['default_reachability_interaction']
        return p


    def upgrade_version(self,projectdict):
        # Upgrade the projectdict to support new versions
        return projectdict

    def todict(self):
        psetdict = dict()
        psetdict['name'] = self.name 
        psetdict['uuid'] = self.uuid 
        psetdict['programs'] = [x.todict() for x in self.programs]
        psetdict['default_reachability_interaction'] = self.default_reachability_interaction 
        psetdict['current_version'] = self.current_version 

        return deepcopy(psetdict)
    
    def __getstate__(self):
        return self.todict()

    def __setstate__(self, state):
        self.fromdict(state)

    def optimizable(self):
        # Return an array the same length as the number of programs
        # containing 'True' if the program has effects and can therefore
        # be optimized
        return [True if prog.coverage_outcome else False for prog in self.programs]

    @classmethod
    def import_legacy(ProgramSet,name,programdata):
        # This function initializes the programs based on the dictionary programdata, obtained
        # from r.metadata['programs']

        ps = ProgramSet(name)
        ps.programs = [] # Make sure we start with an empty program list
        
        for prog in programdata:
            cc_inputs = []
            co_inputs = []

            if prog['effects']: # A spending only program has no effects - it exists in the program list but because it covers no populations, it gets skipped when evaluating parameters
                
                # First, sanitize the population names
                for effect in prog['effects']:
                    if effect['popname'] in ['Total','Average','Overall']:
                        effect['popname'] = 'Overall'

                target_pops = list(set([effect['popname'] for effect in prog['effects']])) # Unique list of affected populations. In legacy programs, they all share the same CC curve
                
                for pop in target_pops:
                    cc_input = dict()
                    cc_input['pop'] = pop
                    if 'scaleup' in prog['ccparams'].keys() and prog['ccparams']['scaleup'] and ~numpy.isnan(prog['ccparams']['scaleup']):
                        cc_input['form'] = 'cc_scaleup'
                    else:
                        cc_input['form'] = 'cc_noscaleup'
                    cc_input['fe_params'] = prog['ccparams']
                    cc_inputs.append(cc_input)

                for effect in prog['effects']:
                    co_input = dict()
                    co_input['pop'] = effect['popname']
                    co_input['param'] = effect['param']

                    if co_input['param'] in coverage_params and co_input['pop'] != 'Overall':
                        # If simbudget2 uses special popsize estimates for the coverage parameters
                        # but this coverage parameter targets a population, then should the population size
                        # or the special estimate be used?
                        raise Exception('A coverage parameter (%s) has been defined for a specific population (%s)? Look into this' % (co_input['param'],co_input['pop']))

                    if effect['param'] in coverage_params: 
                        co_input['form'] = 'identity'
                        co_input['fe_params'] = None
                    else:
                        co_input['form'] = 'co_cofun'
                        co_input['fe_params'] = effect['coparams']
                    
                    co_inputs.append(co_input)

            ps.programs.append(Program(prog['name'],cc_inputs,co_inputs,prog['nonhivdalys']))

        return ps


    def plot(self,pop,par=None,cco=False,show_wait=True):
        # Take in a pop, or a pop and a par
        # Superimpose all curves affecting that quantity

        # First, get a list of all of the programs we are dealing with
        f,ax = pylab.subplots(1,1)

        if par is None: # Plot cost-coverage
            progs = [prog for prog in self.programs if pop in prog.cost_coverage.keys()]

            # Go through and plot coverage for all programs reaching this population
            x = numpy.linspace(0,5e6,100)
            for prog in progs:
                ax.plot(x,prog.get_coverage(pop,x),label=prog.name)
            ax.set_xlabel('Spending ($)')
            ax.set_ylabel('Coverage (fractional)')
        else:
            progs = [prog for prog in self.programs if (pop,par) in prog.get_effects()]
        
            if cco==False: # Plot coverage-outcome
                x = numpy.linspace(0,1,100)
                for prog in progs:
                    ax.plot(x,prog.get_outcome(pop,par,x),label=prog.name)
                ax.set_xlabel('Coverage (fractional)')
                ax.set_ylabel(par)
            else: # Plot cost-coverage-outcome
                x = numpy.linspace(0,5e6,100)
                for prog in progs:
                    cc = prog.get_coverage(pop,x)
                    ax.plot(x,prog.get_outcome(pop,par,cc),label=prog.name)
                ax.set_xlabel('Spending ($)')
                ax.set_ylabel(par)

        ax.legend(loc='lower right')

        if show_wait:
            pylab.show()

        return

    def progs_by_pop(self):
        # Return a dictionary where the keys are all of the populations
        # reached by the programs, and the values are lists of references 
        # to the programs reaching that population 
        # e.g., pops = {'FSW',[<Program 1a04>,<Program a351>]}

        pops = defaultdict(list)
        for prog in self.programs:
            pops_reached = prog.pops()
            for pop in pops_reached:
                pops[pop].append(prog)
        return pops

    def progs_by_effect(self,pop=None,filter_effect=None):
        # Like progs_by_pop, this function returns a dictionary 
        # like {'condomcas': [Program 6b39 (Condoms & SBCC)], u'hivtest': [Program b127 (HTC)]}
        # These are specific to the population provided as an input argument
        # If no population is specified, then (pop,program) tuples for the parameter are returned instead
        # EXTRA USAGE
        # If filter_effect is provided, then only the requested effect will be returned
        # e.g. pset.progs_by_effect('FSW','testing') might return [Program a2b6 (FSW programs), Program 430b (HTC)]
        effects = defaultdict(list)
        for prog in self.programs:
            prog_effects = prog.get_effects()
            for effect in prog_effects:
                if pop is None:
                    effects[effect[1]].append((effect[0],prog))
                elif effect[0] == pop: # If the effect applies to the selected population
                    effects[effect[1]].append(prog)

        if filter_effect is None:
            return effects
        else:
            return effects[filter_effect]

    def get_outcomes(self,tvec,budget,perturb=False):
        # An alloc is a vector of numbers for each program, that is subject to optimization
        # A budget is spending at a particular time, for each program
        # In the legacy code, we would say 
        #   budget = timevarying.timevarying(alloc)
        # 'tvec' should have a size corresponding to 'budget'
        # First, we need to know which populations to iterate over
        outcomes = dict()

        pops = self.progs_by_pop();

        for pop in pops.keys():
            progs_reaching_pop = pops[pop]

            # Now get the coverage for this program
            coverage = []
            for prog in progs_reaching_pop:
                spending = budget[self.programs.index(prog),:] # Get the amount of money spent on this program
                coverage.append(prog.get_coverage(pop,spending,t=tvec,perturb=perturb)) # Calculate the program's coverage

            # Next, get the list of effects to iterate over
            effects = self.progs_by_effect(pop) 

            #Now we iterate over the effects
            outcomes[pop] = dict()
            for effect in effects.keys():           
                if len(effects[effect]) == 1: # There is no overlapping of modalities
                    prog = effects[effect][0]
                    this_coverage = coverage[progs_reaching_pop.index(prog)] # Get the coverage that this program has for this population
                    assert(effect not in outcomes[pop].keys()) # Multiple programs should not be able to write to the same parameter *without* going through the overlapping calculation
                    outcomes[pop][effect] = prog.get_outcome(pop,effect,this_coverage,t=tvec,perturb=perturb) # Get the program outcome and store it in the outcomes dict
                else:
                    print 'OVERLAPPING MODALITIES DETECTED'
                    print 'Pop: %s Effect: %s' % (pop,effect)
                    print 'Programs ',[x.name for x in effects[effect]]
                    print
                    
                    # 'coverage' is an array matched to 'progs_reaching_pop'
                    # However, not all of those programs may target the parameter examined here
                    # So first, get the coverage and parameter value for each program in isolation
                    proglist = effects[effect] # Programs reaching this effect
                    this_coverage = [coverage[progs_reaching_pop.index(prog)] for prog in proglist] # Get the coverage that this program has for this population
                    this_outcome = [prog.get_outcome(pop,effect,cov,t=tvec,perturb=perturb) for (prog,cov) in zip(proglist,this_coverage)]

                    # Also, compute delta_out
                    delta_out = [prog.coverage_outcome[pop][effect].delta_out(tvec) for prog in proglist]

                    # DEBUG OUTPUT - these are the quantities needed for the calculation
                    print proglist
                    print this_coverage
                    print this_outcome
                    print delta_out

                    if pop in self.specific_reachability_interaction.keys() and effect in self.specific_reachability_interaction[pop].keys():
                        interaction = self.specific_reachability_interaction[pop][effect]
                    else:
                        interaction = self.default_reachability_interaction

                    # In the budget, rows correspond to programs, and columns to time
                    # Thus we have a sequence of row vectors that needs to be added
                    if interaction == 'random':
                        # Outcome = c1(1-c2)* delta_out1 + c2(1-c2)*delta_out2 + c1c2* max(delta_out1,delta_out2)
                        outcomes[pop][effect] = 0;
                    elif interaction == 'additive':
                        # Outcome = c1*delta_out1 + c2*delta_out2
                        outcomes[pop][effect] = numpy.sum(this_outcome,0);
                    elif interaction == 'nested':
                        # Outcome =c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
                        
                        # The items at each time need to be sorted
                        outcomes[pop][effect] = numpy.zeros(this_outcome[0].shape)
                        # Iterate over time
                        for i in xrange(0,len(tvec)):
                            o = 0
                            cov = [x[i] for x in this_coverage]
                            cov_tuple = sorted(zip(cov,delta_out)) # A tuple storing the coverage and delta out, ordered by coverage
                            print cov_tuple
                            for j in xrange(0,len(cov_tuple)): # For each entry in here
                                if j == 0:
                                    c1 = cov_tuple[j][0]
                                else:
                                    c1 = cov_tuple[j][0]-cov_tuple[j-1][0]
                                print 'ASDF', c1,numpy.max([x[1] for x in cov_tuple[j:]])
                                o += c1*numpy.max([x[1] for x in cov_tuple[j:]])
                            outcomes[pop][effect][i] = o

                    else:
                        raise Exception('Unknown reachability type "%s"',interaction)

        
        return outcomes

    def convert_units(self,output_outcomes,sim_output):
        # This function takes in a set of outcomes (generated by this program) and
        # simobject output e.g. sim_output = sim.run()
        # It iterates over the modalities to find coverage-type modalities
        # It then uses the population sizes in sim_output to convert nondimensional 
        # coverage into numbers of people
        # Currently not fully implemented
        return output_outcomes

    def __getitem__(self,name):
        # Support dict-style indexing based on name e.g.
        # programset.programs[1] might be the same as programset['MSM programs']
        for prog in self.programs:
            if prog.name == name:
                return prog
        print "Available programs:"
        print [prog.name for prog in self.programs]
        raise Exception('Program "%s" not found' % (name))

    def __repr__(self):
        return 'ProgramSet %s (%s)' % (liboptima.shortuuid(self.uuid),self.name)

class Program(object):
    # This class is a single modality - a single thing that 
    def __init__(self,name='Default',cc_inputs=[],co_inputs=[],nonhivdalys = 0):
        # THINGS THAT PROGRAMS HAVE
        # frontend quantities
        # functions
        # conversion from FE parameters to BE parameters

        # EXAMPLE INPUTS
        # cc_inputs[0] = dict()
        # cc_inputs[0]['pop'] = 'FSW'
        # cc_inputs[0]['form'] = 'cc_scaleup'
        # cc_inputs[0]['fe_params'] = {u'coveragelower': 0.2, u'nonhivdalys': 0.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.75, u'scaleup': 0.73}

        # co_inputs[0] = dict()
        # co_inputs[0]['pop'] = 'FSW'
        # co_inputs[0]['param'] = 'hivtest'
        # co_inputs[0]['form'] = 'co_cofun'
        # co_inputs[0]['fe_params'] = [0, 0, 2, 2]

        self.name = name        
        self.nonhivdalys = nonhivdalys
        self.uuid = str(uuid.uuid4())
        self.cost_coverage = dict()
        self.coverage_outcome = defaultdict(dict)

        assert(set([x['pop'] for x in cc_inputs]) == set([x['pop'] for x in co_inputs])) # A CC curve must be defined for every population that this program affects

        for cc in cc_inputs:
            cc_class = getattr(ccocs, cc['form']) # This is the class corresponding to the CC form e.g. it could be  a <ccocs.cc_scaleup> object
            assert(cc['pop'] not in self.cost_coverage.keys()) # Each program can only have one CC curve per population
            self.cost_coverage[cc['pop']] = cc_class(cc['fe_params']) # Instantiate it with the CC data, and append it to the program's CC array

        for co in co_inputs:
            co_class = getattr(ccocs, co['form'])
            if isinstance(co['param'],list): # Note that lists cannot be dictionary keys, so [u'condom', u'com'] -> 'condomcom'
                co['param'] = ''.join(co['param'])
            assert(co['pop'] not in self.coverage_outcome.keys() or co['param'] not in self.coverage_outcome[co['pop']].keys()) # Each program can only have one CO curve per effect
            self.coverage_outcome[co['pop']][co['param']] = co_class(co['fe_params']) # Instantiate it with the CC data, and append it to the program's CC array

    @classmethod
    def fromdict(Program,programdict):
        p = Program()
        p.name = programdict['name']
        p.nonhivdalys = programdict['nonhivdalys']
        p.uuid = programdict['uuid']
        for pop in programdict['cost_coverage'].keys():
            p.cost_coverage[pop] = ccocs.ccoc.fromdict(programdict['cost_coverage'][pop])
        for pop in programdict['coverage_outcome'].keys():
            for par in programdict['coverage_outcome'][pop].keys():
                p.coverage_outcome[pop][par] = ccocs.ccoc.fromdict(programdict['coverage_outcome'][pop][par])
        return p

    def todict(self):
        programdict = dict()
        programdict['name'] = self.name 
        programdict['nonhivdalys'] = self.nonhivdalys 
        programdict['uuid'] = self.uuid 
        programdict['cost_coverage'] = dict()
        programdict['coverage_outcome'] = defaultdict(dict)
        for pop in self.cost_coverage.keys():
            programdict['cost_coverage'][pop] = self.cost_coverage[pop].todict()
        for pop in self.coverage_outcome.keys():
            for par in self.coverage_outcome[pop].keys():
                programdict['coverage_outcome'][pop][par] = self.coverage_outcome[pop][par].todict()
        return deepcopy(programdict)

    def pops(self):
        # Return a list of populations covered by this program
        return [p for p in self.coverage_outcome.keys() if p is not None]

    def get_effects(self):
        # Returns a list of tuples storing effects as (population,parameter)
        effects = []
        for pop in self.pops():
            for param in self.coverage_outcome[pop].keys():
                effects.append((pop,param))
        return effects

    def get_coverage(self,pop,spending,t=None,perturb=False):
        # Return the coverage of a particular population given the spending amount
        return self.cost_coverage[pop].evaluate(spending,t=t,perturb=perturb)

    def get_outcome(self,pop,effect,coverage,t=None,perturb=False):
        # Return the outcome for a particular effect given the parent population's coverage
        if isinstance(effect,list):
            effect = ''.join(effect)
        return self.coverage_outcome[pop][effect].evaluate(coverage,t=t,perturb=perturb)

    def plot(self,sim=None,show_wait=True):
        # # This function will just plot everything
        # First, plot coverages
        # Then plot a column of outcomes
        # Then plot a column of coverage-outcomes

        # how many pops 
        n_pops = len(self.cost_coverage.keys())
        n_pars = sum([len(self.coverage_outcome[x].keys()) for x in self.cost_coverage.keys()])
        n_rows = max(n_pops,n_pars)

        if n_rows == 0:
            print 'Program %s is spending only' % (self.name)
            return

        # Set up the figure
        if self.cost_coverage.keys() == ['Overall']: # coverage program
            f, axarr = pylab.subplots(n_pops, 1,figsize=(24,16))
        else:
            f, axarr = pylab.subplots(n_rows, 3,figsize=(24,16))
        f.tight_layout()
        f.canvas.set_window_title(self.name)
        # f.set_size_inches(100,100)

        if not isinstance(axarr,numpy.ndarray): # A 1x1 subplot returns an axis, not a list of axes
            axarr = numpy.array([[axarr]])

        # Plot populations
        count = 0
        for pop in self.cost_coverage.keys():
            # Go down the first column
            self.plot_single(pop,ax=axarr[count,0],sim=sim,show_wait=False)
            count += 1

        # Delete extra rows
        while count < n_rows:
            f.delaxes(axarr[count,0])
            count += 1

        # If no effects, return now
        if axarr.shape[0] == 1:
            if show_wait:
                pylab.show()
            return

        # Next, plot the coverages and effects
        count = 0
        for pop in self.cost_coverage.keys():
            for par in self.coverage_outcome[pop].keys():
                self.plot_single(pop,par,cco=False,sim=sim,ax=axarr[count,1],show_wait=False)
                self.plot_single(pop,par,cco=True,sim=sim,ax=axarr[count,2],show_wait=False)
                count += 1

        if show_wait:
            pylab.show()

        return

    def plot_single(self,pop=None,par=None,cco=False,sim=None,show_wait=True,ax=None):
        # Make a single plot of one of the CCOC objects
        # USAGE
        # - specify a population and no par to see cost-coverage
        # - specify a population and an par to see coverage-outcome
        # - specify a population and an par and cco=True to see the CCO curve
        # The x and y values will be returned. Plot will be generated by default
        if ax is None:
            f,ax = pylab.subplots(1,1)

        if sim is not None:
            if not isinstance(sim,simbudget2.SimBudget2):
                raise Exception('You must provide a SimBudget2 to plot program data')

            # What is the index of this program in the alloc/budget?
            p = sim.getproject()

            if not sim.isinitialised():
                sim.initialise()

            prog_list = [a.name for a in sim.getprogramset().programs]
            if self.name not in prog_list:
                sim = None
                cost_x_limit = self.cost_coverage[pop].xlims()[1]
            else:
                prog_index = [a.name for a in sim.getprogramset().programs].index(self.name)
                prog_start_index = numpy.argmin(numpy.abs(sim.program_start_year-sim.default_pars['tvec'])) if numpy.isfinite(sim.program_start_year) else None
                prog_end_index = numpy.argmin(numpy.abs(sim.program_end_year-sim.default_pars['tvec'])) if numpy.isfinite(sim.program_end_year) else None
                datacost = p.data['ccocs'][self.name]['cost']
                cost_x_limit = max(2*max(sim.budget[prog_index,:]),2*numpy.nanmax(datacost),self.cost_coverage[pop].xlims()[1])
                if pop != 'Overall':
                    popnumber = [a['short_name'] for a in p.metadata['inputpopulations']].index(pop)
        else:
            cost_x_limit = self.cost_coverage[pop].xlims()[1]

        if par is None:
            x_limit = cost_x_limit

            # And then plot the CC curve
            x = numpy.linspace(0,x_limit,100)
            y = self.cost_coverage[pop].evaluate(x) 
            yl = self.cost_coverage[pop].evaluate(x,bounds='lower') 
            yu = self.cost_coverage[pop].evaluate(x,bounds='upper') 

            if sim is not None:
                # Get the program data
                datacost = p.data['ccocs'][self.name]['cost']
                datacoverage = get_data_coverage(self.name,pop,sim)
                ax.scatter(datacost,datacoverage,color='#666666',zorder=8)

                # What is the alloc for this program?
                # Let's go with the upper and lower bounds of the budget for this program
                if prog_start_index is not None:
                    ax.axvline(x=sim.budget[prog_index,prog_start_index], color='red',zorder=9)
                if prog_end_index is not None:
                    ax.axvline(x=sim.budget[prog_index,prog_end_index], color='blue',zorder=8)


        elif not cco:  
            # coverage-outcome plot
            x_limit = 1          
            x = numpy.linspace(0,x_limit,100)
            y = self.coverage_outcome[pop][par].evaluate(x) # plot coverage-outcome
            yl = self.coverage_outcome[pop][par].evaluate(x,bounds='lower') 
            yu = self.coverage_outcome[pop][par].evaluate(x,bounds='upper') 

            if sim is not None:
                # First, get the outcome and coverage
                # First, find the population index
                dataoutcome = get_data_outcome(pop,par,sim)

                if len(dataoutcome) == 1:
                    ax.axhline(dataoutcome[0], color='#666666',zorder=8)
                else:
                    datacoverage = get_data_coverage(self.name,pop,sim)
                    ax.scatter(datacoverage,dataoutcome,color='#666666',zorder=8)

                if prog_start_index is not None:
                    ax.axvline(x=self.cost_coverage[pop].evaluate(sim.budget[prog_index,prog_start_index]), color='red',zorder=9)
                    if pop == 'Overall':
                        ax.axhline(y=sim.popsizes['Overall'][prog_start_index], color='red',zorder=9)
                    else:
                        ax.axhline(y=sim.default_pars[par][popnumber,prog_start_index], color='red',zorder=9)

                if prog_end_index is not None:
                    ax.axvline(x=self.cost_coverage[pop].evaluate(sim.budget[prog_index,prog_end_index]), color='blue',zorder=8)
                    if pop == 'Overall':
                        ax.axhline(y=sim.popsizes['Overall'][prog_end_index], color='red',zorder=9)
                    else:
                        ax.axhline(y=sim.default_pars[par][popnumber,prog_end_index], color='blue',zorder=9)

        else:
            x_limit = cost_x_limit

            x = numpy.linspace(0,x_limit,100)
            cc = self.cost_coverage[pop].evaluate(x)
            ccl = self.cost_coverage[pop].evaluate(x,bounds='lower') 
            ccu =self.cost_coverage[pop].evaluate(x,bounds='upper') 
            y = self.coverage_outcome[pop][par].evaluate(cc)
            yl = self.coverage_outcome[pop][par].evaluate(ccl,bounds='lower') 
            yu =self.coverage_outcome[pop][par].evaluate(ccu,bounds='upper') 

            if sim is not None:
                datacost = p.data['ccocs'][self.name]['cost']
                dataoutcome = get_data_outcome(pop,par,sim)
                if len(dataoutcome) == 1:
                    ax.axhline(dataoutcome[0], color='#666666',zorder=8)
                else:
                    ax.scatter(datacost,dataoutcome,color='#666666',zorder=8)


                if par in sim.default_pars:

                    def overlay_scatters(index,color,order):
                        spending_at_time = sim.budget[prog_index,index]
                        datapar_at_time = sim.default_pars[par][popnumber,index]
                        cc_at_time = self.cost_coverage[pop].evaluate(spending_at_time)
                        modelpar_at_time = self.coverage_outcome[pop][par].evaluate(cc_at_time)
                        ax.axvline(spending_at_time, color=color,zorder=order)
                        ax.axhline(datapar_at_time, color=color,zorder=order)
                        # ax.scatter([spending_at_time,spending_at_time],[datapar_at_time,modelpar_at_time],color=color,zorder=order)

                    if prog_start_index is not None:
                        overlay_scatters(prog_start_index,'red',9)
                    if prog_end_index is not None:
                        overlay_scatters(prog_end_index,'blue',8)

                else:
                    if prog_start_index is not None:
                        ax.axvline(sim.budget[prog_index,prog_start_index], color='red',zorder=9)
                    if prog_end_index is not None:
                        ax.axvline(sim.budget[prog_index,prog_stop_index], color='blue',zorder=8)



        ax.plot(x,y,linestyle='-',color='#a6cee3',linewidth=2)
        ax.plot(x,yl,linestyle='--',color='#000000',linewidth=2)
        ax.plot(x,yu,linestyle='--',color='#000000',linewidth=2)
        ax.set_xlim([0,x_limit])

        if par is None:
            ax.set_xlabel('Spending ($)')
            ax.set_ylabel('Coverage (fractional)')
            ax.set_title(pop)
            ax.set_ylim([0,1])
        elif not cco:
            ax.set_xlabel('Coverage (fractional)')
            ax.set_ylabel(par)
            ax.set_title(pop+'-'+par)
        else:
            ax.set_xlabel('Spending ($)')
            ax.set_ylabel(par)
            ax.set_title(pop+'-'+par)

        if show_wait:
            pylab.show()

    def __repr__(self):
        return 'Program %s (%s)' % (liboptima.shortuuid(self.uuid),self.name)

def get_data_coverage(progname,targetpop,sim):
    p = sim.getproject()

    datacoverage = p.data['ccocs'][progname]['coverage']
    epiyears = p.data['epiyears'] # The corresponding years

    if len(datacoverage)==1:
        datacoverage = datacoverage*numpy.ones(epiyears.shape)

    # Rescale the coverage according to the population size estimate
    if numpy.any(datacoverage > 1): # Only rescale if not percentages
        for i in range(len(datacoverage)): 
            if numpy.isfinite(datacoverage[i]):
                matching_index = numpy.argmin(numpy.abs(epiyears[i]-sim.popsizes['tvec']))
                datacoverage[i] /= sim.popsizes[targetpop][matching_index]

    return datacoverage

def get_data_outcome(pop,par,sim):
    p = sim.getproject()
    popnumber = [a['short_name'] for a in p.metadata['inputpopulations']].index(pop)

    # Now, find the data for this program
    for partype in p.data.keys():
        if par in p.data[partype]:
            dataoutcome = p.data[partype][par][popnumber]
            return dataoutcome

    raise Exception('Parameter %s not found' % (par))
