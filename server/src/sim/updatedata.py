"""
UPDATEDATA

Version: 2014oct29
"""

def updatedata(projectname='example'):
    
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    from loadspreadsheet import loadspreadsheet
    from makepars import makepars
    projectfilename = projectname+'.mat'
    spreadsheetname = projectname+'.xlsx'
    data, programs = loadspreadsheet(spreadsheetname)
    G, P = makepars(data)
    
    # Update the data file
    from dataio import savedata
    D = {'data':data, 'programs':programs, 'P':P, 'G':G}
    savedata(projectfilename,D)
    
    return None