from optima import isnumber, checktype, promotetoarray, dcp
from numpy import linspace, array, diff, argsort
pchipeps = 1e-8

def pchip(x=None, y=None, xnew=None, deriv = False, method=None, smooth=None, smoothness=None, monotonic=True):
    """
    This module implements the monotonic Piecewise Cubic Hermite Interpolating Polynomial (PCHIP).
    Slopes are constrained via the Fritsch-Carlson method.
    More details: https://en.wikipedia.org/wiki/Monotone_cubic_interpolation
    Script written by Chris Michalski 2009aug18 used as a basis.
    
    Version: 2017mar02
    """
    
    xorder = argsort(x)
    x = dcp(array(x)[xorder])
    y = dcp(array(y)[xorder])
    
    if smooth:
        x,y = smoothingfunc(x=x,y=y, smooth=smooth, monotonic=monotonic)
    
    if not checktype(xnew, 'arraylike'):
        xnew = promotetoarray(xnew)
    xnew = dcp(sorted(xnew))
    
    if method is None or method=='pchip': # WARNING, need to rename this function something else...
        m = pchip_slopes(x, y) # Compute slopes used by piecewise cubic Hermite interpolator.
        ynew = pchip_eval(x, y, m, xnew, deriv) # Use these slopes (along with the Hermite basis function) to interpolate.
    
    elif method=='smoothinterp':
        from utils import smoothinterp
        ynew = smoothinterp(xnew, x, y, smoothness=smoothness, keepends=False)
        if deriv:
              if len(xnew)==1:
                  print('WARNING, length 1 smooth interpolation derivative not implemented')
                  ynew = [0.0] # WARNING, temp
              else:
                  ynew = (diff(ynew)/diff(xnew)).tolist() # Calculate derivative explicitly
                  ynew.append(ynew[-1]) # Duplicate the last element so the right length
    else:
        raise Exception('Interpolation method "%s" not understood' % method)
    
    if checktype(y, 'array'): ynew = array(ynew) # Try to preserve original type
    
    return ynew
    

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
    
    return array(m)


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

def plotpchip(x, y, deriv=False, returnplot=False, initbudget=None, optbudget=None, subsample=50):

    from pylab import figure, plot, show
    
    xorder = argsort(x)
    x = dcp(array(x)[xorder])
    y = dcp(array(y)[xorder])

    # Process inputs
    if isnumber(initbudget): initbudget = [initbudget] # Plotting expects this to be a list
    if isnumber(optbudget): optbudget = [optbudget] # Plotting expects this to be a list
    
    xstart = x[0]
    xend = x[-1]
    if xend > 1e15: xend = x[-2]    # This handles any artificially big value
    if not initbudget == None:
        xstart = min(xstart,initbudget[0])
        xend = max(xend,initbudget[-1])
    if not optbudget == None:
        xstart = min(xstart,optbudget[0])
        xend = max(xend,optbudget[-1])
    
    # Make a new x-axis by subsampling
    xnew = []
    for i in range(len(x)-1):
        tmp = linspace(x[i],x[i+1],subsample).tolist()
        tmp.pop(-1)
        xnew.extend(tmp)
    xnew = array(xnew)
    
    fig = figure(facecolor=(1,1,1))
    ax = fig.add_subplot(111)
    plot(xnew, pchip(x,y,xnew,deriv), linewidth=2)
    xs = [a+pchipeps for a in x]    # Shift the original points slightly when plotting them, otherwise derivatives become zero-like.
    plot(xs, pchip(x,y,xs,deriv), 'k+', markeredgewidth=2, markersize=20, label='Budget-objective curve')
    if not initbudget == None:
        plot(initbudget, pchip(x,y,initbudget,deriv), 'gs', label='Initial')
    if not optbudget == None:
        plot(optbudget, pchip(x,y,optbudget,deriv), 'ro', label='Optimized')
    ax.legend(loc='best')
    if returnplot:
        return ax
    else:
        show()
    
    return None


