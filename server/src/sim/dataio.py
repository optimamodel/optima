"""
DATAIO

Data input/output. Converts structures to dictionaries so they can be saved by
savemat. Why not use pickle, you ask? Because picke is slow (10x slower for
readout!) and inflexible.

Version: 2014oct29
"""

import os

DATADIR="/tmp/upload"

def normalize_file(filename):
    result = filename
    if not os.path.exists(DATADIR):
        os.makedirs(DATADIR)
    if os.path.dirname(filename)=='':
        result = os.path.join(DATADIR, filename)
    return result


def savedata(filename, data, update=True, verbose=2):
    if verbose>=1: print('Saving data...')
    from cPickle import dump, load
    
    filename = normalize_file(filename)
    try: # First try loading the file and updating it
        rfid = open(filename,'rb') # "Read file ID" -- This will fail if the file doesn't exist
        origdata = load(rfid)
        if update: origdata.update(data)
        else: origdata = data
        wfid = open(filename,'wb')
        dump(data, wfid, protocol=-1)
        if verbose>=2: print('  ..updated file')
    except: # If that fails, save a new file
        wfid = open(filename,'wb')
        dump(data, wfid, protocol=-1)
        if verbose>=2: print('  ..created new file')
    if verbose>=2: print(' ...done saving data.')
    return filename



def loaddata(filename, verbose=2):
    filename = normalize_file(filename)
    if verbose>=1: print('Loading data...')
    from cPickle import load
    rfid = open(filename,'rb')
    data = load(rfid)
    if verbose>=2: print('  ...done loading data.')
    return data