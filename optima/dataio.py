#############################################################################################################################
### Imports
#############################################################################################################################

try: import cPickle as pickle # For Python 2 compatibility
except: import pickle
from gzip import GzipFile
from cStringIO import StringIO
from contextlib import closing
from os import path, sep
from numpy import ones, zeros
from optima import odict, OptimaException
from xlrd import open_workbook


#############################################################################################################################
### Basic I/O functions
#############################################################################################################################

def saveobj(filename, obj, compresslevel=5, verbose=True):
    ''' Save an object to file -- use compression 5, since more is much slower but not much smaller '''
    with GzipFile(filename, 'wb', compresslevel=compresslevel) as fileobj:
        fileobj.write(pickle.dumps(obj, protocol=-1))
    if verbose: print('Object saved to "%s"' % filename)
    return None


def loadobj(filename, verbose=True):
    ''' Load a saved file '''
    # Handle loading of either filename or file object
    if isinstance(filename, basestring): argtype='filename'
    else: argtype = 'fileobj'
    kwargs = {'mode': 'rb', argtype: filename}
    with GzipFile(**kwargs) as fileobj:
        obj = loadpickle(fileobj)
    if verbose: print('Object loaded from "%s"' % filename)
    return obj


def dumpstr(obj):
    ''' Write data to a fake file object,then read from it -- used on the FE '''
    result = None
    with closing(StringIO()) as output:
        with GzipFile(fileobj = output, mode = 'wb') as fileobj: 
            fileobj.write(pickle.dumps(obj, protocol=-1))
        output.seek(0)
        result = output.read()
    return result


def loadstr(source):
    ''' Load data from a fake file object -- also used on the FE '''
    with closing(StringIO(source)) as output:
        with GzipFile(fileobj = output, mode = 'rb') as fileobj: 
            obj = loadpickle(fileobj)
    return obj


def map_path(modulename, classname, verbose=3):
    ''' Adapted from http://stackoverflow.com/questions/13398462/unpickling-python-objects-with-a-changed-module-path '''
    import numpy as np
    
    class ReallyEmptyClass(object): pass
    
    # Define an empty class
    class EmptyClass(object):
        
        def __new__(self, *args, **kwargs):
            if verbose>=3:
                print('Newing empty class...')
                print(args)
                print(kwargs)
                print('Done initializing')
            try:
                newobj = args[0](*args[1:]) # If it's a class, initialize this object with it
                return newobj
            except:
                print('Newing class failed')
                return ReallyEmptyClass()
#                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        
        def __init__(self, *args, **kwargs):
            if verbose>=3:
                print('Initializing empty class...')
                print(args)
                print(kwargs)
                print('Done initializing')
            try: 
                if args[0]==np.ndarray:
                    this = np.ndarray(*args[1:]) # If it's a class, initialize this object with it
                    self.__dict__ = this.__dict__ # Reset this, lol
                    print('is ok')
                else:
                    print('thought tihs isnt an array')
                    print args[0]
                if verbose>=3: print('Initializing object succeeded')
            except:
                if verbose>=3: print('Initializing object failed')
                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            return None
        
        def __setstate__(self, state, *args, **kwargs):
            if verbose>=3:
                print('Setting state...')
                print(state)
                print(args)
                print(kwargs)
                print('Done initializing')
#            try:
#                self.__
            return None
    
    # Handle the case where the module doesn't exist -- shouldn't happen
    try:
        module = __import__(modulename)
        if verbose>=3: print('Success: Loading module %s' % modulename)
    except:
        if verbose>=1: print('Fail: Loading module %s' % modulename)
        module = EmptyClass()
    
    # Handle the case where the attribute doesn't exist -- will happen if class names have changed
    try:
        output = getattr(module, classname) # Main usage case -- everything is fine
        if verbose>=2: print('Success: Loading attribute %s.%s' % (modulename, classname))
        return output
    except:
        if verbose>=2: print('Fail: Loading attribute %s.%s' % (modulename, classname))
        return EmptyClass
        


def loadpickle(fileobj, attempts=10, verbose=True):
    ''' Loads a pickled object -- need to define legacy classes here since they're needed for unpickling '''
    
    # Load the file object
    filestr = fileobj.read() # Read the binary file object
    unpickler = pickle.Unpickler(StringIO(filestr))
    unpickler.find_global = map_path
    obj = unpickler.load() # Actually load it
    
    return obj
    

#############################################################################################################################
### Functions to load the parameters and transitions
#############################################################################################################################

