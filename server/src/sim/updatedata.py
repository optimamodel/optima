"""
UPDATEDATA
Upload Optima spreadsheet
Version: 2014oct29
"""
import os

def updatedata(projectname='example', loaddir = '', verbose=2):
    
    """
    Load the Excel spreadsheet (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    """
    if verbose>=1: print('Updating data... %s' % projectname)
    
    projectfilename = projectname+'.prj'
    spreadsheetname = projectname+'.xlsx'

    if loaddir:
        projectfilename = os.path.join(loaddir, projectfilename)
        spreadsheetname = os.path.join(loaddir, spreadsheetname)
    
    from loadspreadsheet import loadspreadsheet
    from makedatapars import makedatapars
    from dataio import loaddata, savedata
    
    D = loaddata(projectfilename, verbose=verbose) # Load existing file
    D.data, D.programs = loadspreadsheet(spreadsheetname, verbose=verbose)
    D = makedatapars(D, verbose=verbose) # Update parameters
    
    savedata(projectfilename, D, verbose=verbose) # Update the data file
    
    if verbose>=2: print('  ...done updating data: %s.' % projectfilename)

    return projectfilename
