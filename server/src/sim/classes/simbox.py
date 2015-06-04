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
    def createsim(self, simname, regiondata, regionmetadata):
        print('Preparing new simulation for container %s...')
        self.simlist.append(Sim(simname))
        self.simlist[-1].initialise(regiondata, regionmetadata)
        
    def printsimlist(self, assubsubset = False):
        # Prints with long arrow formats if assubsubset is true. Otherwise uses short arrows.        
        if assubsubset:
            if len(self.simlist) > 0:
                for sim in self.simlist:
                    print('   --> %s' % sim.getsimname())
        else:
            if len(self.simlist) == 0:
                print('No simulations are currently stored in container %s.' % self.getsimboxname())
            else:
                for sim in self.simlist:
                    print(' --> %s' % sim.getsimname())
        
    def setsimboxname(self, simboxname):
        self.simboxname = simboxname
        
    def getsimboxname(self):
        return self.simboxname
        
class Sim:
    def __init__(self, simname):
        self.simname = simname
        
        self.parsdata = None
        self.parsmodel = None
        self.parsfitted = None
        
    def setsimname(self, simname):
        self.simname = simname
        
    def getsimname(self):
        return self.simname
    
    # Initialises P, M and F matrices belonging to the Sim object, but does not run simulation yet.
    def initialise(self, regiondata, regionmetadata):
        
        from makedatapars import makedatapars
        
        tempD = dict()
        tempD['data'] = regiondata
        tempD['G'] = regionmetadata
        
        tempD = makedatapars(tempD)
        self.parsdata = tempD['P']
        