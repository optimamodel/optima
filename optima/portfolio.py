from optima import OptimaException, gitinfo, tic, toc, odict, getdate, today, uuid, dcp, objrepr, printv, scaleratio, findinds, saveobj, loadproj, promotetolist # Import utilities
from optima import version # Get current version
from multiprocessing import Process, Queue
from optima import loadbalancer
from optima import defaultobjectives, asd, Project
from numpy import arange, argsort
from glob import glob
import sys
import os

#######################################################################################################
## Portfolio class -- this contains Projects and GA optimisations
#######################################################################################################

budgeteps = 1e-8        # Project optimisations will fail for budgets that are optimised by GA to be zero. This avoids zeros.
tol = 1.0 # Tolerance for checking that budgets match


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
        self.version = version
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
        output += '            Optima version: %s\n' % self.version
        output += '              Date created: %s\n' % getdate(self.created)
        output += '             Date modified: %s\n' % getdate(self.modified)
        output += '                Git branch: %s\n' % self.gitbranch
        output += '               Git version: %s\n' % self.gitversion
        output += '                       UID: %s\n' % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output


    #######################################################################################################
    ## Methods to handle common tasks
    #######################################################################################################

    def addprojects(self, projects=None, replace=False, verbose=2):
        ''' Store a project within portfolio '''
        printv('Adding project to portfolio...', 2, verbose)
        projects = promotetolist(projects, objtype=Project) # Make sure it's a list, but confirm type first
        if replace: self.projects = odict() # Wipe clean before adding new projects
        for project in projects:
            project.uid = uuid() # TEMPPPP WARNING overwrite UUID
            keyname = project.name if project.name not in self.projects.keys() else str(project.uid) # Only fall back on UID if the project name is taken
            self.projects[keyname] = project        
            printv('\nAdded project "%s" to portfolio "%s".' % (project.name, self.name), 2, verbose)
        return None
    
    
    def addfolder(self, folder=None, replace=True, verbose=2):
        ''' Add a folder of projects to a portfolio '''
        filelist = sorted(glob(os.path.join(folder, '*.prj')))
        projects = []
        if replace: self.projects = odict() # Wipe clean before adding new projects
        for f,filename in enumerate(filelist):
            printv('Loading project %i/%i "%s"...' % (f+1, len(filelist), filename), 3, verbose)
            project = loadproj(filename, verbose=0)
            projects.append(project)
        self.addprojects(projects, verbose=verbose)
        return None
        
        
    
    def save(self, filename=None, saveresults=False, verbose=2):
        ''' Save the current portfolio, by default using its name, and without results '''
        if filename is None and self.filename and os.path.exists(self.filename): filename = self.filename
        if filename is None: filename = self.name+'.prt'
        self.filename = os.path.abspath(filename) # Store file path
        if saveresults:
            saveobj(filename, self, verbose=verbose)
        else:
            tmpportfolio = dcp(self) # Need to do this so we don't clobber the existing results
            for P in range(len(self.projects.values())):
                tmpportfolio.projects[P].cleanresults() # Get rid of all results
            saveobj(filename, tmpportfolio, verbose=verbose) # Save it to file
            del tmpportfolio # Don't need it hanging around any more
        return None
    
    
    
    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################
        
    def runGA(self, objectives=None, grandtotal=None, verbose=2):
        ''' Complete geospatial analysis process applied to portfolio for a set of objectives '''
        printv('Performing full geospatial analysis', 1, verbose)
        
        GAstart = tic()
        
        # Gather the BOCs
        BOClist = []
        for pno,P in enumerate(self.projects.values()):
            thisBOC = P.getBOC(objectives=objectives)
            if thisBOC is None:
                errormsg = 'GA FAILED: Project %s has no BOC' % P.name
                raise OptimaException(errormsg)
            BOClist.append(thisBOC)
        
        # Get the grand total
        if grandtotal is None:
            if objectives is not None:
                grandtotal = objectives['budget']
            else:
                grandtotal = 0.0
                for BOC in BOClist:
                    grandtotal += sum(BOC.defaultbudget[:])
        
        # Run actual geospatial analysis optimization
        oldgeooptimization(BOClist=BOClist, grandtotal=grandtotal) # Operate on the BOCs
        
        # Reoptimize projects
