# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 01:03:34 2015

@author: David Kedziora
"""

from sim import Sim, SimBudget

import weakref
import uuid

from scipy.interpolate import PchipInterpolator as pchip

class SimBox:
    def __init__(self, name, region):
        self.name = name
        self.simlist = []
        self.setregion(region)
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality

    @classmethod
    def fromdict(SimBox, simboxdict, region):
        assert(simboxdict['region_uuid'] == region.uuid)

        s = SimBox(simboxdict['name'], region)
#        for x in simboxdict['simlist']:
#            if x['type'] == 'Sim':
#                s.simlist.append(Sim.fromdict(x,region))
#            if x['type'] == 'SimParameter':
#                s.simlist.append(SimParameter.fromdict(x,region))   # To be coded.
#            if x['type'] == 'SimBudget':
#                s.simlist.append(SimBudget.fromdict(x,region))
        s.simlist = [Sim.fromdict(x,region) for x in simboxdict['simlist']]
        s.setregion(region)
        s.uuid = simboxdict['uuid'] # Loading a region restores the original UUID

        return s

    def todict(self):
        simboxdict = {}
        simboxdict['type'] = 'SimBox'
        simboxdict['name'] = self.name
        simboxdict['simlist'] = [s.todict() for s in self.simlist]
        simboxdict['region_uuid'] = self.getregion().uuid
        simboxdict['uuid'] = self.uuid

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
        return self.simlist[-1]
        
    def runallsims(self, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run()
                
    def plotallsims(self):
        for sim in self.simlist:
            if sim.isprocessed():
                sim.plotresults()

    # Needs to check processing like plotallsims.
    def viewmultiresults(self):
        # Superimpose plots, like in the scenarios page in the frontend
        r = self.region()

        tempD = {}
        tempD['G'] = r.metadata

        Rarr = []
        atleastoneplot = False
        for sim in self.simlist:
            if sim.isprocessed():
                atleastoneplot = True
                tmp = {}
                tmp['R'] = sim.debug['results']
                tmp['label'] = sim.name
    
                Rarr.append(tmp)

        if not atleastoneplot:
            print('Not one simulation in this container is processed. No plot data exists.')
        else:
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

    def __repr__(self):
        return "SimBox %s ('%s')" % (self.uuid,self.name)
        
        

# A container just for Sims with budgets. (No hard-coded restriction on multiple unoptimised SimBudgets exist, but may be considered lest things 'break'.)
class SimBoxOpt(SimBox):
    def __init__(self,name,region):
        SimBox.__init__(self,name,region)
        
        # Budget Objective Curve data, used for GPA. (Assuming initial budget spending is fixed.)
        self.BOCx = None        # Array of budget allocation totals.
        self.BOCy = None        # Array of corresponding optimum objective values.
        
        self.hasBOC = False
        
    @classmethod
    def fromdict(SimBoxOpt, simboxdict, region):
        assert(simboxdict['region_uuid'] == region.uuid)

        s = SimBoxOpt(simboxdict['name'], region)
#        s.simlist = [SimBudget.fromdict(x,region) for x in simboxdict['simlist']]
        s.simlist = [Sim.fromdict(x,region) for x in simboxdict['simlist']]
        s.setregion(region)
        s.uuid = simboxdict['uuid'] # Loading a region restores the original UUID
        s.hasBOC = simboxdict['has_BOC']
        s.BOCx = simboxdict['BOC_budgets']
        s.BOCy = simboxdict['BOC_objectives']

        return s        
        
    def todict(self):
        simboxdict = SimBox.todict(self)
        simboxdict['type'] = 'SimBoxOpt'    # Overwrites SimBox type.
        simboxdict['has_BOC'] = self.hasBOC
        simboxdict['BOC_budgets'] = self.BOCx
        simboxdict['BOC_objectives'] = self.BOCy
        
        return simboxdict
        
    # Overwrites the standard Sim create method. This is where budget data would be attached.
    def createsim(self, simname):
        if len(self.simlist) > 0:
            print('Optimisation containers can only contain one initial simulation!')
        else:
            print('Preparing new budget simulation for optimisation container %s...' % self.name)
            self.simlist.append(SimBudget(simname+'-initial',self.getregion()))
            self.simlist[-1].initialise()
            
    # This creates a duplicate SimBudget to 'sim', except with optimised 'G', 'M', 'F', 'S' from sim.resultopt.
    # As an optimised version of the previous SimBudget, it will also be automatically processed, to get plotdata.
    def createsimopt(self, sim, optalloc, optobj, resultopt):
        if not sim == None:
            print('Converting optimisation results into a new budget simulation...')
            self.simlist.append(SimBudget(sim.getname(),self.getregion()))
            
            # The copy can't be completely deep or shallow, so we load the new SimBudget with a developer-made method.
            self.simlist[-1].specialoptload(sim, optalloc, optobj, resultopt)
            self.simlist[-1].run()
            
    # Overwrites normal SimBox method so that SimBudget is not only run, but optimised, with the results (possibly) copied to a new SimBudget.
    def runallsims(self, forcerun = False):
        tempsim = None
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run()
            if sim.isprocessed() and (forcerun or not sim.isoptimised()):
                (optalloc, optobj, resultopt, makenew) = sim.optimise()
                tempsim = sim
                
        # Generates a new SimBudget from the last Sim that was optimised in the list, but only when the loop has ended and if requested.
        if makenew:
            self.createsimopt(tempsim, optalloc, optobj, resultopt)
    
    def calculateBOCxy(self):
        if (not self.BOCx == None) or (not self.BOCy == None):
            print('Budget objective curve already exists for optimisation container %s...' % self.name)
        else:
            try:
                sim = self.simlist[-1]
                if not sim.isprocessed():
                    sim.run()
                self.BOCx, self.BOCy = sim.calculateeffectivenesscurve()
                self.hasBOC = True
            except:
                print('There was a problem generating budget objective curve data...')
    
    # Special printing method for SimBoxOpt to take into account whether a Sim was already optimised.
    def printsimlist(self, assubsubset = False):
        # Prints with long arrow formats if assubsubset is true. Otherwise uses short arrows.        
        if assubsubset:
            if len(self.simlist) > 0:
                for sim in self.simlist:
                    print('   --> %s%s' % (sim.getname(), (" (initialised)" if not sim.isprocessed() else " (simulated + %s)" %
                                             ("further optimisable" if not sim.isoptimised() else "already optimised"))))
        else:
            if len(self.simlist) == 0:
                print(' --> No simulations are currently stored in container %s.' % self.getname())
            else:
                for sim in self.simlist:
                    print(' --> %s%s' % (sim.getname(), (" (initialised)" if not sim.isprocessed() else " (simulated + %s)" %
                                             ("further optimisable" if not sim.isoptimised() else "already optimised"))))

    # GPA function. Returns spline for objective effectiveness at different budget totals.
    def getBOCspline(self):
        try:
            return pchip(self.BOCx, self.BOCy, extrapolate=True)
        except:
            print('Budget objective curve data does not seem to exist...')
        
    def plotBOCspline(self):
        import matplotlib.pyplot as plt
        from numpy import linspace
        
        try:
            f = self.getBOCspline()
            x = linspace(min(self.BOCx), max(self.BOCx), 200)
            plt.plot(x,f(x),'-')
            plt.legend(['BOC'], loc='best')
            plt.show()
        except:
            print('Plotting of budget objective curve failed!')

    def __repr__(self):
        return "SimBoxOpt %s ('%s')" % (self.uuid,self.name)

