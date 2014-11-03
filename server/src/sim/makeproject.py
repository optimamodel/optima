def makeproject(projectname='example', npops=6, nprogs=8, datastart=2000, dataend=2015, loaddir = '', verbose=2):
    """
    Initializes the empty project. Only the "Global" parameters are added on this step.
    The rest of the parameters is calculated after the model is updated with the data from the spreadsheet.
    
    Version: 2014nov03 by cliffk
    """
    if verbose>=1: 
        print("Making project %s, npops=%s, nprogs=%s, datastart = %s, dataend = %s..." % (projectname, npops, nprogs, datastart, dataend))
    
    from dataio import savedata, normalize_file
    from bunch import Bunch as struct
    projectfilename = normalize_file(projectname+'.prj')
    spreadsheetname = projectname + '.xlsx'
    
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
    return result_file_name
    # Make an Excel template and then prompt the user to save it #TODO #FIXME
    from makespreadsheet import makespreadsheet 
    makespreadsheet(spreadsheetname, npops, nprogs, datastart, dataend, verbose=verbose)
    
    if verbose>=2: print('  ...done making project %s., created spreadsheet %s' % (projectname, spreadsheetname))
    return spreadsheetname