#        gaoptim.reoptimize(self.projects, initbudgets, optbudgets, maxtime=maxtime)
        
        # Tidy up
        self.outputstring = gaoptim.printresults() # Store the results as an output string
        toc(GAstart)
        return None


    # Note: Lists of lists extrax and extray allow for extra custom points to be plotted.
    def plotBOCs(self, objectives=None, initbudgets=None, optbudgets=None, deriv=False, verbose=2, extrax=None, extray=None, baseline=0):
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
        for c,P in enumerate(self.projects.values()):
            ax = P.plotBOC(objectives=objectives, deriv=deriv, initbudget=initbudgets[c], optbudget=optbudgets[c], returnplot=True, baseline=baseline)
            if extrax != None:            
                for k in xrange(len(extrax[c])):
                    ax.plot(extrax[c][k], extray[c][k], 'bo')
                    if baseline==0: ax.set_ylim((0,ax.get_ylim()[1])) # Reset baseline
        
        
        
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
    for i in range(len(x)):
        totalobj += BOClist[i].getoutcome([x[i]])[-1]     # Outcomes are currently passed to and from pchip as lists.
    return totalobj
    
    
def oldgeooptimization(BOClist, grandtotal, budgetvec=None, minbound=None, maxiters=1000, maxtime=None, verbose=2):
    ''' Actual runs geospatial optimisation across provided BOCs. '''
    printv('Calculating minimum outcomes for grand total budget of %f' % grandtotal, 2, verbose)
    
    if minbound == None: minbound = [0]*len(BOClist)
    if budgetvec == None: budgetvec = [grandtotal/len(BOClist)]*len(BOClist)
    if not len(budgetvec) == len(BOClist): 
        errormsg = 'Geospatial analysis is minimising %i BOCs with %i initial budgets' % (len(BOClist), len(budgetvec))
        raise OptimaException(errormsg)
        
    args = {'BOClist':BOClist, 'grandtotal':grandtotal, 'minbound':minbound}    
    
    budgetvecnew, fvals, exitreason = asd(objectivecalc, budgetvec, args=args, maxtime=maxtime, maxiters=maxiters, verbose=verbose)
    budgetvecnew = constrainbudgets(budgetvecnew, grandtotal, minbound)

    return budgetvecnew

    
def geooptimization(BOClist=None, grandtotal=None, maxtime=None, stepsize=None, verbose=2):
    ''' Actual runs geospatial optimisation across provided BOCs. '''
    printv('Calculating geospatial optimization for grand total budget of %f' % grandtotal, 2, verbose)
    
    # Check inputs
    if stepsize is None: stepsize = 10000 # The step size, in $
    
    # Set up variables
    
    # Set up vectors
    
    # Extract BOC derivatives
    
    # Iterate over vectors

    return budgetvecnew






#%% Geospatial analysis batch functions for multiprocessing.

