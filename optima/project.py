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

Version: 2015sep03 by cliffk
"""

from copy import deepcopy
try: import cPickle as pickle # For Python 2 compatibility
except: import pickle
from gzip import GzipFile
from metadata import Metadata
from settings import Settings


class Project(object):
    
    
    
    #######################################################################################################
    ## Built-in methods
    #######################################################################################################
    
    def __init__(self,name='default',spreadsheet=None):
        ''' Initialize the project ''' 
        
        
        self.name = name
        
        ## Define the structure lists
        self.params = {}
        self.ccocs = {}
        self.scens = {}
        self.optims = {}
        
        ## Define other quantities
        self.data = {}
        self.metadata = Metadata(name=name)
        self.settings = Settings()
        
        return None
    
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '\n'
        output += '      Project name: %s\n'    % self.name
        output += '\n'
        output += '    Parameter sets: %i\n'    % len(self.params)
        output += '        CCOCs sets: %i\n'    % len(self.ccocs)
        output += '     Scenario sets: %i\n'    % len(self.scens)
        output += ' Optimization sets: %i\n'    % len(self.optims)
        output += '\n'
        output += '    Optima version: %0.1f\n' % self.metadata.version
        output += '      Date created: %s\n'    % self.metadata.getdate(which='created')
        output += '     Date modified: %s\n'    % self.metadata.getdate(which='modified')
        output += '        Git branch: %s\n'    % self.metadata.gitbranch
        output += '       Git version: %s\n'    % self.metadata.gitversion
        output += '              UUID: %s\n'    % str(self.metadata.uuid)
        return output
    
    
    
    
    
    #######################################################################################################
    ## Methods for I/O
    #######################################################################################################
    
    @classmethod
    def load(Project,filename):
        ''' Load a saved project '''
        with GzipFile(filename, 'rb') as fileobj: project = pickle.load(fileobj)
        print('Project loaded from "%s"' % filename)
        return project

    def save(self,filename):
        ''' Save the current project '''
        with GzipFile(filename, 'wb') as fileobj: pickle.dump(self, fileobj, protocol=2)
        print('Project "%s" saved to "%s"' % (self.name, filename))
        return None
    
    
    
    
    
    

    #######################################################################################################
    ## Methods to handle common tasks with structure lists
    #######################################################################################################
    
    
    def getwhat(self, what):
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
    
    
    def checkname(self, what, checkexists=None, checkabsent=None, overwrite=False):
        ''' Check that a name exists if it needs to; check that a name doesn't exist if it's not supposed to '''
        structlist = self.getwhat(what)
        if checkabsent is not None and overwrite==False:
            if checkabsent in structlist:
                raise Exception('Structure list "%s" already has item named "%s"' % (what, checkabsent))
        if checkexists is not None:
            if not checkexists in structlist:
                raise Exception('Structure list "%s" has no item named "%s"' % (what, checkexists))
        return None
    
    
    def add(self, what, name='default', item=None, overwrite=False):
        ''' Add an entry to a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkabsent=name, overwrite=overwrite)
        structlist[name] = item
        print('Item "%s" added to structure list "%s"' % (name, what))
        return None
    
    
    def remove(self, what, name):
        ''' Remove an entry from a structure list by name '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=name)
        structlist.pop(name)
        print('Item "%s" removed from structure list "%s"' % (name, what))
        return None
    
    
    def copy(self, what, orig='default', new='copy', overwrite=False):
        ''' Copy an entry in a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = deepcopy(structlist[orig])
        print('Item "%s" copied to structure list "%s"' % (new, what))
        return None
    
    
    def rename(self, what, orig='default', new='new', overwrite=False):
        ''' Rename an entry in a structure list '''
        structlist = self.getwhat(what)
        self.checkname(what, checkexists=orig, checkabsent=new, overwrite=overwrite)
        structlist[new] = structlist.pop(orig)
        print('Item "%s" renamed to "%s" in structure list "%s"' % (orig, new, what))
        return None

    
    
    #######################################################################################################
    ## Convenience functions
    #######################################################################################################
    
    print('WARNING, need unique add() methods for the different...uhh...classes')
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