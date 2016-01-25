from optima import OptimaException, Settings, Parameterset, Programset, Resultset, Optim # Import classes
from optima import odict, getdate, today, uuid, dcp, objrepr, printv # Import utilities
from optima import loadspreadsheet, model, gitinfo, sensitivity, manualfit, autofit, runscenarios, minoutcomes, loadeconomicsspreadsheet, runmodel # Import functions
from optima import __version__ # Get current version


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

    def __init__(self, name='default', spreadsheet=None):
        ''' Initialize the project '''

        ## Define the structure sets
        self.parsets  = odict()
        self.progsets = odict()
        self.scens    = odict()
        self.optims   = odict()
        self.results  = odict()

        ## Define other quantities
        self.name = name
        self.settings = Settings() # Global settings
        self.data = {} # Data from the spreadsheet

        ## Define metadata
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        self.version = __version__
        self.gitbranch, self.gitversion = gitinfo()

        ## Load spreadsheet, if available
        if spreadsheet is not None:
            self.loadspreadsheet(spreadsheet)

        return None


    def __repr__(self):
        ''' Print out useful information when called '''
        output = '============================================================\n'
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
        output += objrepr(self)
        return output


    #######################################################################################################
    ## Methods for I/O and spreadsheet loading
    #######################################################################################################


    def loadspreadsheet(self, filename, name='default', dorun=True):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file '''

        ## Load spreadsheet and update metadata
        self.data = loadspreadsheet(filename) # Do the hard work of actually loading the spreadsheet
        self.spreadsheetdate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        self.ensureparset(name)
        if dorun: self.runsim(name, addresult=True)
        return None


    def ensureparset(self, name='default'):
        ''' If parameter set of that name doesn't exist, create it'''
        # question: what is that parset does exist? delete it first?
        if not self.data:
            raise OptimaException("No data in project %s!" % self.uid)
        if name not in self.parsets:
            parset = Parameterset(name=name, project=self)
            parset.makepars(self.data) # Create parameters
            self.addparset(name=name, parset=parset) # Store parameters
            self.modified = today()
        return None

    def loadeconomics(self, filename):
        ''' Load economic data and tranforms it to useful format'''

        ## Load spreadsheet
        self.data['econ'] = loadeconomicsspreadsheet(filename)
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


    def checkname(self, what=None, checkexists=None, checkabsent=None, overwrite=False):
        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
        if type(what)==odict: structlist=what # It's already a structlist
        else: structlist = self.getwhat(what=what)
        if isinstance(checkexists, (int, float)): # It's a numerical index
            try: checkexists = structlist.keys()[checkexists] # Convert from 
            except: raise OptimaException('Index %i is out of bounds for structure list "%s" of length %i' % (checkexists, what, len(structlist)))
        if checkabsent is not None:
            if checkabsent in structlist:
                if overwrite==False:
                    raise OptimaException('Structure list "%s" already has item named "%s"' % (what, checkabsent))
                else:
                    printv('Structure list "%s" already has item named "%s"' % (what, checkabsent), 2, self.settings.verbose)
                
        if checkexists is not None:
            if not checkexists in structlist:
                raise OptimaException('Structure list "%s" has no item named "%s"' % (what, checkexists))
        return None


    def add(self, name=None, item=None, what=None, overwrite=False, consistentnames=True):
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
        printv('Item "%s" added to structure list "%s"' % (name, what), 1, self.settings.verbose)
        self.modified = today()
        return None


    def remove(self, what=None, name=None):
        ''' Remove an entry from a structure list by name '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=name)
        structlist.pop(name)
        printv('Item "%s" removed from structure list "%s"' % (name, what), 1, self.settings.verbose)
        self.modified = today()
        return None


    def copy(self, what=None, orig='default', new='copy', overwrite=False):
        ''' Copy an entry in a structure list '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = dcp(structlist[orig])
        structlist[new].name = new  # Update name
        structlist[new].uid = uuid()  # Otherwise there will be 2 structures with same unique identifier
        structlist[new].created = today() # Update dates
        structlist[new].modified = today() # Update dates
        if hasattr(structlist[new], 'project'): structlist[new].project = self # Preserve information about project -- don't deep copy -- WARNING, may not work?
        printv('Item "%s" copied to structure list "%s"' % (new, what), 1, self.settings.verbose)
        self.modified = today()
        return None


    def rename(self, what=None, orig='default', new='new', overwrite=False):
        ''' Rename an entry in a structure list '''
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = structlist.pop(orig)
        structlist[new].name = new # Update name
        printv('Item "%s" renamed to "%s" in structure list "%s"' % (orig, new, what), 1, self.settings.verbose)
        self.modified = today()
        return None



    #######################################################################################################
    ## Convenience functions -- NOTE, do we need these...?
    #######################################################################################################

    def addparset(self,   name=None, parset=None,   overwrite=False): self.add(what='parset',   name=name, item=parset,  overwrite=overwrite)
    def addprogset(self,  name=None, progset=None,  overwrite=False): self.add(what='progset',  name=name, item=progset, overwrite=overwrite)
    def addscen(self,     name=None, scen=None,     overwrite=False): self.add(what='scen',     name=name, item=scen,    overwrite=overwrite)
    def addoptim(self,    name=None, optim=None,    overwrite=False): self.add(what='optim',    name=name, item=optim,   overwrite=overwrite)

    def rmparset(self,   name): self.remove(what='parset',   name=name)
    def rmprogset(self,  name): self.remove(what='progset',  name=name)
    def rmscen(self,     name): self.remove(what='scen',     name=name)
    def rmoptim(self,    name): self.remove(what='optim',    name=name)


    def copyparset(self,   orig='default', new='new', overwrite=False): self.copy(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def copyprogset(self,  orig='default', new='new', overwrite=False): self.copy(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def copyscen(self,     orig='default', new='new', overwrite=False): self.copy(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def copyoptim(self,    orig='default', new='new', overwrite=False): self.copy(what='optim',    orig=orig, new=new, overwrite=overwrite)

    def renameparset(self,   orig='default', new='new', overwrite=False): self.rename(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def renameprogset(self,  orig='default', new='new', overwrite=False): self.rename(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def renamescen(self,     orig='default', new='new', overwrite=False): self.rename(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def renameoptim(self,    orig='default', new='new', overwrite=False): self.rename(what='optim',    orig=orig, new=new, overwrite=overwrite)

    def addresult(self, result=None): self.add(what='result',  name=str(result.uid), item=result, consistentnames=False) # Use UID for key but keep name
    
    
    def rmresult(self, name=-1):
        resultuids = self.results.keys() # Pull out UID keys
        resultnames = [res.name for res in self.results.values()] # Pull out names
        if isinstance(name, (int, float)) and name<len(self.results):  # Remove by index rather than name
            self.remove(what='result', name=self.results.keys()[name])
        elif name in resultuids: # It's a UID: remove directly 
            self.remove(what='result', name=name)
        elif name in resultnames: # It's a name: find the UID corresponding to this name and remove
            self.remove(what='result', name=resultuids[resultnames.index(name)]) # WARNING, if multiple names match, will delete oldest one -- expected behavior?
        else:
            validchoices = ['#%i: name="%s", uid=%s' % (i, resultnames[i], resultuids[i]) for i in range(len(self.results))]
            errormsg = 'Could not remove result "%s": choices are:\n%s' % (name, '\n'.join(validchoices))
            raise OptimaException(errormsg)
    
    
    def addscenlist(self, scenlist): 
        ''' Function to make it slightly easier to add scenarios all in one go -- WARNING, should make this a general feature of add()! '''
        for scen in scenlist: self.addscen(name=scen.name, scen=scen, overwrite=True)
        return None




    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################


    def runsim(self, name=None, simpars=None, start=None, end=None, dt=None, addresult=True):
        ''' This function runs a single simulation, or multiple simulations if pars/simpars is a list '''
        if start is None: start=self.settings.start # Specify the start year
        if end is None: end=self.settings.end # Specify the end year
        if dt is None: dt=self.settings.dt # Specify the timestep
        if name is None and simpars is None: name = 'default' # Set default name

        # Get the parameters sorted
        if simpars is None: # Optionally run with a precreated simpars instead
            simparslist = self.parsets[name].interp(start=start, end=end, dt=dt) # "self.parset[name]" is e.g. P.parset['default']
        else:
            if type(simpars)==list: simparslist = simpars
            else: simparslist = [simpars]

        # Run the model!
        rawlist = []
        for ind in range(len(simparslist)):
            raw = model(simparslist[ind], self.settings) # THIS IS SPINAL OPTIMA
            rawlist.append(raw)

        # Store results -- WARNING, is this correct in all cases?
        resultname = 'parset-'+name if simpars is None else 'simpars'
        results = Resultset(name=resultname, raw=rawlist, simpars=simparslist, project=self) # Create structure for storing results
        if addresult:
            self.addresult(result=results)
            if simpars is None: self.parsets[name].resultsref = results.uid # If linked to a parset, store the results

        return results



    def sensitivity(self, name='perturb', orig='default', n=5, what='force', span=0.5, ind=0): # orig=default or orig=0?
        ''' Function to perform sensitivity analysis over the parameters as a proxy for "uncertainty"'''
        parset = sensitivity(project=self, orig=self.parsets[orig], ncopies=n, what='force', span=span, ind=ind)
        self.addparset(name=name, parset=parset) # Store parameters
        self.modified = today()
        return None


    def manualfit(self, name='manualfit', orig='default', ind=0, verbose=2): # orig=default or orig=0?
        ''' Function to perform manual fitting '''
        self.copyparset(orig=orig, new=name) # Store parameters
        self.parsets[name].pars = [self.parsets[name].pars[ind]] # Keep only the chosen index
        manualfit(project=self, name=name, ind=ind, verbose=verbose) # Actually run manual fitting
        self.modified = today()
        return None


    def autofit(self, name='autofit', orig='default', what='force', maxtime=None, maxiters=100, inds=None, verbose=2):
        ''' Function to perform automatic fitting '''
        self.copyparset(orig=orig, new=name) # Store parameters -- WARNING, shouldn't copy, should create new!
        self.parsets[name] = autofit(project=self, name=name, what=what, maxtime=maxtime, maxiters=maxiters, inds=inds, verbose=verbose)
        results = self.runsim(name=name, addresult=False)
        results.improvement = self.parsets[name].improvement # Store in a more accessible place, since plotting functions use results
        self.addresult(result=results)
        self.parsets[name].resultsref = results.uid
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
        self.addresult(results)
        self.modified = today()
        return None

    
    def minoutcomes(self, name=None, parsetname=None, progsetname=None, inds=0, objectives=None, constraints=None, maxiters=1000, maxtime=None, verbose=5, stoppingfunc=None, method='asd'):
        ''' Function to minimize outcomes '''
        optim = Optim(project=self, name=name, objectives=objectives, constraints=constraints, parsetname=parsetname, progsetname=progsetname)
        multires = minoutcomes(project=self, optim=optim, inds=inds, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, method=method)
        self.addoptim(optim=optim)
        self.addresult(result=multires)
        self.modified = today()
        return None
