def makefittedpars(G, opt, verbose=2):
    """
    Prepares model parameters to run the simulation.
    
    Version: 2014nov23 by cliffk
    """
    
    from printv import printv
    from matplotlib.pylab import array, ones
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    printv('Making fitted parameters...', 1, verbose)
    
    # Initialize fitted parameters
    F = []
    for s in range(opt.nsims):
        F.append(struct())
        F[s].__doc__ = 'Fitted parameters for simulation %i: initial prevalence, force-of-infection, diagnoses, treatment' % s
        F[s].init = ones(G.npops)
        F[s].force = ones(G.npops)
        F[s].dx = array([1, 1, (G.datastart+G.dataend)/2, 1])
        F[s].tx1 = array([1, 1, (G.datastart+G.dataend)/2, 1])
        F[s].tx2 = array([1, 1, (G.datastart+G.dataend)/2, 1])
    
    return F