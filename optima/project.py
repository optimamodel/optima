from optima import odict, Settings, Parameterset, Resultset, loadspreadsheet, model, \
runcommand, getdate, today, uuid, dcp, objectid, sensitivity, manualfit, autofit

version = 2.0 ## Specify the version, for the purposes of figuring out which version was used to create a project


#######################################################################################################
## Project class -- this contains everything else!
#######################################################################################################

class Project(object):
    """
    PROJECT
    
    The main Optima project class. Almost all Optima functionality is provided by this class.
    
    An Optima project is based around 4 major lists:
        1. parsets -- an odict of parameter structures
        2. progsets -- an odict of response structures
        3. scens -- an odict of scenario structures
        4. optims -- an odict of optimization structures
    
    In addition, an Optima project contains:
        1. data -- loaded from the spreadsheet
        2. metadata -- project name, creation date, etc.
        3. settings -- timestep, indices, etc.
    
    Methods for structure lists:
        1. add -- add a new structure to the odict
        2. remove -- remove a structure from the odict
        3. copy -- copy a structure in the odict
        4. rename -- rename a structure in the odict
    
    Version: 2015dec17 by cliffk
    """
    
    
    
    #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################
    
    def __init__(self, name='default', spreadsheet=None):
        ''' Initialize the project ''' 

        ## Define the structure sets
        self.parsets = odict()
        self.progsets = odict()
        self.scens = odict()
        self.optims = odict()
        
        ## Define other quantities
        self.name = name
        self.settings = Settings() # Global settings
        self.data = {} # Data from the spreadsheet
        
        ## Define metadata
        self.uuid = uuid()
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        self.version = version
        try:
            self.gitbranch = runcommand('git rev-parse --abbrev-ref HEAD').rstrip('\n')
            self.gitversion = runcommand('git rev-parse HEAD').rstrip('\n')
        except:
            self.gitbranch = 'Git branch information not retrivable'
            self.gitversion = 'Git version information not retrivable'
            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        
        ## Load spreadsheet, if available
        if spreadsheet is not None:
            self.loadspreadsheet(spreadsheet)
        
        return None
    
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = objectid(self)
        output += '============================================================\n'
        output += '      Project name: %s\n'    % self.name
        output += '\n'
        output += '    Parameter sets: %i\n'    % len(self.parsets)
        output += '     Response sets: %i\n'    % len(self.progsets)
        output += '     Scenario sets: %i\n'    % len(self.scens)
        output += ' Optimization sets: %i\n'    % len(self.optims)
        output += '\n'
        output += '    Optima version: %0.1f\n' % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        if self.modified: output += '     Date modified: %s\n'    % getdate(self.modified)
        output += 'Spreadsheet loaded: %s\n'    % getdate(self.spreadsheetdate)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '              UUID: %s\n'    % self.uuid
        output += '============================================================'
        return output
    
    
    
    
    
    #######################################################################################################
    ## Methods for I/O and spreadsheet loading
    #######################################################################################################
    
    
    def loadspreadsheet(self, filename, name='default'):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file '''
        
        ## Load spreadsheet and update metadata
        self.data = loadspreadsheet(filename) # Do the hard work of actually loading the spreadsheet
        self.spreadsheetdate = today() # Update date when spreadsheet was last loaded
        
        ## If parameter set of that name doesn't exist, create it
        if name not in self.parsets:
            parset = Parameterset()
            parset.makepars(self.data) # Create parameters
            self.addparset(name=name, parset=parset) # Store parameters
        return None
    
    
    
    
    

    #######################################################################################################
    ## Methods to handle common tasks with structure lists
    #######################################################################################################
    
    
    def getwhat(self, what=None):
        ''' 
        Figure out what kind of structure list is being requested, e.g.
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if what is None: raise Exception('No structure list provided')
        elif what in ['p', 'pars', 'parset', 'parameters']: structlist = self.parsets
        elif what in ['r', 'pr', 'progs', 'progset', 'progsets']: structlist = self.progsets # WARNING, inconsistent terminology!
        elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
        elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimisation', 'optimization', 'optimisations', 'optimizations']: structlist = self.optims
        else: raise Exception('Structure list "%s" not understood' % what)
        return structlist
    
    
    def checkname(self, what=None, checkexists=None, checkabsent=None, overwrite=False):
        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
        structlist = self.getwhat(what)
        if checkabsent is not None and overwrite==False:
            if checkabsent in structlist:
                raise Exception('Structure list "%s" already has item named "%s"' % (what, checkabsent))
        if checkexists is not None:
            if not checkexists in structlist:
                raise Exception('Structure list "%s" has no item named "%s"' % (what, checkexists))
        return None
    
    
    def add(self, what=None, name='default', item=None, overwrite=False):
        ''' Add an entry to a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkabsent=name, overwrite=overwrite)
        structlist[name] = item
        structlist[name].name = name # Make sure names are consistent
        print('Item "%s" added to structure list "%s"' % (name, what))
        return None
    
    
    def remove(self, what=None, name=None):
        ''' Remove an entry from a structure list by name '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=name)
        structlist.pop(name)
        print('Item "%s" removed from structure list "%s"' % (name, what))
        return None
    
    
    def copy(self, what=None, orig='default', new='copy', overwrite=False):
        ''' Copy an entry in a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = dcp(structlist[orig])
        structlist[new].name = new # Update name
        print('Item "%s" copied to structure list "%s"' % (new, what))
        return None
    
    
    def rename(self, what=None, orig='default', new='new', overwrite=False):
        ''' Rename an entry in a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = structlist.pop(orig)
        structlist[new].name = new # Update name
        print('Item "%s" renamed to "%s" in structure list "%s"' % (orig, new, what))
        return None

    
    
    #######################################################################################################
    ## Convenience functions -- NOTE, do we need these...?
    #######################################################################################################
    
    def addparset(self,   name='default', parset=None,   overwrite=False): self.add(what='parset',   name=name, item=parset, overwrite=overwrite)
    def addprogset(self,  name='default', progset=None, overwrite=False): self.add(what='progset',   name=name, item=progset, overwrite=overwrite)
    def addscen(self,     name='default', scen=None,     overwrite=False): self.add(what='scen',     name=name, item=scen, overwrite=overwrite)
    def addoptim(self,    name='default', optim=None,    overwrite=False): self.add(what='optim',    name=name, item=optim, overwrite=overwrite)
 
    def rmparset(self,   name): self.remove(what='parset',   name=name)
    def rmprogset(self, name):  self.remove(what='progset', name=name)
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

    



    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################


    def runsim(self, name='default', simpars=None, start=None, end=None, dt=None):
        ''' This function runs a single simulation, or multiple simulations if pars/simpars is a list '''
        if start is None: start=self.settings.start # Specify the start year
        if end is None: end=self.settings.end # Specify the end year
        if dt is None: dt=self.settings.dt # Specify the timestep
        
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
        
        # Store results
        results = Resultset(self, simparslist, rawlist) # Create structure for storing results
        results.make() # Generate derived results
        
        return results
    
    
    
    def sensitivity(self, name='perturb', orig='default', n=5, what='force', span=0.5, ind=0): # orig=default or orig=0?
        ''' Function to perform sensitivity analysis over the parameters as a proxy for "uncertainty"'''
        parset = sensitivity(orig=self.parsets[orig], ncopies=n, what='force', span=span, ind=ind)
        self.addparset(name=name, parset=parset) # Store parameters
        return None
        
        
    def manualfit(self, name='manualfit', orig='default', ind=0): # orig=default or orig=0?
        ''' Function to perform manual fitting'''
        self.copyparset(orig=orig, new=name) # Store parameters
        self.parsets[name].pars = [self.parsets[name].pars[ind]] # Keep only the chosen index
        manualfit(self, name=name, ind=ind) # Actually run manual fitting
        return None
        
    def autofit(self, name='autofit', orig='default', what='force', maxtime=None, niters=100, inds=None):
        self.copyparset(orig=orig, new=name) # Store parameters
        autofit(self, name=name, what=what, maxtime=maxtime, niters=niters, inds=inds)
        return None
    
