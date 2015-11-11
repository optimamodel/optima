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
        self.programs = programs if programs else {}
        self.gettargetpops() if programs else []
        self.gettargetpars() if programs else []
        self.gettargetpartypes() if programs else []
        self.initialize_covout() if programs else []
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = '\n'
        output += '       Response name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog.name for prog in self.programs.values()]
        output += 'Targeted populations: %s\n'    % self.targetpops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                  ID: %s\n'    % self.id
        return output

    def gettargetpops(self):
        '''Lists populations targeted by some program in the response'''
        self.targetpops = []
        if self.programs:
            for prog in self.programs.values():
                for x in prog.targetpops: self.targetpops.append(x)
            self.targetpops = list(set(self.targetpops))
    
    def gettargetpars(self):
        '''Lists model parameters targeted by some program in the response'''
        self.targetpars = []
        if self.programs:
            for prog in self.programs.values():
                for x in prog.targetpars: self.targetpars.append(x)

    def gettargetpartypes(self):
        '''Lists model parameters targeted by some program in the response'''
        self.targetpartypes = []
        if self.programs:
            for prog in self.programs.values():
                for x in prog.targetpartypes: self.targetpartypes.append(x)
            self.targetpartypes = list(set(self.targetpartypes))

    def initialize_covout(self):
        '''Initializes the required coverage-outcome curves.
           Parameters for actually defining these should be added using 
           R.covout[paramtype][parampop].addccopar()'''
        self.gettargetpops()
        self.covout = {}
        for targetpartype in self.targetpartypes:
            self.covout[targetpartype] = {}
            for targetpop in self.progs_by_targetpar(targetpartype).keys():
                self.covout[targetpartype][targetpop] = Covout()

    def addprog(self,newprog,overwrite=False):
        if newprog not in self.programs.keys():
            self.programs[newprog.keys()[0]] = newprog.values()[0]
            self.gettargetpops()
            self.gettargetpartypes
            self.initialize_covout()
            print('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (newprog.keys()[0], self.name, [p.name for p in self.programs.values()]))
        else:
            raise Exception('Program "%s" is already present in programset "%s".' % (newprog.name, self.name))
        
    def optimizable(self):
        return [True if prog.targetpars else False for prog in self.programs.values()]

    def progs_by_targetpop(self, filter_pop=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpop = defaultdict(list)
        for prog in self.programs.values():
            targetpops = prog.targetpops if prog.targetpops else None
            if targetpops:
                for targetpop in targetpops:
                    progs_by_targetpop[targetpop].append(prog)
        if filter_pop: return dict(progs_by_targetpop)[filter_pop]
        else: return dict(progs_by_targetpop)
            
    def progs_by_targetpartype(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpartype = defaultdict(list)
        for prog in self.programs.values():
            targetpartypes = prog.targetpartypes if prog.targetpartypes else None
            if targetpartypes:
                for targetpartype in targetpartypes :
                    progs_by_targetpartype[targetpartype].append(prog)
        if filter_partype: return dict(progs_by_targetpartype)[filter_partype]
        else: return dict(progs_by_targetpartype)

    def progs_by_targetpar(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpar = {}
        for targetpartype in self.targetpartypes:
            progs_by_targetpar[targetpartype] = defaultdict(list)
            for prog in self.progs_by_targetpartype(targetpartype):
                targetpars = prog.targetpars if prog.targetpars else None
                for targetpar in targetpars:
                    if targetpartype==targetpar['param']: progs_by_targetpar[targetpartype][targetpar['pop']].append(prog)
            progs_by_targetpar[targetpartype] = dict(progs_by_targetpar[targetpartype])
        if filter_partype: return dict(progs_by_targetpar)[filter_partype]
        else: return dict(progs_by_targetpar)
            
    def targetpars_by_prog(self,filter_prog=None):
        '''Return a dictionary with:
             keys: all programs
             values: all model parameters targeted by that program'''
        targetpars_by_prog = {}
        progs_by_targetpop = self.progs_by_targetpop()
        for targetpop in progs_by_targetpop.keys():
            for prog in progs_by_targetpop[targetpop]:
                targetpars_by_prog[prog.name] = defaultdict(list)
                for targetpar in prog.targetpars:
                    targetpars_by_prog[prog.name][targetpar['pop']].append(targetpar['param'])
                targetpars_by_prog[prog.name] = dict(targetpars_by_prog[prog.name])
        if filter_prog: return targetpars_by_prog[filter_prog]
        else: return targetpars_by_prog

    def getcoverage(self,tvec,budget,perturb=False):
        coverage = dict()
        return coverage
        
    def getoutcomes(self,tvec,budget,perturb=False):
        outcomes = dict()
        return outcomes

class Program(object):
    ''' Defines a single program. 
    Can be initialized with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    modelpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]'''

    def __init__(self,name,targetpars=None,targetpops =None,ccopars=None,costcovdata=None,nonhivdalys=0):
        '''Initialize'''
        self.name = name
        self.id = uuid()
        self.targetpars = targetpars if targetpars else []            
        self.targetpops = targetpops if targetpops else []
        self.targetpartypes = list(set([x['param'] for x in targetpars])) if targetpars else []
        self.costcovfn = Costcov(ccopars=ccopars)
        self.costcovdata = costcovdata if costcovdata else {'t':[],'cost':[],'coverage':[]}
        
    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += '          Program name: %s\n'    % self.name
        output += '  Targeted populations: %s\n'    % self.targetpops 
        output += '   Targeted parameters: %s\n'    % self.targetpars 
        output += '\n'
        return output

    def addtargetpar(self,targetpar):
        '''Add a model parameter to be targeted by this program'''
        if targetpar not in self.targetpars:
            if not targetpar.get('covout'): targetpar['covout'] = Covout()
            self.targetpars.append(targetpar)
            print('\nAdded target parameter "%s" to the list of target parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.name, self.targetpars))
        else:
            raise Exception('The target parameter you are trying to add is already present in the list of target parameters affected by this program:%s.' % self.targetpars)
        return None
        
    def rmtargetpar(self,targetpar):
        '''Remove a model parameter from those targeted by this program'''
        if targetpar not in self.targetpars:
            raise Exception('The target parameter you have selected for removal is not in the list of target parameters affected by this program:%s.' % self.targetpars)
        else:
            self.targetpars.pop(self.targetpars.index(targetpar))
            print('\nRemoved model parameter "%s" from the list of model parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.name, self.targetpars))
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
        y = self.costcovfn.evaluate()
        return y      
        
class CCOF(object):
    '''Cost-coverage, coverage-outcome and cost-outcome objects'''
    __metaclass__ = abc.ABCMeta

    def __init__(self,ccopars=None):
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
            for ccopartype in ccopar.keys():
                self.ccopars[ccopartype] = [ccopar[ccopartype]]
            if ccopar.get('unitcost') and not ccopar['saturation']: self.ccopars[ccopartype].append(1.)
        else:
            if ccopar['t'] not in self.ccopars['t']:
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].append(ccopar[ccopartype])
                if self.ccopars.get('saturation') and not ccopar['saturation']: self.ccopars[ccopartype].append(1.)
                print('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars))
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = {}
                    for ccopartype in self.ccopars.keys():
                        oldccopar[ccopartype] = self.ccopars[ccopartype][ind]
                        self.ccopars[ccopartype][ind] = ccopar[ccopartype]
                    if self.ccopars.get('saturation') and not ccopar['saturation']: self.ccopars[ccopartype].append(1.)
                    print('\nModified CCO parameter from "%s" to "%s". \nCCO parameters for are: %s' % (oldccopar, ccopar, self.ccopars))
                else:
                    raise Exception('You have already entered CCO parameters for the year %s. If you want to overwrite it, set overwrite=True when calling addccopar().' % ccopar['t'])
        return None

    def rmccopar(self,t):
        '''Remove cost-coverage-outcome data point. The point to be removed can be specified by year (int or float).'''
        if isinstance(t,int) or isinstance(t,float):
            if int(t) in self.ccopars['t']:
                ind = self.ccopars['t'].index(int(t))
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].pop(ind)
                print('\nRemoved CCO parameters in year "%s". \nCCO parameters are: %s' % (t, self.ccopars))
            else:
                raise Exception('You have asked to remove CCO parameters for the year %s, but no data was added for that year. Available parameters are: %s' % (t, self.ccopars))            
        return None

    def getccopar(self,t,randseed=None,bounds=None):
        '''Get a cost-coverage-outcome parameter set for any year in range 1900-2100'''
        from utils import smoothinterp, findinds
        from numpy import array, arange
        from copy import deepcopy
        
        if not self.ccopars:
            raise Exception('Need parameters for at least one year before function can be evaluated.')            
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
    def emptypars(self):
        pass

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

    def emptypars(self):
        ccopars = {}
        ccopars['saturation'] = None
        ccopars['unitcost'] = None
        ccopars['t'] = None
        return ccopars                        

class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        from numpy import array
        i = ccopar['intercept'][0]
        g = ccopar['gradient'][0]
        y = i + (x*g)/popsize
        if isinstance(y,float): return min(y,1)
        else: return array([min(j,1) for j in y]) 
      
    def emptypars(self):
        ccopars = {}
        ccopars['intercept'] = None
        ccopars['gradient'] = None
        ccopars['t'] = None
        return ccopars                        

