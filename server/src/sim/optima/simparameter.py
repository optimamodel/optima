import sim 
from sim import Sim
import numpy
import programset
from liboptima.utils import findinds
from numpy import arange 
from copy import deepcopy

# Derived Sim class that should store parameter overwrites.
class SimParameter(Sim):
    def __init__(self, name, project, calibration = None):
        Sim.__init__(self, name, project, calibration)
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
            r = self.getproject()
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
        r = self.getproject()
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


        
def calculate_totalacts(M):
    eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero

    popsize = M['popsize']
    pships = M['pships']
    numacts = dict()
    numacts['reg'] = M['numactsreg']
    numacts['cas'] = M['numactscas']
    numacts['com'] = M['numactscom']
    numacts['inj'] = M['numactsinj']

    totalacts = dict()
    npts = popsize.shape[1]

    for act in pships.keys():
        npops = len(popsize[:,0])
        npop=len(popsize); # Number of populations
        mixmatrix = pships[act]
        symmetricmatrix=zeros((npop,npop));
        for pop1 in xrange(npop):
            for pop2 in xrange(npop):
                symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))

        a = zeros((npops,npops,npts))
        numact = numacts[act]
        for t in xrange(npts):
            a[:,:,t] = reconcileacts(symmetricmatrix.copy(), popsize[:,t], numact[:,t]) # Note use of copy()

        totalacts[act] = a
    
    return totalacts

def reconcileacts(symmetricmatrix,popsize,popacts):
    eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero

    # Make sure the dimensions all agree
    npop=len(popsize); # Number of populations

    for pop1 in xrange(npop):
        symmetricmatrix[pop1,:]=symmetricmatrix[pop1,:]*popsize[pop1];

    # Divide by the sum of the column to normalize the probability, then
    # multiply by the number of acts and population size to get total number of
    # acts
    for pop1 in xrange(npop):
        symmetricmatrix[:,pop1]=popsize[pop1]*popacts[pop1]*symmetricmatrix[:,pop1] / float(eps+sum(symmetricmatrix[:,pop1]))

    # Reconcile different estimates of number of acts, which must balance
    pshipacts=zeros((npop,npop));
    for pop1 in xrange(npop):
        for pop2 in xrange(npop):
            balanced = (symmetricmatrix[pop1,pop2] * popsize[pop1] + symmetricmatrix[pop2,pop1] * popsize[pop2])/(popsize[pop1]+popsize[pop2]); # here are two estimates for each interaction; reconcile them here
            pshipacts[pop2,pop1] = balanced/popsize[pop2]; # Divide by population size to get per-person estimate
            pshipacts[pop1,pop2] = balanced/popsize[pop1]; # ...and for the other population

    return pshipacts
