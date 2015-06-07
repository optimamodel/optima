# -*- coding: utf-8 -*-
"""
Created on Fri May 29 23:16:12 2015

@author: David Kedziora
"""

import defaults
from simbox import SimBox


class Region:
    def __init__(self, name,populations,programs,datastart,dataend):
        self.D = dict()                 # Data structure for saving everything. Will hopefully be broken down eventually.
              
        self.metadata = {}            # Loosely analogous to D['G']
        self.metadata['datastart'] = datastart
        self.metadata['dataend'] = dataend
        self.metadata['populations'] = populations
        self.metadata['programs'] = programs
        self.metadata['name'] = name

        self.options = None             # This used to be D['opt']. Is it constant? Or should it be tagged 'default'?
        
        self.simboxlist = []            # Container for simbox objects (e.g. optimisations, grouped scenarios, etc.)
        
    def createsimbox(self, simboxname):
        self.simboxlist.append(SimBox(simboxname))
        
        # Makes sure that a new simbox has at least one sim object, ready to run. It is passed regional data, metadata and options.
        self.simboxlist[-1].createsim(simboxname+'-initial', self.data, self.metadata, self.options)
        
    # Runs through every simulation in simbox (if not processed) and processes them.
    def runsimbox(self, simbox):
        simbox.runallsims(self.data, self.metadata, self.options, self.programs, forcerun = False)
    
    # Runs through every simulation in simbox (if not processed) and optimises them.
    # Currently uses default settings.
    def optsimbox(self, simbox):
        simbox.optallsims(self.data, self.metadata, self.options, self.programs, forcerun = True)
        
    # Runs through every simulation in simbox (if processed) and plots them.
    def plotsimbox(self, simbox):
        simbox.plotallsims()
        
    def printdata(self):
        print(self.data)
    
    def printmetadata(self):
        print(self.metadata)
        
    def printoptions(self):
        print(self.options)
        
    def printprograms(self):
        print(self.programs)
        
    def printsimboxlist(self, assubset = False):
        # Prints with nice arrow formats if assubset is true. Otherwise numbers the list.        
        if assubset:
            if len(self.simboxlist) > 0:
                for simbox in self.simboxlist:
                    print(' --> %s' % simbox.getsimboxname())
                    simbox.printsimlist(assubsubset = True)
        else:
            if len(self.simboxlist) == 0:
                print('No simulations are currently associated with region %s.' % self.getregionname())
            else:
                print('Collections of simulations associated with this project...')
                fid = 0
                for simbox in self.simboxlist:
                    fid += 1
                    print('%i: %s' % (fid, simbox.getsimboxname()))
                    simbox.printsimlist(assubsubset = False)
                
    def setdata(self, data):
        self.data = data
        
    def getdata(self):
        return self.data
        
    def setmetadata(self, metadata):
        self.metadata = metadata
        
    def getmetadata(self):
        return self.metadata
        
    def setoptions(self, options):
        self.options = options
        
    def getoptions(self):
        return self.options
    
    def setprograms(self, programs):
        self.programs = programs
        
    def getprograms(self):
        return self.programs
        
    def setregionname(self, regionname):
        self.metadata['name'] = regionname
        
    def getregionname(self):
        return self.metadata['name']
        
    ### Refers to legacy D.
        
    def loadDfrom(self, path):
        from dataio import loaddata
        tempD = loaddata(path)
        self.setD(tempD)                # It would be great to get rid of setD one day. But only when data is fully decomposed.
        self.setdata(tempD['data'])
        self.setmetadata(tempD['G'])
        self.setoptions(tempD['opt'])
        self.setprograms(tempD['programs'])
        
    def setD(self, D):
        self.D = D
        
    def getD(self):
        return self.D
        

    def makeworkbook(self, name, pops, progs, datastart=defaults.datastart, dataend=defaults.dataend, verbose=2):
        """ Generate the Optima workbook -- the hard work is done by makeworkbook.py """
        from printv import printv
        from dataio import templatepath
        from makeworkbook import OptimaWorkbook
    
        printv("""Generating workbook with parameters:
                 name = %s, pops = %s, progs = %s, datastart = %s, dataend = %s""" \
                 % (name, pops, progs, datastart, dataend), 1, verbose)
        path = templatepath(name)
        book = OptimaWorkbook(name, pops, progs, datastart, dataend)
        book.create(path)
        
        printv('  ...done making workbook %s.' % path, 2, verbose)
        return path