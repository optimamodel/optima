"""
UPDATEDATA
Upload Optima spreadsheet
Version: 2014oct29
"""

def updatedata(projectname='example', verbose=2):
    
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    if verbose>=1: print('Updating data...')
    
    projectfilename = projectname+'.prj'
    spreadsheetname = projectname+'.xlsx'
    
    from loadspreadsheet import loadspreadsheet
    from makepars import makepars
    from dataio import loaddata, savedata
    
    D = loaddata(projectfilename, verbose=verbose) # Load existing file
    D.data, D.programs = loadspreadsheet(spreadsheetname, verbose=verbose)
    D = makepars(D, verbose=verbose) # Update parameters
    
    savedata(projectfilename, D, verbose=verbose) # Update the data file
    
    if verbose>=2: print('  ...done updating data.')
