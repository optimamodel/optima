"""
UPDATEDATA

Version: 2014oct28
"""

def updatedata(projectname='example'):
    
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    from loaddata import loaddata
    from makepars import makepars
    projectfilename = projectname+'.mat'
    templatename = projectname+'.xlsx'
    data, programs = loaddata(templatename)
    G, P = makepars(data)
    
    # Update the data file
    from scipy.io import savemat, loadmat
    D = loadmat(projectfilename)
    D.update({'data':data, 'programs':programs, 'P':P, 'G':G})
    savemat(projectfilename,D)
    
    return None