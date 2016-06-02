"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2016feb06
"""

from optima import OptimaException, printv, uuid, today, sigfig, getdate, dcp, smoothinterp, findinds, odict, Settings, sanitize, objrepr, gridcolormap, isnumber, promotetoarray, vec2obj, runmodel
from numpy import ones, prod, array, zeros, exp, linspace, append, nan, isnan, maximum, minimum, sort, concatenate as cat, transpose
from random import uniform
import abc

# WARNING, this should not be hard-coded!!! Available from
# [par.coverage for par in P.parsets[0].pars[0].values() if hasattr(par,'coverage')]
# ...though would be nice to have an easier way!
coveragepars=['numtx','numpmtct','numost','numcirc'] 


class Programset(object):

    def __init__(self, name='default', programs=None, default_interaction='random'):
        ''' Initialize '''
        self.name = name
        self.uid = uuid()
        self.default_interaction = default_interaction
        self.programs = odict()
        if programs is not None: self.addprograms(programs)
        else: self.updateprogset()
        self.defaultbudget = odict()
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = objrepr(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += 'Targeted populations: %s\n'    % self.targetpops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                 UID: %s\n'    % self.uid
        output += '============================================================\n'
        
        return output

    def getsettings(self):
        ''' Try to get the freshest settings available '''
#        print('Warning, using default settings with program set "%s"' % self.name)
        settings = Settings() # WARNING KLUDGY should fix by having project an attribute of Programset
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
        if not hasattr(self, 'covout'): self.covout = odict()

        for targetpartype in self.targetpartypes: # Loop over parameter types
            if not self.covout.get(targetpartype): self.covout[targetpartype] = odict() # Initialize if it's not there already
            for thispop in self.progs_by_targetpar(targetpartype).keys(): # Loop over populations
                if self.covout[targetpartype].get(thispop): # Take the pre-existing one if it's there... 
                    ccopars = self.covout[targetpartype][thispop].ccopars 
                else: # ... or if not, set it up
                    ccopars = odict()
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
                    printv('\nAdded program "%s" to programset "%s". \nPrograms in this programset are: %s' % (newprogram.short, self.name, [thisprog.short for thisprog in self.programs.values()]), 3, verbose)
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

    def optimizableprograms(self):
        return odict((program.short, program) for program in self.programs.values() if program.optimizable())

    def hasbudget(self):
        return [True if prog.hasbudget() else False for prog in self.programs.values()]

    def programswithbudget(self):
        return odict((program.short, program) for program in self.programs.values() if program.hasbudget())

    def hasallcovoutpars(self, detail=False):
        ''' Checks whether all the **required** coverage-outcome parameters are there for coverage-outcome rships'''
        result = True
        details = []
        for thispartype in self.covout.keys():
            for thispop in self.covout[thispartype].keys():
                if not self.covout[thispartype][thispop].ccopars['intercept']:
                    result = False
                    details.append((thispartype,thispop))
                if thispartype not in coveragepars:
                    for thisprog in self.progs_by_targetpar(thispartype)[thispop]: 
                        if not self.covout[thispartype][thispop].ccopars[thisprog.short]:
                            result = False
                            details.append((thispartype,thispop))
        if detail: return list(set(details))
        else: return result

    def hasallcostcovpars(self, detail=False):
        ''' Checks whether all the **required** cost-coverage parameters are there for coverage-outcome rships'''
        result = True
        details = []
        for prog in self.optimizableprograms().values():
            if not prog.costcovfn.ccopars.get('unitcost'):
                details.append(prog.name)
                result = False
        if detail: return list(set(details))
        else: return result
                
    def readytooptimize(self):
        ''' True if the progset is ready to optimize (i.e. has all required pars) and False otherwise''' 
        return (self.hasallcostcovpars() and self.hasallcovoutpars())        

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


    def getdefaultbudget(self, t=None, verbose=2):
        ''' Extract the budget if cost data has been provided'''
        
        # Initialise outputs
        totalbudget, lastbudget, selectbudget = odict(), odict(), odict()

        # Validate inputs
        if t is not None: t = promotetoarray(t)

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
            if t is not None:
                for yr in t:
                    yrindex = findinds(tvec,yr)
                    selectbudget[program].append(totalbudget[program][yrindex][0])
                    
        # TEMP: store default budget as an attribute
        self.defaultbudget = lastbudget
        return selectbudget if t is not None else lastbudget

    def getdefaultcoverage(self, t=None, parset=None, results=None, verbose=2, sample='best'):
        ''' Extract the coverage levels corresponding to the default budget'''
        defaultbudget = self.getdefaultbudget()
        defaultcoverage = self.getprogcoverage(budget=defaultbudget, t=t, parset=parset, results=results, sample=sample)
        for progno in range(len(defaultcoverage)):
            defaultcoverage[progno] = defaultcoverage[progno][0] if defaultcoverage[progno] else nan    
        return defaultcoverage

    def getprogcoverage(self, budget, t, parset=None, results=None, proportion=False, sample='best', verbose=2):
        '''Budget is currently assumed to be a DICTIONARY OF ARRAYS'''

        # Initialise output
        coverage = odict()

        # Validate inputs
        if isnumber(t): t = [t]
        if isinstance(budget, list) or isinstance(budget,type(array([]))):
            budget = vec2obj(orig=self.getdefaultbudget(), newvec=budget) # It seems to be a vector: convert to odict
        if type(budget)==dict: budget = odict(budget) # Convert to odict
        budget = budget.sort([p.short for p in self.programs.values()])

        # Get program-level coverage for each program
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    coverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    coverage[thisprog] = self.programs[thisprog].getcoverage(x=spending, t=t, parset=parset, results=results, proportion=proportion, sample=sample)
            else: coverage[thisprog] = None

        return coverage


    def getprogbudget(self, coverage, t, parset=None, results=None, proportion=False, sample='best', verbose=2):
        '''Return budget associated with specified coverage levels'''

        # Initialise output
        budget = odict()

        # Validate inputs
        if isnumber(t): t = [t]
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
                    budget[thisprog] = self.programs[thisprog].getbudget(x=cov, t=t, parset=parset, results=results, proportion=proportion, sample=sample)
            else: budget[thisprog] = None

        return budget


    def getpopcoverage(self, budget, t, parset=None, results=None, sample='best', verbose=2):
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
                    popcoverage[thisprog] = self.programs[thisprog].getcoverage(x=spending, t=t, parset=parset, results=results, total=False, sample=sample)
            else: popcoverage[thisprog] = None

        return popcoverage


    def getoutcomes(self, coverage=None, t=None, parset=None, results=None, sample='best', coveragepars=coveragepars):
        ''' Get the model parameters corresponding to dictionary of coverage values'''

        # Initialise output
        outcomes = odict()

        # Validate inputs
        if isnumber(t): t = [t]
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')
        if coverage is None:
            coverage = self.getdefaultcoverage(t=t, parset=parset, results=results, sample=sample)
        for covkey, coventry in coverage.iteritems(): # Ensure coverage level values are lists
            if isnumber(coventry): coverage[covkey] = [coventry]

        # Set up internal variables
        nyrs = len(t)
        infbudget = odict((k,array([1e9]*len(coverage[k]))) if self.programs[k].optimizable() else (k,None) for k in coverage.keys())

        # Loop over parameter types
        for thispartype in self.targetpartypes:
            outcomes[thispartype] = odict()
            
            # Loop over populations relevant for this parameter type
            for popno, thispop in enumerate(self.progs_by_targetpar(thispartype).keys()):

                # If it's a coverage parameter, you are done
                if thispartype in coveragepars:
                    outcomes[thispartype][thispop] = array(self.covout[thispartype][thispop].getccopar(t=t, sample=sample)['intercept'])
                    for thisprog in self.progs_by_targetpar(thispartype)[thispop]: # Loop over the programs that target this parameter/population combo
                        if thispop == 'tot':
                            popcoverage = coverage[thisprog.short]
                        else: popcoverage = coverage[thisprog.short]*thisprog.gettargetcomposition(t=t, parset=parset, results=results)[thispop]
                        outcomes[thispartype][thispop] += popcoverage

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
                            outcomes[thispartype][thispop] = self.covout[thispartype][thispop].getccopar(t=t, sample=sample)['intercept']
                            fullx = infbudget[thisprog.short]
                            if thiscovpop:
                                part1 = coverage[thisprog.short]*thisprog.gettargetcomposition(t=t, parset=parset, results=results)[thiscovpop]
                                part2 = thisprog.getcoverage(x=fullx, t=t, parset=parset, results=results, proportion=False,total=False)[thiscovpop]
                                thiscov[thisprog.short] = part1/part2
                            else:
                                part1 = coverage[thisprog.short]*thisprog.gettargetcomposition(t=t, parset=parset, results=results)[thispop]
                                part2 = thisprog.getcoverage(x=fullx,t=t, parset=parset, results=results, proportion=False,total=False)[thispop]
                                thiscov[thisprog.short] = part1/part2
                            delta[thisprog.short] = [self.covout[thispartype][thispop].getccopar(t=t, sample=sample)[thisprog.short][j] - outcomes[thispartype][thispop][j] for j in range(nyrs)]
                            
                    # ADDITIVE CALCULATION
                    # NB, if there's only one program targeting this parameter, just do simple additive calc
                    if self.covout[thispartype][thispop].interaction == 'additive' or len(self.progs_by_targetpar(thispartype)[thispop])==1:
                        # Outcome += c1*delta_out1 + c2*delta_out2
                        for thisprog in self.progs_by_targetpar(thispartype)[thispop]:
                            if not self.covout[thispartype][thispop].ccopars[thisprog.short]:
                                print('WARNING: no coverage-outcome parameters defined for program  "%s", population "%s" and parameter "%s". Skipping over... ' % (thisprog.short, thispop, thispartype))
                                outcomes[thispartype][thispop] = None
                            else: outcomes[thispartype][thispop] += thiscov[thisprog.short]*delta[thisprog.short]
                            
                    # NESTED CALCULATION
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
                
                    # RANDOM CALCULATION
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
                                    outcomes[thispartype][thispop] += overlap_calc([j],i)[0]

                            # All programs together
                            outcomes[thispartype][thispop] += prod(array(thiscov.values()),0)*[max([c[j] for c in delta.values()]) for j in range(nyrs)]
                    
                    else: raise OptimaException('Unknown reachability type "%s"',self.covout[thispartype][thispop].interaction)
        
        # Validate
        for outcome in outcomes.keys():
            for key in outcomes[outcome].keys():
                if outcomes[outcome][key] is not None and len(outcomes[outcome][key])!=nyrs:
                    raise OptimaException('Parameter lengths must match (len(outcome)=%i, nyrs=%i)' % (len(outcomes[outcome][key]), nyrs))

        return outcomes
        
        
        
    def getpars(self, coverage, t=None, parset=None, results=None, ind=0, sample='best', die=False, verbose=2):
        ''' Make pars'''
        
        years = t # WARNING, not renaming in the function definition for now so as to not break things
        
        settings = self.getsettings() # WARNING TEMP shouldn't need this!!!
        
        # Validate inputs
        if years is None: raise OptimaException('To get pars, one must supply years')
        if isnumber(years): years = [years]
        settings = None
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')
        
        # Get settings from somewhere
        try: settings = parset.project.settings
        except:
            printv('Warning, could not extract settings, using defaults', 1, verbose)
            settings = Settings()

        # Get outcome dictionary
        outcomes = self.getoutcomes(coverage=coverage, t=years, parset=parset, results=results, sample=sample)

        # Create a parset and copy over parameter changes
        pars = dcp(parset.pars[ind])
        for outcome in outcomes.keys():
            thispar = pars[outcome]
            
            # Find last good value -- WARNING, copied from scenarios.py!!! and shouldn't be in this loop!
            last_t = min(years) - settings.dt # Last timestep before the scenario starts
            last_y = thispar.interp(tvec=last_t, dt=settings.dt, asarray=False, usemeta=False) # Find what the model would get for this value
            
            for pop in outcomes[outcome].keys(): # WARNING, 'pop' should be renamed 'key' or something for e.g. partnerships
                
                # Validate outcome
                thisoutcome = outcomes[outcome][pop] # Shorten
                lower = float(thispar.limits[0]) # Lower limit, cast to float just to be sure (is probably int)
                upper = settings.convertlimits(limits=thispar.limits[1]) # Upper limit -- have to convert from string to float based on settings for this project
                if thisoutcome is not None:
                    if any(array(thisoutcome<lower).flatten()) or any(array(thisoutcome>upper).flatten()):
                        errormsg = 'Parameter value "%s" for population "%s" based on coverage is outside allowed limits: value=%s (%f, %f)' % (thispar.name, pop, thisoutcome, lower, upper)
                        if die:
                            raise OptimaException(errormsg)
                        else:
                            printv(errormsg, 3, verbose) # WARNING, not sure how serious this is...feels like it shouldn't happen
                            thisoutcome = maximum(thisoutcome, lower) # Impose lower limit
                            thisoutcome = minimum(thisoutcome, upper) # Impose upper limit
                
                    # Remove years after the last good year
                    if last_t < max(thispar.t[pop]):
                        thispar.t[pop] = thispar.t[pop][findinds(thispar.t[pop] <= last_t)]
                        thispar.y[pop] = thispar.y[pop][findinds(thispar.t[pop] <= last_t)]
                    
                    # Append the last good year, and then the new years
                    thispar.t[pop] = append(thispar.t[pop], last_t)
                    thispar.y[pop] = append(thispar.y[pop], last_y[pop]) 
                    thispar.t[pop] = append(thispar.t[pop], years)
                    thispar.y[pop] = append(thispar.y[pop], thisoutcome) 
                
                if len(thispar.t[pop])!=len(thispar.y[pop]):
                    raise OptimaException('Parameter lengths must match (t=%i, y=%i)' % (len(thispar.t[pop]), len(thispar.y[pop])))

            pars[outcome] = thispar # WARNING, probably not needed
                

        return pars
    
    
    
    def compareoutcomes(self, parset=None, year=None, ind=0, doprint=False):
        ''' For every parameter affected by a program, return a list comparing the default parameter values with the budget ones '''
        outcomes = self.getoutcomes(t=year, parset=parset)
        comparison = list()
        maxnamelen = 0
        maxkeylen = 0
        for key1 in outcomes.keys():
            for key2 in outcomes[key1].keys():
                name = parset.pars[ind][key1].name
                maxnamelen = max(len(name),maxnamelen)
                maxkeylen = max(len(str(key2)),maxkeylen)
                parvalue = parset.pars[ind][key1].interp(tvec=year, asarray=False)[key2]
                budgetvalue = outcomes[key1][key2] 
                if budgetvalue is not None: comparison.append([name, key2, parvalue[0], budgetvalue[0]])
                else: comparison.append([name, key2, parvalue[0], None])
        
        if doprint:
            for item in comparison:
                strctrl = '%%%is | %%%is | Par: %%8s | Budget: %%8s' % (maxnamelen, maxkeylen)
                print(strctrl % (item[0], item[1], sigfig(item[2]), sigfig(item[3])))
                
        return comparison
    
    
    
    def reconcilewithpars(self, parset=None, year=None, ind=0):
        ''' A method for automatically reconciling coverage-outcome parameters with model parameters '''
        
        def objectivecalc(progset=None, parset=None, year=None, ind=None, method='mape', eps=1e-3):
            ''' Calculate the mismatch between the budget-derived parameter values and the model parameter values for a given year '''
            comparison = progset.compareoutcomes(parset=parset, year=year, ind=ind)
            allmismatches = []
            mismatch = 0
            for budgetparpair in comparison:
                parval = budgetparpair[2]
                budgetval = budgetparpair[3]
                if   method in ['wape','mape']: thismismatch = abs(budgetval - parval) / (parval+eps)
                elif method=='mad':             thismismatch = abs(budgetval - parval)
                elif method=='mse':             thismismatch =    (budgetval - parval)**2
                else:
                    errormsg = 'autofit(): "method" not known; you entered "%s", but must be one of:\n' % method
                    errormsg += '"wape" = weighted absolute percentage error (default)\n'
                    errormsg += '"mape" = mean absolute percentage error\n'
                    errormsg += '"mad"  = mean absolute difference\n'
                    errormsg += '"mse"  = mean squared error'
                    raise OptimaException(errormsg)
                allmismatches.append(thismismatch)
                mismatch += thismismatch
            return mismatch
        
        ## Do the actual calibration thingo
        def cco2vec(): raise Exception('Not implemented')
        
        def vec2cco(): raise Exception('Not implemented')
        
        raise Exception('Not implemented')
        
        return None



    def plotallcoverage(self,t,parset,existingFigure=None,verbose=2,bounds=None):
        ''' Plot the cost-coverage curve for all programs'''

        cost_coverage_figures = odict()
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program', 1, verbose)
                else:
                    cost_coverage_figures[thisprog] = self.programs[thisprog].plotcoverage(t=t,parset=parset,existingFigure=existingFigure,bounds=bounds)

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

    def hasbudget(self):
        return True if self.costcovdata['cost'] else False

    def addtargetpar(self, targetpar, verbose=2):
        '''Add a model parameter to be targeted by this program'''
        if (targetpar['param'],targetpar['pop']) not in [(tp['param'],tp['pop']) for tp in self.targetpars]:
            self.targetpars.append(targetpar)
            printv('\nAdded target parameter "%s" to the list of target parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.short, self.targetpars), 4, verbose)
        else:
            index = [(tp['param'],tp['pop']) for tp in self.targetpars].index((targetpar['param'],targetpar['pop']))
            self.targetpars[index] = targetpar # overwrite
        return None


    def rmtargetpar(self, targetpar, verbose=2):
        '''Remove a model parameter from those targeted by this program'''
        if (targetpar['param'],targetpar['pop']) not in [(tp['param'],tp['pop']) for tp in self.targetpars]:
            errormsg = 'The target parameter "%s" you have selected for removal is not in the list of target parameters affected by this program:%s.' % (targetpar, self.targetpars)
            raise OptimaException(errormsg)
        else:
            index = [(tp['param'],tp['pop']) for tp in self.targetpars].index((targetpar['param'],targetpar['pop']))
            self.targetpars.pop(index)
            printv('\nRemoved model parameter "%s" from the list of model parameters affected by "%s". \nAffected parameters are: %s' % (targetpar, self.short, self.targetpars), 4, verbose)
        return None


    def addcostcovdatum(self, costcovdatum, overwrite=False, verbose=2):
        '''Add cost-coverage data point'''
        if costcovdatum['t'] not in self.costcovdata['t']:
            self.costcovdata['t'].append(costcovdatum['t'])
            self.costcovdata['cost'].append(costcovdatum['cost'])
            if costcovdatum.get('coverage'):
                self.costcovdata['coverage'].append(costcovdatum['coverage'])
            else:
                self.costcovdata['coverage'].append(None)

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


    def gettargetpopsize(self, t, parset=None, results=None, ind=0, total=True, useelig=False):
        '''Returns target population size in a given year for a given spending amount.'''

        # Validate inputs
        if isnumber(t): t = array([t])
        elif type(t)==list: t = array(t)
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')

        # Initialise outputs
        popsizes = odict()
        targetpopsize = odict()
        
        # If we are ignoring eligibility, just sum the popsizes...
        if not useelig:
            initpopsizes = parset.pars[ind]['popsize'].interp(tvec=t)

        # ... otherwise, have to get the PLHIV pops from results. WARNING, this should be improved.
        else: 

            # Do everything possible to get settings
            try: settings = parset.project.settings
            except: 
                try: settings = results.project.settings
                except:
                    print('Warning, could not find settings for program "%s", using default' % self.name)
                    settings = Settings()
            
            npops = len(parset.pars[ind]['popkeys'])
    
            if not self.criteria['pregnant']:
                if self.criteria['hivstatus']=='allstates':
                    initpopsizes = parset.pars[ind]['popsize'].interp(tvec=t)
        
                else: # If it's a program for HIV+ people, need to find the number of positives
                    if not results: 
                        try: results = parset.getresults(die=True)
                        except OptimaException as E: 
                            print('Failed to extract results because "%s", rerunning the model...' % E.message)
                            results = runmodel(pars=parset.pars[ind], settings=settings)
                            parset.resultsref = results.name # So it doesn't have to be rerun
                    
                    cd4index = sort(cat([settings.__dict__[state] for state in self.criteria['hivstatus']])) # CK: this should be pre-computed and stored if it's useful
                    initpopsizes = zeros((npops,len(t))) 
                    for yrno,yr in enumerate(t):
                        initpopsizes[:,yrno] = results.raw[ind]['people'][cd4index,:,findinds(results.tvec,yr)].sum(axis=0)
                    
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
                            parset.resultsref = results.name # So it doesn't have to be rerun
                    for yr in t:
                        initpopsizes = parset.pars[ind]['popsize'].interp(tvec=[yr])*parset.pars[ind]['birth'].interp(tvec=[yr])*transpose(results.main['prev'].pops[0,:,findinds(results.tvec,yr)])

        for popno, pop in enumerate(parset.pars[ind]['popkeys']):
            popsizes[pop] = initpopsizes[popno,:]
        for targetpop in self.targetpops:
            if targetpop.lower() in ['total','tot','all']:
                targetpopsize[targetpop] = sum(popsizes.values())
            else:
                targetpopsize[targetpop] = popsizes[targetpop]
                
        finalpopsize = array([sum(targetpopsize.values())]) if isnumber(sum(targetpopsize.values())) else sum(targetpopsize.values())
                    
        if total: return finalpopsize
        else: return targetpopsize


    def gettargetcomposition(self, t, parset=None, results=None, total=True):
        '''Tells you the proportion of the total population targeted by a program that is comprised of members from each sub-population group.'''
        targetcomposition = odict()

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(poptargeted.values())

        for targetpop in self.targetpops:
            targetcomposition[targetpop] = poptargeted[targetpop]/totaltargeted
        return targetcomposition


    def getcoverage(self, x, t, parset=None, results=None, total=True, proportion=False, toplot=False, sample='best'):
        '''Returns coverage for a time/spending vector'''

        # Validate inputs
        x = promotetoarray(x)
        t = promotetoarray(t)

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)

        totaltargeted = sum(poptargeted.values())
        totalreached = self.costcovfn.evaluate(x=x, popsize=totaltargeted, t=t, toplot=toplot, sample=sample)

        if total: return totalreached/totaltargeted if proportion else totalreached
        else:
            popreached = odict()
            targetcomposition = self.targetcomposition if self.targetcomposition else self.gettargetcomposition(t=t,parset=parset) 
            for targetpop in self.targetpops:
                popreached[targetpop] = totalreached*targetcomposition[targetpop]
                if proportion: popreached[targetpop] /= poptargeted[targetpop]

            return popreached


    def getbudget(self, x, t, parset=None, results=None, proportion=False, toplot=False, sample='best'):
        '''Returns budget for a coverage vector'''

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(poptargeted.values())
        if not proportion: reqbudget = self.costcovfn.evaluate(x=x,popsize=totaltargeted,t=t,inverse=True,toplot=False,sample=sample)
        else: reqbudget = self.costcovfn.evaluate(x=x*totaltargeted,popsize=totaltargeted,t=t,inverse=True,toplot=False,sample=sample)
        return reqbudget


    def plotcoverage(self, t, parset=None, results=None, plotoptions=None, existingFigure=None,
        plotbounds=True, npts=100, maxupperlim=1e8, doplot=False):
        ''' Plot the cost-coverage curve for a single program'''
        
        # Put plotting imports here so fails at the last possible moment
        from pylab import figure, figtext, isinteractive, ioff, ion, close, show
        from matplotlib.ticker import MaxNLocator
        import textwrap
        
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures

        t = promotetoarray(t)
        colors = gridcolormap(len(t))
        plotdata = odict()
        
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
            y_l = self.getcoverage(x=xlinedata, t=t, parset=parset, results=results, total=True, proportion=False, toplot=True, sample='l')
            y_m = self.getcoverage(x=xlinedata, t=t, parset=parset, results=results, total=True, proportion=False, toplot=True, sample='best')
            y_u = self.getcoverage(x=xlinedata, t=t, parset=parset, results=results, total=True, proportion=False, toplot=True, sample='u')
        except:
            y_l,y_m,y_u = None,None,None
        plotdata['ylinedata_l'] = y_l
        plotdata['ylinedata_m'] = y_m
        plotdata['ylinedata_u'] = y_u
        plotdata['xlabel'] = 'Spending'
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
                    color=colors[yr],
                    label=t[yr])
                if plotbounds:
                    axis.fill_between(plotdata['xlinedata'],
                                      plotdata['ylinedata_l'][yr],
                                      plotdata['ylinedata_u'][yr],
                                      facecolor=colors[yr],
                                      alpha=.1,
                                      lw=0)
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
        if len(t)>1: axis.legend(loc=4)
        
        # Tidy up
        if not doplot: close(cost_coverage_figure)
        if wasinteractive: ion()
        if doplot: show()

        return cost_coverage_figure

########################################################
# COST COVERAGE OUTCOME FUNCTIONS
########################################################
class CCOF(object):
    '''Cost-coverage, coverage-outcome and cost-outcome objects'''
    __metaclass__ = abc.ABCMeta # WARNING, this is the only place where this is used...is it necessary...?

    def __init__(self,ccopars=None,interaction=None):
        self.ccopars = ccopars if ccopars else odict()
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
                    if ccopar.get(ccopartype):  # WARNING: need to check this more appropriately
                        self.ccopars[ccopartype].append(ccopar[ccopartype])
                printv('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars), 4, verbose)
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = odict()
                    for ccopartype in ccopar.keys():
                        if self.ccopars[ccopartype]:
                            oldccopar[ccopartype] = self.ccopars[ccopartype][ind]
                            self.ccopars[ccopartype][ind] = ccopar[ccopartype]
                    printv('\nModified CCO parameter from "%s" to "%s". \nCCO parameters for are: %s' % (oldccopar, ccopar, self.ccopars), 4, verbose)
                else:
                    errormsg = 'You have already entered CCO parameters for the year %s. If you want to overwrite it, set overwrite=True when calling addccopar().' % ccopar['t']
                    raise OptimaException(errormsg)
        return None

    def rmccopar(self, t, verbose=2):
        '''Remove cost-coverage-outcome data point. The point to be removed can be specified by year (int or float).'''
        if isnumber(t):
            if int(t) in self.ccopars['t']:
                ind = self.ccopars['t'].index(int(t))
                for ccopartype in self.ccopars.keys():
                    self.ccopars[ccopartype].pop(ind)
                printv('\nRemoved CCO parameters in year "%s". \nCCO parameters are: %s' % (t, self.ccopars), 4, verbose)
            else:
                errormsg = 'You have asked to remove CCO parameters for the year %s, but no data was added for that year. Available parameters are: %s' % (t, self.ccopars)
                raise OptimaException(errormsg)
        return None

    def getccopar(self, t, verbose=2, sample='best'):
        '''
        Get a cost-coverage-outcome parameter set for any year in range 1900-2100

        Args:
            t: years to interpolate sets of ccopar
            verbose: level of verbosity
            bounds: None - take middle of intervals,
                    'upper' - take top of intervals,
                    'lower' - take bottom if intervals
            randseed: takes a 
        '''

        # Error checks
        if not self.ccopars:
            raise OptimaException('Need parameters for at least one year before function can be evaluated.')

        # Set up necessary variables
        ccopar = odict()
        t = promotetoarray(t)
        nyrs = len(t)
        ccopars_no_t = dcp(odict({k:v for k,v in self.ccopars.iteritems() if v}))
        del ccopars_no_t['t']
        
        # Get the appropriate sample type
        if sample in ['median', 'm', 'best', 'b', 'average', 'av', 'single']:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    ccopars_no_t[parname][j] = (parvalue[j][0]+parvalue[j][1])/2
        elif sample in ['upper','u','up','high','h']:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    ccopars_no_t[parname][j] = parvalue[j][0]
        elif sample in ['lower','l','low']:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    ccopars_no_t[parname][j] = parvalue[j][1]
        elif sample in ['random','rand','r']:
            for parname, parvalue in ccopars_no_t.iteritems():
                for j in range(len(parvalue)):
                    ccopars_no_t[parname][j] = uniform(parvalue[j][0],parvalue[j][1])
        else:
            raise OptimaException('Unrecognised bounds.')
            
        ccopartuples = sorted(zip(self.ccopars['t'], *ccopars_no_t.values()))
        knownt = array([ccopartuple[0] for ccopartuple in ccopartuples])
        j = 1

        # Calculate interpolated parameters
        for param in ccopars_no_t.keys():
            knownparam = array([ccopartuple[j] for ccopartuple in ccopartuples])
            allparams = smoothinterp(t, knownt, knownparam, smoothness=1)
            ccopar[param] = zeros(nyrs)
            for yr in range(nyrs):
                ccopar[param][yr] = allparams[yr]
            if isinstance(t,list): ccopar[param] = ccopar[param].tolist()
            j += 1

        ccopar['t'] = t
        printv('\nCalculated CCO parameters in year(s) %s to be %s' % (t, ccopar), 4, verbose)
        return ccopar

    def evaluate(self, x, popsize, t, toplot, inverse=False, sample='best', verbose=2):
        x = promotetoarray(x)
        t = promotetoarray(t)
        if (not toplot) and (not len(x)==len(t)):
            try: 
                x = x[0:1]
                t = t[0:1]
            except:
                x = array([0]) # WARNING, this should maybe not be here, or should be handled with kwargs
                t = array([2015])
            printv('x needs to be the same length as t, we assume one spending amount per time point.', 1, verbose)
        ccopar = self.getccopar(t=t,sample=sample)
        if not inverse: return self.function(x=x,ccopar=ccopar,popsize=popsize)
        else: return self.inversefunction(x=x,ccopar=ccopar,popsize=popsize)

    @abc.abstractmethod # This method must be defined by the derived class
    def function(self, x, ccopar, popsize):
        pass

    @abc.abstractmethod # This method must be defined by the derived class
    def inversefunction(self, x, ccopar, popsize):
        pass


########################################################
# COST COVERAGE FUNCTIONS
########################################################
class Costcov(CCOF):
    '''
    Cost-coverage object - used to calculate the coverage for a certain
    budget in a program. Best initialized with empty parameters,
    and later, add cost-coverage parameters with self.addccopar.

    Methods:

        addccopar(ccopar, overwrite=False, verbose=2)
            Adds a set of cost-coverage parameters for a budget year

            Args:
                ccopar: {
                            't': [2015,2016],
                            'saturation': [.90,1.],
                            'unitcost': [40,30]
                        }
                        The intervals in ccopar allow a randomization
                        to explore uncertainties in the model.

                overwrite: whether it should be added or replaced for
                           interpolation

        getccopar(t, verbose=2, sample='best')
            Returns an odict of cost-coverage parameters
                { 'saturation': [..], 'unitcost': [...], 't':[...] }
            used for self.evaulate.

            Args:
                t: a number/list of years to interpolate the ccopar
                randseed: used to randomly generate a varying set of parameters
                          to help determine the sensitivity/uncertainty of
                          certain parameters

        evaluate(x, popsize, t, toplot, inverse=False, randseed=None, bounds=None, verbose=2)
            Returns coverage if x=cost, or cost if x=coverage, this is defined by inverse.

            Args
                x: number, or list of numbers, representing cost or coverage
                t: years for each value of cost/coverage
                inverse: False - returns a coverage, True - returns a cost
                randseed: allows a randomization of the cost-cov parameters within
                    the given intervals

    '''

    def function(self, x, ccopar, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if eps is None: eps = Settings().eps # Warning, use project-nonspecific eps
        if isnumber(popsize): popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: return maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
        else:
            y = zeros((nyrs,npts))
            for yr in range(nyrs):
                y[yr,:] = maximum((2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr],eps)
            return y

    def inversefunction(self, x, ccopar, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if eps is None: eps = Settings().eps # Warning, use project-nonspecific eps
        if isnumber(popsize): popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: return maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
        else: raise OptimaException('coverage vector should be the same length as params.')


########################################################
# COVERAGE OUTCOME FUNCTIONS
########################################################
class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        pass

    def inversefunction(self, x, ccopar, popsize):
        pass

