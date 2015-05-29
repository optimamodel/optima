# -*- coding: utf-8 -*-
"""
Created on Thu May 28 07:56:23 2015

@author: David Kedziora
"""

class Project:
    def __init__(self,projectname):
        self.regionlist = []            # List to hold Region objects.
        self.projectname = projectname
        
    def run(self):
        """
        All process associated with the project are run here.
        Consider this as a 'main' loop for the project.
           
        Version: 2015may28 by davidkedz
        """
        from time import time
        from makeproject import Region
        
        print('\nProject %s has been activated.' % self.projectname)
        
        ## Set parameters
        verbose = 4
        show_wait = False       # Hmm. Not used? Can be left for the moment until decided as either a global/local variable.
        nsims = 5     
        
        cmdinput = ''
        cmdinputlist = []
        
        regionlist = []
        
        # The command loop begins here.
        while(cmdinput != 'q'):
            
            cmdinputlist = cmdinput.split(None,1)
            if len(cmdinputlist)>1:
        
                # Is the first word 'make'? Then create a workbook named after the rest of the string.
                if cmdinputlist[0] == 'make':
                    projectname = cmdinputlist[1]
                    starttime = time()
                    
                    print('\n\n\n1. Making project...')
                    regionlist.append(Region())
                    regionlist[-1].setregionname(projectname)
                    regionlist[-1].makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
                    regionlist[-1].getdata()['opt']['nsims'] = nsims # Reset options
                    
                    print('\n\n\n2. Updating data...')
                    from updatedata import updatedata
                    regionlist[-1].setdata(updatedata(regionlist[-1].getdata(), verbose=verbose))
                    
                    print('\n\n\n3. Viewing results...')
                    from viewresults import viewuncerresults
                    viewuncerresults(regionlist[-1].getdata()['plot']['E'])
                    
                    print('\n\n\nDONE; elapsed: %f s' % (time()-starttime))
                # Is the first word 'gpa'? Then, ideally, run geo-prioritisation analysis on subset derived from rest of the string.
                elif cmdinputlist[0] == 'gpa' and len(regionlist) > 1:
                    print('Gotcha! There is no geographical prioritisation analysis! This is just a stub.')
                    
                    # LINK TO GPA METHOD OR FUNCTION. MUST OPERATE ON A SUBSET LIST OF REGIONS.
                    
            if len(regionlist) == 0:
                print('No regions are currently associated with project %s.' % self.projectname)
            else:
                print('Regions associated with this project...')
                for region in regionlist:
                    print('   %s' % region.getregionname())
            if len(regionlist) > 1:
                print('Geographical prioritisation analysis now available.')
                print('To run this analysis over all regions, type: gpa all')       # To be extended when the time comes.
            
            print("To load a region titled 'region_name', type: make region_name")
            print('To quit, type: q')
            cmdinput = raw_input('Enter command: ')