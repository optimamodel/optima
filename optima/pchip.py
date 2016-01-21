'''

pychip.py
Michalski
20090818

Piecewise cubic Hermite interpolation (monotonic...) in Python

References:

    Wikipedia:  Monotone cubic interpolation
                Cubic Hermite spline

A cubic Hermite spline is a third degree spline with each polynomial of the spline
in Hermite form.  The Hermite form consists of two control points and two control
tangents for each polynomial.  Each interpolation is performed on one sub-interval
at a time (piece-wise).  A monotone cubic interpolation is a variant of cubic
interpolation that preserves monotonicity of the data to be interpolated (in other
words, it controls overshoot).  Monotonicity is preserved by linear interpolation
but not by cubic interpolation.

Use:

There are two separate calls, the first call, pchip_slopes(),  computes the slopes that
the interpolator needs.  If there are a large number of points to compute,
it is more efficient to compute the slopes once, rather than for  every point
being evaluated.  The second call, pchip_eval(), takes the slopes computed by
pchip_slopes() along with X, Y, and a vector of desired "xnew"s and computes a vector
of "ynew"s.  If only a handful of points is needed, pchip() is a  third function
which combines a call to pchip_slopes() followed by pchip_eval().

'''
import warnings
import numpy as np
import matplotlib.pyplot as plt
from numpy import linspace
from copy import deepcopy as dcp
#from interpolate import slopes, stineman_interp

#=========================================================
def pchip(x, y, xnew, deriv = False):
    
    xs = [a for a,b in sorted(zip(x,y))]
    ys = [b for a,b in sorted(zip(x,y))]
    x = dcp(xs)
    y = dcp(ys)
    xnew = dcp(sorted(xnew))
    
    print x
    print y

    # Compute slopes used by piecewise cubic Hermite interpolator.
    m = pchip_slopes(x, y)
    
    # Use these slopes (along with the Hermite basis function) to interpolate.
    ynew = pchip_eval(x, y, m, xnew, deriv)
    
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
    
    print secants
    print m
    return np.array(m)

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

        print('%f %f' % (xc,x[c]))        
        
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

def plotpchip(x, y, deriv = False, returnplot = False):
    
    xnew = linspace(x[0],x[-1],200)
    
    try:
        xnew = linspace(x[0],x[-1],200)
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        plt.plot(xnew, pchip(x,y,xnew,deriv))
#        plt.plot(x,f(x),'-',label='BOC')
#        plt.xlabel('Allocation Total')            
#        plt.ylabel('Outcome')
        if returnplot:
            return ax
        else:
#            plt.legend(loc='best')
            plt.show()
    except:
        print('Plotting of Budget Objective Curve failed!')
    
    return None