default_pops = ['']*6
default_progs = ['']*7
default_datastart = 2000
default_dataend = 2015
default_nsims = 5

# IMPORTANT: increment this if structure of D changes
current_version = 4

def makeproject(projectname='example', pops = default_pops, progs = default_progs, datastart=default_datastart, \
    dataend=default_dataend, nsims=default_nsims, verbose=2, savetofile = True, domakeworkbook=True):
    """
    Initializes the empty project. Only the "Global" and "Fitted" parameters are added on this step.
    The rest of the parameters are calculated after the model is updated with the data from the workbook.
    
    Version: 2015jan27 by cliffk
    """
    
    from dataio import savedata, projectpath
    from printv import printv
    from numpy import arange
    from copy import deepcopy

    printv('Making project...', 1, verbose)

    D = dict() # Data structure for saving everything
    D['plot'] = dict() # Initialize plotting data
    
    # Initialize options
    from setoptions import setoptions
    D['opt'] = setoptions(nsims=nsims)
    
    # Set up "G" -- general parameters structure
    D['G'] = dict()
    D['G']['version'] = current_version # so that we know the version of new project with regard to data structure
    D['G']['projectname'] = projectname  
    D['G']['projectfilename'] = projectpath(projectname+'.prj')
    D['G']['workbookname'] = D['G']['projectname'] + '.xlsx'
    D['G']['npops'] = len(pops)
    D['G']['nprogs'] = len(progs)
    D['G']['datastart'] = datastart
    D['G']['dataend'] = dataend
    D['G']['datayears'] = arange(D['G']['datastart'], D['G']['dataend']+1)
    D['G']['inputprograms'] = deepcopy(progs) # remember input programs with their possible deviations from standard parameter set (if entered from GUI). 
    # Hate duplicating the data, but can't think of a cleaner way of export/import.
    D['G']['inputpopulations'] = deepcopy(pops) # should be there as well, otherwise we cannot export project without data
    # Health states
    D['G']['healthstates'] = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
    D['G']['ncd4'] = len(D['G']['healthstates'])
    D['G']['nstates'] = 1+D['G']['ncd4']*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
    D['G']['sus']  = arange(0,1)
    D['G']['undx'] = arange(0*D['G']['ncd4']+1, 1*D['G']['ncd4']+1)
    D['G']['dx']   = arange(1*D['G']['ncd4']+1, 2*D['G']['ncd4']+1)
    D['G']['tx1']  = arange(2*D['G']['ncd4']+1, 3*D['G']['ncd4']+1)
    D['G']['fail'] = arange(3*D['G']['ncd4']+1, 4*D['G']['ncd4']+1)
    D['G']['tx2']  = arange(4*D['G']['ncd4']+1, 5*D['G']['ncd4']+1)
    for i,h in enumerate(D['G']['healthstates']): D['G'][h] = [D['G'][state][i] for state in ['undx', 'dx', 'tx1', 'fail', 'tx2']]
    
    if savetofile: #False if we are using database
        savedata(D['G']['projectfilename'], D, verbose=verbose) # Create project -- #TODO: check if an existing project exists and don't overwrite it
    
    # Make an Excel template and then prompt the user to save it
    if projectname == 'example': # Don't make a new workbook, but just use the existing one, if the project name is "example"
        print('WARNING, Project name set to "example", not creating a new workbook!')
    else: # Make a new workbook
        if domakeworkbook:
            makeworkbook(D['G']['workbookname'], pops, progs, datastart, dataend, verbose=verbose)
    
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
