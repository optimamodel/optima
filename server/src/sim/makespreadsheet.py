"""
MAKESPREADSHEET

Version: 2014oct28
"""

def makespreadsheet(spreadsheetname, npops=6, nprogs=8, datastart=2000, dataend=2015, verbose=2):
    if verbose>=1: print('Making spreadsheet...')
    
    # Make an Excel template and then prompt the user to save it
    print('      ***Need to actually make spreadsheet here!***')
    
    spreadsheetname = projectname+'.xlsx'
    loadspreadsheet(spreadsheetname)
    if verbose>=2: print('  ...done making spreadsheet.')
    return spreadsheetname