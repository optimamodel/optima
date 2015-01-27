def runsimulation(D, simstartyear=2000, simendyear=2030, verbose=2, makeplot = 0, dosave = True):
    """
    Calculate initial model estimates.

    Version: 2015jan16 by cliffk
    """

    from printv import printv
    printv('Running simulation...', 1, verbose)
    # please don't use dosave here, let's just save by default. it makes no sense to save in file in web environment :)

    # Set options to update year range
    from setoptions import setoptions
    D.opt = setoptions(D.opt, simstartyear=simstartyear, simendyear=simendyear)

    # Convert data parameters to model parameters
    if 'M' not in D.keys():
        from makemodelpars import makemodelpars
        D.M = makemodelpars(D.P, D.opt, verbose=verbose)

    # Run model
    from model import model
    allsims = []
    for s in range(len(D.F)): # TODO -- parallelize
        S = model(D.G, D.M, D.F[s], D.opt, verbose=verbose)
        allsims.append(S)
    D.S = allsims[0] # Save one full sim structure for troubleshooting and funsies

    print('WARNING should add conditionals here')
    from makeccocs import makeallccocs
    D = makeallccocs(D, verbose=verbose) # Do not plot, ever

    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(D, allsims, D.opt.quantiles, verbose=verbose)

    # Gather plot data
    from gatherplotdata import gatheruncerdata
    D.plot.E = gatheruncerdata(D, D.R, verbose=verbose)

    # Save output
    if dosave:
        from dataio import savedata
        savedata(D.G.projectfilename, D, verbose=verbose)

    printv('...done running simulation for project %s.' % D.G.projectfilename, 2, verbose)
    return D
