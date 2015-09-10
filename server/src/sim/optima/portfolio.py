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
from copy import deepcopy
from numpy import arange, empty, savez_compressed, load
from project import Project
import multiprocessing
import liboptima.dataio_binary as dataio_binary

def makegpasimbox(inputs):
    # This helper function creates a GPA simbox inside a project
    # This function is declared outside the Portfolio class because
    # a) this way it can be pickled
    # b) it doesn't depend on a specific portfolio instance i.e. 'self'
    #    and therefore it shouldn't be a *method*
    currentproject,gpaname,newtotal = inputs

    print('Initialising a simulation container in project %s for this GPA.' % currentproject.getprojectname())
    tempsimbox = currentproject.createsimbox('GPA '+gpaname+' - '+currentproject.getprojectname(), isopt = True, createdefault = False)
    tempsimbox.createsim(currentproject.getprojectname()+' - Initial', forcecreate = False)
    initsimcopy = tempsimbox.createsim(currentproject.getprojectname()+' - GPA', forcecreate = True)
    tempsimbox.scalealloctototal(initsimcopy, newtotal)
    currentproject.runsimbox(tempsimbox)
    tempsimbox.simlist.remove(initsimcopy)
    return (currentproject,tempsimbox.uuid)

class Portfolio(object):
    def __init__(self, portfolioname):
        if isinstance(portfolioname,dict):
            self.fromdict(portfolioname)
        else:
            self.projectlist = []                # List to hold Project objects.
            self.gpalist = []                   # List to hold GPA runs, specifically lists of SimBoxOpt references, for quick use.
                                                # Will need to be careful about error checking when deletions are implemented.
            self.portfolioname = portfolioname
            self.cwd = os.getcwd()              # Should get the current working directory where Portfolio object is instantiated.
            self.regd = self.cwd + '/projects'   # May be good to remove hardcoding at some stage...
    

    def todict(self):
        portfoliodict = {}
        portfoliodict['projectlist'] = [x.todict() for x in self.projectlist]
        portfoliodict['gpalist'] = [x.uuid for x in self.gpalist]
        portfoliodict['portfolioname'] = self.portfolioname
        portfoliodict['cwd'] = self.cwd
        portfoliodict['regd'] = self.regd
        return portfoliodict

    def fromdict(self,portfoliodict):
        self.projectlist = [Project(x) for x in portfoliodict['projectlist']]
        self.gpalist = [r.fetch(u) for (r,u) in zip(self.projectlist,portfoliodict['gpalist'])] 
        self.portfolioname = portfoliodict['portfolioname'] 
        self.cwd = portfoliodict['cwd'] 
        self.regd = portfoliodict['regd']

    @classmethod
    def load(Portfolio,filename):
        p = dataio_binary.load(filename)
        return Portfolio(p)

    def save(self, filename):
        dataio_binary.save(self.todict(),filename)

    def run(self):
        """
        All processes associated with the portfolio are run here.
        Consider this as a 'main' loop for the portfolio.
           
        Version: 2015may28 by davidkedz
        """
        
        print('\nPortfolio %s has been activated.' % self.portfolioname)
        print('\nThe script that created this portfolio is in...')
        print(self.cwd)
        print('Project data will be sourced from...')
        print(self.regd)
        
        # Initialised variables required by the command loop.
        cmdinput = ''
        cmdinputlist = []
        
        # The command loop begins here.
        while(cmdinput != 'q'):
            
            cmdinputlist = cmdinput.split(None,1)
            if len(cmdinputlist)>1:
        
                # Is the first word 'make'? Then make a project named after the rest of the string.
                if cmdinputlist[0] == 'make':
                    projectname = cmdinputlist[1]
                    # starttime = time()
                    
                    # Checks for files in projects directory. Regex control for .json endings would be nice to implement later...
                    if len(os.listdir(self.regd)) < 1:
                        print('Not possible. There are no .json files to use in...')
                        print(self.regd)
                    else:
                        print('Which data file do you wish to load into %s?' % projectname)
                        fid = 0
                        templist = [x for x in os.listdir(self.regd) if x.endswith('.json')]
                        
                        # Displays files in projects folder along with an integer id for easy selection.
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
                        
                        # Project is created.
                        print('Creating project %s with data from: ' % projectname)
                        print(self.regd+'/'+templist[fchoice-1])
                        self.appendproject(Project.load(self.regd+'/'+templist[fchoice-1],projectname))
                
                # Is the first word 'examine'? Then enter a subloop that processes commands regarding the relevant project.
                elif cmdinputlist[0] == 'examine' and len(self.projectlist) > 0:
                    projectid = cmdinputlist[1]
                    try:
                        int(projectid)
                    except ValueError:
                        projectid = 0
                    if int(projectid) in arange(1,len(self.projectlist)+1):
                        self.examineproject(self.projectlist[int(projectid)-1])
                    else:
                        print('Project ID numbers only range from 1 to %i, inclusive.' % len(self.projectlist))
                        
                # Is the first word 'refine'? Then recalculate the BOC for the relevant project.
                elif cmdinputlist[0] == 'refine' and len(self.projectlist) > 1:
                    projectid = cmdinputlist[1]
                    try:
                        int(projectid)
                    except ValueError:
                        projectid = 0
                    if int(projectid) in arange(1,len(self.projectlist)+1):
                        self.refineprojectBOC(self.projectlist[int(projectid)-1])
                    else:
                        print('Project ID numbers only range from 1 to %i, inclusive.' % len(self.projectlist))
                        
                # Is the first word 'improve'? Then calculate BOC data for a few more budget factors.
                elif cmdinputlist[0] == 'improve' and len(self.projectlist) > 1:
                    projectid = cmdinputlist[1]
                    try:
                        int(projectid)
                    except ValueError:
                        projectid = 0
                    if int(projectid) in arange(1,len(self.projectlist)+1):
                        inputfactors = raw_input('Type a list of space-delimited multiplicative factors to test cost-effectiveness for: ')
                        try:
                            factorlist = [float(factor) for factor in inputfactors.split()]
                        except:
                            print('It was not possible to split the input into a list of floats.')
                            factorlist = []
                        self.improveprojectBOC(self.projectlist[int(projectid)-1], factorlist)
                    else:
                        print('Project ID numbers only range from 1 to %i, inclusive.' % len(self.projectlist))
                        
            # If command is 'gpa', create GPA SimBoxes in each project.
            if cmdinput == 'gpa' and len(self.projectlist) > 1:
                self.geoprioanalysis()
                
            # If command is 'review', plot all information relevant to a previous GPA run.
            if cmdinput == 'review' and len(self.gpalist) > 0:
                
                for gparun in xrange(len(self.gpalist)):
                    print('GPA %i...' % (gparun + 1))
                    for gpasimbox in self.gpalist[gparun]:
                        print(' --> %s' % gpasimbox.getname())
                    
                # Makes sure that an integer is specified.
                while fchoice not in arange(1,len(self.gpalist)+1):
                    try:
                        fchoice = int(raw_input('Choose a number between 1 and %i, inclusive: ' % len(self.gpalist)))
                    except ValueError:
                        fchoice = 0
                        continue
                    
                self.geoprioreview(self.gpalist[fchoice-1])
                
            # If command is 'qs', save to default project filenames (overwriting if necessary).
            if cmdinput == 'qs':
                self.quicksaveprojects()
                    
            print('\n--------------------\n')
            self.printprojectlist()
            print('')
            if len(self.projectlist) > 1:
                print('Geographical prioritisation analysis now available.')
                print('To run this analysis, type: gpa')
                print("To recalculate cost-effectiveness data for a project numbered 'project_id', type: refine project_id")
                print("To calculate additional cost-effectiveness data for a project numbered 'project_id', type: improve project_id")
                if len(self.gpalist) > 0:
                    print('To review results from previous GPA runs, type: review')
            
            print("To make a new project titled 'project_name', type: make project_name")
            if len(self.projectlist) > 0:
                print("To examine a project numbered 'project_id', type: examine project_id")
            print("To quicksave all projects as .json files titled by 'project_name', type: qs")
            print('To quit, type: q')
            cmdinput = raw_input('Enter command: ')
    
    # Appends project onto projectlist.
    def appendproject(self, project):
        self.projectlist.append(project)    
    
    def examineproject(self, currentproject):
        """
        All processes associated with a stored project are run here.
        Consider this as a sub-loop for the portfolio class.
        Note that currentproject has to be a project object.
           
        Version: 2015may28 by davidkedz
        """
        
        print('\nProject %s is now in focus.' % currentproject.getprojectname())
        
        # Initialised variables required by the particular project sub-loop.
        subinput = ''
        subinputlist = []
        
        # The command sub-loop begins here.
        while(subinput != 'r'):
            
            subinputlist = subinput.split(None,1)
            if len(subinputlist)>1:
            
                # Is the first word 'check'? Then display project-specific data.
                if subinputlist[0] == 'check':
                    if subinputlist[1] == 'data':
                        currentproject.printdata();
                    elif subinputlist[1] == 'metadata':
                        currentproject.printmetadata();
                    elif subinputlist[1] == 'options':
                        currentproject.printoptions();
                    elif subinputlist[1] == 'programs':
                        currentproject.printprograms();
                
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
                        currentproject.createsimbox(simboxname, createdefault = False)
                    if fchoice == 2:
                        currentproject.createsimbox(simboxname, isopt = True, createdefault = False)
                        
                # Is the first word 'sim'? Then initialise a new sim object in a simbox of choice.
                elif subinputlist[0] == 'sim' and len(currentproject.simboxlist) > 0:
                    simname = subinputlist[1]                    
                    
                    fchoice = 0
                    while fchoice not in arange(1,len(currentproject.simboxlist)+1):
                        try:
                            fchoice = int(raw_input('Enter the ID number of a simulation container (between 1 and %i, inclusive): ' % len(currentproject.simboxlist)))
                        except ValueError:
                            fchoice = 0
                            continue
                    
                    currentproject.createsiminsimbox(simname, currentproject.simboxlist[fchoice-1])
                
                # Is the first word 'run'? Then process all simulation objects in a simbox of choice.
                elif subinputlist[0] == 'run' and len(currentproject.simboxlist) > 0:
                    simboxid = subinputlist[1]                
                    
                    try:
                        int(simboxid)
                    except ValueError:
                        simboxid = 0
                    if int(simboxid) in arange(1,len(currentproject.simboxlist)+1):
                        currentproject.runsimbox(currentproject.simboxlist[int(simboxid)-1])
                    else:
                        print('Simulation container ID numbers only range from 1 to %i, inclusive.' % len(currentproject.simboxlist))
                
                # Is the first word 'plot' or 'multiplot'? Then plot all the processed results in a simbox of choice.
                elif (subinputlist[0] == 'plot' or 'multiplot') and len(currentproject.simboxlist) > 0:
                    simboxid = subinputlist[1]                
                    
                    try:
                        int(simboxid)
                    except ValueError:
                        simboxid = 0
                    if int(simboxid) in arange(1,len(currentproject.simboxlist)+1):
                        currentproject.plotsimbox(currentproject.simboxlist[int(simboxid)-1], multiplot = (True if subinputlist[0] == 'multiplot' else False))
                    else:
                        print('Simulation container ID numbers only range from 1 to %i, inclusive.' % len(currentproject.simboxlist))
            
            print('\n--------------------\n')
            currentproject.printsimboxlist(assubset=False)
            if len(currentproject.simboxlist) == 0:
                print("Processing cannot begin without the creation of a container.")
            
            print("\nTo check project specifics, where 'x' is as follows, type: check x")
            print("Placeholder 'x' can be: 'data', 'metadata', 'options', 'programs'")
            print("To make a new simulation container in this project titled 'simbox_name', type: make simbox_name")
            if len(currentproject.simboxlist) > 0:
                print("To initialise a new simulation titled 'sim_name', type: sim sim_name")
                print("To process all unprocessed simulations in 'simbox_id', type: run simbox_id")
                print("This will be a simple run or an optimisation depending on simulation container type.")
                print("To plot each processed simulation in 'simbox_id', type: plot simbox_id")
                print("To plot all processed simulations in 'simbox_id', type: multiplot simbox_id")
            print('To return to portfolio level, type: r')
            subinput = raw_input('Enter command: ')
        print('\nNow examining portfolio %s as a whole.' % self.portfolioname)
        return
        
    def printprojectlist(self):
        if len(self.projectlist) == 0:
            print('No projects are currently associated with portfolio %s.' % self.portfolioname)
        else:
            print('Projects associated with this portfolio...')
            fid = 0
            for project in self.projectlist:
                fid += 1
                print('%i: %s' % (fid, project.getprojectname()))
                project.printsimboxlist(assubset=True)
    
    def quicksaveprojects(self):
        for currentproject in self.projectlist:
            currentproject.save(self.regd + '/' + currentproject.getprojectname() + '.json')

    # Creates a duplicate of a project.
    # Note: Everything is deep-copied, but a new uuid is given to mark a unique project.
    def duplicateproject(self, targetproject):
        newproject = deepcopy(targetproject)
        newproject.genuuid()
        self.appendproject(newproject)
        return newproject
            
