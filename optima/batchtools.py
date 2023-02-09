"""
BATCHTOOLS

Functions for doing things in batch...yeah, should make better.

Note - tasks have to be standalone functions or they break on windows, see
http://stackoverflow.com/questions/9670926/multiprocessing-on-windows-breaks

Version: 2017mar17
"""

from optima import Link, loadproj, loadbalancer, printv, getfilelist, dcp, odict, outcomecalc, tic, toc
from numpy import empty, inf
try: from multiprocessing import Process, Queue
except: Process, Queue = None, None # OK to skip these if batch is False


####################################################################################################
### Simple template functions
####################################################################################################

def batchtest_task(obj, ind, outputqueue, nprocs, nrepeats, maxload):
    loadbalancer(maxload=maxload, index=ind)
    print('Running slow test function...')
    for i in range(int(nrepeats)): i += 1
    output = obj+ind
    outputqueue.put(output)
    print('...done.')
    return None


def batchtest(nprocs=4, nrepeats=3e7, maxload=0.5):
    ''' A simple example of how to run a parallel computation -- use this as a template for making more complex functions'''
    from numpy.random import random as rand

    outputqueue = Queue()
    outputlist = empty(nprocs, dtype=object)
    processes = []
    for i in range(nprocs):
        obj = rand()
        prc = Process(target=batchtest_task, 
                      args=(obj, i, outputqueue, nprocs, nrepeats, maxload))
        prc.start()
        processes.append(prc)
    for i in range(nprocs):
        outputlist[i] = outputqueue.get()
    for prc in processes:
        prc.join() # Wait for them to finish
    
    return outputlist


####################################################################################################
### Housekeeping functions
####################################################################################################

def getprojects(projects=None, folder=None, verbose=2):
    ''' Small helper method to decide what to do about projects '''
    if projects is None: # If a projects odict is not supplied -- load from file
        fromfolder = True
        if folder is None: folder = '.'
        filelist = getfilelist(folder, 'prj')
        nprojects = len(filelist)
        projects = odict()
        for i in range(nprojects):
            proj = loadproj(filelist[i])
            proj.filename = filelist[i] # Ensure the filename is up-to-date since we'll save later
            projects[proj.name] = proj
    else:
        nprojects = len(projects)
        fromfolder = False # If it is, just set fromfolder
    
    # Ensure these match, since used to repopulate the odict
    for key,project in projects.items():
        if project.name != key: 
            msg = 'Warning, project name and key do not match (%s vs. %s), updating...' % (project.name, key)
            printv(msg, 2, verbose)
        project.name = key 
    
    return projects, nprojects, fromfolder


def housekeeping(nprojects, batch):
    ''' Small function to return the required variables for running the batch functions '''
    if batch: outputqueue = Queue()
    else: outputqueue = None
    outputlist = empty(nprojects, dtype=object)
    processes = []
    return outputqueue, outputlist, processes


def tidyup(projects=None, batch=None, fromfolder=None, outputlist=None, outputqueue=None, processes=None):
    '''
    Functions to execute after the parallel process has been run. If batch is True, then outputlist will
    be empty and will be populated from outputqueue. If it's False, then outputlist will be a list of
    the processed projects.    
    '''
    
    # Extra tasks required for batch runs
    if batch:
        for i in range(len(projects)):
            outputlist[i] = outputqueue.get()  # This is needed or else the process never finishes
        for prc in processes:
            prc.join() # Wait for them to finish
    
    # Update the odict
    for project in outputlist:
        projects[project.name] = project
    
    # If loaded from a folder, save
    if fromfolder:
        for project in projects.values():
            project.save(filename=project.filename)
    
    # Print any warnings, if they exist
    for project in projects.values(): project.getwarnings() 
    
    return projects


####################################################################################################
### The meat of the matter -- batch functions and their tasks
####################################################################################################

