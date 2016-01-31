##############################################################################
## PRINTING FUNCTIONS
##############################################################################


def printv(string, thisverbose=1, verbose=2, newline=True):
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
        indents = '  '*thisverbose # Create automatic indenting
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


def objrepr(obj):
    ''' Return useful printout for the Python __repr__ method '''
    output =  objectid(obj)
    output += '============================================================\n'
    output += objatt(obj)
    output += '============================================================\n'
    output += objmeth(obj)
    output += '============================================================\n'
    return output

def defaultrepr(obj, maxlen=55):
    ''' Prints out the default representation of an object -- all attributes, plust methods and ID '''
    keys = sorted(obj.__dict__.keys())
    maxkeylen = max([len(key) for key in keys])
    if maxkeylen<maxlen: maxlen = maxlen - maxkeylen
    formatstr = '%'+ '%i'%maxkeylen + 's'
    output = '============================================================\n'
    output +=  objectid(obj)
    output += '============================================================\n'
    for key in keys:
        thisattr = str(getattr(obj, key))
        if len(thisattr)>maxlen: thisattr = thisattr[:maxlen] + ' [...]'
        output += formatstr%key + ': ' + thisattr + '\n'
    output += '============================================================\n'
    output += objmeth(obj)
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
    


def sigfig(x, sigfigs=3):
    """ Return a string representation of variable x with sigfigs number of significant figures """
    try:
        if x==0: return '0'
        from numpy import log10, floor
        magnitude = floor(log10(abs(x)))
        factor = 10**(sigfigs-magnitude-1)
        x = round(x*factor)/float(factor)
        digits = int(abs(magnitude) + max(0, sigfigs - max(0,magnitude) - 1) + 1 + (x<0) + (abs(x)<1)) # one because, one for decimal, one for minus
        decimals = int(max(0,-magnitude+sigfigs-1))
        strformat = '%' + '%i.%i' % (digits, decimals)  + 'f'
        string = strformat % x
        return string
    except:
        return str(x)
    

    


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



def sanitize(arraywithnans):
        """ Sanitize input to remove NaNs. Warning, does not work on multidimensional data!! """
        from numpy import array, isnan
        try:
            arraywithnans = array(arraywithnans) # Make sure it's an array
            sanitized = arraywithnans[~isnan(arraywithnans)]
        except:
            raise Exception('Sanitization failed on array:\n %s' % arraywithnans)
        if len(sanitized)==0:
            sanitized = 0
            print('                WARNING, no data entered for this parameter, assuming 0')

        return sanitized


def findinds(val1, val2=None, eps=1e-6):
    """
    Little function to find matches even if two things aren't eactly equal (eg. 
    due to floats vs. ints). If one argument, find nonzero values. With two arguments,
    check for equality using eps. Returns a tuple of arrays if val1 is multidimensional,
    else returns an array.
    
    Examples:
        findinds(rand(10)<0.5) # e.g. array([2, 4, 5, 9])
        findinds([2,3,6,3], 6) # e.g. array([2])
    
    Version: 2014nov27 by cliffk
    """
    from numpy import nonzero, array, ndim
    if val2==None: # Check for equality
        output = nonzero(val1) # If not, just check the truth condition
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


