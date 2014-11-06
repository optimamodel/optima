"""
DATAIO

Data input/output. Uses pickle because savemat() can't handle arbitrary data
structures, even though savemat() is (much) faster, and the compatibility with
Matlab would be nice.

Version: 2014nov05 by cliffk
"""

from printv import printv
import os

DATADIR="/tmp/uploads"
TEMPLATEDIR = "/tmp/templates"
PROJECTDIR = "/tmp/projects"

def fullpath(filename, datadir=DATADIR):
    """
    "Normalizes" filename:  if it is full path, leaves it alone. Otherwise, prepends it with datadir.
    """
    import os
    result = filename
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
    from cPickle import dump, load
    
    filename = projectpath(filename)
    try: # First try loading the file and updating it
        rfid = open(filename,'rb') # "Read file ID" -- This will fail if the file doesn't exist
        origdata = load(rfid)
        if update: origdata.update(data)
        else: origdata = data
        wfid = open(filename,'wb')
        dump(data, wfid, protocol=-1)
        printv('..updated file', 3, verbose)
    except: # If that fails, save a new file
        wfid = open(filename,'wb')
        dump(data, wfid, protocol=-1)
        printv('..created new file', 3, verbose)
    printv(' ...done saving data at %s.' % filename, 2, verbose)
    return filename




def loaddata(filename, verbose=2):
    """
    Loads the file and unpickles data from it.
    """
    from cPickle import load
    printv('Loading data...', 1, verbose)
    if not os.path.exists(filename):
        filename = projectpath(filename)
    rfid = open(filename,'rb')
    data = load(rfid)
    printv('...done loading data: %s' % data, 2, verbose)
    return data