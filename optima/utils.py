##############################################################################
### PRINTING FUNCTIONS
##############################################################################


def printv(string, thisverbose=1, verbose=2, newline=True, indent=True):
    '''
    Optionally print a message and automatically indent. The idea is that
    a global or shared "verbose" variable is defined, which is passed to
    subfunctions, determining how much detail to print out.

    The general idea is that verbose is an integer from 0-4 as follows:
        0 = no printout whatsoever
        1 = only essential warnings, e.g. suppressed exceptions
        2 = standard printout
        3 = extra debugging detail (e.g., printout on each iteration)
        4 = everything possible (e.g., printout on each timestep)
    
    Thus a very important statement might be e.g.
        printv('WARNING, everything is wrong', 1, verbose)

    whereas a much less important message might be
        printv('This is timestep %i' % i, 4, verbose)

    Version: 2016jan30
    '''
    if thisverbose>4 or verbose>4: print('Warning, verbosity should be from 0-4 (this message: %i; current: %i)' % (thisverbose, verbose))
    if verbose>=thisverbose: # Only print if sufficiently verbose
        indents = '  '*thisverbose*bool(indent) # Create automatic indenting
        if newline: print(indents+str(string)) # Actually print
        else: print(indents+str(string)), # Actually print
    return None


def blank(n=3):
    ''' Tiny function to print n blank lines, 3 by default '''
    print('\n'*n)


def createcollist(oldkeys, title, strlen = 18, ncol = 3):
    ''' Creates a string for a nice columnated list (e.g. to use in __repr__ method) '''
    from numpy import ceil
    nrow = int(ceil(float(len(oldkeys))/ncol))
    newkeys = []
    for x in xrange(nrow):
        newkeys += oldkeys[x::nrow]
    
    attstring = title + ':'
    c = 0    
    for x in newkeys:
        if c%ncol == 0: attstring += '\n  '
        if len(x) > strlen: x = x[:strlen-3] + '...'
        attstring += '%-*s  ' % (strlen,x)
        c += 1
    attstring += '\n'
    return attstring


def objectid(obj):
    ''' Return the object ID as per the default Python __repr__ method '''
    return '<%s.%s at %s>\n' % (obj.__class__.__module__, obj.__class__.__name__, hex(id(obj)))


def objatt(obj, strlen = 18, ncol = 3):
    ''' Return a sorted string of object attributes for the Python __repr__ method '''
    oldkeys = sorted(obj.__dict__.keys())
    return createcollist(oldkeys, 'Attributes', strlen = 18, ncol = 3)


def objmeth(obj, strlen = 18, ncol = 3):
    ''' Return a sorted string of object methods for the Python __repr__ method '''
    oldkeys = sorted([method + '()' for method in dir(obj) if callable(getattr(obj, method)) and not method.startswith('__')])
    return createcollist(oldkeys, 'Methods', strlen = 18, ncol = 3)


def objrepr(obj, showid=True, showmeth=True, showatt=True):
    ''' Return useful printout for the Python __repr__ method '''
    divider = '============================================================\n'
    output = ''
    if showid:
        output += objectid(obj)
        output += divider
    if showmeth:
        output += objmeth(obj)
        output += divider
    if showatt:
        output += objatt(obj)
        output += divider
    return output


def defaultrepr(obj, maxlen=300):
    ''' Prints out the default representation of an object -- all attributes, plust methods and ID '''
    keys = sorted(obj.__dict__.keys()) # Get the attribute keys
    maxkeylen = max([len(key) for key in keys]) # Find the maximum length of the attribute keys
    if maxkeylen<maxlen: maxlen = maxlen - maxkeylen # Shorten the amount of data shown if the keys are long
    formatstr = '%'+ '%i'%maxkeylen + 's' # Assemble the format string for the keys, e.g. '%21s'
    output  = objrepr(obj, showatt=False) # Get the methods
    for key in keys: # Loop over each attribute
        thisattr = str(getattr(obj, key)) # Get the string representation of the attribute
        if len(thisattr)>maxlen: thisattr = thisattr[:maxlen] + ' [...]' # Shorten it
        prefix = formatstr%key + ': ' # The format key
        output += indent(prefix, thisattr)
    output += '============================================================\n'

    return output



def printarr(arr, arrformat='%0.2f  '):
    ''' 
    Print a numpy array nicely.
    
    Example:
        from utils import printarr
        from numpy import random
        printarr(rand(3,7,4))
    
    Version: 2014dec01 by cliffk
    '''
    from numpy import ndim
    if ndim(arr)==1:
        string = ''
        for i in range(len(arr)):
            string += arrformat % arr[i]
        print(string)
    elif ndim(arr)==2:
        for i in range(len(arr)):
            printarr(arr[i], arrformat)
    elif ndim(arr)==3:
        for i in range(len(arr)):
            print('='*len(arr[i][0])*len(arrformat % 1))
            for j in range(len(arr[i])):
                printarr(arr[i][j], arrformat)
    else:
        print(arr) # Give up
    return None
    


def indent(prefix=None, text=None, suffix='\n', n=0, pretty=False, simple=True, width=70, **kwargs):
    '''
    Small wrapper to make textwrap more user friendly.
    
    Arguments:
        prefix = text to begin with (optional)
        text = text to wrap
        suffix = what to put on the end (by default, a newline)
        n = if prefix is not specified, the size of the indent
        prettify = whether to use pprint to format the text
        kwargs = anything to pass to textwrap.fill() (e.g., linewidth)
    
    Examples:
        prefix = 'and then they said:'
        text = 'blah '*100
        print(indent(prefix, text))
        
        print('my fave is: ' + indent(text=rand(100), n=14))
    
    Version: 2017feb20
    '''
    # Imports
    from textwrap import fill
    from pprint import pformat
    
    # Handle no prefix
    if prefix is None: prefix = ' '*n
    
    # Get text in the right format -- i.e. a string
    if pretty: text = pformat(text)
    else:      text = str(text)
    
    # Generate output
    output = fill(text, initial_indent=prefix, subsequent_indent=' '*len(prefix), width=width, **kwargs)+suffix
    
    if n: output = output[n:] # Need to remove the fake prefix
    return output
    




def sigfig(X, sigfigs=5, SI=False):
    '''
    Return a string representation of variable x with sigfigs number of significant figures -- 
    copied from asd.py.
    
    If SI=True, then will return e.g. 32433 as 32.433K
    '''
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
        
        suffix = ''
        formats = [(1e18,'e18'), (1e15,'e15'), (1e12,'t'), (1e9,'b'), (1e6,'m'), (1e3,'k')]
        if SI:
            for val,suff in formats:
                if abs(x)>=val:
                    x = x/val
                    suffix = suff
                    break # Find at most one match
        
        try:
            if x==0:
                output.append('0')
            elif sigfigs is None:
                output.append(str(x)+suffix)
            else:
                magnitude = floor(log10(abs(x)))
                factor = 10**(sigfigs-magnitude-1)
                x = round(x*factor)/float(factor)
                digits = int(abs(magnitude) + max(0, sigfigs - max(0,magnitude) - 1) + 1 + (x<0) + (abs(x)<1)) # one because, one for decimal, one for minus
                decimals = int(max(0,-magnitude+sigfigs-1))
                strformat = '%' + '%i.%i' % (digits, decimals)  + 'f'
                string = strformat % x
                string += suffix
                output.append(string)
        except:
            output.append(str(x))
    if islist:
        return tuple(output)
    else:
        return output[0]








