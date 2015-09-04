"""
PROJECT

The main Optima project class. Almost all Optima functionality is provided by this class.

An Optima project is based around 4 major lists:
    1. params -- a list of parameter structures
    2. ccocs -- a list of CCOC structures
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

## Load general modules
from copy import deepcopy
try: import cPickle as pickle # For Python 2 compatibility
except: import pickle
from gzip import GzipFile
from datetime import datetime

## Load classes
from metadata import Metadata
from settings import Settings

## Load other Optima functions
from loadspreadsheet import loadspreadsheet
from makeparams import makeparams

def loadprj(filename):
    ''' Load a saved project '''
    with GzipFile(filename, 'rb') as fileobj: project = pickle.load(fileobj)
    print('Project loaded from "%s"' % filename)
    return project


class Project(object):
    
    
    
    #######################################################################################################
    ## Built-in methods
    #######################################################################################################
    
    def __init__(self,name='default',spreadsheet=None):
        ''' Initialize the project ''' 
        
        ## Define the structure sets
        self.params = {}
        self.ccocs = {}
        self.scens = {}
        self.optims = {}
        
        ## Define other quantities
        self.metadata = Metadata(name=name) # Project metadata
        self.settings = Settings() # Global settings
        self.data = {} # Data from the spreadsheet
        self.programs = {} # Programs and program-parameter links -- WARNING, is this necessary?
        
        ## Load spreadsheet, if available
        if spreadsheet is not None:
            self.loadspreadsheet(spreadsheet)
        
        return None
    
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '\n'
        output += '============================================================\n'
        output += '      Project name: %s\n'    % self.metadata.name
        output += '          Filename: %s\n'    % self.metadata.filename
        output += '\n'
        output += '    Parameter sets: %i\n'    % len(self.params)
        output += '        CCOCs sets: %i\n'    % len(self.ccocs)
        output += '     Scenario sets: %i\n'    % len(self.scens)
        output += ' Optimization sets: %i\n'    % len(self.optims)
        output += '\n'
        output += '    Optima version: %0.1f\n' % self.metadata.version
        output += '      Date created: %s\n'    % self.metadata.getdate(which='created')
        output += '     Date modified: %s\n'    % self.metadata.getdate(which='modified')
        output += 'Spreadsheet loaded: %s\n'    % self.metadata.getdate(which='spreadsheet')
        output += '        Git branch: %s\n'    % self.metadata.gitbranch
        output += '       Git version: %s\n'    % self.metadata.gitversion
        output += '              UUID: %s\n'    % str(self.metadata.uuid)
        output += '============================================================'
        return output
    
    
    
    
    
    #######################################################################################################
    ## Methods for I/O and spreadsheet loading
    #######################################################################################################
    
    
    def reload(self, filename=None):
        ''' Replace the contents of the current project from the file '''
        filename = self.reconcilefilenames(filename)
        project = loadprj(filename)
        return project


    def save(self, filename=None):
        ''' Save the current project '''
        filename = self.reconcilefilenames(filename)
        with GzipFile(filename, 'wb') as fileobj: pickle.dump(self, fileobj, protocol=2)
        print('Project "%s" saved to "%s"' % (self.metadata.name, filename))
        return None
        
        
    def reconcilefilenames(self, filename=None):
        ''' If filename exists, update metadata; if not, take from metadata; if that doesn't exist, then generate '''
        if filename is not None: # filename is available
            self.metadata.filename = filename # Update stored filename with the new filename
        else: # filename isn't available
            if self.metadata.filename is None: # metadata.filename isn't available
                self.metadata.filename = self.metadata.name+'.prj' # Use project name as filename if none provided
            filename = self.metadata.filename # Replace filename with stored filename            
        return filename
    
    
    
    def loadspreadsheet(self, filename):
        ''' Load a data spreadsheet -- enormous, ugly function so located in its own file '''
        
        ## Load spreadsheet and update metadata
        self.data, self.programs = loadspreadsheet(filename) # WARNING -- might want to change this
        self.metadata.spreadsheetdate = datetime.today() # Update date when spreadsheet was last loaded
        
        ## If default parameters don't exist, create them
        if 'default' not in self.params:
            self.makeparams(name='default')
        return None
    
    
    
    def makeparams(self, name='default', overwrite=False):
        ''' Regenerate the parameters from the spreadsheet data -- also a large function '''
        params = makeparams(self.data) # Create parameters
        self.addparams(name=name, params=params) # Store parameters
        return None
    
    
    
    

    #######################################################################################################
    ## Methods to handle common tasks with structure lists
    #######################################################################################################
    
    
    def getwhat(self, what=None):
        ''' 
        Figure out what kind of structure list is being requested, e.g.
            structlist = getwhat('parameters')
        will return P.params.
        '''
        if what is None: raise Exception('No structure list provided')
        elif what in ['p', 'pars', 'params', 'parameters']: structlist = self.params
        elif what in ['c', 'ccoc', 'ccocs', 'CCOCs']: structlist = self.ccocs
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
    ## Convenience functions
    #######################################################################################################
    
    # WARNING, need unique add() methods for the different...uhh...classes, unless these are defined elsewhere
    def addparams(self, name='default', params=None, overwrite=False): self.add(self, what='params', name=name, item=params, overwrite=overwrite)
    def addccocs(self,  name='default', ccocs=None,  overwrite=False): self.add(self, what='ccocs', name=name, item=ccocs, overwrite=overwrite)
    def addscen(self,   name='default', scen=None,   overwrite=False): self.add(self, what='scen', name=name, item=scen, overwrite=overwrite)
    def addoptim(self,  name='default', optim=None,  overwrite=False): self.add(self, what='optim', name=name, item=optim, overwrite=overwrite)
 
    def rmparams(self, name): self.remove(self, what='params', name=name)
    def rmccocs(self,  name): self.remove(self, what='ccocs',  name=name)
    def rmscen(self,   name): self.remove(self, what='scen',   name=name)
    def rmoptim(self,  name): self.remove(self, what='optim',  name=name)
    
    def copyparams(self, orig='default', new='new', overwrite=False): self.copy(self, what='params', orig=orig, new=new, overwrite=overwrite)
    def copyccocs(self,  orig='default', new='new', overwrite=False): self.copy(self, what='ccocs',  orig=orig, new=new, overwrite=overwrite)
    def copyscen(self,   orig='default', new='new', overwrite=False): self.copy(self, what='scen',   orig=orig, new=new, overwrite=overwrite)
    def copyoptim(self,  orig='default', new='new', overwrite=False): self.copy(self, what='optim',  orig=orig, new=new, overwrite=overwrite)
        
    def renameparams(self, orig='default', new='new', overwrite=False): self.rename(self, what='params', orig=orig, new=new, overwrite=overwrite)
    def renameccocs(self,  orig='default', new='new', overwrite=False): self.rename(self, what='ccocs',  orig=orig, new=new, overwrite=overwrite)
    def renamescen(self,   orig='default', new='new', overwrite=False): self.rename(self, what='scen',   orig=orig, new=new, overwrite=overwrite)
    def renameoptim(self,  orig='default', new='new', overwrite=False): self.rename(self, what='optim',  orig=orig, new=new, overwrite=overwrite)

    


    #######################################################################################################
    ## Methods to perform major tasks
    #######################################################################################################

    
    def calibrate(self):
        return None
    
    def autofit(self):
        return None
    
    def manualfit(self):
        return None
    
    def mcmc(self):
        return None
        
    def makescenarios(self):
        return None
    
    def optimize(self):
        return None
    
    def plotcalibration(self):
        return None
    
    def plotscens(self):
        return None
    
    def plotoptim(self):
        return None