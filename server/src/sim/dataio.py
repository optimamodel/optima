"""
DATAIO

Data input/output. Uses JSON format.

Version: 2014nov17 by cliffk
"""

from printv import printv
import os


DATADIR="/tmp/uploads"
TEMPLATEDIR = "/tmp/templates"
PROJECTDIR = "/tmp/projects"

EXT_JSON = ".json"
EXT_PRJ = ".prj"


def fullpath(filename, datadir=DATADIR):
    """
    "Normalizes" filename:  if it is full path, leaves it alone. Otherwise, prepends it with datadir.
    """

    result = filename

    # get user dir path
    datadir = upload_dir_user(datadir)

    if not(os.path.exists(datadir)):
        os.makedirs(datadir)
    if os.path.dirname(filename)=='' and not os.path.exists(filename):
        result = os.path.join(datadir, filename)

    return result

def templatepath(filename):
    return fullpath(filename, TEMPLATEDIR)

def projectpath(filename):
    return fullpath(filename, PROJECTDIR)




def savedata(filename, data, update=True, verbose=2):
    """
    Saves the pickled data into the file (either updates it or just overwrites).
    """
    printv('Saving data...', 1, verbose)

    from json import dump
    
    filename = projectpath(filename)

    wfid = open(filename,'wb')
    dump(tojson(data), wfid)
    printv('..created new file', 3, verbose)
    printv(' ...done saving data at %s.' % filename, 2, verbose)
    return filename


def loaddata(filename, verbose=2):
    """
    Loads the file and imports json data from it.
    If the file cannot be load as json, tries loading it with cPickle.
    """

    printv('Loading data...', 1, verbose)
    if not os.path.exists(filename):
        filename = projectpath(filename)

    import json
    rfid = open(filename,'rb')
    data = fromjson(json.load(rfid))

    printv('...done loading data.', 2, verbose)
    return data



def tojson(x):
    """ Convert an object to JSON-serializable format, handling e.g. Numpy arrays """
    from numpy import ndarray, isnan

    if isinstance(x, dict):
        return dict( (k, tojson(v)) for k,v in x.iteritems() )
    elif isinstance(x, (list, tuple)):
        return type(x)( tojson(v) for v in x )
    elif isinstance(x, ndarray):
        return {"np_array":[tojson(v) for v in x.tolist()], "np_dtype":x.dtype.name}
    elif isinstance(x, float) and isnan(x):
        return None
    else:
        return x


def fromjson(x):
    """ Convert an object from JSON-serializable format, handling e.g. Numpy arrays """
    NP_ARRAY_KEYS = set(["np_array", "np_dtype"])
    from numpy import asarray, dtype, nan

    if isinstance(x, dict):
        dk = x.keys()
        if len(dk) == 2 and set(dk) == NP_ARRAY_KEYS:
            return asarray(fromjson(x['np_array']), dtype(x['np_dtype']))
        else:
            return dict( (k, fromjson(v)) for k,v in x.iteritems() )
    elif isinstance(x, (list, tuple)):
        return type(x)( fromjson(v) for v in x )
    elif x is None:
        return nan
    else:
        return x


def upload_dir_user(dirpath, user_id = None):

    try:
        from flask.ext.login import current_user # pylint: disable=E0611,F0401

        # get current user
        if current_user.is_anonymous() == False:

            current_user_id = user_id if user_id else current_user.id

            # user_path
            user_path = os.path.join(dirpath, str(current_user_id))

            # if dir does not exist
            if not(os.path.exists(dirpath)):
                os.makedirs(dirpath)

            # if dir with user id does not exist
            if not(os.path.exists(user_path)):
                os.makedirs(user_path)

            return user_path
    except:
        return dirpath

    return dirpath
