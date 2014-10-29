"""
UPDATEDATA

Version: 2014oct29
"""

def updatedata(projectname='example', verbose=2):
    
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    if verbose>=1: print('Updating data...')
    from loadspreadsheet import loadspreadsheet
    from makepars import makepars
    from bunch import Bunch as struct
    projectfilename = projectname+'.prj'
    spreadsheetname = projectname+'.xlsx'
    data, programs = loadspreadsheet(spreadsheetname)
    G, P = makepars(data)
    
    # Update the data file
    from dataio import savedata
    D = struct()
    D.data = data
    D.programs = programs
    D.P = P
    D.G = dict(G) # WARNING KLUDGY
    savedata(projectfilename,D)
    
    if verbose>=2: print('  ...done updating data.')
