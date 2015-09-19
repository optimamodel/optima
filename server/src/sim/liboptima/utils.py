import numpy

def printv(string, thisverbose=1, verbose=2, newline=True):
    """
    Optionally print a message and automatically indent.
    """
    if verbose>=thisverbose: # Only print if sufficiently verbose
        indents = '  '*thisverbose # Create automatic indenting
        if newline: print('%s%s' % (indents,string)) # Actually print
        else: print('%s%s' % (indents,string)), # Actually print

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
    for r in xrange(nrows): 
        output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
    
    return output


def smoothinterp(newx=None, origx=None, origy=None, smoothness=10, growth=None):
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
    
    Version: 2014dec01 by cliffk
    """
    from numpy import array, interp, convolve, linspace, concatenate, ones, exp, isnan, argsort
    
    # Ensure arrays and remove NaNs
    newx = array(newx)
    origx = array(origx)
    origy = array(origy)
    origy = origy[~isnan(origy)] 
    origx = origx[~isnan(origy)]
    
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
    output = output.tolist() # Otherwise, convert to a list
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
        for i in xrange(len(arr)):
            string += arrformat % arr[i]
        print(string)
    elif ndim(arr)==2:
        for i in xrange(len(arr)):
            printarr(arr[i], arrformat)
    elif ndim(arr)==3:
        for i in xrange(len(arr)):
            print('='*len(arr[i][0])*len(arrformat % 1))
            for j in xrange(len(arr[i])):
                printarr(arr[i][j], arrformat)
    else:
        print(arr) # Give up
    return None
    


def sigfig(x, sigfigs=3):
    """ Return a string representation of variable x with sigfigs number of significant figures """
    from numpy import log10, floor
    magnitude = floor(log10(abs(x)))
    factor = 10**(sigfigs-magnitude-1)
    x = round(x*factor)/float(factor)
    digits = int(abs(magnitude) + max(0, sigfigs - max(0,magnitude) - 1) + 1 + (x<0) + (abs(x)<1)) # one because, one for decimal, one for minus
    decimals = int(max(0,-magnitude+sigfigs-1))
    strformat = '%' + '%i.%i' % (digits, decimals)  + 'f'
    string = strformat % x
    return string


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
    


def printdata(data, name='Variable', depth=1, maxlen=40, indent='', level=0, showcontents=False):
    """
    Nicely print a complicated data structure, a la Matlab.
    Arguments:
      data: the data to display
      name: the name of the variable (automatically read except for first one)
      depth: how many levels of recursion to follow
      maxlen: number of characters of data to display (if 0, don't show data)
      indent: where to start the indent (used internally)

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


def run(command, printinput=False, printoutput=False):
	""" Make it easier to run bash commands. Version: 1.0 Date: 2015aug16 """
	from subprocess import Popen, PIPE
	if printinput: print(command)
	try: output = Popen(command, shell=True, stdout=PIPE).communicate()[0]
	except: output = 'Shell command failed'
	if printoutput: print(output)
	return output


def dict_equal(d1,d2,verbose=0,debug_string=''):
	# Check if two dictionaries contain the same stuff

	# Check that they're the same type
	if isinstance(d1,str):
		d1 = unicode(d1)
	if isinstance(d2,str):
		d2 = unicode(d2)

	if type(d1) != type(d2):
		if verbose:
			print '%s Types of %s and %s are different: they are %s and %s' % (debug_string,d1,d2,type(d1),type(d2))
		return False
		
	if hasattr(d1,'todict') and callable(getattr(d1,'todict')): # If the object has a todict() method
		return dict_equal(d1.todict(),d2.todict(),verbose=verbose,debug_string=' d1.todict()->')

	if d1 is None and d2 is None:
		if verbose:
			print '%s %s and %s are None' % (debug_string,d1,d2)
		return True

	# If they are dictionaries, check all of their fields
	if isinstance(d1,dict):
		if d1.viewkeys() != d2.viewkeys():
			if verbose:
				print '%s Keys do not match: d1=%s,d2=%s' % (debug_string,d1.viewkeys(),d2.viewkeys())
			return False
		else:
			return all([dict_equal(d1[k],d2[k],verbose=verbose,debug_string='%s dict[%s]->' % (debug_string,k)) for k in d1.keys() if k is not 'UUID']) # Need to skip the UUID
	
	# Vector reduction for ndarrays
	elif isinstance(d1,(float,numpy.ndarray)):
		# We need to check array equality considering NaN==NaN to be true
		comparison = isequalwithequalnans(d1,d2)
		if not comparison and verbose:
			print '%s arrays do not match' % (debug_string)
		return comparison 

	# We might have a list of ndarrays 
	elif isinstance(d1,list):
		if len(d1) != len(d2):
			if verbose:
				print "%s List length doesn't match" % (debug_string)
			return False
		rval = all([dict_equal(d1[x],d2[x],verbose=verbose,debug_string='%s list[%s]->' % (debug_string,x)) for x in xrange(0,len(d1))]) 
		if verbose and not rval:
			print d1[1]
			print d2[1]
			print "%s List items don't match"  % (debug_string)
			return False
		return rval
	# Direct equality
	elif isinstance(d1,(tuple,int,str,unicode)):
		return d1 == d2
	else:
		raise Exception("%s Do not know how to compare objects of type %s" % (debug_string,type(d1)))

def isequalwithequalnans(a,b):
	# A close of Matlab for testing equality of arrays containing NaNs
	# Note that the type of a and b is *assumed* to be the same
	# i.e. this function will return true if the type conversion leads to equality
	# e.g. isequalwithequalnans(1,1.0) -> True
	if isinstance(a,float):
		if numpy.isnan(a) and numpy.isnan(b):
			return True
		else:
			return a==b

	elif isinstance(a,numpy.ndarray):
		if not numpy.all(a.size == b.size): # If they are different sizes, they aren't equal
			return False
		if a.size == 0:
			return True # Two empty arrays are equal

		# Now check if the non NaN entries are equal
		non_nan_equal =  numpy.ma.all(numpy.ma.masked_where(numpy.isnan(a), a) == numpy.ma.masked_where(numpy.isnan(b), b)) 
		if not non_nan_equal:
			return False

		# Finally, check that the NaNs are in the same place
		return numpy.array_equal(numpy.isnan(a),numpy.isnan(b))
	else:
		raise Exception('Unrecognized type')

