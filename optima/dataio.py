try: import cPickle as pickle # For Python 2 compatibility
except: import pickle
from gzip import GzipFile
from cStringIO import StringIO
from contextlib import closing


def saveobj(filename, obj, verbose=True):
    ''' Save an object to file '''
    with GzipFile(filename, 'wb') as fileobj: pickle.dump(obj, fileobj, protocol=2)
    if verbose: print('Object saved to "%s"' % filename)
    return None


def loadobj(filename, verbose=True):
    ''' Load a saved file '''
    # Handle loading of either filename or file object
    if isinstance(filename, basestring): argtype='filename'
    else: argtype = 'fileobj'
    kwargs = {'mode': 'rb', argtype: filename}
    with GzipFile(**kwargs) as fileobj: obj = pickle.load(fileobj)
    if verbose: print('Object loaded from "%s"' % filename)
    return obj


def dumps(obj):
    ''' Save an object to a string in gzip-compatible way'''
    result = None
    with closing(StringIO()) as output:
        with GzipFile(fileobj = output, mode = 'wb') as fileobj: 
            pickle.dump(obj, fileobj, protocol=2)
        output.seek(0)
        result = output.read()
    return result


def loads(source):
    ''' Load an object from a string in gzip-compatible way'''
    with closing(StringIO(source)) as output:
        with GzipFile(fileobj = output, mode = 'rb') as fileobj: 
            obj = pickle.load(fileobj)
    return obj