def updateP(D, newP)
    from makemodelpars import makemodelpars
    from copy import deepcopy
    
    origM = deepcopy(D.M)
    newM = makemodelpars(newP, D.opt, withwhat='c', verbose=2)
    
    return D



def manualfit(D, F, newP=[], newM=[], startyear=2000, endyear=2015, verbose=2):
    """
    Manual metaparameter fitting code.
    
    Example usage:
        ipython --pylab # Run Python with Pylab
        ion() # Turn on interactive plotting
        import optima # Run Optima
        F = D.F # Shorten name for fitted parameters
        D = manualfit(D, F) # Run manualfit
        F.force *= 0 # Make a modification
        D = manualfit(D, F) # Rerun manualfit
        D = manualfit(D, F, dosave=True) # If the result is good, save
        
    Version: 2014nov26 by cliffk
    """
    
    from printv import printv
    from nested import setnested
    printv('Running manual calibration...', 1, verbose)
    
    # Update P, if provided
    D = updateP(D, newP)
    for par in range(len(newP)):
        try:
            setnested(D.P, newP[par].names, newP[par].data)
        except:
            print('WARNING, problem setting %s for P' % newP[par].names)
    
    # Update M, if provided
    for par in range(len(newM)):
        try:
            setnested(D.M, newM[par].names, newM[par].data)
        except:
            print('WARNING, problem setting %s for M' % newM[par].names)

    # Run model
    from model import model
    allsims = []
    D.F = [F]
    D.S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
    allsims.append(D.S)
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(D, allsims, D.opt.quantiles, verbose=verbose)

    # Gather plot data
    from gatherplotdata import gatherepidata
    D.plot.E = gatherepidata(D, D.R, verbose=verbose)
    
    printv('...done with manual calibration.', 2, verbose)
    return D