def isiterable(obj):
    '''
    Simply determine whether or not the input is iterable, since it's too hard to remember this otherwise.
    From http://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
    '''
    try:
        iter(obj)
        return True
    except:
        return False
    

def checktype(obj=None, objtype=None, subtype=None, die=False):
    ''' 
    A convenience function for checking instances. If objtype is a type,
    then this function works exactly like isinstance(). But, it can also
    be a string, e.g. 'array'.
    
    If subtype is not None, then checktype will iterate over obj and check
    recursively that each element matches the subtype.
    
    Arguments:
        obj     = the object to check the type of
        objtype = the type to confirm the object belongs to
        subtype = optionally check the subtype if the object is iterable
        die     = whether or not to raise an exception if the object is the wrong type.
    
    Examples:
        checktype(rand(10), 'array', 'number') # Returns true
        checktype(['a','b','c'], 'arraylike') # Returns false
        checktype([{'a':3}], list, dict) # Returns True
    '''
    from numbers import Number
    from numpy import array
    
    # Handle "objtype" input
    if   objtype in ['str','string']:  objinstance = basestring
    elif objtype in ['num', 'number']: objinstance = Number
    elif objtype in ['arr', 'array']:  objinstance = type(array([]))
    elif objtype=='arraylike':         objinstance = (list, tuple, type(array([]))) # Anything suitable as a numerical array
    elif type(objtype)==type:          objinstance = objtype  # Don't need to do anything
    elif objtype is None:              return None # If not supplied, exit
    else:
        errormsg = 'Could not understand what type you want to check: should be either a string or a type, not "%s"' % objtype
        raise Exception(errormsg)
    
    # Do first-round checking
    result = isinstance(obj, objinstance)
    
    # Do second round checking
    if result and objtype=='arraylike': # Special case for handling arrays which may be multi-dimensional
        obj = promotetoarray(obj).flatten() # Flatten all elements
        if subtype is None: subtype = 'number' # This is the default
    if isiterable(obj) and subtype is not None:
        for item in obj:
            result = result and checktype(item, subtype)

    # Decide what to do with the information thus gleaned
    if die: # Either raise an exception or do nothing if die is True
        if not result: # It's not an instance
            errormsg = 'Incorrect type: object is %s, but %s is required' % (type(obj), objtype)
            raise Exception(errormsg)
        else:
            return None # It's fine, do nothing
    else: # Return the result of the comparison
        return result
   
         
def isnumber(obj):
    ''' Simply determine whether or not the input is a number, since it's too hard to remember this otherwise '''
    return checktype(obj, 'number')
    

def promotetoarray(x):
    ''' Small function to ensure consistent format for things that should be arrays '''
    from numpy import ndarray, shape
    if isnumber(x):
        return array([x]) # e.g. 3
    elif isinstance(x, (list, tuple)):
        return array(x) # e.g. [3]
    elif isinstance(x, ndarray): 
        if shape(x):
            return x # e.g. array([3])
        else: 
            return array([x]) # e.g. array(3)
    else: # e.g. 'foo'
        raise Exception("Expecting a number/list/tuple/ndarray; got: %s" % str(x))


def promotetolist(obj=None, objtype=None):
    ''' Make sure object is iterable -- used so functions can handle inputs like 'FSW' or ['FSW', 'MSM'] '''
    if type(obj)!=list:
        obj = [obj] # Listify it
    if objtype is not None:  # Check that the types match -- now that we know it's a list, we can iterate over it
        for item in obj:
            checktype(obj=item, objtype=objtype, die=True)
    if obj is None:
        raise Exception('This is mathematically impossible')
    return obj


def promotetoodict(obj=None):
    ''' Like promotetolist, but for odicts -- WARNING, could be made into a method for odicts '''
    if isinstance(obj, odict):
        return obj # Don't need to do anything
    elif isinstance(obj, dict):
        return odict(obj)
    elif isinstance(obj, list):
        newobj = odict()
        for i,val in enumerate(obj):
            newobj['Key %i'%i] = val
        return newobj
    else:
        return odict({'Key':obj})


def printdata(data, name='Variable', depth=1, maxlen=40, indent='', level=0, showcontents=False):
    '''
    Nicely print a complicated data structure, a la Matlab.
    Arguments:
      data: the data to display
      name: the name of the variable (automatically read except for first one)
      depth: how many levels of recursion to follow
      maxlen: number of characters of data to display (if 0, don't show data)
      indent: where to start the indent (used internally)
    
    Note: "printdata" is aliased to "pd".

    Version: 1.0 (2015aug21)    
    '''
    datatype = type(data)
    def printentry(data):
        from numpy import shape, ndarray
        if datatype==dict: string = ('dict with %i keys' % len(data.keys()))
        elif datatype==list: string = ('list of length %i' % len(data))
        elif datatype==tuple: string = ('tuple of length %i' % len(data))
        elif datatype==ndarray: string = ('array of shape %s' % str(shape(data)))
        elif datatype.__name__=='module': string = ('module with %i components' % len(dir(data)))
        elif datatype.__name__=='class': string = ('class with %i components' % len(dir(data)))
        else: string = datatype.__name__
        if showcontents and maxlen>0:
            datastring = ' | '+str(data)
            if len(datastring)>maxlen: datastring = datastring[:maxlen] + ' <etc> ' + datastring[-maxlen:]
        else: datastring=''
        return string+datastring
    
    string = printentry(data).replace('\n',' \ ') # Remove newlines
    print(level*'..' + indent + name + ' | ' + string)


    if depth>0:
        level += 1
        if type(data)==dict:
            keys = data.keys()
            maxkeylen = max([len(key) for key in keys])
            for key in keys:
                thisindent = ' '*(maxkeylen-len(key))
                printdata(data[key], name=key, depth=depth-1, indent=indent+thisindent, level=level)
        elif type(data) in [list, tuple]:
            for i in range(len(data)):
                printdata(data[i], name='[%i]'%i, depth=depth-1, indent=indent, level=level)
        elif type(data).__name__ in ['module', 'class']:
            keys = dir(data)
            maxkeylen = max([len(key) for key in keys])
            for key in keys:
                if key[0]!='_': # Skip these
                    thisindent = ' '*(maxkeylen-len(key))
                    printdata(getattr(data,key), name=key, depth=depth-1, indent=indent+thisindent, level=level)
        print('\n')
    return None
pd = printdata # Alias to make it easier to use












##############################################################################
### MATHEMATICAL FUNCTIONS
##############################################################################


def quantile(data, quantiles=[0.5, 0.25, 0.75]):
    '''
    Custom function for calculating quantiles most efficiently for a given dataset.
        data = a list of arrays, or an array where he first dimension is to be sorted
        quantiles = a list of floats >=0 and <=1
    
    Version: 2014nov23
    '''
    from numpy import array
    nsamples = len(data) # Number of samples in the dataset
    indices = (array(quantiles)*(nsamples-1)).round().astype(int) # Calculate the indices to pull out
    output = array(data)
    output.sort(axis=0) # Do the actual sorting along the 
    output = output[indices] # Trim down to the desired quantiles
    
    return output



def sanitize(data=None, returninds=False):
        '''
        Sanitize input to remove NaNs. Warning, does not work on multidimensional data!!
        
        Example:
            sanitized,inds = sanitize(array([3,4,nan,8,2,nan,nan,nan,8]), returninds=True)
        '''
        from numpy import array, isnan, nonzero
        try:
            data = array(data,dtype=float) # Make sure it's an array of float type
            sanitized = data[~isnan(data)]
        except:
            raise Exception('Sanitization failed on array:\n %s' % data)
        if len(sanitized)==0:
            sanitized = 0.0
            print('                WARNING, no data entered for this parameter, assuming 0')

        if returninds: 
            inds = nonzero(~isnan(data))[0] # WARNING, nonzero returns tuple :(
            return sanitized, inds
        else:          return sanitized



