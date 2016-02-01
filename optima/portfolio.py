from optima import odict, getdate, today, uuid, dcp, objrepr, printv, scaleratio, OptimaException # Import utilities
from optima import gitinfo, tic, toc # Import functions
from optima import __version__ # Get current version

from optima import defaultobjectives, asd, Project

#######################################################################################################
## Portfolio class -- this contains Projects and GA optimisations
#######################################################################################################

budgeteps = 1e-8        # Project optimisations will fail for budgets that are optimised by GA to be zero. This avoids zeros.

class Portfolio(object):
    """
    PORTFOLIO

    The super Optima portfolio class.

    Version: 2016jan20 by davidkedz
    """
    
    #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a portfolio
    #######################################################################################################

    def __init__(self, name='default', projects=None, gaoptims=None):
        ''' Initialize the portfolio '''

        ## Set name
        self.name = name

        ## Define the structure sets
        self.projects = odict()
        if projects is not None: self.addprojects(projects)
        self.gaoptims = gaoptims if gaoptims else odict()

        ## Define metadata
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.version = __version__
        self.gitbranch, self.gitversion = gitinfo()

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '            Portfolio name: %s\n' % self.name
        output += '\n'
        output += '        Number of projects: %i\n' % len(self.projects)
        output += 'Number of GA Optimizations: %i\n' % len(self.gaoptims)
        output += '\n'
        output += '            Optima version: %0.1f\n' % self.version
        output += '              Date created: %s\n'    % getdate(self.created)
        output += '             Date modified: %s\n'    % getdate(self.modified)
        output += '                Git branch: %s\n'    % self.gitbranch
        output += '               Git version: %s\n'    % self.gitversion
        output += '                       UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output


    #######################################################################################################
    ## Methods to handle common tasks
    #######################################################################################################

    def addprojects(self, projects, verbose=2):
        ''' Store a project within portfolio '''
        printv('Adding project to portfolio...', 2, verbose)
        if type(projects)==Project: projects = [projects]
        if type(projects)==list:
            for project in projects: 
                self.projects[project.uid] = project        
                printv('\nAdded project "%s" to portfolio "%s".' % (project.name, self.name), 2, verbose)
        
    def getdefaultbudgets(self, progsetnames=None, verbose=2):
        ''' Get the default allocation totals of each project, using the progset names or indices specified '''
        budgets = []
        printv('Getting budgets...', 2, verbose)
        
        # Validate inputs
        if progsetnames==None:
            printv('\nWARNING: no progsets specified. Using default budget from first saved progset for each project for portfolio "%s".' % (self.name), 4, verbose)
            progsetnames = [0]*len(self.projects)
        if not len(progsetnames)==len(self.projects):
            printv('WARNING: %i program set names/indices were provided, but portfolio "%s" contains %i projects. OVERWRITING INPUTS and using default budget from first saved progset for each project.' % (len(progsetnames), self.name, len(self.projects)), 4, verbose)
            progsetnames = [0]*len(self.projects)

        # Loop over projects & get defaul budget for each, if you can
        for pno, p in enumerate(self.projects.values()):

            # Crash if any project doesn't have progsets
            if not p.progsets: 
                errormsg = 'Project "%s" does not have a progset. Cannot get default budgets.'
                raise OptimaException(errormsg)

            # Check that the progsets that were specified are indeed valid. They could be a string or a list index, so must check both
            if isinstance(progsetnames[pno],str) and progsetnames[pno] not in [progset.name for progset in p.progsets]:
                printv('\nCannot find progset "%s" in project "%s". Using progset "%s" instead.' % (progsetnames[pno], p.name, p.progsets[progsetnames[0]].name), 3, verbose)
                pno=0
            elif isinstance(progsetnames[pno],int) and len(p.progsets)<=progsetnames[pno]:
                printv('\nCannot find progset number %i in project "%s", there are only %i progsets in that project. Using progset 0 instead.' % (progsetnames[pno], p.name, len(p.progsets)), 1, verbose)
                pno=0
            else: 
                printv('\nCannot understand what program set to use for project "%s". Using progset 0 instead.' % (p.name), 3, verbose)
                pno=0            
                
            printv('\nAdd default budget from progset "%s" for project "%s" and portfolio "%s".' % (p.progsets[progsetnames[pno]].name, p.name, self.name), 4, verbose)
            budgets.append(sum(p.progsets[progsetnames[pno]].getdefaultbudget().values()))
        
        return budgets
    
    
    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################
        
        
    def genBOCs(self, objectives=None, progsetnames=None, parsetnames=None, maxtime=None, forceregen=False, verbose=2):
        ''' Loop through stored projects and construct budget-outcome curves '''
        printv('Generating BOCs...', 1, verbose)
        
        # Validate inputs
        if objectives == None: 
            printv('WARNING, you have called genBOCs on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        if progsetnames==None:
            printv('\nWARNING: no progsets specified. Using first saved progset for each project for portfolio "%s".' % (self.name), 3, verbose)
            progsetnames = [0]*len(self.projects)
        if not len(progsetnames)==len(self.projects):
            printv('WARNING: %i program set names/indices were provided, but portfolio "%s" contains %i projects. OVERWRITING INPUTS and using first saved progset for each project.' % (len(progsetnames), self.name, len(self.projects)), 1, verbose)
            progsetnames = [0]*len(self.projects)
        if parsetnames==None:
            printv('\nWARNING: no parsets specified. Using first saved parset for each project for portfolio "%s".' % (self.name), 3, verbose)
            parsetnames = [0]*len(self.projects)
        if not len(parsetnames)==len(self.projects):
            printv('WARNING: %i parset names/indices were provided, but portfolio "%s" contains %i projects. OVERWRITING INPUTS and using first saved parset for each project.' % (len(parsetnames), self.name, len(self.projects)), 1, verbose)
            parsetnames = [0]*len(self.projects)

        for pno, p in enumerate(self.projects.values()):
            if p.getBOC(objectives) == None or forceregen:

                # Crash if any project doesn't have progsets
                if not p.progsets or not p.parsets: 
                    errormsg = 'Project "%s" does not have a progset and/or a parset, can''t generate a BOC.'
                    raise OptimaException(errormsg)
    
                # Check that the progsets that were specified are indeed valid. They could be a string or a list index, so must check both
                if isinstance(progsetnames[pno],str) and progsetnames[pno] not in [progset.name for progset in p.progsets.values()]:
                    printv('\nCannot find progset "%s" in project "%s". Using progset "%s" instead.' % (progsetnames[pno], p.name, p.progsets[0].name), 1, verbose)
                    pno=0
                elif isinstance(progsetnames[pno],int) and len(p.progsets)<=progsetnames[pno]:
                    printv('\nCannot find progset number %i in project "%s", there are only %i progsets in that project. Using progset 0 instead.' % (progsetnames[pno], p.name, len(p.progsets)), 1, verbose)
                    pno=0
                else: 
                    printv('\nCannot understand what program set to use for project "%s". Using progset 0 instead.' % (p.name), 3, verbose)
                    pno=0            

                # Check that the progsets that were specified are indeed valid. They could be a string or a list index, so must check both
                if isinstance(parsetnames[pno],str) and parsetnames[pno] not in [parset.name for parset in p.parsets.values()]:
                    printv('\nCannot find parset "%s" in project "%s". Using pargset "%s" instead.' % (progsetnames[pno], p.name, p.parsets[0].name), 1, verbose)
                    pno=0
                elif isinstance(parsetnames[pno],int) and len(p.parsets)<=parsetnames[pno]:
                    printv('\nCannot find parset number %i in project "%s", there are only %i parsets in that project. Using parset 0 instead.' % (parsetnames[pno], p.name, len(p.parsets)), 1, verbose)
                    pno=0
                else: 
                    printv('\nCannot understand what parset to use for project "%s". Using parset 0 instead.' % (p.name), 3, verbose)
                    pno=0            

                # Actually generate te BOCs
                printv('WARNING, project %s does not have BOC, or else it does but you want to regenerate it. Generating one using parset %s and progset %s... ' % (p.name, p.parsets[parsetnames[pno]].name, p.progsets[progsetnames[pno]].name), 1, verbose)
                p.delBOC(objectives)    # Delete BOCs in case forcing regeneration.
                p.genBOC(parsetname=p.parsets[parsetnames[pno]].name, progsetname=p.progsets[progsetnames[pno]].name, objectives=objectives, maxtime=maxtime)

            else:
                printv('Project %s contains a BOC, no need to generate... ' % p.name, 2, verbose)
                
                
    def plotBOCs(self, objectives=None, initbudgets=None, optbudgets=None, verbose=2):
        ''' Loop through stored projects and plot budget-outcome curves '''
        printv('Plotting BOCs...', 2, verbose)
        
        if initbudgets == None: initbudgets = [None]*len(self.projects)
        if optbudgets == None: optbudgets = [None]*len(self.projects)
        if objectives == None: 
            printv('WARNING, you have called plotBOCs on portfolio %s without specifying objectives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
            
        if not len(self.projects) == len(initbudgets) or not len(self.projects) == len(optbudgets):
            errormsg = 'Error: Plotting BOCs for %i projects with %i initial budgets (%i required) and %i optimal budgets (%i required).' % (len(self.projects), len(initbudgets), len(self.projects), len(optbudgets), len(self.projects))
            raise OptimaException(errormsg)
        
        # Loop for BOCs and then BOC derivatives.
        for inderiv in [False,True]:
            c = 0
            for p in self.projects.values():
                p.plotBOC(objectives=objectives, deriv=inderiv, initbudget=initbudgets[c], optbudget=optbudgets[c])
                c += 1
            
            
    def minBOCoutcomes(self, objectives, progsetnames=None, parsetnames=None, seedbudgets=None, maxtime=None, verbose=2):
        ''' Loop through project BOCs corresponding to objectives and minimise net outcome '''
        printv('Calculating minimum BOC outcomes...', 2, verbose)

        # Check inputs
        if objectives == None: 
            printv('WARNING, you have called minBOCoutcomes on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        if progsetnames==None:
            printv('\nWARNING: no progsets specified. Using first saved progset for each project for portfolio "%s".' % (self.name), 3, verbose)
            progsetnames = [0]*len(self.projects)
        if not len(progsetnames)==len(self.projects):
            printv('WARNING: %i program set names/indices were provided, but portfolio "%s" contains %i projects. OVERWRITING INPUTS and using first saved progset for each project.' % (len(progsetnames), self.name, len(self.projects)), 1, verbose)
            progsetnames = [0]*len(self.projects)
        if parsetnames==None:
            printv('\nWARNING: no parsets specified. Using first saved parset for each project for portfolio "%s".' % (self.name), 3, verbose)
            parsetnames = [0]*len(self.projects)
        if not len(parsetnames)==len(self.projects):
            printv('WARNING: %i parset names/indices were provided, but portfolio "%s" contains %i projects. OVERWRITING INPUTS and using first saved parset for each project.' % (len(parsetnames), self.name, len(self.projects)), 1, verbose)
            parsetnames = [0]*len(self.projects)
        
        # Initialise internal parameters
        BOClist = []
        grandtotal = objectives['budget']
        
        # Scale seedbudgets just in case they don't add up to the required total.
        if not seedbudgets == None:
            seedbudgets = scaleratio(seedbudgets, objectives['budget'])
            
        for pno,p in enumerate(self.projects.values()):
            
            if p.getBOC(objectives) is not None:

                # Crash if any project doesn't have progsets
                if not p.progsets or not p.parsets: 
                    errormsg = 'Project "%s" does not have a progset and/or a parset, can''t generate a BOC.'
                    raise OptimaException(errormsg)
    
                # Check that the progsets that were specified are indeed valid. They could be a string or a list index, so must check both
                if isinstance(progsetnames[pno],str) and progsetnames[pno] not in [progset.name for progset in p.progsets]:
                    printv('\nCannot find progset "%s" in project "%s". Using progset "%s" instead.' % (progsetnames[pno], p.name, p.progsets[0].name), 3, verbose)
                    pno=0
                elif isinstance(progsetnames[pno],int) and len(p.progsets)<=progsetnames[pno]:
                    printv('\nCannot find progset number %i in project "%s", there are only %i progsets in that project. Using progset 0 instead.' % (progsetnames[pno], p.name, len(p.progsets)), 1, verbose)
                    pno=0
                else: 
                    printv('\nCannot understand what program set to use for project "%s". Using progset 0 instead.' % (p.name), 3, verbose)
                    pno=0            
    
                # Check that the parsets that were specified are indeed valid. They could be a string or a list index, so must check both
                if isinstance(parsetnames[pno],str) and parsetnames[pno] not in [parset.name for parset in p.parsets]:
                    printv('\nCannot find parset "%s" in project "%s". Using pargset "%s" instead.' % (progsetnames[pno], p.name, p.parsets[0].name), 1, verbose)
                    pno=0
                elif isinstance(parsetnames[pno],int) and len(p.parsets)-1<=parsetnames[pno]:
                    printv('\nCannot find parset number %i in project "%s", there are only %i parsets in that project. Using parset 0 instead.' % (parsetnames[pno], p.name, len(p.parsets)), 1, verbose)
                    pno=0
                else: 
                    printv('\nCannot understand what parset to use for project "%s". Using parset 0 instead.' % (p.name), 3, verbose)
                    pno=0
                
                    printv('WARNING, project %s does not have BOC. Generating one using parset %s and progset %s... ' % (p.name, p.parsets[0].name, p.progsets[0].name), 1, verbose)
                    p.genBOC(parsetname=p.parsets[parsetnames[pno]].name, progsetname=p.progsets[progsetnames[pno]].name, objectives=objectives, maxtime=maxtime)

            BOClist.append(p.getBOC(objectives))
            
        return minBOCoutcomes(BOClist, grandtotal, budgetvec=seedbudgets, maxtime=maxtime)
        
        
    def fullGA(self, objectives=None, budgetratio=None, maxtime=None, doplotBOCs=False, verbose=2):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''
        printv('Performing full geospatial analysis', 1, verbose)
        
        GAstart = tic()

		# Check inputs
        if objectives == None: 
            printv('WARNING, you have called fullGA on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        objectives = dcp(objectives)    # NOTE: Yuck. Somebody will need to check all of Optima for necessary dcps.
        print('HERE1'); print(objectives)
        
        gaoptim = GAOptim(objectives = objectives)
        self.gaoptims[gaoptim.uid] = gaoptim
        
        if budgetratio == None: budgetratio = self.getdefaultbudgets()
        initbudgets = scaleratio(budgetratio,objectives['budget'])
        print('HERE2'); print(objectives); print(initbudgets)
        
        optbudgets = self.minBOCoutcomes(objectives, seedbudgets = initbudgets, maxtime = maxtime)
        if doplotBOCs: self.plotBOCs(objectives, initbudgets = initbudgets, optbudgets = optbudgets)
        
        gaoptim.complete(self.projects, initbudgets,optbudgets, maxtime=maxtime)
        outputstring = gaoptim.printresults()
        
        self.outputstring = outputstring # Store the results as an output string
        
        toc(GAstart)
        
        
        
        
#%% Functions for geospatial analysis

def constrainbudgets(x, grandtotal, minbound):
    
    # First make sure all values are not below the respective minimum bounds.
    for i in xrange(len(x)):
        if x[i] < minbound[i]:
            x[i] = minbound[i]
    
    # Then scale all excesses over the minimum bounds so that the new sum is grandtotal.
    constrainedx = []
    for i in xrange(len(x)):
        xi = (x[i] - minbound[i])*(grandtotal - sum(minbound))/(sum(x) - sum(minbound)) + minbound[i]
        constrainedx.append(xi)
    
    return constrainedx

def objectivecalc(x, BOClist, grandtotal, minbound):
    ''' Objective function. Sums outcomes from all projects corresponding to budget list x. '''
    x = constrainbudgets(x, grandtotal, minbound)
    
    totalobj = 0
    for i in xrange(len(x)):
        totalobj += BOClist[i].getoutcome([x[i]])[-1]     # Outcomes are currently passed to and from pchip as lists.
    return totalobj
    
def minBOCoutcomes(BOClist, grandtotal, budgetvec=None, minbound=None, maxiters=1000, maxtime=None, verbose=2):
    ''' Actual runs geospatial optimisation across provided BOCs. '''
    printv('Calculating minimum outcomes', 2, verbose)
    
    if minbound == None: minbound = [0]*len(BOClist)
    if budgetvec == None: budgetvec = [grandtotal/len(BOClist)]*len(BOClist)
    if not len(budgetvec) == len(BOClist): 
        errormsg = 'Geospatial analysis is minimising %i BOCs with %i initial budgets' % (len(BOClist), len(budgetvec))
        raise OptimaException(errormsg)
        
    args = {'BOClist':BOClist, 'grandtotal':grandtotal, 'minbound':minbound}    
    
#    budgetvecnew, fval, exitflag, output = asd(objectivecalc, budgetvec, args=args, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
    X, FVAL, EXITFLAG, OUTPUT = asd(objectivecalc, budgetvec, args=args, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)
    X = constrainbudgets(X, grandtotal, minbound)

    return X



#%% Geospatial analysis runs are stored in a GAOptim object.

class GAOptim(object):
    """
    GAOPTIM

    Short for geospatial analysis optimisation. This class stores results from an optimisation run.

    Version: 2016jan26 by davidkedz
    """
        #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a portfolio
    #######################################################################################################

    def __init__(self, name='default', objectives = None):
        ''' Initialize the GA optim object '''

        ## Define the structure sets
        self.objectives = objectives
        self.resultpairs = odict()

        ## Define other quantities
        self.name = name

        ## Define metadata
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.version = __version__
        self.gitbranch, self.gitversion = gitinfo()

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '      GAOptim name: %s\n'    % self.name
        output += '\n'
        output += '    Optima version: %0.1f\n' % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def complete(self, projects, initbudgets, optbudgets, parsetnames=None, progsetnames=None, maxtime=None, verbose=2):
        ''' Runs final optimisations for initbudgets and optbudgets so as to summarise GA optimisation '''
        printv('Finalizing geospatial analysis...', 1, verbose)
        
        # Validate inputs
        if not len(projects) == len(initbudgets) or not len(projects) == len(optbudgets):
            errormsg = 'Cannot complete optimisations for %i projects given %i initial budgets (%i required) and %i optimal budgets (%i required).' % (len(self.projects), len(initbudgets), len(self.projects), len(optbudgets), len(self.projects))
            raise OptimaException(errormsg)
        if progsetnames==None:
            printv('\nWARNING: no progsets specified. Using first saved progset for each project.', 3, verbose)
            progsetnames = [0]*len(projects)
        if not len(progsetnames)==len(projects):
            printv('WARNING: %i program set names/indices were provided, but %i projects. OVERWRITING INPUTS and using first saved progset for each project.' % (len(progsetnames), len(self.projects)), 1, verbose)
            progsetnames = [0]*len(projects)
        if parsetnames==None:
            printv('\nWARNING: no parsets specified. Using first saved parset for each project.', 3, verbose)
            parsetnames = [0]*len(projects)
        if not len(parsetnames)==len(projects):
            printv('WARNING: %i parset names/indices were provided, but %i projects. OVERWRITING INPUTS and using first saved parset for each project.' % (len(parsetnames), len(self.projects)), 1, verbose)
            parsetnames = [0]*len(projects)

        # Project optimisation processes (e.g. Optims and Multiresults) are not saved to Project, only GA Optim.
        # This avoids name conflicts for Optims/Multiresults from multiple GAOptims (via project add methods) that we really don't need.
        for pno,p in enumerate(projects.values()):
            self.resultpairs[p.uid] = odict()

            # Crash if any project doesn't have progsets
            if not p.progsets or not p.parsets: 
                errormsg = 'Project "%s" does not have a progset and/or a parset, can''t generate a BOC.'
                raise OptimaException(errormsg)

            # Check that the progsets that were specified are indeed valid. They could be a string or a list index, so must check both
            if isinstance(progsetnames[pno],str) and progsetnames[pno] not in [progset.name for progset in p.progsets]:
                printv('\nCannot find progset "%s" in project "%s". Using progset "%s" instead.' % (progsetnames[pno], p.name, p.progsets[0].name), 1, verbose)
                pno=0
            elif isinstance(progsetnames[pno],int) and len(p.progsets)<=progsetnames[pno]:
                printv('\nCannot find progset number %i in project "%s", there are only %i progsets in that project. Using progset 0 instead.' % (progsetnames[pno], p.name, len(p.progsets)), 1, verbose)
                pno=0
            else: 
                printv('\nCannot understand what program set to use for project "%s". Using progset 0 instead.' % (p.name), 3, verbose)
                pno=0            

            # Check that the parsets that were specified are indeed valid. They could be a string or a list index, so must check both
            if isinstance(parsetnames[pno],str) and parsetnames[pno] not in [parset.name for parset in p.parsets]:
                printv('\nCannot find parset "%s" in project "%s". Using pargset "%s" instead.' % (progsetnames[pno], p.name, p.parsets[0].name), 1, verbose)
                pno=0
            elif isinstance(parsetnames[pno],int) and len(p.parsets)<=parsetnames[pno]:
                printv('\nCannot find parset number %i in project "%s", there are only %i parsets in that project. Using parset 0 instead.' % (parsetnames[pno], p.name, len(p.parsets)), 1, verbose)
                pno=0
            else: 
                printv('\nCannot understand what parset to use for project "%s". Using parset 0 instead.' % (p.name), 3, verbose)
                pno=0

            initobjectives = dcp(self.objectives)
            initobjectives['budget'] = initbudgets[pno] + budgeteps
            printv("Generating initial-budget optimization for project '%s'." % p.name, 2, verbose)
            self.resultpairs[p.uid]['init'] = p.minoutcomes(name=p.name+' GA initial', parsetname=p.parsets[parsetnames[pno]].name, progsetname=p.progsets[progsetnames[pno]].name, objectives=initobjectives, maxtime=maxtime, saveprocess=False)
            preibudget = initobjectives['budget']
            postibudget = self.resultpairs[p.uid]['init'].budget[-1]
            assert preibudget==sum(postibudget[:])
            
            optobjectives = dcp(self.objectives)
            optobjectives['budget'] = optbudgets[pno] + budgeteps
            printv("Generating optimal-budget optimization for project '%s'." % p.name, 2, verbose)
            self.resultpairs[p.uid]['opt'] = p.minoutcomes(name=p.name+' GA optimal', parsetname=p.parsets[parsetnames[pno]].name, progsetname=p.progsets[progsetnames[pno]].name, objectives=optobjectives, maxtime=maxtime, saveprocess=False)
            preobudget = optobjectives['budget']
            postobudget = self.resultpairs[p.uid]['opt'].budget[-1]
            assert preobudget==sum(postobudget[:])

    def printresults(self, verbose=2):
        ''' Just displays results related to the GA run '''
        printv('Printing results...', 2, verbose)
        
        sumbudgetsinit = 0
        sumbudgetsimp = 0
        sumbudgetsgaopt = 0
        sumoutcomeinit = 0
        sumoutcomeimp = 0
        sumoutcomegaopt = 0
        
        output = ''        
        
        for x in self.resultpairs:          # WARNING: Nervous about all this slicing. Problems foreseeable if format changes.
            projectname = self.resultpairs[x]['init'].project.name
            initalloc = self.resultpairs[x]['init'].budget[0]
            impalloc = self.resultpairs[x]['init'].budget[-1]       # Calling this impalloc rather than optalloc to avoid confusion with GA optimisation!
            gaoptalloc = self.resultpairs[x]['opt'].budget[-1]
            initoutcome = self.resultpairs[x]['init'].improvement[-1][0]
            impoutcome = self.resultpairs[x]['init'].improvement[-1][-1]
            gaoptoutcome = self.resultpairs[x]['opt'].improvement[-1][-1]
            suminitalloc = sum([x[-1] for x in initalloc.values()])
            sumimpalloc = sum([x[-1] for x in impalloc.values()])
            sumgaoptalloc = sum([x[-1] for x in gaoptalloc.values()])
            
            sumbudgetsinit += suminitalloc
            sumbudgetsimp += sumimpalloc
            sumbudgetsgaopt += sumgaoptalloc
            sumoutcomeinit += initoutcome
            sumoutcomeimp += impoutcome
            sumoutcomegaopt += gaoptoutcome
            
            output += '\nProject:\t%s\n' % projectname
            output += 'Default project budget:\t%f\n' % suminitalloc
            output += 'Geospatial analysis budget:\t%f\n' % sumgaoptalloc
            
            output += '\nInitial allocation:\n'
            output +=  'Outcome:\t%f\n'  % initoutcome
            for c in xrange(len(initalloc)): output += '%-15s\t%12.2f\n' % (initalloc.keys()[c], initalloc.values()[c][-1])
#            output += '\nImproved Allocation...     (Outcome: %f)\n' % impoutcome
#            for c in xrange(len(initalloc)): output += '%-15s\t%12.2f\n' % (impalloc.keys()[c],impalloc.values()[c][-1])
            output += '\nOptimal geospatial allocation:\n'
            output +=  'Outcome:\t%f\n'  % gaoptoutcome
            for c in xrange(len(initalloc)): output += '%-15s\t%12.2f\n' % (gaoptalloc.keys()[c], gaoptalloc.values()[c][-1])
                
        output += '\nGA Summary\n'
        output += '\n'
        output += 'Initial portfolio budget:\t%12.2f\n' % sumbudgetsinit
#        output += 'Improved Portfolio Budget:     %12.2f\n' % sumbudgetsimp
        output += 'Optimized portfolio budget:\t%12.2f\n' % sumbudgetsgaopt
        output += '\n'
        output += 'Initial outcome:\t%f\n' % sumoutcomeinit
#        output += 'Improved Aggregate Outcome:     %f\n' % sumoutcomeimp
        output += 'Outcome fter optimization:\t%f\n' % sumoutcomegaopt
        
                
            
            