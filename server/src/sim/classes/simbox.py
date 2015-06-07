# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 01:03:34 2015

@author: David Kedziora
"""

from sim import Sim

class SimBox:
    def __init__(self, simboxname):
        self.simboxname = simboxname
        
        self.simlist = []
        
    # Creates a simulation object but makes sure to initialise it immediately after, ready for processing.
    def createsim(self, simname, regiondata, regionmetadata, regionoptions):
        print('Preparing new simulation for container %s...')
        self.simlist.append(Sim(simname))
        self.simlist[-1].initialise(regiondata, regionmetadata, regionoptions)
    
    def runallsims(self, regiondata, regionmetadata, regionoptions, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run(regiondata, regionmetadata, regionoptions)
                
    def optallsims(self, regiondata, regionmetadata, regionoptions, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.optimise(regiondata, regionmetadata, regionoptions)
                
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