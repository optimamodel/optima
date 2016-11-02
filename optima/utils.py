##############################################################################
## PRINTING FUNCTIONS
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
    
    Thus you a very important statement might be e.g.
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


def defaultrepr(obj, maxlen=55):
    ''' Prints out the default representation of an object -- all attributes, plust methods and ID '''
    keys = sorted(obj.__dict__.keys())
    maxkeylen = max([len(key) for key in keys])
    if maxkeylen<maxlen: maxlen = maxlen - maxkeylen
    formatstr = '%'+ '%i'%maxkeylen + 's'
    output  = objrepr(obj, showatt=False)
    for key in keys:
        thisattr = str(getattr(obj, key))
        if len(thisattr)>maxlen: thisattr = thisattr[:maxlen] + ' [...]'
        output += formatstr%key + ': ' + thisattr + '\n'
    output += '============================================================\n'

    return output



def printarr(arr, arrformat='%0.2f  '):
    """ 
    Print a numpy array nicely.
    
    Example:
        from utils import printarr
        from numpy import random
        printarr(rand(3,7,4))
    
    Version: 2014dec01 by cliffk
    """
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
    





def sigfig(X, sigfigs=5):
    """ Return a string representation of variable x with sigfigs number of significant figures -- copied from asd.py """
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





def isnumber(x):
    ''' Simply determine whether or not the input is a number, since it's too hard to remember this otherwise '''
    from numbers import Number
    return isinstance(x, Number)


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
        raise OptimaException("Expecting a number/list/tuple/ndarray; got: %s" % str(x))


def printdata(data, name='Variable', depth=1, maxlen=40, indent='', level=0, showcontents=False):
    """
    Nicely print a complicated data structure, a la Matlab.
    Arguments:
      data: the data to display
      name: the name of the variable (automatically read except for first one)
      depth: how many levels of recursion to follow
      maxlen: number of characters of data to display (if 0, don't show data)
      indent: where to start the indent (used internally)
    
    Note: "printdata" is aliased to "pd".

    Version: 1.0 (2015aug21)    
    """
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
## MATHEMATICAL FUNCTIONS
##############################################################################


def quantile(data, quantiles=[0.5, 0.25, 0.75]):
    """
    Custom function for calculating quantiles most efficiently for a given dataset.
        data = a list of arrays, or an array where he first dimension is to be sorted
        quantiles = a list of floats >=0 and <=1
    
    Version: 2014nov23
    """
    from numpy import array
    nsamples = len(data) # Number of samples in the dataset
    indices = (array(quantiles)*(nsamples-1)).round().astype(int) # Calculate the indices to pull out
    output = array(data)
    output.sort(axis=0) # Do the actual sorting along the 
    output = output[indices] # Trim down to the desired quantiles
    
    return output



def sanitize(data=None, returninds=False):
        """
        Sanitize input to remove NaNs. Warning, does not work on multidimensional data!!
        
        Example:
            sanitized,inds = sanitize(array([3,4,nan,8,2,nan,nan,nan,8]), returninds=True)
        """
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
    filterdata = array(filterdata)
    if filterdata.dtype=='bool': validindices = filterdata # It's already boolean, so leave it as is
    else:                        validindices = ~isnan(filterdata) # Else, assume it's nans that need to be removed
    if sum(validindices): # There's at least one data point entered
        if len(data)==len(validindices): # They're the same length: use for logical indexing
            validdata = array(array(data)[validindices]) # Store each year
        elif len(validindices)==1: # They're different lengths and it has length 1: it's an assumption
            validdata = array([array(data)[defaultind]]) # Use the default index; usually either 0 (start) or -1 (end)
    else: 
        validdata = array([]) # No valid data, return an empty array
    return validdata



