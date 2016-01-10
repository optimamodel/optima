"""
Functions for running optimizations.
    
Version: 2016jan09 by cliffk
"""

from optima import printv, dcp, asd


def runonebudget():
    return results

def objectivecalc():
    runonebudget()
    return outcome

def minoutcomes(project=None, name=None, parset=None, progset=None, inds=0, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None):
    
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
        
        options = {'pars':pars, 'progs':project.progsets[progset], 'project':project, 'objectives':objectives, 'constraints': constraints}
        budgetvecnew, fval, exitflag, output = asd(errorcalc, budgetvec, options=options, xmin=budgetlower, xmax=budgethigher, timelimit=maxtime, MaxIter=maxiters, verbose=verbose)

    
    return results