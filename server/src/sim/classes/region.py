# -*- coding: utf-8 -*-
"""
Created on Fri May 29 23:16:12 2015

@author: David Kedziora
"""

import defaults
from simbox import SimBox, SimBoxOpt
import sim
import setoptions
import uuid
import program

class Region:
    def __init__(self, name,populations,programs,datastart,dataend):
        # The standard constructor takes in the initial metadata directly
        # In normal usage, this information would come from the frontend
        # whether web interface, or an interactive prompt

        self.D = dict()                 # Data structure for saving everything. Will hopefully be broken down eventually.
              
        self.metadata = defaults.metadata  # Loosely analogous to D['G']. Start with default HIV metadata
        self.metadata['datastart'] = datastart
        self.metadata['dataend'] = dataend
        self.metadata['populations'] = populations
        self.metadata['programs'] = programs
        self.metadata['name'] = name

        self.data = None

        self.options = setoptions.setoptions() # Populate default options here
        
        self.program_sets = []
        self.calibrations = None
        
        self.simboxlist = []            # Container for simbox objects (e.g. optimisations, grouped scenarios, etc.)
    
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality


    @classmethod
    def load(Region,filename,name=None):
        # Create a new region by loading a JSON file
        # If a name is not specified, the one contained in the JSON file is used
        # Note that this function can be used with an old-type or new-type JSON file
        # A new-type JSON file will read a Region object including the UUID
        # While an old-type JSON file corresponds to 'D' and the region will get a new UUID
        r = Region(name,None,None,None,None)

        import dataio
        regiondict = dataio.loaddata(filename)
        if 'uuid' in regiondict.keys(): # This is a new-type JSON file
            r.uuid = regiondict['uuid'] # Loading a region restores the original UUID
            r.fromdict(regiondict)
        else:
            r.fromdict_legacy(regiondict)
        return r

    def fromdict(self,regiondict):
        # Assign variables from a new-type JSON file created using Region.todict()
        self.metadata = regiondict['metadata']
        self.data = regiondict['data']
        self.simboxlist = [SimBox.fromdict(x,self) for x in regiondict['simboxlist']]
        self.options = regiondict['options'] # Populate default options here
        self.program_sets = regiondict['program_sets'] # sets of Programs i.e. an array of sets of CCOCs
        self.calibrations = regiondict['calibrations']       
        self.uuid = regiondict['uuid']
        self.D = regiondict['D']
            
    def fromdict_legacy(self, tempD):
        # Load an old-type D dictionary into the region

        self.setD(tempD)                # It would be great to get rid of setD one day. But only when data is fully decomposed.
        
        current_name = self.metadata['name']
        self.metadata = tempD['G'] # Copy everything from G by default
        self.metadata['programs'] = tempD['programs']
        self.metadata['populations'] = self.metadata['inputpopulations']
        if current_name is not None: # current_name is none if this function is being called from Region.load()
            self.metadata['name'] = current_name
        else:
            self.metadata['name'] = self.metadata['projectname']

        self.data = tempD['data']
        self.data['current_budget'] = tempD['data']['costcov']['cost']

        self.options = tempD['opt']

        # Go through the scenarios and convert them
        if 'scens' in tempD.keys():
            sbox = self.createsimbox('Scenarios')
            for scenario in tempD['scens']: # Separate cases in the web list 
                newsim = sim.SimParameter(scenario['scenario']['name'],self)
                for par in scenario['scenario']['pars']:
                    newsim.create_override(par['names'],par['pops'],par['startyear'],par['endyear'],par['startval'],par['endval'])
                sbox.simlist.append(newsim)

        program_set = {}
        program_set['name'] = 'Default'
        program_set['uuid'] = str(uuid.uuid4())
        program_set['programs'] = []
        for prog in self.metadata['programs']:
            program_set['programs'].append(program.Program(prog))
        self.program_sets.append(program_set)

    def save(self,filename):
        import dataio
        dataio.savedata(filename,self.todict())

    def todict(self):
        # Return a dictionary representation of the object for use with Region.fromdict()
        regiondict = {}
        regiondict['version'] = 1 # Could do something later by checking the version number

        regiondict['metadata'] = self.metadata 
        regiondict['data'] = self.data 
        regiondict['simboxlist'] = [sbox.todict() for sbox in self.simboxlist]
        regiondict['options'] = self.options # Populate default options here = self.options 
        regiondict['program_sets'] = self.program_sets 
        regiondict['calibrations'] = self.calibrations 
        regiondict['uuid'] = self.uuid 
        regiondict['D'] = self.D 
        return regiondict

    def createsimbox(self, simboxname, isopt = False, createdefault = True):
        if isopt:
            self.simboxlist.append(SimBoxOpt(simboxname,self))
        else:
            self.simboxlist.append(SimBox(simboxname,self))
        if createdefault:
            self.simboxlist[-1].createsim(simboxname + '-default')
        return self.simboxlist[-1]
        
    def createsiminsimbox(self, simname, simbox):
        new_sim = simbox.createsim(simname)
        return new_sim
    
# Combine into one SimBox dependent run method?
#------------------------------------
    # Runs through every simulation in simbox (if not processed) and processes them.
    def runsimbox(self, simbox):
        simbox.runallsims(forcerun = False)
    
#    # Runs through every simulation in simbox (if not processed) and optimises them.
#    # Currently uses default settings.
#    def optsimbox(self, simbox):
#        if isinstance(simbox, SimBoxOpt):
#            simbox.optallsims(forcerun = True)
#        else:
#            print('Cannot optimise a standard container.')
#------------------------------------
        
    # Runs through every simulation in simbox (if processed) and plots them, either multiplot or individual style.
    def plotsimbox(self, simbox, multiplot = False):
        if multiplot:
            simbox.viewmultiresults()
        else:
            simbox.plotallsims()
        
    def printdata(self):
        print(self.data)
    
    def printmetadata(self):
        print(self.metadata)
        
    def printoptions(self):
        print(self.options)
        
    def printprograms(self):
        print(self.metadata['programs'])
        
    def printsimboxlist(self, assubset = False):
        # Prints with nice arrow formats if assubset is true. Otherwise numbers the list.        
        if assubset:
            if len(self.simboxlist) > 0:
                for simbox in self.simboxlist:
                    print(' --> %s%s' % (simbox.getname(), (" (optimisation container)" if isinstance(simbox, SimBoxOpt) else " (standard container)")))
                    simbox.printsimlist(assubsubset = True)
        else:
            if len(self.simboxlist) == 0:
                print('No simulations are currently associated with region %s.' % self.getregionname())
            else:
                print('Collections of simulations associated with this project...')
                fid = 0
                for simbox in self.simboxlist:
                    fid += 1
                    print('%i: %s%s' % (fid, simbox.getname(), (" (optimisation container)" if isinstance(simbox, SimBoxOpt) else " (standard container)")))
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
        self.metadata['programs'] = programs
        
    def getprograms(self):
        return self.metadata['programs']
        
    def setregionname(self, regionname):
        self.metadata['name'] = regionname
        
    def getregionname(self):
        return self.metadata['name']


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
        import updatedata
        self.metadata['programs'] = programs
        self.data = updatedata.getrealcosts(data)
        self.data['current_budget'] = self.data['costcov']['cost']
        
    def __repr__(self):
        return "Region %s ('%s')" % (self.uuid,self.metadata['name'])