def batchautofit(folder=None, projects=None, name=None, fitwhat=None, fitto='prev', maxtime=None, maxiters=200, verbose=2, maxload=0.5, batch=True, randseed=None):
    ''' Perform batch autofitting '''
    
    # Praeludium
    starttime = tic()
    projects, nprojects, fromfolder = getprojects(projects, folder, verbose) # If no projects supplied, load them from the folder
    outputqueue, outputlist, processes = housekeeping(nprojects, batch) # Figure out things that need to be figured out

    for i,project in enumerate(projects.values()):
        args = (project, i, outputqueue, name, fitwhat, fitto, maxtime, maxiters, verbose, maxload, batch, randseed)
        if batch:
            prc = Process(target=autofit_task, args=args)
            prc.start()
            processes.append(prc)
        else:
            outputlist[i] = autofit_task(*args) # Simply store here 
    
    # Encore
    projects = tidyup(projects=projects, batch=batch, fromfolder=fromfolder, outputlist=outputlist, outputqueue=outputqueue, processes=processes)
    toc(starttime, 'batchautofit')
    
    return projects


def autofit_task(project, ind, outputqueue, name, fitwhat, fitto, maxtime, maxiters, verbose, maxload, batch, randseed):
    """Kick off the autofit task for a given project file."""
    
    # Standard opening
    if batch: loadbalancer(index=ind, maxload=maxload, label=project.name)
    printv('Running autofitting on %s...' % project.name, 2, verbose)
    
    # The meat
    try:
        project.autofit(name=name, orig=name, fitwhat=fitwhat, fitto=fitto, maxtime=maxtime, maxiters=maxiters, verbose=verbose, randseed=randseed)
    except Exception as E:
        project.addwarning('Exception: batchautofit() failed for %s: %s' % (project.name, repr(E)))
        project.getwarnings()
    
    # Standardized close
    print('...done.')
    if batch: 
        outputqueue.put(project)
        return None
    else:
        return project


def batchBOC(folder=None, projects=None, portfolio=None, budgetratios=None, name=None, parsetname=None, progsetname=None, objectives=None, 
             constraints=None, absconstraints=None, proporigconstraints=None,  maxiters=200, maxtime=None, verbose=2, stoppingfunc=None,
             maxload=0.5, interval=None, prerun=True, batch=True, mc=3, die=False, recalculate=True, strict=True, randseed=None):
    """
    Perform batch BOC calculation.

    Loops through all projects in the specified (default: current) directory,
    loads each project and sends to boc_task, along with any universal
    optimization settings to generate a budget-objective-curve for each
    project.

    Arguments:
        folder - the directory containing all projects for which a BOC will be
                calculated (optional)
        projects - an odict of projects, as from a portfolio; if not None, will
                be used instead of the folder
        portfolio - a portfolio; if supplied, will be used instead of folder or
                projects
        budgetratios - a vector of multiples of the current budget for which an
                optimization will be performed to comprise the BOC (default:
                [1.0, 0.6, 0.3, 0.1, 3.0, 6.0, 10.0])
        name - name of the stored BOC result
        parsetname - name of the parameter set stored within the project to use
                for the optimizations that comprise the BOC
        progsetname - name of the program set stored within the project to use
                for the optimizations that comprise the BOC
        inds - indexing variable for selecting parameters in a parset to use in
                the optimizations
        objectives - typically an odict containing desired outcome and
                weighting to use in the optimizations; if None, uses default
                objectives (jointly minimize incidence and deaths with 1:5
                weighting); if 'latest', extracts objectives from the latest
                stored optimization in the project
        constraints - typically an odict containting desired limits on program
                funding changes relative to current spending; if None, uses
                default constraints; if 'latest', extracts constraints from the
                latest stored opitimization in the project
        maxiters - maximum number of iterations for each optimization run that
                comprises the BOC
        maxtime - maximum time in seconds for each optimization run that
                comprises the BOC
        verbose - number indicating level of text output (higher is more text)
        stoppingfunc - appears to not be functional
        maxload - how much of the CPU to use
        interval - the interval for the loadbalancer to use
        prerun - whether or not to precalculate the results to use for e.g.
                population size denominators
        batch - whether or not to actually run as batch
        mc - the number of Monte Carlo runs
        die - whether to crash or give a warning if something goes wrong
        recalculate - whether to calculate BOCs for projects that already have BOCs
        strict - whether to recalculate BOCs for projects that have non-matching BOCs
        randseed - the random seed to use for the calculations
        
    """
    
    # Praeludium
    starttime = tic()
    if portfolio is not None: projects = portfolio.projects
    projects, nprojects, fromfolder = getprojects(projects, folder, verbose) # If no projects supplied, load them from the folder
    outputqueue, outputlist, processes = housekeeping(nprojects, batch) # Figure out things that need to be figured out
    
    # Loop over the projects
    for i,project in enumerate(projects.values()):
        prjobjectives = project.optims[-1].objectives if objectives == 'latest' else objectives
        prjconstraints         = project.optims[-1].constraints         if constraints == 'latest'         else constraints
        prjabsconstraints      = project.optims[-1].absconstraints      if absconstraints == 'latest'      else absconstraints
        prjproporigconstraints = project.optims[-1].proporigconstraints if proporigconstraints == 'latest' else proporigconstraints
        args = (project, i, outputqueue, budgetratios, name, parsetname, progsetname, prjobjectives, 
                prjconstraints,prjabsconstraints,prjproporigconstraints, maxiters, maxtime, verbose, stoppingfunc, maxload, interval,
                prerun, batch, mc, die, recalculate, strict, randseed)
        if batch:
            prc = Process(target=boc_task, args=args)
            prc.start()
            processes.append(prc)
        else:
            outputlist[i] = boc_task(*args) # Simply store here 
    
    # Encore
    projects = tidyup(projects=projects, batch=batch, fromfolder=fromfolder, outputlist=outputlist, outputqueue=outputqueue, processes=processes)
    toc(starttime, label='batchBOC')
    
    return projects


