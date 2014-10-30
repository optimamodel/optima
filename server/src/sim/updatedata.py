"""
UPDATEDATA
Upload Optima spreadsheet
Version: 2014oct29
"""
import os

def updatedata(projectname='example', loaddir = '', verbose=2):
    
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    if verbose>=1: print('Updating data... %s' % projectname)
    
    projectfilename = projectname+'.prj'
    spreadsheetname = projectname+'.xlsx'

    if loaddir:
        projectfilename = os.join(loaddir, projectfilename)
        spreadsheetname = os.join(loaddir, spreadsheetname)
    
    from loadspreadsheet import loadspreadsheet
    from makepars import makepars
    from dataio import loaddata, savedata
    
    D = loaddata(projectfilename, verbose=verbose) # Load existing file
    D.data, D.programs = loadspreadsheet(spreadsheetname, verbose=verbose)
    D = makepars(D, verbose=verbose) # Update parameters
    
    savedata(projectfilename, D, verbose=verbose) # Update the data file
    
    if verbose>=2: print('  ...done updating data: %s.' % projectfilename)

    return projectfilename
