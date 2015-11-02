'''
This module defines the Project class, which is the main class used in Optima.
The only other thing it contains is a loadprj() function, since that doesn't
need to be in the class.

Version: 2015sep04 by cliffk
'''


#######################################################################################################
## Header -- imports and version
#######################################################################################################


## Load general modules
from numpy import array # TEMP?
from copy import deepcopy
from datetime import datetime
from uuid import uuid4

## Load classes
from settings import Settings
from parameters import Parameterset


## Load other Optima functions
from loadspreadsheet import loadspreadsheet
#from makesimpars import makesimpars
from model import model
from utils import save, load, run, getdate

version = 2.0






#######################################################################################################
## Project class -- this contains everything else!
#######################################################################################################

class Project(object):
    """
    PROJECT
    
    The main Optima project class. Almost all Optima functionality is provided by this class.
    
    An Optima project is based around 4 major lists:
        1. parset -- a list of parameter structures
        2. responses -- a list of response structures
        3. scens -- a list of scenario structures
        4. optims -- a list of optimization structures
    
    In addition, an Optima project contains:
        1. data -- loaded from the spreadsheet
        2. metadata -- project name, creation date, etc.
        3. settings -- timestep, indices, etc.
    
    Methods for structure lists:
        1. add -- add a new structure to the list
        2. remove -- remove a structure from the list
        3. copy -- copy a structure in the list
        4. rename -- rename a structure in the list
        5. show -- show information on all items in the list(s)
    
    Version: 2015sep04 by cliffk
    """
    
    
    
    #######################################################################################################
    ## Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################
    
    def __init__(self, name='default', spreadsheet=None):
        ''' Initialize the project ''' 
        
        ## Define the structure sets
        self.parsets = {}
        self.respsets = {}
        self.scens = {}
        self.optims = {}
        
        ## Define other quantities
        self.name = name
        self.metadata = Metadata() # Project metadata
        self.settings = Settings() # Global settings
        self.data = {} # Data from the spreadsheet
        
        ## Define metadata
        self.filename = None
        self.id = uuid4()
        self.created = datetime.today()
        self.modified = datetime.today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        self.version = version
        try:
            self.gitbranch = run('git rev-parse --abbrev-ref HEAD').rstrip('\n')
            self.gitversion = run('git rev-parse HEAD').rstrip('\n')
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
        output = '\n'
        output += '============================================================\n'
        output += '      Project name: %s\n'    % self.name
        output += '          Filename: %s\n'    % self.metadata.filename
        output += '\n'
        output += '    Parameter sets: %i\n'    % len(self.parsets)
        output += '     Response sets: %i\n'    % len(self.respsets)
        output += '     Scenario sets: %i\n'    % len(self.scens)
        output += ' Optimization sets: %i\n'    % len(self.optims)
        output += '\n'
        output += '    Optima version: %0.1f\n' % self.version
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += 'Spreadsheet loaded: %s\n'    % getdate(self.spreadsheet)
        output += '        Git branch: %s\n'    % self.gitbranch
        output += '       Git version: %s\n'    % self.gitversion
        output += '                ID: %s\n'    % self.id
        output += '============================================================'
        return output
    
    
    
    
    
    #######################################################################################################
    ## Methods for I/O and spreadsheet loading
    #######################################################################################################
    
    
    def loadfromfile(self, filename=None):
        ''' Replace the contents of the current project from the file -- WARNING, do we need this?'''
        filename = self.reconcilefilenames(filename)
        project = load(filename)
        return project


    def save(self, filename=None):
        ''' Save the current project '''
        filename = self.reconcilefilenames(filename)
        save(self, filename)
        return None
        
        
    def reconcilefilenames(self, filename=None):
        ''' If filename exists, update metadata; if not, take from metadata; if that doesn't exist, then generate '''
        if filename: # filename is available
            self.metadata.filename = filename # Update stored filename with the new filename
        else: # filename isn't available
            if self.metadata.filename is None: # metadata.filename isn't available
                self.metadata.filename = self.metadata.name+'.prj' # Use project name as filename if none provided
            filename = self.metadata.filename # Replace filename with stored filename            
        return filename
    
    
    
    def loadspreadsheet(self, filename, name='default'):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file '''
        
        ## Load spreadsheet and update metadata
        self.data = loadspreadsheet(filename) # Do the hard work of actually loading the spreadsheet
        self.metadata.spreadsheetdate = datetime.today() # Update date when spreadsheet was last loaded
        
        ## If parameter set of that name doesn't exist, create it
        if name not in self.parsets:
            parset = Parameterset()
            parset.makeparsfromdata(self.data) # Create parameters
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
        elif what in ['r', 'resp', 'response', 'responses']: structlist = self.resps # WARNING, inconsistent terminology!
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
        structlist[new] = deepcopy(structlist[orig])
        print('Item "%s" copied to structure list "%s"' % (new, what))
        return None
    
    
    def rename(self, what=None, orig='default', new='new', overwrite=False):
        ''' Rename an entry in a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = structlist.pop(orig)
        print('Item "%s" renamed to "%s" in structure list "%s"' % (orig, new, what))
        return None

    
    
    #######################################################################################################
    ## Convenience functions -- NOTE, do we need these...?
    #######################################################################################################
    
    def addparset(self,   name='default', parset=None,   overwrite=False): self.add(what='parset',   name=name, item=parset, overwrite=overwrite)
    def addresponse(self, name='default', response=None, overwrite=False): self.add(what='response', name=name, item=response, overwrite=overwrite)
    def addscen(self,     name='default', scen=None,     overwrite=False): self.add(what='scen',     name=name, item=scen, overwrite=overwrite)
    def addoptim(self,    name='default', optim=None,    overwrite=False): self.add(what='optim',    name=name, item=optim, overwrite=overwrite)
 
    def rmparset(self,   name): self.remove(what='parset',   name=name)
    def rmresponse(self, name): self.remove(what='response', name=name)
    def rmscen(self,     name): self.remove(what='scen',     name=name)
    def rmoptim(self,    name): self.remove(what='optim',    name=name)
    
    def copyparset(self,   orig='default', new='new', overwrite=False): self.copy(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def copyresponse(self, orig='default', new='new', overwrite=False): self.copy(what='response', orig=orig, new=new, overwrite=overwrite)
    def copyscen(self,     orig='default', new='new', overwrite=False): self.copy(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def copyoptim(self,    orig='default', new='new', overwrite=False): self.copy(what='optim',    orig=orig, new=new, overwrite=overwrite)
        
    def renameparset(self,   orig='default', new='new', overwrite=False): self.rename(what='parset',   orig=orig, new=new, overwrite=overwrite)
    def renameresponse(self, orig='default', new='new', overwrite=False): self.rename(what='response', orig=orig, new=new, overwrite=overwrite)
    def renamescen(self,     orig='default', new='new', overwrite=False): self.rename(what='scen',     orig=orig, new=new, overwrite=overwrite)
    def renameoptim(self,    orig='default', new='new', overwrite=False): self.rename(what='optim',    orig=orig, new=new, overwrite=overwrite)

    



    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################


    def runsim(self, name='default', start=2000, end=2030, dt=None):
        ''' This function runs a single simulation '''
        if dt is None: dt=self.settings.dt # Specify the timestep if none is specified, usually 0.1
        simpars = makesimpars(self.parset[name], start=start, end=end, dt=dt) # "self.parset[name]" is e.g. P.parset['default']
        
        simpars['male'] = array(self.data['popprog']['pops']['male']).astype(bool) # Male populations -- TEMP
        S = model(simpars, self.settings)
        return S
        
    
    
#    def runscen(self, name='default', start=2000, end=2030):
#        ''' This function runs a single scenario '''
#        simpars = makesimpars(self.parset[name], start=start, end=end) # "self.getwhat(what)[name]" is e.g. P.parset['default']
#        simpars = applyoverrides(simpars, self.scens[name])
#        S = model(simpars, self.settings)
#        return S
    
    
    def calibrate(self):
        print('Not implemented')
        return None
    
    def autofit(self):
        print('Not implemented')
        return None
    
    def manualfit(self):
        print('Not implemented')
        return None
    
    def mcmc(self):
        print('Not implemented')
        return None
        
    def makescenarios(self):
        print('Not implemented')
        return None
    
    def optimize(self):
        print('Not implemented')
        return None
    
    
    
    
    #######################################################################################################
    ## Plotting methods
    #######################################################################################################    
    
    
    def plotepi(self, parset='default', scens=None, optims=None):
        print('Not implemented')
        return None