def getvaliddata(data=None, filterdata=None, defaultind=0):
    '''
    Return the years that are valid based on the validity of the input data.
    
    Example:
        getvaliddata(array([3,5,8,13]), array([2000, nan, nan, 2004])) # Returns array([3,13])
    '''
    from numpy import array, isnan
    data = array(data)
    if filterdata is None: filterdata = data # So it can work on a single input -- more or less replicates sanitize() then
    filterdata = array(filterdata)
    if filterdata.dtype=='bool': validindices = filterdata # It's already boolean, so leave it as is
    else:                        validindices = ~isnan(filterdata) # Else, assume it's nans that need to be removed
    if validindices.any(): # There's at least one data point entered
        if len(data)==len(validindices): # They're the same length: use for logical indexing
            validdata = array(array(data)[validindices]) # Store each year
        elif len(validindices)==1: # They're different lengths and it has length 1: it's an assumption
            validdata = array([array(data)[defaultind]]) # Use the default index; usually either 0 (start) or -1 (end)
        else:
            raise Exception('Array sizes are mismatched: %i vs. %i' % (len(data), len(validindices)))    
    else: 
        validdata = array([]) # No valid data, return an empty array
    return validdata



def findinds(val1, val2=None, eps=1e-6):
    '''
    Little function to find matches even if two things aren't eactly equal (eg. 
    due to floats vs. ints). If one argument, find nonzero values. With two arguments,
    check for equality using eps. Returns a tuple of arrays if val1 is multidimensional,
    else returns an array.
    
    Examples:
        findinds(rand(10)<0.5) # e.g. array([2, 4, 5, 9])
        findinds([2,3,6,3], 6) # e.g. array([2])
    
    Version: 2016jun06 by cliffk
    '''
    from numpy import nonzero, array, ndim
    if val2==None: # Check for equality
        output = nonzero(val1) # If not, just check the truth condition
    else:
        if isinstance(val2, basestring):
            output = nonzero(array(val1)==val2)
        else:
            output = nonzero(abs(array(val1)-val2)<eps) # If absolute difference between the two values is less than a certain amount
    if ndim(val1)==1: # Uni-dimensional
        output = output[0] # Return an array rather than a tuple of arrays if one-dimensional
    return output


def findnearest(series=None, value=None):
    '''
    Return the index of the nearest match in series to value
    
    Examples:
        findnearest(rand(10), 0.5) # returns whichever index is closest to 0.5
        findnearest([2,3,6,3], 6) # returns 2
        findnearest([2,3,6,3], 6) # returns 2
        findnearest([0,2,4,6,8,10], [3, 4, 5]) # returns array([1, 2, 2])
    
    Version: 2017jan07 by cliffk
    '''
    from numpy import argmin
    series = promotetoarray(series)
    if isnumber(value):
        output = argmin(abs(promotetoarray(series)-value))
    else:
        output = []
        for val in value: output.append(findnearest(series, val))
        output = promotetoarray(output)
    return output
    
    
def dataindex(dataarray, index):        
    ''' Take an array of data and return either the first or last (or some other) non-NaN entry. '''
    from numpy import zeros, shape
    
    nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1).
    output = zeros(nrows)       # Create structure
    for r in range(nrows): 
        output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
    
    return output


def smoothinterp(newx=None, origx=None, origy=None, smoothness=None, growth=None, strictnans=False):
    '''
    Smoothly interpolate over values and keep end points. Same format as numpy.interp.
    
    Example:
        from utils import smoothinterp
        origy = array([0,0.1,0.3,0.8,0.7,0.9,0.95,1])
        origx = linspace(0,1,len(origy))
        newx = linspace(0,1,5*len(origy))
        newy = smoothinterp(newx, origx, origy, smoothness=5)
        plot(newx,newy)
        hold(True)
        scatter(origx,origy)
    
    Version: 2016nov02 by cliffk
    '''
    from numpy import array, interp, convolve, linspace, concatenate, ones, exp, isnan, argsort, ceil
    
    # Ensure arrays and remove NaNs
    if isnumber(newx): newx = [newx] # Make sure it has dimension
    if isnumber(origx): origx = [origx] # Make sure it has dimension
    if isnumber(origy): origy = [origy] # Make sure it has dimension
    newx = array(newx)
    origx = array(origx)
    origy = array(origy)
    
    # If only a single element, just return it, without checking everything else
    if len(origy)==1: 
        newy = zeros(newx.shape)+origy[0]
        return newy
    
    if not(newx.shape): raise Exception('To interpolate, must have at least one new x value to interpolate to')
    if not(origx.shape): raise Exception('To interpolate, must have at least one original x value to interpolate to')
    if not(origy.shape): raise Exception('To interpolate, must have at least one original y value to interpolate to')
    if not(origx.shape==origy.shape): 
        errormsg = 'To interpolate, original x and y vectors must be same length (x=%i, y=%i)' % (len(origx), len(origy))
        raise Exception(errormsg)
    
    if strictnans:
        origy = origy[~isnan(origy)] 
        origx = origx[~isnan(origy)]

    # Calculate smoothness: this is consistent smoothing regardless of the size of the arrays
    if smoothness is None: smoothness = ceil(len(newx)/len(origx))
    smoothness = int(smoothness) # Make sure it's an appropriate number
    
    # Make sure it's in the correct order
    correctorder = argsort(origx)
    origx = origx[correctorder]
    origy = origy[correctorder]
    newx = newx[argsort(newx)] # And sort newx just in case
    
    # Smooth
    kernel = exp(-linspace(-2,2,2*smoothness+1)**2)
    kernel /= kernel.sum()
    newy = interp(newx, origx, origy) # Use interpolation
    validinds = findinds(~isnan(newy)) # Remove nans since these don't exactly smooth well
    if len(validinds): # No point doing these steps if no non-nan values
        validy = newy[validinds]
        validy = concatenate([validy[0]*ones(smoothness), validy, validy[-1]*ones(smoothness)])
        validy = convolve(validy, kernel, 'valid') # Smooth it out a bit
        newy[validinds] = validy # Copy back into full vector
    
    # Apply growth if required
    if growth is not None:
        pastindices = findinds(newx<origx[0])
        futureindices = findinds(newx>origx[-1])
        if len(pastindices): # If there are past data points
            firstpoint = pastindices[-1]+1
            newy[pastindices] = newy[firstpoint] * exp((newx[pastindices]-newx[firstpoint])*growth) # Get last 'good' data point and apply inverse growth
        if len(futureindices): # If there are past data points
            lastpoint = futureindices[0]-1
            newy[futureindices] = newy[lastpoint] * exp((newx[futureindices]-newx[lastpoint])*growth) # Get last 'good' data point and apply growth
        
    return newy
    

def perturb(n=1, span=0.5, randseed=None):
    ''' Define an array of numbers uniformly perturbed with a mean of 1. n = number of points; span = width of distribution on either side of 1.'''
    from numpy.random import rand, seed
    if randseed>=0: seed(randseed) # Optionally reset random seed
    output = 1. + 2*span*(rand(n)-0.5)
    return output
    
def scaleratio(inarray,total):
    ''' Multiply a list or array by some factor so that its sum is equal to the total. '''
    from numpy import array
    origtotal = float(sum(inarray))
    ratio = total/origtotal
    outarray = array(inarray)*ratio
    if type(inarray)==list: outarray = outarray.tolist() # Preserve type
    return outarray