def boc_task(project, ind, outputqueue, budgetratios, name, parsetname, progsetname, objectives, constraints,absconstraints,proporigconstraints, maxiters,
             maxtime, verbose, stoppingfunc, maxload, interval, prerun, batch, mc, die, recalculate, strict, randseed):
    
    # Custom opening
    if batch: loadbalancer(index=ind, maxload=maxload, interval=interval, label=project.name)
    printv('Running BOC generation...', 1, verbose)
    if prerun:
        if parsetname is None: parsetname = -1 # TODO: improve handling of this
        rerun = False
        try:
            results = project.parsets[parsetname].getresults() # First, try getting results 
            if results is None: rerun = True
        except:
            rerun = True
        if rerun: 
            printv('No results set found, so rerunning model...', 2, verbose)
            project.runsim(parsetname) # Rerun if exception or if results is None
    
    # The meat
    boc = None
    if not recalculate: # If we're not recalculating BOCs, check to see if this project already has one
        boc = project.getBOC(objectives=objectives, strict=strict, verbose=verbose)
    if recalculate or boc is None: # Only run if requested or if a BOC can't be found -- otherwise, skip and return immediately
        if randseed is not None: randseed += (ind+1)*(2**9-1) # Just perturb it so we don't get repeats
        try:
            project.genBOC(budgetratios=budgetratios, name=name, parsetname=parsetname,
                           progsetname=progsetname, objectives=objectives, 
                           constraints=constraints, absconstraints=absconstraints, proporigconstraints=proporigconstraints,
                           maxiters=maxiters, maxtime=maxtime,
                           verbose=verbose, stoppingfunc=stoppingfunc, mc=mc, die=die, randseed=randseed)
        except Exception as E:
            project.addwarning('Exception: batchBOC() failed for %s: %s' % (project.name, repr(E)))
            project.getwarnings()
    
    # Standardized close
    print('...done.')
    if batch: 
        outputqueue.put(project)
        return None
    else:
        return project



