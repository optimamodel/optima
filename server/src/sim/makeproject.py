def makeproject(projectname='example', pops = ['']*6, progs = ['']*5, datastart=2000, dataend=2015, \
    econ_datastart=2000, econ_dataend=2030, nsims=5, verbose=2, savetofile = True):
    """
    Initializes the empty project. Only the "Global" and "Fitted" parameters are added on this step.
    The rest of the parameters are calculated after the model is updated with the data from the workbook.
    
    Version: 2014nov26 by cliffk
    """
    
    from dataio import savedata, projectpath
    from bunch import Bunch as struct
    from printv import printv

    printv('Making project...', 1, verbose)

    D = struct() # Data structure for saving everything
    D.__doc__ = 'Data structure for storing everything -- data, parameters, simulation results, velociraptors, etc.'
    D.plot = struct() # Initialize plotting data
    D.plot.__doc__ = 'Plotting data, including labels, colors, etc., for epidemiology data (E), optimization data (O), and scenario data (S)'
    
    # Initialize options
    from setoptions import setoptions
    D.opt = setoptions(startyear=datastart, endyear=dataend, nsims=nsims)
    
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
    
    # Set up "F" -- fitted parameters structure
    D.F = makefittedpars(D.G, D.opt, verbose=verbose)
    
    if savetofile: #False if we are using database
        savedata(D.G.projectfilename, D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    
    # Make an Excel template and then prompt the user to save it
    if projectname == 'example': # Don't make a new workbook, but just use the existing one, if the project name is "example"
        print('WARNING, Project name set to "example", not creating a new workbook!')
    else: # Make a new workbook
        makeworkbook(D.G.workbookname, pops, progs, datastart, dataend, econ_datastart, econ_dataend, verbose=verbose)
    
    printv('  ...done making project.', 2, verbose)
    return D


def makefittedpars(G, opt, verbose=2):
    """ Prepares fitted parameters for the simulation. """
    
    from printv import printv
    from numpy import array
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    printv('Initializing fitted parameters...', 1, verbose)
    
    # Initialize fitted parameters
    F = [struct() for s in range(opt.nsims)]
    for s in range(opt.nsims):
        span=0 if s==0 else 0.5 # Don't have any variance for first simulation
        F[s].__doc__ = 'Fitted parameters for simulation %i: initial prevalence, force-of-infection, diagnoses, treatment' % s
        F[s].init  = perturb(G.npops,span)
        F[s].force = perturb(G.npops,span)
        F[s].dx  = array([perturb(1,span), perturb(1,span), (G.datastart+G.dataend)/2, 1]).tolist()
    
    return F



def perturb(n=1, span=0.5):
    """ Define an array of numbers uniformly perturbed with a mean of 1. n = number of points; span = width of distribution on either side of 1."""
    from numpy.random import rand
    output = 1 + 2*span*(rand(n)-0.5)
    if n==1: output = output[0] # If scalar, return scalar rather than array
    else: output = output.tolist() # Otherwise, convert to a list
    return output




def makeworkbook(name, pops, progs, datastart=2000, dataend=2015, econ_datastart=2015, econ_dataend=2030, verbose=2):
    """ Generate the Optima workbook -- the hard work is done by makeworkbook.py """
    from printv import printv
    from dataio import templatepath
    from makeworkbook import OptimaWorkbook

    printv("""Generating workbook with parameters:
             name = %s, pops = %s, progs = %s, datastart = %s, dataend = %s, 
             econ_datastart = %s, econ_dataend = %s""" % (name, pops, progs, datastart, dataend, econ_datastart, econ_dataend), 1, verbose)
    path = templatepath(name)
    book = OptimaWorkbook(name, pops, progs, datastart, dataend, econ_datastart, econ_dataend)
    book.create(path)
    
    printv('  ...done making workbook %s.' % path, 2, verbose)
    return path
