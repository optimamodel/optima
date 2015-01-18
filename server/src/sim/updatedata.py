def updatedata(D, verbose=2, savetofile = True):
    """
    Load the Excel workbook (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    
    Version: 2014nov24 by cliffk
    """
    
    from loadworkbook import loadworkbook
    from makedatapars import makedatapars
    from dataio import savedata, fullpath
    from printv import printv
    printv('Updating data...', 1, verbose)
    
    datapath = fullpath(D.G.workbookname)
    D.data, D.programs = loadworkbook(datapath, verbose=verbose)
    D.programs = restructureprograms(D.programs)
    D.data = getrealcosts(D.data)
    D = makedatapars(D, verbose=verbose) # Update parameters
    if savetofile:
        savedata(D.G.projectfilename, D, verbose=verbose) # Update the data file
    
    printv('...done updating data.', 2, verbose)

    return D
    

def restructureprograms(programs):
    '''
    Restructure D.programs for easier use.
    '''

    ccparams = []
    convertedccparams = []
    nonhivdalys = [0.0]
    keys = ['ccparams','convertedccparams','nonhivdalys','effects']
    for program in programs.keys():
        programs[program] = dict(zip(keys,[ccparams, convertedccparams, nonhivdalys, programs[program]]))
    
    return programs
    
def getrealcosts(data):
    '''
    Add inflation-adjsted costs to data structure
    '''

    from math import isnan

    cost = data.costcov.cost
    nprogs = len(data.costcov.cost)
    realcost = [[]]*nprogs
    cpi = data.econ.cpi[0] # get CPI
    cpibaseyearindex = data.econyears.index(data.epiyears[-1])
    for prog in range(nprogs):
        if len(cost[prog])==1: # If it's an assumption, assume it's already in current prices
            realcost[prog] = cost[prog]
        else:
            realcost[prog] = [cost[prog][j]*(cpi[cpibaseyearindex]/cpi[j]) if ~isnan(cost[prog][j]) else float('nan') for j in range(len(cost[prog]))]
    
    data.costcov.realcost = realcost
    
    return data




