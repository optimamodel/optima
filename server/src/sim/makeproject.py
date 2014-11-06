"""
MAKEPROJECT
http://54.200.79.218/#/project/create
Version: 2014nov05 by cliffk
"""
import os

default_pops = ['General males','General females','Female sex workers','Clients of sex workers', \
'Men who have sex with men','People who inject drugs']

default_progs = ['Behavior change','Female sex workers','Needle-syringe program', \
'Men who have sex with men','HIV counseling & testing','Voluntary male circumcision', \
'Antiretroviral treatment','Prevention of mother-to-child transmission']

def makeproject(projectname='example', pops = default_pops, progs = default_progs, datastart=2000, dataend=2015, \
    econ_datastart=2015, econ_dataend=2030, verbose=2):
    """
    Initializes the empty project. Only the "Global" parameters are added on this step.
    The rest of the parameters is calculated after the model is updated with the data from the spreadsheet.
    """
    from matplotlib.pylab import ones, array
    from dataio import savedata, fullpath
    from bunch import Bunch as struct
    from printv import printv

    printv("""Making project %s: 
            pops=%s, progs=%s, datastart = %s, dataend = %s,
            econ_datastart=%s, econ_dataend=%s""" % \
            (projectname, pops, progs, datastart, dataend, econ_datastart, econ_datastart), 1, verbose)

    D = struct() # Data structure for saving everything
    D.projectname = projectname
    D.projectfilename = fullpath(projectname+'.prj')
    #hack for your example, Cliff ;-)
    spreadsheetname = projectname + '.xlsx'
    if not os.path.exists(spreadsheetname):
        spreadsheetname = fullpath(spreadsheetname)
    D.spreadsheetname = spreadsheetname
    D.__doc__ = 'Data structure for storing everything -- data, parameters, simulation results, velociraptors, etc.'
    
    D.G = struct() # "G" for "general parameters"
    D.G.__doc__ = 'General parameters for the model, including the number of population groups, project name, etc.'
    D.G.npops = len(pops)
    D.G.nprogs = len(progs)
    D.G.projectname = projectname
    D.G.datastart = datastart
    D.G.dataend = dataend
    
    # Initialize fitted parameters
    D.F = struct()
    D.F.__doc__ = 'Fitted parameters structure: initial prevalence, force-of-infection, diagnoses, treatment'
    D.F.init = ones(D.G.npops)
    D.F.force = ones(D.G.npops)
    D.F.dx = array([1, 1, (D.G.datastart+D.G.dataend)/2, 1])
    D.F.tx1 = array([1, 1, (D.G.datastart+D.G.dataend)/2, 1])
    D.F.tx2 = array([1, 1, (D.G.datastart+D.G.dataend)/2, 1])    
    
    
    savedata(D.projectfilename, D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    # Make an Excel template and then prompt the user to save it
    from makespreadsheet import makespreadsheet 
    makespreadsheet(D.spreadsheetname, pops, progs, datastart, dataend, econ_datastart, econ_dataend, verbose=verbose)
    
    printv('  ...done making project %s., created spreadsheet %s' % (D.projectname, D.spreadsheetname), 2, verbose)
    return D
