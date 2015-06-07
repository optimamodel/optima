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
        self.setoptions(tempD['opt'])
        self.setprograms(tempD['programs'])
        self.data = tempD['data']

        # Adapter for new internal data structures
        self.metadata = tempD['G']
        self.metadata['populations'] = self.metadata['inputpopulations']
        self.metadata['programs'] = self.metadata['inputprograms']

    def setD(self, D):
        self.D = D
        
    def getD(self):
        return self.D
        
    def makeworkbook(self,filename):
        """ Generate the Optima workbook -- the hard work is done by makeworkbook.py """
        from printv import printv
        from dataio import templatepath
        import makeworkbook

        path = templatepath(filename)
        book = makeworkbook.OptimaWorkbook(filename, self.metadata['populations'], self.metadata['programs'], self.metadata['datastart'], self.metadata['dataend'])
        book.create(path)
        
    def loadworkbook(self,filename):
        """ Load an XSLX file into region.data """
        import loadworkbook

        # Note
        # 'data' is different depending on whether or not 'programs' is assigned below or not
        # Also, when loading Haiti.xlsx, the variable 'programs' below is different to
        # the contents of D['programs'] obtained by loading 'haiti.json'
        data, programs = loadworkbook.loadworkbook(filename)

        # For now, check that the uploaded programs are the same
        # In future, check region UUID
        if [x['name'] for x in programs] != [x['short_name'] for x in self.metadata['programs']]:
            raise Exception('The programs in the XLSX file do not match the region')

        # Save variables to region
        self.metadata['programs'] = programs
        self.data = data
