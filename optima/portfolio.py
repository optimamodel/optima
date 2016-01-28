from optima import odict, getdate, today, uuid, dcp, objrepr, printv, scaleratio, OptimaException # Import utilities
from optima import gitinfo # Import functions
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
        if type(projects)==Project: projects = [projects]
        if type(projects)==list:
            for project in projects: 
                self.projects[project.uid] = project        
                printv('\nAdded project "%s" to portfolio "%s".' % (project.name, self.name), 4, verbose)
        
    def getdefaultbudgets(self):
        ''' Get the default allocation totals of each project '''
        budgets = []
        for x in self.projects:
            p = self.projects[x]
            budgets.append(sum(p.progsets[0].getdefaultbudget().values()))      # WARNING!!! SELECTS 1ST PROGSET
        return budgets
    
    
    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################
        
        
    def genBOCs(self, objectives=None, maxtime=None, forceregen=False, verbose=2):
        ''' Loop through stored projects and construct budget-outcome curves '''
        if objectives == None: 
            printv('WARNING, you have called genBOCs on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        for x in self.projects:
            p = self.projects[x]
            if p.getBOC(objectives) == None or forceregen:
                printv('WARNING, project %s does not have BOC. Generating one using parset %s and progset %s... ' % (p.name, p.parsets[0].name, p.progsets[0].name), 0, verbose)
                p.delBOC(objectives)    # Delete BOCs in case forcing regeneration.
                p.genBOC(parsetname=p.parsets[0].name, progsetname=p.progsets[0].name, objectives=objectives, maxtime=maxtime)   # WARNING!!! OPTIMISES FOR 1ST ONES
            else:
                printv('Project %s contains a BOC, no need to generate... ' % p.name, 2, verbose)
                
                
    def plotBOCs(self, objectives=None, initbudgets=None, optbudgets=None, verbose=2):
        ''' Loop through stored projects and plot budget-outcome curves '''
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
            for x in self.projects:
                p = self.projects[x]
                ib = initbudgets[c]
                if not ib == None: ib = [ib]
                ob = optbudgets[c]
                if not ob == None: ob = [ob]
                # Note: The reason plotBOC is being passed listed forms of single values is due to current PCHIP implementation...
                p.plotBOC(objectives=objectives, deriv = inderiv, initbudget = ib, optbudget = ob)
                c += 1
            
            
    def minBOCoutcomes(self, objectives, seedbudgets=None, maxtime=None, verbose=2):
        ''' Loop through project BOCs corresponding to objectives and minimise net outcome '''

        # Check inputs
        if objectives == None: 
            printv('WARNING, you have called minBOCoutcomes on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        
        # Initialise internal parameters
        BOClist = []
        grandtotal = objectives['budget']
        
        # Scale seedbudgets just in case they don't add up to the required total.
        if not seedbudgets == None:
            seedbudgets = scaleratio(seedbudgets, objectives['budget'])
            
        for x in self.projects:
            p = self.projects[x]
            if p.getBOC(objectives) == None:
                printv('WARNING, project %s does not have BOC. Generating one using parset %s and progset %s... ' % (p.name, p.parsets[0].name, p.progsets[0].name), 0, verbose)
                p.genBOC(parsetname=p.parsets[0].name, progsetname=p.progsets[0].name, objectives=objectives, maxtime=maxtime)   # WARNING!!! OPTIMISES FOR 1ST PARSET & PROGSET
            BOClist.append(p.getBOC(objectives))
            
        return minBOCoutcomes(BOClist, grandtotal, budgetvec=seedbudgets)
        
        
    def fullGA(self, objectives=None, budgetratio=None, maxtime=None, verbose=2):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''

		# Check inputs
        if objectives == None: 
            printv('WARNING, you have called fullGA on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        objectives = dcp(objectives)    # NOTE: Yuck. Somebody will need to check all of Optima for necessary dcps.
        
        gaoptim = GAOptim(objectives = objectives)
        self.gaoptims[gaoptim.uid] = gaoptim
        
        if budgetratio == None: budgetratio = self.getdefaultbudgets()
        initbudgets = scaleratio(budgetratio,objectives['budget'])
        
        optbudgets = self.minBOCoutcomes(objectives, seedbudgets = initbudgets, maxtime = maxtime)
        self.plotBOCs(objectives, initbudgets = initbudgets, optbudgets = optbudgets)
        
        gaoptim.complete(self.projects,initbudgets,optbudgets)
        gaoptim.printresults()
        
        
        
        
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
    
def minBOCoutcomes(BOClist, grandtotal, budgetvec=None, minbound=None, maxiters=1000, maxtime=None, verbose=5):
    ''' Actual runs geospatial optimisation across provided BOCs. '''
    
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
        if self.modified: output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def complete(self, projects, initbudgets, optbudgets, maxtime = None):
        ''' Runs final optimisations for initbudgets and optbudgets so as to summarise GA optimisation '''
        print('Finalising geospatial analysis...')

        if not len(projects) == len(initbudgets) or not len(projects) == len(optbudgets):
            OptimaException('Error: The number of projects is not matching the number of initial or optimal budgets in GA!')
        
        # Project optimisation processes (e.g. Optims and Multiresults) are not saved to Project, only GA Optim.
        # This avoids name conflicts for Optims/Multiresults from multiple GAOptims (via project add methods) that we really don't need.
        # WARNING: AS USUAL USING 1ST PARSET AND PROGSET!
        for x in xrange(len(projects)):
            p = projects[x]
            self.resultpairs[p.uid] = odict()
            
            initobjectives = dcp(self.objectives)
            initobjectives['budget'] = initbudgets[x] + budgeteps
            print("Generating initial-budget optimisation for '%s'." % p.name)
            print(initobjectives)
            self.resultpairs[p.uid]['init'] = p.minoutcomes(name=p.name+' GA initial', parsetname=p.parsets[0].name, progsetname=p.progsets[0].name, objectives=initobjectives, maxtime = maxtime, saveprocess = False)
            
            optobjectives = dcp(self.objectives)
            optobjectives['budget'] = optbudgets[x] + budgeteps
            print("Generating optimal-budget optimisation for '%s'." % p.name)
            print(optobjectives)
            self.resultpairs[p.uid]['opt'] = p.minoutcomes(name=p.name+' GA optimal', parsetname=p.parsets[0].name, progsetname=p.progsets[0].name, objectives=optobjectives, maxtime = maxtime, saveprocess = False)


    def printresults(self):
        ''' Just displays results related to the GA run '''
        
        sumbudgetsinit = 0
        sumbudgetsimp = 0
        sumbudgetsgaopt = 0
        sumoutcomeinit = 0
        sumoutcomeimp = 0
        sumoutcomegaopt = 0
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
            
            print('\nProject: %s' % projectname)
            print('Init./Improv. Budget: %f' % suminitalloc)
            print('GA Optimised Budget: %f' % sumgaoptalloc)
            
            print('\nInitial Allocation...      (Outcome: %f)' % initoutcome)
            for c in xrange(len(initalloc)): print('%-15s\t%12.2f' % (initalloc.keys()[c],initalloc.values()[c][-1]))
            print('\nImproved Allocation...     (Outcome: %f)' % impoutcome)
            for c in xrange(len(initalloc)): print('%-15s\t%12.2f' % (impalloc.keys()[c],impalloc.values()[c][-1]))
            print('\nGA Optimal Allocation...   (Outcome: %f)' % gaoptoutcome)
            for c in xrange(len(initalloc)): print('%-15s\t%12.2f' % (gaoptalloc.keys()[c],gaoptalloc.values()[c][-1]))
                
        print('\nGA Summary')
        print('')
        print('Initial Portfolio Budget:      %12.2f' % sumbudgetsinit)
        print('Improved Portfolio Budget:     %12.2f' % sumbudgetsimp)
        print('GA Optimised Portfolio Budget: %12.2f' % sumbudgetsgaopt)
        print('')
        print('Initial Aggregate Outcome:      %f' % sumoutcomeinit)
        print('Improved Aggregate Outcome:     %f' % sumoutcomeimp)
        print('GA Optimised Aggregate Outcome: %f' % sumoutcomegaopt)
        
                
            
            