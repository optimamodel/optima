"""
BATCHTOOLS

Functions for doing things in batch...yeah, should make better.

Version: 2016mar20
"""

from multiprocessing.dummy import Process, Queue
from numpy import empty
from glob import glob
from optima import loadobj, saveobj, loadbalancer
from os import path


# Note - tasks have to be standalone functions or they break on windows, see
# http://stackoverflow.com/questions/9670926/multiprocessing-on-windows-breaks


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
        prc = Process(
            target=batchtest_task, 
            args=(obj, i, outputqueue, nprocs, nrepeats, maxload))
        prc.start()
        processes.append(prc)
    for i in range(nprocs):
        outputlist[i] = outputqueue.get()
    
    return outputlist


def autofit_task(
        project, ind, outputqueue, name, fitwhat, fitto, maxtime, maxiters,
        inds, verbose):
    """Kick off the autofit task for a given project file."""
    loadbalancer(index=ind)
    print('Running autofitting...')
    # Run automatic fitting and update calibration
    project.autofit(
        name=name, orig=name, fitwhat=fitwhat, fitto=fitto, maxtime=maxtime, 
        maxiters=maxiters, inds=inds, verbose=verbose)
    outputqueue.put(project)
    print('...done.')
    return None


def batchautofit(
        folder='.', name=None, fitwhat=None, fitto='prev', maxtime=None, 
        maxiters=200, inds=None, verbose=2):
    ''' Perform batch autofitting '''
    
    filelist = glob(path.join(folder, '*.prj'))
    nfiles = len(filelist)

    outputqueue = Queue()
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for i in range(nfiles):
        loadbalancer(0.5)
        project = loadobj(filelist[i])
        prc = Process(
            target=autofit_task, 
            args=(project, i, outputqueue, name, fitwhat, fitto, maxtime, 
                  maxiters, inds, verbose))
        prc.start()
        processes.append(prc)
    for i in range(nfiles):
        outputlist[i] = outputqueue.get()
        outputlist[i].save(filename=filelist[i])
    
    return outputlist


def boc_task(project, ind, outputqueue, budgetlist, name, parsetname,
             progsetname, inds, objectives, constraints, maxiters, maxtime,
             verbose, stoppingfunc, method):
    loadbalancer(index=ind)
    print('Running BOC generation...')
    project.genBOC(
        budgetlist=budgetlist, name=name, parsetname=parsetname,
        progsetname=progsetname, inds=inds, objectives=objectives, 
        constraints=constraints, maxiters=maxiters, maxtime=maxtime,
        verbose=verbose, stoppingfunc=stoppingfunc, method=method)
    outputqueue.put(project)
    print('...done.')
    return None


def batchBOC(
        folder='.', budgetlist=None, name=None, parsetname=None, 
        progsetname=None, inds=0, objectives=None, constraints=None, 
        maxiters=200, maxtime=None, verbose=2, stoppingfunc=None, 
        method='asd'):
    ''' Perform batch BOC calculation '''
    
    filelist = glob(path.join(folder, '*.prj'))
    nfiles = len(filelist)
    
    outputqueue = Queue()
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for i in range(nfiles):
        project = loadobj(filelist[i])
        project.tmpfilename = filelist[i]
        prc = Process(
            target=boc_task,
            args=(project, i, outputqueue, budgetlist, name, parsetname, 
                  progsetname, inds, objectives, constraints, maxiters, 
                  maxtime, verbose, stoppingfunc, method))
        prc.start()
        processes.append(prc)
    for i in range(nfiles):
        outputlist[i] = outputqueue.get()
        saveobj(outputlist[i].tmpfilename, outputlist[i])
    
    return outputlist