def reoptimizeprojects(projects=None, objectives=None, maxtime=None, maxiters=None, mc=None, maxload=None, interval=None, batch=True, verbose=2, randseed=None):
    ''' Runs final optimisations for initbudgets and optbudgets so as to summarize GA optimization '''
    
    printv('Reoptimizing portfolio projects...', 2, verbose)
    starttime = tic()
    resultpairs = odict()
    if batch:
        outputqueue = Queue()
        processes = []
    else:
        outputqueue = None
    for pind,project in enumerate(projects.values()):
        args = (project, objectives, pind, outputqueue, maxtime, maxiters, mc, batch, maxload, interval, verbose, randseed)
        if batch:
            prc = Process(target=reoptimizeprojects_task, args=args)
            prc.start()
            processes.append(prc)
        else:
            resultpair = reoptimizeprojects_task(*args)
            resultpairs[resultpair['key']] = resultpair
    if batch:
        for key in projects.keys():
            resultpair = outputqueue.get()
            resultpairs[resultpair['key']] = resultpair
        for prc in processes:
            prc.join()
        resultpairs.sort(sortby=list(projects.keys())) # Ensure it's sorted
        
    # Print any warnings, if they exist
    for project in projects.values(): project.getwarnings() 
    
    # Restore project links
    for key,resultpair in resultpairs.items():
        for result in resultpair.values():
            if hasattr(result, 'projectref'): # Not guaranteed to be a result (keys are stored here too)
                result.projectref = Link(projects[key])
    
    printv('Reoptimization complete', 2, verbose)
    toc(starttime, label='reoptimizeprojects')
    
    return resultpairs
        

def reoptimizeprojects_task(project, objectives, pind, outputqueue, maxtime, maxiters, mc, batch, maxload, interval, verbose, randseed):
    """Batch function for final re-optimization step of geospatial analysis."""
    if batch: loadbalancer(index=pind, maxload=maxload, interval=interval, label=project.name)
    
    # Figure out which budget to use as a starting point
    boc = project.getBOC(objectives)
    defaultbudget = boc.defaultbudget[:].sum()
    totalbudget = boc.gaoptimbudget
    smallestmismatch = inf
    for budget in boc.budgets.values(): # Could be done with argmin() but this is more explicit...
        thismismatch = abs(totalbudget-budget[:].sum())
        if thismismatch<smallestmismatch:
            closestbudget = dcp(budget)
            smallestmismatch = thismismatch
    
    # Extract info from the BOC and specify argument lists...painful
    sharedargs = {'objectives':boc.objectives, 
                  'constraints':boc.constraints, 
                  'parsetname':boc.parsetname, 
                  'progsetname':boc.progsetname,
                  'verbose':verbose
                  }
    outcalcargs = {'project':project,
                   'outputresults':True,
                   'doconstrainbudget':True}
    optimargs = {'label':project.name,
                 'maxtime': maxtime,
                 'maxiters': maxiters,
                 'mc':mc,
                 'randseed':randseed}

    # Run the analyses
    resultpair = odict()
    
    # Initial spending
    printv('%s: calculating initial outcome for budget $%0.0f' % (project.name, defaultbudget), 2, verbose)
    sharedargs['origbudget'] = boc.defaultbudget
    sharedargs['objectives']['budget'] = defaultbudget
    outcalcargs.update(sharedargs)
    resultpair['init'] = outcomecalc(**outcalcargs)
    
    # Optimized spending -- reoptimize
    try:
        if totalbudget: printv('%s: reoptimizing with budget $%0.0f, starting from %0.1f%% mismatch...' % (project.name, totalbudget, smallestmismatch/totalbudget*100), 2, verbose)
        else:           printv('%s: total budget is zero, skipping optimization...' % project.name, 2, verbose)
        sharedargs['origbudget'] = closestbudget
        sharedargs['objectives']['budget'] = totalbudget
        optimargs.update(sharedargs)
        if totalbudget: resultpair['opt'] = project.optimize(**optimargs)
        else:           resultpair['opt'] = outcomecalc(**outcalcargs) # Just calculate the outcome
        resultpair['init'].name = project.name+' GA initial'
        resultpair['opt'].name = project.name+' GA optimal'
        resultpair['key'] = project.name # Store the project name to avoid mix-ups
    except Exception as E:
        project.addwarning('Exception: reoptimizeprojects() failed for %s: %s' % (project.name, repr(E)))
        project.getwarnings()
    
    if batch: 
        outputqueue.put(resultpair)
        return None
    else:
        return resultpair