def vec2obj(orig=None, newvec=None, inds=None):
    ''' 
    Function to convert an e.g. budget/coverage vector into an e.g. budget/coverage odict ...or anything, really
    
    WARNING: is all the error checking really necessary?
    
    inds can be a list of indexes, or a list of keys, but newvec must be a list, array, or odict.
    
    Version: 2016feb04
    '''
    from copy import deepcopy as dcp
    
    # Validate input
    if orig is None: raise Exception('vec2obj() requires an original object to update')
    if newvec is None: raise Exception('vec2obj() requires a vector as input')
    lenorig = len(orig)
    lennew = len(newvec)
    if lennew!=lenorig and inds is None: raise Exception('vec2obj(): if inds is not supplied, lengths must match (orig=%i, new=%i)' % (lenorig, lennew))
    if inds is not None and max(inds)>=len(orig): 
        raise Exception('vec2obj(): maximum index is greater than the length of the object (%i, %i)' % (max(inds), len(orig)))
    if inds is None: inds = range(lennew)

    # The actual meat of the function
    new = dcp(orig)    
    for i,ind in enumerate(inds):
        new[ind] = newvec[i]
    
    return new




##############################################################################
### NESTED DICTIONARY FUNCTIONS
##############################################################################

'''
Four little functions to get and set data from nested dictionaries. The first two were stolen from:
    http://stackoverflow.com/questions/14692690/access-python-nested-dictionary-items-via-a-list-of-keys

"getnested" will get the value for the given list of keys:
    getnested(foo, ['a','b'])

"setnested" will set the value for the given list of keys:
    setnested(foo, ['a','b'], 3)

"makenested" will recursively update a dictionary with the given list of keys:
    makenested(foo, ['a','b'])

"iternested" will return a list of all the twigs in the current dictionary:
    twigs = iternested(foo)

Example 1:
    from nested import makenested, getnested, setnested
    foo = {}
    makenested(foo, ['a','b'])
    foo['a']['b'] = 3
    print getnested(foo, ['a','b'])    # 3
    setnested(foo, ['a','b'], 7)
    print getnested(foo, ['a','b'])    # 7
    makenested(foo, ['yerevan','parcels'])
    setnested(foo, ['yerevan','parcels'], 'were tasty')
    print foo['yerevan']  # {'parcels': 'were tasty'}

Example 2:
    from nested import makenested, iternested, setnested
    foo = {}
    makenested(foo, ['a','x'])
    makenested(foo, ['a','y'])
    makenested(foo, ['a','z'])
    makenested(foo, ['b','a','x'])
    makenested(foo, ['b','a','y'])
    count = 0
    for twig in iternested(foo):
        count += 1
        setnested(foo, twig, count)   # {'a': {'y': 1, 'x': 2, 'z': 3}, 'b': {'a': {'y': 4, 'x': 5}}}

Version: 2014nov29 by cliffk
'''

def getnested(nesteddict, keylist, safe=False): 
    ''' Get a value from a nested dictionary'''
    from functools import reduce
    output = reduce(lambda d, k: d.get(k) if d else None if safe else d[k], keylist, nesteddict)
    return output

def setnested(nesteddict, keylist, value): 
    ''' Set a value in a nested dictionary '''
    getnested(nesteddict, keylist[:-1])[keylist[-1]] = value
    return None # Modify nesteddict in place

def makenested(nesteddict, keylist,item=None):
    ''' Insert item into nested dictionary, creating keys if required '''
    currentlevel = nesteddict
    for i,key in enumerate(keylist[:-1]):
    	if not(key in currentlevel):
    		currentlevel[key] = {}
    	currentlevel = currentlevel[key]
    currentlevel[keylist[-1]] = item

def iternested(nesteddict,previous = []):
	output = []
	for k in nesteddict.items():
		if isinstance(k[1],dict):
			output += iternested(k[1],previous+[k[0]]) # Need to add these at the first level
		else:
			output.append(previous+[k[0]])
	return output

















##############################################################################
### MISCELLANEOUS FUNCTIONS
##############################################################################


def tic():
    '''
    A little pair of functions to calculate a time difference, sort of like Matlab:
    t = tic()
    toc(t)
    '''
    from time import time
    return time()



def toc(start=0, label='', sigfigs=3):
    '''
    A little pair of functions to calculate a time difference, sort of like Matlab:
    t = tic()
    toc(t)
    '''
    from time import time
    elapsed = time() - start
    if label=='': base = 'Elapsed time: '
    else: base = 'Elapsed time for %s: ' % label
    print(base + '%s s' % sigfig(elapsed, sigfigs=sigfigs))
    return None
    


def percentcomplete(step=None, maxsteps=None, indent=1):
    ''' Display progress '''
    onepercent = max(1,round(maxsteps/100)); # Calculate how big a single step is -- not smaller than 1
    if not step%onepercent: # Does this value lie on a percent
        thispercent = round(step/maxsteps*100) # Calculate what percent it is
        print('%s%i%%\n'% (' '*indent, thispercent)) # Display the output
    return None


def checkmem(origvariable, descend=0, order='n', plot=False, verbose=0):
    '''
    Checks how much memory the variable in question uses by dumping it to file.
    
    Example:
        from utils import checkmem
        checkmem(['spiffy',rand(2483,589)],descend=1)
    '''
    from os import getcwd, remove
    from os.path import getsize
    from cPickle import dump
    from numpy import iterable, argsort
    
    filename = getcwd()+'/checkmem.tmp'
    
    def dumpfile(variable):
        wfid = open(filename,'wb')
        dump(variable, wfid)
        return None
    
    printnames = []
    printbytes = []
    printsizes = []
    varnames = []
    variables = []
    if descend==False or not(iterable(origvariable)):
        varnames = ['']
        variables = [origvariable]
    elif descend==1 and iterable(origvariable):
        if hasattr(origvariable,'keys'):
            for key in origvariable.keys():
                varnames.append(key)
                variables.append(origvariable[key])
        else:
            varnames = range(len(origvariable))
            variables = origvariable
    
    for v,variable in enumerate(variables):
        if verbose: print('Processing variable %i of %i' % (v+1, len(variables)))
        dumpfile(variable)
        filesize = getsize(filename)
        factor = 1
        label = 'B'
        labels = ['KB','MB','GB']
        for i,f in enumerate([3,6,9]):
            if filesize>10**f:
                factor = 10**f
                label = labels[i]
        printnames.append(varnames[v])
        printbytes.append(filesize)
        printsizes.append('%0.3f %s' % (float(filesize/float(factor)), label))
        remove(filename)

    if order=='a' or order=='alpha' or order=='alphabetical':
        inds = argsort(printnames)
    else:
        inds = argsort(printbytes)

    for v in inds:
        print('Variable %s is %s' % (printnames[v], printsizes[v]))

    if plot==True:
        from pylab import pie, array, axes
        axes(aspect=1)
        pie(array(printbytes)[inds], labels=array(printnames)[inds], autopct='%0.2f')

    return None


def getfilelist(folder=None, ext=None):
    ''' A short-hand since glob is annoying '''
    from glob import glob
    import os
    if folder is None: folder = os.getcwd()
    if ext is None: ext = '*'
    filelist = sorted(glob(os.path.join(folder, '*.'+ext)))
    return filelist