def findinds(val1, val2=None, eps=1e-6):
    """
    Little function to find matches even if two things aren't eactly equal (eg. 
    due to floats vs. ints). If one argument, find nonzero values. With two arguments,
    check for equality using eps. Returns a tuple of arrays if val1 is multidimensional,
    else returns an array.
    
    Examples:
        findinds(rand(10)<0.5) # e.g. array([2, 4, 5, 9])
        findinds([2,3,6,3], 6) # e.g. array([2])
    
    Version: 2016jun06 by cliffk
    """
    from numpy import nonzero, array, ndim
    if val2==None: # Check for equality
        output = nonzero(val1) # If not, just check the truth condition
    else:
        if isinstance(val2, (str, unicode)):
            output = nonzero(array(val1)==val2)
        else:
            output = nonzero(abs(array(val1)-val2)<eps) # If absolute difference between the two values is less than a certain amount
    if ndim(val1)==1: # Uni-dimensional
        output = output[0] # Return an array rather than a tuple of arrays if one-dimensional
    return output
    
    
def dataindex(dataarray, index):        
    """ Take an array of data and return either the first or last (or some other) non-NaN entry. """
    from numpy import zeros, shape
    
    nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1).
    output = zeros(nrows)       # Create structure
    for r in range(nrows): 
        output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
    
    return output


def smoothinterp(newx=None, origx=None, origy=None, smoothness=None, growth=None, strictnans=False):
    """
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
    """
    from numpy import array, interp, convolve, linspace, concatenate, ones, exp, isnan, argsort, ceil, float64
    
    # Ensure arrays and remove NaNs
    if isnumber(newx): newx = [newx] # Make sure it has dimension
    newx = array(newx, dtype=float64)
    origx = array(origx, dtype=float64)
    origy = array(origy, dtype=float64)
    
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
    """ Define an array of numbers uniformly perturbed with a mean of 1. n = number of points; span = width of distribution on either side of 1."""
    from numpy.random import rand, seed
    if randseed>=0: seed(randseed) # Optionally reset random seed
    output = 1. + 2*span*(rand(n)-0.5)
    return output
    
def scaleratio(inarray,total):
    """ Multiply a list or array by some factor so that its sum is equal to the total. """
    from numpy import array
    outarray = array([float(x)*total/float(sum(inarray)) for x in inarray])
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
## NESTED DICTIONARY FUNCTIONS
##############################################################################

"""
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
"""

def getnested(nesteddict, keylist, safe=False): 
    """ Get a value from a nested dictionary"""
    from functools import reduce
    output = reduce(lambda d, k: d.get(k) if d else None if safe else d[k], keylist, nesteddict)
    return output

def setnested(nesteddict, keylist, value): 
    """ Set a value in a nested dictionary """
    getnested(nesteddict, keylist[:-1])[keylist[-1]] = value
    return None # Modify nesteddict in place

def makenested(nesteddict, keylist,item=None):
    """ Insert item into nested dictionary, creating keys if required """
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
## MISCELLANEOUS FUNCTIONS
##############################################################################


def tic():
    """
    A little pair of functions to calculate a time difference, sort of like Matlab:
    t = tic()
    toc(t)
    """
    from time import time
    return time()



def toc(start=0, label='', sigfigs=3):
    """
    A little pair of functions to calculate a time difference, sort of like Matlab:
    t = tic()
    toc(t)
    """
    from time import time
    elapsed = time() - start
    if label=='': base = 'Elapsed time: '
    else: base = 'Elapsed time for %s: ' % label
    print(base + '%s s' % sigfig(elapsed, sigfigs=sigfigs))
    return None
    


def checkmem(origvariable, descend=0, order='n', plot=False, verbose=0):
    """
    Checks how much memory the variable in question uses by dumping it to file.
    
    Example:
        from utils import checkmem
        checkmem(['spiffy',rand(2483,589)],descend=1)
    """
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


def loadbalancer(maxload=0.5, index=None, refresh=1.0, maxtime=3600, verbose=True):
    ''' A little function to delay execution while CPU load is too high -- a poor man's load balancer '''
    from psutil import cpu_percent
    from time import sleep
    from numpy.random import random
    
    # Set up processes to start asynchronously
    if index is None:  delay = random()
    else:              delay = index*refresh
    if maxload>1: maxload/100. # If it's >1, assume it was given as a percent
    sleep(delay) # Give it time to asynchronize
    
    # Loop until load is OK
    toohigh = True # Assume too high
    count = 0
    maxcount = maxtime/float(refresh)
    while toohigh and count<maxcount:
        count += 1
        currentload = cpu_percent()/100.
        if currentload>maxload:
            if verbose: print('CPU load too high (%0.2f/%0.2f); process %s queued for the %ith time' % (currentload, maxload, index, count))
            sleep(refresh)
        else: 
            toohigh = False # print('CPU load fine (%0.2f/%0.2f)' % (currentload, maxload))
    return None
    
    