#%% GPA Methods

    # Break an aggregate project (e.g. a nation) into subprojects (e.g. districts), according to a provided population and prevalence data file.
    def splitcombinedproject(self, aggregateproject, popprevfile):
        
        from xlrd import open_workbook  # For opening Excel workbooks.
        
        inbook = open_workbook(popprevfile)
        summarysheet = inbook.sheet_by_name('Summary - sub-populations')

        # Determine project names from summary sheet.
        subprojectlist = []
        for rowindex in xrange(summarysheet.nrows):
            if summarysheet.cell_value(rowindex, 0) == 'National total':
                break
            if summarysheet.cell_type(rowindex, 0) == 2:    # Check if 1st cell in row is a number.
                subprojectlist.append(summarysheet.cell_value(rowindex, 1))
        print subprojectlist
        print len(subprojectlist)
        
        for subprojectname in subprojectlist:
            try:
                print('Creating project: %s' % subprojectname)
                subprojectsheet = inbook.sheet_by_name(subprojectname)
                newproject = self.duplicateproject(aggregateproject)
                newproject.setprojectname(subprojectname)
                
#                for rowindex in xrange(districtsheet.nrows):
#                    inrow = districtsheet.row(rowindex)
#                    for colindex in xrange(len(inrow)):
#                        celldata = districtsheet.cell_value(rowindex, colindex)
                
            except:
                print('There is a problem loading a district sheet. All subsequent actions are cancelled.')
        
        # Finalise conversion by removing original aggregate project.
        self.projectlist.remove(aggregateproject)



    # The GPA algorithm.
    def geoprioanalysis(self, gpaname = 'Test', usebatch=False):
        
        # First, choose 'spend' factors for the construction of your Budget Objective Curve.
        varfactors = [0.0, 0.3, 0.6, 1.0, 1.8, 3.2, 10.0]
        
        # If a loaded project does not store Budget Objective data in its json file, then calculate some.
        for currentproject in self.projectlist:
            if not currentproject.hasBOC():
                print('Project %s has no Budget Objective Curve. Initialising calculation.' % currentproject.getprojectname())
                currentproject.developBOC(varfactors)
            else:
                print('Project %s already has a Budget Objective Curve.' % currentproject.getprojectname())
            
        # The actual optimisation process.
        from geoprioritisation import gpaoptimisefixedtotal
        
        newtotals = gpaoptimisefixedtotal(self.projectlist)
        
        # Assemble the inputs for makegpasimbox()
        inputs = []
        for (r,newtotal) in zip(self.projectlist,newtotals):
            inputs.append((r,'Test',newtotal))

        if usebatch:
            pool = multiprocessing.Pool()
            outputs = pool.map(makegpasimbox,inputs)
        else:
            outputs = [makegpasimbox(y) for y in inputs]

        # Update the projectlist now that all of the projects have had GPA run on them
        # Otherwise, the simboxlist references will be broken when their parent projects
        # (the ones inside the array 'outputs') go out of scope
        self.projectlist = []
        self.gpalist = []
        for x in outputs:
            r,simboxid = x
            self.projectlist.append(r)
            self.gpalist.append(r.fetch(simboxid))

    # Iterate through loaded projects. Develop default BOCs if they do not have them.
    def geoprioreview(self, gpasimboxlist):
        
        for gpasimbox in gpasimboxlist:
            print(gpasimbox.getname())
            gpasimbox.getproject().plotsimbox(gpasimbox, multiplot = True)   # Note: Really stupid excessive way of doing all plots. May simplify later.
        
        # Display GPA results for debugging purposes. Modified version of code in geoprioritisation.py. May fuse later.
        totsumin = 0
        totsumopt = 0
        totsumgpaopt = 0
        esttotsuminobj = 0
        esttotsumoptobj = 0
        esttotsumgpaoptobj = 0
        realtotsuminobj = 0
        realtotsumoptobj = 0
        realtotsumgpaoptobj = 0
        for i in xrange(len(gpasimboxlist)):
            r = gpasimboxlist[i].getproject()
            projectname = r.getprojectname()

            print('Project %s...' % projectname)
            sumin = sum(gpasimboxlist[i].simlist[0].alloc)
            sumopt = sum(gpasimboxlist[i].simlist[1].alloc)
            sumgpaopt = sum(gpasimboxlist[i].simlist[2].alloc)
            estsuminobj = r.getBOCspline()([sumin])
            estsumoptobj = r.getBOCspline()([sumopt])
            estsumgpaoptobj = r.getBOCspline()([sumgpaopt])
            realsuminobj = gpasimboxlist[i].simlist[0].calculateobjectivevalue()
            realsumoptobj = gpasimboxlist[i].simlist[1].calculateobjectivevalue(normaliser = gpasimboxlist[i].simlist[0])
            realsumgpaoptobj = gpasimboxlist[i].simlist[2].calculateobjectivevalue(normaliser = gpasimboxlist[i].simlist[0])
            
            import matplotlib.pyplot as plt
            ax = r.plotBOCspline(returnplot = True)
            ms = 10
            mw = 2
            ax.plot(sumopt, estsumoptobj, 'x', markersize = ms, markeredgewidth = mw, label = 'Init. Opt. Est.')
            ax.plot(sumopt, realsumoptobj, '+', markersize = ms, markeredgewidth = mw, label = 'Init. Opt. Real')
            ax.plot(sumgpaopt, estsumgpaoptobj, 'x', markersize = ms, markeredgewidth = mw, label = 'GPA Opt. Est.')
            ax.plot(sumgpaopt, realsumgpaoptobj, '+', markersize = ms, markeredgewidth = mw, label = 'GPA Opt. Real')
            ax.legend(loc='best')
            plt.show()
            
            if sumin == sumopt:
                print('Initial Unoptimised/Optimised Budget Total: $%.2f' % sumin)
            else:
                print('Initial Unoptimised Budget Total: $%.2f' % sumin)
                print('Initial Optimised Budget Total: $%.2f' % sumopt)
            print('GPA Optimised Budget Total: $%.2f' % sumgpaopt)
            print
            if not sumin == sumopt: print('Initial Unoptimised Objective Estimate (BOC): %f' % estsuminobj)
            print('Initial Optimised Objective Estimate (BOC): %f' % estsumoptobj)
            print('GPA Optimised Objective Estimate (BOC): %f' % estsumgpaoptobj)
            print
            if not sumin == sumopt: print('Initial Unoptimised BOC Derivative: %.3e' % r.getBOCspline().derivative()(sumin))
            print('Initial Optimised BOC Derivative: %.3e' % r.getBOCspline().derivative()(sumopt))
            print('GPA Optimised BOC Derivative: %.3e' % r.getBOCspline().derivative()(sumgpaopt))
            print
            print('Initial Unoptimised Real Objective: %f' % realsuminobj)
            print('Initial Optimised Real Objective: %f' % realsumoptobj)
            print('GPA Optimised Real Objective: %f' % realsumgpaoptobj)
            print('BOC Estimate was off for %s objective by: %f (%f%%)' % (projectname, estsumgpaoptobj-realsumgpaoptobj, 100*abs(estsumgpaoptobj-realsumgpaoptobj)/realsumgpaoptobj))
            print('\n')
            
            
            print('%40s%20s%20s' % ('Unoptimised...', 'Optimised...', 'GPA Optimised...'))
            for x in xrange(len(r.metadata['inputprograms'])):
                print('%-20s%20.2f%20.2f%20.2f' % (r.metadata['inputprograms'][x]['short_name']+':',r.simboxlist[-1].simlist[0].alloc[x],r.simboxlist[-1].simlist[1].alloc[x],r.simboxlist[-1].simlist[2].alloc[x]))
            print('\n')
            
            totsumin += sumin
            totsumopt += sumopt
            totsumgpaopt += sumgpaopt
            esttotsuminobj += estsuminobj
            esttotsumoptobj += estsumoptobj
            esttotsumgpaoptobj += estsumgpaoptobj
            realtotsuminobj += realsuminobj
            realtotsumoptobj += realsumoptobj
            realtotsumgpaoptobj += realsumgpaoptobj
            
        print('\nGPA Aggregated Results...\n')
        if totsumin == totsumopt:
            print('Initial Unoptimised/Optimised Budget Grand Total: $%.2f' % totsumin)
        else:
            print('Initial Unoptimised Budget Grand Total: $%.2f' % totsumin)
            print('Initial Optimised Budget Grand Total: $%.2f' % totsumopt)
        print('GPA Optimised Budget Grand Total: $%.2f' % totsumgpaopt)
        print
        if not totsumin == totsumopt: print('Initial Unoptimised Objective Sum Estimate (BOC): %f' % esttotsuminobj)
        print('Initial Optimised Objective Sum Estimate (BOC): %f' % esttotsumoptobj)
        print('GPA Optimised Objective Sum Estimate (BOC): %f' % esttotsumgpaoptobj)
        print('Aggregate Objective Improvement Estimate (BOC): %f (%f%%)' % (esttotsumgpaoptobj-esttotsumoptobj, 100*(esttotsumoptobj-esttotsumgpaoptobj)/esttotsumoptobj))
        print
        print('Initial Unoptimised Real Objective Sum: %f' % realtotsuminobj)
        print('Initial Optimised Real Objective Sum: %f' % realtotsumoptobj)
        print('GPA Optimised Real Objective Sum: %f' % realtotsumgpaoptobj)
        print('BOC Estimate was off for aggregate objective by: %f (%f%%)' % (esttotsumgpaoptobj-realtotsumgpaoptobj, 100*abs(esttotsumgpaoptobj-realtotsumgpaoptobj)/realtotsumgpaoptobj))
        print('Real Aggregate Objective Improvement (Before Individual Optimisation): %f (%f%%)' % (realtotsumgpaoptobj-realtotsuminobj, 100*(realtotsuminobj-realtotsumgpaoptobj)/realtotsuminobj))
        print('Real Aggregate Objective Improvement (After Individual Optimisation): %f (%f%%)' % (realtotsumgpaoptobj-realtotsumoptobj, 100*(realtotsumoptobj-realtotsumgpaoptobj)/realtotsumoptobj))        
        print('\n')
        

    def refineprojectBOC(self, project):
        project.recalculateBOC()
        
    def improveprojectBOC(self, project, factorlist):
        project.developBOC(factorlist, extendresults = True)