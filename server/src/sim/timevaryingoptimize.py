# Imports for all functions
from printv import printv
from bunch import Bunch as struct
from matplotlib.pylab import show, figure, subplot, plot, axis, xlim, ylim, legend
from numpy import ones, zeros, arange, random, absolute

def optimize(D, objectives=None, constraints=None, budgets=None, optimstartyear=2015, optimendyear=2030, ntimepm=1, randomize=1, timelimit=60, progressplot=False, verbose=2):
    """
    Allocation optimization code:
        D is the project data structure
        objectives is a dictionary defining the objectives of the optimization
        constraints is a dictionary defining the constraints on the optimization
        timelimit is the maximum time in seconds to run optimization for
        verbose determines how much information to print.
        
    Version: 2014dec01 by cliffk
    """
    
    ###############################################################################
    ## Setup
    ###############################################################################    
    
    printv('Running optimization...', 1, verbose)
    
    # Imports
    from model import model
    from copy import deepcopy
    from ballsd import ballsd
    from getcurrentbudget import getcurrentbudget
    from makemodelpars import makemodelpars
    from timevarying import timevarying
    
    # Set options to update year range - AS: I've set different variables here, let me know if that's not what was wanted
    from setoptions import setoptions
    D.opt = setoptions(D.opt, optimstartyear=optimstartyear, optimendyear=optimendyear)
    
    # Make sure objectives, constraints and budgets exist
    if not isinstance(objectives, struct):  objectives  = defaultobjectives(D, verbose=verbose)
    if not isinstance(constraints, struct): constraints = defaultconstraints(D, verbose=verbose)
    if not isinstance(budgets, list):       budgets     = defaultbudgets(verbose=verbose)
    
    # Convert weightings from percentage to number
    if objectives.outcome.inci:  objectives.outcome.inciweight  = float(objectives.outcome.inciweight) / 100.0
    if objectives.outcome.daly:  objectives.outcome.dalyweight  = float(objectives.outcome.dalyweight) / 100.0
    if objectives.outcome.death: objectives.outcome.deathweight = float(objectives.outcome.deathweight) / 100.0
    if objectives.outcome.cost:  objectives.outcome.costweight  = float(objectives.outcome.costweight) / 100.0

    # Set up objectives
    for ob in objectives.money.objectives.keys():
        if objectives.money.objectives[ob].use: objectives.money.objectives[ob].by = float(objectives.money.objectives[ob].by) / 100.0

    # Set up costs
    for prog in objectives.money.costs.keys():
        objectives.money.costs[prog] = float(objectives.money.costs[prog]) / 100.0

    # Set up constraints
    for prog in constraints.decrease.keys():
        if constraints.decrease[prog].use: constraints.decrease[prog].by = float(constraints.decrease[prog].by) / 100.0

    # Original spending -- copied from D.A
    originalspend = deepcopy(D.A[0].alloc)
    
    # Initialize optimisation results structure
    D.O = [struct()]
    D.O[0].__doc__ = 'Optimization results' # AS: Errr... how do you do this here?!? -- CK: You made it a list so need [0]
    
    # Number of budgets to optimize
    nbudgets = len(budgets)
    nprogs = len(originalspend)
    
    ###############################################################################
    ## Objective function
    ############################################################################### 

    def objectivecalc(optimparams):
        """ Calculate the objective function """
        
        thisalloc = timevarying(optimparams, ntimepm=ntimepm, nprogs=nprogs, t=D.opt.toptvec, totalspend=totalspend)
                
        
        # GO FROM HERE... getcurrentbudget now needs to handle allocation arrays as appose to just an allocation vector which remains the same over time        


        #TODO CK verify that it's OK
        alloc = None
        # Alter the parameters and run the model
        newD = deepcopy(D)
        newD, newcov, newnonhivdalysaverted = getcurrentbudget(newD, alloc)
        newD.M = makemodelpars(newD.P, newD.opt, withwhat='c', verbose=0)
        newD.opt.turnofftrans = D.opt.optimendyear # Turn off transmissions after this year
        S = model(newD.G, newD.M, newD.F[0], newD.opt, verbose=0)
        
        # Obtain value of the objective function
        objective = 0 # Preallocate objective value 
        if objectives.what == 'outcome':
            for ob in ['inci', 'death', 'daly', 'cost']:
                if objectives.outcome[ob]: objective += S[ob].sum() * objectives.outcome[ob + 'weight'] # TODO -- can we do 'daly' and 'cost' like this too??
        else: print('Work to do here') # 'money'
        
        if progressplot: # Just to test time-varying stuff
        
            # Store values for plotting
            global niter
            alliters[:, niter] = thisalloc
            allobjs[niter] = objective
            niter += 1        
            
            # Plot value of objective function
            figure(num=100)
            subplot(1,3,1)
            plot(range(niter), allobjs[range(niter)])
            ylim(ymin=0)
            xlim(xmin=0, xmax=maxiters)        
            
            # Plot allocations over iterations
            subplot(1,3,2)
            xlim(xmin=0, xmax=maxiters)
            for prog in range(nprogs): plot(range(niter), alliters[prog, range(niter)])
    
            # Plot this allocation over time
            for prog in range(nprogs): plot(D.opt.toptvec, thisalloc[prog, :])  
            plot(D.opt.toptvec, thisalloc.sum(axis=0), color='k', linewidth=3)
            
            ylim(ymin=0, ymax=round(totalspend + 100, -2))
    
            # Plot legend on the right        
            subplot(1,3,3)
            for prog in range(nprogs): plot(0, prog)
            legend(D.G.meta.progs.short, loc = 'center left')
            axis('off')
            show()        
        
        return objective
        
    ###############################################################################
    ## Run optimization # TODO -- actually implement :)
    ############################################################################### 
    
    # Iterate through the budgets
    for b in range(nbudgets):
        
        # This budget
        thisb = budgets[b]
        
        # Extending D.O struct -- AS: I imagine this is awful form, someone feel free to correct me!
        if b > 0: D.O.append(struct())
        
        # Check whether budget is the 'original' (denoted with a string)
        if isinstance(thisb, basestring):
            if thisb == 'original':

                # Nothing to do here -- just append original information
                printv('Original budget -- no optimisation to be done')
                D.O[b].allocation = originalspend # Copy original spending
                D.O[b].totalspend = originalspend.sum() # Sum up total spending
                D.O[b].budget = 1 # Factor of the original budget
                D.O[b].label = 'Original' # Append original label
            
            # Throw an exception is budget is any other string
            else: raise Exception('Budget not recognised')
        
        else: # Budget is a factor of original spending
        
            # Calculate total budget based on value of budgets[b]
            totalspend = originalspend.sum() * thisb
            D.O[b].totalspend = totalspend
            
            # Append budget (as a factor of original) and label
            D.O[b].budget = thisb
            D.O[b].label = 'Optimal ' + str(thisb * 100) + '%'
            
            ## TODO -- do constraint stuff here -- same as MatLab version, nice and easy.            
            
            if randomize: # Randomize the initial allocation prior to optimisation
            
                # Create array of random numbers and normalize
                randvec = random.random(nprogs)
                randvec = randvec / sum(randvec)
                
                # Initial allocation to be optimized
                thisalloc = randvec * totalspend
                
            # If flag is off, randomization is trivial
            else: thisalloc = originalspend * thisb

            # Quick sanity check for the sum of thisalloc
            if absolute(sum(thisalloc) - totalspend) > 1:
                raise Exception('Initial randomization issue')
    
            maxiters = 50 # Might not want to do it using maxiters
            if progressplot: # Set up stuff for plotting if necessary
                
                # Number of iterations
                global niter
                niter = 0
            
                # Preallocate arrays to store optimisation progress
                alliters = zeros((nprogs, maxiters+1))
                allobjs  = zeros(maxiters+1)
    
            # Run the optimization algorithm
            optalloc, fval, exitflag, output = ballsd(objectivecalc, thisalloc, xmin=zeros(nprogs), timelimit=120, verbose=10, MaxIter=maxiters-1, sinitial=ones(nprogs)*100000) # timelimit=timelimit, verbose=verbose)
    
    
    #### SORT THIS OUT...    
    
    # Update the model
    for i,alloc in enumerate([origalloc,optalloc]):
        D, D.A[i].coverage, D.A[i].nonhivdalysaverted = getcurrentbudget(D, alloc)
        D.M = makemodelpars(D.P, D.opt, withwhat='c', verbose=2)
        D.A[i].S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
        D.A[i].alloc = alloc # Now that it's run, store total program costs
    
    # Calculate results
    from makeresults import makeresults
    for alloc in range(len(D.A)):
        D.A[alloc].R = makeresults(D, [D.A[alloc].S], D.opt.quantiles, verbose=verbose)
    
    # Gather plot data
    from gatherplotdata import gatheroptimdata, gathermultidata
    D.plot.OA = gatheroptimdata(D, D.A, verbose=verbose)
    D.plot.OM = gathermultidata(D, D.A, verbose=verbose)
    
    printv('...done optimizing programs.', 2, verbose)
    return D



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
    ob.outcome.inciweight = 100 # "Incidence weighting"
    ob.outcome.daly = False # "Minimize cumulative DALYs"
    ob.outcome.dalyweight = 100 # "DALY weighting"
    ob.outcome.death = False # "Minimize cumulative AIDS-related deaths"
    ob.outcome.deathweight = 100 # "Death weighting"
    ob.outcome.cost = False # "Minimize cumulative costs"
    ob.outcome.costweight = 100 # "Cost weighting"
    
    ob.money = struct()
    ob.money.objectives = struct()
    for objective in ['inci', 'incisex', 'inciinj', 'mtct', 'mtctbreast', 'mtctnonbreast', 'deaths', 'dalys']:
        ob.money.objectives[objective] = struct()
        ob.money.objectives[objective].use = False # TIck box: by default don't use
        ob.money.objectives[objective].by = 50 # "By" text entry box: 0.5 = 50% reduction
        ob.money.objectives[objective].to = 0 # "To" text entry box: don't use if set to 0
    ob.money.objectives.inci.use = True # Set incidence to be on by default
    
    ob.money.costs = struct()
    for prog in D.programs.keys():
        ob.money.costs[prog] = 100 # By default, use a weighting of 100%
        
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
        con.decrease[prog].by = 50 # Text entry box: 0.5 = 50% per year
    
    con.coverage = struct()
    for prog in D.programs.keys(): # Loop over all defined programs
        con.coverage[prog] = struct()
        con.coverage[prog].use = False # Tick box: by default don't use
        con.coverage[prog].level = 0 # First text entry box: default no limit
        con.coverage[prog].year = 2030 # Year to reach coverage level by
        
    return con

    
def defaultbudgets(verbose=2):
    """
    Define default list of budgets for optimisation
    """
    
    printv('Defining default budgets...', 3, verbose=verbose)
    
    binc = 0.1 # Default budget increment    
    
    # Default budgets are effectively 0:0.1:2, plus the original budget
    budgets = [1e-10] + arange(binc, 1+binc, binc).tolist() + \
    ['original'] + arange(1+binc, 2+binc, binc).tolist()
    
    return budgets
    
    