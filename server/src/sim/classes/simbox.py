# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 01:03:34 2015

@author: David Kedziora
"""

from sim import Sim, SimBudget
import weakref

class SimBox:
    def __init__(self, name,region):
        self.name = name
        self.simlist = []
        self.setregion(region)

    @classmethod
    def fromdict(SimBox,simboxdict,region):
        assert(simboxdict['region_uuid'] == region.uuid)

        s = SimBox(simboxdict['name'],region)
        s.simlist = [Sim.fromdict(x,region) for x in simboxdict['simlist']]
        s.setregion(region)

        return s

    def todict(self):
        simboxdict = {}
        simboxdict['name'] = self.name
        simboxdict['simlist'] = [s.todict() for s in self.simlist]
        simboxdict['region_uuid'] = self.getregion().uuid

        return simboxdict
    
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

    # Creates a simulation object but makes sure to initialise it immediately after, ready for processing.
    def createsim(self, simname):
        print('Preparing new basic simulation for standard container %s...' % self.name)
        self.simlist.append(Sim(simname,self.getregion()))
        self.simlist[-1].initialise()
    
    def runallsims(self, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run()
                
    def plotallsims(self):
        for sim in self.simlist:
            if sim.isprocessed():
                sim.plotresults()

    # Needs to check processing like plotallsims.
    def viewmultiresults(self, regionmetadata):
        # Superimpose plots, like in the scenarios page in the frontend
        r = self.region()

        tempD = {}
        tempD['G'] = r.metadata

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
    def __init__(self,name,region):
        SimBox.__init__(self,name,region)
        
    # Overwrites the standard Sim create method. This is where budget data would be attached.
    def createsim(self, simname):
        if len(self.simlist) > 0:
            print('Optimisation containers can only contain one initial simulation!')
        else:
            print('Preparing new budget simulation for optimisation container %s...' % self.name)
            self.simlist.append(SimBudget(simname+'-initial'))
            self.simlist[-1].initialise()
                
    def optallsims(self, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.optimise()