def batch_reopt(gaoptim, P, pind, outputqueue, projects, initbudgets, optbudgets, maxtime, parprogind, verbose):
    """Batch function for final re-optimization step of geospatial analysis."""
    loadbalancer(index=pind)
    printv('Running %i of %i...' % (pind+1, len(projects)), 2, verbose)

    tmp = odict()

    # Crash if any project doesn't have progsets
    if not P.progsets or not P.parsets:
        errormsg = 'Project "%s" does not have a progset and/or a parset, can''t generate a BOC.'
        raise OptimaException(errormsg)

    initobjectives = dcp(gaoptim.objectives)
    initobjectives['budget'] = initbudgets[pind] + budgeteps
    printv("Generating initial-budget optimization for project '%s'." % P.name, 2, verbose)
    tmp['init'] = P.optimize(name=P.name+' GA initial', parsetname=P.parsets[parsetnames[parprogind]].name, progsetname=P.progsets[progsetnames[parprogind]].name, objectives=initobjectives, maxtime=0.0, saveprocess=False) # WARNING TEMP
    sys.stdout.flush()

    optobjectives = dcp(gaoptim.objectives)
    optobjectives['budget'] = optbudgets[pind] + budgeteps
    printv("Generating optimal-budget optimization for project '%s'." % P.name, 2, verbose)
    tmp['opt'] = P.optimize(name=P.name+' GA optimal', parsetname=P.parsets[parsetnames[parprogind]].name, progsetname=P.progsets[progsetnames[parprogind]].name, objectives=optobjectives, maxtime=maxtime, saveprocess=False)
    sys.stdout.flush()

    outputqueue.put(tmp)
    return None
    
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
        self.version = version
        self.gitbranch, self.gitversion = gitinfo()

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
        output += '      GAOptim name: %s\n'    % self.name
        output += '\n'
        output += '    Optima version: %s\n'    % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output



    def reoptimize(self, projects, initbudgets, optbudgets, maxtime=None, parprogind=0, verbose=2):
        ''' Runs final optimisations for initbudgets and optbudgets so as to summarise GA optimisation '''
        printv('Finalizing geospatial analysis...', 1, verbose)
        printv('Warning, using default programset/programset!', 2, verbose)
        
        # Project optimisation processes (e.g. Optims and Multiresults) are not saved to Project, only GA Optim.
        # This avoids name conflicts for Optims/Multiresults from multiple GAOptims (via project add methods) that we really don't need.
        
        outputqueue = Queue()
        processes = []
        for pind,P in enumerate(projects.values()):
            prc = Process(
                target=batch_reopt,
                args=(self, P, pind, outputqueue, projects, initbudgets,
                      optbudgets, parsetnames, progsetnames, maxtime,
                      parprogind, verbose))
            prc.start()
            processes.append(prc)
        for pind,P in enumerate(projects.values()):
            self.resultpairs[str(P.uid)] = outputqueue.get()
    
        return None


    # WARNING: We are comparing the un-optimised outcomes of the pre-GA allocation with the re-optimised outcomes of the post-GA allocation!
    # Be very wary of the indices being used...
    def printresults(self, verbose=2):
        ''' Just displays results related to the GA run '''
        printv('Printing results...', 2, verbose)
        
        overallbudgetinit = 0
        overallbudgetopt = 0
        overalloutcomeinit = 0
        overalloutcomeopt = 0
        
        overalloutcomesplit = odict()
        for key in self.objectives['keys']:
            overalloutcomesplit['num'+key] = odict()
            overalloutcomesplit['num'+key]['init'] = 0
            overalloutcomesplit['num'+key]['opt'] = 0
        
        projnames = []
        projbudgets = []
        projcov = []
        projoutcomes = []
        projoutcomesplit = []
        
        for prj,x in enumerate(self.resultpairs.keys()):          # WARNING: Nervous about all this slicing. Problems foreseeable if format changes.
            # Figure out which indices to use
            tvector = self.resultpairs[x]['init'].tvec          # WARNING: NOT USING DT NORMALISATIONS LATER, SO ASSUME DT = 1 YEAR.
            initial = findinds(tvector, self.objectives['start'])
            final = findinds(tvector, self.objectives['end'])
            indices = arange(initial, final)
            
            projectname = self.resultpairs[x]['init'].projectinfo['name']
            initalloc = self.resultpairs[x]['init'].budget['Current']
            gaoptalloc = self.resultpairs[x]['opt'].budget['Optimal']
            initoutcome = self.resultpairs[x]['init'].improvement[0][0]     # The first 0 corresponds to best.
                                                                            # The second 0 corresponds to outcome pre-optimisation (which shouldn't matter anyway due to pre-GA budget 'init' being optimised for 0 seconds).
            gaoptoutcome = self.resultpairs[x]['opt'].improvement[0][-1]    # The -1 corresponds to outcome post-optimisation (with 'opt' being a maxtime optimisation of a post-GA budget).
            suminitalloc = sum(initalloc.values())
            sumgaoptalloc = sum(gaoptalloc.values())
            
            overallbudgetinit += suminitalloc
            overallbudgetopt += sumgaoptalloc
            overalloutcomeinit += initoutcome
            overalloutcomeopt += gaoptoutcome
            
            projnames.append(projectname)
            projbudgets.append(odict())
            projoutcomes.append(odict())
            projbudgets[prj]['init']  = initalloc
            projbudgets[prj]['opt']   = gaoptalloc
            projoutcomes[prj]['init'] = initoutcome
            projoutcomes[prj]['opt']  = gaoptoutcome
            
            projoutcomesplit.append(odict())
            projoutcomesplit[prj]['init'] = odict()
            projoutcomesplit[prj]['opt'] = odict()
            
            initpars = self.resultpairs[x]['init'].parset[0]
            optpars = self.resultpairs[x]['opt'].parset[-1]
            initprog = self.resultpairs[x]['init'].progset[0]
            optprog = self.resultpairs[x]['opt'].progset[-1]
            initcov = initprog.getprogcoverage(initalloc,self.objectives['start'],parset=initpars)
            optcov = optprog.getprogcoverage(gaoptalloc,self.objectives['start'],parset=optpars)
            
            projcov.append(odict())
            projcov[prj]['init']  = initcov
            projcov[prj]['opt']   = optcov
            
            
            for key in self.objectives['keys']:
                projoutcomesplit[prj]['init']['num'+key] = self.resultpairs[x]['init'].main['num'+key].tot['Current'][indices].sum()     # Again, current and optimal should be same for 0 second optimisation, but being explicit.
                projoutcomesplit[prj]['opt']['num'+key] = self.resultpairs[x]['opt'].main['num'+key].tot['Optimal'][indices].sum()
                overalloutcomesplit['num'+key]['init'] += projoutcomesplit[prj]['init']['num'+key]
                overalloutcomesplit['num'+key]['opt'] += projoutcomesplit[prj]['opt']['num'+key]
                
                 
        ## Actually create the output
        output = ''
        output += 'Geospatial analysis results: minimize outcomes from %i to %i' % (self.objectives['start'], self.objectives['end'])
        output += '\n\n'
        output += '\n\t\tInitial\tOptimal'
        output += '\nOverall summary'
        output += '\n\tPortfolio budget:\t%0.0f\t%0.0f' % (overallbudgetinit, overallbudgetopt)
        output += '\n\tOutcome:\t%0.0f\t%0.0f' % (overalloutcomeinit, overalloutcomeopt)
        for key in self.objectives['keys']:
            output += '\n\t' + self.objectives['keylabels'][key] + ':\t%0.0f\t%0.0f' % (overalloutcomesplit['num'+key]['init'], overalloutcomesplit['num'+key]['opt'])
        
        ## Sort, then export
        projindices = argsort(projnames)
        for prj in projindices:
            output += '\n'
            output += '\n'
            output += '\n\t\tInitial\tOptimal'
            output += '\nProject: "%s"' % projnames[prj]
            output += '\n'
            output += '\n\tBudget:\t%0.0f\t%0.0f' % (sum(projbudgets[prj]['init'][:]), sum(projbudgets[prj]['opt'][:]))
            output += '\n\tOutcome:\t%0.0f\t%0.0f' % (projoutcomes[prj]['init'], projoutcomes[prj]['opt'])
            for key in self.objectives['keys']:
                output += '\n\t' + self.objectives['keylabels'][key] + ':\t%0.0f\t%0.0f' % (projoutcomesplit[prj]['init']['num'+key], projoutcomesplit[prj]['opt']['num'+key])
            output += '\n'
            output += '\n\tAllocation:'
            for prg in projbudgets[prj]['init'].keys():
                output += '\n\t%s\t%0.0f\t%0.0f' % (prg, projbudgets[prj]['init'][prg], projbudgets[prj]['opt'][prg])
            output += '\n'
            output += '\n\tCoverage (%i):' % (self.objectives['start'])
            for prg in projbudgets[prj]['init'].keys():
                initval = projcov[prj]['init'][prg]
                optval = projcov[prj]['opt'][prg]
                if initval is None: initval = 0
                if optval is None: optval = 0
                output += '\n\t%s\t%0.0f\t%0.0f' % (prg, initval, optval)
        
        print(output)
        
        return output
        
    def getinitbudgets(self):
        bl = []
        for proj in self.resultpairs:
            bl.append(sum(self.resultpairs[proj]['init'].budget[0].values()))
        return bl
        
    def getoptbudgets(self):
        bl = []
        for proj in self.resultpairs:
            bl.append(sum(self.resultpairs[proj]['opt'].budget[-1].values()))
        return bl
        
    
