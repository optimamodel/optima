'''
Define classes and functions for handling scenarios and ICERs.

Version: 2017jun03
'''

## Imports
from numpy import append, array
from optima import OptimaException, Link, Multiresultset, ICER, runmodel, defaultobjectives, outcomecalc # Core classes/functions
from optima import dcp, today, odict, printv, findinds, defaultrepr, getresults, vec2obj, isnumber, uuid, promotetoarray # Utilities

class Scen(object):
    ''' The scenario base class -- not to be used directly, instead use Parscen or Progscen '''
    def __init__(self, name=None, parsetname=-1, t=None, active=True):
        self.uid = uuid()
        self.name = name
        self.parsetname = parsetname
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


def runscenarios(project=None, verbose=2, defaultparset=0, debug=False, **kwargs):
    """
    Run all the scenarios.
    Version: 2016jan22 by cliffk
    """
    
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if project is None: raise OptimaException('First argument to runscenarios() must be a project')
    if len(project.scens)==0:  # Create scenario list if not existing
        baselinescen = baselinescenario(project.parsets[defaultparset], verbose=verbose)
        project.addscens(baselinescen)
    scenlist = [scen for scen in project.scens.values() if scen.active==True]
    nscens = len(scenlist)
    
    # Convert the list of scenarios to the actual parameters to use in the model
    scenparsets = makescenarios(project=project, scenlist=scenlist, verbose=verbose)

    # Run scenarios
    allresults = []
    for scenno, scen in enumerate(scenparsets):
        printv('Running scenario "%s" (%i/%i)...' % (scen, scenno+1, nscens), 2, verbose)
        scenparset = scenparsets[scen]
        project.scens[scenno].scenparset = scenparset # Copy into scenarios objects

        # Items specific to program (budget or coverage) scenarios
        budget = scenlist[scenno].budget if isinstance(scenlist[scenno], Progscen) else None
        coverage = scenlist[scenno].coverage if isinstance(scenlist[scenno], Progscen) else None
        budgetyears = scenlist[scenno].t if isinstance(scenlist[scenno], Progscen) else None
        progset = project.progsets[scenlist[scenno].progsetname] if isinstance(scenlist[scenno], Progscen) else None

        # Run model and add results
        result = runmodel(pars=scenparset.pars, parset=scenparset, progset=progset, project=project, budget=budget, coverage=coverage, budgetyears=budgetyears, verbose=0, debug=debug, label=project.name+'-scenarios', **kwargs)
        result.name = scenlist[scenno].name # Give a name to these results so can be accessed for the plot legend
        allresults.append(result) 
        printv('... completed scenario: %i/%i' % (scenno+1, nscens), 3, verbose)
    
    multires = Multiresultset(resultsetlist=allresults, name='scenarios')
    for scen in scenlist: scen.resultsref = multires.uid # Copy results into each scenario that's been run
    
    return multires





