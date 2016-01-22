## Imports
from numpy import append #, arange, linspace # array, isnan, zeros, shape, argmax, log, polyfit, exp
from optima import dcp, today, odict, printv, findinds, runmodel, Multiresultset, getdate, uuid, objrepr, defaultrepr, getresults #, sanitize, uuid, getdate, smoothinterp



class Scen(object):
    ''' The scenario base class -- not to be used directly, instead use Parscen or Progscen '''
    def __init__(self, name=None, parset=None, t=None):
        self.name = name
        self.parset = parset
        self.t = t
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output
    
    

class Parscen(Scen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, name=None, parset=None, t=None, pars=None):
            Scen.__init__(self, name=name, parset=parset, t=t)
            self.pars = pars

class Progscen(Scen):
    ''' An object for storing a single parameter scenario '''
    def __init__(self, name=None, parset=None, t=None, progscentype=None, progset=None, programs=None):
            Scen.__init__(self, name=name, parset=parset, t=t)
            self.progscentype = progscentype
            self.progset = progset
            self.programs = programs


class Scenset(object):
    ''' An object for storing a set of scenarios '''
    
    def __init__(self, project=None, name='default', scenlist=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uid = uuid() # ID
        self.project = project # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.scenlist = scenlist
        self.resultsref = None # Store pointer to results
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '============================================================\n'
        output += '      Scenario name: %s\n'    % self.name
        output += 'Number of scenarios: %i\n'    % len(self.scenlist)
        output += '       Date created: %s\n'    % getdate(self.created)
        output += '      Date modified: %s\n'    % getdate(self.modified)
        output += '                UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objrepr(self)
        return output
    
    
    def getresults(self):
        ''' A little method for getting the results '''
        if self.resultsref is not None and self.project is not None:
            results = getresults(project=self.project, pointer=self.resultsref)
            return results
        else:
            print('WARNING, no results associated with this parameter set')








def runscenarios(project=None, scenlist=None, verbose=2, defaultparset=0):
    """
    Run all the scenarios.
    
    Version: 2016jan22 by cliffk
    """
    
    printv('Running scenarios...', 1, verbose)
    
    # Make sure scenarios exist
    if scenlist==None: scenlist = defaultscenarios(project.parsets[defaultparset], verbose=verbose)
    nscens = len(scenlist)
    
    # Convert the list of scenarios to the actual parameters to use in the model
    scenparsets = makescenarios(scenlist,verbose=verbose)

    # Run scenarios
    allresults = []
    for scenno, scen in enumerate(scenparsets):
        allresults.append(runmodel(pars=scenparsets[scen].pars[0], verbose=1)) # Don't bother printing out model run because it's obvious
        allresults[-1].name = scenlist[scenno].name # Give a name to these results so can be accessed for the plot legend
        printv('Scenario: %i/%i' % (scenno+1, nscens), 2, verbose)
    
    multires = Multiresultset(allresults)
    
    printv('...done running scenarios.', 2, verbose)
    return multires





def makescenarios(scenlist, verbose=2):
    """ Convert dictionary of scenario parameters into parset to model parameters """

    scenparsets = odict()
    for scenno, scen in enumerate(scenlist):
        
        thisparset = dcp(scen.parset)
        thisparset.modified = today()
        thisparset.name = scen.name
        npops = len(thisparset.popkeys)

        if type(scen)==Parscen:
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
                        raise Exception(errormsg)
                    for pop in pops:
                        if par['startyear'] < max(thispar.t[pop]):
                            thispar.t[pop] = thispar.t[pop][thispar.t[pop] < par['startyear']]
                            thispar.y[pop] = thispar.y[pop][thispar.t[pop] < par['startyear']]
                        thispar.t[pop] = append(thispar.t[pop], par['startyear'])
                        thispar.y[pop] = append(thispar.y[pop], par['startval']) 
                        if par['endyear']: # Add end year values if supplied
                            thispar.t[pop] = append(thispar.t[pop], par['endyear'])
                            thispar.y[pop] = append(thispar.y[pop], par['endval'])
    
        elif type(scen)==Progscen:
            thisprogset = scen.progset
            if scen.progscentype=='budget':
                thiscoverage = thisprogset.getprogcoverage(budget=scen.programs, t=scen.t, parset=scen.parset)
            elif scen.progscentype=='coverage':
                thiscoverage = scen.programs
            
            thisparsdict = thisprogset.getparsdict(coverage=thiscoverage, t=scen.t, parset=scen.parset)
            for pardictno in range(len(thisparset.pars)): # Loop over all parameter dictionaries
                thisparset.pars[pardictno] = thisparsdict

        else: 
            errormsg = 'Unrecognized program scenario type.'
            raise Exception(errormsg)
            

        scenparsets[scen.name] = thisparset

    return scenparsets





def defaultscenarios(parset=None, verbose=2):
    """ Define a list of default scenarios -- only "Current conditions" by default """
    if parset is None: raise Exception('You need to supply a parset to generate default scenarios')
    
    scenlist = [Parscen()]
    
    ## Current conditions
    scenlist[0].name = 'Current conditions'
    scenlist[0].parset = parset
    scenlist[0].pars = [] # No changes
    
    return scenlist



def getparvalues(parset, par):
    """
    Return the default parameter values from simpars for a given par. -- WARNING, shouldn't this be a method of Par?
    
    defaultvals = getparvalues(P, parset, scenariolist[1]['pars'][2])
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
        



