def updatedata(D, verbose=2, savetofile = True):
    """
    Load the Excel workbook (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    
    Version: 2014nov24 by cliffk
    """
    
    from loadworkbook import loadworkbook
    from makeccocs import restructureprograms
    from makedatapars import makedatapars
    from dataio import savedata, fullpath
    from printv import printv
    printv('Updating data...', 1, verbose)
    
    datapath = fullpath(D.G.workbookname)
    D.data, D.programs = loadworkbook(datapath, verbose=verbose)
    D.programs = restructureprograms(D.programs)
    D = makedatapars(D, verbose=verbose) # Update parameters
    if savetofile:
        savedata(D.G.projectfilename, D, verbose=verbose) # Update the data file
    
    printv('...done updating data.', 2, verbose)

    return D