from optima import OptimaException, Settings, Parameterset, Programset, Resultset, BOC, Parscen, Optim # Import classes
from optima import odict, getdate, today, uuid, dcp, objrepr, printv, isnumber, saveobj, promotetolist, sigfig # Import utilities
from optima import loadspreadsheet, model, gitinfo, manualfit, autofit, runscenarios, defaultscenarios, makesimpars, makespreadsheet
from optima import defaultobjectives, runmodel # Import functions
from optima import version # Get current version
from numpy import argmin, array, argsort
from numpy.random import seed, randint
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


    Methods for structure lists:
        1. add -- add a new structure to the odict
        2. remove -- remove a structure from the odict
        3. copy -- copy a structure in the odict
        4. rename -- rename a structure in the odict

    Version: 2016jan22 by cliffk
    """



    #######################################################################################################
    ### Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################

    def __init__(self, name='default', spreadsheet=None, dorun=True, makedefaults=True, verbose=2, **kwargs):
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
        self.version = version
        self.gitbranch, self.gitversion = gitinfo()
        self.filename = None # File path, only present if self.save() is used
        self.warnings = None # Place to store information about warnings (mostly used during migrations)

        ## Load spreadsheet, if available
        if spreadsheet is not None:
            self.loadspreadsheet(spreadsheet, dorun=dorun, makedefaults=makedefaults, verbose=verbose, **kwargs)

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
        output += '    Optima version: %s\n'    % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += 'Spreadsheet loaded: %s\n'    % getdate(self.spreadsheetdate)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += self.getwarnings(doprint=False) # Don't print since print later
        return output
    
    def getinfo(self):
        ''' Return an odict with basic information about the project '''
        info = odict()
        for attr in ['name', 'version', 'created', 'modified', 'spreadsheetdate', 'gitbranch', 'gitversion', 'uid']:
            info[attr] = getattr(self, attr) # Populate the dictionary
        info['parsetkeys'] = self.parsets.keys()
        info['progsetkeys'] = self.parsets.keys()
        return info

    def getwarnings(self, doprint=True):
        ''' Tiny method to print the warnings in the project, if any '''
        if hasattr(self, 'warnings') and self.warnings: # There are warnings
            output = '\nWARNING: This project contains the following warnings:'
            output += str(self.warnings)
        else: # There are no warnings
            output = ''
        if output and doprint: # Print warnings if requested
            print(output)
        return output

    #######################################################################################################
    ### Methods for I/O and spreadsheet loading
    #######################################################################################################


    def loadspreadsheet(self, filename, name='default', overwrite=True, makedefaults=True, dorun=True, **kwargs):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file '''

        ## Load spreadsheet and update metadata
        self.data = loadspreadsheet(filename, verbose=self.settings.verbose) # Do the hard work of actually loading the spreadsheet
        self.spreadsheetdate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        self.makeparset(name=name, overwrite=overwrite)
        if makedefaults: self.makedefaults(name)
        self.settings.start = self.data['years'][0] # Reset the default simulation start to initial year of data
        if dorun: self.runsim(name, addresult=True, **kwargs)
        if self.name is 'default' and filename.endswith('.xlsx'): self.name = os.path.basename(filename)[:-5] # If no project filename is given, reset it to match the uploaded spreadsheet, assuming .xlsx extension
        return None


    def makespreadsheet(self, filename=None, pops=None):
        ''' Create a spreadsheet with the data from the project'''
        if filename is None: filename = self.name+'.xlsx'
        if filename[-5:]!='.xlsx': filename += '.xlsx'
        makespreadsheet(filename=filename, pops=pops, data=self.data, datastart=self.settings.start, dataend=self.settings.dataend)
        return None


    
    def reorderpops(self, poporder=None):
        '''
        Reorder populations according to a defined list.
        
        WARNING, doesn't reorder things like circumcision or birthrates
        
        '''
        def reorder(origlist, neworder):
            return [origlist[i] for i in neworder]
        
        if self.data is None: raise OptimaException('Need to load spreadsheet before can reorder populations')
        if len(poporder) != self.data['npops']: raise OptimaException('Wrong number of populations')
        origdata = dcp(self.data)
        for key in self.data['pops']:
            self.data['pops'][key] = reorder(origdata['pops'][key], poporder)
        for key1 in self.data:
            try:
                if len(self.data[key1])==self.data['npops']:
                    self.data[key1] = reorder(origdata[key1], poporder)
                    print('    %s succeeded' % key1)
                else:
                    print('  %s wrong length' % key1)
            except:
                print('%s failed' % key1)
        
        


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
            progset = Programset(name=name, project=self)
            self.addprogset(progset)
        if overwrite or scenname not in self.scens:
            scen = Parscen(name=scenname)
            self.addscen(scen)
        if overwrite or name not in self.optims:
            optim = Optim(project=self, name=name)
            self.addoptim(optim)
        return None



    #######################################################################################################
    ### Methods to handle common tasks with structure lists
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
                    printv('Structure list already has item named "%s"' % (checkabsent), 3, self.settings.verbose)
                
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
        printv('Item "%s" added to "%s"' % (name, what), 3, self.settings.verbose)
        self.modified = today()
        return None


    def remove(self, what=None, name=None):
        ''' Remove an entry from a structure list by name '''
        if name is None: name = -1 # If no name is supplied, remove the last item
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=name)
        structlist.pop(name)
        printv('%s "%s" removed' % (what, name), 3, self.settings.verbose)
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
        printv('%s "%s" copied to "%s"' % (what, orig, new), 3, self.settings.verbose)
        self.modified = today()
        return None


    def rename(self, what=None, orig='default', new='new', overwrite=True):
        ''' Rename an entry in a structure list '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = structlist.pop(orig)
        structlist[new].name = new # Update name
        printv('%s "%s" renamed "%s"' % (what, orig, new), 3, self.settings.verbose)
        self.modified = today()
        return None
        

    #######################################################################################################
    ### Convenience functions -- NOTE, do we need these...?
    #######################################################################################################

    def addparset(self,   name=None, parset=None,   overwrite=True): self.add(what='parset',   name=name, item=parset,  overwrite=overwrite)
    def addprogset(self,  name=None, progset=None,  overwrite=True): self.add(what='progset',  name=name, item=progset, overwrite=overwrite)
    def addscen(self,     name=None, scen=None,     overwrite=True): self.add(what='scen',     name=name, item=scen,    overwrite=overwrite)
    def addoptim(self,    name=None, optim=None,    overwrite=True): self.add(what='optim',    name=name, item=optim,   overwrite=overwrite)

    def rmparset(self,   name=None): self.remove(what='parset',   name=name)
    def rmprogset(self,  name=None): self.remove(what='progset',  name=name)
    def rmscen(self,     name=None): self.remove(what='scen',     name=name)
    def rmoptim(self,    name=None): self.remove(what='optim',    name=name)


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
        self.modified = today()
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
        self.modified = today()
        return None
    
    
    def cleanresults(self):
        ''' Remove all results except for BOCs '''
        for key,result in self.results.items():
            if type(result)!=BOC: self.results.pop(key)
        self.modified = today()
        return None
    
    
    def addscenlist(self, scenlist): 
        ''' Function to make it slightly easier to add scenarios all in one go -- WARNING, should make this a general feature of add()! '''
        for scen in scenlist: self.addscen(name=scen.name, scen=scen, overwrite=True)
        self.modified = today()
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
    ### Utilities
    #######################################################################################################


    def refreshparset(self, name=None, orig='default'):
        '''
        Reset the chosen (or all) parsets to reflect the parameter values from the spreadsheet (or another parset).
        
        Usage:
            P.refreshparset() # Refresh all parsets in the project to match 'default'
            P.refreshparset(name='calibrated') # Reset parset 'calibrated' to match 'default'
            P.refreshparset(name=['default', 'bugaboo'], orig='calibrated') # Reset parsets 'default' and 'bugaboo' to match 'calibrated'
        '''
        
        if name is None: name = self.parsets.keys() # If none is given, use all
        name = promotetolist(name) # Make sure it's a list
        origpars = self.parsets[orig].pars # "Original" parameters to copy from (based on data)
        for parset in [self.parsets[n] for n in name]: # Loop over all named parsets
            keys = parset.pars.keys() # Assume all pars structures have the same keys
            newpars = parset.pars
            for key in keys:
                if hasattr(newpars[key],'y'): newpars[key].y = origpars[key].y # Reset y (value) variable, if it exists
                if hasattr(newpars[key],'t'): newpars[key].t = origpars[key].t # Reset t (time) variable, if it exists
        
        self.modified = today()
        return None
        
        

    def reconcileparsets(self, name=None, orig=None):
        ''' Helper function to copy a parset if required -- used by sensitivity, manualfit, and autofit '''
        if name is None and orig is None: # Nothing supplied, just use defaults
            name = -1
            orig = -1
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
        return name, orig


    def pars(self, key=-1):
        ''' Shortcut for getting the latest active set of parameters, i.e. self.parsets[-1].pars '''
        return self.parsets[key].pars
    
    def progs(self, key=-1):
        ''' Shortcut for getting the latest active set of programs, i.e. self.progsets[-1].programs '''
        return self.progsets[key].programs
    
    def parset(self, key=-1):
        ''' Shortcut for getting the latest active parameters set, i.e. self.parsets[-1] '''
        return self.parsets[key]
    
    def programs(self, key=-1):
        ''' Shortcut for getting the latest active set of programs '''
        return self.progsets[key].programs

    def progset(self, key=-1):
        ''' Shortcut for getting the latest active program set, i.e. self.progsets[-1]'''
        return self.progsets[key]
    
    def result(self, key=-1):
        ''' Shortcut for getting the latest active results, i.e. self.results[-1]'''
        return self.results[key]


    #######################################################################################################
    ### Methods to perform major tasks
    #######################################################################################################


    def runsim(self, name=None, simpars=None, start=None, end=None, dt=None, addresult=True, die=True, debug=False, overwrite=True, n=1, sample=False, tosample=None, randseed=None, verbose=None, keepraw=False, **kwargs):
        ''' 
        This function runs a single simulation, or multiple simulations if n>1.
        
        Version: 2016nov07
        '''
        if start is None: start=self.settings.start # Specify the start year
        if end is None: end=self.settings.end # Specify the end year
        if dt is None: dt=self.settings.dt # Specify the timestep
        if name is None: name = -1 # Set default name
        if verbose is None: verbose = self.settings.verbose
        
        # Get the parameters sorted
        if simpars is None: # Optionally run with a precreated simpars instead
            simparslist = [] # Needs to be a list
            if n>1 and sample is None: sample = 'new' # No point drawing more than one sample unless you're going to use uncertainty
            if randseed is not None: seed(randseed) # Reset the random seed, if specified
            for i in range(n):
                sampleseed = randint(0,2**32-1)
                simparslist.append(makesimpars(self.parsets[name].pars, start=start, end=end, dt=dt, settings=self.settings, name=name, sample=sample, tosample=tosample, randseed=sampleseed))
        else:
            simparslist = promotetolist(simpars)

        # Run the model! -- WARNING, the logic of this could be cleaned up a lot!
        rawlist = []
        for ind,simpars in enumerate(simparslist):
            raw = model(simpars, self.settings, die=die, debug=debug, verbose=verbose, label=self.name, **kwargs) # ACTUALLY RUN THE MODEL
            rawlist.append(raw)

        # Store results -- WARNING, is this correct in all cases?
        resultname = 'parset-'+self.parsets[name].name 
        results = Resultset(name=resultname, raw=rawlist, simpars=simparslist, project=self, keepraw=keepraw, verbose=verbose) # Create structure for storing results
        if addresult:
            keyname = self.addresult(result=results, overwrite=overwrite)
            self.parsets[name].resultsref = keyname # If linked to a parset, store the results

        self.modified = today()
        return results


    def sensitivity(self, name='perturb', orig='default', n=5, tosample=None, randseed=None, **kwargs): # orig=default or orig=0?
        '''
        Function to perform sensitivity analysis over the parameters as a proxy for "uncertainty".
        
        Specify tosample as a string or list of par.auto types to only look at sensitivity in a subset
        of parameters. Set to None for all. For example:
        
        P.sensitivity(n=5, tosample='force')
        '''
        name, orig = self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        results = self.runsim(name=name, n=n, sample='new', tosample=tosample, randseed=randseed, **kwargs)
        self.modified = today()
        return results


    def manualfit(self, orig=None, parsubset=None, name=None, verbose=2, **kwargs): # orig=default or orig=0?
        ''' Function to perform manual fitting '''
        name, orig = self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        manualfit(project=self, name=name, parsubset=parsubset, verbose=verbose, **kwargs) # Actually run manual fitting
        self.modified = today()
        return None


    def autofit(self, name=None, orig=None, fitwhat='force', fitto='prev', method='wape', maxtime=None, maxiters=1000, verbose=2, doplot=False):
        ''' Function to perform automatic fitting '''
        name, orig = self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        self.parsets[name] = autofit(project=self, name=name, fitwhat=fitwhat, fitto=fitto, method=method, maxtime=maxtime, maxiters=maxiters, verbose=verbose, doplot=doplot)
        results = self.runsim(name=name, addresult=False)
        results.improvement = self.parsets[name].improvement # Store in a more accessible place, since plotting functions use results
        keyname = self.addresult(result=results)
        self.parsets[name].resultsref = keyname
        self.modified = today()
        return None
    
    
    def runscenarios(self, scenlist=None, verbose=2, debug=False, **kwargs):
        ''' Function to run scenarios '''
        if scenlist is not None: self.addscenlist(scenlist) # Replace existing scenario list with a new one
        multires = runscenarios(project=self, verbose=verbose, debug=debug, **kwargs)
        self.addresult(result=multires)
        self.modified = today()
        return None
    
    def defaultscenarios(self, **kwargs):
        ''' Wrapper for default scenarios '''
        defaultscenarios(self, **kwargs)
        return None
    

    def runbudget(self, name='runbudget', budget=None, budgetyears=None, progsetname=None, parsetname='default', verbose=2):
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
        results = runmodel(pars=progpars, project=self, parset=self.parsets[parsetname], progset=self.progsets[progsetname], budget=budget, budgetyears=budgetyears, label=self.name+'-runbudget') # WARNING, this should probably use runsim, but then would need to make simpars...
        results.name = name
        self.addresult(results)
        self.modified = today()
        return None

    
    def optimize(self, name=None, parsetname=None, progsetname=None, objectives=None, constraints=None, maxiters=1000,
                 maxtime=None, verbose=2, stoppingfunc=None, method='asd', die=False, saveprocess=True, origbudget=None, ccsample='best', randseed=None, **kwargs):
        ''' Function to minimize outcomes or money '''
        optim = Optim(project=self, name=name, objectives=objectives, constraints=constraints, parsetname=parsetname, progsetname=progsetname)
        multires = optim.optimize(name=name, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, 
                                  method=method, die=die, origbudget=origbudget, ccsample=ccsample, randseed=randseed, **kwargs)
        optim.resultsref = multires.name
        if saveprocess:        
            self.addoptim(optim=optim)
            self.addresult(result=multires)
            self.modified = today()
        return multires



    #######################################################################################################
    ## Methods to handle tasks for geospatial analysis
    #######################################################################################################
        
    def genBOC(self, budgetratios=None, name=None, parsetname=None, progsetname=None, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, method='asd', mc=3, die=False, **kwargs):
        ''' Function to generate project-specific budget-outcome curve for geospatial analysis '''
        boc = BOC(name='BOC '+self.name)
        if objectives is None:
            printv('Warning, genBOC "%s" did not get objectives, using defaults...' % (self.name), 2, verbose)
            objectives = defaultobjectives(project=self, progset=progsetname)
        boc.objectives = objectives
        boc.constraints = constraints
        
        if parsetname is None:
            printv('Warning, using default parset', 3, verbose)
            parsetname = -1
        
        if progsetname is None:
            printv('Warning, using default progset', 3, verbose)
            progsetname = -1
        
        defaultbudget = self.progsets[progsetname].getdefaultbudget()
        
        if budgetratios is None:
            budgetratios = [1.0, 0.8, 0.5, 0.3, 0.1, 0.01, 1.5, 3.0, 5.0, 10.0, 30.0, 100.0]
        
        # Calculate the number of iterations
        noptims = 1+(mc!=0)*3+max(mc,0) # Calculate the number of optimizations per BOC point
        nbocpts = len(budgetratios)
        guessstalliters = 50  # WARNING, shouldn't hardcode stalliters but doesn't really matter, either
        guessmaxiters = maxiters if maxiters is not None else 1000
        estminiters = noptims*nbocpts*guessstalliters
        estmaxiters = noptims*nbocpts*guessmaxiters
        printv('Generating BOC for %s for %0.0f-%0.0f with weights deaths=%0.1f, infections=%0.1f (est. %i-%i iterations)' % (self.name, objectives['start'], objectives['end'], objectives['deathweight'], objectives['inciweight'], estminiters, estmaxiters), 1, verbose)
        
        # Initialize arrays
        budgetdict = odict()
        for budgetratio in budgetratios:
            budgetdict['%s'%budgetratio] = budgetratio # Store the budget ratios as a dicitonary
        tmptotals = odict()
        tmpallocs = odict()
        tmpoutcomes = odict()
        counts = odict([(key,0) for key in budgetdict.keys()]) # Initialize to zeros -- count how many times each budget is run
        while len(budgetdict):
            key, ratio = budgetdict.items()[0] # Use first budget in the stack
            counts[key] += 1
            budget = ratio*sum(defaultbudget[:])
            printv('Running budget %i/%i (%0.0f)' % (sum(counts[:]), len(budgetdict)+sum(counts[:])-1, budget), 2, verbose)
            objectives['budget'] = budget
            optim = Optim(project=self, name=name, objectives=objectives, constraints=constraints, parsetname=parsetname, progsetname=progsetname)
            
            # All subsequent genBOC steps use the allocation of the previous step as its initial budget, scaled up internally within optimization.py of course.
            if len(tmptotals):
                closest = argmin(abs(tmptotals[:]-budget)) # Find closest budget
                owbudget = tmpallocs[closest]
            else:
                owbudget = None
            label = self.name+' $%sm' % sigfig(budget/1e6, sigfigs=3)
            
            # Actually run
            results = optim.optimize(maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method, origbudget=owbudget, label=label, mc=mc, die=die, **kwargs)
            tmptotals[key] = budget
            tmpallocs[key] = dcp(results.budget['Optimal'])
            tmpoutcomes[key] = results.improvement[-1][-1]
            boc.x.append(budget)
            boc.y.append(tmpoutcomes[-1])
            boc.budgets[key] = tmpallocs[-1]
            
            # Check that the BOC points are monotonic, and if not, rerun
            budgetdict.pop(key) # Remove the current key from the list
            for oldkey in tmpoutcomes.keys():
                if tmpoutcomes[oldkey]>tmpoutcomes[key] and tmptotals[oldkey]>tmptotals[key]: # Outcome is worse but budget is larger
                    printv('WARNING, outcome for %s is worse than outcome for %s, rerunning...' % (oldkey, key), 1, verbose)
                    if counts[oldkey]<5: # Don't get stuck in an infinite loop -- 5 is arbitrary, but jeez, that should take care of it
                        budgetdict.insert(0, oldkey, float(oldkey)) # e.g. key2='0.8'
                    else:
                        printv('WARNING, tried 5 times to reoptimize budget and unable to get lower', 1, verbose) # Give up
                        
        # Tidy up: insert remaining points
        if sum(counts[:]):
            xorder = argsort(boc.x) # Sort everything
            boc.x = array(boc.x)[xorder].tolist()
            boc.y = array(boc.y)[xorder].tolist()
            boc.budgets.sort(xorder)
            boc.x.insert(0, 0) # Add the zero-budget point to the beginning of the list
            boc.y.insert(0, results.outcomes['Zero']) # It doesn't matter which results these come from
            boc.yinf = results.outcomes['Infinite'] # Store infinite money, but not as part of the BOC
            boc.parsetname = parsetname
            boc.progsetname = progsetname
            boc.defaultbudget = dcp(defaultbudget)
            self.addresult(result=boc)
            self.modified = today()
        else:
            errormsg = 'BOC generation failed: no BOC points were calculated'
            raise OptimaException(errormsg)
        return None        
    
    
    def getBOC(self, objectives=None):
        ''' Returns a BOC result with the desired objectives (budget notwithstanding) if it exists, else None '''
        
        boc = None
        for x in reversed(self.results.keys()): # Get last BOC
            if isinstance(self.results[x],BOC):
                boc = self.results[x]
                if objectives is None: return boc
                same = True
                for y in boc.objectives:
                    if y in ['start','end','deathweight','inciweight'] and boc.objectives[y] != objectives[y]: same = False
                if same:
                    return boc
        print('No BOC with the required objectives can be found in project: %s; using last BOC found' % self.name)
        if boc is None:
            print('WARNING, no BOCs found!')
        return boc
        
        
    def delBOC(self, objectives):
        ''' Deletes BOC results with the required objectives (budget notwithstanding) '''
        while not self.getBOC(objectives = objectives) == None:
            print('Deleting an old BOC...')
            ind = self.getBOC(objectives = objectives).uid
            self.rmresult(str(ind))
        self.modified = today()
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
    
