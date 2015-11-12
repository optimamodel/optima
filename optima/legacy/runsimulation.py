def runsimulation(D, verbose=2, makeplot = 0, dosave = True):
    """
    Calculate initial model estimates.

    Version: 2015mar23 by cliffk
    """

    from printv import printv
    printv('Running simulation...', 1, verbose)
    
    # Convert data parameters to model parameters
    if 'M' not in D.keys():
        from makemodelpars import makemodelpars
        D['M'] = makemodelpars(D['P'], D['opt'], verbose=verbose)

    # Run model
    from model import model
    allsims = []
    for s in range(len(D['F'])): # TODO -- parallelize
        S = model(G=D['G'], tmpM=D['M'], tmpF=D['F'][s], opt=D['opt'], verbose=verbose)
        allsims.append(S)
    D['S'] = allsims[0] # Save one full sim structure for troubleshooting and funsies

#    print('WARNING should add conditionals here')
#    from makeccocs import makeallccocs
#    D = makeallccocs(D, verbose=verbose) # Do not plot, ever

    # Calculate results
    from makeresults import makeresults
    D['R'] = makeresults(D, allsims, D['opt']['quantiles'], verbose=verbose)

    # Gather plot data
    from gatherplotdata import gatheruncerdata
    D['plot']['E'] = gatheruncerdata(D, D['R'], verbose=verbose)

    # Save output
    if dosave:
        from dataio import savedata
        savedata(D['G']['projectfilename'], D, verbose=verbose)

    printv('...done running simulation for project %s.' % D['G']['projectfilename'], 2, verbose)
    return D
