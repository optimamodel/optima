from bunch import Bunch as struct
from printv import printv

def optimize(D, objectives=None, constraints=None, timelimit=60, verbose=2):
    """
    Allocation optimization code:
        D is the project data structure
        objectives is a dictionary defining the objectives of the optimization
        constraints is a dictionary defining the constraints on the optimization
        timelimit is the maximum time in seconds to run optimization for
        verbose determines how much information to print.
        
    Version: 2014nov24 by cliffk
    """
    
    from time import time
    from model import model
    printv('Running optimization...', 1, verbose)
    
    # Make sure objectives and constraints exist
    if objectives==None: objectives = defaultobjectives(D, verbose=verbose)
    if constraints==None: constraints = defaultconstraints(D, verbose=verbose)
    
    # Run optimization # TODO -- actually implement :)
    tstart = time()
    elapsed = 0
    iteration = 0
    while elapsed<timelimit:
        iteration += 1
        elapsed = time() - tstart
        D.S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
        printv('Iteration: %i | Elapsed: %f s |  Limit: %f s' % (iteration, elapsed, timelimit), 2, verbose)
        D.S.mismatch = -1 # Mismatch for this simulation
    
    D.A = struct()
    D.A.__doc__ = 'Optimal allocation results'
    D.A.orig = zeros(len(D.data.costcov.cost))
    
    allsims = [D.S]
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(allsims, D, D.opt.quantiles, verbose=verbose)
    
    # Gather data into a simple structure for plotting -- Z for "optimiZation"
    D.O.optim = gatheroptimdata(D)
    
    printv('...done optimizing programs.', 2, verbose)
    return D



def gatheroptimdata(D):
    """
    Return the data for plotting the optimization pie charts.
    """
    
    
    
    optim = struct()
    
    return optim
    



def defaultobjectives(D, verbose=2):
    """
    Define default objectives for the optimization.
    """

    printv('Defining default objectives...', 3, verbose=verbose)

    ob = struct() # Dictionary of all objectives
    ob.year = struct() # Time periods for objectives
    ob.year.start = 2015 # "Year to begin optimization from"
    ob.year.numyears = 5 # "Number of years to optimize funding for"
    ob.year.until = 2030 # "Year to project outcomes to"
    ob.what = 'outcome' # Alternative is "money"
    
    ob.outcome = struct()
    ob.outcome.fixed = 1e6 # "With a fixed amount of money available"
    ob.outcome.inci = True # "Minimize cumulative HIV incidence"
    ob.outcome.inciweight = 1 # "Incidence weighting"
    ob.outcome.daly = False # "Minimize cumulative DALYs"
    ob.outcome.dalyweight = 1 # "DALY weighting"
    ob.outcome.death = False # "Minimize cumulative HIV-related deaths"
    ob.outcome.deathweight = 1 # "Death weighting"
    ob.outcome.cost = False # "Minimize cumulative DALYs"
    ob.outcome.costweight = 1 # "Cost weighting"
    
    ob.money.objectives = struct()
    for objective in ['inci', 'incisex', 'inciinj', 'mtct', 'mtctbreast', 'mtctnonbreast', 'deaths', 'dalys']:
        ob.money.objectives[objective] = struct()
        ob.money.objectives[objective].use = False # TIck box: by default don't use
        ob.money.objectives[objective].by = 0.5 # "By" text entry box: 0.5 = 50% reduction
        ob.money.objectives[objective].to = 0 # "To" text entry box: don't use if set to 0
    ob.money.inci.use = True # Set incidence to be on by default
    
    ob.money.costs = struct()
    for prog in D.programs.keys():
        ob.money.costs[prog] = 1 # By default, use a weighting of 1
        
    return ob




def defaultconstraints(D, verbose=2):
    """
    Define default constraints for the optimization.
    """
    
    printv('Defining default constraints...', 3, verbose=verbose)
    
    con = struct()
    con.txelig = 4 # 4 = "All people diagnosed with HIV"
    con.dontstopart = True # "No one who initiates treatment is to stop receiving ART"
    con.decrease = struct()
    for prog in D.programs.keys(): # Loop over all defined programs
        con.decrease[prog] = struct()
        con.decrease[prog].use = False # Tick box: by default don't use
        con.decrease[prog].by = 0.5 # Text entry box: 0.5 = 50% per year
    
    con.coverage = struct()
    for prog in D.programs.keys(): # Loop over all defined programs
        con.coverage[prog] = struct()
        con.coverage[prog].use = False # Tick box: by default don't use
        con.coverage[prog].level = 0 # First text entry box: default no limit
        con.coverage[prog].year = 2030 # Year to reach coverage level by
        
    return con