import weakref
import uuid
import defaults
from copy import deepcopy
from numpy import array, isnan, zeros, shape, mean
from liboptima.utils import sanitize, printv
from numpy import zeros, array, exp, shape

class Sim(object):
    def __init__(self, name, project, calibration = None):
        self.name = name
        self.initialised = False    # This tag monitors if the simulation has been initialised.        
        self.processed = False      # This tag monitors if the simulation has been run.
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality

        self.parsdata = None        # This used to be D['P'].
        self.parsmodel = None       # This used to be D['M'].
        self.parsfitted = None      # This used to be D['F'].
        self.calibration = calibration if calibration is not None else project.calibrations[0]['uuid'] # Use the first project calibration by default - could reorder the project's calibrations to choose a default later

        # Check the calibration exists
        if self.calibration not in [x['uuid'] for x in project.calibrations]:
            raise Exception('The provided calibration UUID could not be found in the provided project')

        self.debug = {}             # This stores the (large) output from running the simulation
        self.debug['results'] = None         # This used to be D['R'].
        self.debug['structure'] = None       # This used to be D['S'].
        
        self.plotdata = None        # This used to be D['plot']['E']. Be aware that it is not D['plot']!        
        self.setproject(project)

    @classmethod
    def fromdict(Sim,simdict,project):
        # This function instantiates the correct subtype based on simdict['type']
        assert(simdict['project_uuid'] == project.uuid)
        sim_type = globals()[simdict['type']]
        s = sim_type(simdict['name'],project)
        s.setproject(project)
        s.load_dict(simdict)
        return s

    def load_dict(self,simdict):
        self.initialised = simdict['initialised']
        self.processed  = simdict['processed']  
        self.parsdata  = simdict['parsdata']  
        self.parsmodel  = simdict['parsmodel']  
        self.parsfitted  = simdict['parsfitted']  
        self.debug  = simdict['debug']   
        self.plotdata  = simdict['plotdata']  
        self.uuid = simdict['uuid']
        try:
            self.calibration = simdict['calibration']
        except: 
            print 'WARNING! Calibration was not saved in json file'
            self.calibration = None

    def todict(self):
        # Guard against temporary Sims being passed around via regions or being saved to files
        if not isinstance(self.project,weakref.ref):
            raise Exception('You cannot save a Sim that has been turned into a standalone simulation')

        simdict = {}
        simdict['type'] = 'Sim'
        simdict['name'] = self.name
        simdict['initialised']  = self.initialised
        simdict['processed']  = self.processed 
        simdict['parsdata']  = self.parsdata 
        simdict['parsmodel']  = self.parsmodel 
        simdict['parsfitted']  = self.parsfitted 
        simdict['debug']   = self.debug 
        simdict['plotdata']  = self.plotdata 
        simdict['project_uuid'] = self.getproject().uuid
        simdict['uuid'] = self.uuid
        simdict['calibration'] = self.calibration
        return simdict
    
    def setproject(self,project):
        self.project = weakref.ref(project)

    def getproject(self):
        # self.project is a weakref object, which means to get
        # the project you need to do self.project() rather than
        # self.project. This function abstracts away this 
        # implementation detail in case it changes in future
        if isinstance(self.project,weakref.ref):
            r = self.project()
            if r is None:
                raise Exception('The parent project has been garbage-collected and the reference is no longer valid.')
            else:
                return r
        else:
            return self.project

    def make_standalone_copy(self):
        # I'm not entirely happy about this function
        # The problem is when you want to do a parallel optimization, you need to 
        # run a multiprocessing pool inside a *simbox*, and it makes no sense to 
        # pass the entire parent region around. But a weakref cannot be pickled
        # So this function should STRICTLY only be used for TEMPORARY Sims that
        # need to be passed into a multiprocessing loop/pool

        # First, get a normal copy
        s2 = self.duplicate()

        # Now, tweak the project contained within the copy        
        s2.project = deepcopy(s2.getproject())
        s2.project.simboxlist = list() # delete the simboxlist to try and save a bit of space
        s2.project.calibrations = [x for x in s2.project.calibrations if x['uuid'] == s2.calibration] # Keep only the calibration being used
        return s2

    def duplicate(self):
        # Return a deep-copied new Sim that is the same as the current Sim, but with a new UUID 
        simdict = self.todict()
        s2 = Sim.fromdict(simdict,self.getproject())
        s2.uuid = str(uuid.uuid4())
        return s2

    def getcalibration(self):
        # Return a deepcopy of the selected calibration
        r = self.getproject()
        uuids = [x['uuid'] for x in r.calibrations]
        idx = uuids.index(self.calibration)
        return deepcopy(r.calibrations[idx])

    def setname(self, name):
        self.name = name
        
    def getname(self):
        return self.name
    
    def isinitialised(self):
        return self.initialised   
    
    def isprocessed(self):
        return self.processed
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
    def initialise(self, forcebasicmodel = False):
        r = self.getproject()
        calibration = self.getcalibration()

        from makedatapars import makedatapars
        from numpy import arange

        # Explicit construction of tempD, so that one day we know how to recode makedatapars.
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        tempD['G']['datayears'] = arange(r.metadata['datastart'], r.metadata['dataend']+1)
        tempD['G']['npops'] = len(r.metadata['populations'])
        tempD['G']['nprogs'] = len(r.metadata['programs'])

        self.makedatapars()
        
        # Sometimes you'll want derived Sim classes to use Sim's basic makemodelpars function. Turn on forcebasicmodel for that.
        if forcebasicmodel:
            Sim.makemodelpars(self)
        else:
            self.makemodelpars()

        self.parsfitted = calibration['metaparameters']
        self.initialised = True

    def makedatapars(self, verbose=2):
        # This method creates self.parsdata
        # parsdata is *intended* to only store things with D.P.T and D.P.C
        r = self.getproject() 
        calibration = self.getcalibration()

        ## Preliminaries
        
        def data2par(dataarray, project, usetime=True):
            """ Take an array of data and turn it into default parameters -- here, just take the means """
            nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
            output = dict() # Create structure
            output['p'] = [0]*nrows # Initialize array for holding population parameters
            if usetime:
                output['t'] = [0]*nrows # Initialize array for holding time parameters
                for n in xrange(nrows): 
                    validdata = ~isnan(dataarray[n])
                    if sum(validdata): # There's at least one data point
                        output['p'][n] = sanitize(dataarray[n]) # Store each extant value
                        output['t'][n] = project.metadata['datayears'][~isnan(dataarray[n])] # Store each year
                    else: # Blank, assume zero
                        output['p'][n] = array([0])
                        output['t'][n] = array([0])

            else:
                print('TMP6666')
                for r in xrange(nrows): 
                    output['p'][r] = mean(sanitize(dataarray[r])) # Calculate mean for each population
                    print('TMP223')
            
            return output

        ## Loop over quantities
        self.parsdata = dict() # Initialize parameters structure
        
        ## Key parameters - These were hivprev and pships, and are now in the calibration

        ## Loop over parameters that can be converted automatically
        for parclass in ['epi', 'txrx', 'sex', 'inj']:
            printv('Converting data parameter %s...' % parclass, 3, verbose)
            for parname in r.data[parclass].keys():
                printv('Converting data parameter %s...' % parname, 4, verbose)
                if parname in ['numfirstline','numsecondline','txelig']:
                    self.parsdata[parname] = data2par(r.data[parclass][parname], r, usetime=True)
                else:
                    self.parsdata[parname] = data2par(r.data[parclass][parname], r, usetime=True) # TMP
        
        ## Add a data parameter for number circumcised, if VMMC is a program
        if 'VMMC' in [p['name'] for p in r.metadata['programs']]:
            printv('Making a data parameter for numcircum', 2, verbose)
            prognumber = [p['name'] for p in r.metadata['programs']].index('VMMC')
            self.parsdata['numcircum'] = data2par([r.data['costcov']['cov'][prognumber]], r, usetime=True)        
        
        ## Change sizes of circumcision and births
        def popexpand(origarray, popbool):
            """ For variables that are only defined for certain populations, expand to the full array. WARNING, doesn't work for time """
            from copy import deepcopy
            newarray = deepcopy(origarray)
            if 't' in newarray.keys(): 
                newarray['p'] = [array([0]) for i in xrange(len(r.data['meta']['pops']['male']))]
                newarray['t'] = [array([0]) for i in xrange(len(r.data['meta']['pops']['male']))]
                count = -1
                if hasattr(popbool,'__iter__'): # May or may not be a list
                    for i,tf in enumerate(popbool):
                        if tf:
                            count += 1
                            newarray['p'][i] = origarray['p'][count]
                            newarray['t'][i] = origarray['t'][count]
            else: 
                newarray['p'] = zeros(shape(r.data['meta']['pops']['male']))
                count = -1
                if hasattr(popbool,'__iter__'): # May or may not be a list
                    for i,tf in enumerate(popbool):
                        if tf:
                            count += 1
                            newarray['p'][i] = origarray['p'][count]
            
            return newarray
        
        self.parsdata['birth']     = popexpand(self.parsdata['birth'],     array(r.data['meta']['pops']['female'])==1)
        self.parsdata['circum']    = popexpand(self.parsdata['circum'],    array(r.data['meta']['pops']['male'])==1)
                
        printv('...done converting data to parameters.', 2, verbose)

    def makemodelpars(self):
        # SimParameter, SimBudget and SimCoverage differ in how they calculate D.M
        # but are otherwise almost identical. Thus this is the function that is
        # expected to be re-implemented in the derived classes
        r = self.getproject()
        calibration = self.getcalibration()

        opt = r.options
        withwhat = 'p'

        M = dict()
        M['tvec'] = r.options['partvec'] # Store time vector with the model parameters
        npts = len(M['tvec']) # Number of time points # TODO probably shouldn't be repeated from model.m

        # The function below can be tidied to only use P because that is the only case handled by Sim
        def dpar2mpar(datapar, withwhat, default_withwhat='p', smoothness=5*int(1/opt['dt'])):
           """
           Take parameters and turn them into model parameters
           Set withwhat = p if you want to use the epi data for the parameters
           Set withwhat = c if you want to use the ccoc data for the parameters
           """
           from numpy import isnan
           from liboptima.utils import smoothinterp

           withwhat = withwhat if withwhat in datapar else default_withwhat #if that is not there, then it has to fail anyway
           
           npops = len(datapar[withwhat])
           
           output = zeros((npops,npts))
           for pop in xrange(npops):
               if withwhat=='c' and ~isnan(datapar[withwhat][pop]).all(): # Use cost relationship
                   output[pop, :] = datapar[withwhat][pop, :]
               else: # Use parameter
                   if 't' in datapar.keys(): # It's a time parameter
                       output[pop,:] = smoothinterp(M['tvec'], datapar['t'][pop], datapar['p'][pop], smoothness=smoothness) # Use interpolation
                   else:
                       output[pop,:] = datapar['p'][pop]
                       print('TMP')
           
           return output


        def grow(popsizes, growth):
           """ Define a special function for population growth, which is just an exponential growth curve """
           npops = len(popsizes)        
           output = zeros((npops,npts))
           for pop in xrange(npops):
               output[pop,:] = popsizes[pop]*exp(growth*(M['tvec']-M['tvec'][0])) # Special function for population growth
               
           return output


        ## Epidemiology parameters -- most are data
        M['popsize'] = grow(calibration['popsize'], opt['growth']) # Population size
        M['hivprev'] = calibration['hivprev'] # Initial HIV prevalence
        M['stiprevulc'] = dpar2mpar(self.parsdata['stiprevulc'], withwhat) # STI prevalence
        M['stiprevdis'] = dpar2mpar(self.parsdata['stiprevdis'], withwhat) # STI prevalence
        M['death']  = dpar2mpar(self.parsdata['death'], withwhat)  # Death rates
        M['tbprev'] = dpar2mpar(self.parsdata['tbprev'], withwhat) # TB prevalence

        ## Testing parameters -- most are data
        M['hivtest'] = dpar2mpar(self.parsdata['hivtest'], withwhat) # HIV testing rates
        M['aidstest'] = dpar2mpar(self.parsdata['aidstest'], withwhat)[0] # AIDS testing rates
        M['tx1'] = dpar2mpar(self.parsdata['numfirstline'], withwhat, smoothness=int(1/opt['dt']))[0] # Number of people on first-line treatment -- 0 since overall not by population
        M['tx2'] = dpar2mpar(self.parsdata['numsecondline'], withwhat, smoothness=int(1/opt['dt']))[0] # Number of people on second-line treatment
        M['txelig'] = dpar2mpar(self.parsdata['txelig'], withwhat, smoothness=int(1/opt['dt']))[0] # Treatment eligibility criterion

        ## MTCT parameters
        M['numpmtct'] = dpar2mpar(self.parsdata['numpmtct'], withwhat)[0]
        M['birth']    = dpar2mpar(self.parsdata['birth'], withwhat)
        M['breast']   = dpar2mpar(self.parsdata['breast'], withwhat)[0]  

        ## Sexual behavior parameters -- all are parameters so can loop over all
        M['numactsreg'] = dpar2mpar(self.parsdata['numactsreg'], withwhat) # ...
        M['numactscas'] = dpar2mpar(self.parsdata['numactscas'], withwhat) # ...
        M['numactscom'] = dpar2mpar(self.parsdata['numactscom'], withwhat) # ...
        M['numactsinj'] = dpar2mpar(self.parsdata['numinject'], withwhat) # ..
        M['condomreg']  = dpar2mpar(self.parsdata['condomreg'], withwhat) # ...
        M['condomcas']  = dpar2mpar(self.parsdata['condomcas'], withwhat) # ...
        M['condomcom']  = dpar2mpar(self.parsdata['condomcom'], withwhat) # ...

        ## Circumcision parameters
        M['circum']    = dpar2mpar(self.parsdata['circum'], withwhat) # Circumcision percentage
        if 'VMMC' in [p['name'] for p in r.metadata['programs']]:
            M['numcircum'] = dpar2mpar(self.parsdata['numcircum'], withwhat)[0] # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
        else:
            M['numcircum'] = zeros(shape(M['tvec'])) # Number to be circumcised -- to be populated by the relevant CCOC
            

        ## Drug behavior parameters
        M['numost'] = dpar2mpar(self.parsdata['numost'], withwhat)[0]
        M['sharing'] = dpar2mpar(self.parsdata['sharing'], withwhat)

        ## Other intervention parameters (proportion of the populations, not absolute numbers)
        M['prep'] = dpar2mpar(self.parsdata['prep'], withwhat)

        ## Matrices can be used almost directly
        M['pships'] = dict()
        M['transit'] = dict()
        for key in calibration['pships'].keys(): 
            M['pships'][key] = array(calibration['pships'][key])
        for key in calibration['transit'].keys(): 
            M['transit'][key] = array(calibration['transit'][key])

        ## Constants...can be used directly
        M['const'] = calibration['const']

        ## Calculate total acts
        M['totalacts'] = calculate_totalacts(M)

        ## Program parameters not related to data
        M['propaware'] = zeros(shape(M['hivtest'])) # Initialize proportion of PLHIV aware of their status
        M['txtotal'] = zeros(shape(M['tx1'])) # Initialize total number of people on treatment

        self.parsmodel = M

    def run(self,force_initialise=False):
        # Returns the full debug output i.e. D.S
        if not self.initialised or force_initialise: # Force initialization if something might have changed
            self.initialise()

        r = self.getproject()
        calibration = self.getcalibration()

        from model import model
        
        # Note: Work out what we're looping through. There may be a more sensible alternative...?
        allsims = []
        for s in range(len(self.parsfitted)):   # Parallelise eventually.
            S = model(r.metadata, self.parsmodel, self.parsfitted[s], r.options)
            allsims.append(S)
        self.debug['structure'] = allsims[0]     # Save one full sim structure for troubleshooting and... funsies?
    
        # Calculate results.
        from makeresults import makeresults
        
        # Explicit construction of tempD, so that one day we know how to recode makeresults.
        tempD = dict()
        tempD['G'] = r.metadata
        tempD['P'] = deepcopy(self.parsdata)
        tempD['P']['const'] = calibration['const']

        tempD['S'] = self.debug['structure']
        
        # Input that only the financialanalysis subfunction in makeresults wants.
        # It would be a good idea to somehow separate the two...
        tempD['data'] = r.data
        tempD['opt'] = r.options
        tempD['programs'] = r.metadata['programs']
        
        R = makeresults(tempD, allsims, r.options['quantiles'])
        self.debug['results'] = R

        # Gather plot data.
        from gatherplotdata import gatheruncerdata
        
        # Explicit construction of tempD, so that one day we know how to recode gatheruncerdata.
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        
        self.plotdata = gatheruncerdata(tempD, self.debug['results'])
        
        self.processed = True

        return (allsims[0],R)   
        
    def plotresults(self, show_wait=True):
        
        from viewresults import viewuncerresults
        
        viewuncerresults(self.plotdata,show_wait=show_wait)

    def __repr__(self):
        return "Sim %s ('%s')" % (self.uuid,self.name)

    def __getstate__(self):
        raise Exception('Simobject must be saved via a project')

    def __setstate__(self, state):
        raise Exception('Simobjects must be re-created via a project')

#------------------------------------------------------------------------------
        
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

# Tail imports
from simbudget import SimBudget
from simbudget2 import SimBudget2
from simparameter import SimParameter
