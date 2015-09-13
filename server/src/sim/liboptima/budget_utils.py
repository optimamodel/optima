# Helper functions for allocs and budgets
from copy import deepcopy

def scalealloctototal(curralloc,newtotal,pset):
	# Rescale an alloc, for a given program set
    
    # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
    # These will be ignored when testing different allocations.
    curralloc = deepcopy(curralloc)

    optimizable = pset.optimizable()
    fixedtrue = [1.0 if opt else 0.0 for opt in optimizable]

    # Extract the fixed costs from scaling.
    fixedtotal = sum([curralloc[i]*fixedtrue[i] for i in xrange(len(curralloc))])
    vartotal = sum([curralloc[i]*(1.0-fixedtrue[i]) for i in xrange(len(curralloc))])
    scaledtotal = newtotal - fixedtotal
    
    # Deal with a couple of possible errors.
    if scaledtotal < 0:
        print('Warning: You are attempting to generate an allocation for a budget total that is smaller than the sum of relevant fixed costs!')
        print('Continuing with the assumption that all non-fixed program allocations are zero.')
        print('This may invalidate certain analyses such as GPA.')
        scaledtotal = 0
    try:
        factor = scaledtotal/vartotal
    except:
        print("Possible 'divide by zero' error.")
        curralloc[0] = scaledtotal      # Shove all the budget into the first program.
    
    # Updates the alloc of this SimBudget according to the scaled values.
    return [curralloc[i]*(factor+(1-factor)*fixedtrue[i]) for i in xrange(len(curralloc))]