def loadbalancer(maxload=None, index=None, interval=None, maxtime=None, label=None, verbose=True):
    ''' A little function to delay execution while CPU load is too high -- a poor man's load balancer '''
    from psutil import cpu_percent
    from time import sleep
    from numpy.random import random
    
    # Set up processes to start asynchronously
    if maxload is None: maxload = 0.5
    if interval is None: interval = 10.0
    if maxtime is None: maxtime = 3600
    if label is None: label = ''
    else: label += ': '
    if index is None:  pause = random()*interval
    else:              pause = index*interval
    if maxload>1: maxload/100. # If it's >1, assume it was given as a percent
    sleep(pause) # Give it time to asynchronize
    
    # Loop until load is OK
    toohigh = True # Assume too high
    count = 0
    maxcount = maxtime/float(interval)
    while toohigh and count<maxcount:
        count += 1
        currentload = cpu_percent(interval=0.1)/100. # If interval is too small, can give very inaccurate readings
        if currentload>maxload:
            if verbose: print(label+'CPU load too high (%0.2f/%0.2f); process %s queued %i times' % (currentload, maxload, index, count))
            sleep(interval*2*random()) # Sleeps for an average of refresh seconds, but do it randomly so you don't get locking
        else: 
            toohigh = False 
            if verbose: print(label+'CPU load fine (%0.2f/%0.2f), starting process %s after %i tries' % (currentload, maxload, index, count))
    return None
    
    



def runcommand(command, printinput=False, printoutput=False):
   ''' Make it easier to run bash commands. Version: 1.1 Date: 2015sep03 '''
   from subprocess import Popen, PIPE
   if printinput: print(command)
   try: output = Popen(command, shell=True, stdout=PIPE).communicate()[0].decode("utf-8")
   except: output = 'Shell command failed'
   if printoutput: print(output)
   return output



def gitinfo(die=False):
    ''' Try to extract git information based on the file structure '''
    try: # This whole thing could fail, you know!
        from os import path, sep # Path and file separator
        rootdir = path.abspath(path.dirname(__file__)) # e.g. /user/username/optima/optima
        while len(rootdir): # Keep going as long as there's something left to go
            gitdir = rootdir+sep+'.git' # look for the git directory in the current directory
            if path.isdir(gitdir): break # It's found! terminate
            else: rootdir = sep.join(rootdir.split(sep)[:-1]) # Remove the last directory and keep looking
        headstrip = 'ref: ref'+sep+'heads'+sep # Header to strip off...hope this is generalizable!
        with open(gitdir+sep+'HEAD') as f: gitbranch = f.read()[len(headstrip)+1:].strip() # Read git branch name
        with open(gitdir+sep+'refs'+sep+'heads'+sep+gitbranch) as f: gitversion = f.read().strip() # Read git commit
    except: 
        try: # Try using git-python instead -- most users probably won't have
            import git
            repo = git.Repo(path=rootdir, search_parent_directories=True)
            gitbranch = str(repo.active_branch.name) # Just make sure it's a string
            gitversion = str(repo.head.object.hexsha) # Unicode by default
        except: # Failure? Give up
            gitbranch = 'Git branch information not retrivable'
            gitversion = 'Git version information not retrivable'
            if die:
                errormsg = 'Could not extract git info; please check paths or install git-python'
                raise Exception(errormsg)
    return gitbranch, gitversion



def compareversions(version1=None, version2=None):
    ''' Function to compare versions, expecting both arguments to be a string of the format 1.2.3, but numeric works too '''
    if version1 is None or version2 is None: 
        raise Exception('Must supply both versions as strings')
    versions = [version1, version2]
    for i in range(2):
        versions[i] = array(str(versions[i]).split('.'), dtype=float) # Convert to array of numbers
    maxlen = max(len(versions[0]), len(versions[1]))
    versionsarr = zeros((2,maxlen))
    for i in range(2):
        versionsarr[i,:len(versions[i])] = versions[i]
    for j in range(maxlen):
        if versionsarr[0,j]<versionsarr[1,j]: return -1
        if versionsarr[0,j]>versionsarr[1,j]: return 1
    if (versionsarr[0,:]==versionsarr[1,:]).all(): return 0
    else:
        raise Exception('Failed to compare %s and %s' % (version1, version2))






def slacknotification(to=None, message=None, fromuser=None, token=None, verbose=2, die=False):
    ''' 
    Send a Slack notification when something is finished.
    
    Arguments:
        to:
            The Slack channel or user to post to. Note that channels begin with #, while users begin with @.
        message:
            The message to be posted.
        fromuser:
            The pseudo-user the message will appear from.
        token:
            This must be a plain text file containing a single line which is the Slack API URL token.
            Tokens are effectively passwords and must be kept secure. If you need one, contact me.
        verbose:
            How much detail to display.
        die:
            If false, prints warnings. If true, raises exceptions.
    
    Example usage:
        slacknotification('#athena', 'Long process is finished')
        slacknotification(token='/.slackurl', channel='@cliffk', message='Hi, how are you going?')
    
    What's the point? Add this to the end of a very long-running script to notify
    your loved ones that the script has finished.
        
    Version: 2017feb09 by cliffk    
    '''
    
    # Imports
    from requests import post # Simple way of posting data to a URL
    from json import dumps # For sanitizing the message
    from getpass import getuser # In case username is left blank
    
    # Validate input arguments
    printv('Sending Slack message...', 2, verbose)
    if token is None: token = '/.slackurl'
    if to is None: to = '#athena'
    if fromuser is None: fromuser = getuser()+'-bot'
    if message is None: message = 'This is an automated notification: your notifier is notifying you.'
    printv('Channel: %s | User: %s | Message: %s' % (to, fromuser, message), 3, verbose) # Print details of what's being sent
    
    # Try opening token file    
    try:
        with open(token) as f: slackurl = f.read()
    except:
        print('Could not open Slack URL/token file "%s"' % token)
        if die: raise
        else: return None
    
    # Package and post payload
    payload = '{"text": %s, "channel": %s, "username": %s}' % (dumps(message), dumps(to), dumps(fromuser))
    printv('Full payload: %s' % payload, 4, verbose)
    response = post(url=slackurl, data=payload)
    printv(response, 3, verbose) # Optionally print response
    printv('Message sent.', 1, verbose) # We're done
    return None




##############################################################################
### CLASS FUNCTIONS
##############################################################################




def getdate(obj, which='modified', fmt='str'):
        ''' Return either the date created or modified ("which") as either a str or int ("fmt") '''
        from time import mktime
        
        dateformat = '%Y-%b-%d %H:%M:%S'
        
        try:
            if isinstance(obj, basestring): return obj # Return directly if it's a string
            obj.timetuple() # Try something that will only work if it's a date object
            dateobj = obj # Test passed: it's a date object
        except: # It's not a date object
            if which=='created': dateobj = obj.created
            elif which=='modified': dateobj = obj.modified
            elif which=='spreadsheet': dateobj = obj.spreadsheetdate
            else: raise Exception('Getting date for "which=%s" not understood; must be "created", "modified", or "spreadsheet"' % which)
        
        if fmt=='str':
            try:
                return dateobj.strftime(dateformat).encode('ascii', 'ignore') # Return string representation of time
            except UnicodeDecodeError:
                dateformat = '%Y-%m-%d %H:%M:%S'
                return dateobj.strftime(dateformat)
        elif fmt=='int': return mktime(dateobj.timetuple()) # So ugly!! But it works -- return integer representation of time
        else: raise Exception('"fmt=%s" not understood; must be "str" or "int"' % fmt)






##############################################################################
### ORDERED DICTIONARY
##############################################################################


from collections import OrderedDict
from numpy import array
from numbers import Number

