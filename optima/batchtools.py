"""
BATCHTOOLS

Functions for doing things in batch...yeah, should make better.

Note - tasks have to be standalone functions or they break on windows, see
http://stackoverflow.com/questions/9670926/multiprocessing-on-windows-breaks

Version: 2017mar2
"""

from multiprocessing import Process, Queue
from numpy import empty
from glob import glob
from optima import loadproj, loadbalancer, printv
from os import path


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
    filelist = sorted(glob(path.join(folder, '*.prj')))
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
    
    return outputlist


def boc_task(project, ind, outputqueue, budgetlist, name, parsetname, progsetname, objectives, constraints,
             maxiters, maxtime, verbose, stoppingfunc, method, maxload, prerun, batch):
    if batch: loadbalancer(index=ind, maxload=maxload)
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
    project.genBOC(budgetlist=budgetlist, name=name, parsetname=parsetname,
                   progsetname=progsetname, objectives=objectives, 
                   constraints=constraints, maxiters=maxiters, maxtime=maxtime,
                   verbose=verbose, stoppingfunc=stoppingfunc, method=method)
    project.save(filename=project.tmpfilename)
    if batch: outputqueue.put(project)
    print('...done.')
    return None


def batchBOC(folder='.', budgetlist=None, name=None, parsetname=None, 
             progsetname=None, objectives=None, constraints=None, 
             maxiters=200, maxtime=None, verbose=2, stoppingfunc=None, 
             method='asd', maxload=0.5, prerun=True, batch=True):
    """
    Perform batch BOC calculation.

    Loops through all projects in the specified (default: current) directory,
    loads each project and sends to boc_task, along with any universal
    optimization settings to generate a budget-objective-curve for each
    project.

    Arguments:
        folder - the directory containing all projects for which a BOC will be
                calculated
        budgetlist - a vector of multiples of the current budget for which an
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
    
    filelist = sorted(glob(path.join(folder, '*.prj')))
    nfiles = len(filelist)
    
    if batch: outputqueue = Queue()
    else: outputqueue = None
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for i in range(nfiles):
        project = loadproj(filelist[i])
        project.tmpfilename = filelist[i]
        prjobjectives = project.optims[-1].objectives if objectives == 'latest' else objectives
        prjconstraints = project.optims[-1].constraints if constraints == 'latest' else constraints
        args = (project, i, outputqueue, budgetlist, name, parsetname, 
                progsetname, prjobjectives, prjconstraints, maxiters, 
                maxtime, verbose, stoppingfunc, method, maxload, prerun, batch)
        if batch:
            prc = Process(target=boc_task, args=args)
            prc.start()
            processes.append(prc)
        else:
            boc_task(*args)
    
    return outputlist
