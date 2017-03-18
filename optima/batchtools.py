"""
BATCHTOOLS

Functions for doing things in batch...yeah, should make better.

Note - tasks have to be standalone functions or they break on windows, see
http://stackoverflow.com/questions/9670926/multiprocessing-on-windows-breaks

Version: 2017mar09
"""

from multiprocessing import Process, Queue
from numpy import empty, inf
from optima import loadproj, loadbalancer, printv, getfilelist, dcp, odict, outcomecalc


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


def autofit_task(project, ind, outputqueue, name, fitwhat, fitto, maxtime, maxiters, verbose, maxload):
    """Kick off the autofit task for a given project file."""
    loadbalancer(index=ind, maxload=maxload)
    print('Running autofitting...')
    project.autofit(name=name, orig=name, fitwhat=fitwhat, fitto=fitto, maxtime=maxtime, maxiters=maxiters, verbose=verbose)
    project.save()
    outputqueue.put(project)
    print('...done.')
    return None


def batchautofit(folder=None, name=None, fitwhat=None, fitto='prev', maxtime=None, maxiters=200, verbose=2, maxload=0.5):
    ''' Perform batch autofitting '''
    
    if folder is None: folder = '.'
    filelist = getfilelist(folder, 'prj')
    nfiles = len(filelist)

    outputqueue = Queue()
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for i in range(nfiles):
        printv('Calibrating file "%s"' % filelist[i], 3, verbose)
        project = loadproj(filelist[i])
        project.filename = filelist[i]
        prc = Process(target=autofit_task, 
                      args=(project, i, outputqueue, name, fitwhat, fitto, maxtime, maxiters, verbose, maxload))
        prc.start()
        processes.append(prc)
    for i in range(nfiles):
        outputlist[i] = outputqueue.get() # This is needed or else the process never finishes
    for prc in processes:
        prc.join() # Wait for them to finish
    
    return outputlist


def boc_task(project, ind, outputqueue, budgetratios, name, parsetname, progsetname, objectives, constraints,
             maxiters, maxtime, verbose, stoppingfunc, method, maxload, interval, prerun, batch, mc, die):
    if batch: loadbalancer(index=ind, maxload=maxload, interval=interval, label=project.name)
    printv('Running BOC generation...', 1, verbose)
    if prerun:
        if parsetname is None: parsetname = -1 # WARNING, not fantastic, but have to explicitly handle this now
        rerun = False
        try:
            results = project.parsets[parsetname].getresults() # First, try getting results 
            if results is None: rerun = True
        except:
            rerun = True
        if rerun: 
            printv('No results set found, so rerunning model...', 2, verbose)
            project.runsim(parsetname) # Rerun if exception or if results is None
    project.genBOC(budgetratios=budgetratios, name=name, parsetname=parsetname,
                   progsetname=progsetname, objectives=objectives, 
                   constraints=constraints, maxiters=maxiters, maxtime=maxtime,
                   verbose=verbose, stoppingfunc=stoppingfunc, method=method, mc=mc, die=die)
    print('...done.')
    if batch: 
        outputqueue.put(project)
        return None
    else:
        return project


def batchBOC(folder=None, projects=None, budgetratios=None, name=None, parsetname=None, progsetname=None, objectives=None, 
             constraints=None,  maxiters=200, maxtime=None, verbose=2, stoppingfunc=None, method='asd', 
             maxload=0.5, interval=None, prerun=True, batch=True, mc=3, die=False):
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
        method - optimization algorithm to use for optimization runs that
                comprise the BOC
        maxload - how much of the CPU to use
    """
    
    # If no projects supplied, load them from the folder
    if projects is None:
        fromfolder = True
        if folder is None: folder = '.'
        filelist = getfilelist(folder, 'prj')
        nfiles = len(filelist)
        projects = odict()
        for i in range(nfiles):
            proj = loadproj(filelist[i])
            proj.filename = filelist[i] # Ensure the filename is up-to-date since we'll save later
            projects[proj.name] = proj
    else:
        fromfolder = False
    
    # Housekeeping
    if batch: outputqueue = Queue()
    else: outputqueue = None
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for key,project in projects.items():
        if project.name != key: 
            msg = 'Warning, project name and key do not match (%s vs. %s), updating...' % (project.name, key)
            printv(msg, 2, verbose)
        project.name = key # Ensure these match, since used to repopulate the odict
    
    # Loop over the projects
    for i,project in enumerate(projects.values()):
        prjobjectives = project.optims[-1].objectives if objectives == 'latest' else objectives
        prjconstraints = project.optims[-1].constraints if constraints == 'latest' else constraints
        args = (project, i, outputqueue, budgetratios, name, parsetname, 
                progsetname, prjobjectives, prjconstraints, maxiters, 
                maxtime, verbose, stoppingfunc, method, maxload, interval, prerun, batch, mc, die)
        if batch:
            prc = Process(target=boc_task, args=args)
            prc.start()
            processes.append(prc)
        else:
            outputlist[i] = boc_task(*args) # Simply store here 
    
    # Extra tasks required for batch runs
    if batch:
        for i in range(nfiles):
            outputlist[i] = outputqueue.get()  # This is needed or else the process never finishes
        for prc in processes:
            prc.join() # Wait for them to finish
    
    # Update the odict
    for i,project in enumerate(outputlist):
        projects[project.name] = project
    
    # If loaded from a folder, save
    if fromfolder:
        for project in projects.values():
            project.save(filename=project.tmpfilename)
    
    return projects


def reoptimizeprojects(projects=None, objectives=None, maxtime=None, maxiters=None, mc=None, maxload=None, interval=None, batch=True, verbose=2):
    ''' Runs final optimisations for initbudgets and optbudgets so as to summarise GA optimisation '''
    
    printv('Reoptimizing portfolio projects...', 2, verbose)
    resultpairs = odict()
    if batch:
        outputqueue = Queue()
        processes = []
    else:
        outputqueue = None
    for pind,project in enumerate(projects.values()):
        args = (project, objectives, pind, outputqueue, maxtime, maxiters, mc, batch, maxload, interval, verbose)
        if batch:
            prc = Process(target=reoptimizeprojects_task, args=args)
            prc.start()
            processes.append(prc)
        else:
            resultpair = reoptimizeprojects_task(*args)
            resultpairs[resultpair['key']] = resultpair
    if batch:
        for key in projects:
            resultpair = outputqueue.get()
            resultpairs[resultpair['key']] = resultpair
        for prc in processes:
            prc.join()
    
    printv('Reoptimization complete', 2, verbose)
    
    return resultpairs      
        

def reoptimizeprojects_task(project, objectives, pind, outputqueue, maxtime, maxiters, mc, batch, maxload, interval, verbose):
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
                 'mc':mc}

    # Run the analyses
    resultpair = odict()
    
    # Initial spending
    printv('%s: calculating initial outcome for budget $%0.0f' % (project.name, defaultbudget), 2, verbose)
    sharedargs['origbudget'] = boc.defaultbudget
    sharedargs['objectives']['budget'] = defaultbudget
    outcalcargs.update(sharedargs)
    resultpair['init'] = outcomecalc(**outcalcargs)
    
    # Optimal spending -- reoptimize
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
    
    if batch: 
        outputqueue.put(resultpair)
        return None
    else:
        return resultpair