def runcommand(command, printinput=False, printoutput=False):
   """ Make it easier to run bash commands. Version: 1.1 Date: 2015sep03 """
   from subprocess import Popen, PIPE
   if printinput: print(command)
   try: output = Popen(command, shell=True, stdout=PIPE).communicate()[0].decode("utf-8")
   except: output = 'Shell command failed'
   if printoutput: print(output)
   return output



def gitinfo():
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
    except: # Failure? Give up
        gitbranch = 'Git branch information not retrivable'
        gitversion = 'Git version information not retrivable'
    return gitbranch, gitversion










##############################################################################
## CLASS FUNCTIONS
##############################################################################




def getdate(obj, which='modified', fmt='str'):
        ''' Return either the date created or modified ("which") as either a str or int ("fmt") '''
        from time import mktime
        
        dateformat = '%Y-%b-%d %H:%M:%S'
        
        try:
            if type(obj)==str: return obj # Return directly if it's a string
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
## ORDERED DICTIONARY
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
            except: # WARNING, should be KeyError, but this can't print newlines!!!
                if len(self.keys()): 
                    errormsg = 'odict key "%s" not found; available keys are:\n%s' % (str(key), 
                        '\n'.join([str(k) for k in self.keys()]))
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
        if type(key)==str:
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
    
    
    def __repr__(self, maxlen=None, spaces=True, divider=True):
        ''' Print a meaningful representation of the odict '''
         # Maximum length of string to display
        toolong = ' [...]'
        divider = '#############################################################\n'
        if len(self.keys())==0: 
            output = 'odict()'
        else: 
            output = ''
            hasspaces = 0
            for i in range(len(self)):
                if divider and spaces and hasspaces: output += divider
                thiskey = str(self.keys()[i]) # Probably don't need to cast to str, but just to be sure
                thisval = str(self.values()[i])
                if not(spaces):                    thisval = thisval.replace('\n','\\n') # Replace line breaks with characters
                if maxlen and len(thisval)>maxlen: thisval = thisval[:maxlen-len(toolong)] + toolong # Trim long entries
                if thisval.find('\n'): hasspaces = True
                output += '#%i: "%s": %s\n' % (i, thiskey, thisval)
        return output
    
    def disp(self, maxlen=55, spaces=False, divider=False):
        ''' Print out flexible representation, short by default'''
        print(self.__repr__(maxlen=maxlen, spaces=spaces, divider=divider))
    
    def _repr_pretty_(self, p, cycle):
        ''' Stupid function to fix __repr__ because IPython is stupid '''
        print(self.__repr__())
    
    
    def index(self, item):
        ''' Return the index of a given key '''
        return self.keys().index(item)
    
    def valind(self, item):
        ''' Return the index of a given value '''
        return self.items().index(item)
    
    def append(self, item):
        ''' Support an append method, like a list '''
        keyname = str(len(self)) # Define the key just to be the current index
        self.__setitem__(keyname, item)
        return None
    
    def rename(self, oldkey, newkey):
        ''' Change a key name -- WARNING, very inefficient! '''
        nkeys = len(self)
        if isinstance(oldkey, Number): 
            index = oldkey
            keystr = self.keys()[index]
        elif type(oldkey) is str: 
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
    
    def sort(self, sortby=None):
        ''' Return a sorted copy of the odict. 
        Sorts by order of sortby, if provided, otherwise alphabetical'''
        if not sortby: allkeys = sorted(self.keys())
        else:
            if not isinstance(sortby, list): raise Exception('Please provide a list to determine the sort order.')
            if all(isinstance(x,basestring) for x in sortby): # Going to sort by keys
                if not set(sortby)==set(self.keys()): 
                    errormsg = 'List of keys to sort by must be the same as list of keys in odict.\n You provided the following list of keys to sort by:\n'
                    errormsg += '\n'.join(sortby)
                    errormsg += '\n List of keys in odict is:\n'
                    errormsg += '\n'.join(self.keys())
                    raise Exception(errormsg)
                else: allkeys = sortby
            elif all(isinstance(x,int) for x in sortby): # Going to sort by numbers
                if not set(sortby)==set(range(len(self))):
                    errormsg = 'List to sort by "%s" is not compatible with length of odict "%i"' % (sortby, len(self))
                    raise Exception(errormsg)
                else: allkeys = [y for (x,y) in sorted(zip(sortby,self.keys()))]
            else: raise Exception('Cannot figure out how to sort by "%s"' % sortby)
        out = odict()
        for key in allkeys: out[key] = self[key]
        return out