def smoothingfunc(x=None, y=None, npts=10, smooth=10, monotonic=True):
    '''
    pchip can introduce irregularities, so this smooths them out.
    
    Inputs:
        x = the x values to smooth
        y = the y values to smooth
        npts = the number of times to replicate each point
        smooth = the number of times to apply the smoothing kernel
        monotonic = whether or not to enforce monotonicity in the derivative
    
    Returns new values of x and y as a tuple.
    
    Version: 2017mar02 
    '''
    
    print('WARNING, has strange behavior sometimes still :(')
    
    problemcase = '''
    from pylab import *; from optima import *

    x = array([0.0, 3840693.0, 2304416.0, 1152208.0, 384069.0, 11522078.0, 23044156.0, 38406927.0, 10000000000.0])
    y = array([13290.0, 3950.0, 6211.0, 9145.0, 11707.0, 3064.0, 3018.0, 2990.0, 1970.0])
    
    inds = argsort(x)
    x = x[inds]
    y = y[inds]
    
    usederiv = 1
    
    xnew = []
    for i in range(len(x)-1):
        tmp = linspace(x[i],x[i+1],10).tolist()
        tmp.pop(-1)
        xnew.extend(tmp)
    
    ynew = pchip(x, y, xnew, smooth=0, deriv=usederiv)
    ynew2 = pchip(x, y, xnew, smooth=10, deriv=usederiv)
     
    scatter(xnew, ynew)
    scatter(xnew, ynew2, c=(1,0.4,0))
    if not usederiv: scatter(x,y,c=(0,0.8,0))
    '''

    # Imports
    from pylab import concatenate, ones, array, convolve, diff, argsort, linspace, cumsum, clip, minimum, maximum, sign
    from optima import dcp
    
    # Set parameters
    repeats = npts*smooth # Number of times to apply smoothing
    npad = npts # Size of buffer on each end
    kernel = array([0.25, 0.5, 0.25]) # Kernel to convolve with on each step
    
    # Ensure it's in the correct order and calculate derivative
    order = argsort(x)
    X = array(x)[order]
    Y = array(y)[order]
    derivs = diff(Y)/diff(X)
    
    # Calculate the new x axis, since now npts times as many points as originally
    newx = []
    for z in range(len(X)-1):
        if z<len(X)-2: newx.extend((linspace(X[z], X[z+1], npts+1))[:-1].tolist())
        else:          newx.extend((linspace(X[z], X[z+1], npts+1)).tolist())
    newx = array(newx, dtype=float) # Convert to array -- for plotting y
    
    # Make original derivative (y0 = original, y1 = 1st derivative, y2 = 2nd derivative)
    y1 = []
    for der in derivs:
        y1.extend((der*ones(npts)).tolist())
    y1 = array(y1, dtype=float)
    y1pad = concatenate([ones(npad)*y1[0], y1, ones(npad)*y1[-1]]) # Pad the ends
    
    # Set up the original for comparison
    y1o = dcp(y1) # Original derivative
    y0o = concatenate([[0.], cumsum(y1o*diff(newx))]) # Original function value
    y0o += Y[0] # Adjust for constant of integration
    
    # Convolve the derivative with the kernel
    for r in range(repeats):
        y1pad = convolve(y1pad, kernel, mode='same') # Do the convolution
        for d,der in enumerate(derivs):
            start = d*npts
            end   = (d+1)*npts
            nbstart = start+npad
            nbend   = end+npad
            if monotonic:
                if der>=0:  
                    y1pad[nbstart:nbend] = maximum(y1pad[nbstart:nbend], 0)
                elif der<0: 
                    y1pad[nbstart:nbend] = minimum(y1pad[nbstart:nbend], 0)
                else:       raise Exception('Derivative is neither more or less than zero')
                if d>0 and d<len(derivs)-1 and sign(derivs[d]-derivs[d-1])!=-sign(derivs[d+1]-derivs[d]): # Enforce monotonicity for points in the middle
                    lower = min(derivs[d-1], derivs[d+1])
                    upper = max(derivs[d-1], derivs[d+1])
                    y1pad[nbstart:nbend] = clip(y1pad[nbstart:nbend], lower, upper)
            y1osum = sum(y1o[start:end]) # Calculate the desired sum
            y1sum = sum(y1pad[nbstart:nbend]) # Calculate the actual sum
            y1pad[nbstart:nbend] = y1pad[nbstart:nbend] + (y1osum-y1sum)/npts # Adjust actual to match desired -- if sum(y1) is right, then y0 will be right too
        y1pad[:npad] = y1pad[npad] # Reset the initial pad
        y1pad[-npad:] = y1pad[-npad]  # Reset the final pad
        y1 = y1pad[npad:-npad] # Trim the buffer
        
        # Calculate integral and derivative (used for plotting only)
        y0 = concatenate([[0.], cumsum(y1*diff(newx))]) # Original function value
        y0 += Y[0] # Adjust for constant of integration
    
    newy = y0
    return newx,newy