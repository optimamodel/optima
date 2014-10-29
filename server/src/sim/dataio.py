"""
DATAIO

Data input/output. Converts structures to dictionaries so they can be saved by
savemat. Why not use pickle, you ask? Because picke is slow (10x slower for
readout!) and inflexible.

Version: 2014oct29
"""

def savedata(filename, data):
    from bunch import Bunch as unbunchify
    from scipy.io import savemat
    data = unbunchify(data)
    savemat(filename,data)
    return None

def loaddata(filename):
    from bunch import bunchify
    from scipy.io import loadmat
    data = loadmat(filename)
    data = bunchify(data)
    return data