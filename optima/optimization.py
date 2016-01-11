"""
Functions for running optimizations.
    
Version: 2016jan10 by cliffk
"""

from optima import printv, dcp, asd, runmodel


def runonebudget():
    
    return results

def objectivecalc(budgetvec, options):
    parset = options['pars']
    progset = options['progs']
    project = options['project']
    objectives = options['objectives']
    constraints = options['constraints']
    
    # Convert budgetvec to budget
    print('temp')
    
    # Define years
    print('temp')
    year = 2016
    startyear = 2000
    endyear = 2030
    
    thiscoverage = progset.getprogcoverage(budget=budget, t=year, parset=parset)
    thisparset = progset.getparset(coverage=thiscoverage, t=year, parset=parset)
    results = runmodel(pars=thisparset.pars[0], start=startyear, end=endyear, project=project, verbose=0)
    
    # Calculate outcome
    print('temp')
    
    return outcome

def minoutcome(project=None, name=None, parset=None, progset=None, inds=0, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None):
    
    printv('Running outcomes optimization...', 1, verbose)
    
    parset = project.parsets[parset] # Copy the original parameter set
    origparlist = dcp(parset.pars)
    lenparlist = len(origparlist)
    
    if isinstance(inds, (int, float)): inds = [inds] # # Turn into a list if necessary
    if inds is None: inds = range(lenparlist)
    if max(inds)>lenparlist: raise Exception('Index %i exceeds length of parameter list (%i)' % (max(inds), lenparlist+1))
    
    for ind in inds:
        try: pars = origparlist[ind]
        except: raise Exception('Could not load parameters %i from parset %s' % (ind, parset.name))
        
        # Calculate limits
        print('temp')
        
        options = {'pars':pars, 'progs':project.progsets[progset], 'project':project, 'objectives':objectives, 'constraints': constraints}
        budgetvecnew, fval, exitflag, output = asd(objectivecalc, budgetvec, options=options, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)

    
    return results