"""
UPDATEDATA

Version: 2014oct28
"""

def updatedata(projectname='Test', excelfile):
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    from loaddata import loaddata
    from data2pars import data2pars
    data, programs = loaddata(filename)
    P = data2pars(data)
    
    projectdatafilename = projectname + '.mat'
    
    # Save data, programs, and P variables to the appropriate data file   
#    save(projectdatafile, data, programs, P)
    
    # Return the name of the project data file
    
    return projectdatafilename