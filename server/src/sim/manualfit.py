## Imports used in multiple functions
from nested import getnested, setnested, iternested


def manualfit(D, F, Plist=[], Mlist=[], startyear=2000, endyear=2015, verbose=2):
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
        
    Version: 2014nov29 by cliffk
    """
    from printv import printv
    printv('Running manual calibration...', 1, verbose)
    
    # Update P and M, if provided
    D = updateP(D, Plist)
    D = updateM(D, Mlist)

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




def updateP(D, Plist):
    """ 
    Update certain fields of D.P and D.M only. Plist is a list of parameter names
    and values matching the structure of D.P.
    
    Version: 2014nov29 by cliffk
    """
    from copy import deepcopy
    from makemodelpars import makemodelpars
    
    oldP = deepcopy(D.P)
    for twig in iternested(D.P):
        setnested(D.P, Plist[twig].name, Plist[twig].data)
    
    oldM = makemodelpars(oldP, D.opt, withwhat='c', verbose=2)
    newM = makemodelpars(D.P, D.opt, withwhat='c', verbose=2)
    
    # Update M
    for twig in iternested(D.M):
        if not(all(getnested(oldM,twig) == getnested(newM,twig))): # Don't replace everything in M, only things that have just changed
            setnested(D.M, twig, getnested(newM,twig))
    
    return D




def updateM(D, Mlist):
    """ Update certain fields of D.M -- way easier than updating D.P :) """
    for twig in iternested(D.M): setnested(D.M, Mlist[twig].name, Mlist[twig].data)
    return D