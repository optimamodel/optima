import sim 
from sim import Sim
import numpy
import programset
from liboptima.utils import findinds
from numpy import arange 
from copy import deepcopy
import operator
from timevarying import timevarying

# todo: default_pars should be stored in the calibration

class SimBudget2(Sim):

    def __init__(self,name,project,budget=None,calibration=None,programset=None):
        # programset and calibration are UUIDs
        Sim.__init__(self, name, project,calibration)

        if budget is None: # Use data alloc
            budget = project.data['origalloc']

        if len(budget.shape)==1: # User probably put in an alloc
            budget = timevarying(budget,nprogs=len(budget), tvec=project.options['partvec'], totalspend=sum(budget))

        self.budget = budget # This contains spending values for all of the modalities for the simulation timepoints i.e. there are len(D['opt']['partvec']) spending values
        
        self.programset = programset
        if self.programset is None and len(project.programsets) > 0:
            self.programset = project.programsets[0].uuid

        self.popsizes = {} # Estimates for the population size obtained by running a base Sim within the parent project
        self.default_pars = {}

        # Check that the program set exists
        if programset is not None and self.programset not in [x.uuid for x in project.programsets]:
            raise Exception('The provided program set UUID could not be found in the provided project')

        # The CCOCs will be used between the years specified here 
        self.program_start_year = 2015
        self.program_end_year = numpy.inf

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget2'
        simdict['budget'] = self.budget
        simdict['programset'] = self.programset
        simdict['popsizes'] = self.popsizes
        simdict['default_pars'] = self.default_pars
        simdict['program_start_year'] = self.program_start_year 
        simdict['program_end_year'] = self.program_end_year 
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.budget = simdict['budget'] 
        self.programset = simdict['programset']
        self.programset = simdict['programset']
        self.popsizes = simdict['popsizes']
        self.default_pars = simdict['default_pars']
        self.program_start_year = simdict['program_start_year']
        self.program_end_year = simdict['program_end_year']

    def getprogramset(self):
        # Return a reference to the selected program set
        r = self.getproject()
        uuids = [x.uuid for x in r.programsets]
        return r.programsets[uuids.index(self.programset)]

    def get_estimated_popsizes(self,artindex=None):
        # This function populates self.popsizes which is used in self.makemodelpars() to convert
        # fractions of populations (coverage) into actual numbers of people
        # This function generates a dict like {'FSW':[1 1.1 1.2...],'....'} where the keys are different
        # population breakdowns, and the values are arrays of number of people for each time in 
        # project.options['partvec']
        #
        # Available populations are
        #   - All of the populations listed in r.metadata['inputpopulations'] (access by short name)
        #   - total
        # And then the numbers of people potentially reached by the following program names
        #   - aidstest, numost, sharing, numpmtct, breast, numfirstline, numsecondline, numcircum

        self.popsizes = {}
        r = self.getproject()
        s = Sim('temp',r,self.calibration) # Make a base sim with the selected calibration
        DS = s.run()[0] # Retrieve D.S
        people = DS['people']

        # Define indexes for various breakdowns
        pops = [x['short_name'] for x in r.metadata['inputpopulations']]
        injects = numpy.array([x['injects'] for x in r.metadata['inputpopulations']])
        ismale  = numpy.array([x['male'] for x in r.metadata['inputpopulations']])
        aidstested = numpy.array(range(27,31)) # WARNING - this assumes particular indexes for the relevant health states!
        if artindex is None:
            artindex = range(1,r.metadata['nstates']) # Choose a sensible default here - here it is all states except the first

        # Calculate the population sizes
        for i in xrange(len(pops)): # Iterate over the populations
            self.popsizes[pops[i]] = people[:,i,:].sum(axis=(0))

        self.popsizes['total'] = people.sum(axis=(0,1)) # This should be removed in favour of using Overall
        self.popsizes['Overall'] = people.sum(axis=(0,1)) # This popsize is used for programs affecting all populations
        self.popsizes['aidstest'] = people[aidstested,:,:].sum(axis=(0,1)) 
        self.popsizes['numost'] = people[:,injects,:].sum(axis=(0,1))
        self.popsizes['sharing'] = self.popsizes['numost']
        self.popsizes['numpmtct'] = numpy.cumsum(numpy.multiply(s.parsmodel['birth'][:,:]*r.options['dt'], people[artindex,:,:].sum(axis=0)).sum(axis=0))
        self.popsizes['breast'] = numpy.multiply(s.parsmodel['birth'][:,:], s.parsmodel['breast'][:], people[artindex,:,:].sum(axis=0)).sum(axis=0)
        self.popsizes['numfirstline'] = people[artindex,:,:].sum(axis=(0,1))
        self.popsizes['numsecondline'] = self.popsizes['numfirstline']
        self.popsizes['numcircum'] = people[:,ismale,:].sum(axis = (0,1))
        self.popsizes['tvec'] = deepcopy(DS['tvec'])

        # Store the parameters so they can be superimposed on plots
        self.default_pars = s.parsmodel

    def makemodelpars(self,perturb=False):
        # The programs will be used to overwrite the parameter values for times between program_start_year and program_end_year

        # If perturb == True, then a random perturbation will be applied at the CCOC level
        r = self.getproject()
        self.makedatapars() # Construct the data pars

        # First, set self.parsmodel as though this was a base sim
        # This assigns parts of self.parsmodel from the calibration
        # Specifically, these are the parts of self.parsmodel that do not go through
        # dpar2mpar - popsize,hivprev,pships,transit,totalacts,propaware,txtotal
        Sim.makemodelpars(self) # First, set self.parsmodel as though this was a base sim 

        # Calculate self.popsizes if it has not already been calculated
        # This calculation should persist if used in a loop
        if not self.popsizes:  
            self.get_estimated_popsizes()

        # Get the parameter values from the CCOCs
        progs = self.getprogramset()
        outcomes = progs.get_outcomes(r.options['partvec'],self.budget,perturb)

        # Declare a helper function to convert population names into array indexes
        pops = [x['short_name'] for x in r.metadata['inputpopulations']]
        popnumber = lambda s: pops.index(s)
        npops = len(pops)
        npts = len(r.options['partvec'])

        # TODO - fix these parameter names
        self.parsmodel['numfirstline'] = self.parsmodel['tx1']            
        self.parsmodel['numsecondline'] = self.parsmodel['tx2']     

        # First check - all of the parameters and populations provided by the ProgramSet should exist
        outcome_pops = set(outcomes.keys()) 
        outcome_pars = set(reduce(operator.add,[outcomes[x].keys() for x in outcomes.keys()],[]))
        project_pops = set(pops + ['Overall']) # Manually add the special population 'Total'
        project_pars = set(self.parsmodel.keys())

        if not (outcome_pops <= project_pops):
            print "Warning - outcomes exist for populations that are not in the Project: ", outcome_pops - project_pops

        if not (outcome_pars <= project_pars):
            print "Warning - outcomes exist for parameters that are not in the Project: ", outcome_pars - project_pars

        # Now we overwrite the data parameters (computed via Sim.makemodelpars()) with program values
        # if the program specified the parameter value
        update_indexes = numpy.logical_and(r.options['partvec']>self.program_start_year, r.options['partvec']<self.program_end_year) # This does the same thing as partialupdateM
        
        # First, assign population-dependent parameters
        # TODO: Invert the loop to iterate over the intersection of the project parameters
        # and program parameters - that way it will behave sensibly if there is a mismatch
        for par in ['hivprev','stiprevulc','stiprevdis','death','tbprev','hivtest','birth','numactsreg','numactscas','numactscom','numactsinj','condomreg','condomcas','condomcom','circum','sharing','prep']:
            for pop in pops:
                if pop in outcomes.keys() and par in outcomes[pop].keys():
                    if par in programset.coverage_params: 
                        # If this is a coverage par, rescale it by population size - note that all coverage pars have
                        # had a specific popsize calculated in self.get_estimated_popsizes
                        # Hence popsizes is queried by parameter, rather than population
                        self.parsmodel[par][popnumber(pop),update_indexes] = outcomes[pop][par][update_indexes]*self.popsizes[par][update_indexes]
                    else:
                        self.parsmodel[par][popnumber(pop),update_indexes] = outcomes[pop][par][update_indexes]

        # Next, assign total (whole project) parameters
        for par in ['aidstest','numfirstline','numsecondline','txelig','numpmtct','breast','numost','numcircum']:
            if par in outcomes['Overall']: # This string should match the conversion in ProgramSet.import_legacy()
                if par in programset.coverage_params: 
                    self.parsmodel[par][update_indexes] = outcomes['Overall'][par][update_indexes]*self.popsizes[par][update_indexes]
                else:
                    self.parsmodel[par][update_indexes] = outcomes['Overall'][par][update_indexes]

        # Finally, realculate totalacts in case numacts is different now for some reason
        self.parsmodel['totalacts'] = sim.calculate_totalacts(self.parsmodel)

        # FINALLY, APPLY SOME HACKS THAT NEED TO BE CLEANED UP

        # TODO - fix these parameter names
        self.parsmodel['tx1'] = self.parsmodel['numfirstline']
        self.parsmodel['tx2'] = self.parsmodel['numsecondline']
        
        # And remove the temporary keys
        del self.parsmodel['numfirstline']
        del self.parsmodel['numsecondline']
       
        # Hideous hack for ART to use linear unit cost
        #try:
        from liboptima.utils import sanitize
        artind = r.data['meta']['progs']['short'].index('ART')
        currcost = sanitize(r.data['costcov']['cost'][artind])[-1]
        currcov = sanitize(r.data['costcov']['cov'][artind])[-1]
        unitcost = currcost/currcov
        self.parsmodel['tx1'].flat[update_indexes] = self.budget[:,1][artind]/unitcost
        #except:
        #    print('Attempt to calculate ART coverage failed for an unknown reason')
        
    def __repr__(self):
        return "SimBudget2 %s ('%s')" % (self.uuid,self.name)  