#%% 'EASY' STACK-PLOTTING CODE PULLED FROM v1.5 FOR CLIFF. DOES NOT WORK.   :)
    

#    def sortfixed(somelist):
#        # Prog array help: [VMMC, FSW, MSM, HTC, ART, PMTCT, OVC, Other Care, MGMT, HR, ENV, SP, M&E, Other, SBCC, CT]
#        sortingarray = [2, 4, 5, 7, 8, 6, 1, 9, 10, 11, 12, 13, 14, 15, 3, 0]
#        return [y for x,y in sorted(zip(sortingarray,somelist), key = lambda x:x[0])]
#    #    return [y for x,y in sorted(enumerate(somelist), key = lambda x: -len(progs[x[0]]['effects']))]
        
    
#    def superplot(self):
#        
#        from pylab import gca, xlabel, tick_params, xlim, figure, subplot, plot, pie, bar, title, legend, xticks, ylabel, show
#        from gridcolormap import gridcolormap
#        from matplotlib import gridspec
#        import numpy
#        
#        progs = p1.regionlist[0].metadata['programs']    
#        
#        figure(figsize=(22,15))
#        
#        nprograms = len(p1.gpalist[-1][0].region.data['origalloc'])
##        colors = sortfixed(gridcolormap(nprograms))
##        colors[0] = numpy.array([ 0.20833333,  0.20833333,  0.54166667])  #CT
##        colors[1] = numpy.array([ 0.45833333,  0.875     ,  0.79166667])  #OVC
##        colors[2] = numpy.array([0.125, 0.125, 0.125])  #VMMC
##        colors[3] = numpy.array([ 0.79166667,  0.45833333,  0.875     ])+numpy.array([ 0.125,  0.125,  0.125     ])  #SBCC
##        colors[4] = numpy.array([ 0.54166667,  0.20833333,  0.20833333])  #FSW
##        colors[5] = numpy.array([ 0.875     ,  0.45833333,  0.125     ])  #MSM
##        colors[6] = numpy.array([ 0.125     ,  0.875     ,  0.45833333])+numpy.array([ 0.0,  0.125,  0.0     ])  #PMTCT
##        colors[7] = numpy.array([ 0.54166667,  0.875     ,  0.125     ])   #HTC
##        colors[8] = numpy.array([ 0.20833333,  0.54166667,  0.20833333])  #ART
##        for i in xrange(7): colors[-(i+1)] = numpy.array([0.25+0.5*i/6.0, 0.25+0.5*i/6.0, 0.25+0.5*i/6.0])
#    
#        
#        
#        gpl = sorted(p1.gpalist[-1], key=lambda sbo: sbo.name)
#        ind = [val for pair in ([x, 0.25+x] for x in xrange(len(gpl))) for val in pair]
#        width = [0.25, 0.55]*(len(gpl))       # the width of the bars: can also be len(x) sequence
#        
#        bar(ind, [val*1e-6 for pair in zip([sortfixed(sb.simlist[1].alloc)[-1] for sb in gpl], [sortfixed(sb.simlist[2].alloc)[-1] for sb in gpl]) for val in pair], width, color=colors[-1])
#        for p in xrange(2,nprograms+1):
#            bar(ind, [val*1e-6 for pair in zip([sortfixed(sb.simlist[1].alloc)[-p] for sb in gpl], [sortfixed(sb.simlist[2].alloc)[-p] for sb in gpl]) for val in pair], width, color=colors[-p], bottom=[val*1e-6 for pair in zip([sum(sortfixed(sb.simlist[1].alloc)[1-p:]) for sb in gpl], [sum(sortfixed(sb.simlist[2].alloc)[1-p:]) for sb in gpl]) for val in pair])
#        
#        xticks([x+0.5 for x in xrange(len(gpl))], [sb.region.getregionname() for sb in gpl], rotation=-60)
#        xlim([0,32])
#        tick_params(axis='both', which='major', labelsize=15)
#        tick_params(axis='both', which='minor', labelsize=15)
#        ylabel('Budget Allocation (US$m)', fontsize=15)
#        
#    
#    
#        fig = figure(figsize=(22,15))    
#        
#        gs = gridspec.GridSpec(3, 11) #, width_ratios=[len(sb.simlist[1:]), 2])
#        
#        for x in xrange(len(gpl)):
#            sb = gpl[x]
#            r = sb.region
#    
#            ind = xrange(len(sb.simlist[1:]))
#            width = 0.8       # the width of the bars: can also be len(x) sequence
#            
#            if x < 10: subplot(gs[x])
#            else: subplot(gs[x+1])
#            bar(ind, [sortfixed([x*1e-6 for x in sim.alloc])[-1] for sim in sb.simlist[1:]], width, color=colors[-1])
#            for p in xrange(2,nprograms+1):
#                bar(ind, [sortfixed([x*1e-6 for x in sim.alloc])[-p] for sim in sb.simlist[1:]], width, color=colors[-p], bottom=[sum(sortfixed([x*1e-6 for x in sim.alloc])[1-p:]) for sim in sb.simlist[1:]])
#            #xticks([index+width/2.0 for index in ind], [sim.getname() for sim in sb.simlist[1:]])
#            xlabel(r.getregionname(), fontsize=18)
#            if x in [0,10,21]: ylabel('Budget Allocation (US$m)', fontsize=18)
#            tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off')
#        
#    #        ax = gca()
#    #        ax.ticklabel_format(style='sci', axis='y')
#    #        ax.yaxis.major.formatter.set_powerlimits((0,0))
#            
#            tick_params(axis='both', which='major', labelsize=14)
#            tick_params(axis='both', which='minor', labelsize=14)
#        
#        fig.tight_layout()
#        
#        
#        
#    #    bar(ind, [val for pair in zip([sb.simlist[1].alloc[-1] for sb in gpl], [sb.simlist[2].alloc[-1] for sb in gpl]) for val in pair], width, color=colors[-1])
#    #    for p in xrange(2,nprograms+1):
#    #        bar(ind, [val for pair in zip([sb.simlist[1].alloc[-p] for sb in gpl], [sb.simlist[2].alloc[-p] for sb in gpl]) for val in pair], width, color=colors[-p], bottom=[val for pair in zip([sum(sb.simlist[1].alloc[1-p:]) for sb in gpl], [sum(sb.simlist[2].alloc[1-p:]) for sb in gpl]) for val in pair])
#    #    
#    #    xticks([x+0.5 for x in xrange(len(gpl))], [sb.region.getregionname() for sb in gpl], rotation=-60)
#    #    xlim([0,32])
#    #    tick_params(axis='both', which='major', labelsize=15)
#    #    tick_params(axis='both', which='minor', labelsize=15)
#    #    ylabel('Budget Allocation ($)', fontsize=15)
#    #    
#    #
#    #
#    #    fig = figure(figsize=(22,15))    
#    #    
#    #    gs = gridspec.GridSpec(3, 11) #, width_ratios=[len(sb.simlist[1:]), 2])
#    #    
#    #    for x in xrange(len(gpl)):
#    #        sb = gpl[x]
#    #        r = sb.region
#    #
#    #        ind = xrange(len(sb.simlist[1:]))
#    #        width = 0.8       # the width of the bars: can also be len(x) sequence
#    #        
#    #        if x < 10: subplot(gs[x])
#    #        else: subplot(gs[x+1])
#    #        bar(ind, [sim.alloc[-1] for sim in sb.simlist[1:]], width, color=colors[-1])
#    #        for p in xrange(2,nprograms+1):
#    #            bar(ind, [sim.alloc[-p] for sim in sb.simlist[1:]], width, color=colors[-p], bottom=[sum(sim.alloc[1-p:]) for sim in sb.simlist[1:]])
#    #        #xticks([index+width/2.0 for index in ind], [sim.getname() for sim in sb.simlist[1:]])
#    #        xlabel(r.getregionname(), fontsize=18)
#    #        if x in [0,10,21]: ylabel('Budget Allocation ($)', fontsize=18)
#    #        tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off')
#    #    
#    #        ax = gca()
#    #        ax.ticklabel_format(style='sci', axis='y')
#    #        ax.yaxis.major.formatter.set_powerlimits((0,0))
#    #        
#    #        tick_params(axis='both', which='major', labelsize=13)
#    #        tick_params(axis='both', which='minor', labelsize=13)
#    #    
#    #    fig.tight_layout()    
#        
#        
#        
#    #    for x in xrange(len(p1.gpalist[-1])):
#        for x in xrange(1):
#            sb = p1.gpalist[-1][x]
#            r = sb.region
#            
#            nprograms = len(r.data['origalloc'])
#    #        colors = sortfixed(gridcolormap(nprograms))
#            
#            figure(figsize=(len(sb.simlist[1:])*2+4,nprograms/2))
#            gs = gridspec.GridSpec(1, 2, width_ratios=[len(sb.simlist[1:]), 2]) 
#            ind = xrange(len(sb.simlist[1:]))
#            width = 0.8       # the width of the bars: can also be len(x) sequence
#            
#            subplot(gs[0])
#            bar(ind, [sortfixed(sim.alloc)[-1] for sim in sb.simlist[1:]], width, color=colors[-1])
#            for p in xrange(2,nprograms+1):
#                bar(ind, [sortfixed(sim.alloc)[-p] for sim in sb.simlist[1:]], width, color=colors[-p], bottom=[sum(sortfixed(sim.alloc)[1-p:]) for sim in sb.simlist[1:]])
#            xticks([index+width/2.0 for index in ind], [sim.getname() for sim in sb.simlist[1:]])
#            ylabel('Budget Allocation ($)')
#            
#            subplot(gs[1])
#            for prog in xrange(nprograms): plot(0, 0, linewidth=3, color=colors[prog])
#            legend(sortfixed(r.data['meta']['progs']['short']))
#            
#        show()
                