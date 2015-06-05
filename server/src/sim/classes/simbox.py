# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 01:03:34 2015

@author: David Kedziora
"""

class SimBox:
    def __init__(self, simboxname):
        self.simboxname = simboxname
        
        self.simlist = []
        
    # Creates a simulation object but makes sure to initialise it immediately after, ready for processing.
    def createsim(self, simname, regiondata, regionmetadata, regionoptions):
        print('Preparing new simulation for container %s...')
        self.simlist.append(Sim(simname))
        self.simlist[-1].initialise(regiondata, regionmetadata, regionoptions)
    
    def runallsims(self, regiondata, regionmetadata, regionoptions, regionprograms, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run(regiondata, regionmetadata, regionoptions, regionprograms)
                
    def plotallsims(self):
        for sim in self.simlist:
            if sim.isprocessed():
                sim.plotresults()
        
    def printsimlist(self, assubsubset = False):
        # Prints with long arrow formats if assubsubset is true. Otherwise uses short arrows.        
        if assubsubset:
            if len(self.simlist) > 0:
                for sim in self.simlist:
                    print('   --> %s%s' % (sim.getsimname(), (" (unprocessed)" if not sim.isprocessed() else " (processed)")))
        else:
            if len(self.simlist) == 0:
                print('No simulations are currently stored in container %s.' % self.getsimboxname())
            else:
                for sim in self.simlist:
                    print(' --> %s%s' % (sim.getsimname(), (" (unprocessed)" if not sim.isprocessed() else " (processed)")))
        
    def setsimboxname(self, simboxname):
        self.simboxname = simboxname
        
    def getsimboxname(self):
        return self.simboxname
        
class Sim:
    def __init__(self, simname):
        self.simname = simname
        self.processed = False      # This tag monitors if the simulation has been run.
        
        self.parsdata = None        # This used to be D['P'].
        self.parsmodel = None       # This used to be D['M'].
        self.parsfitted = None      # This used to be D['F'].
        
        self.results = None         # This used to be D['R'].
        self.plotdata = None        # This used to be D['plot']['E']. Be aware that it is not D['plot']!
        
    def setsimname(self, simname):
        self.simname = simname
        
    def getsimname(self):
        return self.simname
        
    def isprocessed(self):
        return self.processed
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
    # Very dangerous, as stability relies on the trust that no data passed in is being changed behind the scenes...
    def initialise(self, regiondata, regionmetadata, regionoptions):
        
        from makedatapars import makedatapars
        
        # Explicit construction of tempD, so that one day we know how to recode makedatapars.
        tempD = dict()
        tempD['data'] = regiondata
        tempD['G'] = regionmetadata
        
        tempD = makedatapars(tempD)
        self.parsdata = tempD['P']
        
        from makemodelpars import makemodelpars
        
        self.parsmodel = makemodelpars(self.parsdata, regionoptions)
        
        from updatedata import makefittedpars
        
        # Explicit construction of tempD, so that one day we know how to recode makefittedpars.
        tempD = dict()
        tempD['opt'] = regionoptions
        tempD['G'] = regionmetadata
        tempD['M'] = self.parsmodel
        
        tempD = makefittedpars(tempD)
        self.parsfitted = tempD['F']
    
    # Runs model given all the initialised parameters.
    def run(self, regiondata, regionmetadata, regionoptions, regionprograms):
        
        from model import model

        allsims = []
        for s in range(len(self.parsfitted)):   # Parallelise eventually.
            S = model(regionmetadata, self.parsmodel, self.parsfitted[s], regionoptions)
            allsims.append(S)
    
        # Calculate results.
        from makeresults import makeresults
        
        # Explicit construction of tempD, so that one day we know how to recode makeresults.
        tempD = dict()
        tempD['G'] = regionmetadata
        tempD['P'] = self.parsdata
        tempD['S'] = allsims[0]                 # Save one full sim structure for troubleshooting and... funsies?
        
        # Input that only the financialanalysis subfunction in makeresults wants.
        # It would be a good idea to somehow separate the two...
        tempD['data'] = regiondata
        tempD['opt'] = regionoptions
        tempD['programs'] = regionprograms
        
        # Note: Beware financialanalysis subfunction. It wants all the D...
        self.results = makeresults(tempD, allsims, regionoptions['quantiles'])
    
        # Gather plot data.
        from gatherplotdata import gatheruncerdata
        
        tempD = dict()
        tempD['data'] = regiondata
        tempD['G'] = regionmetadata
        
        self.plotdata = gatheruncerdata(tempD, self.results)
        
        self.processed = True
        
    def plotresults(self):
        
        from viewresults import viewuncerresults
        
        viewuncerresults(self.plotdata)