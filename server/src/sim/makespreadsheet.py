"""
MAKESPREADSHEET

Version: 2014oct28
"""

from optima_workbook import OptimaWorkbook

def generate_spreadsheet(path, npops=6, nprogs=8, datastart=2000, dataend=2015, verbose=2):
  if verbose >=1: 
    print("""Generating spreadsheet with parameters:
             path = %s, npops = %s, nprogs = %s, datastart = %s, dataend = %s""" % \
             (path, npops, nprogs, datastart, dataend))
    (folder, name) = os.path.split(path)
    book = OptimaWorkbook(name, npops, nprogs, datastart, dataend)
    book.create(path)


def makespreadsheet(spreadsheetname, npops=6, nprogs=8, datastart=2000, dataend=2015, verbose=2):
    if verbose>=1: print('Making spreadsheet...')
    
    # Make an Excel template and then prompt the user to save it
    print('      ***Need to actually make spreadsheet here!***')
    
    spreadsheetname = projectname+'.xlsx'
    loadspreadsheet(spreadsheetname)
    if verbose>=2: print('  ...done making spreadsheet.')
    return spreadsheetname