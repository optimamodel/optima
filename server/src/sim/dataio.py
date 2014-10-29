"""
DATAIO

Data input/output. Converts structures to dictionaries so they can be saved by
savemat. Why not use pickle, you ask? Because picke is slow (10x slower for
readout!) and inflexible.

Version: 2014oct29
"""

def savedata(filename, data):
    from bunch import Bunch as struct, unbunchify
    from scipy.io import savemat
    if type(data)==type(struct()): unbunchify(data)
    
    # KLUDGY -- recursively iterate over items, converting any found dictionaries to structures, up to 3 levels
    if iterable(data):
        for item1 in data:
            if type(data[item1])==type(struct()): data[item1] = dict(data[item1])
            if iterable(data[item1]):
                for item2 in data[item1]:
                    if type(data[item1][item2])==type(struct()): data[item1][item2] = dict(data[item1][item2])
                    if iterable(data[item1][item2]):
                        for item3 in data[item1][item2]:
                            if type(data[item1][item2][item3])==type(struct()): data[item1][item2][item3] = dict(data[item1][item2][item3])
                            if iterable(data[item1][item2][item3]):
                                raise Exception('Only 3 levels of recursion currently supported!')
    
    savemat(filename,data)
    return None

def loaddata(filename):
    from matplotlib.pylab import iterable
    from bunch import Bunch as struct
    from scipy.io import loadmat
    data = loadmat(filename)
    if type(data)==type(dict()): data = struct(data)
    
    # KLUDGY -- recursively iterate over items, converting any found dictionaries to structures, up to 3 levels
    if iterable(data):
        for item1 in data:
            if type(data[item1])==type(dict()): data[item1] = struct(data[item1])
            if iterable(data[item1]):
                for item2 in data[item1]:
                    if type(data[item1][item2])==type(dict()): data[item1][item2] = struct(data[item1][item2])
                    if iterable(data[item1][item2]):
                        for item3 in data[item1][item2]:
                            if type(data[item1][item2][item3])==type(dict()): data[item1][item2][item3] = struct(data[item1][item2][item3])
                            if iterable(data[item1][item2][item3]):
                                raise Exception('Only 3 levels of recursion currently supported!')
            
    return data