"""
BATCHTOOLS

Functions for doing things in batch...yeah, should make better.

Version: 2016mar20
"""

from multiprocessing import Process, Queue
from numpy import empty
from glob import glob
from optima import loadobj, saveobj



def batchtest(nprocs=4, nrepeats=3e7):
    ''' A simple example of how to run a parallel computation -- use this as a template for making more complex functions'''
    from pylab import rand
    
    def testfunc(obj, ind, outputqueue):
        print('Running slow test function...')
        for i in range(int(nrepeats)): i += 1
        output = obj+ind
        outputqueue.put(output)
        print('...done.')
        return None
    
    outputqueue = Queue()
    outputlist = empty(nprocs, dtype=object)
    processes = []
    for i in range(nprocs):
        obj = rand()
        prc = Process(target=testfunc, args=(obj, i, outputqueue))
        prc.start()
        processes.append(prc)
    for i in range(nprocs):
        outputlist[i] = outputqueue.get()
    
    return outputlist



def batchautofit(folder='.', name=None, fitwhat=None, fitto='prev', maxtime=None, maxiters=60, inds=None, verbose=2):
    ''' Perform batch autofitting '''
    
    filelist = glob(folder+'/*.prj')
    nfiles = len(filelist)

    def batchfunc(project, outputqueue):
        print('Running autofitting...')
        project.autofit(name=name, orig=name, fitwhat=fitwhat, fitto=fitto, maxtime=maxtime, maxiters=maxiters, inds=inds, verbose=verbose) # Run automatic fitting and update calibration
        outputqueue.put(project)
        print('...done.')
        return None
    
    outputqueue = Queue()
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for i in range(nfiles):
        project = loadobj(filelist[i])
        project.tmpfilename = filelist[i]
        prc = Process(target=batchfunc, args=(project, outputqueue))
        prc.start()
        processes.append(prc)
    for i in range(nfiles):
        outputlist[i] = outputqueue.get()
        saveobj(outputlist[i].tmpfilename, outputlist[i])
    
    return outputlist



def batchBOC(folder='.', budgetlist=None, name=None, parsetname=None, progsetname=None, inds=0, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, method='asd'):
    ''' Perform batch BOC calculation '''
    
    filelist = glob(folder+'/*.prj')
    nfiles = len(filelist)

    def batchfunc(project, outputqueue):
        print('Running BOC generation...')
        project.genBOC(budgetlist=budgetlist, name=name, parsetname=parsetname, progsetname=parsetname, inds=inds, objectives=objectives, constraints=constraints, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method)
        outputqueue.put(project)
        print('...done.')
        return None
    
    outputqueue = Queue()
    outputlist = empty(nfiles, dtype=object)
    processes = []
    for i in range(nfiles):
        project = loadobj(filelist[i])
        prc = Process(target=batchfunc, args=(project, outputqueue))
        prc.start()
        processes.append(prc)
    for i in range(nfiles):
        outputlist[i] = outputqueue.get()
        saveobj(filelist[i], outputlist[i])
    
    return outputlist
