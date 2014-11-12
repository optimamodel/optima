def updatedata(D, loaddir='', verbose=2):
    """
    Load the Excel spreadsheet (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    
    Version: 2014nov05 by cliffk
    """
    
    from loadspreadsheet import loadspreadsheet
    from makedatapars import makedatapars
    from dataio import savedata, fullpath
    from printv import printv
    printv('Updating data... %s with spreadsheet %s' % (D.projectname, D.spreadsheetname), 1, verbose)
    
    datapath = fullpath(D.spreadsheetname)
    D.data, D.programs = loadspreadsheet(datapath, verbose=verbose)
    D = makedatapars(D, verbose=verbose) # Update parameters
    savedata(D.projectfilename, D, verbose=verbose) # Update the data file
    
    printv('  ...done updating data: %s.' % D.projectfilename, 2, verbose)

    return D
