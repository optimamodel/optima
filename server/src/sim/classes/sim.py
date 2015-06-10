# -*- coding: utf-8 -*-
"""
Created on Fri Jun 05 23:27:38 2015

@author: David Kedziora
"""

import weakref

class Sim:
    def __init__(self, name, region):
        self.name = name
        self.processed = False      # This tag monitors if the simulation has been run.
        self.initialised = False    # This tag monitors if the simulation has been initialised.

        self.parsdata = None        # This used to be D['P'].
        self.parsmodel = None       # This used to be D['M'].
        self.parsfitted = None      # This used to be D['F'].
        
        self.debug = {}             # This stores the (large) output from running the simulation
        self.debug['results'] = None         # This used to be D['R'].
        self.debug['structure'] = None       # This used to be D['S'].
        
        self.plotdata = None        # This used to be D['plot']['E']. Be aware that it is not D['plot']!        
        self.plotdataopt = []       # This used to be D['plot']['optim']. Be aware that it is not D['plot']!
    
        self.setregion(region)

    @classmethod
    def fromdict(SimBox,simdict,region):
        assert(simdict['region_uuid'] == region.uuid)

        s = Sim(simdict['name'],region)
        s.processed  = simdict['processed']  
        s.parsdata  = simdict['parsdata']  
        s.parsmodel  = simdict['parsmodel']  
        s.parsfitted  = simdict['parsfitted']  
        s.debug  = simdict['debug']   
        s.plotdata  = simdict['plotdata']  
        s.plotdataopt  = simdict['plotdataopt']  
        s.setregion(region)
        return s

    def todict(self):
        simdict = {}
        simdict['name'] = self.name
        simdict['processed']  = self.processed 
        simdict['parsdata']  = self.parsdata 
        simdict['parsmodel']  = self.parsmodel 
        simdict['parsfitted']  = self.parsfitted 
        simdict['debug']   = self.debug 
        simdict['plotdata']  = self.plotdata 
        simdict['plotdataopt']  = self.plotdataopt 
        simdict['region_uuid'] = self.getregion().uuid
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
            raise Exception('The parent region has been garbage-collected and the reference is no longer valid')
        else:
            return r

    def setname(self, name):
        self.name = name
        
    def getname(self):
        return self.name
        
    def isprocessed(self):
        return self.processed
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
    # Very dangerous, as stability relies on the trust that no data passed in is being changed behind the scenes...
    def initialise(self):
        r = self.getregion()

        from makedatapars import makedatapars
        from numpy import arange

        # Explicit construction of tempD, so that one day we know how to recode makedatapars.
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        tempD['G']['datayears'] = arange(r.metadata['datastart'], r.metadata['dataend']+1)
        tempD['G']['npops'] = len(r.metadata['populations'])
        tempD['G']['nprogs'] = len(r.metadata['programs'])

        tempD = makedatapars(tempD)
        self.parsdata = tempD['P']
        
        from makemodelpars import makemodelpars
        
        self.parsmodel = makemodelpars(self.parsdata, r.options)
        
        from updatedata import makefittedpars
        
        # Explicit construction of tempD, so that one day we know how to recode makefittedpars.
        tempD = dict()
        tempD['opt'] = r.options
        tempD['G'] = r.metadata
        tempD['M'] = self.parsmodel
        
        tempD = makefittedpars(tempD)
        self.parsfitted = tempD['F']
        
        self.initialised = True

    def makemodelpars(self):
        # SimParameter, SimBudget and SimCoverge differ in how they calculate D.M
        # but are otherwise almost identical. Thus this is the function that is
        # expected to be re-implemented in the derived classes
        from makemodelpars import makemodelpars

        self.parsmodel = makemodelpars(self.parsdata, r.options)

    # Runs model given all the initialised parameters.
    def run(self):
        if not self.initialised:
            self.initialise()

        r = self.getregion()

        from model import model

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
        tempD['P'] = self.parsdata
        tempD['S'] = self.debug['structure']
        
        # Input that only the financialanalysis subfunction in makeresults wants.
        # It would be a good idea to somehow separate the two...
        tempD['data'] = r.data
        tempD['opt'] = r.options
        tempD['programs'] = r.metadata['programs']
        
        self.debug['results'] = makeresults(tempD, allsims, r.options['quantiles'])
    
        # Gather plot data.
        from gatherplotdata import gatheruncerdata
        
        tempD = dict()
        tempD['data'] = r.data
        tempD['G'] = r.metadata
        
        self.plotdata = gatheruncerdata(tempD, self.debug['results'])
        
        self.processed = True        
        
    def plotresults(self):
        
        from viewresults import viewuncerresults
        
        viewuncerresults(self.plotdata, show_wait = True)



# Derived Sim class that should store budget data.
class SimBudget(Sim):
    def __init__(self, name, region):
        Sim.__init__(self, name, region)
        
    # Currently just optimises simulation according to defaults.
    def optimise(self):
        r = self.getregion()

        from optimize import optimize
        
        tempD = dict()
        tempD['data'] = r.data
        tempD['opt'] = r.options
        tempD['programs'] = r.metadata['programs']
        tempD['G'] = r.metadata
        tempD['P'] = self.parsdata
        tempD['M'] = self.parsmodel
        tempD['F'] = self.parsfitted
        tempD['R'] = self.debug['results']
        tempD['plot'] = dict()
        
        tempD['S'] = self.debug['structure']     # Error rising. Where does S come from? Do I need to run simulation first?
        optimize(tempD, maxiters = 2)   # Temporary restriction on iterations. Not meant to be hardcoded!
        
        self.plotdataopt = tempD['plot']['optim'][-1]       # What's this -1 business about?
        
#        # Figure out plotting shortly.
#        from viewresults import viewmultiresults, viewoptimresults
#        
#        viewmultiresults(tempD['plot']['optim'][-1]['multi'], show_wait = True)
#        viewmultiresults(tempD['plot']['optim'][-1]['multi'], show_wait = True)
#        viewoptimresults(tempD['plot']['optim'][-1])
#        viewoptimresults(tempD['plot']['optim'][-1])