# alloc to budget: timevarying
def timevarying(allocpm, ntimepm=1, nprogs=None, tvec=None, totalspend=None, fundingchanges=None):

    """
    Determines allocation values over time for 2, 3 or 4 parameter time-varying
    optimisation.
    
    Inputs:
        allocpm
        ntimepm
        nprogs
        t
        totalspend
        
    Outputs:
        allocation
        
    Version: 2015jan15 by Roo
    """
    
    # Import stuff
    from numpy import asarray, tile, transpose, exp, power, maximum, absolute, ones
    
    # Sanity check for the values of ntimepm, nprogs and len(allocpm)
    if len(allocpm) / ntimepm != nprogs:
        raise Exception('Invalid number of parameters to define allocations over time (%i parameters, %i time parameters, %i programs)' % (len(allocpm), ntimepm, nprogs))

    # Set t to be between 0 and 1, and get the number of time points
    npts = len(tvec)
    tvec = asarray(tvec) - tvec[0]
    tvec = tile(tvec / float(max(tvec)), (nprogs, 1))
    
    if ntimepm == 1: # Non-time-varying optimisation

        # Repeat the vector across the npts time points - easy
        allocation = transpose(tile(allocpm, (npts, 1)))
            
    elif ntimepm == 2: # Two parameter curve - exponential
            
        # Indices of initial allocations and shape parameters
        ai = range(nprogs)
        gi = range(nprogs, nprogs*2)
        
        # Values of allocpm at the indcies
        av = [allocpm[j] for j in ai]
        gv = [allocpm[j] for j in gi]
    
        # Define the two parameters
        intalloc = transpose(tile(av, (npts, 1))) # Initial allocation
        shapepar = transpose(tile(gv, (npts, 1))) # Shape parameters
            
        # Calulate shape and scale up to initial allocation
        timealloc = exp(power(-tvec, 2) * shapepar) * intalloc
            
        # Ensure that we have no negative entries - we shouldn't here though
        if (timealloc < 0).any(): maximum(timealloc, 0)
            
        # Normalise spending across all time points s.t: the sum equals totalspend
        timealloc /= tile(timealloc.sum(axis=0) / float(totalspend), (nprogs, 1))
            
        # Sanity check for normalisation of each time point
        if (absolute(timealloc.sum(axis=0) - totalspend) > 1).any():
            raise Exception('Normalisation issue')
        
        # Output the time-varying allocation
        allocation = timealloc
        
    elif ntimepm in (3, 4): # Three and four parameter curves - logistic (fixed or variable inflection)
            
        # Indices of initial allocations, growth rates and saturations
        ai = range(nprogs)
        gi = range(nprogs,   nprogs*2)
        si = range(nprogs*2, nprogs*3)
        
        # Values of allocpm at the indcies
        av = [allocpm[j] for j in ai]
        gv = [allocpm[j] for j in gi]
        sv = [allocpm[j] for j in si]
        
        # Define the first three parameters
        intercept  = transpose(tile(av, (npts, 1))) # Intercept
        growthrate = transpose(tile(gv, (npts, 1))) # Growth rate
        saturation = transpose(tile(sv, (npts, 1))) # Saturation
        
        # For three parameter case, set inflection point in the middle
        if ntimepm == 3: inflection = ones((nprogs, npts)) * 0.5
        
        else:
       
            # In four parameter case use input
            ii = range(nprogs*3, nprogs*4)
            iv = [allocpm[j] for j in ii]
        
            # Extend to matrix as with other variables
            inflection = transpose(tile(iv, (npts, 1)))
            
        # Calulate shape and scale up to initial allocation
        timealloc = (saturation - intercept) / (1 + exp(power(-growthrate, tvec - inflection))) + intercept

        # Ensure that we have no negative entries - we shouldn't here though
        if (timealloc < 0).any(): maximum(timealloc, 0)
        
        # Normalise spending across all time points s.t: the sum equals totalspend
        timealloc /= tile(timealloc.sum(axis=0) / float(totalspend), (nprogs, 1))
        
        # Sanity check for normalisation of each time point
        if (absolute(timealloc.sum(axis=0) - totalspend) > 1).any():
            raise Exception('Normalisation issue')
        
        # Output the time-varying allocation
        allocation = timealloc
       
    # Throw an error if any other inputs are gievn
    else: raise Exception('Algorithm can only handle 2, 3 or 4 parameter time-varying curves')
    
    # Use funding limits
    if fundingchanges is not None:
        newallocation = allocation # Copy
        for t in xrange(1,npts):
            for p in xrange(nprogs):
                if newallocation[p,t]<fundingchanges['total']['dec'][p]: # Too low: make bigger up to the limit
                    newallocation[p,t] = fundingchanges['total']['dec'][p]
                if newallocation[p,t]>fundingchanges['total']['inc'][p]: # Too high: make smaller down to the limit
                    newallocation[p,t] = fundingchanges['total']['inc'][p]
            newallocation[:,t] *= sum(allocation[:,t]) / sum(newallocation[:,t]) # Normalize
    

    # Output full allocation over time
    return allocation

# alloc to budget: multiyear
def multiyear(allocpm, years=[], totalspends=[], nprogs=None, tvec=None):

    """
    Determines allocation values over time for a set budget in each year.
        
    Version: 2015jan30 by cliffk
    """
    
    # Import stuff
    from numpy import zeros, arange, array, tile
    from utils import findinds
    
    nyears = len(years)
    npts = len(tvec)
    
    # Sanity check for the values of ntimepm, nprogs and len(allocpm)
    if len(allocpm) / nyears != nprogs:
        raise Exception('Invalid number of parameters to define allocations over years (%i parameters, %i years, %i programs)' % (len(allocpm), len(years), nprogs))

    allocation = zeros((nprogs,npts)) # Define allocation
    proginds = arange(nprogs)
    yearindex = 0 # Index of year to use
    
    # Loop over years, finding indices
    changes = [0,npts]
    for y in xrange(nyears):
        changes.insert(-1,findinds(tvec>=years[y])[0])
    
    for y in xrange(nyears+1):
        thisalloc = array(allocpm)[proginds+yearindex*nprogs]
        thisalloc *= totalspends[max(0,y-1)] / float(sum(thisalloc))
        allocation[:,changes[y]:changes[y+1]] = tile(thisalloc, (changes[y+1]-changes[y],1)).transpose()  # Assign totals and normalize
        
    return allocation # Output full allocation over time