class odict(OrderedDict):
    '''
    An ordered dictionary, like the OrderedDict class, but supporting list methods like integer referencing, slicing, and appending.
    Version: 2016sep14 (cliffk)
    '''
    
    def __init__(self, *args, **kwargs):
        ''' See collections.py '''
        if len(args)==1 and args[0] is None: args = [] # Remove a None argument
        OrderedDict.__init__(self, *args, **kwargs) # Standard init

    def __slicekey(self, key, slice_end):
        shift = int(slice_end=='stop')
        if isinstance(key, Number): return key
        elif type(key) is str: return self.index(key)+shift # +1 since otherwise confusing with names (CK)
        elif key is None: return (len(self) if shift else 0)
        else: raise Exception('To use a slice, %s must be either int or str (%s)' % (slice_end, key))


    def __is_odict_iterable(self, v):
        return type(v)==list or type(v)==type(array([]))


    def __getitem__(self, key):
        ''' Allows getitem to support strings, integers, slices, lists, or arrays '''
        if isinstance(key, (str,tuple)):
            try:
                output = OrderedDict.__getitem__(self, key)
                return output
            except Exception as E: # WARNING, should be KeyError, but this can't print newlines!!!
                if len(self.keys()): 
                    errormsg = E.__repr__()+'\n'
                    errormsg += 'odict key "%s" not found; available keys are:\n%s' % (str(key), '\n'.join([str(k) for k in self.keys()]))
                else: errormsg = 'Key "%s" not found since odict is empty'% key
                raise Exception(errormsg)
        elif isinstance(key, Number): # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            return OrderedDict.__getitem__(self,thiskey)
        elif type(key)==slice: # Handle a slice -- complicated
            try:
                startind = self.__slicekey(key.start, 'start')
                stopind = self.__slicekey(key.stop, 'stop')
                if stopind<startind:
                    print('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
                    raise Exception
                slicevals = [self.__getitem__(i) for i in range(startind,stopind)]
                try: return array(slicevals) # Try to convert to an array
                except: return slicevals
            except:
                print('Invalid odict slice... returning empty list...')
                return []
        elif self.__is_odict_iterable(key): # Iterate over items
            listvals = [self.__getitem__(item) for item in key]
            try: return array(listvals)
            except: return listvals
        else: # Handle everything else
            return OrderedDict.__getitem__(self,key)
        
        
    def __setitem__(self, key, value):
        ''' Allows setitem to support strings, integers, slices, lists, or arrays '''
        if isinstance(key, (str,tuple)):
            OrderedDict.__setitem__(self, key, value)
        elif isinstance(key, Number): # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            OrderedDict.__setitem__(self, thiskey, value)
        elif type(key)==slice:
            startind = self.__slicekey(key.start, 'start')
            stopind = self.__slicekey(key.stop, 'stop')
            if stopind<startind:
                errormsg = 'Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind)
                raise Exception(errormsg)
            slicerange = range(startind,stopind)
            enumerator = enumerate(slicerange)
            slicelen = len(slicerange)
            if hasattr(value, '__len__'):
                if len(value)==slicelen:
                    for valind,index in enumerator:
                        self.__setitem__(index, value[valind])  # e.g. odict[:] = arr[:]
                else:
                    errormsg = 'Slice "%s" and values "%s" have different lengths! (%i, %i)' % (slicerange, value, slicelen, len(value))
                    raise Exception(errormsg)
            else: 
                for valind,index in enumerator:
                    self.__setitem__(index, value) # e.g. odict[:] = 4
        elif self.__is_odict_iterable(key) and hasattr(value, '__len__'): # Iterate over items
            if len(key)==len(value):
                for valind,thiskey in enumerate(key): 
                    self.__setitem__(thiskey, value[valind])
            else:
                errormsg = 'Keys "%s" and values "%s" have different lengths! (%i, %i)' % (key, value, len(key), len(value))
                raise Exception(errormsg)
        else:
            OrderedDict.__setitem__(self, key, value)
        return None
    
    
    def pop(self, key, *args, **kwargs):
        ''' Allows pop to support strings, integers, slices, lists, or arrays '''
        if isinstance(key, basestring):
            return OrderedDict.pop(self, key, *args, **kwargs)
        elif isinstance(key, Number): # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            return OrderedDict.pop(self, thiskey, *args, **kwargs)
        elif type(key)==slice: # Handle a slice -- complicated
            try:
                startind = self.__slicekey(key.start, 'start')
                stopind = self.__slicekey(key.stop, 'stop')
                if stopind<startind:
                    print('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
                    raise Exception
                slicevals = [self.pop(i, *args, **kwargs) for i in range(startind,stopind)] # WARNING, not tested
                try: return array(slicevals) # Try to convert to an array
                except: return slicevals
            except:
                print('Invalid odict slice... returning empty list...')
                return []
        elif self.__is_odict_iterable(key): # Iterate over items
            listvals = [self.pop(item, *args, **kwargs) for item in key]
            try: return array(listvals)
            except: return listvals
        else: # Handle string but also everything else
            try:
                return OrderedDict.pop(self, key, *args, **kwargs)
            except: # WARNING, should be KeyError, but this can't print newlines!!!
                if len(self.keys()): 
                    errormsg = 'odict key "%s" not found; available keys are:\n%s' % (str(key), 
                        '\n'.join([str(k) for k in self.keys()]))
                else: errormsg = 'Key "%s" not found since odict is empty'% key
                raise Exception(errormsg)
    
    
    def __repr__(self, maxlen=None, spaces=True, divider=False):
        ''' Print a meaningful representation of the odict '''
         # Maximum length of string to display
        toolong = ' [...]'
        dividerstr = '#############################################################\n'
        if len(self.keys())==0: 
            output = 'odict()'
        else: 
            output = ''
            hasspaces = 0
            for i in range(len(self)):
                if divider and spaces and hasspaces: output += dividerstr
                thiskey = str(self.keys()[i]) # Probably don't need to cast to str, but just to be sure
                thisval = str(self.values()[i].__repr__()) # __repr__() is slightly more accurate
                if not(spaces):                    thisval = thisval.replace('\n','\\n') # Replace line breaks with characters
                if maxlen and len(thisval)>maxlen: thisval = thisval[:maxlen-len(toolong)] + toolong # Trim long entries
                if thisval.find('\n'): hasspaces = True
                output += '#%i: "%s": %s\n' % (i, thiskey, thisval)
        return output
    
    def disp(self, maxlen=55, spaces=False, divider=False):
        ''' Print out flexible representation, short by default'''
        print(self.__repr__(maxlen=maxlen, spaces=spaces, divider=divider))
    
    def _repr_pretty_(self, p, cycle):
        ''' Function to fix __repr__ in IPython'''
        print(self.__repr__())
    
    
    def index(self, value):
        ''' Return the index of a given key '''
        return self.keys().index(value)
    
    def valind(self, value):
        ''' Return the index of a given value '''
        return self.items().index(value)
    
    def append(self, key=None, value=None):
        ''' Support an append method, like a list '''
        needkey = False
        if value is None: # Assume called with a single argument
            value = key
            needkey = True
        if key is None or needkey:
            keyname = 'key'+str(len(self))  # Define the key just to be the current index
        else:
            keyname = key
        self.__setitem__(keyname, value)
        return None
    
    def insert(self, pos=None, key=None, value=None):
        '''
        Stupid, slow function to do insert -- WARNING, should be able to use approach more like rename...
        
        Usage:
            z = odict()
            z['foo'] = 1492
            z.insert(1604)
            z.insert(0, 'ganges', 1444)
            z.insert(2, 'midway', 1234)
        '''
        
        # Handle inputs
        realpos, realkey, realvalue = pos, key, value
        if key is None and value is None: # Assume it's called like odict.insert(666)
            realvalue = pos
            realkey = 'key'+str(len(self))
            realpos = 0
        elif value is None: # Assume it's called like odict.insert('devil', 666)
            realvalue = key
            realkey = pos
            realpos = 0
        if pos is None:
            realpos = 0
        if realpos>len(self):
            errormsg = 'Cannot insert %s at position %i since length of odict is %i ' % (key, pos, len(self))
            raise Exception(errormsg)
        
        # Create a temporary dictionary to hold all of the items after the insertion point
        tmpdict = odict()
        origkeys = self.keys()
        originds = range(len(origkeys))
        if not len(originds) or realpos==len(originds): # It's empty or in the final position, just append
            self.__setitem__(realkey, realvalue)
        else: # Main usage case, it's not empty
            try: insertind = originds.index(realpos) # Figure out which index we're inseting at
            except:
                errormsg = 'Could not insert item at position %i in odict with %i items' % (realpos, len(originds))
                raise Exception(errormsg)
            keystopop = origkeys[insertind:] # Pop these keys until we get far enough back
            for keytopop in keystopop:
                tmpdict.__setitem__(keytopop, self.pop(keytopop))
            self.__setitem__(realkey, realvalue) # Insert the new item at the right location
            for keytopop in keystopop: # Insert popped items back in
                self.__setitem__(keytopop, tmpdict.pop(keytopop))

        return None
        
        
    def rename(self, oldkey, newkey):
        ''' Change a key name -- WARNING, very inefficient! '''
        nkeys = len(self)
        if isinstance(oldkey, Number): 
            index = oldkey
            keystr = self.keys()[index]
        elif isinstance(oldkey, basestring): 
            index = self.keys().index(oldkey)
            keystr = oldkey
        else: raise Exception('Key type not recognized: must be int or str')
        self.__setitem__(newkey, self.pop(keystr))
        if index<nkeys-1:
            for i in range(index+1, nkeys):
                key = self.keys()[index]
                value = self.pop(key)
                self.__setitem__(key, value)
        return None
    
    
    def sort(self, sortby=None, copy=False):
        '''
        Create a sorted version of the odict. Sorts by order of sortby, if provided, otherwise alphabetical.
        If copy is True, then returns a copy (like sorted())
        
        Note: very slow, do not use for serious computations!!
        '''
        if sortby is None: allkeys = sorted(self.keys())
        else:
            if not isiterable(sortby): raise Exception('Please provide a list to determine the sort order.')
            if all(isinstance(x,basestring) for x in sortby): # Going to sort by keys
                if not set(sortby)==set(self.keys()): 
                    errormsg = 'List of keys to sort by must be the same as list of keys in odict.\n You provided the following list of keys to sort by:\n'
                    errormsg += '\n'.join(sortby)
                    errormsg += '\n List of keys in odict is:\n'
                    errormsg += '\n'.join(self.keys())
                    raise Exception(errormsg)
                else: allkeys = sortby
            elif all(isinstance(x,Number) for x in sortby): # Going to sort by numbers
                if not set(sortby)==set(range(len(self))):
                    errormsg = 'List to sort by "%s" is not compatible with length of odict "%i"' % (sortby, len(self))
                    raise Exception(errormsg)
                else: allkeys = [y for (x,y) in sorted(zip(sortby,self.keys()))]
            else: raise Exception('Cannot figure out how to sort by "%s"' % sortby)
        tmpdict = odict()
        if copy:
            for key in allkeys: tmpdict[key] = self[key]
            return tmpdict
        else:
            for key in allkeys: tmpdict.__setitem__(key, self.pop(key))
            for key in allkeys: self.__setitem__(key, tmpdict.pop(key))
            return None
    
    def sorted(self, sortby=None):
        ''' Shortcut for making a copy of the sorted odict '''
        return self.sort(sortby=sortby, copy=True)







##############################################################################
### DATA FRAME CLASS
##############################################################################

# Some of these are repeated to make this frationally more self-contained
from numpy import array, zeros, empty, vstack, hstack, matrix, argsort, argmin # analysis:ignore
from numbers import Number # analysis:ignore

class dataframe(object):
    '''
    A simple data frame, based on simple lists, for simply storing simple data.
    
    Example usage:
        a = dataframe(['x','y'],[[1238,2,3],[0.04,5,6]]) # Create data frame
        print a['x'] # Print out a column
        print a[0] # Print out a row
        print a['x',0] # Print out an element
        a[0] = [5,6]; print a # Set values for a whole row
        a['y'] = [8,5,0]; print a # Set values for a whole column
        a['z'] = [14,14,14]; print a # Add new column
        a.addcol('z', [14,14,14]); print a # Alternate way to add new column
        a.rmcol('z'); print a # Remove a column
        a.pop(1); print a # Remove a row
        a.append([1,2]); print a # Append a new row
        a.insert(1,[9,9]); print a # Insert a new row
        a.sort(); print a # Sort by the first column
        a.sort('y'); print a # Sort by the second column
        a.addrow([1,44]); print a # Replace the previous row and sort
        a.getrow(1) # Return the row starting with value '1'
        a.rmrow(); print a # Remove last row
        a.rmrow(3); print a # Remove the row starting with element '3'
    
    Version: 2016oct31
    '''

    def __init__(self, cols=None, data=None):
        if cols is None: cols = list()
        if data is None: data = zeros((len(cols),0), dtype=object) # Object allows more than just numbers to be stored
        self.cols = cols
        self.data = array(data, dtype=object)
        return None
    
    def __repr__(self, spacing=2):
        ''' spacing = space between columns '''
        if not self.cols: # No keys, give up
            return ''
        
        else: # Go for it
            outputlist = dict()
            outputformats = dict()
            
            # Gather data
            nrows = self.nrows()
            for c,col in enumerate(self.cols):
                outputlist[col] = list()
                maxlen = len(col) # Start with length of column name
                if nrows:
                    for val in self.data[c,:]:
                        output = str(val)
                        maxlen = max(maxlen, len(output))
                        outputlist[col].append(output)
                outputformats[col] = '%'+'%i'%(maxlen+spacing)+'s'
            
            if   nrows<10:   indformat = '%2s' # WARNING, KLUDGY, but easier to do explicitly than to find the general solution!
            elif nrows<100:  indformat = '%3s'
            elif nrows<1000: indformat = '%4s'
            else:            indformat = '%6s'
            
            # Assemble output
            output = indformat % '' # Empty column for index
            for col in self.cols: # Print out header
                output += outputformats[col] % col
            output += '\n'
            
            for ind in range(nrows): # WARNING, KLUDGY
                output += indformat % str(ind)
                for col in self.cols: # Print out data
                    output += outputformats[col] % outputlist[col][ind]
                output += '\n'
            
            return output
    
    def _val2row(self, value=None):
        ''' Convert a list, array, or dictionary to the right format for appending to a dataframe '''
        if isinstance(value, dict):
            output = zeros(self.ncols(), dtype=object)
            for c,col in enumerate(self.cols):
                try: 
                    output[c] = value[col]
                except: 
                    raise Exception('Entry for column %s not found; keys you supplied are: %s' % (col, value.keys()))
            return array(output, dtype=object)
        elif value is None:
            return empty(self.ncols(),dtype=object)
        else: # Not sure what it is, just make it an array
            return array(value, dtype=object)
    
    def _sanitizecol(self, col):
        ''' Take None or a string and return the index of the column '''
        if col is None: output = 0 # If not supplied, assume first column is control
        elif isinstance(col, basestring): output = self.cols.index(col) # Convert to index
        else: output = col
        return output
        
    def __getitem__(self, key):
        if isinstance(key, basestring):
            colindex = self.cols.index(key)
            output = self.data[colindex,:]
        elif isinstance(key, Number):
            rowindex = int(key)
            output = self.data[:,rowindex]
        elif isinstance(key, tuple):
            colindex = self.cols.index(key[0])
            rowindex = int(key[1])
            output = self.data[colindex,rowindex]
        return output
        
    def __setitem__(self, key, value):
        if isinstance(key, basestring):
            if len(value) != self.nrows(): 
                raise Exception('Vector has incorrect length (%i vs. %i)' % (len(value), self.nrows()))
            try:
                colindex = self.cols.index(key)
                self.data[colindex,:] = value
            except:
                self.cols.append(key)
                colindex = self.cols.index(key)
                self.data = vstack((self.data, array(value, dtype=object)))
        elif isinstance(key, Number):
            value = self._val2row(value) # Make sure it's in the correct format
            if len(value) != self.ncols(): 
                raise Exception('Vector has incorrect length (%i vs. %i)' % (len(value), self.ncols()))
            rowindex = int(key)
            self.data[:,rowindex] = value
        elif isinstance(key, tuple):
            colindex = self.cols.index(key[0])
            rowindex = int(key[1])
            self.data[colindex,rowindex] = value
        return None
    
    def pop(self, key, returnval=True):
        ''' Remove a row from the data frame '''
        rowindex = int(key)
        thisrow = self.data[:,rowindex]
        self.data = hstack((self.data[:,:rowindex], self.data[:,rowindex+1:]))
        if returnval: return thisrow
        else:         return None
    
    def append(self, value):
        ''' Add a row to the end of the data frame '''
        value = self._val2row(value) # Make sure it's in the correct format
        self.data = hstack((self.data, array(matrix(value).transpose(), dtype=object)))
        return None
    
    def ncols(self):
        ''' Get the number of columns in the data frame '''
        return len(self.cols)

    def nrows(self):
        ''' Get the number of rows in the data frame '''
        try:    return self.data.shape[1]
        except: return 0 # If it didn't work, probably because it's empty
    
    def addcol(self, key, value):
        ''' Add a new colun to the data frame -- for consistency only '''
        self.__setitem__(key, value)
    
    def rmcol(self, key):
        ''' Remove a column from the data frame '''
        colindex = self.cols.index(key)
        self.cols.pop(colindex) # Remove from list of columns
        self.data = vstack((self.data[:colindex,:], self.data[colindex+1:,:])) # Remove from data
        return None
    
    def addrow(self, value=None, overwrite=True, col=None, reverse=False):
        ''' Like append, but removes duplicates in the first column and resorts '''
        value = self._val2row(value) # Make sure it's in the correct format
        col   = self._sanitizecol(col)
        index = self._rowindex(key=value[col], col=col, die=False) # Return None if not found
        if index is None or not overwrite: self.append(value)
        else: self.data[:,index] = value # If it exists already, just replace it
        self.sort(col=col, reverse=reverse) # Sort
        return None
    
    def _rowindex(self, key=None, col=None, die=False):
        ''' Get the sanitized row index for a given key and column '''
        col = self._sanitizecol(col)
        coldata = self.data[col,:] # Get data for this column
        if key is None: key = coldata[-1] # If not supplied, pick the last element
        try:    index = coldata.tolist().index(key) # Try to find duplicates
        except: 
            if die: raise Exception('Item %s not found; choices are: %s' % (key, coldata))
            else:   return None
        return index
        
    def rmrow(self, key=None, col=None, returnval=False, die=True):
        ''' Like pop, but removes by matching the first column instead of the index '''
        index = self._rowindex(key=key, col=col, die=die)
        if index is not None: self.pop(index)
        return None
    
    def _todict(self, row):
        ''' Return row as a dict rather than as an array '''
        if len(row)!=len(self.cols): 
            errormsg = 'Length mismatch between "%s" and "%s"' % (row, self.cols)
            raise Exception(errormsg)
        rowdict = dict(zip(self.cols, row))
        return rowdict
    
    def getrow(self, key=None, col=None, default=None, closest=False, die=False, asdict=False):
        '''
        Get a row by value.
        
        Arguments:
            key = the value to look for
            col = the column to look for this value in
            default = the value to return if key is not found (overrides die)
            closest = whether or not to return the closest row (overrides default and die)
            die = whether to raise an exception if the value is not found
            asdict = whether to return results as dict rather than list
        
        Example:
            df = dataframe(cols=['year','val'],data=[[2016,2017],[0.3,0.5]])
            df.getrow(2016) # returns array([2016, 0.3], dtype=object)
            df.getrow(2013) # returns None, or exception if die is True
            df.getrow(2013, closest=True) # returns array([2016, 0.3], dtype=object)
            df.getrow(2016, asdict=True) # returns {'year':2016, 'val':0.3}
        '''
        if not closest: # Usual case, get 
            index = self._rowindex(key=key, col=col, die=(die and default is None))
        else:
            col = self._sanitizecol(col)
            coldata = self.data[col,:] # Get data for this column
            index = argmin(abs(coldata-key)) # Find the closest match to the key
        if index is not None:
            thisrow = self.data[:,index]
            if asdict:
                thisrow = self._todict(thisrow)
        else:
            thisrow = default # If not found, return as default
        return thisrow
        
    def insert(self, row=0, value=None):
        ''' Insert a row at the specified location '''
        rowindex = int(row)
        value = self._val2row(value) # Make sure it's in the correct format
        self.data = hstack((self.data[:,:rowindex], array(matrix(value).transpose(), dtype=object), self.data[:,rowindex:]))
        return None
    
    def sort(self, col=None, reverse=False):
        ''' Sort the data frame by the specified column '''
        col = self._sanitizecol(col)
        sortorder = argsort(self.data[col,:])
        if reverse: sortorder = array(list(reversed(sortorder)))
        self.data = self.data[:,sortorder]
        return None
        










##############################################################################
### OTHER CLASSES
##############################################################################


class LinkException(Exception):
        ''' An exception to raise when links are broken -- note, can't define classes inside classes :( '''
        def __init(self, *args, **kwargs):
            Exception.__init__(self, *args, **kwargs)


class Link(object):
    '''
    A class to differentiate between an object and a link to an object. Not very
    useful at the moment, but the idea eventually is that this object would be
    parsed differently from other objects -- most notably, a recursive method
    (such as a pickle) would skip over Link objects, and then would fix them up
    after the other objects had been reinstated.
    
    Version: 2017jan31
    '''
    
    def __init__(self, obj=None):
        ''' Store the reference to the object being referred to '''
        self.obj = obj # Store the object -- or rather a reference to it, if it's mutable
        try:    self.uid = obj.uid # If the object has a UID, store it separately 
        except: self.uid = None # If not, just use None
    
    def __call__(self, obj=None):
        ''' If called with no argument, return the stored object; if called with argument, update object '''
        if obj is None:
            if type(self.obj)==LinkException: # If the link is broken, raise it now
                raise self.obj 
            return self.obj
        else:
            self.__init__(obj)
            return None
    
    def __copy__(self, *args, **kwargs):
        ''' Do NOT automatically copy link objects!! '''
        return Link(LinkException('Link object copied but not yet repaired'))
    
    def __deepcopy__(self, *args, **kwargs):
        ''' Same as copy '''
        return self.__copy__(self, *args, **kwargs)
        
        
