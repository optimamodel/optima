# -*- coding: utf-8 -*-
"""
Created on Thu May 28 07:56:23 2015

@author: David Kedziora
"""

## Set parameters. These are legacy, so not sure what to do with them yet.
verbose = 4
show_wait = False       # Hmm. Not used? Can be left for the moment until decided as either a global/local variable.
nsims = 5   

import os
from numpy import arange

from region import Region
import defaults


class Portfolio:
    def __init__(self, portfolioname):
        self.regionlist = []                # List to hold Region objects.
        self.portfolioname = portfolioname
        self.cwd = os.getcwd()              # Should get the current working directory where Portfolio object is instantiated.
        self.regd = self.cwd + '/regions'  # May be good to remove hardcoding at some stage...
        
    def run(self):
        """
        All processes associated with the portfolio are run here.
        Consider this as a 'main' loop for the portfolio.
           
        Version: 2015may28 by davidkedz
        """
        #from time import time
        
        print('\nPortfolio %s has been activated.' % self.portfolioname)
        print('\nThe script that created this portfolio is in...')
        print(self.cwd)
        print('Region data will be sourced from...')
        print(self.regd)
        
        # Initialised variables required by the command loop.
        cmdinput = ''
        cmdinputlist = []
        
        # The command loop begins here.
        while(cmdinput != 'q'):
            
            cmdinputlist = cmdinput.split(None,1)
            if len(cmdinputlist)>1:
        
                # Is the first word 'make'? Then make a region named after the rest of the string.
                if cmdinputlist[0] == 'make':
                    regionname = cmdinputlist[1]
                    # starttime = time()
                    
                    # Checks for files in regions directory. Regex control for .json endings would be nice to implement later...
                    if len(os.listdir(self.regd)) < 1:
                        print('Not possible. There are no .json files to use in...')
                        print(self.regd)
                    else:
                        print('Which data file do you wish to load into %s?' % regionname)
                        fid = 0
                        templist = [x for x in os.listdir(self.regd) if x.endswith('.json') ]
                        
                        # Displays files in regions folder along with an integer id for easy selection.
                        for filename in templist:
                            fid += 1
                            print('%i: %s' % (fid, filename))
                        fchoice = 0
                        
                        # Makes sure that an integer is specified.
                        while fchoice not in arange(1,fid+1):
                            try:
                                fchoice = int(raw_input('Choose a number between 1 and %i, inclusive: ' % fid))
                            except ValueError:
                                fchoice = 0
                                continue
                        
                        # Region is created.
                        print('Creating region %s with data from: ' % regionname)
                        print(self.regd+'/'+templist[fchoice-1])
                        self.regionlist.append(Region(regionname,defaults.pops,defaults.progs,defaults.datastart,defaults.dataend))
                        self.regionlist[-1].loadDfrom(self.regd+'/'+templist[fchoice-1])
                
                # Is the first word 'examine'? Then enter a subloop that processes commands regarding the relevant region.
                elif cmdinputlist[0] == 'examine' and len(self.regionlist) > 0:
                    regionid = cmdinputlist[1]
                    try:
                        int(regionid)
                    except ValueError:
                        regionid = 0
                    if int(regionid) in arange(1,len(self.regionlist)+1):
                        self.examineregion(self.regionlist[int(regionid)-1])
                    else:
                        print('Region ID numbers only range from 1 to %i, inclusive.' % len(self.regionlist))
                    
                # Is the first word 'gpa'? Then, ideally, run geo-prioritisation analysis on subset derived from rest of the string.
                elif cmdinputlist[0] == 'gpa' and len(self.regionlist) > 1:
                    print('Gotcha! There is no geographical prioritisation analysis! This is just a stub.')
                    
                    # LINK TO GPA METHOD OR FUNCTION. MUST OPERATE ON A SUBSET LIST OF REGIONS.
                    
            print('\n--------------------\n')
            self.printregionlist()
            print('')
            if len(self.regionlist) > 1:
                print('Geographical prioritisation analysis now available.')
                print('To run this analysis over all regions, type: gpa all')       # To be extended when the time comes.
            
            print("To make a new region titled 'region_name', type: make region_name")
            if len(self.regionlist) > 0:
                print("To examine a region numbered 'region_id', type: examine region_id")
            print('To quit, type: q')
            cmdinput = raw_input('Enter command: ')
            
    def examineregion(self, currentregion):
        """
        All processes associated with a stored region are run here.
        Consider this as a sub-loop for the portfolio class.
        Note that currentregion has to be a region object.
           
        Version: 2015may28 by davidkedz
        """
        
        print('\nRegion %s is now in focus.' % currentregion.getregionname())
        
        # Initialised variables required by the particular region sub-loop.
        subinput = ''
        subinputlist = []
        
        # The command sub-loop begins here.
        while(subinput != 'r'):
            
            subinputlist = subinput.split(None,1)
            if len(subinputlist)>1:
            
                # Is the first word 'make'? Then make a simbox named after the rest of the string.
                if subinputlist[0] == 'check':
                    if subinputlist[1] == 'data':
                        currentregion.printdata();
                    elif subinputlist[1] == 'metadata':
                        currentregion.printmetadata();
                    elif subinputlist[1] == 'options':
                        currentregion.printoptions();
                    elif subinputlist[1] == 'programs':
                        currentregion.printprograms();
                
                # Is the first word 'make'? Then make a simbox named after the rest of the string.
                elif subinputlist[0] == 'make':
                    simboxname = subinputlist[1]                
                    
                    # Check whether user wants this to be a standard or optimisation container.
                    fchoice = 0
                    while fchoice not in arange(1,3):
                        try:
                            fchoice = int(raw_input('Enter 1 or 2 to create a standard or optimisation container, respectively: '))
                        except ValueError:
                            fchoice = 0
                            continue                    
                    
                    # SimBox (standard or optimisation) is created.
                    print('Creating %s simulation container %s.' % (("standard" if fchoice == 1 else "optimisation"), simboxname))
                    if fchoice == 1:
                        currentregion.createsimbox(simboxname)
                    if fchoice == 2:
                        currentregion.createsimbox(simboxname, isopt = True)
                        
                # Is the first word 'sim'? Then initialise a new sim object in a simbox of choice.
                elif subinputlist[0] == 'sim' and len(currentregion.simboxlist) > 0:
                    simname = subinputlist[1]                    
                    
                    fchoice = 0
                    while fchoice not in arange(1,len(currentregion.simboxlist)+1):
                        try:
                            fchoice = int(raw_input('Enter the ID number of a simulation container (between 1 and %i, inclusive): ' % len(currentregion.simboxlist)))
                        except ValueError:
                            fchoice = 0
                            continue
                    
                    currentregion.createsiminsimbox(simname, currentregion.simboxlist[fchoice-1])
                
                # Is the first word 'run'? Then process all simulation objects in a simbox of choice.
                elif subinputlist[0] == 'run' and len(currentregion.simboxlist) > 0:
                    simboxid = subinputlist[1]                
                    
                    try:
                        int(simboxid)
                    except ValueError:
                        simboxid = 0
                    if int(simboxid) in arange(1,len(currentregion.simboxlist)+1):
                        currentregion.runsimbox(currentregion.simboxlist[int(simboxid)-1])
                    else:
                        print('Simulation container ID numbers only range from 1 to %i, inclusive.' % len(currentregion.simboxlist))
                
                # Is the first word 'opt'? Then optimise all simulation objects in a simbox of choice.
                elif subinputlist[0] == 'opt' and len(currentregion.simboxlist) > 0:
                    simboxid = subinputlist[1]                
                    
                    try:
                        int(simboxid)
                    except ValueError:
                        simboxid = 0
                    if int(simboxid) in arange(1,len(currentregion.simboxlist)+1):
                        currentregion.optsimbox(currentregion.simboxlist[int(simboxid)-1])
                    else:
                        print('Simulation container ID numbers only range from 1 to %i, inclusive.' % len(currentregion.simboxlist))                
                
                # Is the first word 'plot'? Then plot all the processed results in a simbox of choice.
                elif subinputlist[0] == 'plot' and len(currentregion.simboxlist) > 0:
                    simboxid = subinputlist[1]                
                    
                    try:
                        int(simboxid)
                    except ValueError:
                        simboxid = 0
                    if int(simboxid) in arange(1,len(currentregion.simboxlist)+1):
                        currentregion.plotsimbox(currentregion.simboxlist[int(simboxid)-1])
                    else:
                        print('Simulation container ID numbers only range from 1 to %i, inclusive.' % len(currentregion.simboxlist))
            
            print('\n--------------------\n')
            currentregion.printsimboxlist(assubset=False)
            if len(currentregion.simboxlist) == 0:
                print("Processing cannot begin without the creation of a container.")
            
            print("\nTo check region specifics, where 'x' is as follows, type: check x")
            print("Placeholder 'x' can be: 'data', 'metadata', 'options', 'programs'")
            print("To make a new simulation container in this region titled 'simbox_name', type: make simbox_name")
            if len(currentregion.simboxlist) > 0:
                print("To initialise a new simulation titled 'sim_name', type: sim sim_name")
                print("To run all unprocessed simulations in 'simbox_id', type: run simbox_id")
                print("To optimise all unprocessed simulations in 'simbox_id', type: opt simbox_id")    # Heavy work ahead.
                print("To plot all processed simulations in 'simbox_id', type: plot simbox_id")
            print('To return to portfolio level, type: r')
            subinput = raw_input('Enter command: ')
        print('\nNow examining portfolio %s as a whole.' % self.portfolioname)
        return
        
    def printregionlist(self):
        if len(self.regionlist) == 0:
            print('No regions are currently associated with portfolio %s.' % self.portfolioname)
        else:
            print('Regions associated with this portfolio...')
            fid = 0
            for region in self.regionlist:
                fid += 1
                print('%i: %s' % (fid, region.getregionname()))
                region.printsimboxlist(assubset=True)