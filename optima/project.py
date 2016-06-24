from optima import OptimaException, Settings, Parameterset, Programset, Resultset, BOC, Parscen, Optim # Import classes
from optima import odict, getdate, today, uuid, dcp, objrepr, printv, isnumber, saveobj, defaultrepr # Import utilities
from optima import loadspreadsheet, model, gitinfo, sensitivity, manualfit, autofit, runscenarios 
from optima import defaultobjectives, defaultconstraints, loadeconomicsspreadsheet, runmodel # Import functions
from optima import __version__ # Get current version
from numpy import argmin, array
import os

#######################################################################################################
## Project class -- this contains everything else!
#######################################################################################################

class Project(object):
    """
    PROJECT

    The main Optima project class. Almost all Optima functionality is provided by this class.

    An Optima project is based around 4 major lists:
        1. parsets -- an odict of parameter sets
        2. progsets -- an odict of program sets
        3. scens -- an odict of scenario structures
        4. optims -- an odict of optimization structures
        5. results -- an odict of results associated with parsets, scens, and optims

    In addition, an Optima project contains:
        1. data -- loaded from the spreadsheet
        2. settings -- timestep, indices, etc.
        3. various kinds of metadata -- project name, creation date, etc.
        4. econ -- data and time series loaded from the economics spreadsheet


    Methods for structure lists:
        1. add -- add a new structure to the odict
        2. remove -- remove a structure from the odict
        3. copy -- copy a structure in the odict
        4. rename -- rename a structure in the odict

    Version: 2016jan22 by cliffk
    """



    #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################

    def __init__(self, name='default', spreadsheet=None, dorun=True, verbose=2):
        ''' Initialize the project '''

        ## Define the structure sets
        self.parsets  = odict()
        self.progsets = odict()
        self.scens    = odict()
        self.optims   = odict()
        self.results  = odict()

        ## Define other quantities
        self.name = name
        self.settings = Settings(verbose=verbose) # Global settings
        self.data = {} # Data from the spreadsheet

        ## Define metadata
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        self.spreadsheet = None # Binary version of the spreadsheet file
        self.version = __version__
        self.gitbranch, self.gitversion = gitinfo()
        self.filename = None # File path, only present if self.save() is used

        ## Load spreadsheet, if available
        if spreadsheet is not None:
            self.loadspreadsheet(spreadsheet, dorun=dorun)

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = objrepr(self)
        output += '      Project name: %s\n'    % self.name
        output += '\n'
        output += '    Parameter sets: %i\n'    % len(self.parsets)
        output += '      Program sets: %i\n'    % len(self.progsets)
        output += '         Scenarios: %i\n'    % len(self.scens)
        output += '     Optimizations: %i\n'    % len(self.optims)
        output += '      Results sets: %i\n'    % len(self.results)
        output += '\n'
        output += '    Optima version: %0.1f\n' % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += 'Spreadsheet loaded: %s\n'    % getdate(self.spreadsheetdate)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        return output


    #######################################################################################################
    ## Methods for I/O and spreadsheet loading
    #######################################################################################################


    def loadspreadsheet(self, filename, name='default', overwrite=True, makedefaults=False, dorun=True, **kwargs):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file '''

        ## Load spreadsheet and update metadata
        self.spreadsheet = Spreadsheet(filename) # Load spreadsheet binary file into project -- WARNING, only partly implemented since not sure how to read from
        self.data = loadspreadsheet(filename, verbose=self.settings.verbose) # Do the hard work of actually loading the spreadsheet
        self.spreadsheetdate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        self.makeparset(name=name, overwrite=overwrite)
        if makedefaults: self.makedefaults(name)
        self.settings.start = self.data['years'][0] # Reset the default simulation start to initial year of data
        if dorun: self.runsim(name, addresult=True, **kwargs)
        return None


    def makeparset(self, name='default', overwrite=True):
        ''' If parameter set of that name doesn't exist, create it '''
        # question: what is that parset does exist? delete it first?
        if not self.data:
            raise OptimaException('No data in project "%s"!' % self.name)
        if overwrite or name not in self.parsets:
            parset = Parameterset(name=name, project=self)
            parset.makepars(self.data, verbose=self.settings.verbose) # Create parameters
            self.addparset(name=name, parset=parset, overwrite=overwrite) # Store parameters
            self.modified = today()
        return None


    def makedefaults(self, name='default', overwrite=False):
        ''' When creating a project, create a default program set, scenario, and optimization to begin with '''
        scenname = 'Current conditions'
        if overwrite or name not in self.progsets:
            progset = Programset(name=name)
            self.addprogset(progset)
        if overwrite or scenname not in self.scens:
            scen = Parscen(name=scenname, parsetname=self.parsets.keys()[0], pars=[])
            self.addscen(scen)
        if overwrite or name not in self.optims:
            optim = Optim(project=self, name=name, objectives=defaultobjectives(project=self, progset=0), constraints=defaultconstraints(project=self, progset=0), parsetname=self.parsets.keys()[0], progsetname=self.progsets.keys()[0])
            self.addoptim(optim)
        return None


    def loadeconomics(self, filename):
        ''' Load economic data and tranforms it to useful format'''
        self.data['econ'] = loadeconomicsspreadsheet(filename) ## Load spreadsheet
        self.modified = today()
        return None


    #######################################################################################################
    ## Methods to handle common tasks with structure lists
    #######################################################################################################


    def getwhat(self, item=None, what=None):
        '''
        Figure out what kind of structure list is being requested, e.g.
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if item is None and what is None: raise OptimaException('No inputs provided')
        if what is not None: # Explicitly define the type, item be damned
            if what in ['p', 'pars', 'parset', 'parameters']: structlist = self.parsets
            elif what in ['pr', 'progs', 'progset', 'progsets']: structlist = self.progsets # WARNING, inconsistent terminology!
            elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
            elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimisation', 'optimization', 'optimisations', 'optimizations']: structlist = self.optims
            elif what in ['r', 'res', 'result', 'results']: structlist = self.results
            else: raise OptimaException('Structure list "%s" not understood' % what)
        else: # Figure out the type based on the input
            if type(item)==Parameterset: structlist = self.parsets
            elif type(item)==Programset: structlist = self.progsets
            elif type(item)==Resultset: structlist = self.results
            else: raise OptimaException('Structure list "%s" not understood' % str(type(item)))
        return structlist


    def checkname(self, what=None, checkexists=None, checkabsent=None, overwrite=True):
        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
        if type(what)==odict: structlist=what # It's already a structlist
        else: structlist = self.getwhat(what=what)
        if isnumber(checkexists): # It's a numerical index
            try: checkexists = structlist.keys()[checkexists] # Convert from 
            except: raise OptimaException('Index %i is out of bounds for structure list "%s" of length %i' % (checkexists, what, len(structlist)))
        if checkabsent is not None:
            if checkabsent in structlist:
                if overwrite==False:
                    raise OptimaException('Structure list "%s" already has item named "%s"' % (what, checkabsent))
                else:
                    printv('Structure list already has item named "%s"' % (checkabsent), 2, self.settings.verbose)
                
        if checkexists is not None:
            if not checkexists in structlist:
                raise OptimaException('Structure list has no item named "%s"' % (checkexists))
        return None


    def add(self, name=None, item=None, what=None, overwrite=True, consistentnames=True):
        ''' Add an entry to a structure list -- can be used as add('blah', obj), add(name='blah', item=obj), or add(item) '''
        if name is None:
            try: name = item.name # Try getting name from the item
            except: name = 'default' # If not, revert to default
        if item is None and type(name)!=str: # Maybe an item has been supplied as the only argument
            try: 
                item = name # It's actully an item, not a name
                name = item.name # Try getting name from the item
            except: raise OptimaException('Could not figure out how to add item with name "%s" and item "%s"' % (name, item))
        structlist = self.getwhat(item=item, what=what)
        self.checkname(structlist, checkabsent=name, overwrite=overwrite)
        structlist[name] = item
        if consistentnames: structlist[name].name = name # Make sure names are consistent -- should be the case for everything except results, where keys are UIDs
        printv('Item "%s" added to "%s"' % (name, what), 2, self.settings.verbose)
        self.modified = today()
        return None


    def remove(self, what=None, name=None):
        ''' Remove an entry from a structure list by name '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=name)
        structlist.pop(name)
        printv('%s "%s" removed' % (what, name), 2, self.settings.verbose)
        self.modified = today()
        return None


    def copy(self, what=None, orig='default', new='copy', overwrite=True):
        ''' Copy an entry in a structure list '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = dcp(structlist[orig])
        structlist[new].name = new  # Update name
        structlist[new].uid = uuid()  # Otherwise there will be 2 structures with same unique identifier
        structlist[new].created = today() # Update dates
        structlist[new].modified = today() # Update dates
        if hasattr(structlist[new], 'project'): structlist[new].project = self # Preserve information about project -- don't deep copy -- WARNING, may not work?
        printv('%s "%s" copied to "%s"' % (what, orig, new), 2, self.settings.verbose)
        self.modified = today()
        return None


    def rename(self, what=None, orig='default', new='new', overwrite=True):
        ''' Rename an entry in a structure list '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = structlist.pop(orig)
        structlist[new].name = new # Update name
        printv('%s "%s" renamed "%s"' % (what, orig, new), 2, self.settings.verbose)
        self.modified = today()
        return None
        

    #######################################################################################################
    ## Convenience functions -- NOTE, do we need these...?
    #######################################################################################################

    def addparset(self,   name=None, parset=None,   overwrite=True): self.add(what='parset',   name=name, item=parset,  overwrite=overwrite)
    def addprogset(self,  name=None, progset=None,  overwrite=True): self.add(what='progset',  name=name, item=progset, overwrite=overwrite)
    def addscen(self,     name=None, scen=None,     overwrite=True): self.add(what='scen',     name=name, item=scen,    overwrite=overwrite)
    def addoptim(self,    name=None, optim=None,    overwrite=True): self.add(what='optim',    name=name, item=optim,   overwrite=overwrite)

    def rmparset(self,   name): self.remove(what='parset',   name=name)
    def rmprogset(self,  name): self.remove(what='progset',  name=name)
    def rmscen(self,     name): self.remove(what='scen',     name=name)
    def rmoptim(self,    name): self.remove(what='optim',    name=name)


    def copyparset(self,   orig='default', new='new', overwrite=True): self.copy(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def copyprogset(self,  orig='default', new='new', overwrite=True): self.copy(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def copyscen(self,     orig='default', new='new', overwrite=True): self.copy(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def copyoptim(self,    orig='default', new='new', overwrite=True): self.copy(what='optim',    orig=orig, new=new, overwrite=overwrite)

    def renameparset(self,   orig='default', new='new', overwrite=True): self.rename(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def renameprogset(self,  orig='default', new='new', overwrite=True): self.rename(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def renamescen(self,     orig='default', new='new', overwrite=True): self.rename(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def renameoptim(self,    orig='default', new='new', overwrite=True): self.rename(what='optim',    orig=orig, new=new, overwrite=overwrite)

    def addresult(self, result=None, overwrite=True): 
        ''' Try adding result by name, but if no name, add by UID '''
        if result.name is None: keyname = str(result.uid)
        else: keyname = result.name
        self.add(what='result',  name=keyname, item=result, consistentnames=False, overwrite=overwrite) # Use UID for key but keep name
        return keyname # Can be useful to know what ended up being chosen
    
    def rmresult(self, name=-1):
        ''' Remove a single result by name '''
        resultuids = self.results.keys() # Pull out UID keys
        resultnames = [res.name for res in self.results.values()] # Pull out names
        if isnumber(name) and name<len(self.results):  # Remove by index rather than name
            self.remove(what='result', name=self.results.keys()[name])
        elif name in resultuids: # It's a UID: remove directly 
            self.remove(what='result', name=name)
        elif name in resultnames: # It's a name: find the UID corresponding to this name and remove
            self.remove(what='result', name=resultuids[resultnames.index(name)]) # WARNING, if multiple names match, will delete oldest one -- expected behavior?
        else:
            validchoices = ['#%i: name="%s", uid=%s' % (i, resultnames[i], resultuids[i]) for i in range(len(self.results))]
            errormsg = 'Could not remove result "%s": choices are:\n%s' % (name, '\n'.join(validchoices))
            raise OptimaException(errormsg)
    
    
    def cleanresults(self):
        ''' Remove all results '''
        self.results = odict() # Just replace with an empty odict, as at initialization
        return None
    
    
    def addscenlist(self, scenlist): 
        ''' Function to make it slightly easier to add scenarios all in one go -- WARNING, should make this a general feature of add()! '''
        for scen in scenlist: self.addscen(name=scen.name, scen=scen, overwrite=True)
        return None
    
    
    def save(self, filename=None, saveresults=False, verbose=2):
        ''' Save the current project, by default using its name, and without results '''
        if filename is None and self.filename and os.path.exists(self.filename): filename = self.filename
        if filename is None: filename = self.name+'.prj'
        self.filename = os.path.abspath(filename) # Store file path
        if saveresults:
            saveobj(filename, self, verbose=verbose)
        else:
            tmpproject = dcp(self) # Need to do this so we don't clobber the existing results
            tmpproject.cleanresults() # Get rid of all results
            saveobj(filename, tmpproject, verbose=verbose) # Save it to file
            del tmpproject # Don't need it hanging around any more
        return None




    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################


    def runsim(self, name=None, simpars=None, start=None, end=None, dt=None, addresult=True, die=True, debug=False, overwrite=True, verbose=None):
        ''' This function runs a single simulation, or multiple simulations if pars/simpars is a list.
        
        WARNING, do we need this? What's it for? Why not use runmodel()?
        '''
        if start is None: start=self.settings.start # Specify the start year
        if end is None: end=self.settings.end # Specify the end year
        if dt is None: dt=self.settings.dt # Specify the timestep
        if name is None and simpars is None: name = 'default' # Set default name
        if verbose is None: verbose = self.settings.verbose
        
        # Get the parameters sorted
        if simpars is None: # Optionally run with a precreated simpars instead
            simparslist = self.parsets[name].interp(start=start, end=end, dt=dt, verbose=verbose) # "self.parset[name]" is e.g. P.parset['default']
        else:
            if type(simpars)==list: simparslist = simpars
            else: simparslist = [simpars]

        # Run the model! -- wARNING, the logic of this could be cleaned up a lot!
        rawlist = []
        for ind in range(len(simparslist)):
            if debug: # Should this be die?
                raw = model(simparslist[ind], self.settings, die=die, debug=debug, verbose=verbose) # ACTUALLY RUN THE MODEL
            else:
                try:
                    raw = model(simparslist[ind], self.settings, die=die, debug=debug, verbose=verbose) # ACTUALLY RUN THE MODEL
                    if not (raw['people']>=0).all(): # Check for negative people
                        printv('Negative people found with runsim(); rerunning with a smaller timestep...')
                        self.settings.dt /= 4
                        raw = model(simparslist[ind], self.settings, die=die, debug=debug, verbose=verbose) # ACTUALLY RUN THE MODEL
                except:
                    printv('Running model failed; running again with debugging...', 1, verbose)
                    raw = model(simparslist[ind], self.settings, die=die, debug=True, verbose=verbose) # ACTUALLY RUN THE MODEL
            rawlist.append(raw)

        # Store results -- WARNING, is this correct in all cases?
        resultname = 'parset-'+self.parsets[name].name if simpars is None else 'simpars'
        results = Resultset(name=resultname, raw=rawlist, simpars=simparslist, project=self) # Create structure for storing results
        if addresult:
            keyname = self.addresult(result=results, overwrite=overwrite)
            if simpars is None: self.parsets[name].resultsref = keyname # If linked to a parset, store the results

        return results


    def reconcileparsets(self, name=None, orig=None):
        ''' Helper function to copy a parset if required -- used by sensitivity, manualfit, and autofit '''
        if name is None and orig is None: # Nothing supplied, just use defaults
            name = 'default'
            orig = 'default'
        if isnumber(name): name = self.parsets.keys()[name] # Convert from index to name if required
        if isnumber(orig): orig = self.parsets.keys()[orig]
        if name is not None and orig is not None and name!=orig:
            self.copyparset(orig=orig, new=name, overwrite=True) # Store parameters, user seems to know what she's doing, trust her!
        if name is None and orig is not None: name = orig # Specify name if not supplied
        if name is not None and orig is None: orig = name # Specify orig if not supplied
        if name not in self.parsets.keys():
            if orig not in self.parsets.keys(): 
                errormsg = 'Cannot use original parset "%s": parset does not exist; choices are:\n:%s' % (orig, self.parsets.keys())
                raise OptimaException(errormsg)
            else:
                self.copyparset(orig=orig, new=name) # Store parameters
        return None


    def pars(self):
        ''' Shortcut for getting the latest active set of parameters, i.e. self.parsets[-1].pars[0] '''
        return self.parsets[-1].pars[0]
    
    
    def progs(self):
        ''' Shortcut for getting the latest active set of programs '''
        return self.progsets[0].programs


    def sensitivity(self, name='perturb', orig='default', n=5, what='force', span=0.5, ind=0): # orig=default or orig=0?
        ''' Function to perform sensitivity analysis over the parameters as a proxy for "uncertainty"'''
        self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        self.parsets[name] = sensitivity(project=self, orig=self.parsets[orig], ncopies=n, what='force', span=span, ind=ind)
        self.modified = today()
        return None


    def manualfit(self, name='manualfit', orig='default', ind=0, verbose=2, **kwargs): # orig=default or orig=0?
        ''' Function to perform manual fitting '''
        self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        self.parsets[name].pars = [self.parsets[name].pars[ind]] # Keep only the chosen index
        manualfit(project=self, name=name, ind=ind, verbose=verbose, **kwargs) # Actually run manual fitting
        self.modified = today()
        return None


    def autofit(self, name=None, orig=None, fitwhat='force', fitto='prev', method='wape', maxtime=None, maxiters=1000, inds=None, verbose=2, doplot=False):
        ''' Function to perform automatic fitting '''
        self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        self.parsets[name] = autofit(project=self, name=name, fitwhat=fitwhat, fitto=fitto, method=method, maxtime=maxtime, maxiters=maxiters, inds=inds, verbose=verbose, doplot=doplot)
        results = self.runsim(name=name, addresult=False)
        results.improvement = self.parsets[name].improvement # Store in a more accessible place, since plotting functions use results
        keyname = self.addresult(result=results)
        self.parsets[name].resultsref = keyname
        self.modified = today()
        return None
    
    
    def runscenarios(self, scenlist=None, verbose=2):
        ''' Function to run scenarios '''
        if scenlist is not None: self.addscenlist(scenlist) # Replace existing scenario list with a new one
        multires = runscenarios(project=self, verbose=verbose)
        self.addresult(result=multires)
        self.modified = today()
        return None
    

    def runbudget(self, budget=None, budgetyears=None, progsetname=None, parsetname='default', verbose=2):
        ''' Function to run the model for a given budget, years, programset and parameterset '''
        if budget is None: raise OptimaException("Please enter a budget dictionary to run")
        if budgetyears is None: raise OptimaException("Please specify the years for your budget") # WARNING, the budget should probably contain the years itself
        if progsetname is None:
            try:
                progsetname = self.progsets[0].name
                printv('No program set entered to runbudget, using stored program set "%s"' % (self.progsets[0].name), 1, self.settings.verbose)
            except: raise OptimaException("No program set entered, and there are none stored in the project") 
        coverage = self.progsets[progsetname].getprogcoverage(budget=budget, t=budgetyears, parset=self.parsets[parsetname])
        progpars = self.progsets[progsetname].getpars(coverage=coverage,t=budgetyears, parset=self.parsets[parsetname])
        results = runmodel(pars=progpars, project=self, progset=self.progsets[progsetname], budget=budget, budgetyears=budgetyears) # WARNING, this should probably use runsim, but then would need to make simpars...
        results.name = 'runbudget'
        self.addresult(results)
        self.modified = today()
        return None

    
    def optimize(self, name=None, parsetname=None, progsetname=None, objectives=None, constraints=None, inds=0, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, method='asd', debug=False, saveprocess=True, overwritebudget=None, ccsample='best'):
        ''' Function to minimize outcomes or money '''
        optim = Optim(project=self, name=name, objectives=objectives, constraints=constraints, parsetname=parsetname, progsetname=progsetname)
        multires = optim.optimize(name=name, inds=inds, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method, debug=debug, overwritebudget=overwritebudget, ccsample=ccsample)
        optim.resultsref = multires.name
        if saveprocess:        
            self.addoptim(optim=optim)
            self.addresult(result=multires)
            self.modified = today()
        return multires



    #######################################################################################################
    ## Methods to handle tasks for geospatial analysis
    #######################################################################################################
        
    def genBOC(self, budgetlist=None, name=None, parsetname=None, progsetname=None, inds=0, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, method='asd'):
        ''' Function to generate project-specific budget-outcome curve for geospatial analysis '''
        projectBOC = BOC(name='BOC')
        if objectives == None:
            printv('WARNING, you have called genBOC for project "%s" without specifying obejctives. Using default objectives... ' % (self.name), 2, verbose)
            objectives = defaultobjectives(project=self, progset=progsetname)
        projectBOC.objectives = objectives
        
        if parsetname is None:
            printv('Warning, using default parset', 3, verbose)
            parsetname = 0
        
        if progsetname is None:
            printv('Warning, using default progset', 3, verbose)
            progsetname = 0
        
        if budgetlist == None:
            if not progsetname == None:
                baseline = sum(self.progsets[progsetname].getdefaultbudget().values())
            else:
                try:
                    baseline = sum(self.progsets[0].getdefaultbudget().values())
                    printv('\nWARNING: no progsetname specified. Using first saved progset "%s" in project "%s".' % (self.progsets[0].name, self.name), 1, verbose)
                except:
                    OptimaException('Error: No progsets associated with project for which BOC is being generated!')
            budgetlist = [x*baseline for x in [1.0, 0.6, 0.3, 0.1, 3.0, 6.0, 10.0]] # Start from original, go down, then go up
                
        results = None
        owbudget = None
        tmptotals = []
        tmpallocs = []
        for i,budget in enumerate(budgetlist):
            print('Running budget %i/%i (%0.0f)' % (i+1, len(budgetlist), budget))
            objectives['budget'] = budget
            optim = Optim(project=self, name=name, objectives=objectives, constraints=constraints, parsetname=parsetname, progsetname=progsetname)
            
            # All subsequent genBOC steps use the allocation of the previous step as its initial budget, scaled up internally within optimization.py of course.
            if len(tmptotals):
                closest = argmin(abs(array(tmptotals)-budget)) # Find closest budget
                owbudget = tmpallocs[closest]
                print('Using old allocation as new starting point.')
            results = optim.optimize(inds=inds, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method, overwritebudget=owbudget)
            tmptotals.append(budget)
            tmpallocs.append(dcp(results.budget['Optimal allocation']))
            projectBOC.x.append(budget)
            projectBOC.y.append(results.improvement[-1][-1])
        self.addresult(result=projectBOC)
        return None        
    
    def getBOC(self, objectives):
        ''' Returns a BOC result with the desired objectives (budget notwithstanding) if it exists, else None '''
        for x in self.results:
            if isinstance(self.results[x],BOC):
                boc = self.results[x]
                same = True
                for y in boc.objectives:
                    if y in ['start','end','deathweight','inciweight'] and boc.objectives[y] != objectives[y]: same = False
                if same:
#                    print('BOC located in project: %s' % self.name)
                    return boc
        print('No BOC with the required objectives can be found in project: %s' % self.name)
        return None
        
        
    def delBOC(self, objectives):
        ''' Deletes BOC results with the required objectives (budget notwithstanding) '''
        while not self.getBOC(objectives = objectives) == None:
            print('Deleting an old BOC...')
            ind = self.getBOC(objectives = objectives).uid
            self.rmresult(str(ind))
        return None
    
    
    def plotBOC(self, boc=None, objectives=None, deriv=False, returnplot=False, initbudget=None, optbudget=None, baseline=0):
        ''' If a BOC result with the desired objectives exists, return an interpolated object '''
        from pylab import title, show
        if boc is None:
            try: boc = self.getBOC(objectives=objectives)
            except: raise OptimaException('Cannot plot a nonexistent BOC!')
        
        if not deriv:
            print('Plotting BOC for "%s"...' % self.name)
        else:
            print('Plotting BOC derivative for "%s"...' % self.name)
        ax = boc.plot(deriv = deriv, returnplot = returnplot, initbudget = initbudget, optbudget=optbudget, baseline=baseline)
        title('Project: %s' % self.name)
        if returnplot: return ax
        else: show()
        return None



class Spreadsheet(object):
    ''' A class for reading and writing spreadsheet data in binary format, so a project contains the spreadsheet loaded '''
    
    def __init__(self, filename=None):
        self.data = None
        self.filename = None
        if filename is not None: self.load(filename)
        return None
    
    def __repr__(self):
        output = defaultrepr(self)
        return output
    
    def load(self, filename=None):
        if filename is not None:
            self.filename = filename
            with open(filename, mode='rb') as f: self.data = f.read()
    
    def save(self, filename=None, verbose=2):
        if filename is None:
            if self.filename is not None: filename = self.filename
        if filename is not None:
            with open(filename, mode='wb') as f: f.write(self.data)
        printv('Spreadsheet "%s" saved.' % filename, 2, verbose)
    
