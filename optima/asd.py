def asd(function, x, args=None, stepsize=0.1, sinc=2, sdec=2, pinc=2, pdec=2,
    pinitial=None, sinitial=None, absinitial=None, xmin=None, xmax=None,
    maxiters=None, maxtime=None, abstol=None, reltol=1e-3, stalliters=None,
    stoppingfunc=None, randseed=None, label=None, fulloutput=True, verbose=2):
    """
    Optimization using adaptive stochastic descent (ASD).
    
    output = asd(func,x0) starts at x0 and attempts to find a 
    local minimizer x of the function func. func accepts input x and returns a scalar 
    function value evaluated  at x. x0 can be a scalar, list, or Numpy array of 
    any size. 
    
    If fulloutput is False, then asd() returns x only. If it is true, then it returns
    a tuple with the following items:
        x          -- The parameter set that minimizes the objective function
        fval       -- The value of the objective function at each iteration (use fval[-1] for final)
        exitreason -- The reason the algorithm terminated
    
    asd() has the following options that can be set using keyword arguments. Their
    names and default values are as follows:
    
      stepsize       0.1     Initial step size as a fraction of each parameter
      sinc           2       Step size learning rate (increase)
      sdec           2       Step size learning rate (decrease)
      pinc           2       Parameter selection learning rate (increase)
      pdec           2       Parameter selection learning rate (decrease)
      pinitial       None    Set initial parameter selection probabilities
      sinitial       None    Set initial step sizes; if empty, calculated from stepsize instead
      xmin           None    Min value allowed for each parameter  
      xmax           None    Max value allowed for each parameter 
      maxiters       1000    Maximum number of iterations (1 iteration = 1 function evaluation)
      maxtime        3600    Maximum time allowed, in seconds
      abstol         1e-6    Minimum absolute change in objective function
      reltol         5e-3    Minimum relative change in objective function
      stalliters     50      Number of iterations over which to calculate TolFun
      stoppingfunc   None    External method that can be used to stop the calculation from the outside.
      randseed       None    The random seed to use
      fulloutput     True    Whether or not to return the full output
      verbose        2       How much information to print during the run
      label          None    A label to use to annotate the output
  
    Example:
        from asd import asd
        from numpy import norm
        x, fval, exitflag, output = asd(norm, [1, 2, 3])
    
    Version: 2017mar08 by Cliff Kerr (cliff@thekerrlab.com)
    """
    
    from numpy import array, shape, reshape, ones, zeros, mean, cumsum, mod, hstack, floor, flatnonzero, isnan, inf
    from numpy.random import random, seed
    from copy import deepcopy # For arrays, even y = x[:] doesn't copy properly
    from time import time
    if randseed is not None: seed(randseed) # Don't reset it if not supplied
    
    def consistentshape(userinput):
        """
        Make sure inputs have the right shape and data type.
        """
        origshape = shape(userinput)
        output = reshape(array(userinput,dtype='float'),-1)
        return output, origshape
    
    ## Handle inputs and set defaults
    if maxtime  is None: maxtime = 3600
    if maxiters is None: maxiters = 1000
    x, origshape = consistentshape(x) # Turn it into a vector but keep the original shape (not necessarily class, though)
    nparams = len(x) # Number of parameters
    p,tmp = ones(2*nparams),0 if pinitial is None else consistentshape(pinitial)  # Set initial parameter selection probabilities -- uniform by default
    
    # Handle step sizes
    if absinitial is None: s1,tmp = abs(stepsize*x),0 if sinitial is None else consistentshape([abs(i) for i in sinitial]) # Set initial parameter selection probabilities -- uniform by default
    else:                  s1,tmp = consistentshape([abs(i) for i in absinitial])
    s1 = hstack((s1,s1)) # need to duplicate since two for each parameter
    
    # Handle x limits
    if xmin is None: xmin = zeros(nparams)-inf
    else:            xmin,tmp = consistentshape(xmin)
    if xmax is None: xmax = zeros(nparams)+inf
    else:            xmax,tmp = consistentshape(xmax)
    
    # Final input checking
    if sum(isnan(x)): 
        errormsg = 'At least one value in the vector of starting points is NaN:\n%s' % x
        raise Exception(errormsg)
    if label is None: label = ''
    if stalliters is None: stalliters = 5*nparams # By default, try five times per parameter on average
    stalliters = int(stalliters)
    maxiters = int(maxiters)
    
    ## Initialization
    s1[s1==0] = mean(s1[s1!=0]) # Replace step sizes of zeros with the mean of non-zero entries
    fval = function(x, **args) # Calculate initial value of the objective function
    fvalorig = fval # Store the original value of the objective function, since fval is overwritten on each step
    count = 0 # Keep track of how many iterations have occurred
    abserrorhistory = zeros(stalliters) # Store previous error changes
    relerrorhistory = zeros(stalliters) # Store previous error changes
    fulloutputfval = zeros(maxiters) # Store all objective function values
    fulloutputx = zeros((maxiters, nparams)) # Store all parameters
    
    ## Loop
    start = time()
    offset = ' '*4 # Offset the print statements
    maxrangeiters = 1000 # Number of times to try generating a new parameter
    while True:
        if verbose==1: print(offset+label+'Iteration %i; elapsed %0.1f s; objective: %0.3e' % (count+1, time()-start, fval)) # For more verbose, use other print statement below
        
        # Calculate next parameters
        count += 1 # On each iteration there are two function evaluations
        p = p/sum(p) # Normalize probabilities
        cumprobs = cumsum(p) # Calculate the cumulative distribution
        inrange = False
        for r in range(maxrangeiters):
            choice = flatnonzero(cumprobs > random())[0] # Choose a parameter and upper/lower at random
            par = mod(choice,nparams) # Which parameter was chosen
            pm = floor((choice)/nparams) # Plus or minus
            newval = x[par] + ((-1)**pm)*s1[choice] # Calculate the new parameter set
            if newval>=xmin[par] and newval<=xmax[par]:
                inrange = True
                break
            else:
                p[choice] = p[choice]/pdec # decrease probability of picking this parameter again
                s1[choice] = s1[choice]/sdec # decrease size of step for next time
        
        if not inrange:
            if verbose>=2: print('======== Can\'t find parameters within range after %i tries, terminating ========' % maxrangeiters)
            break

        # Calculate the new value
        xnew = deepcopy(x) # Initialize the new parameter set
        xnew[par] = newval # Update the new parameter set
        fvalnew = function(xnew, **args) # Calculate the objective function for the new parameter set
        abserrorhistory[mod(count,stalliters)] = max(0, fval-fvalnew) # Keep track of improvements in the error
        relerrorhistory[mod(count,stalliters)] = max(0, fval/float(fvalnew)-1.0) # Keep track of improvements in the error  
        if verbose>=3:
            print(offset+'step=%i choice=%s, par=%s, pm=%s, origval=%s, newval=%s, inrange=%s' % (count, choice, par, pm, x[par], xnew[par], inrange))

        # Check if this step was an improvement
        fvalold = fval # Store old fval
        if fvalnew < fvalold: # New parameter set is better than previous one
            p[choice] = p[choice]*pinc # Increase probability of picking this parameter again
            s1[choice] = s1[choice]*sinc # Increase size of step for next time
            x = xnew # Reset current parameters
            fval = fvalnew # Reset current error
            flag = '++' # Marks an improvement
        elif fvalnew >= fvalold: # New parameter set is the same or worse than the previous one
            p[choice] = p[choice]/pdec # Decrease probability of picking this parameter again
            s1[choice] = s1[choice]/sdec # Decrease size of step for next time
            flag = '--' # Marks no change
        else:
            exitreason = 'Objective function returned NaN'
            break
        if verbose>=2: 
            print(offset + label + ' step %i (%0.1f s) %s (orig: %s | best:%s | new:%s | diff:%s)' % ((count, time()-start, flag)+multisigfig([fvalorig, fvalold, fvalnew, fvalnew-fvalold])))
        
        # Store output information
        fulloutputfval[count-1] = fval # Store objective function evaluations
        fulloutputx[count-1,:] = x # Store parameters
        
        # Stopping criteria
        if count >= maxiters: # Stop if the iteration limit is exceeded
            exitreason = 'Maximum iterations reached'
            break 
        if (time()-start) > maxtime:
            exitreason = 'Time limit reached (%s > %s)' % multisigfig([(time()-start), maxtime])
            break
        if (count>stalliters) and (abs(mean(abserrorhistory))<abstol): # Stop if improvement is too small
            exitreason = 'Absolute improvement too small (%s < %s)' % multisigfig([mean(abserrorhistory), abstol])
            break
        if (count>stalliters) and (sum(relerrorhistory)<reltol): # Stop if improvement is too small
            exitreason = 'Relative improvement too small (%s < %s)' % multisigfig([mean(relerrorhistory), reltol])
            break
        if stoppingfunc and stoppingfunc():
            exitreason = 'Stopping function called'
            break

    # Return
    x = reshape(x,origshape) # Parameters
    fval = fulloutputfval[:count] # Function evaluations
    if verbose>=2: print('=== %s %s (%i steps, orig: %s | best: %s | ratio: %s) ===' % ((label, exitreason, count)+multisigfig([fval[0], fval[-1], fval[-1]/fval[0]])))
    if fulloutput: return (x, fval, exitreason)
    else:          return x




def multisigfig(X, sigfigs=5):
    """ Return a string representation of variable x with sigfigs number of significant figures """
    from numpy import log10, floor
    
    output = []
    try: 
        n=len(X)
        islist = True
    except:
        X = [X]
        n = 1
        islist = False
    for i in range(n):
        x = X[i]
        try:
            if x==0:
                output.append('0')
            else:
                magnitude = floor(log10(abs(x)))
                factor = 10**(sigfigs-magnitude-1)
                x = round(x*factor)/float(factor)
                digits = int(abs(magnitude) + max(0, sigfigs - max(0,magnitude) - 1) + 1 + (x<0) + (abs(x)<1)) # one because, one for decimal, one for minus
                decimals = int(max(0,-magnitude+sigfigs-1))
                strformat = '%' + '%i.%i' % (digits, decimals)  + 'f'
                string = strformat % x
                output.append(string)
        except:
            output.append(str(x))
    if islist:
        return tuple(output)
    else:
        return output[0]