def smoothinterp(newx=None, origx=None, origy=None, smoothness=None, growth=None):
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
    
    Version: 2016jan29 by cliffk
    """
    from numpy import array, interp, convolve, linspace, concatenate, ones, exp, isnan, argsort, ceil
    
    # Ensure arrays and remove NaNs
    newx = array(newx)
    origx = array(origx)
    origy = array(origy)
    
    if not(newx.shape): raise Exception('To interpolate, must have at least one new x value to interpolate to')
    if not(origx.shape): raise Exception('To interpolate, must have at least one original x value to interpolate to')
    if not(origy.shape): raise Exception('To interpolate, must have at least one original y value to interpolate to')
    if not(origx.shape==origy.shape): 
        errormsg = 'To interpolate, original x and y vectors must be same length (x=%i, y=%i)' % (len(origx), len(origy))
        raise Exception(errormsg)
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
    newy = concatenate([newy[0]*ones(smoothness), newy, newy[-1]*ones(smoothness)])
    newy = convolve(newy, kernel, 'valid') # Smooth it out a bit
    
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
    outarray = array(inarray)
    outarray = [float(x)*total/sum(outarray) for x in outarray]
    if type(inarray)==list: outarray = outarray.tolist() # Preserve type
    return outarray






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
        from matplotlib.pylab import pie, array, axes
        axes(aspect=1)
        pie(array(printbytes)[inds], labels=array(printnames)[inds], autopct='%0.2f')

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


def saveobj(filename, obj, verbose=True):
    ''' Save an object to file '''
    try: import cPickle as pickle # For Python 2 compatibility
    except: import pickle
    from gzip import GzipFile
    
    with GzipFile(filename, 'wb') as fileobj: pickle.dump(obj, fileobj, protocol=2)
    if verbose: print('Object saved to "%s"' % filename)
    return None


def loadobj(filename, verbose=True):
    ''' Load a saved file '''
    try:
        import cPickle as pickle  # For Python 2 compatibility
    except:
        import pickle
    from gzip import GzipFile
    
    # Handle loading of either filename or file object
    if isinstance(filename, basestring): argtype='filename'
    else: argtype = 'fileobj'
    kwargs = {'mode': 'rb', argtype: filename}

    with GzipFile(**kwargs) as fileobj: obj = pickle.load(fileobj)
    if verbose: print('Object loaded from "%s"' % filename)
    return obj


def saves(obj):
    ''' Save an object to a string in gzip-compatible way'''
    try: import cPickle as pickle # For Python 2 compatibility
    except: import pickle
    from gzip import GzipFile
    from cStringIO import StringIO
    from contextlib import closing
    result = None
    with closing(StringIO()) as output:
        with GzipFile(fileobj = output, mode = 'wb') as fileobj: 
            pickle.dump(obj, fileobj, protocol=2)
        output.seek(0)
        result = output.read()
    return result


def loads(source):
    ''' Load an object from a string in gzip-compatible way'''
    try: import cPickle as pickle # For Python 2 compatibility
    except: import pickle
    from gzip import GzipFile
    from cStringIO import StringIO
    from contextlib import closing
    with closing(StringIO(source)) as output:
        with GzipFile(fileobj = output, mode = 'rb') as fileobj: 
            obj = pickle.load(fileobj)
    return obj


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
        
        if fmt=='str': return dateobj.strftime(dateformat) # Return string representation of time
        elif fmt=='int': return mktime(dateobj.timetuple()) # So ugly!! But it works -- return integer representation of time
        else: raise Exception('"fmt=%s" not understood; must be "str" or "int"' % fmt)
    
    
    
def setdate(obj):
    ''' Update the last modified date '''
    from datetime import datetime
    obj.modified = datetime.today()
    return None









##############################################################################
## ORDERED DICTIONARY
##############################################################################


from collections import OrderedDict
from numpy import array

class odict(OrderedDict):
    """
    ODICT
    
    An ordered dictionary, like the OrderedDict class, but supporting list methods like integer referencing,
    slicing, and appending.
    
    WARNING: self.update() may not be functional
    
    Version: 2015nov21 by cliffk
    """

    def __slicekey(self, key, slice_end):
        shift = int(slice_end=='stop')
        if isinstance(key, (int, float)): return key
        elif type(key) is str: return self.index(key)+shift # +1 since otherwise confusing with names (CK)
        elif key is None: return (len(self) if shift else 0)
        else: raise Exception('To use a slice, %s must be either int or str (%s)' % (slice_end, key))


    def __is_odict_iterable(self, v):
        return type(v)==list or type(v)==type(array([]))


    def __getitem__(self, key):
        ''' Allows getitem to support strings, integers, slices, lists, or arrays '''
        if isinstance(key, (int, float)): # Convert automatically from float...dangerous?
            return self.values()[int(key)]
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
        else: # Handle string but also everything else
            try:
                output = OrderedDict.__getitem__(self,key)
                return output
            except: # WARNING, should be KeyError, but this can't print newlines!!!
                if len(self.keys()): errormsg = 'odict key "%s" not found; available keys are:\n%s' % (key, '\n'.join(self.keys()))
                else: errormsg = 'Key "%s" not found since odict is empty'% key
                raise Exception(errormsg)

        
    def __setitem__(self, key, value):
        ''' Allows setitem to support strings, integers, slices, lists, or arrays '''
        if type(key)==str:
            OrderedDict.__setitem__(self, key, value)
        elif isinstance(key, (int, float)): # Convert automatically from float...dangerous?
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
                        self.__setitem__(index, value[valind])
                else:
                    errormsg = 'Slice "%s" and values "%s" have different lengths! (%i, %i)' % (slicerange, value, slicelen, len(value))
                    raise Exception(errormsg)
            else: 
                self.__setitem__(key, value)
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
    
    
    def __repr__(self):
        ''' Print a meaningful representation of the odict '''
        if len(self.keys())==0: output = 'odict()'
        else: output = '\n'.join(["#%i: '%s': %s" % (i, self.keys()[i], self.values()[i]) for i in range(len(self))])
        return output
    
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
        if isinstance(oldkey, (int, float)): 
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
            if all(isinstance(x,str) for x in sortby): # Going to sort by keys
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
## OPTIMA EXCEPTIONS CLASS
##############################################################################

class OptimaException(Exception):
    ''' A tiny class to allow for Optima-specific exceptions '''
    def __init(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
