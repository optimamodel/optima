# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 01:03:34 2015

@author: David Kedziora
"""

from sim import Sim

class SimBox:
    def __init__(self, name):
        self.name = name
        
        self.simlist = []
        
    @classmethod
    def fromdict(SimBox,simboxdict):
        s = SimBox(None)
        self.name = simboxdict['name']
        self.simlist = [Sim.fromdict(x) for x in simboxdict['simlist']]
        return s

    def todict(SimBox):
        simboxdict = {}
        simboxdict['name'] = self.name
        simboxdict['simlist'] = [s.todict() for s in self.simlist]
        return simboxdict
       
    # Creates a simulation object but makes sure to initialise it immediately after, ready for processing.
    def createsim(self, simname, regiondata, regionmetadata, regionoptions):
        print('Preparing new simulation for container %s...')
        self.simlist.append(Sim(simname))
        self.simlist[-1].initialise(regiondata, regionmetadata, regionoptions)
    
    def runallsims(self, regiondata, regionmetadata, regionoptions, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run(regiondata, regionmetadata, regionoptions)
                
    def plotallsims(self):
        for sim in self.simlist:
            if sim.isprocessed():
                sim.plotresults()

    def viewmultiresults(self,regionmetadata):
        # Superimpose plots, like in the scenarios page in the frontend

        tempD = {}
        tempD['G'] = regionmetadata

        Rarr = []
        for sim in self.simlist:
            tmp = {}
            tmp['R'] = sim.debug['results']
            tmp['label'] = sim.name

            Rarr.append(tmp)

        import gatherplotdata,viewresults
        multidata = gatherplotdata.gathermultidata(tempD, Rarr,verbose=0)
        #viewmultiresults(M, whichgraphs={'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1], 'costcum':[1,1]}, simstartyear=2000, simendyear=2030, onefig=True, verbose=2, show_wait=False, linewidth=2):
        viewresults.viewmultiresults(multidata, show_wait = True)

    def printsimlist(self, assubsubset = False):
        # Prints with long arrow formats if assubsubset is true. Otherwise uses short arrows.        
        if assubsubset:
            if len(self.simlist) > 0:
                for sim in self.simlist:
                    print('   --> %s%s' % (sim.getname(), (" (unprocessed)" if not sim.isprocessed() else " (processed)")))
        else:
            if len(self.simlist) == 0:
                print(' --> No simulations are currently stored in container %s.' % self.getname())
            else:
                for sim in self.simlist:
                    print(' --> %s%s' % (sim.getname(), (" (unprocessed)" if not sim.isprocessed() else " (processed)")))
        
    def setname(self, name):
        self.name = name
        
    def getname(self):
        return self.name
        
        
        
# A container just for Sims with budgets.
class SimBoxOpt(SimBox):
    def __init__(self, name):
        SimBox.__init__(self, name)
                
    def optallsims(self, regiondata, regionmetadata, regionoptions, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.optimise(regiondata, regionmetadata, regionoptions)