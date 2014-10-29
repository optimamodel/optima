"""
UPDATEDATA

Version: 2014oct28
"""

def updatedata(projectname='example'):
    
    # Load the Excel spreadsheet, read it in (via loaddata.py), and save it somewhere
    from loaddata import loaddata
    from data2pars import data2pars
    projectfilename = projectname+'.mat'
    templatename = projectname+'.xlsx'
    data, programs = loaddata(templatename)
    P = data2pars(data)
    
    # Update the data file
    from scipy.io import savemat, loadmat
    D = loadmat(projectfilename)
    D.update({'data':data, 'programs':programs, 'P':P})
    savemat(projectfilename,D)
    
    # Rerun the simulation
    from runsimulation import runsimulation
    runsimulation(projectfilename)
    
    return None