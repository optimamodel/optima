"""
This module defines the Program and Response classes, which are 
used to define a single program/modality (e.g., FSW programs) and a 
set of programs, respectively.

Version: 2015nov04 by robynstuart
"""
from uuid import uuid4
from datetime import datetime
from utils import getdate
from collections import defaultdict

class Programset(object):

    def __init__(self, name='default',programs=None):
        ''' Initialise '''
        self.name = name
        self.id = uuid4()
        self.programs = programs if programs else []
        self.created = datetime.today()
        self.modified = datetime.today()
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += 'Response name: %s\n'    % self.name
        output += '     Programs: %s\n'    % [prog.name for prog in self.programs]
        output += ' Date created: %s\n'    % getdate(self.created)
        output += 'Date modified: %s\n'    % getdate(self.modified)
        output += '           ID: %s\n'    % self.id
        return output

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

class Program(object):
    ''' Defines a single program. 
    Can be initialised with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    modelpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]'''

    def __init__(self,name,modelpars=None,ccpars=None,ccdata=None,nonhivdalys=0):
        self.name = name
        self.id = uuid4()
        self.modelpars = modelpars if modelpars else []
        self.pops = list(set([x['pop'] for x in modelpars])) if modelpars else []
        self.ccpars = ccpars if ccpars else {'t':[],'saturation':[],'unitcost':[]}
        self.ccdata = ccdata if ccdata else {'t':[],'cost':[],'coverage':[]}
        
    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += '          Program name: %s\n'    % self.name
        output += '  Targeted populations: %s\n'    % self.pops 
        output += '   Targeted parameters: %s\n'    % self.modelpars 
        output += '    Program parameters: %s\n'    % self.ccpars
        output += '\n'
        return output

    def addmodelpar(self,modelpar):
        '''Add a model parameter to be targeted by this program'''
        if modelpar not in self.modelpars:
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
        
    def addccpar(self,ccpar,ow=False):
        ''' Add or replace parameters for cost-coverage function'''
        if ccpar['t'] not in self.ccpars['t']:
            self.ccpars['t'].append(ccpar['t'])
            self.ccpars['saturation'].append(ccpar['saturation'] if ccpar.get('saturation') else 1.)
            self.ccpars['unitcost'].append(ccpar['unitcost'])
            print('\nAdded cc parameters "%s" to program: "%s". \nCC parameters for this program are: %s' % (ccpar, self.name, self.ccpars))
        else:
            if ow:
                ind = self.ccpars['t'].index(int(ccpar['t']))
                oldccpar = {'t':self.ccpars['t'][ind], 'saturation':self.ccpars['saturation'][ind], 'unitcost':self.ccpars['unitcost'][ind]}
                self.ccpars['t'][ind] = ccpar['t']
                self.ccpars['saturation'][ind] = ccpar['saturation'] if ccpar.get('saturation') else 1.
                self.ccpars['unitcost'][ind] = ccpar['unitcost']
                print('\nModified cc parameter from "%s" to "%s" for program: "%s". \nCC parameters for this program are: %s' % (oldccpar, ccpar, self.name, self.ccpars))
            else:
                raise Exception('You have already entered cost function parameters for the year %s. If you want to overwrite it, set ow=True when calling addccpar().' % ccpar['t'])
        return None

    def rmccpar(self,year):
        '''Remove cost-coverage data point. The point to be removed can be specified by year (int or float).'''
        if isinstance(year,int) or isinstance(year,float):
            if int(year) in self.ccpars['t']:
                self.ccpars['unitcost'].pop(self.ccpars['t'].index(int(year)))
                self.ccpars['saturation'].pop(self.ccpars['t'].index(int(year)))
                self.ccpars['t'].pop(self.ccpars['t'].index(int(year)))
                print('\nRemoved cc parameters in year "%s" from program: "%s". \nCC parameters for this program are: %s' % (year, self.name, self.ccpars))
            else:
                raise Exception('You have asked to remove cost function parameters for the year %s, but no data was added for that year. Available parameters are: %s' % (year, self.ccpars))            
        return None
        
    def getccpar(self,year):
        '''Get a cost-coverage parameter set for a year for which it hasn't been explicitly entered'''
        from utils import smoothinterp, findinds
        from numpy import array, arange
        
        ccparlist = sorted(zip(self.ccpars['t'],self.ccpars['saturation'],self.ccpars['unitcost']))
        knownt = array([t for (t,s,u) in ccparlist])
        knownu = array([u for (t,s,u) in ccparlist])
        knowns = array([s for (t,s,u) in ccparlist])
        allt = arange(1900,2100)
        allu = smoothinterp(allt, knownt, knownu, smoothness=1)
        alls = smoothinterp(allt, knownt, knowns, smoothness=1)

        newu = allu[findinds(allt,year)]
        news = alls[findinds(allt,year)]
        
        return {'t':year,'unitcost':newu,'saturation':news}

    def addccdatum(self,ccdatum,ow=False):
        '''Add cost-coverage data point'''
        if ccdatum['t'] not in self.ccdata['t']:
            self.ccdata['t'].append(ccdatum['t'])
            self.ccdata['cost'].append(ccdatum['cost'])
            self.ccdata['coverage'].append(ccdatum['coverage'])
            print('\nAdded cc data "%s" to program: "%s". \nCC data for this program are: %s' % (ccdatum, self.name, self.ccdata))
        else:
            if ow:
                ind = self.ccdata['t'].index(int(ccdatum['t']))
                oldccdatum = {'t':self.ccdata['t'][ind],'cost':self.ccdata['cost'][ind],'coverage':self.ccdata['coverage'][ind]}
                self.ccdata['t'][ind] = ccdatum['t']
                self.ccdata['cost'][ind] = ccdatum['cost']
                self.ccdata['coverage'][ind] = ccdatum['coverage']
                newccdatum = {'t':self.ccdata['t'][ind],'cost':self.ccdata['cost'][ind],'coverage':self.ccdata['coverage'][ind]}
                print('\nModified cc data from "%s" to "%s" for program: "%s". \nCC data for this program are: %s' % (oldccdatum, newccdatum, self.name, self.ccdata))
            else:
                raise Exception('You have already entered cost and/or coverage data for the year %s .' % ccdatum['t'])

    def rmccdatum(self,year):
        '''Remove cost-coverage data point. The point to be removed can be specified by year (int or float).'''
        if int(year) in self.ccdata['t']:
            self.ccdata['cost'].pop(self.ccdata['t'].index(int(year)))
            self.ccdata['coverage'].pop(self.ccdata['t'].index(int(year)))
            self.ccdata['t'].pop(self.ccdata['t'].index(int(year)))
            print('\nRemoved cc data in year "%s" from program: "%s". \nCC data for this program are: %s' % (year, self.name, self.ccdata))
        else:
            raise Exception('You have asked to remove data for the year %s, but no data was added for that year. Cost coverage data are: %s' % (year, self.ccdata))

    def getcoverage(self,year,popsize,x):
        '''Returns coverage in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        from numpy import exp
        u = self.getccpar(year)['unitcost']
        s = self.getccpar(year)['saturation']
        y = (2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize
        return y      
        

