"""
MAKEPROJECT
http://54.200.79.218/#/project/create
Version: 2014oct29
"""

default_pops = ['General males','General females','Female sex workers','Clients of sex workers' \
'Men who have sex with men''People who inject drugs']

default_progs = ['Behavior change','Female sex workers','Needle-syringe program', \
'Men who have sex with men','HIV counseling & testing','Voluntary male circumcision', \
'Antiretroviral treatment','Prevention of mother-to-child transmission']

def makeproject(projectname='example', pops = default_pops, progs = default_progs, datastart=2000, dataend=2015, \
    econ_datastart=2015, econ_dataend=2030, verbose=2):
    """
    Initializes the empty project. Only the "Global" parameters are added on this step.
    The rest of the parameters is calculated after the model is updated with the data from the spreadsheet.
    """
    if verbose>=1: 
        print("""Making project %s: 
            pops=%s, progs=%s, datastart = %s, dataend = %s,
            econ_datastart=%s, econ_dataend=%s""" % \
            (projectname, pops, progs, datastart, dataend, econ_datastart, econ_datastart))
    
    from dataio import savedata, normalize_file
    from bunch import Bunch as struct
    projectfilename = normalize_file(projectname+'.prj')
    spreadsheetname = normalize_file(projectname + '.xlsx')

    npops = len(pops)
    nprogs = len(progs)
    
    D = struct() # Data structure for saving everything
    D.__doc__ = 'Data structure for storing everything -- data, parameters, simulation results, velociraptors, etc.'
    D.G = struct() # "G" for "general parameters"
    D.G.__doc__ = 'General parameters for the model, including the number of population groups, project name, etc.'
    D.G.npops = npops
    D.G.nprogs = nprogs
    D.G.projectname = projectname
    D.G.datastart = datastart
    D.G.dataend = dataend
    result_file_name = savedata(projectfilename, D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
#    return result_file_name
    # Make an Excel template and then prompt the user to save it #TODO #FIXME
    from makespreadsheet import makespreadsheet 
    makespreadsheet(spreadsheetname, pops, progs, datastart, dataend, econ_datastart, econ_dataend, verbose=verbose)
    
    if verbose>=2: print('  ...done making project %s., created spreadsheet %s' \
        % (projectname, spreadsheetname))
    return spreadsheetname