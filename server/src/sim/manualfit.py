def manualfit(D, F, dosave=False, verbose=2):
    """
    Manual fitting code. Edit the structure F and rerun.
    
    Version: 2014nov05
    """
    from printv import printv    
    
    printv('1. Running simulation...', 1, verbose)
    from runsimulation import runsimulation
    D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)
    
    printv('2. Making results...', 1, verbose)
    from epiresults import epiresults
    D = epiresults(D, verbose=verbose)
    
    printv('3. Viewing results...', 1, verbose)
    from viewresults import viewresults
    viewresults(D, whichgraphs={'prev':1, 'inci':1, 'daly':1, 'death':1, 'pops':1, 'tot':1}, onefig=True, verbose=verbose)
    
    if dosave:
        from dataio import savedata
        savedata(D.projectfilename, D, verbose=verbose)
        printv('...done running simulation.', 2, verbose)
    
    return D
