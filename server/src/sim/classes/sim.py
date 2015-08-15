# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 23:27:38 2015

@author: David Kedziora
"""

import weakref
import uuid
import defaults
from copy import deepcopy
from printv import printv
from numpy import array, isnan, zeros, shape, mean
from utils import sanitize
from printv import printv
from numpy import zeros, array, exp, shape

class Sim:
    def __init__(self, name, region, calibration = None):
        self.name = name
        self.initialised = False    # This tag monitors if the simulation has been initialised.        
        self.processed = False      # This tag monitors if the simulation has been run.
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality

        self.parsdata = None        # This used to be D['P'].
        self.parsmodel = None       # This used to be D['M'].
        self.parsfitted = None      # This used to be D['F'].
        self.calibration = calibration if calibration is not None else region.calibrations[0]['uuid'] # Use the first region calibration by default - could reorder the region's calibrations to choose a default later

        self.debug = {}             # This stores the (large) output from running the simulation
        self.debug['results'] = None         # This used to be D['R'].
        self.debug['structure'] = None       # This used to be D['S'].
        
        self.plotdata = None        # This used to be D['plot']['E']. Be aware that it is not D['plot']!        
        self.plotdataopt = None # TEMP DEBUG, DON'T COMMIT
        self.setregion(region)

    @classmethod
    def fromdict(Sim,simdict,region):
        # This function instantiates the correct subtype based on simdict['type']
        assert(simdict['region_uuid'] == region.uuid)
        if simdict['type'] == 'Sim':
            s = Sim(simdict['name'],region)
        if simdict['type'] == 'SimParameter':
            s = SimParameter(simdict['name'],region)
        if simdict['type'] == 'SimBudget':
            s = SimBudget(simdict['name'],region)
        s.setregion(region)
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
        simdict['region_uuid'] = self.getregion().uuid
        simdict['uuid'] = self.uuid
        simdict['calibration'] = self.calibration
        return simdict
    
    def setregion(self,region):
        self.region = weakref.ref(region)

    def getregion(self):
        # self.region is a weakref object, which means to get
        # the region you need to do self.region() rather than
        # self.region. This function abstracts away this 
        # implementation detail in case it changes in future
        r = self.region()
        if r is None:
            raise Exception('The parent region has been garbage-collected and the reference is no longer valid.')
        else:
            return r

    def getcalibration(self):
        # Return a deepcopy of the selected calibration
        r = self.getregion()
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
        r = self.getregion()
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
        r = self.getregion() 
        calibration = self.getcalibration()

        ## Preliminaries
        
        def data2par(dataarray, region,usetime=True):
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
                        output['t'][n] = region.metadata['datayears'][~isnan(dataarray[n])] # Store each year
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
        r = self.getregion()
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
           from utils import smoothinterp

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

        def totalacts(M, npts):
            eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero

            totalacts = dict()

            popsize = M['popsize']
            pships = M['pships']

            for act in pships.keys():
                npops = len(M['popsize'][:,0])
                npop=len(popsize); # Number of populations
                mixmatrix = pships[act]
                symmetricmatrix=zeros((npop,npop));
                for pop1 in xrange(npop):
                    for pop2 in xrange(npop):
                        symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))

                a = zeros((npops,npops,npts))
                numacts = M['numacts'][act]
                for t in xrange(npts):
                    a[:,:,t] = reconcileacts(symmetricmatrix.copy(), popsize[:,t], numacts[:,t]) # Note use of copy()

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
        M['numacts'] = dict()
        M['condom']  = dict()
        M['numacts']['reg'] = dpar2mpar(self.parsdata['numactsreg'], withwhat) # ...
        M['numacts']['cas'] = dpar2mpar(self.parsdata['numactscas'], withwhat) # ...
        M['numacts']['com'] = dpar2mpar(self.parsdata['numactscom'], withwhat) # ...
        M['numacts']['inj'] = dpar2mpar(self.parsdata['numinject'], withwhat) # ..
        M['condom']['reg']  = dpar2mpar(self.parsdata['condomreg'], withwhat) # ...
        M['condom']['cas']  = dpar2mpar(self.parsdata['condomcas'], withwhat) # ...
        M['condom']['com']  = dpar2mpar(self.parsdata['condomcom'], withwhat) # ...

        ## Circumcision parameters
        M['circum']    = dpar2mpar(self.parsdata['circum'], withwhat) # Circumcision percentage
        M['numcircum'] = zeros(shape(M['tvec'])) # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations

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
        M['totalacts'] = totalacts(M, npts)


        ## Program parameters not related to data
        M['propaware'] = zeros(shape(M['hivtest'])) # Initialize proportion of PLHIV aware of their status
        M['txtotal'] = zeros(shape(M['tx1'])) # Initialize total number of people on treatment

        self.parsmodel = M

    def run(self):
        # Returns the full debug output
        if not self.initialised:
            self.initialise()

        r = self.getregion()
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
        
        self.debug['results'] = makeresults(tempD, allsims, r.options['quantiles'])

        # Gather plot data.
        from gatherplotdata import gatheruncerdata
        
        # Explicit construction of tempD, so that one day we know how to recode gatheruncerdata.
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        
        self.plotdata = gatheruncerdata(tempD, self.debug['results'])
        
        self.processed = True

        return allsims[0]        
        
    def plotresults(self):
        
        from viewresults import viewuncerresults
        
        viewuncerresults(self.plotdata, show_wait = True)

    def __repr__(self):
        return "Sim %s ('%s')" % (self.uuid,self.name)



#------------------------------------------------------------------------------



# Derived Sim class that should store parameter overwrites.
class SimParameter(Sim):
    def __init__(self, name, region, calibration = None):
        Sim.__init__(self, name, region, calibration)
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
            r = self.getregion()
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
        r = self.getregion()
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

class SimBudget2(Sim):
    def __init__(self, name, region,budget):
        # budget and alloc are the same thing i.e. an 'alloc' *is* actually a budget
        Sim.__init__(self, name, region)
        self.budget = budget # This contains spending values for all of the modalities for the simulation timepoints i.e. there are len(D['opt']['partvec']) spending values
        self.program_set = region.program_sets[0] # Eventually modify to support multiple programs

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget2'
        simdict['budget'] = self.budget
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.budget = simdict['budget'] 

    def makemodelpars(self):
        r = self.getregion()
        npts = len(r.options['partvec']) # Number of time points

        P = self.parsdata 
        from numpy import nan, zeros
        for param in P.keys():
            if isinstance(P[param], dict) and 'p' in P[param].keys():
                P[param]['c'] = nan+zeros((len(P[param]['p']), npts))

        for prog, spending in zip(self.program_set['programs'], self.budget):
            coverage = prog.get_coverage(spending) # Returns metamodality coverage
            outcomes = prog.get_outcomes(coverage) # Returns program outcomes (for each effect)

            try:
                print '--- SIM'
                print 'Coverage: ', coverage[0][0][0]
                print 'Outcome: ', [x[0][0] for x in outcomes]
            except:
                continue
            for i in xrange(0,len(prog.effects['param'])): # For each of the effects
                if prog.effects['iscoverageparam'][i]:
                    P[prog.effects['param'][i]]['c'][:] = outcomes[i]
                else:
                    popnumber = r.get_popidx(prog.effects['popname'][i])-1 # Yes, get_popidx is 1-based rather than 0 based...cf. scenarios
                    P[prog.effects['param'][i]]['c'][popnumber] = outcomes[i]

        from makemodelpars import makemodelpars
        self.parsmodel = makemodelpars(P, r.options, withwhat='c')

    def __repr__(self):
        return "SimBudget2 %s ('%s')" % (self.uuid,self.name)  

#%% Tail imports pointing to derived classes, so as to avoid circular import problems.

from simbudget import SimBudget