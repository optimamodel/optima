"""
DATAIO

Data input/output. Converts structures to dictionaries so they can be saved by
savemat. Why not use pickle, you ask? Because picke is slow (10x slower for
readout!) and inflexible.

Version: 2014oct29
"""


def savedata(filename, data, update=True):
    from bunch import unbunchify
    from scipy.io import loadmat, savemat
    data = unbunchify(data)
    
    try: # First try loading the file and updating it
        origdata = loadmat(filename)
        if update: origdata.update(data)
        else: origdata = data
        savemat(filename,origdata)
    except: # If that fails, save a new file
        savemat(filename, data)
    
    return None



def loaddata(filename):
    from bunch import bunchify
    from scipy.io import loadmat
    data = loadmat(filename)
    data = bunchify(data)
    return data