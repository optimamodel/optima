"""
RUNSIMULATION

Version: 2014oct29



"""

#def runsimulation(projectdatafile='example.mat', endyear=2030):
    
# For troubleshooting
if 1:
    projectdatafile = 'example.mat'
    endyear = 2030
    
    # The project data file name needs to be 
    from dataio import loaddata, savedata
    D = loaddata(projectdatafile)
    
    from model import model
    model(D.G,D.P)