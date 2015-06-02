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

from regionclass import Region



class Project:
    def __init__(self, projectname):
        self.regionlist = []                # List to hold Region objects.
        self.projectname = projectname
        self.cwd = os.getcwd()              # Should get the current working directory where Project object is instantiated.
        self.regd = self.cwd + '/regions'  # May be good to remove hardcoding at some stage...
        
    def run(self):
        """
        All processes associated with the project are run here.
        Consider this as a 'main' loop for the project.
           
        Version: 2015may28 by davidkedz
        """
        #from time import time
        
        print('\nProject %s has been activated.' % self.projectname)
        print('\nThe script that created this project is in...')
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
                        templist = os.listdir(self.regd);
                        
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
                        self.regionlist.append(Region(regionname))
                        self.regionlist[-1].loaddatafrom(self.regd+'/'+templist[fchoice-1])
                
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
                    
                    
#                    print('\n\n\n1. Making project...')
#                    regionlist.append(Region())
#                    regionlist[-1].setregionname(projectname)
#                    regionlist[-1].makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
#                    regionlist[-1].getdata()['opt']['nsims'] = nsims # Reset options
#                    
#                    print('\n\n\n2. Updating data...')
#                    from updatedata import updatedata
#                    regionlist[-1].setdata(updatedata(regionlist[-1].getdata(), verbose=verbose))
#                    
#                    print('\n\n\n3. Viewing results...')
#                    from viewresults import viewuncerresults
#                    viewuncerresults(regionlist[-1].getdata()['plot']['E'])
#                    
#                    print('\n\n\nDONE; elapsed: %f s' % (time()-starttime))
                    
                # Is the first word 'gpa'? Then, ideally, run geo-prioritisation analysis on subset derived from rest of the string.
                elif cmdinputlist[0] == 'gpa' and len(self.regionlist) > 1:
                    print('Gotcha! There is no geographical prioritisation analysis! This is just a stub.')
                    
                    # LINK TO GPA METHOD OR FUNCTION. MUST OPERATE ON A SUBSET LIST OF REGIONS.
                    
            print('\n--------------------\n')
            if len(self.regionlist) == 0:
                print('No regions are currently associated with project %s.' % self.projectname)
            else:
                print('Regions associated with this project...')
                fid = 0
                for region in self.regionlist:
                    fid += 1
                    print('%i: %s' % (fid, region.getregionname()))
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
        Consider this as a sub-loop for the project class.
        Note that currentregion has to be a region object.
           
        Version: 2015may28 by davidkedz
        """
        
        print('\nRegion %s is now in focus.' % currentregion.getregionname())
        
        # Initialised variables required by the particular region sub-loop.
        subinput = ''
        subinputlist = []
        
        # The command sub-loop begins here.
        while(subinput != 'r'):
            
            print('\n--------------------\n')
            currentregion.printsimboxlist()
            
#            print("To make a new region titled 'region_name', type: make region_name")
#            if len(self.regionlist) > 0:
#                print("To examine a region numbered 'region_id', type: examine region_id")
            print('To return to project level, type: r')
            subinput = raw_input('Enter command: ')
        print('\nNow examining project %s as a whole.' % self.projectname)
        return