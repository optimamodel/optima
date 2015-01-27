default_pops = ['']*6
default_progs = ['']*7
default_datastart = 2000
default_dataend = 2015
default_nsims = 5

def makeproject(projectname='example', pops = default_pops, progs = default_progs, datastart=default_datastart, \
    dataend=default_dataend, nsims=default_nsims, verbose=2, savetofile = True):
    """
    Initializes the empty project. Only the "Global" and "Fitted" parameters are added on this step.
    The rest of the parameters are calculated after the model is updated with the data from the workbook.
    
    Version: 2015jan27 by cliffk
    """
    
    from dataio import savedata, projectpath
    from bunch import Bunch as struct
    from printv import printv
    from numpy import arange

    printv('Making project...', 1, verbose)

    D = struct() # Data structure for saving everything
    D.__doc__ = 'Data structure for storing everything -- data, parameters, simulation results, velociraptors, etc.'
    D.plot = struct() # Initialize plotting data
    D.plot.__doc__ = 'Plotting data, including labels, colors, etc., for epidemiology data (E), optimization data (O), and scenario data (S)'
    
    # Initialize options
    from setoptions import setoptions
    D.opt = setoptions(nsims=nsims)
    
    # Set up "G" -- general parameters structure
    D.G = struct()
    D.G.__doc__ = 'General parameters for the model, including the number of population groups, project name, etc.'
    D.G.projectname = projectname  
    D.G.projectfilename = projectpath(projectname+'.prj')
    D.G.workbookname = D.G.projectname + '.xlsx'
    D.G.npops = len(pops)
    D.G.nprogs = len(progs)
    D.G.datastart = datastart
    D.G.dataend = dataend
    D.G.datayears = arange(D.G.datastart, D.G.dataend+1)
    
    # Health states
    D.G.healthstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
    D.G.ncd4 = len(D.G.healthstates)
    D.G.nstates = 1+D.G.ncd4*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
    D.G.sus  = arange(0,1)
    D.G.undx = arange(0*D.G.ncd4+1, 1*D.G.ncd4+1)
    D.G.dx   = arange(1*D.G.ncd4+1, 2*D.G.ncd4+1)
    D.G.tx1  = arange(2*D.G.ncd4+1, 3*D.G.ncd4+1)
    D.G.fail = arange(3*D.G.ncd4+1, 4*D.G.ncd4+1)
    D.G.tx2  = arange(4*D.G.ncd4+1, 5*D.G.ncd4+1)
    for i,h in enumerate(D.G.healthstates): D.G[h] = [D.G[state][i] for state in ['undx', 'dx', 'tx1', 'fail', 'tx2']]
    # Q:should econ_dataend also be saved somewhere?
    
    if savetofile: #False if we are using database
        savedata(D.G.projectfilename, D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    
    # Make an Excel template and then prompt the user to save it
    if projectname == 'example': # Don't make a new workbook, but just use the existing one, if the project name is "example"
        print('WARNING, Project name set to "example", not creating a new workbook!')
    else: # Make a new workbook
        makeworkbook(D.G.workbookname, pops, progs, datastart, dataend, verbose=verbose)
    
    printv('  ...done making project.', 2, verbose)
    return D


def makeworkbook(name, pops, progs, datastart=default_datastart, dataend=default_dataend, verbose=2):
    """ Generate the Optima workbook -- the hard work is done by makeworkbook.py """
    from printv import printv
    from dataio import templatepath
    from makeworkbook import OptimaWorkbook

    printv("""Generating workbook with parameters:
             name = %s, pops = %s, progs = %s, datastart = %s, dataend = %s""" \
             % (name, pops, progs, datastart, dataend), 1, verbose)
    path = templatepath(name)
    book = OptimaWorkbook(name, pops, progs, datastart, dataend)
    book.create(path)
    
    printv('  ...done making workbook %s.' % path, 2, verbose)
    return path