def makescenarios(project=None, scenlist=None, verbose=2):
    """ Convert dictionary of scenario parameters into parset to model parameters """

    scenparsets = odict()
    for scenno, scen in enumerate(scenlist):
        
        try: 
            thisparset = dcp(project.parsets[scen.parsetname])
            thisparset.projectref = Link(project) # Replace copy of project with pointer -- WARNING, hacky
        except: raise OptimaException('Failed to extract parset "%s" from this project:\n%s' % (scen.parsetname, project))
        npops = len(thisparset.popkeys)

        if isinstance(scen,Parscen):
            if scenlist[scenno].pars is None: scenlist[scenno].pars = [] # Turn into empty list instead of None
            for scenpar in scenlist[scenno].pars: # Loop over all parameters being changed

                # Get the parameter object
                thispar = thisparset.pars[scenpar['name']]

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

                # Find last good value # WARNING, FIX!!!!
                last_t = scenpar['startyear'] - project.settings.dt # Last timestep before the scenario starts
                last_y = thispar.interp(tvec=last_t, dt=project.settings.dt, asarray=False, sample=False) # Find what the model would get for this value

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
                            this_y = thispar.interp(tvec=scenpar['startyear'], sample=False)[popind] # Find what the model would get for this value
                        else:
                            this_y = thisparset.getprop(proptype=scenpar['name'],year=scenpar['startyear'])                            

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
            
            if isinstance(scen, Budgetscen):
                
                # If the budget has been passed in as a vector, convert it to an odict & sort by program names
                tmpbudget = dcp(thisprogset.getdefaultbudget())
                if isinstance(scen.budget, list) or isinstance(scen.budget,type(array([]))):
                    scen.budget = vec2obj(orig=tmpbudget, newvec=scen.budget) # It seems to be a vector: convert to odict
                if not isinstance(scen.budget,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
                if not isinstance(scen.budget,odict): scen.budget = odict(scen.budget)

                # Update, ensuring a consistent number of programs, using defaults where not provided -- WARNING, ugly
                tmpbudget.update(scen.budget)
                scen.budget = tmpbudget
                
                # Ensure budget values are lists
                for budgetkey, budgetentry in scen.budget.iteritems():
                    if isnumber(budgetentry):
                        scen.budget[budgetkey] = [budgetentry]
                
                # Figure out coverage
                scen.coverage = thisprogset.getprogcoverage(budget=scen.budget, t=scen.t, parset=thisparset, results=results)

            elif isinstance(scen, Coveragescen):
                
                # If the coverage levels have been passed in as a vector, convert it to an odict & sort by program names
                tmpbudget = dcp(thisprogset.getdefaultbudget())
                tmpcoverage = thisprogset.getprogcoverage(budget=tmpbudget, t=2000, parset=thisparset) # WARNING, IT DOES NOT MATTER THE VALUE OF t YOU USE HERE!!!

                if isinstance(scen.coverage, list) or isinstance(scen.coverage, type(array([]))):
                    scen.coverage = vec2obj(scen.progset.getdefaultbuget(), newvec=scen.coverage) # It seems to be a vector: convert to odict -- WARNING, super dangerous!!
                if not isinstance(scen.coverage,dict): raise OptimaException('Currently only accepting coverage as dictionaries.')
                if not isinstance(scen.coverage,odict): scen.coverage = odict(scen.coverage)

                # Update, ensuring a consistent number of programs, using defaults where not provided -- WARNING, ugly
                tmpcoverage.update(scen.coverage)
                scen.coverage = tmpcoverage

                # Ensure coverage level values are lists
                for covkey, coventry in scen.coverage.iteritems():
                    if isnumber(coventry):
                        scen.coverage[covkey] = [coventry]

                # Figure out coverage
                scen.budget = thisprogset.getprogbudget(coverage=scen.coverage, t=scen.t, parset=thisparset, results=results)

            # Create parameter dictionary
            thisparsdict = thisprogset.getpars(coverage=scen.coverage, t=scen.t, parset=thisparset, results=results)
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
        startval = parset.pars[parname].interp(startyear,asarray=False)[forwhom][0]
    else:
        if startyear is None: startyear = parset.projectref().settings.now
        startval = parset.getprop(proptype=parname,year=startyear)[0]

    
    return {'startval':startval,'startyear':startyear}



def defaultscenarios(project=None, which=None, startyear=2016, endyear=2020, parset=-1, progset=-1, dorun=True, doplot=True):
    ''' Add default scenarios to a project...examples include min-max budgets and 90-90-90 '''
    
    if which is None: which = 'budgets'
    
    if which=='budgets':
        parsetname = 'default-scenarios'
        project.copyparset(orig=parset, new=parsetname)
        project.parsets['default-scenarios'].fixprops(False) # Ensure they're not fixed
        defaultbudget = project.progsets[progset].getdefaultbudget()
        maxbudget = dcp(defaultbudget)
        nobudget = dcp(defaultbudget)
        for key in maxbudget: maxbudget[key] += project.settings.infmoney
        for key in nobudget: nobudget[key] *= 1e-6
        scenlist = [
            Parscen(   name='Baseline',         parsetname=parsetname, pars=[]),
            Budgetscen(name='Zero budget',      parsetname=parsetname, progsetname=0, t=[startyear], budget=nobudget),
            Budgetscen(name='Baseline budget',  parsetname=parsetname, progsetname=0, t=[startyear], budget=defaultbudget),
            Budgetscen(name='Unlimited budget', parsetname=parsetname, progsetname=0, t=[startyear], budget=maxbudget),
            ]
    
    # WARNING, this may not entirely work
    elif which=='90-90-90':
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
    if dorun: project.runscenarios()
    if doplot: 
        from optima import pygui
        pygui(project)
    return None # Can get it from project.scens


def icers(name=None, project=None, parsetname=None, progsetname=None, which=None, startyear=None, endyear=None, budgetratios=None, marginal=True, verbose=2, **kwargs):
    ''' Calculate ICERs for each program '''
    
    printv('Calculating ICERs...')
    
    # Handle inputs
    if type(project).__name__ != 'Project': # Can't compare types directly since can't import Project since not defined yet
        errormsg = 'To calculate ICERs you must supply a project, not "%s"' % type(project)
        raise OptimaException(errormsg)
    
    # Set defaults
    eps = project.settings.eps
    if which        is None: which        = 'numdaly'
    if parsetname   is None: parsetname   = -1
    if progsetname  is None: progsetname  = -1
    if budgetratios is None: budgetratios = [0.0, 0.5, 1.0, 2.0] #[0.0, 0.1, 0.2, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    budgetratios = array(budgetratios) # Ensure it's an array
    nbudgetratios = len(budgetratios)
    
    # Define objectives
    objectives = defaultobjectives(project=project)
    objectives['which'] = which # Overwrite this by default
    if startyear is not None: objectives['start'] = startyear # Do not overwrite by default
    if endyear   is not None: objectives['end']   = endyear
    nyears = objectives['end']-objectives['start'] # Calculate the number of years
    
    # Get budget information
    origbudget    = project.defaultbudget(progsetname, optimizable=False) # Get default budget for optimizable programs
    defaultbudget = project.defaultbudget(progsetname, optimizable=True)  # ...and just for optimizable programs
    keys = defaultbudget.keys() # Get the program keys
    nkeys = len(keys)
    
    # Define structures for storing results
    rawx = odict().make(keys=keys, vals=[])
    rawy = dcp(rawx)
    y    = dcp(rawx)
    
    # Define arguments that don't change in the loop
    defaultargs = {'which':'outcomes', 'project':project, 'parsetname':parsetname, 'progsetname':progsetname, 'objectives':objectives, 
                   'origbudget':origbudget, 'outputresults':False, 'verbose':verbose, 'doconstrainbudget':False}
    
    # Calculate baseline
    baselinex = defaultbudget[:].sum()
    baseliney = outcomecalc(budgetvec=defaultbudget, **defaultargs)
    
    # Loop over both programs and budget ratios
    count = 0
    for key in keys:
        for budgetratio in budgetratios:
            count += 1
            printv('Running ICER budget %i of %i' % (count, nkeys*nbudgetratios), 2, verbose)
            thisbudget = dcp(defaultbudget)
            thisbudget[key] *= budgetratio
            rawx[key].append(thisbudget[key])
            if budgetratio==1: outcome = baseliney # Don't need to run, just copy this
            else:              outcome = outcomecalc(budgetvec=thisbudget, **defaultargs) # The crux of the matter!! Actually calculate
            rawy[key].append(outcome)
            
    # Calculate y values
    for key in keys:
        for b in range(nbudgetratios):
            
            # Gather values to use
            thisx = rawx[key][b]
            thisy = rawy[key][b]
            try:    
                lowerx = rawx[key][b-1]
                lowery = rawy[key][b-1]
            except: 
                lowerx = None
                lowery = None
            try:    
                upperx = rawx[key][b+1]
                uppery = rawy[key][b+1]
            except: 
                upperx = None
                uppery = None
            
            # Calculate estimates by comparing to lower and upper values, and baseline if those fail
            estimates = [] # Start assembling ICER estimates
            if marginal:
                if lowerx is not None:
                    lowerdiffx = (thisx - lowerx)*nyears
                    lowerdiffy = thisy - lowery
                    lower = lowerdiffy/(lowerdiffx+eps)
                    estimates.append(lower)
                if upperx is not None:
                    upperdiffx = (thisx - upperx)*nyears
                    upperdiffy = thisy - uppery
                    upper = upperdiffy/(upperdiffx+eps)
                    estimates.append(upper)
            else:
                baselinediffx = (thisx - baselinex)*nyears # To get total cost, need to multiply by the number of years
                baselinediffy = thisy - baseliney
                baselinediff = baselinediffy/(baselinediffx+eps)
                estimates = [baselinediff]
            
            # Finally, calculate the DALYs per dollar
            thisicer = array(estimates).mean() # Average upper and lower estimates, if available
            y[key].append(thisicer)
            print key, b, thisx, lowerx, upperx, thisy, lowery, uppery, lower, upper, thisicer
                
    # Assemble into results
    results = ICER(name=name, which=objectives['which'], startyear=objectives['start'], endyear=objectives['end'], rawx=rawx, rawy=rawy, x=budgetratios, y=y, baseline=baseliney, keys=keys, defaultbudget=defaultbudget, parsetname=parsetname, progsetname=progsetname)
    return results
