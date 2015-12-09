"""
This module defines the Program and Programset classes, which are 
used to define a single program/modality (e.g., FSW programs) and a 
set of programs, respectively.

Version: 2015nov04 by robynstuart
"""

from numpy import ones, max, prod, array, arange, zeros, exp, linspace, append, log
from optima import printv, uuid, today, getdate, dcp, smoothinterp, findinds, odict
from collections import defaultdict
import abc
from pylab import figure
from matplotlib.ticker import MaxNLocator

class Programset(object):

    def __init__(self, name='default',programs=None):
        ''' Initialize '''
        self.name = name
        self.id = uuid()
        self.programs = odict()
        if programs is not None: self.addprograms(programs)
        self.gettargetpops()
        self.gettargetpars()
        self.gettargetpartypes()
        self.initialize_covout()
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = '\n'
        output += '       Response name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
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
                for thispop in prog.targetpops: self.targetpops.append(thispop)
            self.targetpops = list(set(self.targetpops))
    
    def gettargetpars(self):
        '''Lists model parameters targeted by some program in the response'''
        self.targetpars = []
        if self.programs:
            for thisprog in self.programs.values():
                for thispop in thisprog.targetpars: self.targetpars.append(thispop)

    def gettargetpartypes(self):
        '''Lists model parameter types targeted by some program in the response'''
        self.targetpartypes = []
        if self.programs:
            for thisprog in self.programs.values():
                for thispartype in thisprog.targetpartypes: self.targetpartypes.append(thispartype)
            self.targetpartypes = list(set(self.targetpartypes))

    def initialize_covout(self):
        '''Initializes the required coverage-outcome curves.
           Parameters for actually defining these should be added using 
           R.covout[paramtype][parampop].addccopar()'''
        self.gettargetpops()
        self.covout = odict()
        for targetpartype in self.targetpartypes:
            self.covout[targetpartype] = odict()
            for thispop in self.progs_by_targetpar(targetpartype).keys():
                targetingprogs = [x.name for x in self.progs_by_targetpar(targetpartype)[thispop]]                
                initccoparams = {k: [] for k in targetingprogs}
                initccoparams['t'],initccoparams['intercept'] = [], []
                self.covout[targetpartype][thispop] = Covout(initccoparams)                

    def addprograms(self,newprograms):
        ''' Add new programs'''
        if type(newprograms)==Program: newprograms = [newprograms]
        if type(newprograms)==list:
            for newprogram in newprograms: 
                if newprogram not in self.programs:
                    self.programs[newprogram.name] = newprogram
                    self.gettargetpops()
                    self.gettargetpartypes()
                    self.initialize_covout()
                    print('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (newprogram.name, self.name, [p.name for p in self.programs.values()]))
                else:
                    raise Exception('Program "%s" is already present in programset "%s".' % (newprogram.name, self.name))
        elif type(newprograms)==dict:
            for newprogram in newprograms.values(): 
                if newprogram not in self.programs:
                    self.programs[newprogram.name] = newprogram
                    self.gettargetpops()
                    self.gettargetpartypes()
                    self.initialize_covout()
                    print('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (newprogram.name, self.name, [p.name for p in self.programs.values()]))
                else:
                    raise Exception('Program "%s" is already present in programset "%s".' % (newprogram.name, self.name))
                   
    def rmprogram(self,program):
        ''' Remove a program. Expects type(program) in [Program,str]'''
        if not type(program)==str: program = program.name
        if program not in self.programs:
            raise Exception('You have asked to remove program "%s", but there is no program by this name in programset "%s". Available programs are' % (program, self.name, [p for p in self.programs]))
        else:
            self.programs.pop(program)
            self.gettargetpops()
            self.gettargetpartypes()
            self.initialize_covout()
            print('\nRemoved program "%s" from programset "%s". \nPrograms in this programset are: %s' % (program, self.name, [p.name for p in self.programs.values()]))
        
    def optimizable(self):
        return [True if prog.targetpars else False for prog in self.programs.values()]

    def progs_by_targetpop(self, filter_pop=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpop = defaultdict(list)
        for thisprog in self.programs.values():
            targetpops = thisprog.targetpops if thisprog.targetpops else None
            if targetpops:
                for thispop in targetpops:
                    progs_by_targetpop[thispop].append(thisprog)
        if filter_pop: return dict(progs_by_targetpop)[filter_pop]
        else: return dict(progs_by_targetpop)
            
    def progs_by_targetpartype(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpartype = defaultdict(list)
        for thisprog in self.programs.values():
            targetpartypes = thisprog.targetpartypes if thisprog.targetpartypes else None
            if targetpartypes:
                for thispartype in targetpartypes :
                    progs_by_targetpartype[thispartype].append(thisprog)
        if filter_partype: return dict(progs_by_targetpartype)[filter_partype]
        else: return dict(progs_by_targetpartype)

    def progs_by_targetpar(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpar = {}
        for thispartype in self.targetpartypes:
            progs_by_targetpar[thispartype] = defaultdict(list)
            for prog in self.progs_by_targetpartype(thispartype):
                targetpars = prog.targetpars if prog.targetpars else None
                for targetpar in targetpars:
                    if thispartype==targetpar['param']: progs_by_targetpar[thispartype][targetpar['pop']].append(prog)
            progs_by_targetpar[thispartype] = dict(progs_by_targetpar[thispartype])
        if filter_partype: return dict(progs_by_targetpar)[filter_partype]
        else: return dict(progs_by_targetpar)
            
    def getprogcoverage(self,budget,t,parset,proportion=False,perturb=False,verbose=2):
        '''Budget is currently assumed to be a DICTIONARY OF ARRAYS'''        
        coverage = {}
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    coverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    coverage[thisprog] = self.programs[thisprog].getcoverage(x=spending,t=t,parset=parset,proportion=proportion) 
            else: coverage[thisprog] = None
        return coverage
        
    def getprogbudget(self,coverage,t,parset,proportion=False,perturb=False,verbose=2):
        '''Budget is currently assumed to be a DICTIONARY OF ARRAYS'''        
        budget = {}
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    budget[thisprog] = None
                else:
                    cov = coverage[thisprog] # Get the amount of money spent on this program
                    budget[thisprog] = self.programs[thisprog].getbudget(x=cov,t=t,parset=parset,proportion=proportion) 
            else: budget[thisprog] = None
        return budget
        
    def getpopcoverage(self,budget,t,parset,perturb=False,verbose=2):
        '''Get the number of people from each population covered by each program...'''
        popcoverage = {}
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    popcoverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    popcoverage[thisprog] = self.programs[thisprog].getcoverage(x=spending,t=t,parset=parset,total=False) 
            else: popcoverage[thisprog] = None
        return popcoverage

    def getoutcomes(self,forwhat,t,parset,forwhattype='budget',interaction='random',perturb=False):
        ''' Get the model parameters corresponding to a budget or coverage vector'''
        nyrs = len(t)
        outcomes = odict()
        
        if forwhattype=='coverage':
            budget = self.getprogbudget(coverage=forwhat,t=t,parset=parset)
        else: budget = forwhat
        
        for thispartype in self.targetpartypes: # Loop over parameter types
            outcomes[thispartype] = odict()

            for thispop in self.progs_by_targetpar(thispartype).keys(): # Loop over the populations associated with this parameter type
                delta, thiscov = odict(), odict()
                
                for thisprog in self.progs_by_targetpar(thispartype)[thispop]: # Loop over the programs that target this parameter/population combo
                    if not self.covout[thispartype][thispop].ccopars[thisprog.name]:
                        print('WARNING: no coverage-outcome function defined for optimizable program  "%s", skipping over... ' % (thisprog.name))
                        outcomes[thispartype][thispop] = None
                    else:
                        outcomes[thispartype][thispop] = self.covout[thispartype][thispop].getccopar(t=t)['intercept']
                        x = budget[thisprog.name]
                        thiscov[thisprog.name] = thisprog.getcoverage(x=x,t=t,parset=parset,proportion=True,total=False)[thispop]
                        delta[thisprog.name] = self.covout[thispartype][thispop].getccopar(t=t)[thisprog.name]

                if interaction == 'additive':
                        # Outcome += c1*delta_out1 + c2*delta_out2
                    for thisprog in self.progs_by_targetpar(thispartype)[thispop]:
                        if not self.covout[thispartype][thispop].ccopars[thisprog.name]:
                            print('WARNING: no coverage-outcome parameters defined for program  "%s", population "%s" and parameter "%s". Skipping over... ' % (thisprog.name, thispop, thispartype))
                            outcomes[thispartype][thispop] = None
                        else: outcomes[thispartype][thispop] += thiscov[thisprog.name]*delta[thisprog.name]
                        
                elif interaction == 'nested':
                    # Outcome += c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
                    for yr in range(nyrs):
                        cov,delt = [],[]
                        for thisprog in thiscov.keys():
                            cov.append(thiscov[thisprog][yr])
                            delt.append(delta[thisprog][yr])
                        cov_tuple = sorted(zip(cov,delt)) # A tuple storing the coverage and delta out, ordered by coverage
                        for j in range(len(cov_tuple)): # For each entry in here
                            if j == 0: c1 = cov_tuple[j][0]
                            else: c1 = cov_tuple[j][0]-cov_tuple[j-1][0]
                            outcomes[thispartype][thispop][yr] += c1*max([ct[1] for ct in cov_tuple[j:]])                
            
                elif interaction == 'random':
                    # Outcome += c1(1-c2)* delta_out1 + c2(1-c1)*delta_out2 + c1c2* max(delta_out1,delta_out2)
                
                    for prog1 in thiscov.keys():
                        product = ones(thiscov[prog1].shape)
                        for prog2 in thiscov.keys():
                            if prog1 != prog2:
                                product *= (1-thiscov[prog2])
        
                        outcomes[thispartype][thispop] += delta[prog1]*thiscov[prog1]*product 

                    # Recursion over overlap levels
                    def overlap_calc(indexes,target_depth):
                        if len(indexes) < target_depth:
                            accum = 0
                            for j in range(indexes[-1]+1,len(thiscov)):
                                accum += overlap_calc(indexes+[j],target_depth)
                            return thiscov.values()[indexes[-1]]*accum
                        else:
                            return thiscov.values()[indexes[-1]]* max([delta.values()[x] for x in [0]],0)

                    # Iterate over overlap levels
                    for i in range(2,len(thiscov)): # Iterate over numbers of overlapping programs
                        for j in range(0,len(thiscov)-1): # Iterate over the index of the first program in the sum
                            outcomes[thispartype][thispop] += overlap_calc([j],i)

                    # All programs together
                    outcomes[thispartype][thispop] += prod(array(thiscov.values()),0)*[max([c[j] for c in delta.values()]) for j in range(nyrs)]
                
                else: raise Exception('Unknown reachability type "%s"',interaction)
        
        return outcomes
        
    def getparset(self,forwhat,t,parset,forwhattype='budget',newparsetname='programpars',interaction='random',perturb=False):
        ''' Make a parset'''
        outcomes = self.getoutcomes(forwhat=forwhat,t=t,parset=parset,interaction=interaction,perturb=perturb)
        progparset = dcp(parset)
        progparset.name = newparsetname
        progparset.created = today() 
        progparset.modified = today() 
        for outcome in outcomes.keys():
            for p in outcomes[outcome].keys():
                progparset.pars[0][outcome].t[p] = append(progparset.pars[0][outcome].t[p], min(t)-1) # Include the year before the programs start...
                progparset.pars[0][outcome].y[p] = append(progparset.pars[0][outcome].y[p], progparset.pars[0][outcome].y[p][0]) # Include the year before the programs start...
                progparset.pars[0][outcome].t[p] = append(progparset.pars[0][outcome].t[p], array(t))
                progparset.pars[0][outcome].y[p] = append(progparset.pars[0][outcome].y[p], array(outcomes[outcome][p]))
            
        return progparset
        
    def plotallcoverage(self,t,parset,xupperlim=None,targetpopprop=None,existingFigure=None,verbose=2,randseed=None,bounds=None):
        ''' Plot the cost-coverage curve for all programs'''
    
        cost_coverage_figures = {}
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program', 1, verbose)
                else:
                    cost_coverage_figures[thisprog] = self.programs[thisprog].plotcoverage(t=t,parset=parset,xupperlim=xupperlim,targetpopprop=targetpopprop,existingFigure=existingFigure,randseed=randseed,bounds=bounds)

        return cost_coverage_figures   
        
class Program(object):
    ''' Defines a single program. 
    Can be initialized with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    modelpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]'''

    def __init__(self,name,targetpars=None,targetpops=None,ccopars=None,costcovdata=None,nonhivdalys=0):
        '''Initialize'''
        self.name = name
        self.id = uuid()
        self.targetpars = targetpars if targetpars else []
        self.targetpops = targetpops if targetpops else []
        self.targetpartypes = list(set([thispar['param'] for thispar in targetpars])) if targetpars else []
        self.optimizable()
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

    def optimizable(self):
        return True if self.targetpars else False

    def addtargetpar(self,targetpar):
        '''Add a model parameter to be targeted by this program'''
        if targetpar not in self.targetpars:
            self.targetpars.append(targetpar)
            self.optimizable
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
            self.optimizable
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

    def gettargetpopsize(self,t,parset,total=True):
        '''Returns target population size in a given year for a given spending amount.'''

        # Figure out input data type, transform if necessary
        if type(t) in [float,int]: t = array([t])
        elif type(t)==list: t = array(t)

        # Sum the target populations
        targetpopsize = {}
        allpops = getpopsizes(parset=parset,years=t,filter_pop=None)
        for targetpop in self.targetpops:
            targetpopsize[targetpop] = allpops[targetpop]

        if total: return sum(targetpopsize.values())
        else: return targetpopsize

    def getcoverage(self,x,t,parset,targetpopprop=None,total=True,proportion=False,toplot=False):
        '''Returns coverage for a time/spending vector'''

        poptargeted = self.gettargetpopsize(t=t,parset=parset,total=False)
        totaltargeted = sum(poptargeted.values())
        totalreached = self.costcovfn.evaluate(x=x,popsize=totaltargeted,t=t,toplot=toplot)
        
        popreached = {}
        if not total and not targetpopprop: # calculate targeting since it hasn't been provided
            targetpopprop = {}
            for targetpop in self.targetpops:
                targetpopprop[targetpop] = poptargeted[targetpop]/totaltargeted
                popreached[targetpop] = totalreached*targetpopprop[targetpop]
                if proportion: popreached[targetpop] /= totaltargeted 

        if total: return totalreached/totaltargeted if proportion else totalreached
        else: return popreached
        
    def getbudget(self,x,t,parset,proportion=False,toplot=False):
        '''Returns budget for a coverage vector'''

        poptargeted = self.gettargetpopsize(t=t,parset=parset,total=False)
        totaltargeted = sum(poptargeted.values())
        if not proportion: reqbudget = self.costcovfn.evaluate(x=x,popsize=totaltargeted,t=t,inverse=True,toplot=False)
        else: reqbudget = self.costcovfn.evaluate(x=x*totaltargeted,popsize=totaltargeted,t=t,inverse=True,toplot=False)
        return reqbudget
                            
    def plotcoverage(self,t,parset,xupperlim=None,targetpopprop=None,existingFigure=None,randseed=None,bounds=None):
        ''' Plot the cost-coverage curve for a single program'''
        plotdata = {}
        if xupperlim is None: xupperlim = 10e6
        x = linspace(0,xupperlim,100)
        plotdata['xlinedata'] = x
        try:
            y = self.getcoverage(x=x,t=t,parset=parset,targetpopprop=None,total=True,proportion=False,toplot=True)
        except:
            y = None
        plotdata['ylinedata'] = y
        plotdata['xlabel'] = 'USD'
        plotdata['ylabel'] = 'Number covered'

        cost_coverage_figure = existingFigure if existingFigure else figure()
        cost_coverage_figure.hold(True)
        axis = cost_coverage_figure.gca()

        if y is not None:
            for yr in range(y.shape[0]):
                axis.plot(
                    x,
                    y[yr],
                    linestyle='-',
                    linewidth=2,
                    color='#a6cee3')
        axis.scatter(
            self.costcovdata['cost'],
            self.costcovdata['coverage'],
            color='#666666')
    
        axis.set_xlim([0, xupperlim])
        axis.set_ylim(bottom=0)
        axis.tick_params(axis='both', which='major', labelsize=11)
        axis.set_xlabel(plotdata['xlabel'], fontsize=11)
        axis.set_ylabel(plotdata['ylabel'], fontsize=11)
        axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
        axis.set_title(self.name)
    
        return cost_coverage_figure
        
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
        ''' Add or replace parameters for cost-coverage functions'''

        if ccopar.get('unitcost') and not ccopar.get('saturation'): ccopar['saturation'] = 1.

        if self.ccopars is None:
            self.ccopars = {}
            for ccopartype in ccopar.keys():
                self.ccopars[ccopartype] = [ccopar[ccopartype]]
        else:
            if (not self.ccopars['t']) or (ccopar['t'] not in self.ccopars['t']):
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].append(ccopar[ccopartype])
                print('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars))
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = {}
                    for ccopartype in self.ccopars.keys():
                        oldccopar[ccopartype] = self.ccopars[ccopartype][ind]
                        self.ccopars[ccopartype][ind] = ccopar[ccopartype]
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

    def getccopar(self,t,verbose=1,randseed=None,bounds=None):
        '''Get a cost-coverage-outcome parameter set for any year in range 1900-2100'''
        
        # Error checks
        if not self.ccopars:
            raise Exception('Need parameters for at least one year before function can be evaluated.')            
        elif not self.ccopars['t']:
            raise Exception('Need parameters for at least one year before function can be evaluated.')
        if randseed and bounds:
            raise Exception('Either select bounds or specify randseed')            

        # Set up necessary variables
        ccopar = {}
        if isinstance(t,(float,int)): t = [t]
        nyrs = len(t)
        ccopars_no_t = dcp(self.ccopars)
        del ccopars_no_t['t']
        ccopartuples = sorted(zip(self.ccopars['t'], *ccopars_no_t.values()))
        knownt = array([ccopartuple[0] for ccopartuple in ccopartuples])
        allt = arange(1900,2100)
        j = 1
        
        # Calculate interpolated parameters
        for param in ccopars_no_t.keys():
            knownparam = array([ccopartuple[j] for ccopartuple in ccopartuples])
            allparams = smoothinterp(allt, knownt, knownparam, smoothness=1)
            ccopar[param] = zeros(nyrs)
            for yr in range(nyrs):
                ccopar[param][yr] = allparams[findinds(allt,t[yr])]
            if isinstance(t,list): ccopar[param] = ccopar[param].tolist()
            j += 1
        
        # Finsh, return
        ccopar['t'] = t
        printv('\nCalculated CCO parameters in year(s) %s to be %s' % (t, ccopar), 4, verbose)
        return ccopar

    def evaluate(self,x,popsize,t,toplot,inverse=False,randseed=None,bounds=None):
        if (not toplot) and (not len(x)==len(t)): raise Exception('x needs to be the same length as t, we assume one spending amount per time point.')
        ccopar = self.getccopar(t=t,randseed=randseed,bounds=bounds)
        if not inverse: return self.function(x=x,ccopar=ccopar,popsize=popsize)
        else: return self.inversefunction(x=x,ccopar=ccopar,popsize=popsize)

    @abc.abstractmethod # This method must be defined by the derived class
    def emptypars(self):
        pass

    @abc.abstractmethod # This method must be defined by the derived class
    def function(self,x,ccopar,popsize):
        pass

    @abc.abstractmethod # This method must be defined by the derived class
    def inversefunction(self,x,ccopar,popsize):
        pass

######## SPECIFIC CCOF IMPLEMENTATIONS
class Costcov(CCOF):
    '''Cost-coverage objects'''
            
    def function(self,x,ccopar,popsize):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if isinstance(popsize,(float,int)): popsize = array([popsize])
                        
        nyrs,npts = len(u),len(x)
        if nyrs==npts: return (2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize
        else:
            y = zeros((nyrs,npts))        
            for yr in range(nyrs):
                y[yr,:] = (2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr]
            return y
 
    def inversefunction(self,x,ccopar,popsize):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if isinstance(popsize,(float,int)): popsize = array([popsize])
                        
        nyrs,npts = len(u),len(x)
        if nyrs==npts: return -0.5*popsize*s*u*log(2*s/(x/popsize+s)-1)
        else: raise Exception('coverage vector should be the same length as params.')

    def emptypars(self):
        ccopars = {}
        ccopars['saturation'] = None
        ccopars['unitcost'] = None
        ccopars['t'] = None
        return ccopars                        

class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        '''Returns single-program outcome in a given year for a given spending amount. Currently assumes coverage is a proportion.'''
        i = array(ccopar['intercept'])
        g = array(ccopar['gradient'])
        if isinstance(popsize,(float,int)): popsize = array([popsize])
        y = array([min(j,1) for j in (i + (x*g)/popsize)])
        return y
        
    def inversefunction(self,x,ccopar,popsize):
        pass
      
    def emptypars(self):
        ccopars = {}
        ccopars['intercept'] = None
        ccopars['gradient'] = None
        ccopars['t'] = None
        return ccopars                        


#######################################################
# What needs to happen to get population sizes...
#######################################################

def getpopsizes(parset, years, ind=0, filter_pop=None):
    '''Get population sizes in given years from a parset.'''
    
    if type(years) in [float, int]: years = array([[years]])
    elif type(years)==list: years = array([years])
    
    initpopsizes = parset.interp(ind=0, tvec=years, verbose=0)['popsize']
    popsizes = {}

    for popnumber, pop in enumerate(parset.pars[ind]['popkeys']):
        popsizes[pop] = initpopsizes[popnumber,:]

    if filter_pop: return {filter_pop: popsizes[filter_pop]}
    else: return popsizes
   
