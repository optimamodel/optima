from copy import deepcopy

def updatedata(D, workbookname=None, verbose=2, savetofile=True, input_programs=None, rerun=True):
    """
    Load the Excel workbook (for the given project), assuming it's in the standard uploads directory
    loads the data for the given project,
    updates the model based on the speardsheet contents
    programs - set up in GUI, contain information about the (adjusted) programs and parameters for the given project
    
    Version: 2015jan19 by cliffk
    """
    
    from loadworkbook import loadworkbook
    from makedatapars import makedatapars
    from makemodelpars import makemodelpars
    from runsimulation import runsimulation
    from dataio import savedata, fullpath
    from printv import printv
    printv('Updating data...', 1, verbose)
    
    if workbookname is None:
        workbookname = D['G']['workbookname']
        
    datapath = fullpath(workbookname)
    data, programs = loadworkbook(datapath, input_programs, verbose=verbose)
    D['data'] = getrealcosts(data)
    if 'programs' not in D:
        D['programs'] = addtoprograms(programs)
    if rerun or 'P' not in D: # Rerun if asked or if it doesn't exist
        D = makedatapars(D, verbose=verbose) # Update parameters
    if rerun or 'M' not in D: # Rerun if asked, or if it doesn't exist
        D['M'] = makemodelpars(D['P'], D['opt'], verbose=verbose)
    if 'F' not in D: # Only rerun if it doesn't exist
        D = makefittedpars(D, verbose=verbose)
    elif 'F' in D and len(D['F'])==1:
        D['F'][0]['popsize'] = [D['M']['popsize'][p][0] for p in range(D['G']['npops'])]
    if rerun or 'R' not in D: # Rerun if asked, or if no results
        D = runsimulation(D, makeplot = 0, dosave = False)
    if savetofile:
        savedata(D['G']['projectfilename'], D, verbose=verbose) # Update the data file
    
    printv('...done updating data.', 2, verbose)

    return D
    

def addtoprograms(programs):
    ''' Add things to D['programs'] '''
    for prognumber, program in enumerate(programs):
        programs[prognumber]['ccparams'] = {'saturation': None, 
                                            'coveragelower': None, 
                                            'coverageupper':None, 
                                            'funding':None, 
                                            'scaleup':None, 
                                            'nonhivdalys':None,
                                            'xupperlim':None,
                                            'cpibaseyear':None, 
                                            'perperson':None}
        programs[prognumber]['convertedccparams'] = None
        programs[prognumber]['nonhivdalys'] = 0.0
        
        if program['name'] == 'VMMC':
            program['effects'] = [{'paramtype':'sex', 'param':'numcircum', 'popname':u'Total', 'coparams':None, 'convertedcoparams':None, 'convertedccoparams':None}]

    return programs
    
    
    
def getrealcosts(data):
    '''
    Add inflation-adjsted costs to data structure
    '''

    import math
    import numpy
    from datetime import date
    from utils import smoothinterp, sanitize

    cost = data['costcov']['cost']
    nprogs = len(data['costcov']['cost'])
    realcost = [[]]*nprogs

    # Get CPI, expand to all years
    cpi = sanitize(data['econ']['cpi']['past'][0])
    if len(cpi)<len(data['epiyears']): # Only interpolate if there's missing data
        cpi = smoothinterp(newx=data['epiyears'], origx=data['epiyears'], origy=data['econ']['cpi']['past'][0], growth=data['econ']['cpi']['future'][0][0])

    # Set the CPI base year to the current year or the last year for which data were provided.
    cpibaseyearindex = data['epiyears'].index(min(data['epiyears'][-1],date.today().year))

    for prog in xrange(nprogs):
        if len(cost[prog])==1: # If it's an assumption, assume it's already in current prices
            realcost[prog] = cost[prog]
        else:
            realcost[prog] = [cost[prog][j]*(cpi[cpibaseyearindex]/cpi[j]) if ~math.isnan(cost[prog][j]) else float('nan') for j in xrange(len(cost[prog]))]

        # Origalloc should also use inflation-adjusted figures
        temp_cost = numpy.array(realcost[prog])[:cpibaseyearindex]
        temp_cost = temp_cost[~numpy.isnan(temp_cost)]
        try:
            temp_cost = temp_cost[-1]
        except:
            print('WARNING, no cost data entered for %s' % data['meta']['progs']['short'][prog])
            temp_cost = 0 # No data entered for this program
        data['origalloc'][prog] = temp_cost
    
    data['costcov']['realcost'] = realcost
    
    return data



def makefittedpars(D, verbose=2):
    """ Prepares fitted parameters for the simulation. """
    
    from printv import printv
    from utils import perturb
    from numpy import zeros
    printv('Initializing fitted parameters...', 1, verbose)
    
    # Initialize fitted parameters
    D['F'] = [dict() for s in xrange(D['opt']['nsims'])]
    for s in xrange(D['opt']['nsims']):
        span=0 if s==0 else 0.5 # Don't have any variance for first simulation
        D['F'][s]['init']  = perturb(D['G']['npops'],span)
        D['F'][s]['popsize'] = perturb(D['G']['npops'],span)
        D['F'][s]['force'] = perturb(D['G']['npops'],span)
        D['F'][s]['inhomo'] = zeros(D['G']['npops']).tolist()
        D['F'][s]['dx']  = perturb(4,span)
        D['F'][s] = unnormalizeF(D['F'][s], D['M'], D['G'], normalizeall=True) # Un-normalize F
    
    return D


def unnormalizeF(normF, M, G, normalizeall=False):
    """ Convert from F values where everything is 1 to F values that can be real-world interpretable. """
    unnormF = deepcopy(normF)
    for p in xrange(G['npops']):
        unnormF['init'][p] *= M['hivprev'][p] # Multiply by initial prevalence
        if normalizeall: unnormF['popsize'][p] *= M['popsize'][p][0] # Multiply by initial population size
    if normalizeall: unnormF['dx'][2] += G['datayears'].mean()-1 # Add mean data year
    return unnormF


def normalizeF(unnormF, M, G, normalizeall=False):
    """ Convert from F values that can be real-world interpretable to F values where everything is 1. """
    normF = deepcopy(unnormF)
    for p in xrange(G['npops']):
        normF['init'][p] /= M['hivprev'][p] # Divide by initial prevalence
        if normalizeall: normF['popsize'][p] /= M['popsize'][p][0] # Divide by initial population size
    if normalizeall: normF['dx'][2] -= G['datayears'].mean()+1 # Subtract mean data year
    return normF





