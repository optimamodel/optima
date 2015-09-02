from sim import Sim
import numpy
import programset
from utils import findinds
from numpy import arange 
from copy import deepcopy

class SimBudget2(Sim):

    def __init__(self, name, region,budget,calibration=None,programset=None):
        Sim.__init__(self, name, region,calibration)
        self.budget = budget # This contains spending values for all of the modalities for the simulation timepoints i.e. there are len(D['opt']['partvec']) spending values
        self.programset = programset if programset is not None else region.programsets[0].uuid # Use the first program set by default
        self.popsizes = {} # Estimates for the population size obtained by running a base Sim within the parent region

        # Check that the program set exists
        if self.programset not in [x.uuid for x in region.programsets]:
            raise Exception('The provided program set UUID could not be found in the provided region')

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget2'
        simdict['budget'] = self.budget
        simdict['programset'] = self.programset
        simdict['popsizes'] = self.popsizes
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.budget = simdict['budget'] 
        self.programset = simdict['programset']
        self.programset = simdict['programset']
        self.popsizes = simdict['popsizes']

    def getprogramset(self):
        # Return a reference to the selected program set
        r = self.getregion()
        uuids = [x.uuid for x in r.programsets]
        return r.programsets[uuids.index(self.programset)]

    def get_estimated_popsizes(self,artindex=None):
        # This function populates self.popsizes which is used in self.makemodelpars() to convert
        # fractions of populations (coverage) into actual numbers of people
        # This function generates a dict like {'FSW':[1 1.1 1.2...],'....'} where the keys are different
        # population breakdowns, and the values are arrays of number of people for each time in 
        # region.options['partvec']
        #
        # Available populations are
        #   - All of the populations listed in r.metadata['inputpopulations'] (access by short name)
        #   - total
        # And then the numbers of people potentially reached by the following program names
        #   - aidstest, numost, sharing, numpmtct, breast, numfirstline, numsecondline, numcircum

        self.popsizes = {}
        r = self.getregion()
        s = Sim('temp',r,self.calibration) # Make a base sim with the selected calibration
        DS = s.run() # Retrieve D.S
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

        self.popsizes['total'] = people.sum(axis=(0,1))
        self.popsizes['aidstest'] = people[aidstested,:,:].sum(axis=(0,1)) 
        self.popsizes['numost'] = people[:,injects,:].sum(axis=(0,1))
        self.popsizes['sharing'] = self.popsizes['numost']
        self.popsizes['numpmtct'] = numpy.cumsum(numpy.multiply(s.parsmodel['birth'][:,:]*r.options['dt'], people[artindex,:,:].sum(axis=0)).sum(axis=0))
        self.popsizes['breast'] = numpy.multiply(s.parsmodel['birth'][:,:], s.parsmodel['breast'][:], people[artindex,:,:].sum(axis=0)).sum(axis=0)
        self.popsizes['numfirstline'] = people[artindex,:,:].sum(axis=(0,1))
        self.popsizes['numsecondline'] = self.popsizes['numfirstline']
        self.popsizes['numcircum'] = people[:,ismale,:].sum(axis = (0,1))

    def makemodelpars(self,perturb=False,program_start_year=2015,program_end_year=numpy.inf):
        # The programs will be used to overwrite the parameter values for times between program_start_year and program_end_year

        # If perturb == True, then a random perturbation will be applied at the CCOC level
        r = self.getregion()
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
        outcomes = progs.get_outcomes(self.budget,perturb)

        # Declare a helper function to convert population names into array indexes
        pops = [x['short_name'] for x in r.metadata['inputpopulations']]
        popnumber = lambda s: pops.index(s)
        npops = len(pops)
        npts = len(r.options['partvec'])

        # Now we overwrite the data parameters (computed via Sim.makemodelpars()) with program values
        # if the program specified the parameter value

        # TODO - fix these parameter names
        self.parsmodel['numfirstline'] = self.parsmodel['tx1']            
        self.parsmodel['numsecondline'] = self.parsmodel['tx2']            
        self.parsmodel['numactsreg'] = self.parsmodel['numacts']['reg'] 
        self.parsmodel['numactscas'] = self.parsmodel['numacts']['cas'] 
        self.parsmodel['numactscom'] = self.parsmodel['numacts']['com'] 
        self.parsmodel['numactsinj'] = self.parsmodel['numacts']['inj'] 
        self.parsmodel['condomreg'] = self.parsmodel['condom']['reg']  
        self.parsmodel['condomcas'] = self.parsmodel['condom']['cas']  
        self.parsmodel['condomcom'] = self.parsmodel['condom']['com']  

        update_indexes = numpy.logical_and(r.options['partvec']>program_start_year, r.options['partvec']<program_end_year) # This does the same thing as partialupdateM

        # First, assign population-dependent parameters
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

        # Next, assign total (whole region) parameters
        for par in ['aidstest','numfirstline','numsecondline','txelig','numpmtct','breast','numost','numcircum']:
            if par in outcomes['Total']:
                if par in programset.coverage_params: 
                    self.parsmodel[par][update_indexes] = outcomes['Total'][par][update_indexes]*self.popsizes[par][update_indexes]
                else:
                    self.parsmodel[par][update_indexes] = outcomes['Total'][par][update_indexes]

        # FINALLY, APPLY SOME HACKS THAT NEED TO BE CLEANED UP

        # TODO - fix these parameter names
        self.parsmodel['tx1'] = self.parsmodel['numfirstline']
        self.parsmodel['tx2'] = self.parsmodel['numsecondline']
        self.parsmodel['numacts']['reg'] = self.parsmodel['numactsreg']
        self.parsmodel['numacts']['cas'] = self.parsmodel['numactscas']
        self.parsmodel['numacts']['com'] = self.parsmodel['numactscom']
        self.parsmodel['numacts']['inj'] = self.parsmodel['numactsinj']
        self.parsmodel['condom']['reg']  = self.parsmodel['condomreg'] 
        self.parsmodel['condom']['cas']  = self.parsmodel['condomcas'] 
        self.parsmodel['condom']['com']  = self.parsmodel['condomcom'] 

        # And remove the temporary keys
        del self.parsmodel['numfirstline']
        del self.parsmodel['numsecondline']
        del self.parsmodel['numactsreg']
        del self.parsmodel['numactscas']
        del self.parsmodel['numactscom']
        del self.parsmodel['numactsinj']
        del self.parsmodel['condomreg'] 
        del self.parsmodel['condomcas'] 
        del self.parsmodel['condomcom'] 
       
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
        
    def __repr__(self):
        return "SimBudget2 %s ('%s')" % (self.uuid,self.name)  
