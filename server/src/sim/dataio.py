"""
DATAIO

Data input/output. Converts structures to dictionaries so they can be saved by
savemat. Why not use pickle, you ask? Because picke is slow (10x slower for
readout!) and inflexible.

Version: 2014oct29
"""



def savedata(filename, data, update=True, verbose=1):
    if verbose>=1: print('Saving data...')
    from cPickle import dump, load
    fid = open(filename,'wb')
    
    try: # First try loading the file and updating it
        fid2 = open(filename,'rb')
        origdata = load(fid2)
        if update: 
            origdata.update(data)
        else: 
            origdata = data
        dump(data, fid, protocol=-1)
    except: # If that fails, save a new file
        if verbose>=1: print('  Creating new file')
        dump(data, fid, protocol=-1)
    if verbose>=1: print(' ...done saving data.')




def loaddata(filename, verbose=1):
    if verbose>=1: print('Loading data...')
    from cPickle import load
    fid = open(filename,'rb')
    data = load(fid)
    if verbose>=1: print('  ...done loading data.')
    return data