## Imports
from numpy import append, array
from optima import OptimaException, dcp, today, odict, printv, findinds, runmodel, Multiresultset, defaultrepr, getresults, vec2budget #, sanitize, uuid, getdate, smoothinterp



class Scen(object):
    ''' The scenario base class -- not to be used directly, instead use Parscen or Progscen '''
    def __init__(self, name=None, parsetname=None, t=None, active=True):
        self.name = name
        self.parsetname = parsetname
        self.t = t
        self.active = active
        self.resultsref = None
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output

    def getresults(self):
        ''' Returns the results '''
        if self.resultsref is not None and self.project is not None:
            results = getresults(project=self.project, pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this scenario')
    
    

class Parscen(Scen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, pars=None, **defaultargs):
        Scen.__init__(self, **defaultargs)
        self.pars = pars



class Progscen(Scen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, progsetname=None, **defaultargs):
        Scen.__init__(self, **defaultargs)
        self.progsetname = progsetname # Programset


class Budgetscen(Progscen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, budget=None, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.budget = budget


class Coveragescen(Progscen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, coverage=None, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.coverage = coverage


def runscenarios(project=None, verbose=2, defaultparset=0):
    """
    Run all the scenarios.
    Version: 2016jan22 by cliffk
    """
    
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if project is None: raise OptimaException('First argument to runscenarios() must be a project')
    if len(project.scens)==0:  # Create scenario list if not existing
        defaultscens = defaultscenarios(project.parsets[defaultparset], verbose=verbose)
        project.addscenlist(defaultscens)
    scenlist = [scen for scen in project.scens.values() if scen.active==True]
    nscens = len(scenlist)
    
    # Convert the list of scenarios to the actual parameters to use in the model
    scenparsets = makescenarios(project=project, scenlist=scenlist, verbose=verbose)

    # Run scenarios
    allresults = []
    for scenno, scen in enumerate(scenparsets):
        budget = scenlist[scenno].budget if isinstance(scenlist[scenno], Progscen) else None
        coverage = scenlist[scenno].coverage if isinstance(scenlist[scenno], Progscen) else None
        budgetyears = scenlist[scenno].t if isinstance(scenlist[scenno], Progscen) else None
        progset = project.progsets[scenlist[scenno].progsetname] if isinstance(scenlist[scenno], Progscen) else None
        result = runmodel(pars=scenparsets[scen].pars[0], parset=project.parsets[scenlist[scenno].parsetname], progset=progset, project=project, budget=budget, coverage=coverage, budgetyears=budgetyears, verbose=1)
        allresults.append(result) 
        allresults[-1].name = scenlist[scenno].name # Give a name to these results so can be accessed for the plot legend
        printv('Scenario: %i/%i' % (scenno+1, nscens), 2, verbose)
    
    multires = Multiresultset(resultsetlist=allresults, name='scenarios')
    for scen in scenlist: scen.resultsref = multires.uid # Copy results into each scenario that's been run
    
    printv('...done running scenarios.', 2, verbose)
    return multires





def makescenarios(project=None, scenlist=None, verbose=2):
    """ Convert dictionary of scenario parameters into parset to model parameters """

    scenparsets = odict()
    for scenno, scen in enumerate(scenlist):
        
        try: thisparset = dcp(project.parsets[scen.parsetname])
        except: raise OptimaException('Failed to extract parset "%s" from this project:\n%s' % (scen.parsetname, project))
        thisparset.modified = today()
        thisparset.name = scen.name
        npops = len(thisparset.popkeys)


        if isinstance(scen,Parscen):
            for pardictno in range(len(thisparset.pars)): # Loop over all parameter sets
                for par in scenlist[scenno].pars: # Loop over all parameters being changed
                    thispar = thisparset.pars[pardictno][par['name']]
                    if type(par['for'])==tuple: # If it's a partnership...
                        par2 = (par['for'][1],par['for'][0])
                        pops = [par['for'], par2] # This is confusing - for partnership parameters, pops is a list of the two different partnership orderings.
                    elif type(par['for'])==int: #... if its a population.
                        pops = range(npops) if par['for'] > npops else [par['for']]
                    elif type(par['for'])==list: #... if its a population.
                        pops = par['for']
                    else: 
                        errormsg = 'Unrecognized population or partnership type.'
                        raise OptimaException(errormsg)
                    for pop in pops:
                        if par['startyear'] < max(thispar.t[pop]):
                            thispar.t[pop] = thispar.t[pop][thispar.t[pop] < par['startyear']]
                            thispar.y[pop] = thispar.y[pop][thispar.t[pop] < par['startyear']]
                        thispar.t[pop] = append(thispar.t[pop], par['startyear'])
                        thispar.y[pop] = append(thispar.y[pop], par['startval']) 
                        if par['endyear']: # Add end year values if supplied
                            thispar.t[pop] = append(thispar.t[pop], par['endyear'])
                            thispar.y[pop] = append(thispar.y[pop], par['endval'])
    
        elif isinstance(scen,Progscen):

            try: thisprogset = dcp(project.progsets[scen.progsetname])
            except: raise OptimaException('Failed to extract progset "%s" from this project:\n%s' % (scen.progset, project))
            
            try: results = project.parsets[scen.parsetname].getresults() # See if there are results already associated with this parset
            except:
                results = None

            if isinstance(scen.t,(int,float)): scen.t = [scen.t]

            if isinstance(scen, Budgetscen):
                
                # If the budget has been passed in as a vector, convert it to an odict & sort by program names
                if isinstance(scen.budget, list) or isinstance(scen.budget,type(array([]))):
                    scen.budget = vec2budget(scen.progset, scen.budget) # It seems to be a vector: convert to odict
                if not isinstance(scen.budget,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
                if not isinstance(scen.budget,odict): scen.budget = odict(scen.budget)
                scen.budget = scen.budget.sort([p.short for p in thisprogset.programs.values()]) # Re-order to preserve ordering of programs

                # Ensure budget values are lists
                for budgetkey, budgetentry in scen.budget.iteritems():
                    if isinstance(budgetentry,(int,float)):
                        scen.budget[budgetkey] = [budgetentry]

                # Figure out coverage
                scen.coverage = thisprogset.getprogcoverage(budget=scen.budget, t=scen.t, parset=thisparset, results=results)

            elif isinstance(scen, Coveragescen):

                # If the coverage levels have been passed in as a vector, convert it to an odict & sort by program names
                if isinstance(scen.coverage, list) or isinstance(scen.coverage, type(array([]))):
                    scen.coverage = vec2budget(scen.progset, scen.coverage) # It seems to be a vector: convert to odict
                if not isinstance(scen.coverage,dict): raise OptimaException('Currently only accepting coverage as dictionaries.')
                if not isinstance(scen.coverage,odict): scen.coverage = odict(scen.coverage)
                scen.coverage = scen.coverage.sort([p.short for p in thisprogset.programs.values()]) # Re-order to preserve ordering of programs

                # Ensure coverage level values are lists
                for covkey, coventry in scen.coverage.iteritems():
                    if isinstance(coventry,(int,float)):
                        scen.coverage[covkey] = [coventry]

                # Figure out coverage
                scen.budget = thisprogset.getprogbudget(coverage=scen.coverage, t=scen.t, parset=thisparset, results=results)

            thisparsdict = thisprogset.getpars(coverage=scen.coverage, t=scen.t, parset=thisparset, results=results)
            scen.pars = thisparsdict
            for pardictno in range(len(thisparset.pars)): # Loop over all parameter dictionaries
                thisparset.pars[pardictno] = thisparsdict

        else: 
            errormsg = 'Unrecognized program scenario type.'
            raise OptimaException(errormsg)
            

        scenparsets[scen.name] = thisparset

    return scenparsets





def defaultscenarios(parset=None, verbose=2):
    """ Define a list of default scenarios -- only "Current conditions" by default """
    if parset is None: raise OptimaException('You need to supply a parset to generate default scenarios')
    
    scenlist = [Parscen()]
    
    ## Current conditions
    scenlist[0].name = 'Current conditions'
    scenlist[0].parset = parset
    scenlist[0].pars = [] # No changes
    
    return scenlist



def getparvalues(parset, par):
    """
    Return the default parameter values from simpars for a given par. -- WARNING, shouldn't this be a method of Par?
    
    defaultvals = getparvalues(parset, scenariolist[1]['pars'][2])
    """
    npops = len(parset.pars[0]['popkeys'])
    simpars = parset.interp(start=par['startyear'], end=par['endyear'])

    original = simpars[par['names'][0]]
    
    if par['pops'] < npops: # It's for a specific population, get the value
        original = original[par['pops'],:]
    else:
        original = original[:,:].mean(axis=0)
    initialindex = findinds(simpars['tvec'],par['startyear'])
    finalindex = findinds(simpars['tvec'],par['endyear'])

    startval = original[initialindex][0]
    endval = original[finalindex][0]
    return [startval, endval]
        



