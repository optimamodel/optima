def truncnorm(a, b, loc=0, scale=1, size=1):
    """
    Super, SUPER kludgy implementation of truncnorm(). 
        
    Inputs:
        a, b : array_like
            shape parameters
        loc : array_like, optional
            location parameter (default=0)
        scale : array_like, optional
            scale parameter (default=1)
        size : int or tuple of ints, optional
            defining number of random variates (default=1)    
        
    Code for testing:
        from scipy import stats
        from truncnorm import truncnorm
        from matplotlib.pylab import subplot, hist
        from time import time
        
        # Parameters
        muz = 0.3
        stdevz = 0.1
        
        # The two methods
        t1 = time()
        zerosample1 = stats.truncnorm.rvs((0 - muz) / stdevz, (1 - muz) / stdevz, loc=muz, scale=stdevz, size = 1000)
        t2 = time()
        zerosample2 = truncnorm((0 - muz) / stdevz, (1 - muz) / stdevz, loc=muz, scale=stdevz, size = 1000)
        t3 = time()
        
        print('Time for original: %f s' % (t2-t1))
        print('Time for new: %f s' % (t3-t2))
        print('Ratio: %f' % ((t3-t2)/(t2-t1)))
        
        # Plot
        subplot(2,1,1)
        hist(zerosample1)
        subplot(2,1,2)
        hist(zerosample2)
    
    Version: 2014nov26 by cliffk
    """
    from numpy import zeros, nan, isnan
    from numpy.random import normal
    output = zeros(size)+nan
    maxcount = 1e5 # Limit for how long to try looping before realizing that something is horribly wrong
    maxstdevs = 3
    
    # Swap variables
    if not(a<=b):
        tmp = a
        a = b
        b = tmp
        print('a>b so a and b swapped (a=%f, b=%f)' % (a,b))
    
    # If the two parameters are the same, make all entries that
    if a==b:
        return [a]*size 
    
    # If the distance from the mean is too large, reset the standard deviation
    distfrommean = min(abs(a-loc), abs(b-loc))
    if distfrommean > maxstdevs*scale:
        print('Your scale (%f) is too small for the distance from mean (%f), resetting' % (scale, distfrommean))
        scale = distfrommean/maxstdevs
        
    s = 0
    count = 0
    while s<size:
        while isnan(output[s]) or output[s]<a or output[s]>b: # Haha LOL this is like the suckiest code ever it makes me want to puke in my mouth
            count += 1
            output[s] = normal(loc=loc, scale=scale, size=1)
            if count >= maxcount:
                print('Your parameters suck: a=%f, b=%f, loc=%f, scale=%f, size=%f' % (a, b, loc, scale, size))
                print('Exceeded the maximum number of iterations for the truncated normal distribution (%i), entering debugger' % maxcount)
                import pdb; pdb.set_trace()
        s += 1
    
    return output

