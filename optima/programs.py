"""
This module defines the Program and Response classes, which are 
used to define a single program/modality (e.g., FSW programs) and a 
set of programs, respectively.

Version: 2015nov04 by robynstuart
"""
from utils import getdate, today, uuid
from collections import defaultdict
import abc

class Programset(object):

    def __init__(self, name='default',programs=None):
        ''' Initialize '''
        self.name = name
        self.id = uuid()
        self.programs = programs if programs else []
        self.getpops() if programs else []
        self.setcostcov() if programs else []
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = '\n'
        output += '       Response name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog.name for prog in self.programs]
        output += 'Targeted populations: %s\n'    % self.pops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                  ID: %s\n'    % self.id
        return output

    def __getitem__(self,name):
        ''' Support dict-style indexing based on name e.g.
            R.programs[1] might be the same as programset['MSM programs']'''
        for prog in self.programs:
            if prog.name == name:
                return prog
        print "Available programs:"
        print [prog.name for prog in self.programs]
        raise Exception('Program "%s" not found' % (name))

    def getpops(self):
        '''Lists populations targeted by some program in the response'''
        self.pops = []
        if self.programs:
            for prog in self.programs:
                for x in prog.pops: self.pops.append(x)
            self.pops = list(set(self.pops))
    
    def setcostcov(self,ccopars):
        '''Sets up the required coverage-outcome curves'''
        self.getpops()
        self.covout = {}
        for pop in self.pops:
            self.covout[pop] = {}
            for modelpar in self.progs_by_modelpar(pop).keys():
                self.covout[pop][modelpar] = {}
                for prog in self.progs_by_modelpar(pop)[modelpar]: self.covout[pop][modelpar][prog.name] = Covout(ccopars)

    def addprog(self, prog, overwrite=False):
        if prog not in self.programs:
            self.programs.append(prog)
            self.getpops()
            self.setcostcov()
            print('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (prog.name, self.name, [p.name for p in self.programs]))
        else:
            raise Exception('Program "%s" is already present in programset "%s".' % (prog.name, self.name))
        
    def optimizable(self):
        return [True if prog.modelpars else False for prog in self.programs]

    def progs_by_pop(self, filter_pop=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_pop = defaultdict(list)
        for prog in self.programs:
            pops_reached = prog.pops if prog.pops else None
            if pops_reached:
                for pop in pops_reached:
                    progs_by_pop[pop].append(prog)
        if filter_pop: return dict(progs_by_pop)[filter_pop]
        else: return dict(progs_by_pop)
            
    def progs_by_modelpar(self,filter_pop=None):
        '''Return a dictionary with:
             keys: all parameters targeted by programs
             values: programs targeting that parameter '''
        progs_by_modelpar = {}
        progs_by_pop = self.progs_by_pop()
        for pop in progs_by_pop.keys():
            progs_by_modelpar[pop] = defaultdict(list)
            for prog in progs_by_pop[pop]:
                for par in prog.modelpars:
                    if pop==par['pop']: progs_by_modelpar[pop][par['param']].append(prog)
            progs_by_modelpar[pop] = dict(progs_by_modelpar[pop])
        if filter_pop: return progs_by_modelpar[filter_pop]
        else: return progs_by_modelpar
        
    def modelpars_by_prog(self,filter_prog=None):
        '''Return a dictionary with:
             keys: all programs
             values: all model parameters targeted by that program'''
        modelpars_by_prog = {}
        progs_by_pop = self.progs_by_pop()
        for pop in progs_by_pop.keys():
            for prog in progs_by_pop[pop]:
                modelpars_by_prog[prog.name] = defaultdict(list)
                for par in prog.modelpars:
                    modelpars_by_prog[prog.name][par['pop']].append(par['param'])
                modelpars_by_prog[prog.name] = dict(modelpars_by_prog[prog.name])
        if filter_prog: return modelpars_by_prog[filter_prog]
        else: return modelpars_by_prog

    def get_outcomes(self,tvec,budget,perturb=False):
        outcomes = dict()
        return outcomes

class Program(object):
    ''' Defines a single program. 
    Can be initialised with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    modelpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]'''

    def __init__(self,name,modelpars=None,ccpars=None,costcovdata=None,nonhivdalys=0):
        '''Initialize'''
        self.name = name
        self.id = uuid4()
        self.modelpars = modelpars if modelpars else []            
        self.pops = list(set([x['pop'] for x in modelpars])) if modelpars else []
        self.costcov = Costcov(ccopars=ccpars)
        self.costcovdata = costcovdata if costcovdata else {'t':[],'cost':[],'coverage':[]}
        
    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += '          Program name: %s\n'    % self.name
        output += '  Targeted populations: %s\n'    % self.pops 
        output += '   Targeted parameters: %s\n'    % self.modelpars 
        output += '\n'
        return output

    def addmodelpar(self,modelpar):
        '''Add a model parameter to be targeted by this program'''
        if modelpar not in self.modelpars:
            if not modelpar.get('covout'): modelpar['covout'] = Covout()
            self.modelpars.append(modelpar)
            self.pops = list(set([x['pop'] for x in self.modelpars]))
            print('\nAdded model parameter "%s" to the list of model parameters affected by "%s". \nAffected parameters are: %s' % (modelpar, self.name, self.modelpars))
        else:
            raise Exception('The model parameter you are trying to add is already present in the list of model parameters affected by this program:%s.' % self.modelpars)
        return None
        
    def rmmodelpar(self,modelpar):
        '''Remove a model parameter from those targeted by this program'''
        if modelpar not in self.modelpars:
            raise Exception('The model parameter you have selected for removal is not in the list of model parameters affected by this program:%s.' % self.modelpars)
        else:
            self.modelpars.pop(self.modelpars.index(modelpar))
            print('\nRemoved model parameter "%s" from the list of model parameters affected by "%s". \nAffected parameters are: %s' % (modelpar, self.name, self.modelpars))
        return None
        
    def addcostcovdatum(self,costcovdatum,overwrite=False):
        '''Add cost-coverage data point'''
        if costcovdatum['t'] not in self.costcovdata['t']:
            self.costcovdata['t'].append(costcovdatum['t'])
            self.costcovdata['cost'].append(costcovdatum['cost'])
            self.costcovdata['coverage'].append(costcovdatum['coverage'])
            print('\nAdded cc data "%s" to program: "%s". \nCC data for this program are: %s' % (costcovdatum, self.name, self.costcovdata))
        else:
            if overwrite:
                ind = self.costcovdata['t'].index(int(costcovdatum['t']))
                oldcostcovdatum = {'t':self.costcovdata['t'][ind],'cost':self.costcovdata['cost'][ind],'coverage':self.costcovdata['coverage'][ind]}
                self.costcovdata['t'][ind] = costcovdatum['t']
                self.costcovdata['cost'][ind] = costcovdatum['cost']
                self.costcovdata['coverage'][ind] = costcovdatum['coverage']
                newcostcovdatum = {'t':self.costcovdata['t'][ind],'cost':self.costcovdata['cost'][ind],'coverage':self.costcovdata['coverage'][ind]}
                print('\nModified cc data from "%s" to "%s" for program: "%s". \nCC data for this program are: %s' % (oldcostcovdatum, newcostcovdatum, self.name, self.costcovdata))
            else:
                raise Exception('You have already entered cost and/or coverage data for the year %s .' % costcovdatum['t'])

    def rmcostcovdatum(self,year):
        '''Remove cost-coverage data point. The point to be removed can be specified by year (int or float).'''
        if int(year) in self.costcovdata['t']:
            self.costcovdata['cost'].pop(self.costcovdata['t'].index(int(year)))
            self.costcovdata['coverage'].pop(self.costcovdata['t'].index(int(year)))
            self.costcovdata['t'].pop(self.costcovdata['t'].index(int(year)))
            print('\nRemoved cc data in year "%s" from program: "%s". \nCC data for this program are: %s' % (year, self.name, self.costcovdata))
        else:
            raise Exception('You have asked to remove data for the year %s, but no data was added for that year. Cost coverage data are: %s' % (year, self.costcovdata))

    def getcoverage(self,t,popsize,x):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        y = self.costcov.evaluate()
        return y      
        
class CCOF(object):
    '''Cost-coverage, coverage-outcome and cost-outcome objects'''
    __metaclass__ = abc.ABCMeta

    def __init__(self,ccopars=None,usedefaults=True):
        if ccopars is None and usedefaults:
            ccopars = self.defaults()
        self.ccopars = ccopars

    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += 'Programmatic parameters: %s\n'    % self.ccopars
        output += '\n'
        return output

    def addccopar(self,ccopar,overwrite=False):
        ''' Add or replace parameters for cost-coverage-outcome functions'''
        if self.ccopars is None:
            self.ccopars = {}
            for partype in ccopar.keys():
                self.ccopars[partype] = [ccopar[partype]]
            if ccopar.get('unitcost') and not ccopar['saturation']: self.ccopars[partype].append(1.)
        else:
            if ccopar['t'] not in self.ccopars['t']:
                for partype in self.ccopars.keys():
                    self.ccopars[partype].append(ccopar[partype])
                if self.ccopars.get('saturation') and not ccopar['saturation']: self.ccopars[partype].append(1.)
                print('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars))
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = {}
                    for partype in self.ccopars.keys():
                        oldccopar[partype] = self.ccopars[partype][ind]
                        self.ccopars[partype][ind] = ccopar[partype]
                    if self.ccopars.get('saturation') and not ccopar['saturation']: self.ccopars[partype].append(1.)
                    print('\nModified CCO parameter from "%s" to "%s". \nCCO parameters for are: %s' % (oldccopar, ccopar, self.ccopars))
                else:
                    raise Exception('You have already entered CCO parameters for the year %s. If you want to overwrite it, set overwrite=True when calling addccopar().' % ccopar['t'])
        return None

    def rmccopar(self,t):
        '''Remove cost-coverage-outcome data point. The point to be removed can be specified by year (int or float).'''
        if isinstance(t,int) or isinstance(t,float):
            if int(t) in self.ccopars['t']:
                ind = self.ccopars['t'].index(int(t))
                for partype in self.ccopars.keys():
                    self.ccopars[partype].pop(ind)
                print('\nRemoved CCO parameters in year "%s". \nCCO parameters are: %s' % (t, self.ccopars))
            else:
                raise Exception('You have asked to remove CCO parameters for the year %s, but no data was added for that year. Available parameters are: %s' % (t, self.ccopars))            
        return None

    def getccopar(self,t,randseed=None,bounds=None):
        '''Get a cost-coverage-outcome parameter set for any year in range 1900-2100'''
        from utils import smoothinterp, findinds
        from numpy import array, arange
        from copy import deepcopy
        
        if randseed and bounds:
            raise Exception('Either select bounds or specify randseed')            
        ccopar = {}
        ccopars_no_t = deepcopy(self.ccopars)
        del ccopars_no_t['t']
        ccopartuples = sorted(zip(self.ccopars['t'], *ccopars_no_t.values()))
        knownt = array([ccopartuple[0] for ccopartuple in ccopartuples])
        allt = arange(1900,2100)
        j = 1
        for param in ccopars_no_t.keys():
            knownparam = array([ccopartuple[j] for ccopartuple in ccopartuples])
            allparams = smoothinterp(allt, knownt, knownparam, smoothness=1)
            ccopar[param] = allparams[findinds(allt,t)]
            j += 1
        ccopar['t'] = t
        return ccopar

    def evaluate(self,x,popsize,t,randseed=None,bounds=None):
        ccopar = self.getccopar(t,randseed,bounds)
        return self.function(x,ccopar,popsize)

    @abc.abstractmethod # This method must be defined by the derived class
    def function(self,x,ccopar,popsize):
        pass

######## SPECIFIC CCOF IMPLEMENTATIONS
class Costcov(CCOF):
    '''Cost-coverage objects'''
    
    def function(self,x,ccopar,popsize):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        from numpy import exp
        u = ccopar['unitcost']
        s = ccopar['saturation']
        y = (2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize
        return y      
                        
class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        i = ccopar['intercept'][0]
        g = ccopar['gradient'][0]
        y = i + (x*g)/popsize
        return y
      
