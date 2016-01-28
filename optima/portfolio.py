from optima import odict, getdate, today, uuid, objrepr, printv, scaleratio, OptimaException # Import utilities
from optima import gitinfo # Import functions
from optima import __version__ # Get current version

from optima import defaultobjectives, asd, Project

#######################################################################################################
## Portfolio class -- this contains everything else!
#######################################################################################################

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


    
    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################    
        
    def genBOCs(self, objectives=None, verbose=2):
        ''' Loop through stored projects and pull out budget-outcome curves, or construct them if they don't exist '''
        if objectives == None: 
            printv('WARNING, you have called genBOCs on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
        for p in self.projects.values():
            if p.getBOC(objectives) == None:
                printv('WARNING, project %s does not have BOC. Generating one using parset %s and progset %s... ' % (p.name, p.parsets[0].name, p.progsets[0].name), 0, verbose)
                p.genBOC(parsetname=p.parsets[0].name, progsetname=p.progsets[0].name, objectives=objectives, maxtime=10)   # WARNING!!! OPTIMISES FOR 1ST ONES
            else:
                printv('Project %s contains a BOC, no need to generate... ' % p.name, 2, verbose)
                
                
    def plotBOCs(self, objectives=None, initbudgets=None, optbudgets=None, verbose=2):
        ''' Loop through stored projects and plot budget-outcome curves '''
        if initbudgets == None: initbudgets = [None]*len(self.projects)
        if optbudgets == None: optbudgets = [None]*len(self.projects)
        if objectives == None: 
            printv('WARNING, you have called plotBOCs on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()
            
        if not len(self.projects) == len(initbudgets) or not len(self.projects) == len(optbudgets):
            errormsg = 'Error: Plotting BOCs for %i projects with %i initial budgets (%i required) and %i optimal budgets (%i required).' % (len(self.projects), len(initbudgets), len(self.projects), len(optbudgets), len(self.projects))
            raise OptimaException(errormsg)
        
        # Loop for BOCs.
        c = 0
        for x in self.projects:
            p = self.projects[x]
            p.plotBOC(objectives=objectives, initbudget=initbudgets[c], optbudget=optbudgets[c])
            c += 1
        
        # Reloop for BOC derivatives just because they group nicer for the GUI.
        c = 0
        for x in self.projects:
            p = self.projects[x]
            p.plotBOC(objectives=objectives, deriv=True, initbudget=initbudgets[c], optbudget=optbudgets[c])
            c += 1
            
            
    def minBOCoutcomes(self, objectives, seedbudgets=None, verbose=2):
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
            
        for p in self.projects.values():
            if p.getBOC(objectives) == None:
                printv('WARNING, project %s does not have BOC. Generating one using parset %s and progset %s... ' % (p.name, p.parsets[0].name, p.progsets[0].name), 0, verbose)
                p.genBOC(parsetname=p.parsets[0].name, progsetname=p.progsets[0].name, objectives=objectives, maxtime=10)   # WARNING!!! OPTIMISES FOR 1ST ONES
            BOClist.append(p.getBOC(objectives))
            
        return minBOCoutcomes(BOClist, grandtotal, budgetvec=seedbudgets)
        
        
    def fullGA(self, objectives=None, budgetratio=None, verbose=0):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''

        # Check inputs
        if objectives == None: 
            printv('WARNING, you have called fullGA on portfolio %s without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives()

        grandtotal = objectives['budget']

        initbudgets = scaleratio(budgetratio, grandtotal)
        optbudgets = self.minBOCoutcomes(objectives=objectives, seedbudgets=initbudgets)
        self.plotBOCs(objectives=objectives, initbudgets=initbudgets, optbudgets=optbudgets)
        
        
        
        
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

