from optima import OptimaException, Settings, Parameterset, Programset, Resultset, BOC, Parscen, Budgetscen, Coveragescen, Progscen, Optim, Link # Import classes
from optima import odict, getdate, today, uuid, dcp, makefilepath, objrepr, printv, isnumber, saveobj, promotetolist, promotetoodict, sigfig # Import utilities
from optima import loadspreadsheet, model, gitinfo, defaultscenarios, makesimpars, makespreadsheet
from optima import defaultobjectives, autofit, runscenarios, optimize, multioptimize, tvoptimize, outcomecalc, icers # Import functions
from optima import version, cpu_count # Get current version
from numpy import argmin, argsort, nan, ceil
from numpy.random import seed, randint
from time import time
from sciris import parallelize

import os

__all__ = [
    'Project'
]

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

    Version: 2017oct30
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
        self.data = odict() # Data from the spreadsheet

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
        if spreadsheet:
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
        ''' Return an odict with basic information about the project -- used in resultsets '''
        info = odict()
        for attr in ['name', 'version', 'created', 'modified', 'spreadsheetdate', 'gitbranch', 'gitversion', 'uid']:
            info[attr] = getattr(self, attr) # Populate the dictionary
        info['parsetkeys'] = self.parsets.keys()
        info['progsetkeys'] = self.progsets.keys()
        return info
    
    
    def addwarning(self, message=None, **kwargs):
        ''' Add a warning to the project, which is printed when migrated or loaded '''
        if not hasattr(self, 'warnings') or type(self.warnings)!=str: # If no warnings attribute, create it
            self.warnings = ''
        self.warnings += '\n'*3+str(message) # # Add this warning
        return None


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

    def loadspreadsheet(self, filename=None, folder=None, name=None, overwrite=True, makedefaults=None, refreshparsets=None, dorun=True, **kwargs):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file
        :param overwrite: whether to replace an existing spreadsheet if it has the same name as specified
        :param makedefaults: whether to add a default parset, progset, scenario, and optimization to the project.
        :param refreshparsets: Boolean for whether to update with the new data. Happens AFTER creating new parset if requested (may refresh the same parset!)
        '''
        ## Load spreadsheet and update metadata
        newdata = loadspreadsheet(filename=filename, folder=folder, verbose=self.settings.verbose) # Do the hard work of actually loading the spreadsheet
        firstbook = True if self.data==odict() else False #is this the first time a databook has ever been loaded to the project?
        if refreshparsets is None:
            refreshparsets = False if firstbook else True #Generally True unless making a first parset in which case no need to refresh it immediately
        if makedefaults is None:
            makedefaults = True if firstbook else False #Probably don't want defaults if there was already some data (unless parset/progset are entirely missing but that's handled below)
        
        if (not firstbook) and newdata['pops']['short'] != self.data['pops']['short']:
            raise OptimaException('Loading a databook with different population short names to the existing project is not allowed: create a new project instead.')
        self.data = newdata
        self.spreadsheetdate = today() # Update date when spreadsheet was last loaded
        self.modified = today()
        
        
        if makedefaults or self.parsets==odict(): #always make a new parset if there isn't one
            if name is None: name = 'default'
            self.makeparset(name=name, overwrite=overwrite)
        else:
            if name is None: name = self.parsets[-1].name #Use the most recent parset if not creating a new one.
        if makedefaults or self.progsets==odict(): #always make a new progset (and default scenario/opt) if there isn't one
            self.makedefaults(name)
        
        if refreshparsets:
            self.refreshparset(name=None, orig=None, resetprevalence=False) #name=None means refresh ALL parsets, orig=None means from data, resetprevalence means don't update initprev
        
        self.settings.start = self.data['years'][0] # Reset the default simulation start to initial year of data
        if dorun: self.runsim(name, addresult=True, **kwargs) # Pass all kwargs to runsim as well
        if self.name == 'default' and filename.endswith('.xlsx'): self.name = os.path.basename(filename)[:-5] # If no project filename is given, reset it to match the uploaded spreadsheet, assuming .xlsx extension
        return None


    def makespreadsheet(self, filename=None, folder=None, pops=None, datastart=None, dataend=None):
        ''' Create a spreadsheet with the data from the project'''
        fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='xlsx')
        if datastart is None: 
            try:    datastart = self.data['years'][0]
            except: datastart = self.settings.start
        if dataend is None:   
            try:    dataend = self.data['years'][-1]
            except: dataend = self.settings.dataend
        makespreadsheet(filename=fullpath, pops=pops, data=self.data, datastart=datastart, dataend=dataend)
        return fullpath


    
#    def reorderpops(self, poporder=None):
#        '''
#        Reorder populations according to a defined list.
#        
#        WARNING, doesn't reorder things like circumcision or birthrates, or programsets, or anything...
#        
#        '''
#        def reorder(origlist, neworder):
#            return [origlist[i] for i in neworder]
#        
#        if self.data is None: raise OptimaException('Need to load spreadsheet before can reorder populations')
#        if len(poporder) != self.data['npops']: raise OptimaException('Wrong number of populations')
#        origdata = dcp(self.data)
#        for key in self.data['pops']:
#            self.data['pops'][key] = reorder(origdata['pops'][key], poporder)
#        for key1 in self.data:
#            try:
#                if len(self.data[key1])==self.data['npops']:
#                    self.data[key1] = reorder(origdata[key1], poporder)
#                    print('    %s succeeded' % key1)
#                else:
#                    print('  %s wrong length' % key1)
#            except:
#                print('%s failed' % key1)
        

    def makeparset(self, name='default', overwrite=False, dosave=True, die=False):
        ''' If parameter set of that name doesn't exist, create it '''
        if not self.data:
            raise OptimaException('No data in project "%s"!' % self.name)
        parset = Parameterset(name=name, project=self)
        parset.makepars(self.data, verbose=self.settings.verbose, start=self.settings.start, end=self.settings.end) # Create parameters
        if dosave: # Save to the project if requested
            if name in self.parsets and not overwrite: # and overwrite if requested
                errormsg = 'Cannot make parset "%s" because it already exists (%s) and overwrite is off' % (name, self.parsets.keys())
                if die: raise OptimaException(errormsg) # Probably not a big deal, so...
                else:   printv(errormsg, 3, verbose=self.settings.verbose) # ...don't even print it except with high verbose settings
            else:
                self.addparset(name=name, parset=parset, overwrite=overwrite) # Store parameters
                self.modified = today()
        return parset


    def makedefaults(self, name=None, scenname=None, overwrite=False):
        ''' When creating a project, create a default program set, scenario, and optimization to begin with '''

        # Handle inputs
        if name is None: name = 'default'
        if scenname is None: scenname = 'default'

        # Make default progset, scenarios and optimizations
        if overwrite or name not in self.progsets:
            progset = Programset(name=name, project=self)
            self.addprogset(progset)

        if overwrite or scenname not in self.scens:
            scenlist = [Parscen(name=scenname, parsetname=name,pars=[])]
            self.addscens(scenlist)

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
        if isinstance(what, dict): structlist=what # It's already a structlist
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
        if item is None:
            if type(name)!=str: # Maybe an item has been supplied as the only argument
                try: 
                    item = name # It's actully an item, not a name
                    name = item.name # Try getting name from the item
                except: raise OptimaException('Could not figure out how to add item with name "%s" and item "%s"' % (name, item))
            else: # No item has been supplied, add a default one
                if what=='parset':  
                    item = Parameterset(name=name, project=self)
                    item.makepars(self.data, verbose=self.settings.verbose) # Create parameters
                elif what=='progset': 
                    item = Programset(name=name, project=self)
                elif what=='scen':
                    item = Parscen(name=name)
                elif what=='optim': 
                    item = Optim(project=self, name=name)
                else:
                    raise OptimaException('Unable to add item of type "%s", please supply explicitly' % what)
        structlist = self.getwhat(item=item, what=what)
        self.checkname(structlist, checkabsent=name, overwrite=overwrite)
        structlist[name] = item
        if consistentnames: structlist[name].name = name # Make sure names are consistent -- should be the case for everything except results, where keys are UIDs
        if hasattr(structlist[name], 'projectref'): structlist[name].projectref = Link(self) # Fix project links
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


    def copy(self, what=None, orig=None, new=None, overwrite=True):
        ''' Copy an entry in a structure list '''
        if orig is None: orig = -1
        if new  is None: new = 'new'
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = dcp(structlist[orig])
        structlist[new].name = new  # Update name
        structlist[new].uid = uuid()  # Otherwise there will be 2 structures with same unique identifier
        structlist[new].created = today() # Update dates
        structlist[new].modified = today() # Update dates
        if hasattr(structlist[new], 'projectref'): structlist[new].projectref = Link(self) # Fix project links
        printv('%s "%s" copied to "%s"' % (what, orig, new), 3, self.settings.verbose)
        self.modified = today()
        return None


    def rename(self, what=None, orig=None, new=None, overwrite=True):
        ''' Rename an entry in a structure list '''
        if orig is None: orig = -1
        if new  is None: new = 'new'
        structlist = self.getwhat(what=what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist.rename(oldkey=orig, newkey=new)
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


    def copyparset(self,  orig=None, new=None, overwrite=True): self.copy(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def copyprogset(self, orig=None, new=None, overwrite=True): self.copy(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def copyscen(self,    orig=None, new=None, overwrite=True): self.copy(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def copyoptim(self,   orig=None, new=None, overwrite=True): self.copy(what='optim',    orig=orig, new=new, overwrite=overwrite)

    def renameparset(self,  orig=None, new=None, overwrite=True): self.rename(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def renameprogset(self, orig=None, new=None, overwrite=True): self.rename(what='progset',  orig=orig, new=new, overwrite=overwrite)
    def renamescen(self,    orig=None, new=None, overwrite=True): self.rename(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def renameoptim(self,   orig=None, new=None, overwrite=True): self.rename(what='optim',    orig=orig, new=new, overwrite=overwrite)


    def addscens(self, scenlist, overwrite=True): 
        ''' Function to make it slightly easier to add scenarios all in one go '''
        if overwrite: self.scens = odict() # Remove any existing scenarios
        scenlist = promotetolist(scenlist) # Allow adding a single scenario
        for scen in scenlist: self.addscen(name=scen.name, scen=scen, overwrite=True)
        self.modified = today()
        return None


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
        return None
    
    
    def cleanresults(self):
        ''' Remove all results except for BOCs '''
        for key,result in self.results.items():
            if type(result)!=BOC: self.results.pop(key)
        return None

    def cleanparsfromscens(self):
        ''' Remove the scenparset from Scen objects and pars too if it is a Progscen.
            These are not needed to re-run the Scenarios and take up space if saving to .prj.
        '''
        for scen in self.scens.values():
            if isinstance(scen,Progscen):
                if hasattr(scen,'pars'):   del scen.pars  # pars of a Progscen get re-generated when run, only needed in a Parscen
            if hasattr(scen,'scenparset'): scen.scenparset = None  # scenparset always gets re-generated
    
    def save(self, filename=None, folder=None, saveresults=False, verbose=2, advancedtracking=False, cleanparsfromscens=None):
        ''' Save the current project, by default using its name, and without results '''
        if cleanparsfromscens is None: cleanparsfromscens = not saveresults  # Default to cleaning if we are not saving results
        origadvancedtracking = self.settings.advancedtracking
        self.settings.advancedtracking = advancedtracking # Default to turning advancedtracking off
        fullpath = makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext='prj', sanitize=True)
        self.filename = fullpath # Store file path
        if saveresults and not cleanparsfromscens:
            fullpath = saveobj(fullpath, self, verbose=verbose)
        else:
            tmpproject = dcp(self) # Need to do this so we don't clobber the existing results
            tmpproject.restorelinks() # Make sure links are restored
            if not saveresults:    tmpproject.cleanresults()       # Get rid of all results
            if cleanparsfromscens: tmpproject.cleanparsfromscens() # Get rid of (unnecessary) parameters from scenarios
            fullpath = saveobj(fullpath, tmpproject, verbose=verbose) # Save it to file
            del tmpproject # Don't need it hanging around any more
        self.settings.advancedtracking = origadvancedtracking
        return fullpath


    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def refreshparset(self, name=None, orig=None, resetprevalence=False):
        '''
        Reset the chosen (or all) parsets to reflect the parameter values from the spreadsheet (or another parset).
        This has to be a method of project rather than parset because it relies on the project's data, which is
        not stored in the parset.
        
        Usage:
            P.refreshparset() # Refresh all parsets in the project to match the data
            P.refreshparset(name='calibrated', orig='default') # Reset parset 'calibrated' to match 'default'
            P.refreshparset(name=['default', 'bugaboo'], orig='calibrated') # Reset parsets 'default' and 'bugaboo' to match 'calibrated'
        '''
        
        if name is None: name = self.parsets.keys() # If none is given, use all
        namelist = promotetolist(name) # Make sure it's a list
        if orig is None: # No original parset is supplied: recreate from data
            origparset = self.makeparset(dosave=False) # Create a temporary parset from the data
        else: # It's supplied, so...
            try: origparset = self.parsets[orig] # ...try to read it from the data...
            except: # ...but raise an error if it isn't there
                errormsg = 'Cannot refresh parset from %s since it does not exist: parsets are: %s' % (orig, self.parsets.keys())
                raise OptimaException(errormsg)
        for parset in [self.parsets[n] for n in namelist]: # Loop over all named parsets
            keys = parset.pars.keys() # Assume all pars structures have the same keys
            for key in keys: # Loop over all parset keys
                if hasattr(parset.pars[key],'fromdata') and parset.pars[key].fromdata: # Don't refresh parameters that aren't based on data
                    if key!='initprev' or resetprevalence: # Initial prevalence is a special case: the only user-edited parameter that is also a data parameter
                        if hasattr(parset.pars[key],'y'): parset.pars[key].y = origparset.pars[key].y # Reset y (value) variable, if it exists
                        if hasattr(parset.pars[key],'t'): parset.pars[key].t = origparset.pars[key].t # Reset t (time) variable, if it exists
                        if hasattr(parset.pars[key],'insertiveonly'): parset.pars[key].insertiveonly = origparset.pars[key].insertiveonly # Special to actsreg, actscas, actscom
                # Reset transition matrices
                if key in ['birthtransit','agetransit','risktransit']: 
                    parset.pars[key] = dcp(origparset.pars[key])
        
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
    
    
    def restorelinks(self):
        ''' Loop over all objects that have links back to the project and restore them '''
        for item in self.parsets.values()+self.progsets.values()+self.scens.values()+self.optims.values()+self.results.values():
            if hasattr(item, 'projectref'):
                item.projectref = Link(self)
        return None


    def pars(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active set of parameters, i.e. self.parsets[-1].pars '''
        try:    return self.parsets[key].pars
        except: return printv('Warning, parameters dictionary not found!', 1, verbose) # Returns None
    
    def parset(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active parameters set, i.e. self.parsets[-1] '''
        try:    return self.parsets[key]
        except: return printv('Warning, parameter set not found!', 1, verbose) # Returns None
    
    def programs(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active set of programs '''
        try:    return self.progsets[key].programs
        except: return printv('Warning, programs not found!', 1, verbose) # Returns None

    def progset(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active program set, i.e. self.progsets[-1]'''
        try:    return self.progsets[key]
        except: return printv('Warning, program set not found!', 1, verbose) # Returns None
    
    def scen(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest scenario, i.e. self.scens[-1]'''
        try:    return self.scens[key]
        except: return printv('Warning, scenario not found!', 1, verbose) # Returns None

    def optim(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest optimization, i.e. self.optims[-1]'''
        try:    return self.optims[key]
        except: return printv('Warning, optimization not found!', 1, verbose) # Returns None

    def result(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest active results, i.e. self.results[-1]'''
        try:    return self.results[key]
        except: return printv('Warning, results set not found!', 1, verbose) # Returns None


    #######################################################################################################
    ### Methods to perform major tasks
    #######################################################################################################


    def runsim(self, name=None, pars=None, simpars=None, start=None, end=None, dt=None, tvec=None, 
               budget=None, coverage=None, budgetyears=None, data=None, n=1, sample=None, tosample=None, randseed=None,
               addresult=True, overwrite=True, keepraw=False, doround=False, die=True, debug=False, verbose=None,
               parsetname=None, progsetname=None, resultname=None, label=None, smoothness=None,
               advancedtracking=None, parallel=False, ncpus=None, **kwargs):
        ''' 
        This function runs a single simulation, or multiple simulations if n>1. This is the
        core function for actually running the model!!!!!!
        
        Version: 2018jan13
        '''
        if dt      is None: dt      = self.settings.dt # Specify the timestep
        if verbose is None: verbose = self.settings.verbose
        if advancedtracking is None: advancedtracking = self.settings.advancedtracking # settings.advancedtracking defaults to False
        if ncpus is not None: ncpus = int(ncpus)

        # Extract parameters either from a parset stored in project or from input
        if parsetname is None:
            if name is not None: parsetname = name # This is mostly for backwards compatibility -- allow the first argument to set the parset
            else:                parsetname = -1 # Set default name
            if pars is None:
                pars = self.parsets[parsetname].pars
                parsetuid = self.parsets[parsetname].uid
                resultname = 'parset-'+self.parsets[parsetname].name
            else:
                printv('Model was given a pardict and a parsetname, defaulting to use pardict input', 3, self.settings.verbose)
                if resultname is None: resultname = 'pardict'
                parsetuid = None
        else:
            if pars is not None:
                printv('Model was given a pardict and a parsetname, defaulting to use pardict input', 3, self.settings.verbose)
                if resultname is None: resultname = 'pardict'
                parsetuid = None
            else:
                if resultname is None: resultname = 'parset-'+self.parsets[parsetname].name
                pars = self.parsets[parsetname].pars
                parsetuid = self.parsets[parsetname].uid
        if label is None: # Define the label
            if name is None: label = '%s' % parsetname
            else:            label = name
            
        # Get the parameters sorted
        if simpars is None: # Optionally run with a precreated simpars instead
            simparslist = [] # Needs to be a list
            if n>1 and sample is None: sample = 'new' # No point drawing more than one sample unless you're going to use uncertainty
            if randseed is not None: seed(randseed) # Reset the random seed, if specified
            if start is None: 
                try:    start = self.parsets[parsetname].start # Try to get start from parameter set, but don't worry if it doesn't exist
                except: start = self.settings.start # Else, specify the start year from the project
            if end is None: 
                try:    end   = self.parsets[parsetname].end # Ditto
                except: end   = self.settings.end # Ditto
            for i in range(n):
                maxint = 2**31-1 # See https://en.wikipedia.org/wiki/2147483647_(number)
                sampleseed = randint(0,maxint) if sample is not None else None
                simparslist.append(makesimpars(pars, start=start, end=end, dt=dt, tvec=tvec, settings=self.settings, name=parsetname, sample=sample, tosample=tosample, randseed=sampleseed, smoothness=smoothness))
        else:
            simparslist = promotetolist(simpars)

        # Run the model!
        rawlist = []
        if n == 1 or (not parallel): # Run single simulation as quick as possible (or just not in parallel)
            for ind,simpars in enumerate(simparslist):
                raw = model(simpars, self.settings, die=die, debug=debug, verbose=verbose, label=self.name, advancedtracking=advancedtracking, **kwargs) # ACTUALLY RUN THE MODEL
                rawlist.append(raw)

        else: # Run in parallel
            all_kwargs = {'settings':self.settings, 'die':die, 'debug':debug, 'verbose':verbose, 'label':self.name, 'advancedtracking':advancedtracking, **kwargs}
            try: rawlist = parallelize(model, iterarg=simparslist, kwargs=all_kwargs, ncpus=ncpus) # ACTUALLY RUN THE MODEL
            except:
                printv('\nWARNING: Could not run in parallel probably because this process is already running in parallel. Trying in serial...', 1, verbose)
                rawlist = []
                for ind,simpars in enumerate(simparslist):
                    raw = model(simpars, self.settings, die=die, debug=debug, verbose=verbose, label=self.name, advancedtracking=advancedtracking, **kwargs) # ACTUALLY RUN THE MODEL
                    rawlist.append(raw)

        # Store results if required
        results = Resultset(name=resultname, pars=pars, parsetname=parsetname, parsetuid=parsetuid, progsetname=progsetname, raw=rawlist, simpars=simparslist, budget=budget, coverage=coverage, budgetyears=budgetyears, project=self, keepraw=keepraw, doround=doround, data=data, verbose=verbose, advancedtracking=advancedtracking) # Create structure for storing results
        if addresult:
            keyname = self.addresult(result=results, overwrite=overwrite)
            if parsetname is not None:
                self.parsets[parsetname].resultsref = keyname # If linked to a parset, store the results
            self.modified = today() # Only change the modified date if the results are stored
        
        return results


    def sensitivity(self, name='perturb', orig=-1, n=5, tosample=None, randseed=None, **kwargs): # orig=default or orig=0?
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


    def autofit(self, name=None, orig=None, fitwhat='force', fitto='prev', method='wape', maxtime=None, maxiters=1000, verbose=2, doplot=False, randseed=None, **kwargs):
        ''' Function to perform automatic fitting '''
        name, orig = self.reconcileparsets(name, orig) # Ensure that parset with the right name exists
        self.parsets[name] = autofit(project=self, name=name, fitwhat=fitwhat, fitto=fitto, method=method, maxtime=maxtime, maxiters=maxiters, verbose=verbose, doplot=doplot, randseed=randseed, **kwargs)
        results = self.runsim(name=name, addresult=False)
        results.improvement = self.parsets[name].improvement # Store in a more accessible place, since plotting functions use results
        keyname = self.addresult(result=results)
        self.parsets[name].resultsref = keyname
        self.modified = today()
        return None
    
    
    def runscenarios(self, scenlist=None, name=None, verbose=2, debug=False, nruns=None, base=None, ccsample=None, randseed=None, **kwargs):
        ''' Function to run scenarios '''

        if scenlist is not None: self.addscens(scenlist) # Replace existing scenario list with a new one
        if name is None: name = 'scenarios' 
    
        scenres = runscenarios(project=self, verbose=verbose, name=name, debug=debug, nruns=nruns, base=base, ccsample=ccsample, randseed=randseed, **kwargs)
        self.addresult(result=scenres[name])
        self.modified = today()
        return scenres
    
    
    def defaultscenarios(self, which=None, **kwargs):
        ''' Wrapper for default scenarios '''
        defaultscenarios(self, which=which, **kwargs)
        return None
    
    
    def defaultbudget(self, progsetname=None, optimizable=None):
        ''' Small method to get the default budget '''
        if progsetname is None: progsetname = -1
        if optimizable is None: optimizable = False
        output = self.progsets[progsetname].getdefaultbudget(optimizable=optimizable) # Note that this is already safely dcp'd...
        return output
    

    def runbudget(self, name=None, budget=None, budgetyears=None, progsetname=None, parsetname='default', verbose=2):
        ''' Function to run the model for a given budget, years, programset and parameterset '''
        if name        is None: name        = 'runbudget'
        if budget      is None: budget      = self.progset().getdefaultbudget()
        if budgetyears is None: budgetyears = self.settings.now
        if progsetname is None:
            try:
                progsetname = self.progsets[0].name
                printv('No program set entered to runbudget, using stored program set "%s"' % (self.progsets[0].name), 1, self.settings.verbose)
            except: raise OptimaException("No program set entered, and there are none stored in the project") 
        coverage = self.progsets[progsetname].getprogcoverage(budget=budget, t=budgetyears, parset=self.parsets[parsetname])
        progpars = self.progsets[progsetname].getpars(coverage=coverage,t=budgetyears, parset=self.parsets[parsetname])
        results = self.runsim(pars=progpars, parsetname=parsetname, progsetname=progsetname, budget=budget, budgetyears=budgetyears, coverage=coverage, label=self.name+'-runbudget')
        return results
    
    
    def outcomecalc(self, name=None, budget=None, optim=None, optimname=None, parsetname=None, progsetname=None, 
                objectives=None, absconstraints=None, origbudget=None, verbose=2, doconstrainbudget=False):
        '''
        Calculate the outcome for a given budget -- a substep of optimize(); similar to runbudget().
        
        Since it relies on an optimization structure, all the inputs that are valid for an optimization are valid
        here too -- e.g. you can give it an Optim, or define objectives separately. By default it will use the 
        objectives and constraints from the most recent optimization.
        
        Example usage:
            import optima as op
            P = op.demo(0)
            budget1 = P.defaultbudget()
            budget2 = P.defaultbudget()
            budget1[:] *= 0.5
            budget2[:] *= 2.0
            P.outcomecalc(name='Baseline')
            P.outcomecalc(name='Halve funding', budget=budget1)
            P.outcomecalc(name='Double funding', budget=budget2)
            P.result('Baseline').outcome
            P.result('Halve funding').outcome
            P.result('Double funding').outcome
        '''
        
        # Check inputs
        if name is None: name = 'outcomecalc'
        if optim is None:
            if len(self.optims) and all([arg is None for arg in [objectives, absconstraints, parsetname, progsetname, optimname]]):
                optimname = -1 # No arguments supplied but optims exist, use most recent optim to run
            if optimname is not None: # Get the optimization by name if supplied
                optim = self.optims[optimname] 
            else: # If neither an optim nor an optimname is supplied, create one
                optim = Optim(project=self, name=name, objectives=objectives, absconstraints=absconstraints, parsetname=parsetname, progsetname=progsetname)

        # Run outcome calculation        
        results = outcomecalc(budgetvec=budget, which='outcomes', project=self, parsetname=optim.parsetname, 
                              progsetname=optim.progsetname, objectives=optim.objectives, absconstraints=optim.absconstraints,
                              origbudget=origbudget, outputresults=True, verbose=verbose, doconstrainbudget=doconstrainbudget)
        # Add results
        results.name = name
        self.addresult(results)
        self.modified = today()
        
        return results


    def icers(self, parsetname=None, progsetname=None, objective=None, startyear=None, endyear=None, budgetratios=None, verbose=2, marginal=None, **kwargs):
        '''
        Calculate ICERs. Example:
            import optima as op
            P = op.demo(0)
            P.parset().fixprops(False)
            P.icers()
            op.ploticers(P.result(), interactive=True)
        '''
        results = icers(project=self, parsetname=parsetname, progsetname=progsetname, objective=objective, startyear=startyear, 
                        endyear=endyear, budgetratios=budgetratios, marginal=marginal, verbose=verbose, **kwargs)
        self.addresult(results)
        self.modified = today()
        return results


    def optimize(self, name=None, parsetname=None, progsetname=None, objectives=None, constraints=None, absconstraints=None, proporigconstraints=None, maxiters=None, maxtime=None,
                 verbose=2, stoppingfunc=None, die=False, origbudget=None, randseed=None, mc=None, optim=None, optimname=None, multi=False, 
                 nchains=None, nblocks=None, blockiters=None, ncpus=None, parallel=None, timevarying=None, tvsettings=None, tvconstrain=None, which=None,
                 makescenarios=True, **kwargs):
        '''
        Function to minimize outcomes or money.
        
        Usage examples:
            P = op.demo(0); P.parset().fixprops(False) # Initialize project so ART has an effect
            P.optimize() # Use defaults
            pygui(P) # To plot results

        Suggested inputs are: parsetname, progsetname, objectives, proporigconstraints, maxtime, ncpus, randseed
            (or constraints or absconstraints, but proporigconstraints also work the best in the FE)

        maxtime <= 60 is a test run, maxtime > 60 is a proper run (generally 1000), maxtime = None runs the most thorough optimization
        !! Be careful in the code, maxtime for this function refers to the entire optimization time, whereas outside this
        function it refers to how long a single call of asd will last. That is why we have finishtime !!

        ncpus is the max number of threads to use: sc.cpu_count()/2 won't slow your computer down,
            sc.cpu_count()-2 might be faster, sc.cpu_count() if you're a madman

        To customize behaviour, generally use maxtime but:
            mc: minoutcomes starts optimizations from different starting budgets, either (baselines, randoms, progbaselines). See minoutcomes
            parallel: whether minoutcomes or minmoney should run in parallel (generally True)
            maxiters: the max iterations each optimization will stop at (generally None, limited by time or convergence instead)
            nchains: how many chains multioptimize should run in parallel, NOTE that each chain will run with mc. (generally 1 when using mc)
            nblocks: runs nchains, then updates origbudget from the best chain and reoptimizes. Repeats this nblocks times (generally 1 or 2)
            multi: !! This input gets ignored since this function interprets whether or not multioptimize needs to be used now !!
            blockiters !! This input gets ignored now since it is the same as maxiters !!
            origbudget: if you want to customize the "Optimization baseline", which is the optimization's starting point
        '''
        
        if parsetname  is None or parsetname == -1:  parsetname  = self.parsets.keys()[-1]  #use the real name instead of -1
        if progsetname is None or progsetname == -1: progsetname = self.progsets.keys()[-1] #use the real name instead of -1

        # Check inputs
        if name is None: name = 'default'
        if optim is None:
            if len(self.optims) and all([arg is None for arg in [objectives, parsetname, progsetname, optimname, which]]):
                optimname = -1 # No arguments supplied but optims exist, use most recent optim to run
            if optimname is not None: # Get the optimization by name if supplied
                optim = self.optims[optimname] 
            else: # If neither an optim nor an optimname is supplied, create one
                optim = Optim(project=self, name=name, objectives=objectives, constraints=constraints, absconstraints=absconstraints, proporigconstraints=proporigconstraints,
                              parsetname=parsetname, progsetname=progsetname, timevarying=timevarying, tvsettings=tvsettings, which=which)
        if objectives  is not None: optim.objectives  = objectives # Update optim structure with inputs
        if tvsettings  is not None: optim.tvsettings  = tvsettings
        if timevarying is not None: optim.tvsettings['timevarying'] = timevarying # Set time-varying optimization
        if tvconstrain is not None: optim.tvsettings['tvconstrain'] = tvconstrain # Set whether programs should be constrained to their time-varying values
        if absconstraints is not None:      optim.absconstraints = absconstraints
        if constraints is not None:         optim.constraints = constraints
        if proporigconstraints is not None: optim.proporigconstraints = proporigconstraints

        if maxiters is None: maxiters = blockiters  # blockiters and maxiters are the same and will be called maxiters from here on out
        settings = {'maxtime':maxtime,'maxiters':maxiters, 'parallel':parallel, 'ncpus': ncpus, 'nchains':nchains, 'nblocks':nblocks, 'mc':mc}
        if maxtime is None:  # Unlimited time so run the most thorough optimization
            defaultsettings = {'maxiters':None, 'parallel':True, 'nchains':1, 'nblocks':10, 'mc':(24,12,12), 'ncpus':ceil(cpu_count()/2)}
        elif maxtime <= 60:  # 1 min or less, so run a test optimization
            defaultsettings = {'maxiters':None, 'parallel':True, 'nchains':1, 'nblocks':1,  'mc':( 2, 0, 0), 'ncpus':ceil(cpu_count()/2)}
        else:                # Longer than 1 minute, but not unlimited so run the most "efficient" optimization
            defaultsettings = {'maxiters':None, 'parallel':True, 'nchains':1, 'nblocks':1,  'mc':(12, 6, 6), 'ncpus':ceil(cpu_count()/2)}
        for key in defaultsettings.keys():
            if settings[key] is None: settings[key] = defaultsettings[key]  # Only overwrite Nones with the default

        multi = settings['nchains'] > 1 or settings['nblocks'] > 1    # Need to run with multioptimize if you have nchains or nblocks
        if settings['maxtime'] is not None: settings['finishtime'] = time() + settings['maxtime'] # START THE TIMER
        # Note we still pass maxtime into the functions, even though it will reach finishtime before maxtime, so that it saves maxtime

        # Run the optimization
        if optim.tvsettings['timevarying']: # Call time-varying optimization
            for key in ['nchains','nblocks']: settings.pop(key)
            multires = tvoptimize(optim=optim, verbose=verbose, stoppingfunc=stoppingfunc, die=die, origbudget=origbudget,
                                  randseed=randseed, **settings, **kwargs)
        elif multi and not optim.objectives['which']=='money': # It's a multi-run objectives optimization
            multires = multioptimize(optim=optim, verbose=verbose, stoppingfunc=stoppingfunc, die=die, origbudget=origbudget,
                                     randseed=randseed, **settings, **kwargs)
        else: # Neither special case, so minoutcomes or minmoney
            multires = optimize(optim=optim, verbose=verbose, stoppingfunc=stoppingfunc, die=die, origbudget=origbudget,
                                randseed=randseed, **settings, **kwargs)
        
        # Tidy up
        optim.resultsref = multires.name
        self.addoptim(optim=optim)
        self.addresult(result=multires)
        self.modified = today()

        try:
            optbudget = multires.budgets['Optimized']
            if hasattr(multires,'improvement'):
                  printv(f'\nOptimization "{name}" finished with outcomes: Original: {multires.improvement[0][0]}, Best: {multires.improvement[0][-1]}!\n',2,verbose)
            else: printv(f'\nOptimization "{name}" finished with budgets: Original: {sum(multires.budgets["Baseline"])}, Best: {sum(optbudget)}!\n')
        except:   printv(f'\nOptimization "{name}" unsuccessful!\n',2,verbose)

        if makescenarios: #Make a new budget scenario out of each optimized result
            budgetscens = []            
            for resname in multires.resultsetnames:
                optscenname = multires.optim.name + '_' + resname
                optbudget = dcp(multires.budgets[resname])
                for prog in optbudget.keys():
                    optbudget[prog] = promotetolist(optbudget[prog])
                optt = promotetolist(multires.budgetyears[resname])
                
                budgetscens.append(Budgetscen(name = optscenname, t=optt, budget=optbudget,
                                              parsetname=parsetname, progsetname=progsetname))
            self.addscens(budgetscens, overwrite=False)
        
        return multires
    
    
    def export(self, filename=None, folder=None, spreadsheetpath=None, verbose=2):
        '''
        Export a script that, when run, generates this project. Example:
            import optima as op
            P = op.demo(0)
            P.export(filename='demo.py')
        
        If a spreadsheet path isn't supplied, then export the spreadsheet as well.
        '''
        
        fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='py', sanitize=True)
        
        if spreadsheetpath is None:
            spreadsheetpath = self.name+'.xlsx'
            self.makespreadsheet(filename=spreadsheetpath, folder=folder)
            printv('Generated spreadsheet from project %s and saved to file %s' % (self.name, spreadsheetpath), 2, verbose)

        output = "'''\nSCRIPT TO GENERATE PROJECT %s\n" %(self.name)
        output += "Created %s\n\n\n'''\n\n\n" %(today())
        output += "### Imports\n" 
        output += "from optima import Project, Program, Programset, Parscen, Budgetscen, Coveragescen, Optim, odict, dcp \n" 
        output += "from numpy import nan, array \n\n" 
        output += "### Define analyses to run\n"
        output += "torun = ['makeproject',\n'calibrate',\n'makeprograms',\n'scens',\n'optims',\n'saveproject',\n]\n\n"
        output += "### Filepaths and global variables\n"
        output += "dorun = True\n" # Run things by default
        output += "spreadsheetfile = '%s'\n\n\n" %(spreadsheetpath)
        output += "### Make project\n" 
        output += "if 'makeproject' in torun:\n"
        output += "    P = Project(spreadsheet=spreadsheetfile, dorun=False)\n\n"
        output += "### Calibrate\n" 
        output += "if 'calibrate' in torun:\n"
        output += "    defaultps = dcp(P.parsets[0]) # Copy the default parset\n"
        output += "    P.rmparset(0) # Remove the default parset\n\n"
        for psn,ps in self.parsets.items():
            output += "    parset = dcp(defaultps)\n"
            output += "    parset.name = '"+psn+"'\n"
            output += "    pars = parset.pars\n"
            output += "    "+ps.export().replace("\n","\n    ")+"\n"
            output += "    P.addparset(name='"+psn+"',parset=parset)\n\n"
        output += "### Make programs\n" 
        output += "if 'makeprograms' in torun:\n"
        output += "    P.rmprogset(0) # Remove the default progset\n\n"
        for prn,pr in self.progsets.items():
            pi = 0
            plist = "["
            for pn,p in pr.programs.items():
                output += "    p"+str(pi)+" = Program(short='"+p.short+"',name='"+p.name+"',targetpars="+str(p.targetpars)+",targetpops="+str(p.targetpops)+")\n"
                output += "    p"+str(pi)+".costcovfn.ccopars = "+p.costcovfn.ccopars.export(doprint=False)+"\n"
                output += "    p"+str(pi)+".costcovdata = "+promotetoodict(p.costcovdata).export(doprint=False)+"\n\n"
                plist += "p"+str(pi)+","
                pi += 1
            plist += "]"
            output += "    R = Programset(programs="+plist+")\n"
            for partype in pr.covout.keys():
                for popname in pr.covout[partype].keys():
                    strpopname = str(popname) if isinstance(popname,tuple) else "'"+popname+"'"
                    output += "    R.covout['"+partype+"']["+strpopname+"].ccopars = "+pr.covout[partype][popname].ccopars.export(doprint=False)+"\n"
                    output += "    R.covout['"+partype+"']["+strpopname+"].interaction = '"+pr.covout[partype][popname].interaction+"'\n\n"

            output += "    P.addprogset(name='"+prn+"',progset=R)\n\n"
        
        output += "### Scenarios\n" 
        output += "if 'scens' in torun:\n"
        slist = "["
        for sn,s in self.scens.items():
            parsetname = "'"+s.parsetname+"'" if isinstance(s.parsetname,str) else str(s.parsetname)
            if isinstance(s,Parscen):
                scentoadd = "Parscen(name='"+s.name+"',parsetname="+parsetname+",pars="+str(s.pars)+")"
            elif isinstance(s,Progscen):
                progsetname = "'"+s.progsetname+"'" if isinstance(s.progsetname,str) else str(s.progsetname)
                t = str(s.t)
                if isinstance(s,Budgetscen):
                    scentoadd = "Budgetscen(name='"+s.name+"',parsetname="+parsetname+",progsetname="+progsetname+",budget="+promotetoodict(s.budget).export(doprint=False)+",t="+t+")"
                elif isinstance(s,Coveragescen):
                    scentoadd = "Coveragescen(name='"+s.name+"',parsetname="+parsetname+",progsetname="+progsetname+",coverage="+promotetoodict(s.coverage).export(doprint=False)+",t="+t+")"
            slist += scentoadd+",\n                "
        slist += "]"
            
        output += "    P.addscens("+slist+")\n"
        output += "    if dorun: P.runscenarios()\n\n\n"

        output += "### Optimizations\n" 
        output += "if 'optims' in torun:\n"
        for on,o in self.optims.items():
            parsetname = "'"+o.parsetname+"'" if isinstance(o.parsetname,str) else str(o.parsetname)
            progsetname = "'"+o.progsetname+"'" if isinstance(o.progsetname,str) else str(o.progsetname)
            constraints = promotetoodict(o.proporigconstraints).export(doprint=False) if o.proporigconstraints is not None else 'None'
            output += "    P.addoptim(name='"+on+"',\n               optim=Optim(project=P,\n                           parsetname="+parsetname+",\n                           progsetname="+progsetname+",\n                           objectives="+promotetoodict(o.objectives).export(doprint=False)+",\n                           constraints="+constraints+"))\n\n"

        output += "    if dorun: P.optimize() # Run the most recent optimization\n\n\n"

        output += "### Save project\n" 
        output += "if 'saveproject' in torun:\n"
        output += "    P.save(filename='"+self.name+"-scripted.prj')\n\n"

        f = open(fullpath, 'w')
        f.write( output )
        f.close()
        printv('Saved project %s to script file %s' % (self.name, fullpath), 2, verbose)
        return None


    #######################################################################################################
    ## Methods to handle tasks for geospatial analysis
    #######################################################################################################
        
    def genBOC(self, budgetratios=None, name=None, parsetname=None, progsetname=None, objectives=None, constraints=None, absconstraints=None, proporigconstraints=None,
               maxiters=1000, maxtime=None, verbose=2, stoppingfunc=None, mc=None, parallel=True, finishtime=None, ncpus=None, die=False, randseed=None, origbudget=None, **kwargs):
        ''' Function to generate project-specific budget-outcome curve for geospatial analysis '''
        if name is None:
            name = 'BOC ' + self.name
        if objectives is None:
            printv('Warning, genBOC "%s" did not get objectives, using defaults...' % (self.name), 2, verbose)
            objectives = defaultobjectives(project=self, progsetname=progsetname)
        boc = BOC(name=name,objectives=objectives,constraints=constraints,absconstraints=absconstraints,proporigconstraints=proporigconstraints)
        
        if parsetname is None:
            printv('Warning, using default parset', 3, verbose)
            parsetname = -1
        
        if progsetname is None:
            printv('Warning, using default progset', 3, verbose)
            progsetname = -1

        # Set defaults
        if sc.isnumber(mc): mc = (1,0,mc)
        elif mc is None or sum(mc) == 0: mc = (3,0,0)
        if ncpus is None: ncpus = int(ceil( sc.cpu_count()/2 ))

        defaultbudget = self.progsets[progsetname].getdefaultbudget()
        
        if budgetratios is None:
            budgetratios = [1.0, 0.8, 0.5, 0.3, 0.1, 0.01, 1.5, 3.0, 5.0, 10.0, 30.0, 100.0]
        if 1.0 not in budgetratios:
            printv('Warning, current budget not present in budget ratios, adding...', 3, verbose)
            budgetratios = list(budgetratios).insert(0, 1.0) # Ensure 1.0 is in there
        ybaseline = nan # Prepopulate, assuming it won't be found (which it probably will be)
        yregionoptim = nan # The optimal y value for the within-region optimum
        regionoptimbudget = None # The budget for the within-region optimum
        
        # Calculate the number of iterations
        noptims = 1 + (mc!=0) + max(abs(mc),0) # Calculate the number of optimizations per BOC point
        nbocpts = len(budgetratios)
        guessmaxiters = maxiters if maxiters is not None else 1000
        guessminiters = min(50, guessmaxiters)  # WARNING, shouldn't hardcode stalliters but doesn't really matter, either
        estminiters = noptims*nbocpts*guessminiters
        estmaxiters = noptims*nbocpts*guessmaxiters
        printv('Generating BOC for %s for %0.0f-%0.0f with weights deaths=%0.1f, infections=%0.1f, DALYs=%0.1f (est. %i-%i iterations)' % (self.name, objectives['start'], objectives['end'], objectives['deathweight'], objectives['inciweight'], objectives['dalyweight'], estminiters, estmaxiters), 1, verbose)
        
        # Initialize arrays
        budgetdict = odict()
        for budgetratio in budgetratios:
            budgetdict['%s'%budgetratio] = budgetratio # Store the budget ratios as a dictionary
        tmpx = odict()
        tmpy = odict()
        tmptotals = odict()
        tmpallocs = odict()
        counts = odict([(key,0) for key in budgetdict.keys()]) # Initialize to zeros -- count how many times each budget is run
        while len(budgetdict):
            key, ratio = budgetdict.items()[0] # Use first budget in the stack
            counts[key] += 1
            budget = ratio*sum(defaultbudget[:])
            thiscount = sum(counts[:])
            totalcount = len(budgetdict)+sum(counts[:])-1
            printv('Running budget %i/%i ($%0.0f)' % (thiscount, totalcount, budget), 2, verbose)
            objectives['budget'] = budget
            optim = Optim(project=self, name=name, constraints=constraints,absconstraints=absconstraints,proporigconstraints=proporigconstraints,
                          objectives=objectives, parsetname=parsetname, progsetname=progsetname)
            
            # All subsequent genBOC steps use the allocation of the previous step as its initial budget, scaled up internally within optimization.py of course.
            if len(tmptotals):
                closest = argmin(abs(tmptotals[:]-budget)) # Find closest budget
                origbudget = tmpallocs[closest]
            label = self.name+' $%sm (%i/%i)' % (sigfig(budget/1e6, sigfigs=3), thiscount, totalcount)

            if finishtime is None and maxtime is not None: finishtime = time() + maxtime  # Each optimization gets its own maxtime
            # Actually run
            results = optimize(optim=optim, maxiters=maxiters, maxtime=maxtime, verbose=verbose, stoppingfunc=stoppingfunc, origbudget=origbudget, label=label, mc=mc, finishtime=finishtime, parallel=parallel, ncpus=ncpus, die=die, randseed=randseed, **kwargs)
            tmptotals[key] = budget
            tmpallocs[key] = dcp(results.budgets.findbykey('Optim'))
            tmpx[key] = budget # Used to be append, but can't use lists since can iterate multiple times over a single budget
            tmpy[key] = results.outcome
            boc.budgets[key] = tmpallocs[-1]
            if ratio==1.0: # Check if ratio is 1, and if so, store the baseline
                ybaseline = results.outcomes.findbykey('Base') # Store baseline result, but also not part of the BOC
                yregionoptim = results.outcome
                regionoptimbudget = budget
            
            # Check that the BOC points are monotonic, and if not, rerun
            budgetdict.pop(key) # Remove the current key from the list
            for oldkey in tmpy.keys():
                if tmpy[oldkey]>tmpy[key] and tmptotals[oldkey]>tmptotals[key]: # Outcome is worse but budget is larger
                    printv('WARNING, outcome for %s is worse than outcome for %s, rerunning...' % (oldkey, key), 1, verbose)
                    if counts[oldkey]<5: # Don't get stuck in an infinite loop -- 5 is arbitrary, but jeez, that should take care of it
                        budgetdict.insert(0, oldkey, float(oldkey)) # e.g. key2='0.8'
                    else:
                        printv('WARNING, tried 5 times to reoptimize budget and unable to get lower', 1, verbose) # Give up
                        
        # Tidy up: insert remaining points
        if sum(counts[:]):
            boc.parsetname = parsetname
            boc.progsetname = progsetname
            xorder = argsort(tmpx[:]) # Sort everything
            boc.x = tmpx[:][xorder].tolist() # Convert to list
            boc.y = tmpy[:][xorder].tolist()
            boc.budgets.sort(xorder)
            boc.x.insert(0, 0) # Add the zero-budget point to the beginning of the list
            boc.y.insert(0, results.extremeoutcomes['Zero']) # It doesn't matter which results these come from
            boc.yinf      = results.extremeoutcomes['Infinite'] # Store infinite money, but not as part of the BOC
            boc.ybaseline = ybaseline # Has to be calculated out of the loop since this changes depending on the budget
            boc.yregionoptim = yregionoptim # Outcome for within-region optimization
            boc.defaultbudget = dcp(defaultbudget) # Default budget
            boc.regionoptimbudget = dcp(regionoptimbudget) # Within-region-optimal budget
            boc.bocsettings = odict([('maxiters',maxiters),('maxtime',maxtime),('mc',mc),('randseed',randseed)])
            self.addresult(result=boc)
            self.modified = today()
        else:
            errormsg = 'BOC generation failed: no BOC points were calculated'
            raise OptimaException(errormsg)
        return None        
    
    
    def getBOC(self, objectives=None, strict=False, verbose=2):
        ''' Returns a BOC result with the desired objectives (budget notwithstanding) if it exists, else None '''
        
        boc = None
        objkeys = ['start','end','deathweight','inciweight']
        for result in reversed(self.results.values()): # Get last result and work backwards
            if isinstance(result,BOC):
                boc = result
                if objectives is None:
                    return boc # A BOC was found, and objectives are None: we're done
                same = True
                for y in boc.objectives:
                    if y in objkeys and boc.objectives[y] != objectives[y]:
                        same = False
                if same:
                    return boc # Objectives are defined, but they match: return BOC
        
        # Figure out what happened
        if boc is None: # No BOCs were found of any kind
            printv('Warning, no BOCs found!', 1, verbose)
            return None
        
        # Compare the last BOC found with the wanted objectives
        wantedobjs = ', '.join(['%s=%0.1f' % (key,objectives[key]) for key in objkeys])
        actualobjs = ', '.join(['%s=%0.1f' % (key,boc.objectives[key]) for key in objkeys])
        if not same and strict: # The BOCs don't match exactly, and strict checking is enabled, return None
            printv('WARNING, project %s has no BOC with objectives "%s", aborting (closest match was "%s")' % (self.name, wantedobjs, actualobjs), 1, verbose)
            return None
        else:
            printv('WARNING, project %s has no BOC with objectives "%s", instead using BOC with objectives "%s"' % (self.name, wantedobjs, actualobjs), 1, verbose)
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
    
