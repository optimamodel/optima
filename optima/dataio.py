from __future__ import print_function

import ast
import optima
import numpy
import datetime
import types
import uuid
import zlib
import math

from dateutil import parser, tz
from twisted.python.reflect import qual, namedAny




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



def savedbobj(filename, obj, verbose=True):
    ''' Save an object to file '''
    dumped = dumps(obj)

    with open(filename, 'wb') as fileobj:
        fileobj.write(dumped)
    if verbose: print('Object saved to "%s"' % filename)
    return None


def loaddbobj(filename, verbose=True):
    ''' Load a saved file (pickle or JSON)'''
    try:
        import cPickle as pickle  # For Python 2 compatibility
    except:
        import pickle
    from gzip import GzipFile

    # Handle loading of either filename or file object
    if isinstance(filename, basestring): argtype='filename'
    else: argtype = 'fileobj'
    kwargs = {'mode': 'rb', argtype: filename}

    try:
        from ._serialize import loads

        if argtype == "fileobj":
            read = filename.read()
        else:
            with open(filename, 'rb') as f:
                read = f.read()

        obj = loads(read)
    except:
        if argtype == "fileobj":
            filename.seek(0)
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






def dumps(obj):

    obj_registry = {}
    id_number = [0]
    saved_types = set()

    def default(r):

        if isinstance(r, optima.odict):
            o = {
                "obj": "odict",
                "val": [(default(x), default(y)) for x, y in r.iteritems()]}

        elif isinstance(r, uuid.UUID):
            o = {"obj": "UUID", "val": str(r.hex)}

        elif isinstance(r, numpy.ndarray):
            o = {"obj": "numpy.ndarray", "val": [default(x) for x in r]}

        elif isinstance(r, numpy.bool_):
            o = bool(r)

        elif isinstance(r, numpy.int32):
            o = long(r)

        elif r == numpy.nan:
            o = {"obj": "numpy.NaN"}

        elif isinstance(r, datetime.datetime):
            r.replace(tzinfo=tz.tzlocal())
            o = {"obj": "datetime", "val": r.isoformat(" ")}

        elif isinstance(r, tuple):
            o = {"obj": "tuple", "val": [default(x) for x in r]}

        elif isinstance(r, (str, unicode, int, long, types.NoneType, bool)):
            o = r

        elif isinstance(r, float):
            if math.isnan(r):
                o = {"obj": "float", "val": "nan"}
            else:
                o = r

        elif isinstance(r, list):
            o = [default(x) for x in r]

        elif isinstance(r, dict):
            o = {}
            for x,y in r.items():
                o[default(x)] = default(y)

        else:
            if not r in obj_registry:

                my_id = id_number[0]
                id_number[0] += 1

                obj_registry[r] = [my_id, None]

                try:
                    results = default(r.__getstate__())
                except AttributeError:
                    results = default(r.__dict__)

                q = {
                    "obj": "obj",
                    "type": qual(r.__class__),
                    "val": results,
                    "id": my_id
                }
                obj_registry[r][1] = q
                saved_types.add(qual(r.__class__))

            o = {
                "obj": "ref",
                "ref": obj_registry[r][0]
            }

        return o

    schema = default(obj)
    new_registry = {x[0]:x[1] for x in obj_registry.values()}

    dumped = repr({"registry": new_registry, "schema": schema})

    # print("Serialized:\n", "\n".join(saved_types))

    return zlib.compress(dumped, 6)



def loads(input):

    a = ast.literal_eval(zlib.decompress(input))

    registry = a["registry"]
    schema = a["schema"]
    loaded = {}

    def decode(o):

        if isinstance(o, list):
            return [decode(x) for x in o]

        elif isinstance(o, dict):

            if "obj" in o:

                obj = o["obj"]
                val = o.get("val")

                if obj == "ref":

                    ref = o["ref"]
                    return decode(registry[ref])

                elif obj == "obj":

                    if o["id"] in loaded:
                        return loaded[o["id"]]

                    newClass = namedAny(o["type"])

                    new = object.__new__(newClass)

                    loaded[o["id"]] = new

                    state = {x:decode(y) for x,y in val.items()}
                    try:
                        new.__setstate__(state)
                    except AttributeError:
                        new.__dict__ = state

                    return new

                elif obj == "datetime":
                    o = parser.parse(val)
                    return o

                elif obj == "UUID":
                    o = uuid.UUID(val)
                    return o

                elif obj == "numpy.ndarray":
                    o = numpy.array([decode(x) for x in val])
                    return o

                elif obj == "odict":

                    o = optima.odict()

                    for i in val:
                        key = decode(i[0])
                        val = decode(i[1])

                        o[key] = val

                elif obj == "tuple":
                    o = tuple([decode(x) for x in val])

                elif obj == "float":
                    o = float(val)

                else:
                    assert False, str(o)[0:1000]
            else:
                return {decode(x):decode(y) for x,y in o.iteritems()}

            return o

        return o

    done = decode(schema)
    return done
