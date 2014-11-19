"""
TRUNCNORM

Super, SUPER kludgy implementation of truncnorm(). Code for testing:
    
from scipy import stats
from truncnorm import truncnorm
from matplotlib.pylab import subplot, hist

# Parameters
muz = 0.3
stdevz = 0.1

# The two methods
zerosample1 = stats.truncnorm.rvs((0 - muz) / stdevz, (1 - muz) / stdevz, loc=muz, scale=stdevz, size = 1000)
zerosample2 = truncnorm((0 - muz) / stdevz, (1 - muz) / stdevz, loc=muz, scale=stdevz, size = 1000)

# Plot
subplot(2,1,1)
hist(zerosample1)
subplot(2,1,2)
hist(zerosample2) # LOL it actually matches
"""

def truncnorm(a, b, loc=0, scale=1, size=1):
    """
    Truncated normal distribution. Hacked together by cliffk.
    
    Version: 2014nov19
    """
    from matplotlib.pylab import zeros, normal, nan, isnan
    output = zeros(size)+nan
    
    s=0
    while s<size:
        while isnan(output[s]) or output[s]<a or output[s]>b: # Haha LOL this is like the suckiest code ever it makes me want to puke in my mouth
            output[s] = normal(loc=loc, scale=scale, size=1)
        s += 1
    
    return output