# Default filename for all the functions that read this spreadsheet
default_filename = 'model-inputs.xlsx'


def loadpartable(filename=default_filename):
    '''  Function to parse the parameter definitions from the spreadsheet and return a structure that can be used to generate the parameters '''
    sheetname = 'Model parameters'
    workbook = open_workbook(path.abspath(path.dirname(__file__))+sep+filename)
    sheet = workbook.sheet_by_name(sheetname)

    rawpars = []
    for rownum in range(sheet.nrows-1):
        rawpars.append({})
        for colnum in range(sheet.ncols):
            attr = sheet.cell_value(0,colnum)
            rawpars[rownum][attr] = sheet.cell_value(rownum+1,colnum) if sheet.cell_value(rownum+1,colnum)!='None' else None
            if sheet.cell_value(0,colnum) in ['limits']:
                rawpars[rownum][attr] = eval(sheet.cell_value(rownum+1,colnum)) # Turn into actual values
    return rawpars



def loadtranstable(filename=default_filename, npops=None):
    ''' Function to load the allowable transitions from the spreadsheet '''
    sheetname = 'Transitions' # This will only change between Optima versions, so OK to have in body of function
    if npops is None: npops = 1 # Use just one population if not told otherwise
    workbook = open_workbook(path.abspath(path.dirname(__file__))+sep+filename)
    sheet = workbook.sheet_by_name(sheetname)
    
    if sheet.nrows != sheet.ncols:
        errormsg = 'Transition matrix should have the same number of rows and columns (%i vs. %i)' % (sheet.nrows, sheet.ncols)
        raise OptimaException(errormsg)
    nstates = sheet.nrows-1 # First row is header

    fromto = []
    transmatrix = zeros((nstates,nstates,npops))
    for rownum in range(nstates): # Loop over each health state: the from state
        fromto.append([]) # Append two lists: the to state and the probability
        for colnum in range(nstates): # ...and again
            if sheet.cell_value(rownum+1,colnum+1):
                fromto[rownum].append(colnum) # Append the to states
                transmatrix[rownum,colnum,:] = ones(npops) # Append the probabilities
    
    return fromto, transmatrix



def loaddatapars(filename=default_filename, verbose=2):
    ''' Function to parse the data parameter definitions '''
    inputsheets = ['Data inputs', 'Data constants']
    workbook = open_workbook(path.abspath(path.dirname(__file__))+sep+filename)
    
    pardefinitions = odict()
    for inputsheet in inputsheets:
        sheet = workbook.sheet_by_name(inputsheet)
        rawpars = []
        for rownum in range(sheet.nrows-1):
            rawpars.append({})
            for colnum in range(sheet.ncols):
                attr = str(sheet.cell_value(0,colnum))
                cellval = sheet.cell_value(rownum+1,colnum)
                if cellval=='None': cellval = None
                if type(cellval)==unicode: cellval = str(cellval)
                rawpars[rownum][attr] = cellval
        pardefinitions[inputsheet] = rawpars
    
    sheets = odict() # Lists of parameters in each sheet
    sheettypes = odict() # The type of each sheet -- e.g. time parameters or matrices
    checkupper = odict() # Whether or not the upper limit of the parameter should be checked
    sheetcontent = odict()
    for par in pardefinitions['Data inputs']:
        if par['sheet'] not in sheets.keys(): # Create new list if sheet not encountered yet
            sheets[par['sheet']] = [] # Simple structure for storing a list of parameter names, used in loadspreadsheet
            sheetcontent[par['sheet']] = [] # Complex structure for storing all information, used in makespreadsheet
        sheets[par['sheet']].append(par['short']) # All-important: append the parameter name
        sheetcontent[par['sheet']].append(par) # Append entire dictionary
        sheettypes[par['sheet']] = par['type'] # Figure out why kind of sheet this is
        checkupper[par['short']] = True if par['rowformat'] in ['decimal', 'percentage'] else False # Whether or not to check the upper limit
    
    # Handle constants separately
    sheets['Constants'] = []
    for par in pardefinitions['Data constants']:
        sheets['Constants'].append(par['short'])
    sheettypes['Constants'] = 'constant' # Hard-code this
    
    # Store useful derivative information
    pardefinitions['sheets'] = sheets
    pardefinitions['sheetcontent'] = sheetcontent
    pardefinitions['sheettypes'] = sheettypes
    pardefinitions['checkupper'] = checkupper
    
    return pardefinitions