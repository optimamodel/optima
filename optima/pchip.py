"""
This module implements the monotonic Piecewise Cubic Hermite Interpolating Polynomial (PCHIP).
Slopes are constrained via the Fritsch-Carlson method.
More details: https://en.wikipedia.org/wiki/Monotone_cubic_interpolation
Script written by Chris Michalski 2009aug18 used as a basis.

Version: 2016jan31
"""

import matplotlib.pyplot as plt
from numpy import linspace, array, diff
from copy import deepcopy as dcp
import collections
#from interpolate import slopes, stineman_interp

pchipeps = 1e-8

#=========================================================
def pchip(x, y, xnew, deriv = False, method='smoothinterp'):
    
    xs = [a for a,b in sorted(zip(x,y))]
    ys = [b for a,b in sorted(zip(x,y))]
    x = dcp(xs)
    y = dcp(ys)
    
    if not isinstance(xnew,collections.Sequence):       # Is this reliable enough...?
        Exception('Error: Values to interpolate for with PCHIP have not been given in sequence form (e.g. list or array)!')
    xnew = dcp(sorted(xnew))
    
#    print x
#    print y
    
    if method=='pchip': # WARNING, need to rename this function something else...
        m = pchip_slopes(x, y) # Compute slopes used by piecewise cubic Hermite interpolator.
        ynew = pchip_eval(x, y, m, xnew, deriv) # Use these slopes (along with the Hermite basis function) to interpolate.
    
    elif method=='smoothinterp':
        from utils import smoothinterp
        ynew = smoothinterp(xnew, x, y)
        if deriv:
              if len(xnew)==1:
                  print('WARNING, length 1 smooth interpolation derivative not implemented')
                  ynew = [0.0] # WARNING, temp
              else:
        		    ynew = (diff(ynew)/diff(xnew)).tolist() # Calculate derivative explicitly
        		    ynew.append(ynew[-1]) # Duplicate the last element so the right length
    else:
        raise Exception('Interpolation method "%s" not understood' % method)
    
    
    
    if type(y)==type(array([])): ynew = array(ynew) # Try to preserve original type
    
    return ynew
    
#=========================================================
def pchip_slopes(x, y, monotone=True):

    if not len(x) == len(y): raise Exception('Error: Interpolation failure due to unequal x and y points!')

    m = []
    secants = []
    
    if not len(x) > 1:
        raise Exception('Error: Interpolation failure due to the existence of only one point!')
    else:
        for c in xrange(len(x)-1):
            secants.append((y[c+1]-y[c])/(x[c+1]-x[c]))
        for c in xrange(len(x)):
            if c == 0: deriv = secants[c]
            elif c == len(x)-1: deriv = secants[c-1]
            elif secants[c]*secants[c-1] <= 0: deriv = 0
            else: deriv = (secants[c]+secants[c-1])/2
            
            if c < len(x)-1 and abs(deriv) > 3*abs(secants[c]): deriv = 3*secants[c]
            if c > 0 and abs(deriv) > 3*abs(secants[c-1]): deriv = 3*secants[c-1]
    
            m.append(deriv)
    
#    print secants
#    print m
    return array(m)

#=========================================================
def pchip_eval(x, y, m, xvec, deriv = False):
    '''
     Evaluate the piecewise cubic Hermite interpolant with  monoticity preserved
    
        x = array containing the x-data
        y = array containing the y-data
        m = slopes at each (x,y) point [computed to preserve  monotonicity]
        xnew = new "x" value where the interpolation is desired
    
        x must be sorted low to high... (no repeats)
        y can have repeated values
    
     This works with either a scalar or vector of "xvec"
    '''
    
    yvec = []    
    
    c = 0
    for xc in xvec:
        while xc < x[-1] and xc >= x[c+1]:
            c += 1
        if xc >= x[-1]: c = -2

#        print('%f %f' % (xc,x[c]))        
        
        # Create the Hermite coefficients
        h = x[c+1] - x[c]
        t = (xc - x[c]) / h
        
        # Hermite basis functions
        if not deriv:
            h00 = (2 * t**3) - (3 * t**2) + 1
            h10 =      t**3  - (2 * t**2) + t
            h01 = (-2* t**3) + (3 * t**2)
            h11 =      t**3  -      t**2
        else:
            h00 = ((6 * t**2) - (6 * t**1))/h
            h10 = ((3 * t**2) - (4 * t**1) + 1)/h
            h01 = ((-6* t**2) + (6 * t**1))/h
            h11 = ((3 * t**2)  - (2 * t**1))/h
        
        # Compute the interpolated value of "y"
        ynew = h00*y[c] + h10*h*m[c] + h01*y[c+1] + h11*h*m[c+1]
        yvec.append(ynew)
    
    return yvec

##=========================================================

def plotpchip(x, y, deriv = False, returnplot = False, initbudget = None, optbudget = None):

    xnew = linspace(x[0],x[-1],200)

    # Process inputs
    if isinstance(initbudget, (int, float)): initbudget = [initbudget] # Plotting expects this to be a list
    if isinstance(optbudget, (int, float)): optbudget = [optbudget] # Plotting expects this to be a list
    
#    try:
    xstart = x[0]
    xend = x[-1]
    if not initbudget == None:
        xstart = min(xstart,initbudget[0])
        xend = max(xend,initbudget[-1])
    if not optbudget == None:
        xstart = min(xstart,optbudget[0])
        xend = max(xend,optbudget[-1])
    xnew = linspace(xstart,xend,200)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
#    print(xnew)
#    print(pchip(x,y,xnew,deriv))
#    print(optbudget)
#    print(pchip(x,y,optbudget,deriv))
    plt.plot(xnew, pchip(x,y,xnew,deriv))
    xs = [a+pchipeps for a in x]    # Shift the original points slightly when plotting them, otherwise derivatives become zero-like.
    plt.plot(xs, pchip(x,y,xs,deriv), 'k+', markeredgewidth=1.5, label='BOC Data')
#        print(x)
#        print(pchip(x,y,x,deriv))
    if not initbudget == None:
        plt.plot(initbudget, pchip(x,y,initbudget,deriv), 'gs', label='Init. Est.')
    if not optbudget == None:
        plt.plot(optbudget, pchip(x,y,optbudget,deriv), 'ro', label='Opt. Est.')
    ax.legend(loc='best')
    if returnplot:
        return ax
    else:
        plt.show()
#    except:
#        print('Plotting of PCHIP-interpolated data failed!')
    
    return None