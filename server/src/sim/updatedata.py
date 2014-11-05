def updatedata(D, loaddir='', verbose=2):
    """
    Load the Excel spreadsheet (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    
    Version: 2014nov03 by cliffk
    """
    
    if verbose>=1: print('Updating data... %s' % D.projectname)
    
    from loadspreadsheet import loadspreadsheet
    from makedatapars import makedatapars
    from dataio import savedata
    
    D.data, D.programs = loadspreadsheet(D.spreadsheetname, verbose=verbose)
    D = makedatapars(D, verbose=verbose) # Update parameters
    
    savedata(D.projectfilename, D, verbose=verbose) # Update the data file
    
    if verbose>=2: print('  ...done updating data: %s.' % D.projectfilename)

    return D