##############################################################################
## DATA FRAME CLASS
##############################################################################

# These are repeated to make this frationally more self-contained
from numpy import array, zeros, vstack, hstack, matrix, argsort # analysis:ignore
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
        a.rmrow(); print a # Remove last row
        a.rmrow(3); print a # Remove the row starting with element '3'
    
    Version: 2016oct31
    '''

    def __init__(self, cols=None, data=None):
        if cols is None: cols = list()
        if data is None: data = zeros((len(cols),0), dtype=object)
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
                maxlen = -1
                if nrows:
                    for val in self.data[c,:]:
                        output = str(val)
                        maxlen = max(maxlen, len(output))
                        outputlist[col].append(output)
                outputformats[col] = '%'+'%i'%(maxlen+spacing)+'s'
            
            if   nrows<10:   indformat = '%2s' # WARNING, KLUDGY
            elif nrows<100:  indformat = '%3s'
            elif nrows<1000: indformat = '%4s'
            else:            indformat = '%5s'
            
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
    
    def _val2row(self, value):
        ''' Convert a list, array, or dictionary to the right format for appending to a dataframe '''
        if isinstance(value, dict):
            output = zeros(self.ncols(), dtype=object)
            for c,col in enumerate(self.cols):
                try: 
                    output[c] = value[col]
                except: 
                    raise Exception('Entry for column %s not found; keys you supplied are: %s' % (col, value.keys()))
            return array(output, dtype=object)
        else: # Not sure what it is, just make it an array
            return array(value, dtype=object)
    
    def _sanitizecol(self, col):
        ''' Take None or a string and return the index of the column '''
        if col is None: output = 0 # If not supplied, assume first column is control
        elif isinstance(col, (str, unicode)): output = self.cols.index(col) # Convert to index
        else: output = col
        return output
        
    def __getitem__(self, key):
        if isinstance(key, (str, unicode)):
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
        if isinstance(key, (str, unicode)):
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
    
    def rmcol(self, key, returnval=True):
        ''' Remove a column from the data frame '''
        colindex = self.cols.index(key)
        self.cols.pop(colindex)
        thiscol = self.data[colindex,:]
        self.data = vstack((self.data[:colindex,:], self.data[colindex+1:,:]))
        if returnval: return thiscol
        else: return None
    
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
    
    def addrow(self, value, overwrite=True, col=None, reverse=False):
        ''' Like append, but removes duplicates in the first column and resorts '''
        value = self._val2row(value) # Make sure it's in the correct format
        col = self._sanitizecol(col)
        try:    index = self.data[col,:].tolist().index(value[col]) # Try to find duplicates
        except: index = None
        if index is None or not overwrite: self.append(value)
        else: self.data[:,index] = value # If it exists already, just replace it
        self.sort(col=col, reverse=reverse) # Sort
        return None
    
    def rmrow(self, key=None, col=None, returnval=False):
        ''' Like pop, but removes by matching the first column instead of the index '''
        col = self._sanitizecol(col)
        if key is None: key = self.data[col,-1] # If not supplied, pick the last element
        try:    index = self.data[col,:].tolist().index(key) # Try to find duplicates
        except: raise Exception('Item %s not found; choices are: %s' % (key, self.data[col,:]))
        thisrow = self.pop(index)
        if returnval: return thisrow
        else:         return None
    
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
## OPTIMA EXCEPTIONS CLASS
##############################################################################

class OptimaException(Exception):
    ''' A tiny class to allow for Optima-specific exceptions '''
    def __init(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
