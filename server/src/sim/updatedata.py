from copy import deepcopy

def updatedata(D, verbose=2, savetofile = True, input_programs = None):
    """
    Load the Excel workbook (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    programs - set up in GUI, contain information about the (adjusted) programs and parameters for the given project
    
    Version: 2015jan19 by cliffk
    """
    
    from loadworkbook import loadworkbook
    from makedatapars import makedatapars
    from makemodelpars import makemodelpars
    from runsimulation import runsimulation
    from dataio import savedata, fullpath
    from printv import printv
    printv('Updating data...', 1, verbose)
    
    datapath = fullpath(D.G.workbookname)
    D.data, D.programs = loadworkbook(datapath, input_programs, verbose=verbose)
    D.programs = restructureprograms(D.programs)
    D.data = getrealcosts(D.data)
    
    D = makedatapars(D, verbose=verbose) # Update parameters
    D.M = makemodelpars(D.P, D.opt, verbose=verbose)
    D = makefittedpars(D, verbose=verbose)
    D = runsimulation(D, makeplot = 0, dosave = False)
    if savetofile:
        savedata(D.G.projectfilename, D, verbose=verbose) # Update the data file
    
    printv('...done updating data.', 2, verbose)

    return D
    

def restructureprograms(programs):
    '''
    Restructure D.programs for easier use.
    '''

    ccparams = []
    convertedccparams = []
    nonhivdalys = [0.0]
    keys = ['ccparams','convertedccparams','nonhivdalys','effects','ccplot']
    for program in programs.keys():
        programs[program] = dict(zip(keys,[ccparams, convertedccparams, nonhivdalys, programs[program]]))

    return programs
    
    
    
def getrealcosts(data):
    '''
    Add inflation-adjsted costs to data structure
    '''

    from math import isnan

    cost = data.costcov.cost
    nprogs = len(data.costcov.cost)
    realcost = [[]]*nprogs
    cpi = data.econ.cpi.past[0] # get CPI
    cpibaseyearindex = data.econyears.index(data.epiyears[0])
    for prog in range(nprogs):
        if len(cost[prog])==1: # If it's an assumption, assume it's already in current prices
            realcost[prog] = cost[prog]
        else:
            realcost[prog] = [cost[prog][j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(cost[prog][j]) else float('nan') for j in range(len(cost[prog]))]
    
    data.costcov.realcost = realcost
    
    return data



def makefittedpars(D, verbose=2):
    """ Prepares fitted parameters for the simulation. """
    
    from printv import printv
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    printv('Initializing fitted parameters...', 1, verbose)
    
    # Initialize fitted parameters
    D.F = [struct() for s in range(D.opt.nsims)]
    for s in range(D.opt.nsims):
        span=0 if s==0 else 0.5 # Don't have any variance for first simulation
        D.F[s].__doc__ = 'Fitted parameters for simulation %i: initial prevalence, force-of-infection, population size, diagnoses, treatment' % s
        D.F[s].init  = perturb(D.G.npops,span)
        D.F[s].popsize = perturb(D.G.npops,span)
        D.F[s].force = perturb(D.G.npops,span)
        D.F[s].dx  = perturb(4,span)
        D.F[s] = unnormalizeF(D.F[s], D.M, D.G, normalizeall=True) # Un-normalize F
    
    return D


def unnormalizeF(normF, M, G, normalizeall=False):
    """ Convert from F values where everything is 1 to F values that can be real-world interpretable. """
    unnormF = deepcopy(normF)
    for p in range(G.npops):
        unnormF.init[p] *= M.hivprev[p] # Multiply by initial prevalence
        if normalizeall: unnormF.popsize[p] *= M.popsize[p][0] # Multiply by initial population size
    if normalizeall: unnormF.dx[3] *= G.datayears.mean() # Multiply by mean data year
    return unnormF


def normalizeF(unnormF, M, G, normalizeall=False):
    """ Convert from F values that can be real-world interpretable to F values where everything is 1. """
    normF = deepcopy(unnormF)
    for p in range(G.npops):
        normF.init[p] /= M.hivprev[p] # Divide by initial prevalence
        if normalizeall: normF.popsize[p] /= M.popsize[p][0] # Divide by initial population size
    if normalizeall: normF.dx[3] /= G.datayears.mean() # Divide by mean data year
    return normF



def perturb(n=1, span=0.5, randseed=None):
    """ Define an array of numbers uniformly perturbed with a mean of 1. n = number of points; span = width of distribution on either side of 1."""
    from numpy.random import rand, seed
    if randseed>=0: seed(randseed) # Optionally reset random seed
    output = 1. + 2*span*(rand(n)-0.5)
    output = output.tolist() # Otherwise, convert to a list
    return output



