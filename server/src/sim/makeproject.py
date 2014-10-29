"""
MAKEPROJECT

Version: 2014oct29
"""

def makeproject(projectname='example', npops=6, nprogs=8, datastart=2000, dataend=2015):
    
    from dataio import savedata
    from bunch import Bunch as struct
    projectfilename = projectname+'.prj'
    
    G = struct() # "G" for "general parameters"
    G.npops = npops
    G.nprogs = nprogs
    G.projectname = projectname
    G.datastart = datastart
    G.dataend = dataend
    savedata(projectfilename, G) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    
    # Make an Excel template and then prompt the user to save it
    from makespreadsheet import makespreadsheet
    spreadsheetname = makespreadsheet(projectname, npops, nprogs, datastart, dataend)
    
    return spreadsheetname