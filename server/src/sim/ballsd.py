def ballsd(function, x, options = None, stepsize = 0.1, sinc = 2, sdec = 2, pinc = 2, pdec = 2, \
    pinitial = None, sinitial = None, absinitial = None, xmin = None, xmax = None, MaxRangeIter = 1000, \
    MaxFunEvals = None, MaxIter = 1e3, AbsTolFun = 1e-6, RelTolFun = 5e-3, TolX = None, StallIterLimit = 20, \
    fulloutput = True, maxarraysize = 1e6, timelimit = 3600, stoppingfunc = None, verbose = 10):
    """
    Optimization using the Bayesian adaptive locally linear stochastic descent 
    algorithm.
    
    X, FVAL, EXITFLAG, OUTPUT = ballsd(FUN,X0) starts at X0 and attempts to find a 
    local minimizer X of the function FUN. FUN accepts input X and returns a scalar 
    function value F evaluated  at X. X0 can be a scalar, list, or Numpy array of 
    any size. The outputs are:
               X -- The parameter set that minimizes the objective function
            FVAL -- The value of the objective function at X
        EXITFLAG -- The exit condition of the algorithm possibilities are:
                     0 -- Maximum number of function evaluations or iterations reached
                     1 -- Step size below threshold
                     2 -- Improvement in objective function below minimum threshold
                     3 -- Maximum number of iterations to calculate new parameter when out of range reached
                     4 -- Time limit exceeded
                     5 -- Stopping function criteria met
                    -1 -- Algorithm terminated for other reasons
          OUTPUT -- An object with the following attributes:
            iterations -- Number of iterations
             funcCount -- Number of function evaluations
                  fval -- Value of objective function at each iteration
                     x -- Vector of parameter values at each iteration
    
    ballsd() has the following options that can be set using keyword arguments. Their
    names and default values are as follows:
    
                   stepsize {0.1} -- Initial step size as a fraction of each parameter
                         sinc {2} -- Step size learning rate (increase)
                         sdec {2} -- Step size learning rate (decrease)
                         pinc {2} -- Parameter selection learning rate (increase)
                         pdec {2} -- Parameter selection learning rate (decrease)
      pinitial {ones(2*size(X0))} -- Set initial parameter selection probabilities
                    sinitial {[]} -- Set initial step sizes; if empty, calculated from stepsize instead
                        xmin {[]} -- Min value allowed for each parameter  
                        xmax {[]} -- Max value allowed for each parameter 
              MaxRangeIter {1000} -- Maximum number of iterations to calculate new parameter when out of range
      MaxFunEvals {1000*size(X0)} -- Maximum number of function evaluations
                    MaxIter {1e3} -- Maximum number of iterations (1 iteration = 1 function evaluation)
                 AbsTolFun {1e-3} -- Minimum absolute change in objective function
                 RelTolFun {5e-3} -- Minimum relative change in objective function
              TolX {1e-6*size(x)} -- Minimum change in parameters
              StallIterLimit {50} -- Number of iterations over which to calculate TolFun
                fulloutput {True} -- Whether or not to output the parameters and errors at each iteration
               maxarraysize {1e6} -- Limit on MaxIter and StallIterLimit to ensure arrays don't get too big
                 timelimit {3600} -- Maximum time allowed, in seconds
              stoppingfunc {None} -- External method that can be used to stop the calculation from the outside.
                      verbose {0} -- How much information to print during the run
  
    
    Example:
        from ballsd import ballsd
        from pylab import norm
        x, fval, exitflag, output = ballsd(norm, [1, 2, 3])
    
    
    Version: 2015jan16 by Cliff Kerr (cliff@thekerrlab.com)
    """
    
    from numpy import array, shape, reshape, ones, zeros, size, mean, cumsum, mod, hstack, floor
    from numpy.random import random # Was pylab.rand
    from utils import findinds # Remove dependency on pylab.find
    from copy import deepcopy # For arrays, even y = x[:] doesn't copy properly
    from time import time, sleep
    
    def consistentshape(userinput):
        """
        Make sure inputs have the right shape and data type.
        """
        origshape = shape(userinput)
        output = reshape(array(userinput,dtype='float'),-1)
        return output, origshape
    
    
    ## Handle inputs and set defaults
    nparams = size(x); # Number of parameters
    x, origshape = consistentshape(x) # Turn it into a vector but keep the original shape (not necessarily class, though)
    p,tmp = ones(2*nparams),0 if pinitial is None else consistentshape(pinitial)  # Set initial parameter selection probabilities -- uniform by default
    if absinitial is not None:
        s1,tmp = consistentshape([abs(i) for i in absinitial])
    else:
        s1,tmp = abs(stepsize*x),0 if sinitial is None else consistentshape([abs(i) for i in sinitial]) # Set initial parameter selection probabilities -- uniform by default
    s1 = hstack((s1,s1)) # need to duplicate since two for each parameter
    if xmax is not None: xmax,tmp = consistentshape(xmax)
    if xmin is not None: xmin,tmp = consistentshape(xmin)
    MaxFunEvals = 1000*nparams if MaxFunEvals == None else MaxFunEvals # Maximum number of function evaluations
    TolX = 1e-6*mean(x) if TolX == None else TolX  # Minimum change in parameters
    StallIterLimit = min(StallIterLimit, maxarraysize); # Don't by default let users create arrays larger than this -- slow and pointless
    MaxIter = min(MaxIter, maxarraysize);
    
    ## Initialization
    s1[s1==0] = mean(s1[s1!=0]) # Replace step sizes of zeros with the mean of non-zero entries
    fval = function(x) if options is None else function(x,options) # Calculate initial value of the objective function
    count = 0 # Keep track of how many iterations have occurred
    exitflag = -1 # Set default exit flag
    abserrorhistory = zeros(StallIterLimit) # Store previous error changes
    relerrorhistory = zeros(StallIterLimit) # Store previous error changes
    if fulloutput: # Include additional output structure
        fulloutputfval = zeros(MaxIter) # Store all objective function values
        fulloutputx = zeros((MaxIter,nparams)) # Store all parameters
    
    ## Loop
    start = time()
    while 1:
        sleep(0.1) # no tight loops please
        if verbose>=1: print('Iteration %i; elapsed %0.1f s; objective: %0.3e' % (count+1, time()-start, fval))
        
        # Calculate next step
        count += 1 # On each iteration there are two function evaluations
        p = p/sum(p) # Normalize probabilities
        cumprobs = cumsum(p) # Calculate the cumulative distribution
        inrange = 0
        count2 = 0
        while not inrange:
            count2=count2+1
            choice = findinds(cumprobs > random())[0] # Choose a parameter and upper/lower at random
            par = mod(choice,nparams) # Which parameter was chosen
            pm = floor((choice)/nparams) # Plus or minus
            newval = x[par] + ((-1)**pm)*s1[choice] # Calculate the new parameter set
            if count2 > MaxRangeIter: # if stuck due to x range limits, exit after 1000 iterations
                newval = x[par]
                #exitflag = -1
                inrange = 1
            elif (xmax is None) and (xmin is None): 
                inrange = 1
            elif (xmin is None) and (xmax is not None) and (newval <= xmax[par]):
                inrange = 1
            elif (xmax is None) and (xmin is not None) and (newval >= xmin[par]):
                inrange = 1
            elif (xmax is not None) and (xmin is not None) and (newval <= xmax[par]) and (newval >= xmin[par]):
                inrange = 1
            else:
                p[choice] = p[choice]/pdec # decrease probability of picking this parameter again
                s1[choice] = s1[choice]/sdec # decrease size of step for next time

        xnew = deepcopy(x) # Initialize the new parameter set
        xnew[par] = newval # Update the new parameter set
        fvalnew = function(xnew) if options is None else function(xnew, options) # Calculate the objective function for the new parameter set
        abserrorhistory[mod(count,StallIterLimit)] = fval - fvalnew # Keep track of improvements in the error
        relerrorhistory[mod(count,StallIterLimit)] = fval/float(fvalnew)-1 # Keep track of improvements in the error  
        if verbose>5:
            print('       choice=%s, par=%s, pm=%s, origval=%s, newval=%s, inrange=%s1' % (choice, par, pm, x[par], xnew[par], inrange))

        

        # Check if this step was an improvement
        fvalold = fval # Store old fval
        if fvalnew < fvalold: # New parameter set is better than previous one
            p[choice] = p[choice]*pinc # Increase probability of picking this parameter again
            s1[choice] = s1[choice]*sinc # Increase size of step for next time
            x = xnew # Reset current parameters
            fval = fvalnew # Reset current error
            if verbose>=5: flag = 'SUCCESS'
        elif fvalnew >= fvalold: # New parameter set is the same or worse than the previous one
            p[choice] = p[choice]/pdec # Decrease probability of picking this parameter again
            s1[choice] = s1[choice]/sdec # Decrease size of step for next time
            if verbose>=5: flag = 'FAILURE'
        if verbose>=5: print(' '*80 + flag + ' on step %i (old:%0.1f new:%0.1f diff:%0.5f ratio:%0.3f)' % (count, fvalold, fvalnew, fvalnew-fvalold, fvalnew/fvalold) )

        # Optionally store output information
        if fulloutput: # Include additional output structure
            fulloutputfval[count-1] = fval # Store objective function evaluations
            fulloutputx[count-1,:] = x # Store parameters
        
        # Stopping criteria
        if (count+1) >= MaxFunEvals: # Stop if the function evaluation limit is exceeded
            exitflag = 0 
            if verbose>=5: print('======== Maximum function evaluations reached (%i >= %i), terminating ========' % ((count+1), MaxFunEvals))
            break
        if count >= MaxIter: # Stop if the iteration limit is exceeded
            exitflag = 0 
            if verbose>=5: print('======== Maximum iterations reached (%i >= %i), terminating ========' % (count, MaxIter))
            break 
        if mean(s1) < TolX: # Stop if the step sizes are too small
            exitflag = 1 
            if verbose>=5: print('======== Step sizes too small (%f < %f), terminating ========' % (mean(s1), TolX))
            break
        if (count > StallIterLimit) and (abs(mean(abserrorhistory)) < AbsTolFun): # Stop if improvement is too small
            exitflag = 2 
            if verbose>=5: print('======== Absolute improvement too small (%f < %f), terminating ========' % (mean(abserrorhistory), AbsTolFun))
            break
        if (count > StallIterLimit) and (abs(mean(relerrorhistory)) < RelTolFun): # Stop if improvement is too small
            exitflag = 2 
            if verbose>=5: print('======== Relative improvement too small (%f < %f), terminating ========' % (mean(relerrorhistory), RelTolFun))
            break
        if count2 > MaxRangeIter: 
            exitflag = 3
            if verbose>=5: print('======== Can\'t find parameters within range (%i > %i), terminating ========' % (count2, MaxRangeIter))
            break
        if timelimit is not None and (time()-start)>timelimit:
            exitflag = 4
            if verbose>=5: print('======== Time limit reached (%f > %f), terminating ========' % ((time()-start), timelimit))
            break
        if stoppingfunc and stoppingfunc():
            exitflag = 5
            if verbose>=5: print('======== Stopping function called, terminating ========')
            break

    # Create additional output
    class makeoutput:
        iterations = count # Number of iterations
        funcCount = count+1 # Number of function evaluations
        if fulloutput: # Include additional output structure
            fval = fulloutputfval[0:count] # Function evaluations
            x = fulloutputx[0:count,:] # Parameters
    output = makeoutput()
    
    # Return x to its original shape
    x = reshape(x,origshape)

    return x, fval, exitflag, output
