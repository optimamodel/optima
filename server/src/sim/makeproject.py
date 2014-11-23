default_pops = ['General males','General females','Female sex workers','Clients of sex workers', \
'Men who have sex with men','People who inject drugs']

default_progs = ['Behavior change','Female sex workers','Needle-syringe program', \
'Men who have sex with men','HIV counseling & testing','Voluntary male circumcision', \
'Antiretroviral treatment','Prevention of mother-to-child transmission']

def makeproject(projectname='example', pops = default_pops, progs = default_progs, datastart=2000, dataend=2015, \
    econ_datastart=2015, econ_dataend=2030, verbose=2, savetofile = True):
    """
    Initializes the empty project. Only the "Global" parameters are added on this step.
    The rest of the parameters is calculated after the model is updated with the data from the spreadsheet.
    
    Version: 2014nov22 by cliffk
    """
    
    from dataio import savedata, projectpath
    from bunch import Bunch as struct
    from printv import printv

    printv("""Making project %s: 
            pops=%s, progs=%s, datastart = %s, dataend = %s,
            econ_datastart=%s, econ_dataend=%s""" % (projectname, pops, progs, datastart, dataend, econ_datastart, econ_datastart), 1, verbose)

    D = struct() # Data structure for saving everything
    D.__doc__ = 'Data structure for storing everything -- data, parameters, simulation results, velociraptors, etc.'
    D.projectname = projectname
    D.projectfilename = projectpath(projectname+'.prj')
    D.spreadsheetname = projectname + '.xlsx'
    
    # Initialize options
    from setoptions import setoptions
    D.opt = setoptions()
    
    D.G = struct() # "G" for "general parameters"
    D.G.__doc__ = 'General parameters for the model, including the number of population groups, project name, etc.'
    D.G.npops = len(pops)
    D.G.nprogs = len(progs)
    D.G.projectname = projectname
    D.G.datastart = datastart
    D.G.dataend = dataend
    
    if savetofile: #False if we are using database
        savedata(D.projectfilename, D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    
    # Make an Excel template and then prompt the user to save it
    if projectname == 'example': # Don't make a new spreadsheet, but just use the existing one, if the project name is "example"
        print('WARNING, Project name set to "example", not creating a new spreadsheet!')
    else: # Make a new spreadsheet
        from makespreadsheet import makespreadsheet 
        makespreadsheet(D.spreadsheetname, pops, progs, datastart, dataend, econ_datastart, econ_dataend, verbose=verbose)
    
    printv('  ...done making project %s, created spreadsheet %s' % (D.projectname, D.spreadsheetname), 2, verbose)
    return D
