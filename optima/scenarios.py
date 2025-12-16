'''
Define classes and functions for handling scenarios and ICERs.

Version: 2017jun03
'''

## Imports
from numpy import append, array, inf
from optima import OptimaException, Link, Multiresultset, Timepar, Popsizepar # Core classes/functions
from optima import parallelpool, dcp, today, odict, printv, findinds, defaultrepr, getresults, vec2obj, isnumber, uuid, promotetoarray, cpu_count # Utilities
from optima import checkifparsetoverridesprogset, checkifparsoverridepars, createwarningforoverride # From programs.py and parameters.py for warning
from sciris import parallelize
from numpy import ceil

__all__ = [
    'Parscen',
    'Budgetscen',
    'Coveragescen',
    'Progscen',
    'runscenarios',
    'makescenarios',
    'baselinescenario',
    'setparscenvalues',
    'defaultscenarios',
    'checkifparsetoverridesscenario'
]

class Scen(object):
    ''' The scenario base class -- not to be used directly, instead use Parscen or Progscen '''
    def __init__(self, name=None, parsetname=-1, progsetname=-1, t=None, active=True):
        self.uid = uuid()
        self.name = name
        self.parsetname  = parsetname
        self.progsetname = progsetname
        self.t = t
        self.active = active
        self.resultsref = None
        self.scenparset = None # Store the actual parset generated
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output

    def getresults(self):
        ''' Returns the results '''
        if self.resultsref is not None and self.projectref() is not None:
            results = getresults(project=self.projectref(), pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this scenario')
    
    

class Parscen(Scen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, pars=None, **defaultargs):
        Scen.__init__(self, **defaultargs)
        if pars is None: pars = []
        self.pars = pars



class Progscen(Scen):
    ''' The program scenario base class -- not to be used directly, instead use Budgetscen or Coveragescen '''
    def __init__(self, progsetname=-1, **defaultargs):
        Scen.__init__(self, **defaultargs)
        self.progsetname = progsetname # Programset


class Budgetscen(Progscen):
    ''' Stores a single budget scenario. Initialised with a budget. Coverage added during makescenarios()'''
    def __init__(self, budget=None, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.budget = budget


class Coveragescen(Progscen):
    ''' Stores a single coverage scenario. Initialised with a coverage. Budget added during makescenarios()'''
    def __init__(self, coverage=None, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.coverage = coverage

def runsim_wrapper(project, print_label, verbose=2, **kwargs):
    printv(print_label, 2, verbose)
    return project.runsim(verbose=0, **kwargs)

def runscenarios(project=None, verbose=2, name=None, defaultparset=-1, debug=False, nruns=None, base=None, ccsample=None,
                 randseed=None, parallel=False, ncpus=None, keepresultsetlist=False, **kwargs):
    """
    Run all the scenarios.
    Version: 2017aug15
    """
    
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if project is None: raise OptimaException('First argument to runscenarios() must be a project')
    if len(project.scens)==0:  # Create scenario list if not existing
        baselinescen = baselinescenario(project.parsets[defaultparset], verbose=verbose)
        project.addscens(baselinescen)
    scenlist = [scen for scen in project.scens.values() if scen.active==True]
    nscens = len(scenlist)
    
    # Handle inputs
    if ccsample is None: ccsample = 'best' 
    if nruns is None:    nruns = 1
    if base is None:     base = 0
    if ncpus is None:    ncpus = int(ceil( cpu_count()/2 ))
    # We run in a parallel here if the number of scenarios is more than the number of runs per scenario (nruns)
    this_parallel = True if (parallel and nscens > nruns) else False
    parallel = parallel and (not this_parallel)  # Allowed to run in parallel and we are not running here in parallel
    parallelizer = parallelpool(ncpus).map if parallel else None

    if this_parallel:
        project_copy = project.cp(movelinks=False)
        project_copy.parsets  = odict()
        project_copy.progsets = odict()
        project_copy.scens    = odict()
        project_copy.optims   = odict()
        project_copy.results  = odict()
        project_copy = dcp(project_copy)

    # Convert the list of scenarios to the actual parameters to use in the model
    scenparsets = makescenarios(project=project, scenlist=scenlist, ccsample=ccsample, randseed=randseed, verbose=verbose)        

    # Run scenarios
    all_kwargs = [None] * nscens
    for scenno, scen in enumerate(scenparsets):
        scenparset = scenparsets[scen]
        project.scens[scenparsets.keys()[scenno]].scenparset = scenparset # Copy into scenarios objects

        # Items specific to program (budget or coverage) scenarios
        budget = scenlist[scenno].budget if isinstance(scenlist[scenno], Progscen) else None
        coverage = scenlist[scenno].coverage if isinstance(scenlist[scenno], Progscen) else None
        budgetyears = scenlist[scenno].t if isinstance(scenlist[scenno], Progscen) else None
        progsetname = scenlist[scenno].progsetname if isinstance(scenlist[scenno], Progscen) else None

        if this_parallel: # Create a specific copy, simply for speed of pickling which is part of the process running in parallel.
            this_project = dcp(project_copy)
            scenparset.pars.func = None
        else:
            this_project = project

        # Run model and add results
        all_kwargs[scenno] = {'project': this_project, 'pars': scenparset.pars, 'name': scenlist[scenno].parsetname, 'progsetname': progsetname,
                              'print_label': f'Running scenario "{scen}" ({scenno+1}/{nscens})...',
                              'budget': budget, 'coverage': coverage, 'budgetyears': budgetyears, 'verbose': verbose, 'parallel': parallel,
                              'debug': debug, 'resultname': project.name+'-scenarios', 'addresult': False, 'n': nruns,
                              'parallelizer':parallelizer, **kwargs}

    # We need the runsim_wrapper instead of project.runsim because we need different projects in parallel
    allresults = parallelize(runsim_wrapper, iterkwargs=all_kwargs, serial=(not this_parallel), parallelizer='fast', ncpus=ncpus)

    for scenno, result in enumerate(allresults):
        result.name = scenlist[scenno].name # Give a name to these results so can be accessed for the plot legend
        # Make sure all results refer to the same project
        if this_parallel:
            result.projectref  = Link(project)
            result.projectinfo = project.getinfo()
            result.settings    = project.settings

    if name is None: name='scenarios'

    multires = Multiresultset(resultsetlist=allresults, name=name, keepresultsetlist=keepresultsetlist)
    for scen in scenlist: scen.resultsref = multires.uid # Copy results into each scenario that's been run
    scenres = odict()
    scenres[name] = multires
    return scenres





def makescenarios(project=None, scenlist=None, verbose=2, ccsample=None, randseed=None):
    """ Convert dictionary of scenario parameters into parset to model parameters """
    if ccsample is None: ccsample = 'best'

    if scenlist is None and project is not None and hasattr(project,'scens'):
        scenlist = [scen for scen in project.scens.values()]  # Default to making all the scenarios in the project if none are given

    scenparsets = odict()
    for scenno, scen in enumerate(scenlist):
        try:
            if scen.parsetname not in project.parsets.keys() and len(project.parsets)==1: #if there is only 1 parset, then just update the scenarios
                scen.parsetname = project.parsets.keys()[0]
            
            thisparset = dcp(project.parsets[scen.parsetname])
            thisparset.projectref = Link(project) # Replace copy of project with pointer -- TODO: improve logic
        except: 
            raise OptimaException('Failed to extract parset "%s" from this project:\n%s' % (scen.parsetname, project))
        npops = len(thisparset.popkeys)

        if isinstance(scen,Parscen):
            if scenlist[scenno].pars is None: scenlist[scenno].pars = [] # Turn into empty list instead of None
            for scenpar in scenlist[scenno].pars: # Loop over all parameters being changed

                # Get the parameter object
                thispar = thisparset.pars[scenpar['name']]

                if isinstance(thispar, Timepar): # Sometimes Timepar.t = dict accidentally, which causes issues in this code (maybe elsewhere too)
                    if type(thispar.t) != odict: thispar.t = odict(thispar.t) # Ugly fix...
                    if type(thispar.y) != odict: thispar.y = odict(thispar.y)
                if isinstance(thispar, Popsizepar): # Similarly for Popsizepar
                    if type(thispar.t) != odict: thispar.t = odict(thispar.t)
                    if type(thispar.y) != odict: thispar.y = odict(thispar.y)
                    if type(thispar.e) != odict: thispar.e = odict(thispar.e)
                    if type(thispar.start) != odict: thispar.start = odict(thispar.start)

                # Parse inputs to figure out which population(s) are affected
                if type(scenpar['for'])==tuple: # If it's a partnership...
                    if not scenpar['for'] in thispar.keys():
                        errormsg = 'Partnership %s not associated with parameter %s' % (scenpar['for'],thispar.short)
                        raise OptimaException(errormsg)
                    else: pops = [scenpar['for']] 

                elif isnumber(scenpar['for']): #... if its asingle  population.
                    pops = [range(npops)] if scenpar['for'] > npops else [scenpar['for']]

                elif type(scenpar['for']) in [list, type(array([]))]: #... if its list of population.
                    pops = scenpar['for']

                elif type(scenpar['for'])==str: 
                    if not scenpar['for'] in thispar.keys():
                        errormsg = 'Population %s not associated with parameter %s' % (scenpar['for'],thispar.short)
                        raise OptimaException(errormsg)
                    else: pops = [scenpar['for']] 

                else: 
                    errormsg = 'Unrecognized population or partnership type: %s' % scenpar['for']
                    raise OptimaException(errormsg)

                # Find last good value 
                last_t = scenpar['startyear'] - project.settings.dt # Last timestep before the scenario starts
                last_y = thispar.interp(tvec=last_t, dt=project.settings.dt, asarray=False, usemeta=False) # Find what the model would get for this value

                # Loop over populations
                for pop in pops:

                    # Get the index of the population
                    if isnumber(pop): popind = pop
                    else: popind = thispar.keys().index(pop)
                    
                    # Find or set new value 
                    if scenpar.get('startval') is not None:
                        this_y = promotetoarray(scenpar['startval']) # Use supplied starting value if there is one
                    else:
                        if int(thispar.fromdata): # If it's a regular parameter made from data, we get the default start value from the data
                            this_y = thispar.interp(tvec=scenpar['startyear'], usemeta=False)[popind] # Find what the model would get for this value
                        else:
                            this_y = inf # Another special value, indicating this should be filled in to the maximum                 
                            fixproppar = thisparset.pars['fix'+scenpar['name']] # Pull out e.g. fixpropdx
                            fixproppar.t = min(fixproppar.t, scenpar['startyear']) # Reset start year to the lower of these
                    
                    # Remove years after the last good year
                    if last_t < max(thispar.t[popind]):
                        thispar.t[popind] = thispar.t[popind][findinds(thispar.t[popind] <= last_t)]
                        thispar.y[popind] = thispar.y[popind][findinds(thispar.t[popind] <= last_t)]
                    
                    # Append the last good year, and then the new years
                    thispar.t[popind] = append(thispar.t[popind], last_t)
                    thispar.y[popind] = append(thispar.y[popind], last_y[popind]) 
                    thispar.t[popind] = append(thispar.t[popind], scenpar['startyear'])
                    thispar.y[popind] = append(thispar.y[popind], this_y) 
                    
                    # Add end year values if supplied
                    if scenpar.get('endyear') is not None: 
                        thispar.t[popind] = append(thispar.t[popind], scenpar['endyear'])
                        thispar.y[popind] = append(thispar.y[popind], scenpar['endval'])
                    
                    if len(thispar.t[popind])!=len(thispar.y[popind]):
                        raise OptimaException('Parameter lengths must match (t=%i, y=%i)' % (len(thispar.t), len(thispar.y)))
                        
        elif isinstance(scen,Progscen):

            try: thisprogset = dcp(project.progsets[scen.progsetname])
            except: raise OptimaException('Failed to extract progset "%s" from this project:\n%s' % (scen.progset, project))
            
            try: results = project.parsets[scen.parsetname].getresults() # See if there are results already associated with this parset
            except: results = None

            scen.t = promotetoarray(scen.t)
            if not len(scen.t):
                raise OptimaException(f'Scenario "{scen.name}" does not have a year specified - this is necessary to determine when programs start applying.')

            if isinstance(scen, Budgetscen):
                
                # If the budget has been passed in as a vector, convert it to an odict & sort by program names
                tmpbudget = dcp(thisprogset.getdefaultbudget())
                if isinstance(scen.budget, list) or isinstance(scen.budget,type(array([]))):
                    scen.budget = vec2obj(orig=tmpbudget, newvec=scen.budget) # It seems to be a vector: convert to odict
                if not isinstance(scen.budget,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
                if not isinstance(scen.budget,odict): scen.budget = odict(scen.budget)

                # Update, ensuring a consistent number of programs, using defaults where not provided 
                tmpbudget.update(scen.budget)
                scen.budget = tmpbudget
                
                # Ensure budget values are lists
                for budgetkey, budgetentry in scen.budget.items():
                    if isnumber(budgetentry):
                        scen.budget[budgetkey] = [budgetentry]
                
                # Figure out coverage
                scen.coverage = thisprogset.getprogcoverage(budget=scen.budget, t=scen.t, parset=thisparset, results=results, sample=ccsample)

            elif isinstance(scen, Coveragescen):
                
                # If the coverage levels have been passed in as a vector, convert it to an odict & sort by program names
                tmpbudget = dcp(thisprogset.getdefaultbudget())
                tmpcoverage = thisprogset.getprogcoverage(budget=tmpbudget, t=2000, parset=thisparset) # NOTE, IT DOES NOT MATTER THE VALUE OF t YOU USE HERE!!!

                if isinstance(scen.coverage, list) or isinstance(scen.coverage, type(array([]))):
                    scen.coverage = vec2obj(scen.progset.getdefaultbuget(), newvec=scen.coverage) # It seems to be a vector: convert to odict -- WARNING, super dangerous!!
                if not isinstance(scen.coverage,dict): raise OptimaException('Currently only accepting coverage as dictionaries.')
                if not isinstance(scen.coverage,odict): scen.coverage = odict(scen.coverage)

                # Update, ensuring a consistent number of programs, using defaults where not provided 
                tmpcoverage.update(scen.coverage)
                scen.coverage = tmpcoverage

                # Ensure coverage level values are lists
                for covkey, coventry in scen.coverage.items():
                    if isnumber(coventry):
                        scen.coverage[covkey] = [coventry]

                # Figure out coverage
                scen.budget = thisprogset.getprogbudget(coverage=scen.coverage, t=scen.t, parset=thisparset, results=results)

            # Create parameter dictionary
            thisparsdict = thisprogset.getpars(coverage=scen.coverage, t=scen.t, parset=thisparset, results=results, sample=ccsample)
            scen.pars = thisparsdict
            thisparset.pars = thisparsdict
            
        else: 
            errormsg = 'Unrecognized program scenario type.'
            raise OptimaException(errormsg)
            
        thisparset.modified = today()
        thisparset.name = scen.name
        scenparsets[scen.name] = thisparset
        
    return scenparsets





def baselinescenario(parset=None, verbose=2):
    """ Define the baseline scenario -- "Baseline" by default """
    if parset is None: raise OptimaException('You need to supply a parset to generate default scenarios')
    
    scenlist = [Parscen()]
    
    ## Current conditions
    scenlist[0].name = 'Baseline'
    scenlist[0].parset = parset
    scenlist[0].pars = [] # No changes
    
    return scenlist



def setparscenvalues(parset=None, parname=None, forwhom=None, startyear=None, verbose=2):
    """ Set the values of a parameter scenario """
    if parset is None: raise OptimaException('You need to supply a parset to generate default scenarios')
    
    if parname is None: raise OptimaException('Please supply a parameter')
    
    ## Generate dictionary
    if parset.pars[parname].fromdata: # If it's a regular parameter made from data, we get the default start value from the data
        if startyear is None: startyear = parset.pars[parname].t[forwhom][-1]
        startval = parset.pars[parname].interp(startyear,asarray=False, usemeta=False)[forwhom][0]
    else: # Otherwise, give up -- we can't predict a proportion until the model is run
        if startyear is None: startyear = parset.projectref().settings.now
        startval = None

    
    return {'startval':startval,'startyear':startyear}



def defaultscenarios(project=None, which=None, startyear=2025, endyear=2025, parset=-1, progset=-1, dorun=True, doplot=True, **kwargs):
    '''
    Add default scenarios to a project...examples include min-max budgets and 90-90-90.
    Keyword arguments are passed to runscenarios().
    
    '''
    
    if which is None: which = 'budgets'
    
    if which=='budgets':
        parsetname = 'default-scens'
        parsetnamefixed = 'default-scens-fixed-tx-supp-pmtct'
        project.copyparset(orig=parset, new=parsetname)
        project.copyparset(orig=parset, new=parsetnamefixed)
        project.parsets[parsetname].fixprops(False, which='all')  # For budget scenarios, want unfixed proportions
        project.parsets[parsetnamefixed].fixprops(True)           # For baseline, fix proptx, propsupp, and proppmtct
        defaultbudget = project.progsets[progset].getdefaultbudget()
        maxbudget = dcp(defaultbudget)
        nobudget = dcp(defaultbudget)
        for key in maxbudget: maxbudget[key] += project.settings.infmoney
        for key in nobudget: nobudget[key] *= 1e-6
        scenlist = [
            Parscen(   name='Baseline',         parsetname=parsetnamefixed, pars=[]),
            Budgetscen(name='Zero budget',      parsetname=parsetname, progsetname=0, t=[startyear], budget=nobudget),
            Budgetscen(name='Baseline budget',  parsetname=parsetname, progsetname=0, t=[startyear], budget=defaultbudget),
            Budgetscen(name='Unlimited budget', parsetname=parsetname, progsetname=0, t=[startyear], budget=maxbudget),
            ]
    
    # WARNING, this may not entirely work
    elif which=='90-90-90' or which=='909090':
        scenlist = [
            Parscen(name='Baseline', parsetname=0, pars=[]),
            Parscen(name='90-90-90',
                  parsetname=0,
                  pars=[
                  {'name': 'propdx',
                  'for': ['tot'],
                  'startyear': startyear,
                  'endyear': endyear,
                  'startval': None,
                  'endval': 0.9,
                  },
                  
                  {'name': 'proptx',
                  'for': ['tot'],
                  'startyear': startyear,
                  'endyear': endyear,
                  'startval': None,
                  'endval': 0.9,
                  },
                  
                  {'name': 'propsupp',
                  'for': ['tot'],
                  'startyear': startyear,
                  'endyear': endyear,
                  'startval': None,
                  'endval': .9,
                  },
                  ]),]
    else:
        errormsg = 'Default scenario options are "budgets" and "90-90-90", not %s' % which
        raise OptimaException(errormsg)

    
    # Run the scenarios
    project.addscens(scenlist)
    if dorun: project.runscenarios(**kwargs)
    if doplot: 
        from optima import pygui
        pygui(project)
    return None # Can get it from project.scens


def checkifparsetoverridesscenario(project, parset, scen, progset=None, progendyear=None, formatfor='console', createmessages=True, die=False, verbose=2):
    """
        A function that sets up the inputs to see if the current parset contains any parameters that
        override the parameters that a (parameter or program) scenario is trying to target.
        If any conflicts are found, the warning message(s) can
        be created with createmessages=True, otherwise combinedwarningmsg, warningmessages will both be None
        Args:
            project: the project (to get the parset from if it is not provided)
            parset: the associated parset to the scen
            scen: a single Scen object (any type is fine)
            progendyear: year the progset is starting
            formatfor: 'console' with \n linebreaks, or 'html' with <p> and <br> elements.
            createmessages: True to get combinedwarningmsg, warningmessages from createwarningforoverride()
        Returns:
            warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages
            See checkifparsoverridepars and createwarningforoverride for information about the outputs
        """
    if isinstance(scen, Progscen):
        if progset is None:
            try: progset = project.progsets[scen.progsetname]
            except:
                errmsg = f'Warning could not get progset with name "{scen.progsetname}" for scenario "{scen.name}" from project "{project.name}" to check if any parameters override it.'
                if die: raise OptimaException(errmsg)
                else:
                    printv(errmsg, 2, verbose=verbose)
                    # warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages
                    return False, odict(), odict(), odict(), '', []

        progstartyear = min(promotetoarray(scen.t))

        # warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages = \
        return checkifparsetoverridesprogset(progset=progset, parset=parset, progendyear=progendyear, progstartyear=progstartyear, formatfor=formatfor, createmessages=createmessages)
    elif isinstance(scen, Parscen):
        origpars = parset.pars
        targetpars = scen.pars
        if len(targetpars) == 0: return False, odict(), odict(), odict(), '', []

        targetparsnames = [par['name'] for par in targetpars]
        targetparsstart = [par['startyear'] for par in targetpars]
        targetparsend = [par['endyear'] for par in targetpars]

        warning, parsoverridingparsdict, overridetimes, overridevals = \
            checkifparsoverridepars(origpars,
                                    targetparsnames,
                                    progstartyear=min(targetparsstart),
                                    progendyear=max(targetparsend)) # note that assumes that all Pars are set starting in the same year, and ending in the same year but this is good enough? for a warning

        combinedwarningmsg, warningmessages = None, None
        if createmessages:
            warning, combinedwarningmsg, warningmessages = createwarningforoverride(origpars, warning,
                                                                                    parsoverridingparsdict,
                                                                                    overridetimes, overridevals,
                                                                                    fortype='Parscen',
                                                                                    parsetname=parset.name,
                                                                                    progendyear=progendyear,
                                                                                    formatfor=formatfor)
        # warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages
        return warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages

