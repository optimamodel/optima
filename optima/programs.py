"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2015nov04 by robynstuart
"""
from optima import OptimaException, printv, uuid, today, getdate, dcp, smoothinterp, findinds, odict, Settings, runmodel, sanitize, objatt, objmeth
from numpy import ones, max, prod, array, arange, zeros, exp, linspace, append, log, sort, transpose, nan, isnan, ndarray, concatenate as cat
import abc
import textwrap
from pylab import figure, figtext
from matplotlib.ticker import MaxNLocator

coveragepars=['numtx','numpmtct','numost','numcircum']

class Programset(object):

    def __init__(self, name='default', programs=None, default_interaction='random'):
        ''' Initialize '''
        self.name = name
        self.uid = uuid()
        self.default_interaction = default_interaction
        self.programs = odict()
        if programs is not None: self.addprograms(programs)
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = '\n'
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += 'Targeted populations: %s\n'    % self.targetpops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                 UID: %s\n'    % self.uid
        output += '============================================================\n'
        output += objatt(self)
        output += '============================================================\n'
        output += objmeth(self)
        output += '============================================================\n'
        return output

    def getsettings(self):
        ''' Try to get the freshest settings available '''
        print('Warning, using default settings with program set "%s"' % self.name)
        settings = Settings()
        return settings
        
    def gettargetpops(self):
        '''Update populations targeted by some program in the response'''
        self.targetpops = []
        if self.programs:
            for prog in self.programs.values():
                for thispop in prog.targetpops: self.targetpops.append(thispop)
            self.targetpops = list(set(self.targetpops))

    def gettargetpars(self):
        '''Update model parameters targeted by some program in the response'''
        self.targetpars = []
        if self.programs:
            for thisprog in self.programs.values():
                for thispop in thisprog.targetpars: self.targetpars.append(thispop)

    def gettargetpartypes(self):
        '''Update model parameter types targeted by some program in the response'''
        self.targetpartypes = []
        if self.programs:
            for thisprog in self.programs.values():
                for thispartype in thisprog.targetpartypes: self.targetpartypes.append(thispartype)
            self.targetpartypes = list(set(self.targetpartypes))

    def initialize_covout(self):
        '''Sets up the required coverage-outcome curves.
           Parameters for actually defining these should be added using 
           R.covout[paramtype][parampop].addccopar()'''
        if not self.__dict__.get('covout'): self.covout = odict()

        for targetpartype in self.targetpartypes: # Loop over parameter types
            if not self.covout.get(targetpartype): self.covout[targetpartype] = {} # Initialize if it's not there already
            for thispop in self.progs_by_targetpar(targetpartype).keys(): # Loop over populations
                if self.covout[targetpartype].get(thispop): # Take the pre-existing one if it's there... 
                    ccopars = self.covout[targetpartype][thispop].ccopars 
                else: # ... or if not, set it up
                    ccopars = {}
                    ccopars['intercept'] = []
                    ccopars['t'] = []
                targetingprogs = [thisprog.short for thisprog in self.progs_by_targetpar(targetpartype)[thispop]]
                for tp in targetingprogs:
                    if not ccopars.get(tp): ccopars[tp] = []
                                    
                # Delete any stored programs that are no longer needed (if removing a program)
                progccopars = dcp(ccopars)
                del progccopars['t'], progccopars['intercept']
                for prog in progccopars.keys(): 
                    if prog not in targetingprogs: del ccopars[prog]

                self.covout[targetpartype][thispop] = Covout(ccopars=ccopars,interaction=self.default_interaction)

        # Delete any stored effects that aren't needed (if removing a program)
        for tpt in self.covout.keys():
            if tpt not in self.targetpartypes: del self.covout[tpt]
            else: 
                for tp in self.covout[tpt].keys():
                    if type(tp)==str and tp not in self.progs_by_targetpar(tpt).keys(): del self.covout[tpt][tp]

    def updateprogset(self, verbose=2):
        ''' Update (run this is you change something... )'''
        self.gettargetpars()
        self.gettargetpartypes()
        self.gettargetpops()
        self.initialize_covout()
        printv('\nUpdated programset "%s"' % (self.name), 4, verbose)

    def addprograms(self, newprograms, verbose=2):
        ''' Add new programs'''
        if type(newprograms)==Program: newprograms = [newprograms]
        if type(newprograms)==list:
            for newprogram in newprograms: 
                if newprogram not in self.programs.values():
                    self.programs[newprogram.short] = newprogram
                    print('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (newprogram.short, self.name, [thisprog.short for thisprog in self.programs.values()]))
                else:
                    raise OptimaException('Program "%s" is already present in programset "%s".' % (newprogram.short, self.name))
        self.updateprogset()
                   
    def rmprogram(self,program,verbose=2):
        ''' Remove a program. Expects type(program) in [Program,str]'''
        if not type(program) == str: program = program.short
        if program not in self.programs:
            errormsg = 'You have asked to remove program "%s", but there is no program by this name in programset "%s". Available programs are' % (program, self.name, [thisprog for thisprog in self.programs])
            raise OptimaException(errormsg)
        else:
            self.programs.pop(program)
            self.updateprogset()
            printv('\nRemoved program "%s" from programset "%s". \nPrograms in this programset are: %s' % (program, self.name, [thisprog.short for thisprog in self.programs.values()]), 4, verbose)

    def optimizable(self):
        return [True if prog.optimizable() else False for prog in self.programs.values()]

    def coveragepar(self, coveragepars=coveragepars):
        return [True if par in coveragepars else False for par in self.targetpartypes]

    def progs_by_targetpop(self, filter_pop=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpop = odict()
        for thisprog in self.programs.values():
            targetpops = thisprog.targetpops if thisprog.targetpops else None
            if targetpops:
                for thispop in targetpops:
                    if thispop not in progs_by_targetpop: progs_by_targetpop[thispop] = []
                    progs_by_targetpop[thispop].append(thisprog)
        if filter_pop: return progs_by_targetpop[filter_pop]
        else: return progs_by_targetpop

    def progs_by_targetpartype(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpartype = odict()
        for thisprog in self.programs.values():
            targetpartypes = thisprog.targetpartypes if thisprog.targetpartypes else None
            if targetpartypes:
                for thispartype in targetpartypes:
                    if thispartype not in progs_by_targetpartype: progs_by_targetpartype[thispartype] = []
                    progs_by_targetpartype[thispartype].append(thisprog)
        if filter_partype: return progs_by_targetpartype[filter_partype]
        else: return progs_by_targetpartype

    def progs_by_targetpar(self, filter_partype=None):
        '''Return a dictionary with:
             keys: all populations targeted by programs
             values: programs targeting that population '''
        progs_by_targetpar = odict()
        for thispartype in self.targetpartypes:
            progs_by_targetpar[thispartype] = odict()
            for prog in self.progs_by_targetpartype(thispartype):
                targetpars = prog.targetpars if prog.targetpars else None
                for targetpar in targetpars:
                    if thispartype == targetpar['param']:
                        if targetpar['pop'] not in progs_by_targetpar[thispartype]: progs_by_targetpar[thispartype][targetpar['pop']] = []
                        progs_by_targetpar[thispartype][targetpar['pop']].append(prog)
            progs_by_targetpar[thispartype] = progs_by_targetpar[thispartype]
        if filter_partype: return progs_by_targetpar[filter_partype]
        else: return progs_by_targetpar


    def getdefaultbudget(self, years=None, verbose=2):
        ''' Extract the budget if cost data has been provided'''
        
        # Initialise outputs
        totalbudget, lastbudget, selectbudget = odict(), odict(), odict()

        # Validate inputs
        if type(years) in [int, float]: years = [years]
        if isinstance(years,ndarray): years = years.tolist()

        # Set up internal variables
        settings = self.getsettings()
        tvec = settings.maketvec() 
        emptyarray = array([nan]*len(tvec))
        
        # Get cost data for each program in each year that it exists
        for program in self.programs:
            totalbudget[program] = dcp(emptyarray)
            selectbudget[program] = []
            if self.programs[program].costcovdata['t']:
                for yrno, yr in enumerate(self.programs[program].costcovdata['t']):
                    yrindex = findinds(tvec,yr)
                    totalbudget[program][yrindex] = self.programs[program].costcovdata['cost'][yrno]
                    lastbudget[program] = sanitize(totalbudget[program])[-1]
            else: 
                printv('\nWARNING: no cost data defined for program "%s"...' % program, 1, verbose)
                lastbudget[program] = nan

            # Extract cost data for particular years, if requested 
            if years is not None:
                for yr in years:
                    yrindex = findinds(tvec,yr)
                    selectbudget[program].append(totalbudget[program][yrindex][0])

        return selectbudget if years is not None else lastbudget


    def getprogcoverage(self, budget, t, parset=None, results=None, proportion=False, perturb=False, verbose=2):
        '''Budget is currently assumed to be a DICTIONARY OF ARRAYS'''

        # Initialise output
        coverage = odict()

        # Validate inputs
        if type(t) in [int, float]: t = [t]
        if not isinstance(budget,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
        if not isinstance(budget,odict): budget = odict(budget)
        budget = budget.sort([p.short for p in self.programs.values()])

        # Get program-level coverage for each program
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    coverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    coverage[thisprog] = self.programs[thisprog].getcoverage(x=spending, t=t, parset=parset, results=results, proportion=proportion)
            else: coverage[thisprog] = None

        return coverage


    def getprogbudget(self, coverage, t, parset=None, results=None, proportion=False, perturb=False, verbose=2):
        '''Return budget associated with specified coverage levels'''

        # Initialise output
        budget = odict()

        # Validate inputs
        if type(t) in [int, float]: t = [t]
        if not isinstance(coverage,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
        if not isinstance(coverage,odict): budget = odict(budget)
        coverage = coverage.sort([p.short for p in self.programs.values()])

        # Get budget for each program
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    budget[thisprog] = None
                else:
                    cov = coverage[thisprog] # Get the amount of money spent on this program
                    budget[thisprog] = self.programs[thisprog].getbudget(x=cov, t=t, parset=parset, results=results, proportion=proportion)
            else: budget[thisprog] = None

        return budget


    def getpopcoverage(self, budget, t, parset=None, results=None, perturb=False, verbose=2):
        '''Get the number of people from each population covered by each program.'''

        # Initialise output
        popcoverage = odict()

        # Validate inputs
        if not isinstance(budget,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
        if not isinstance(budget,odict): budget = odict(budget)
        budget = budget.sort([p.short for p in self.programs.values()])

        # Get population-level coverage for each program
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    popcoverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    popcoverage[thisprog] = self.programs[thisprog].getcoverage(x=spending, t=t, parset=parset, results=results, total=False)
            else: popcoverage[thisprog] = None

        return popcoverage


    def getoutcomes(self,coverage, t, parset=None, results=None, perturb=False,coveragepars=coveragepars):
        ''' Get the model parameters corresponding to dictionary of coverage values'''

        # Initialise output
        outcomes = odict()

        # Validate inputs
        if type(t) in [int,float]: t = [t]
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')

        # Set up internal variables
        nyrs = len(t)        
        budget = self.getprogbudget(coverage=coverage, t=t, parset=parset, results=results, proportion=False)

        # Loop over parameter types
        for thispartype in self.targetpartypes:
            outcomes[thispartype] = odict()
            
            # Loop over populations releavent for this parameter type
            for thispop in self.progs_by_targetpar(thispartype).keys():

                # If it's a coverage parameter, you are done
                if thispartype in coveragepars: # and thispop.lower() in ['total','tot','all']:
                    outcomes[thispartype][thispop] = self.covout[thispartype][thispop].getccopar(t=t)['intercept']
                    for thisprog in self.progs_by_targetpar(thispartype)[thispop]: # Loop over the programs that target this parameter/population combo
                        outcomes[thispartype][thispop] += coverage[thisprog.short]

                # If it's an outcome parameter, need to get outcomes
                else:
                    
                    delta, thiscov = odict(), odict()
    
                    # Loop over the programs that target this parameter/population combo
                    for thisprog in self.progs_by_targetpar(thispartype)[thispop]: 
                        if type(thispop)==tuple: thiscovpop = thisprog.targetpops[0] # If it's a partnership parameters, get the target population separately
                        else: thiscovpop = None
                        if not self.covout[thispartype][thispop].ccopars[thisprog.short]:
                            print('WARNING: no coverage-outcome function defined for optimizable program  "%s", skipping over... ' % (thisprog.short))
                            outcomes[thispartype][thispop] = None
                        else:
                            outcomes[thispartype][thispop] = self.covout[thispartype][thispop].getccopar(t=t)['intercept']
                            x = budget[thisprog.short]
                            if thiscovpop: thiscov[thisprog.short] = thisprog.getcoverage(x=x,t=t, parset=parset, results=results, proportion=True,total=False)[thiscovpop]
                            else: thiscov[thisprog.short] = thisprog.getcoverage(x=x, t=t, parset=parset, results=results, proportion=True, total=False)[thispop]
                            delta[thisprog.short] = [self.covout[thispartype][thispop].getccopar(t=t)[thisprog.short][j] - outcomes[thispartype][thispop][j] for j in range(nyrs)]
    
                    if self.covout[thispartype][thispop].interaction == 'additive':
                        # Outcome += c1*delta_out1 + c2*delta_out2
                        for thisprog in self.progs_by_targetpar(thispartype)[thispop]:
                            if not self.covout[thispartype][thispop].ccopars[thisprog.short]:
                                print('WARNING: no coverage-outcome parameters defined for program  "%s", population "%s" and parameter "%s". Skipping over... ' % (thisprog.short, thispop, thispartype))
                                outcomes[thispartype][thispop] = None
                            else: outcomes[thispartype][thispop] += thiscov[thisprog.short]*delta[thisprog.short]
                            
                    elif self.covout[thispartype][thispop].interaction == 'nested':
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
                
                    elif self.covout[thispartype][thispop].interaction == 'random':
                        # Outcome += c1(1-c2)* delta_out1 + c2(1-c1)*delta_out2 + c1c2* max(delta_out1,delta_out2)
    
                        if all(self.covout[thispartype][thispop].ccopars.values()):
                    
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
                    
                    else: raise OptimaException('Unknown reachability type "%s"',self.covout[thispartype][thispop].interaction)
        
        return outcomes
        
    def getpars(self, coverage, t, parset=None, results=None, ind=0, perturb=False):
        ''' Make pars'''
        
        # Validate inputs
        if type(t) in [int,float]: t = [t]
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')

        # Get outcome dictionary
        outcomes = self.getoutcomes(coverage=coverage, t=t, parset=parset, results=results, perturb=perturb)

        # Create a parset and copy over parameter changes
        pars = dcp(parset.pars[ind])
        for outcome in outcomes.keys():
            for p in outcomes[outcome].keys():
                pars[outcome].t[p] = append(pars[outcome].t[p], min(t)-1) # Include the year before the programs start...
                pars[outcome].y[p] = append(pars[outcome].y[p], pars[outcome].y[p][-1]) # Include the year before the programs start...
                pars[outcome].t[p] = append(pars[outcome].t[p], array(t))
                pars[outcome].y[p] = append(pars[outcome].y[p], array(outcomes[outcome][p]))

        return pars

    def plotallcoverage(self,t,parset,existingFigure=None,verbose=2,randseed=None,bounds=None):
        ''' Plot the cost-coverage curve for all programs'''

        cost_coverage_figures = {}
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program', 1, verbose)
                else:
                    cost_coverage_figures[thisprog] = self.programs[thisprog].plotcoverage(t=t,parset=parset,existingFigure=existingFigure,randseed=randseed,bounds=bounds)

        return cost_coverage_figures


class Program(object):
    '''
    Defines a single program. 
    Can be initialized with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    targetpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]
    targetpops, e.g. ['FSW','MSM']
    '''

    def __init__(self, short, targetpars=None, targetpops=None, ccopars=None, costcovdata=None, nonhivdalys=0,
        category='No category', name='', criteria=None, targetcomposition=None):
        '''Initialize'''
        self.short = short
        self.name = name
        self.uid = uuid()
        if targetpars:
            self.targetpars = targetpars
        else: self.targetpars = []
        self.targetpops = targetpops if targetpops else []
        try:
            self.targetpartypes = list(set([thispar['param'] for thispar in self.targetpars])) if self.targetpars else []
        except:
            print("Error while initializing targetpartypes in program %s for targetpars %s" % (short, self.targetpars))
            self.targetpartypes = []
        self.optimizable()
        self.costcovfn = Costcov(ccopars=ccopars)
        self.costcovdata = costcovdata if costcovdata else {'t':[],'cost':[],'coverage':[]}
        self.category = category
        self.criteria = criteria if criteria else {'hivstatus': 'allstates', 'pregnant': False}
        self.targetcomposition = targetcomposition


    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.targetpops
        output += '   Targeted parameters: %s\n'    % self.targetpars
        output += '\n'
        return output


    def optimizable(self):
        return True if self.targetpars else False


    def addtargetpar(self, targetpar, verbose=2):
        '''Add a model parameter to be targeted by this program'''
        if (targetpar['param'],targetpar['pop']) not in [(tp['param'],tp['pop']) for tp in self.targetpars]:
            self.targetpars.append(targetpar)
            printv('\nAdded target parameter "%s" to the list of target parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.short, self.targetpars), 4, verbose)
        else:
            index = [(tp['param'],tp['pop']) for tp in self.targetpars].index((targetpar['param'],targetpar['pop']))
            self.targetpars[index] = targetpar # overwrite
        self.optimizable
        return None


    def rmtargetpar(self, targetpar, verbose=2):
        '''Remove a model parameter from those targeted by this program'''
        if (targetpar['param'],targetpar['pop']) not in [(tp['param'],tp['pop']) for tp in self.targetpars]:
            errormsg = 'The target parameter "%s" you have selected for removal is not in the list of target parameters affected by this program:%s.' % (targetpar, self.targetpars)
            raise OptimaException(errormsg)
        else:
            index = [(tp['param'],tp['pop']) for tp in self.targetpars].index((targetpar['param'],targetpar['pop']))
            self.targetpars.pop(index)
            self.optimizable
            printv('\nRemoved model parameter "%s" from the list of model parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.short, self.targetpars), 4, verbose)
        return None


    def addcostcovdatum(self, costcovdatum, overwrite=False, verbose=2):
        '''Add cost-coverage data point'''
        if costcovdatum['t'] not in self.costcovdata['t']:
            self.costcovdata['t'].append(costcovdatum['t'])
            self.costcovdata['cost'].append(costcovdatum['cost'])
            self.costcovdata['coverage'].append(costcovdatum['coverage'])
            printv('\nAdded cc data "%s" to program: "%s". \nCC data for this program are: %s' % (costcovdatum, self.short, self.costcovdata), 4, verbose)
        else:
            if overwrite:
                ind = self.costcovdata['t'].index(int(costcovdatum['t']))
                oldcostcovdatum = {'t':self.costcovdata['t'][ind],'cost':self.costcovdata['cost'][ind],'coverage':self.costcovdata['coverage'][ind]}
                self.costcovdata['t'][ind] = costcovdatum['t']
                self.costcovdata['cost'][ind] = costcovdatum['cost']
                self.costcovdata['coverage'][ind] = costcovdatum['coverage']
                newcostcovdatum = {'t':self.costcovdata['t'][ind],'cost':self.costcovdata['cost'][ind],'coverage':self.costcovdata['coverage'][ind]}
                printv('\nModified cc data from "%s" to "%s" for program: "%s". \nCC data for this program are: %s' % (oldcostcovdatum, newcostcovdatum, self.short, self.costcovdata), 4, verbose)
            else:
                errormsg = 'You have already entered cost and/or coverage data for the year %s .' % costcovdatum['t']
                raise OptimaException(errormsg)


    def rmcostcovdatum(self, year, verbose=2):
        '''Remove cost-coverage data point. The point to be removed can be specified by year (int or float).'''
        if int(year) in self.costcovdata['t']:
            self.costcovdata['cost'].pop(self.costcovdata['t'].index(int(year)))
            self.costcovdata['coverage'].pop(self.costcovdata['t'].index(int(year)))
            self.costcovdata['t'].pop(self.costcovdata['t'].index(int(year)))
            printv('\nRemoved cc data in year "%s" from program: "%s". \nCC data for this program are: %s' % (year, self.short, self.costcovdata), 4, verbose)
        else:
            errormsg = 'You have asked to remove data for the year %s, but no data was added for that year. Cost coverage data are: %s' % (year, self.costcovdata)
            raise OptimaException(errormsg)


    def gettargetpopsize(self, t, parset=None, results=None, ind=0, total=True):
        '''Returns target population size in a given year for a given spending amount.'''

        # Validate inputs
        if type(t) in [float,int]: t = array([t])
        elif type(t)==list: t = array(t)
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')

        # Initialise outputs
        popsizes = {}
        targetpopsize = {}
        
        # Do everything possible to get settings
        try: settings = parset.project.settings
        except: 
            try: settings = results.project.settings
            except:
                print('Warning, could not find settings for program "%s", using default' % self.name)
                settings = Settings()
        
        

        # If it's a program for everyone... 
        if not self.criteria['pregnant']:
            if self.criteria['hivstatus']=='allstates':
                initpopsizes = parset.pars[ind]['popsize'].interp(tvec=t)
    
            else: # If it's a program for HIV+ people, need to find the number of positives
                if not results: 
                    try: results = parset.getresults(die=True)
                    except OptimaException as E: 
                        print('Failed to extract results because "%s", rerunning the model...' % E.message)
                        results = runmodel(pars=parset.pars[ind], settings=settings)
                        parset.resultsref = results.uid # So it doesn't have to be rerun
                
                cd4index = sort(cat([settings.__dict__[state] for state in self.criteria['hivstatus']])) # CK: this should be pre-computed and stored if it's useful
                eligplhiv = results.raw[ind]['people'][cd4index,:,:].sum(axis=0)
                for yr in t:
                    initpopsizes = eligplhiv[:,findinds(results.tvec,yr)]
                
        # ... or if it's a program for pregnant women.
        else:
            if self.criteria['hivstatus']=='allstates': # All pregnant women
                initpopsizes = parset.pars[ind]['popsize'].interp(tvec=t)*parset.pars[0]['birth'].interp(tvec=t)

            else: # HIV+ pregnant women
                initpopsizes = parset.pars[ind]['popsize'].interp(tvec=t)
                if not results: 
                    try: results = parset.getresults(die=True)
                    except OptimaException as E: 
                        print('Failed to extract results because "%s", rerunning the model...' % E.message)
                        results = runmodel(pars=parset.pars[ind], settings=settings)
                        parset.resultsref = results.uid # So it doesn't have to be rerun
                for yr in t:
                    initpopsizes = parset.pars[ind]['popsize'].interp(tvec=[yr])*parset.pars[ind]['birth'].interp(tvec=[yr])*transpose(results.main['prev'].pops[0,:,findinds(results.tvec,yr)])

        for popnumber, pop in enumerate(parset.pars[ind]['popkeys']):
            popsizes[pop] = initpopsizes[popnumber,:]
        for targetpop in self.targetpops:
            if targetpop.lower() in ['total','tot','all']:
                targetpopsize[targetpop] = sum(popsizes.values())
            else:
                targetpopsize[targetpop] = popsizes[targetpop]
                    
        if total: return sum(targetpopsize.values())
        else: return targetpopsize


    def gettargetcomposition(self, t, parset=None, results=None, total=True):
        '''Tells you the proportion of the total population targeted by a program that is comprised of members from each sub-population group.'''
        targetcomposition = {}

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(poptargeted.values())

        for targetpop in self.targetpops:
            targetcomposition[targetpop] = poptargeted[targetpop]/totaltargeted
        return targetcomposition


    def getcoverage(self, x, t, parset=None, results=None, total=True, proportion=False, toplot=False, bounds=None):
        '''Returns coverage for a time/spending vector'''

        # Validate inputs
        if isinstance(x, (int,float)): x = [x]
        if isinstance(t, (int,float)): t = [t]
        if isinstance(x, list): x = array(x)
        if isinstance(t, list): t = array(t)

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(poptargeted.values())
        totalreached = self.costcovfn.evaluate(x=x, popsize=totaltargeted, t=t, toplot=toplot, bounds=bounds)

        if total: return totalreached/totaltargeted if proportion else totalreached
        else:
            popreached = {}
            targetcomposition = self.targetcomposition if self.targetcomposition else self.gettargetcomposition(t=t,parset=parset) 
            for targetpop in self.targetpops:
                popreached[targetpop] = totalreached*targetcomposition[targetpop]
                if proportion: popreached[targetpop] /= poptargeted[targetpop]

            return popreached


    def getbudget(self, x, t, parset=None, results=None, proportion=False, toplot=False, bounds=None):
        '''Returns budget for a coverage vector'''

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(poptargeted.values())
        if not proportion: reqbudget = self.costcovfn.evaluate(x=x,popsize=totaltargeted,t=t,inverse=True,toplot=False,bounds=bounds)
        else: reqbudget = self.costcovfn.evaluate(x=x*totaltargeted,popsize=totaltargeted,t=t,inverse=True,toplot=False,bounds=bounds)
        return reqbudget


    def plotcoverage(self, t, parset=None, results=None, plotoptions=None, existingFigure=None,
        randseed=None, bounds=None, npts=100, maxupperlim=1e8):
        ''' Plot the cost-coverage curve for a single program'''

        if type(t) in [int,float]: t = [t]
        plotdata = {}
        
        # Get caption & scatter data 
        caption = plotoptions['caption'] if plotoptions and plotoptions.get('caption') else ''
        costdata = dcp(self.costcovdata['cost']) if self.costcovdata.get('cost') else []

        # Make x data... 
        if plotoptions and plotoptions.get('xupperlim') and ~isnan(plotoptions['xupperlim']):
            xupperlim = plotoptions['xupperlim']
        else: 
            if costdata: xupperlim = 1.5*max(costdata)
            else: xupperlim = maxupperlim
        xlinedata = linspace(0,xupperlim,npts)

        if plotoptions and plotoptions.get('perperson'):
            xlinedata = linspace(0,xupperlim*self.gettargetpopsize(t[-1],parset),npts)

        # Create x line data and y line data
        try:
            y_l = self.getcoverage(x=xlinedata, t=t, parset=parset, results=results, total=True, proportion=False,toplot=True, bounds='l')
            y_m = self.getcoverage(x=xlinedata, t=t, parset=parset, results=results, total=True, proportion=False,toplot=True, bounds=None)
            y_u = self.getcoverage(x=xlinedata, t=t, parset=parset, results=results, total=True, proportion=False,toplot=True, bounds='u')
        except:
            y_l,y_m,y_u = None,None,None
        plotdata['ylinedata_l'] = y_l
        plotdata['ylinedata_m'] = y_m
        plotdata['ylinedata_u'] = y_u
        plotdata['xlabel'] = 'USD'
        plotdata['ylabel'] = 'Number covered'

        # Flag to indicate whether we will adjust by population or not
        if plotoptions and plotoptions.get('perperson'):
            if costdata:
                for yrno, yr in enumerate(self.costcovdata['t']):
                    targetpopsize = self.gettargetpopsize(t=yr, parset=parset, results=results)
                    costdata[yrno] /= targetpopsize[0]
            if not (plotoptions and plotoptions.get('xupperlim') and ~isnan(plotoptions['xupperlim'])):
                if costdata: xupperlim = 1.5*max(costdata) 
                else: xupperlim = 1e3
            plotdata['xlinedata'] = linspace(0,xupperlim,npts)
        else:
            plotdata['xlinedata'] = xlinedata
            
        cost_coverage_figure = existingFigure if existingFigure else figure()
        cost_coverage_figure.hold(True)
        axis = cost_coverage_figure.gca()

        axis.set_position((0.1, 0.35, .8, .6)) # to make a bit of room for extra text
        figtext(.1, .05, textwrap.fill(caption))
        
        if y_m is not None:
            for yr in range(y_m.shape[0]):
                axis.plot(
                    plotdata['xlinedata'],
                    plotdata['ylinedata_m'][yr],
                    linestyle='-',
                    linewidth=2,
                    color='#a6cee3')
                axis.plot(
                    plotdata['xlinedata'],
                    plotdata['ylinedata_l'][yr],
                    linestyle='--',
                    linewidth=2,
                    color='#000000')
                axis.plot(
                    plotdata['xlinedata'],
                    plotdata['ylinedata_u'][yr],
                    linestyle='--',
                    linewidth=2,
                    color='#000000')
        axis.scatter(
            costdata,
            self.costcovdata['coverage'],
            color='#666666')
        

        axis.set_xlim([0, xupperlim])
        axis.set_ylim(bottom=0)
        axis.tick_params(axis='both', which='major', labelsize=11)
        axis.set_xlabel(plotdata['xlabel'], fontsize=11)
        axis.set_ylabel(plotdata['ylabel'], fontsize=11)
        axis.get_xaxis().set_major_locator(MaxNLocator(nbins=3))
        axis.set_title(self.short)
        axis.get_xaxis().get_major_formatter().set_scientific(False)
        axis.get_yaxis().get_major_formatter().set_scientific(False)

        return cost_coverage_figure


class CCOF(object):
    '''Cost-coverage, coverage-outcome and cost-outcome objects'''
    __metaclass__ = abc.ABCMeta

    def __init__(self,ccopars=None,interaction=None):
        self.ccopars = ccopars if ccopars else {}
        self.interaction = interaction

    def __repr__(self):
        ''' Print out useful info'''
        output = '\n'
        output += 'Programmatic parameters: %s\n'    % self.ccopars
        output += '            Interaction: %s\n'    % self.interaction
        output += '\n'
        return output

    def addccopar(self, ccopar, overwrite=False, verbose=2):
        ''' Add or replace parameters for cost-coverage functions'''

        # Fill in the missing information for cost-coverage curves
        if ccopar.get('unitcost'):
            if not ccopar.get('saturation'): ccopar['saturation'] = (1.,1.)

        if not self.ccopars:
            for ccopartype in ccopar.keys():
                self.ccopars[ccopartype] = [ccopar[ccopartype]]
        else:
            if (not self.ccopars['t']) or (ccopar['t'] not in self.ccopars['t']):
                for ccopartype in self.ccopars.keys():
                    if not ccopar.get(ccopartype): 
                        printv('WARNING: no parameter value supplied for "%s", setting to ZERO...' %(ccopartype), 1, verbose)
                        ccopar[ccopartype] = (0,0)
                    self.ccopars[ccopartype].append(ccopar[ccopartype])
                printv('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars), 4, verbose)
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = {}
                    for ccopartype in self.ccopars.keys():
                        oldccopar[ccopartype] = self.ccopars[ccopartype][ind]
                        self.ccopars[ccopartype][ind] = ccopar[ccopartype]
                    printv('\nModified CCO parameter from "%s" to "%s". \nCCO parameters for are: %s' % (oldccopar, ccopar, self.ccopars), 4, verbose)
                else:
                    errormsg = 'You have already entered CCO parameters for the year %s. If you want to overwrite it, set overwrite=True when calling addccopar().' % ccopar['t']
                    raise OptimaException(errormsg)
        return None

    def rmccopar(self, t, verbose=2):
        '''Remove cost-coverage-outcome data point. The point to be removed can be specified by year (int or float).'''
        if isinstance(t, (int,float)):
            if int(t) in self.ccopars['t']:
                ind = self.ccopars['t'].index(int(t))
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].pop(ind)
                printv('\nRemoved CCO parameters in year "%s". \nCCO parameters are: %s' % (t, self.ccopars), 4, verbose)
            else:
                errormsg = 'You have asked to remove CCO parameters for the year %s, but no data was added for that year. Available parameters are: %s' % (t, self.ccopars)
                raise OptimaException(errormsg)
        return None

    def getccopar(self, t, verbose=2, randseed=None, bounds=None):
        '''Get a cost-coverage-outcome parameter set for any year in range 1900-2100'''

        # Error checks
        if not self.ccopars:
            raise OptimaException('Need parameters for at least one year before function can be evaluated.')
        if randseed and bounds:
            raise OptimaException('Either select bounds or specify randseed')

        # Set up necessary variables
        ccopar = {}
        if isinstance(t,(float,int)): t = [t]
        nyrs = len(t)
        ccopars_no_t = dcp(self.ccopars)
        del ccopars_no_t['t']
        
        # Deal with bounds
        if not bounds:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    ccopars_no_t[parname][j] = (parvalue[j][0]+parvalue[j][1])/2
        elif bounds in ['upper','u','up','high','h']:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    if parname=='saturation': ccopars_no_t[parname][j] = parvalue[j][0]
                    else: ccopars_no_t[parname][j] = parvalue[j][1]
        elif bounds in ['lower','l','low']:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    if parname=='saturation': ccopars_no_t[parname][j] = parvalue[j][1]
                    else: ccopars_no_t[parname][j] = parvalue[j][0]
        else:
            raise OptimaException('Unrecognised bounds.')
            
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

        ccopar['t'] = t
        printv('\nCalculated CCO parameters in year(s) %s to be %s' % (t, ccopar), 4, verbose)
        return ccopar

    def evaluate(self, x, popsize, t, toplot, inverse=False, randseed=None, bounds=None):
        if (not toplot) and (not len(x)==len(t)): raise OptimaException('x needs to be the same length as t, we assume one spending amount per time point.')
        ccopar = self.getccopar(t=t,randseed=randseed,bounds=bounds)
        if not inverse: return self.function(x=x,ccopar=ccopar,popsize=popsize)
        else: return self.inversefunction(x=x,ccopar=ccopar,popsize=popsize)

    @abc.abstractmethod # This method must be defined by the derived class
    def emptypars(self):
        pass

    @abc.abstractmethod # This method must be defined by the derived class
    def function(self, x, ccopar, popsize):
        pass

    @abc.abstractmethod # This method must be defined by the derived class
    def inversefunction(self, x, ccopar, popsize):
        pass


######## SPECIFIC CCOF IMPLEMENTATIONS
class Costcov(CCOF):
    '''Cost-coverage objects'''

    def function(self, x, ccopar, popsize):
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

    def inversefunction(self, x, ccopar, popsize):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if isinstance(popsize, (float, int)): popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        if nyrs==npts: return -0.5*popsize*s*u*log(2*s/(x/popsize+s)-1)
        else: raise OptimaException('coverage vector should be the same length as params.')

    def emptypars(self):
        ccopars = {}
        ccopars['saturation'] = None
        ccopars['unitcost'] = None
        ccopars['t'] = None
        return ccopars

class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        pass

    def inversefunction(self, x, ccopar, popsize):
        pass

    def emptypars(self):
        ccopars = {}
        ccopars['intercept'] = None
        ccopars['t'] = None
        return ccopars

