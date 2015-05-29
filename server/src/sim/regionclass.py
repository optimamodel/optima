# -*- coding: utf-8 -*-
"""
Created on Fri May 29 23:16:12 2015

@author: David Kedziora
"""

# Default values are currently duplicated in legacy makeproject.py and regionclass.py.
# Consider making them globals at some stage.
default_pops = ['']*6
default_progs = ['']*7
default_datastart = 2000
default_dataend = 2015
default_nsims = 5

# IMPORTANT: increment this if structure of D changes
current_version = 5

class Region:
    def __init__(self):
        self.D = dict() # Data structure for saving everything
        self.regionname = 'Unnamed'
        
    def makeproject(self, projectname='example', pops = default_pops, progs = default_progs, datastart=default_datastart, \
        dataend=default_dataend, nsims=default_nsims, verbose=2, savetofile = True, domakeworkbook=True):
        """
        Initializes the empty project. Only the "Global" and "Fitted" parameters are added on this step.
        The rest of the parameters are calculated after the model is updated with the data from the workbook.
        
        Version: 2015jan27 by cliffk
        """
        
        from dataio import savedata, projectpath
        from printv import printv
        from numpy import arange
        from copy import deepcopy
    
        printv('Making project...', 1, verbose)
    
        self.D['plot'] = dict() # Initialize plotting data
        
        # Initialize options
        from setoptions import setoptions
        self.D['opt'] = setoptions(nsims=nsims)
        
        # Set up "G" -- general parameters structure
        self.D['G'] = dict()
        self.D['G']['version'] = current_version # so that we know the version of new project with regard to data structure
        self.D['G']['projectname'] = projectname  
        self.D['G']['projectfilename'] = projectpath(projectname+'.prj')
        self.D['G']['workbookname'] = self.D['G']['projectname'] + '.xlsx'
        self.D['G']['npops'] = len(pops)
        self.D['G']['nprogs'] = len(progs)
        self.D['G']['datastart'] = datastart
        self.D['G']['dataend'] = dataend
        self.D['G']['datayears'] = arange(self.D['G']['datastart'], self.D['G']['dataend']+1)
        self.D['G']['inputprograms'] = deepcopy(progs) # remember input programs with their possible deviations from standard parameter set (if entered from GUI). 
        # Hate duplicating the data, but can't think of a cleaner way of export/import.
        self.D['G']['inputpopulations'] = deepcopy(pops) # should be there as well, otherwise we cannot export project without data
        # Health states
        self.D['G']['healthstates'] = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
        self.D['G']['ncd4'] = len(self.D['G']['healthstates'])
        self.D['G']['nstates'] = 1+self.D['G']['ncd4']*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
        self.D['G']['sus']  = arange(0,1)
        self.D['G']['undx'] = arange(0*self.D['G']['ncd4']+1, 1*self.D['G']['ncd4']+1)
        self.D['G']['dx']   = arange(1*self.D['G']['ncd4']+1, 2*self.D['G']['ncd4']+1)
        self.D['G']['tx1']  = arange(2*self.D['G']['ncd4']+1, 3*self.D['G']['ncd4']+1)
        self.D['G']['fail'] = arange(3*self.D['G']['ncd4']+1, 4*self.D['G']['ncd4']+1)
        self.D['G']['tx2']  = arange(4*self.D['G']['ncd4']+1, 5*self.D['G']['ncd4']+1)
        for i,h in enumerate(self.D['G']['healthstates']): self.D['G'][h] = [self.D['G'][state][i] for state in ['undx', 'dx', 'tx1', 'fail', 'tx2']]
        
        if savetofile: #False if we are using database
            savedata(self.D['G']['projectfilename'], self.D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
        
        # Make an Excel template and then prompt the user to save it
        if projectname == 'example': # Don't make a new workbook, but just use the existing one, if the project name is "example"
            print('WARNING, Project name set to "example", not creating a new workbook!')
        else: # Make a new workbook
            if domakeworkbook:
                self.makeworkbook(self.D['G']['workbookname'], pops, progs, datastart, dataend, verbose=verbose)
        
        printv('  ...done making project.', 2, verbose)
    
    
    def makeworkbook(self, name, pops, progs, datastart=default_datastart, dataend=default_dataend, verbose=2):
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
    
    def setdata(self, D):
        self.D = D
        
    def getdata(self):
        return self.D
        
    def setregionname(self, regionname):
        self.regionname = regionname
        
    def getregionname(self):
        return self.regionname