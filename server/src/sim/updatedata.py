def updatedata(D, loaddir='', verbose=2):
    """
    Load the Excel spreadsheet (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    
    Version: 2014nov05 by cliffk
    """
    
    from loadspreadsheet import loadspreadsheet
    from makedatapars import makedatapars
    from dataio import savedata
    from printv import printv
    printv('Updating data... %s' % D.projectname, 1, verbose)
    
    D.data, D.programs = loadspreadsheet(D.spreadsheetname, verbose=verbose)
    D = makedatapars(D, verbose=verbose) # Update parameters
    savedata(D.projectfilename, D, verbose=verbose) # Update the data file
    
    printv('  ...done updating data: %s.' % D.projectfilename, 2, verbose)

    return D
