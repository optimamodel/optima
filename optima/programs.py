"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2019jan09
"""

from optima import OptimaException, Link, printv, uuid, today, sigfig, getdate, dcp, promotetolist, smoothinterp, findinds, odict, Settings, sanitize, defaultrepr, isnumber, promotetoarray, vec2obj, asd, convertlimits, Timepar, Yearpar, checkifparsoverridepars, createwarningforoverride, standard_dcp, standard_cp, odict_custom
from numpy import ones, prod, array, zeros, exp, log, append, nan, isnan, maximum, minimum, sort, concatenate as cat, transpose, mean, argsort
from random import uniform
import six
if six.PY3:
	basestring = str
	unicode = str

__all__ = [
    'Program',
    'Programset',
    'checkifparsetoverridesprogset'
]

class Programset(object):

    def __init__(self, name='default', programs=None, default_interaction='additive', project=None):
        ''' Initialize '''
        self.name = name
        self.uid = uuid()
        self.default_interaction = default_interaction
        self.programs = odict_custom(func=self.checkpropagateversion)
        self.projectref = Link(project) # Store pointer for the project, if available
        self.projectversion = project.version if hasattr(project, 'version') else None
        if programs is not None: self.addprograms(programs)
        else: self.updateprogset()
        self.defaultbudget = odict()
        self.created = today()
        self.modified = today()

    def __repr__(self):
        ''' Print out useful information'''
        output = defaultrepr(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % [prog for prog in self.programs]
        output += 'Targeted populations: %s\n'    % self.targetpops
        output += '        Date created: %s\n'    % getdate(self.created)
        output += '       Date modified: %s\n'    % getdate(self.modified)
        output += '                 UID: %s\n'    % self.uid
        output += '============================================================\n'
        
        return output

    def __copy__(self):
        print('WARNING: copying a Programset will make it so that the programs[:].projectversion will get updated by this new progset, not the old one which they are still included in. '
              'It is recommended to deepcopy the progset instead.')
        copy = standard_cp(self)
        if isinstance(copy.programs, odict_custom): copy.programs.func = copy.checkpropagateversion
        return copy

    def __deepcopy__(self, memodict={}):
        copy = standard_dcp(self, memodict)
        if isinstance(copy.programs, odict_custom): copy.programs.func = copy.checkpropagateversion
        return copy

    def __setattr__(self, name, value):
        if name == 'programs':
            if not isinstance(value, odict_custom):
                value = odict_custom(value, func=self.checkpropagateversion)
            value.func = self.checkpropagateversion

        super(Programset, self).__setattr__(name, value)

        if name == 'programs': # If we are adding programs, make sure they match the projectversion of the parset
            self.checkpropagateversion(None, None, self.programs.values())
        if name == 'projectversion' and hasattr(self, 'programs') and self.programs is not None:
            self.propagateversion(None, None, self.programs.values())

    def propagateversion(self, odict, keys, values, die=True):
        ''' Dies because it should be able to add .projectversion to a Program'''
        values = promotetolist(values)
        for val in values:
            try: val.projectversion = self.projectversion
            except: # try to add projectversion but don't stress if it doesn't work
                if die: raise

    def checkversion(self, odict, keys, values):
        if self.projectversion is None:
            return
        values = promotetolist(values)
        for val in values:
            if not hasattr(val, 'projectversion'):
                raise OptimaException(f'Cannot add {type(val)} "{val.name}" to Programset "{self.name}" because it is '
                                      f'missing a projectversion so it might not be compatible with Programset.projectversion={self.projectversion}')
            if self.projectversion is not None and val.projectversion is not None and val.projectversion != self.projectversion:
                raise OptimaException(f'Cannot add {type(val)} "{val.name}" to Programset "{self.name}" because it has '
                                      f'a different projectversion={val.projectversion} than the Programset.projectversion={self.projectversion}')

    def checkpropagateversion(self, odict, keys, values):
        values = promotetolist(values)

        if hasattr(self, 'projectversion') and self.projectversion is not None:
            self.checkversion(odict, keys, values)
            self.propagateversion(odict, keys, values)

    def getsettings(self, project=None, parset=None, results=None):
        ''' Try to get the freshest settings available '''

        try: settings = project.settings
        except:
            try: settings = self.projectref().settings
            except:
                try: settings = parset.projectref().settings
                except:
                    try: settings = results.projectref().settings
                    except: settings = Settings()
        
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
        progdefaultpars = self.projectref().parset().getprogdefaultpars() # Get list of parameters that have default values under zero program coverage

        for targetpartype in self.targetpartypes: # Loop over parameter types
            if not self.covout.get(targetpartype): self.covout[targetpartype] = odict() # Initialize if it's not there already HERE could be linked
            for thispop in self.progs_by_targetpar(targetpartype).keys(): # Loop over populations
                if self.covout[targetpartype].get(thispop): # Take the pre-existing one if it's there... 
                    ccopars = self.covout[targetpartype][thispop].ccopars 
                    interaction = self.covout[targetpartype][thispop].interaction 
                else: # ... or if not, set it up
                    ccopars = odict()
                    ccopars['intercept'] = []
                    ccopars['t'] = []
                    if targetpartype in progdefaultpars:  # It has a default intercept value
                        defaultintercept = self.projectref().pars()[targetpartype].progdefault
                        ccopars['intercept'].append((defaultintercept,defaultintercept)) # Append default intercepts
                        ccopars['t'].append(2020) # Append a year
                    interaction = self.default_interaction
                targetingprogs = [thisprog.short for thisprog in self.progs_by_targetpar(targetpartype)[thispop]]
                for tp in targetingprogs:
                    if not ccopars.get(tp): ccopars[tp] = []
                                    
                # Delete any stored programs that are no longer needed (if removing a program)
                progccopars = dcp(ccopars)
                progccopars.pop('t', None)
                progccopars.pop('intercept', None)
                for prog in progccopars.keys(): 
                    if prog not in targetingprogs:
                        ccopars.pop(prog, None)

                self.covout[targetpartype][thispop] = Covout(ccopars=ccopars,interaction=interaction)

        # Delete any stored effects that aren't needed (if removing a program)
        for tpt in self.covout.keys():
            if tpt not in self.targetpartypes: self.covout.pop(tpt, None)
            else: 
                for tp in self.covout[tpt].keys():
                    if type(tp) in [tuple,str,unicode] and tp not in self.progs_by_targetpar(tpt).keys(): self.covout[tpt].pop(tp, None)

    def updateprogset(self, verbose=2):
        ''' Update (run this is you change something... )'''
        if self.programs is not None and not isinstance(self.programs, odict_custom):
            self.programs = odict_custom(self.programs, func=self.checkpropagateversion)
        self.gettargetpars()
        self.gettargetpartypes()
        self.gettargetpops()
        self.initialize_covout()
        printv('Updated program set "%s"' % (self.name), 4, verbose)
        return None

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

    def reorderprograms(self,desiredorder,verbose=2):
        ''' Reorder the odict of programs. Expects desiredorder to be a list of Program or list of str'''
        if not (len(desiredorder) == len(self.programs)):
            raise OptimaException(f'You have asked to reorder the programs {[thisprog for thisprog in self.programs]} of programset {self.name} into order {desiredorder}, but the desired order only has {len(desiredorder)} programs not {len(self.programs)}.')

        for i,program in enumerate(desiredorder):
            if not type(program) == str: desiredorder[i] = program.short  # If not str, assume Program and get it's short name

        if desiredorder == list(self.programs.keys()): return # Same order so don't need to continue
        if not (set(desiredorder) == set(self.programs.keys())):   # desiredorder is a list of str, self.programs is an odict
            raise OptimaException(f'You have asked to reorder the programs {[thisprog for thisprog in self.programs]} of programset {self.name} into order {desiredorder}, but the desired order does not have all of the programs.')

        originalprograms = dcp(self.programs)
        self.programs = odict_custom(func=self.checkpropagateversion)
        for i,program in enumerate(desiredorder):
            if program not in originalprograms:
                raise OptimaException(f'You have asked to reorder the program "{program}" to position {i} in programset {self.name}, but there is no program by this name. Available programs are {[thisprog for thisprog in self.programs]}')
            else:
                self.programs[program] = originalprograms[program]  # ordering an odict is done by the order of insertion
        self.updateprogset()
        printv(f'\nReordered the programs in programset: {self.name}.\nThe old order was: {[key for key in originalprograms.keys()]} and the new order is {[key for key in self.programs.keys()]}.')

    def optimizable(self):
        return [True if prog.optimizable() else False for prog in self.programs.values()]

    def optimizableprograms(self):
        return odict((program.short, program) for program in self.programs.values() if program.optimizable())

    def hasbudget(self):
        return [True if prog.hasbudget() else False for prog in self.programs.values()]

    def programswithbudget(self):
        return odict((program.short, program) for program in self.programs.values() if program.hasbudget())

    def hasallcovoutpars(self, detail=False, verbose=2):
        ''' Checks whether all the **required** coverage-outcome parameters are there for coverage-outcome rships'''
        result = True
        details = []
        printv('Checking covout pars', 4, verbose)
        pars = self.projectref().pars() # Link to pars for getting full names
        coveragepars = self.projectref().parset().getcovpars() # Get list of coverage-only parameters
        for thispartype in self.covout.keys():
            printv('Checking %s partype' % thispartype, 4, verbose)
            for thispop in self.covout[thispartype].keys():
                printv('Checking %s pop' % str(thispop), 4, verbose)
                intercept = self.covout[thispartype][thispop].ccopars.get('intercept', None)
                if not(intercept) and intercept!=0:
                    printv('WARNING: %s %s intercept is none' % (thispartype, str(thispop)), 4, verbose)
                    result = False
                    details.append(pars[thispartype].name)
                else:
                    printv('%s %s intercept is %s' % (thispartype, str(thispop), intercept), 4, verbose)
                if thispartype not in coveragepars:
                    for thisprog in self.progs_by_targetpar(thispartype)[thispop]: 
                        printv('Checking %s program' % thisprog.short, 4, verbose)
                        progeffect = self.covout[thispartype][thispop].ccopars.get(thisprog.short, None)
                        if not(progeffect) and progeffect!=0:
                            printv('WARNING: %s %s %s program effect is none' % (thispartype, str(thispop), thisprog.short), 4, verbose)
                            result = False
                            details.append(pars[thispartype].name)
                        else:
                            printv('%s %s %s program effect is %s' % (thispartype, str(thispop), thisprog.short, progeffect), 4, verbose)
        if detail: return list(set(details))
        else: return result

    def hasallcostcovpars(self, detail=False, verbose=2):
        ''' Checks whether all the **required** cost-coverage parameters are there for coverage-outcome rships'''
        result = True
        details = []
        printv('Checking costcov pars', 4, verbose)
        for key,prog in self.optimizableprograms().items():
            printv('Checking %s program' % key, 4, verbose)
            unitcost = prog.costcovfn.ccopars.get('unitcost', None)
            if not(unitcost) and unitcost!=0  or (isinstance(unitcost, list) and isnan(unitcost).all()):
                printv('WARNING: %s unit cost is none' % key, 4, verbose)
                details.append(prog.name)
                result = False
            else:
                printv('%s unit cost is %s' % (key, unitcost), 4, verbose)
            saturation = prog.costcovfn.ccopars.get('saturation', None)
            if not(saturation) and saturation!=0 or (isinstance(saturation, list) and isnan(saturation).all()):
                printv('WARNING: %s saturation is none' % key, 4, verbose)
                details.append(prog.name)
                result = False
            else:
                printv('%s saturation is %s' % (key, saturation), 4, verbose)
            popfactor = prog.costcovfn.ccopars.get('popfactor', None)
            if not(popfactor) and popfactor!=0  or (isinstance(popfactor, list) and isnan(popfactor).all()):
                printv('WARNING: %s popfactor is none' % key, 4, verbose)
                details.append(prog.name)
                result = False
            else:
                printv('%s popfactor is %s' % (key, popfactor), 4, verbose)
                
            totalcost = prog.costcovdata.get('cost',None) 
            if totalcost is None or totalcost==[]:
                printv('WARNING: %s total cost is none' % key, 4, verbose)
                details.append(prog.name)
                result = False
            else:
                printv('%s total cost is %s' % (key, totalcost), 4, verbose)
        if detail: return list(set(details))
        else: return result
                
    def readytooptimize(self, detail=False, verbose=2):
        ''' True if the progset is ready to optimize (i.e. has all required pars) and False otherwise''' 
        hasprograms = bool(sum(self.optimizable()))
        if not detail:
            costcovready = self.hasallcostcovpars(verbose=verbose)
            covoutready = self.hasallcovoutpars(verbose=verbose)
            isready = (hasprograms and costcovready and covoutready)
            return isready  
        else:
            if not hasprograms:
                msg = 'No programs have been defined'
            else:
                msg = ''
                costcovlist = self.hasallcostcovpars(detail=True, verbose=verbose)
                covoutlist = self.hasallcovoutpars(detail=True, verbose=verbose)
                costcovmissing = ', '.join(costcovlist)
                covoutmissing = ', '.join(covoutlist)
                if costcovmissing: msg += 'The following program(s) are missing cost-coverage data: %s. ' % costcovmissing
                if covoutmissing: msg += 'The following parameter(s) are missing coverage-outcome data: %s.'% covoutmissing
            return msg

    def changepopname(self, oldname=None, newname=None):
        '''
        Change the short name of a population in a progset.
        
        Example:
            import optima as op
            P = op.defaultproject('concentrated')
            P.progset().changepopname(oldname='PWID',newname='IDU')
            print(P.progset())
        '''

        if oldname == None: 
            errormsg = 'Please specify the old name of the population that you want to change. Available popnames are' % (self.targetpops)
            raise OptimaException(errormsg)
        if newname == None: 
            errormsg = 'Please specify the new name that you want the population to be called.'
            raise OptimaException(errormsg)
        
        # Helper function for renaming things in tuples
        def changepopobj(popnameobj, oldname=oldname, newname=newname):
            if isinstance(popnameobj,basestring):
                if popnameobj == oldname: 
                    popnameobj = newname
                return popnameobj
            elif isinstance(popnameobj,(tuple,list)):
                pshiplist = list(popnameobj)
                for pn,pop in enumerate(pshiplist):
                    if pop==oldname:
                        pshiplist[pn] = newname
                return tuple(pshiplist)
            else:
                raise OptimaException('changepopobj() only works on strings, tuples, and lists, not %s' % type(popnameobj)) 
    
        # Change name in programs
        for program in self.programs.values():

            # Change name in targetpars
            for targetpar in program.targetpars:
                targetpar['pop'] = changepopobj(targetpar['pop'], oldname=oldname, newname=newname)

            # Change name in targetpops
            for tn, targetpop in enumerate(program.targetpops):
                program.targetpops[tn] = changepopobj(targetpop, oldname=oldname, newname=newname)
                    
        # Change name in covout objects
        for covoutpar in self.covout.keys():
            self.covout[covoutpar] = odict((changepopobj(k, oldname=oldname, newname=newname) if oldname in k else k, v) for k, v in self.covout[covoutpar].items())
        
        # Update WARNING IS THIS REQUIRED?
        self.updateprogset()
        
        return None


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
        progs_by_targetpartype = self.progs_by_targetpartype()
        for thispartype in self.targetpartypes:
            progs_by_targetpar[thispartype] = odict()
            for prog in progs_by_targetpartype[thispartype]:
                targetpars = prog.targetpars if prog.targetpars else None
                for targetpar in targetpars:
                    if thispartype == targetpar['param']:
                        if targetpar['pop'] not in progs_by_targetpar[thispartype]: progs_by_targetpar[thispartype][targetpar['pop']] = []
                        progs_by_targetpar[thispartype][targetpar['pop']].append(prog)
            progs_by_targetpar[thispartype] = progs_by_targetpar[thispartype]
        if filter_partype: return progs_by_targetpar[filter_partype]
        else: return progs_by_targetpar


    def getdefaultbudget(self, t=None, verbose=2, optimizable=None):
        ''' Extract the budget if cost data has been provided; if optimizable is True, then only return optimizable programs '''

        # Initialise outputs
        totalbudget, lastbudget, selectbudget = odict(), odict(), odict()

        # Validate inputs
        if t is not None:t = promotetoarray(t)
        if optimizable is None: optimizable = False # Return only optimizable indices

        # Set up internal variables
        settings = self.getsettings()
        tvec = settings.maketvec()
        emptyarray = array([nan]*len(tvec))

        # Get cost data for each program in each year that it exists
        for program in self.programs:
            totalbudget[program] = dcp(emptyarray)
            selectbudget[program] = []
            try:
                for yrno, yr in enumerate(self.programs[program].costcovdata['t']):
                    yrindex = findinds(tvec,yr)
                    totalbudget[program][yrindex] = self.programs[program].costcovdata['cost'][yrno]
                lastbudget[program] = sanitize(totalbudget[program])[-1]
            except:
                lastbudget[program] = nan # Initialize, to overwrite if there's data
            if isnan(lastbudget[program]):
                printv('WARNING: no cost data defined for program "%s"...' % program, 1, verbose)

            # Extract cost data for particular years, if requested
            if t is not None:
                for yr in t:
                    yrindex = findinds(tvec,yr)
                    selectbudget[program].append(totalbudget[program][yrindex][0])

        # Store default budget as an attribute
        self.defaultbudget = lastbudget
        if t is None:   thisbudget = dcp(lastbudget)
        else:           thisbudget = dcp(selectbudget)
        if optimizable: thisbudget = thisbudget.sorted(self.optimizable()) # Pull out only optimizable programs
        return thisbudget


    def getdefaultcoverage(self, t=None, parset=None, results=None, verbose=2, sample='best', proportion=False):
        ''' Extract the coverage levels corresponding to the default budget'''
        if t is not None: t = promotetoarray(t)
        defaultbudget = self.getdefaultbudget() # WARNING: should be passing t here, but this causes interpolation issues
        if t is not None:
            for prog,budget in defaultbudget.items():
                defaultbudget[prog] = budget*ones(len(t))
        defaultcoverage = self.getprogcoverage(budget=defaultbudget, t=t, parset=parset, results=results, proportion=proportion, sample=sample)
        if t is None or len(list(t)) <= 1:
            for progno in range(len(defaultcoverage)):
                # This does two this, selects the 0th entry from the list, turning it from a odict of lists, into odict of nums, and turns Nones into nans
                defaultcoverage[progno] = defaultcoverage[progno][0] if defaultcoverage[progno] else nan
        return defaultcoverage


    def gettargetpopsizes(self, t=None, parset=None, results=None, verbose=2):
        ''' Extract a disctionary of target pop sizes'''
        # Validate inputs
        if isnumber(t): t = array([t])
        elif isinstance(t, (range, list)): t = array(t)
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')
        defaultinitpopsizes = parset.pars['popsize'].interp(tvec=t)

        targetpopsizes = odict()
        for pn,prog in self.programs.items():
            targetpopsizes[prog.short] = self.programs[pn].gettargetpopsize(t=t, parset=parset, defaultinitpopsizes=defaultinitpopsizes)
        return targetpopsizes


    def getprogcoverage(self, budget, t, parset=None, results=None, proportion=False, sample='best', verbose=2):
        '''Budget is currently assumed to be a DICTIONARY OF ARRAYS'''

        # Initialise output
        coverage = odict()

        # Validate inputs
        if isnumber(t): t = [t]
        if isinstance(budget, list) or isinstance(budget,type(array([]))):
            budget = vec2obj(orig=self.getdefaultbudget(), newvec=budget) # It seems to be a vector: convert to odict
        if type(budget)==dict: budget = odict(budget) # Convert to odict
        budget.sort([p.short for p in self.programs.values()])
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')
        defaultinitpopsizes = parset.pars['popsize'].interp(tvec=t)

        # Get program-level coverage for each program
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    coverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    coverage[thisprog] = self.programs[thisprog].getcoverage(x=spending, t=t, parset=parset, results=results, proportion=proportion, sample=sample, defaultinitpopsizes=defaultinitpopsizes)
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
        coverage.sort([p.short for p in self.programs.values()])

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


    def getpopcoverage(self, budget, t, parset=None, results=None, sample='best', verbose=2, proportion=False):
        '''Get the number of people from each population covered by each program.'''

        # Initialise output
        popcoverage = odict()

        # Validate inputs
        if not isinstance(budget,dict): raise OptimaException('Currently only accepting budgets as dictionaries.')
        if not isinstance(budget,odict): budget = odict(budget)
        budget.sort([p.short for p in self.programs.values()])

        # Get population-level coverage for each program
        for thisprog in self.programs.keys():
            if self.programs[thisprog].optimizable():
                if not self.programs[thisprog].costcovfn.ccopars:
                    printv('WARNING: no cost-coverage function defined for optimizable program, setting coverage to None...', 1, verbose)
                    popcoverage[thisprog] = None
                else:
                    spending = budget[thisprog] # Get the amount of money spent on this program
                    popcoverage[thisprog] = self.programs[thisprog].getcoverage(x=spending, t=t, parset=parset, results=results, total=False, sample=sample, proportion=proportion)
            else: popcoverage[thisprog] = None

        return popcoverage


    def getoutcomes(self, coverage=None, t=None, parset=None, results=None, sample='best'):
        ''' Get the model parameters corresponding to dictionary of coverage values (number covered)'''

        # Initialise output
        outcomes = odict()

        # Validate inputs
        if isnumber(t): t = [t]
        if parset is None:
            if results and results.parset: 
                parset = results.parset
            else: 
                try:    parset = self.projectref().parset() # Get default parset
                except: raise OptimaException('Please provide either a parset or a resultset that contains a parset')
        if coverage is None:
            coverage = self.getdefaultcoverage(t=t, parset=parset, results=results, sample=sample, proportion=False)
        for covkey, coventry in coverage.items(): # Ensure coverage level values are lists
            if isnumber(coventry): coverage[covkey] = [coventry]

        # Set up internal variables
        nyrs = len(t)
        coveragepars = parset.getcovpars() # Get list of coverage-only parameters
        targetpopsizes = self.gettargetpopsizes(t=t, parset=parset)
        progs_by_targetpar = self.progs_by_targetpar()
        propcovered = odict()
        for pn in coverage.keys():
            if coverage[pn] is not None: propcovered[pn] = coverage[pn]/targetpopsizes[pn]

        # Loop over parameter types
        for thispartype in self.targetpartypes:
            outcomes[thispartype] = odict()
            
            # Loop over populations relevant for this parameter type
            for popno, thispop in enumerate(progs_by_targetpar[thispartype].keys()):

                # If it's a coverage parameter, you are done
                if thispartype in coveragepars:
                    outcomes[thispartype][thispop] = array(self.covout[thispartype][thispop].getccopar(t=t, sample=sample)['intercept'])
                    for thisprog in progs_by_targetpar[thispartype][thispop]: # Loop over the programs that target this parameter/population combo
                        if thispop == 'tot':
                            popcoverage = coverage[thisprog.short]
                        else: popcoverage = coverage[thisprog.short]*thisprog.gettargetcomposition(t=t, parset=parset, results=results)[thispop]
                        outcomes[thispartype][thispop] += popcoverage

                # If it's an outcome parameter, need to get outcomes
                else:
                    delta, thiscov = odict(), odict()
                    ccopar = self.covout[thispartype][thispop].getccopar(t=t, sample=sample)

                    # Loop over the programs that target this parameter/population combo
                    for thisprog in progs_by_targetpar[thispartype][thispop]:
                        if not self.covout[thispartype][thispop].ccopars[thisprog.short]:
                            print('WARNING: no coverage-outcome function defined for optimizable program  "%s", skipping over... ' % (thisprog.short))
                            outcomes[thispartype][thispop] = None
                        else:
                            outcomes[thispartype][thispop] = ccopar['intercept']
                            thiscov[thisprog.short] = propcovered[thisprog.short]
                            delta[thisprog.short] = [ccopar[thisprog.short][j] - outcomes[thispartype][thispop][j] for j in range(nyrs)]
                    
                    if outcomes[thispartype][thispop] is not None:
                        for yr in range(nyrs):
                            delt, cov = [],[]
                            for thisprog in thiscov.keys():
                                delt.append(delta[thisprog][yr])
                                cov.append(thiscov[thisprog][yr])
                            # A tuple storing the coverage and delta out, ordered descending by absolute value of delta change, e.g. most impactful program first
                            cov_tuple = sorted(zip(delt,cov), key= lambda x: abs(x[0]), reverse=True)  
                            
                            cumulative_covered = 0. #make sure we can't have more than 100% coverage
                            #By sorting in descending order of program impact, and assuming that each person is only reached by the one most impactful program that they are reached by, we simplify the results.
                            for delt, cov in cov_tuple:
                                #Coverage determined by interaction type
                                #WARNING: a parameter with 'nested' or 'random' coverage and strong negative and strong positive deltas could get strange flipping results, but that's probably a problem with program definitions
                                if self.covout[thispartype][thispop].interaction == 'additive' or len(progs_by_targetpar[thispartype][thispop])==1:
                                    this_cov = min(1-cumulative_covered, cov) #e.g. full coverage unless exceeding 100%
                                elif self.covout[thispartype][thispop].interaction == 'nested':
                                    this_cov = max(cov - cumulative_covered, 0) #e.g. only anything overlapping outside the circle of coverage from more impactful programs
                                elif self.covout[thispartype][thispop].interaction == 'random':
                                    this_cov = (1 - cumulative_covered) * cov  #e.g. a proportional random amount of coverage outside of what has been covered by more impactful programs 
                                else:
                                    raise OptimaException('Unknown reachability type "%s"',self.covout[thispartype][thispop].interaction)
                                outcomes[thispartype][thispop][yr] += this_cov*delt
                                cumulative_covered += this_cov                      
        
        # Validate
        for outcome in outcomes.keys():
            for key in outcomes[outcome].keys():
                if outcomes[outcome][key] is not None and len(outcomes[outcome][key])!=nyrs:
                    raise OptimaException('Parameter lengths must match (len(outcome)=%i, nyrs=%i)' % (len(outcomes[outcome][key]), nyrs))
        return outcomes
        
        
        
    def getpars(self, coverage, t=None, parset=None, results=None, sample='best', die=False, verbose=2):
        ''' Make pars'''
        
        years = t # WARNING, not renaming in the function definition for now so as to not break things
        
        
        # Validate inputs
        if years is None: raise OptimaException('To get pars, one must supply years')
        if isnumber(years): years = [years]
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')
        
        # Get settings
        settings = self.getsettings()

        # Get outcome dictionary
        outcomes = self.getoutcomes(coverage=coverage, t=years, parset=parset, results=results, sample=sample)

        # Create a parset and copy over parameter changes
        pars = dcp(parset.pars)
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
    
    
    
    def compareoutcomes(self, parset=None, year=None, doprint=False):
        ''' For every parameter affected by a program, return a list comparing the default parameter values with the budget ones '''
        outcomes = self.getoutcomes(t=year, parset=parset)
        comparison = list()
        maxnamelen = 0
        maxkeylen = 0
        for key1 in outcomes.keys():
            for key2 in outcomes[key1].keys():
                name = parset.pars[key1].name
                maxnamelen = max(len(name),maxnamelen)
                maxkeylen = max(len(str(key2)),maxkeylen)
                parvalue = parset.pars[key1].interp(tvec=year, asarray=False, usemeta=False)[key2]
                budgetvalue = outcomes[key1][key2] 
                if budgetvalue is not None: comparison.append([name, key2, parvalue[0], budgetvalue[0]])
                else: comparison.append([name, key2, parvalue[0], None])
        
        if doprint:
            for item in comparison:
                strctrl = '%%%is | %%%is | Par: %%8s | Budget: %%8s' % (maxnamelen, maxkeylen)
                print(strctrl % (item[0], item[1], sigfig(item[2]), sigfig(item[3])))
                
        return comparison
    

    def cco2odict(self, t=None, sample='best'):
        ''' Parse the cost-coverage-outcome tree and pull out parameter values into an odict '''
        if t is None: raise OptimaException('Please supply a year')
        pardict = odict()
        for targetpartype in self.covout.keys():
            for targetparpop in self.covout[targetpartype].keys():
                pardict[(targetpartype,targetparpop,'intercept')] = [self.covout[targetpartype][targetparpop].getccopar(t=t,sample='lower')['intercept'][0],self.covout[targetpartype][targetparpop].getccopar(t=t,sample='upper')['intercept'][0]]
                for thisprog in self.progs_by_targetpar(targetpartype)[targetparpop]:
                    try: pardict[(targetpartype,targetparpop,thisprog.short)] = [self.covout[targetpartype][targetparpop].getccopar(t=t,sample='lower')[thisprog.short][0], self.covout[targetpartype][targetparpop].getccopar(t=t,sample='upper')[thisprog.short][0]]
                    except: pass # Must be something like ART, which does not have adjustable parameters -- WARNING, could test explicitly!
        return pardict



    def odict2cco(self, modifiablepars=None, t=None):
        ''' Take an odict and use it to update the cost-coverage-outcome tree '''
        if modifiablepars is None: raise OptimaException('Please supply modifiablepars')
        for key,val in modifiablepars.items():
            targetpartype,targetparpop,thisprogkey = key # Split out tuple
            self.covout[targetpartype][targetparpop].ccopars[thisprogkey] = [tuple(val)]
            if t: self.covout[targetpartype][targetparpop].ccopars['t'] = [t] # WARNING, reassigned multiple times, but shouldn't matter...
        return None
    
    
    
    def reconcile(self, parset=None, year=None, objective='mape', maxiters=1000, maxtime=None, uselimits=True, verbose=2, **kwargs):
        '''
        A method for automatically reconciling coverage-outcome parameters with model parameters.
        
        Example code to test:
        
        import optima as op
        P = op.defaults.defaultproject('best')
        P.progset().reconcile(year=2016, uselimits=False, verbose=4)
        '''
        printv('Reconciling cost-coverage outcomes with model parameters....', 1, verbose)
        
        # Try defaults if none supplied
        if not hasattr(self,'project'):
            try: self.projectref = Link(parset.projectref())
            except: raise OptimaException('Could not find a usable project')
                
        if parset is None:
            try: parset = self.projectref().parset()
            except: raise OptimaException('Could not find a usable parset')
        
        # Initialise internal variables 
        settings = self.getsettings()
        origpardict = dcp(self.cco2odict(t=year))
        pardict = dcp(origpardict)
        pararray = dcp(pardict[:]) # Turn into array format
        parmeans = pararray.mean(axis=1)
        if uselimits: # Use user-specified limits
            parlower = dcp(pararray[:,0])
            parupper = dcp(pararray[:,1])
        else: # Just use parameter limits
            npars = len(parmeans)            
            parlower = zeros(npars)
            parupper = zeros(npars)
            for k,tmp in enumerate(pardict.keys()):
                parname = tmp[0] # First entry is parameter name
                limits = convertlimits(parset.pars[parname].limits, dt=settings.dt)
                parlower[k] = limits[0]
                parupper[k] = limits[1]
        if any(parupper<parlower): 
            problemind = findinds(parupper<parlower)
            errormsg = 'At least one lower limit is higher than one upper limit:\n%s %s' % (pardict.keys()[problemind], pardict[problemind])
            raise OptimaException(errormsg)
        
        # Prepare inputs to optimization method
        args = odict([('pardict',pardict), ('progset',self), ('parset',parset), ('year',year), ('objective',objective), ('verbose',verbose)])
        origmismatch = costfuncobjectivecalc(parmeans, **args) # Calculate initial mismatch too get initial probabilities (pinitial)
            
        res = asd(costfuncobjectivecalc, parmeans, args=args, xmin=parlower, xmax=parupper, maxiters=maxiters, maxtime=maxtime, verbose=verbose, **kwargs)
        currentmismatch = costfuncobjectivecalc(res.x, **args) # Calculate initial mismatch, just, because
        
        # Wrap up
        pardict[:] = replicatevec(res.x)
        self.odict2cco(pardict) # Copy best values
        printv('Reconciliation reduced mismatch from %f to %f' % (origmismatch, currentmismatch), 2, verbose)
        return None


def replicatevec(vec,n=2):
    ''' Tiny function to turn a vector into a form suitable for feeding into an odict '''
    output = []
    for i in vec: output.append([i]*n) # Make a list of lists, with the sublists having length n
    return output
    

def costfuncobjectivecalc(parmeans=None, pardict=None, progset=None, parset=None, year=None, objective=None, verbose=2, eps=1e-3):
    ''' Calculate the mismatch between the budget-derived cost function parameter values and the model parameter values for a given year '''
    pardict[:] = replicatevec(parmeans)
    progset.odict2cco(dcp(pardict), t=year)
    comparison = progset.compareoutcomes(parset=parset, year=year)
    allmismatches = []
    mismatch = 0
    for budgetparpair in comparison:
        parval = budgetparpair[2]
        budgetval = budgetparpair[3]
        if parval and budgetval: # If either of these values are zero, probably hopeless trying to calculate mismatch
            if   objective in ['wape','mape']: thismismatch = abs(budgetval - parval) / (parval+eps)
            elif objective=='mad':             thismismatch = abs(budgetval - parval)
            elif objective=='mse':             thismismatch =    (budgetval - parval)**2
            else:
                errormsg = 'autofit(): "objective" not known; you entered "%s", but must be one of:\n' % objective
                errormsg += '"wape"/"mape" = weighted/mean absolute percentage error (default)\n'
                errormsg += '"mad"  = mean absolute difference\n'
                errormsg += '"mse"  = mean squared error'
                raise OptimaException(errormsg)
        else:
            thismismatch = 0.0 # Give up
        allmismatches.append(thismismatch)
        mismatch += thismismatch
        printv('%45s | %30s | par: %s | budget: %s | mismatch: %s' % ((budgetparpair[0],budgetparpair[1])+sigfig([parval,budgetval,thismismatch],4)), 3, verbose)
    return mismatch




def checkifparsetoverridesprogset(progset=None, parset=None, progendyear=None, progstartyear=None, formatfor='console', createmessages=True):
    """
    A function that sets up the inputs to call checkifparsoverridepars() to see if the parset contains any parameters that
    override the parameters that a progset is trying to target. If any conflicts are found, the warning message(s) can
    be created with createmessages=True, otherwise combinedwarningmsg, warningmessages will both be None
    Args:
        progset: a Programset object
        parset: a Parameterset object that may override the progset's target parameters
        progendyear: year the progset is starting
        progstartyear: year the progset is ending
        formatfor: 'console' with \n linebreaks, or 'html' with <p> and <br> elements.
        createmessages: True to get combinedwarningmsg, warningmessages from createwarningforoverride()
    Returns:
        warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages
        See checkifparsoverridepars and createwarningforoverride for information about the outputs
    """
    if progset is None or parset is None or parset.pars is None:
        raise OptimaException('checkifparsetoverridesprogset() must be provided with both a progset and a parset, but at least one of them was none.')
    if progendyear is None: progendyear = 2100
    progset.gettargetpars()
    progset.gettargetpartypes()
    progtargetpartypes = progset.targetpartypes
    origpars = parset.pars
    # Returns
    warning, parsoverridingparsdict, overridetimes, overridevals = checkifparsoverridepars(origpars=origpars, targetpars=progtargetpartypes, progstartyear=progstartyear, progendyear=progendyear)

    combinedwarningmsg, warningmessages = None, None
    if createmessages:
        progsbytargetpartype = progset.progs_by_targetpartype()
        warning, combinedwarningmsg, warningmessages = createwarningforoverride(origpars, warning, parsoverridingparsdict, overridetimes, overridevals, fortype='Progscen',
                                 progsetname=progset.name, parsetname=parset.name, progsbytargetpartype=progsbytargetpartype, progendyear=progendyear,
                                 formatfor=formatfor)
    return warning, parsoverridingparsdict, overridetimes, overridevals, combinedwarningmsg, warningmessages



class Program(object):
    '''
    Defines a single program. 
    Can be initialized with:
    ccpars, e.g. {'t': [2015,2016], 'saturation': [.90,1.], 'unitcost': [40,30]}
    targetpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]
    targetpops, e.g. ['FSW','MSM']
    '''

    def __init__(self, short, targetpars=None, targetpops=None, ccopars=None, costcovdata=None, nonhivdalys=0,
        category='No category', name='', criteria=None, targetcomposition=None, projectversion=None):
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
        self.projectversion = projectversion


    def __repr__(self):
        ''' Print out useful info'''
        output = defaultrepr(self)
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.targetpops
        output += '   Targeted parameters: %s\n'    % self.targetpars
        output += '\n'
        return output

    def getprojectversion(self, projectversion=None, die=False):
        if projectversion is None: projectversion = self.projectversion
        if projectversion is None:
            err = f'Program "{self.short}" is missing its projectversion'
            if die: raise OptimaException(err)
            else: print('WARNING: '+err)
            return None
        return projectversion

    def optimizable(self):
        return True if self.targetpars else False # and self.hasbudget()

    def hasbudget(self):
        return True if self.costcovdata['cost'] else False

    def addtargetpar(self, targetpar, verbose=2):
        '''Add a model parameter to be targeted by this program'''
        if (targetpar['param'],targetpar['pop']) not in [(tp['param'],tp['pop']) for tp in self.targetpars]:
            self.targetpars.append(targetpar)
            self.targetpartypes = list(set([thispar['param'] for thispar in self.targetpars]))
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
            if costcovdatum.get('coverage') or ('coverage' in costcovdatum.keys() and costcovdatum.get('coverage') == 0):
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
        
        # Ensure it's in order
        order = argsort(self.costcovdata['t']) # Get the order from the years
        for key in ['t', 'cost', 'coverage']: # Reorder each of them to be the same
            self.costcovdata[key] = [self.costcovdata[key][o] for o in order]
        return None


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
        return None


    def gettargetpopsize(self, t, parset=None, results=None, total=True, useelig=False, die=False, defaultinitpopsizes=None):
        '''Returns target population size in a given year (either total or by population).
        Target population size is adjusted according to the population factor for the program.
        '''

        # Validate inputs
        if isnumber(t): t = array([t])
        elif isinstance(t, (range, list)): t = array(t)
        if parset is None:
            if results and results.parset: parset = results.parset
            else: raise OptimaException('Please provide either a parset or a resultset that contains a parset')

        # Initialise outputs
        popsizes = odict()
        targetpopsize = odict()
        if defaultinitpopsizes is None: defaultinitpopsizes = parset.pars['popsize'].interp(tvec=t)
        else: defaultinitpopsizes = dcp(defaultinitpopsizes)
        
        # If we are ignoring eligibility, just sum the popsizes...
        if not useelig:
            initpopsizes = defaultinitpopsizes


        # ... otherwise, have to get the PLHIV pops from results. WARNING, this should be improved.
        else: 

            # Get settings
            try: settings = parset.projectref().settings
            except:
                try: settings = results.projectref().settings
                except: settings = Settings()

            npops = len(parset.pars['popkeys'])
    
            if not self.criteria['pregnant']:
                if self.criteria['hivstatus']=='allstates':
                    initpopsizes = defaultinitpopsizes
                else: # If it's a program for HIV+ people, need to find the number of positives
                    try:
                        if not results: results = parset.getresults(die=die)
                        cd4index = sort(cat([settings.__dict__[state] for state in self.criteria['hivstatus']])) # CK: this should be pre-computed and stored if it's useful
                        initpopsizes = zeros((npops,len(t))) 
                        for yrno,yr in enumerate(t):
                            initpopsizes[:,yrno] = results.raw[0]['people'][cd4index,:,findinds(results.tvec,yr)].sum(axis=0) # WARNING, is using the zeroth result OK?
                    except OptimaException as E: 
                        if die: 
                            raise E
                        else:
                            print('Failed to extract results because "%s", using default' % repr(E))
                            initpopsizes = defaultinitpopsizes
            
            else: # ... or if it's a program for pregnant women.
                if self.criteria['hivstatus']=='allstates': # All pregnant women
                    initpopsizes = parset.pars['popsize'].interp(tvec=t)*parset.pars['birth'].interp(tvec=t)
    
                else: # HIV+ pregnant women
                    try: 
                        if not results: results = parset.getresults(die=die)
                        for yr in t:
                            initpopsizes = parset.pars['popsize'].interp(tvec=[yr])*parset.pars['birth'].interp(tvec=[yr])*transpose(results.main['prev'].pops[0,:,findinds(results.tvec,yr)])
                    except OptimaException as E: 
                        if die: 
                            raise E
                        else: 
                            print('Failed to extract results because "%s", using default' % repr(E))
                            initpopsizes = defaultinitpopsizes
        for popno, pop in enumerate(parset.pars['popkeys']):
            popsizes[pop] = initpopsizes[popno,:]
        
        if self.costcovfn.ccopars:
            popfactor = promotetoarray(self.costcovfn.getccopar(t=t)['popfactor'])
        else:
            popfactor = array([1.])
            
        for targetpop in self.targetpops:
            if targetpop.lower() in ['total','tot','all']:
                targetpopsize[targetpop] = sum(list(popsizes.values()))
            else:
                targetpopsize[targetpop] = popsizes[targetpop]
            #Adjust by population factor for the program
            targetpopsize[targetpop] *= popfactor
                
        finalpopsize = array([sum(list(targetpopsize.values()))]) if isnumber(sum(list(targetpopsize.values()))) else sum(list(targetpopsize.values()))
                    
        if total: return finalpopsize
        else:     return targetpopsize


    def gettargetcomposition(self, t, parset=None, results=None, total=True):
        '''Tells you the proportion of the total population targeted by a program that is comprised of members from each sub-population group.'''
        targetcomposition = odict()

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(list(poptargeted.values()))

        for targetpop in self.targetpops:
            targetcomposition[targetpop] = poptargeted[targetpop]/totaltargeted
        return targetcomposition


    def getcoverage(self, x, t, parset=None, results=None, total=True, proportion=False, toplot=False, sample='best', defaultinitpopsizes=None):
        '''Returns coverage for a time/spending vector'''

        # Validate inputs
        x = promotetoarray(x)
        t = promotetoarray(t)

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False, defaultinitpopsizes=defaultinitpopsizes)

        totaltargeted = sum(list(poptargeted.values()))
        totalreached = self.costcovfn.evaluate(x=x, popsize=totaltargeted, t=t, toplot=toplot, sample=sample)

        if total: 
            if proportion: output = totalreached/totaltargeted
            else:          output = totalreached
        else:
            popreached = odict()
            targetcomposition = self.targetcomposition if self.targetcomposition else self.gettargetcomposition(t=t,parset=parset)
            for targetpop in self.targetpops:
                popreached[targetpop] = totalreached*targetcomposition[targetpop]
                if proportion: popreached[targetpop] /= poptargeted[targetpop]
            output = popreached
        return output
            


    def getbudget(self, x, t, parset=None, results=None, proportion=False, toplot=False, sample='best'):
        '''Returns budget for a coverage vector'''

        poptargeted = self.gettargetpopsize(t=t, parset=parset, results=results, total=False)
        totaltargeted = sum(list(poptargeted.values()))
        if not proportion: reqbudget = self.costcovfn.evaluate(x=x,popsize=totaltargeted,t=t,inverse=True,toplot=False,sample=sample)
        else: reqbudget = self.costcovfn.evaluate(x=x*totaltargeted,popsize=totaltargeted,t=t,inverse=True,toplot=False,sample=sample)
        return reqbudget


########################################################
# COST COVERAGE OUTCOME FUNCTIONS
########################################################
class CCOF(object):
    '''Cost-coverage, coverage-outcome and cost-outcome objects'''

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
        if ccopar.get('unitcost') is not None:
            if not ccopar.get('saturation'): ccopar['saturation'] = (1.,1.)
            if not ccopar.get('popfactor'):  ccopar['popfactor']  = (1.,1.)

        if not self.ccopars:
            for ccopartype in ccopar.keys():
                self.ccopars[ccopartype] = [ccopar[ccopartype]]
        else:
            if (not self.ccopars['t']) or (ccopar['t'] not in self.ccopars['t']):
                for ccopartype in self.ccopars.keys():
                    if ccopartype in ccopar.keys() and ccopar[ccopartype] is not None: #Treatment progs can have an empty list for saturation
                        self.ccopars[ccopartype].append(ccopar[ccopartype])
                printv('\nAdded CCO parameters "%s". \nCCO parameters are: %s' % (ccopar, self.ccopars), 4, verbose)
            else:
                if overwrite:
                    ind = self.ccopars['t'].index(int(ccopar['t']))
                    oldccopar = odict()
                    for ccopartype in ccopar.keys():
                        if self.ccopars[ccopartype]:
                            oldccopar[ccopartype] = self.ccopars[ccopartype][ind]
                            printv('\nModified CCO parameter "%s" from "%s" to "%s"' % (ccopartype, oldccopar[ccopartype], ccopar[ccopartype]), 4, verbose)
                        else:
                            printv('Added CCO parameter "%s" with value "%s"' % (ccopartype, ccopar[ccopartype]), 4, verbose)
                        self.ccopars[ccopartype][ind] = ccopar[ccopartype]
                    
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
        ccopars_sample = odict()
        t = promotetoarray(t)
        nyrs = len(t)
        
        # Get the appropriate sample type
        for parname, parvalue in self.ccopars.items():
            parvalue = promotetoarray(parvalue)
            if parname != 't' and len(parvalue):
                ccopars_sample[parname] = zeros(len(parvalue))
                for j in range(len(parvalue)):
                    thisval = parvalue[j]
                    if isnumber(thisval): thisval = (thisval, thisval)
                    if sample in ['median', 'm', 'best', 'b', 'average', 'av', 'single']:
                        ccopars_sample[parname][j] = mean(array(thisval[:]))
                    elif sample in ['lower','l','low']:
                        ccopars_sample[parname][j] = thisval[0]
                    elif sample in ['upper','u','up','high','h']:
                        ccopars_sample[parname][j] = thisval[1]
                    elif sample in ['random','rand','r']:
                        ccopars_sample[parname][j] = uniform(parvalue[j][0],parvalue[j][1])
                    else:
                        raise OptimaException('Unrecognised bounds.')
        
        # CK: I feel there might be a more direct way of doing all of this...
        ccopartuples = list(zip(self.ccopars['t'], *ccopars_sample.values())) # Rather than forming a tuple and then pulling out the elements, maybe keep the arrays separate?
        knownt = array([ccopartuple[0] for ccopartuple in ccopartuples])

        # Calculate interpolated parameters
        for j,param in enumerate(ccopars_sample.keys()): 
            knownparam = array([ccopartuple[j+1] for ccopartuple in ccopartuples])
            allparams = smoothinterp(t, knownt, knownparam, smoothness=0)
            ccopar[param] = zeros(nyrs)
            for yr in range(nyrs):
                ccopar[param][yr] = allparams[yr]
            if isinstance(t,list): ccopar[param] = ccopar[param].tolist()

        ccopar['t'] = t
        if verbose>=4: printv('\nCalculated CCO parameters in year(s) %s to be %s' % (t, ccopar), 4, verbose)
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
        ccopar  = self.getccopar(t=t,sample=sample)
        saturationlower = self.getccopar(t=t,sample='lower')['saturation']
        saturationupper = self.getccopar(t=t,sample='upper')['saturation']
        
        if not inverse: return self.function(x=x,ccopar=ccopar,popsize=popsize, saturationlower=saturationlower, saturationupper=saturationupper)
        else: return self.inversefunction(x=x,ccopar=ccopar,popsize=popsize, saturationlower=saturationlower, saturationupper=saturationupper)

    def function(self, x, ccopar, popsize):
        pass

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
                            'unitcost': [40,30],
                            'popfactor': [1,1]
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

    def function(self, x, ccopar, popsize, eps=None, saturationlower=None, saturationupper=None):
        '''Returns coverage in a given year for a given spending amount.
        Linear coverage up to saturationlower, scaling non-linearly to saturationupper
        popsize should have been adjusted by population factor if appropriate before reaching this function'''
        
        if eps is None: eps = Settings().eps # Warning, this uses project-nonspecific eps

        # Get the values that are always there
        u  = promotetoarray(ccopar['unitcost'])
        s  = promotetoarray(ccopar['saturation'])
        pf = promotetoarray(ccopar['popfactor'])
        popsize = promotetoarray(popsize)
        
        nyrs,npts = len(u),len(x)
        
        #if saturationlowwer andd saturationupper are not specified, default to previous behaviour using fully non-linear scaling to the median saturation value
        if saturationlower is None:
            saturationlower = zeros(npts)
        if saturationupper is None:
            saturationupper = maximum(saturationlower, s)
        
        eps = array([eps]*npts)
        
        if nyrs==npts:
            naivey = x/maximum(eps, popsize*u) #naive coverage (just total spend/unit cost as a proportion of the population)
            liny  = minimum(naivey, saturationlower) #linear component of coverage (naive cover, or lower saturation limit if that's lower)
            
            covscale = maximum((1.-saturationlower), eps) #this is the remaining proportion of the coverage space that needs to be scaled nonlinearly
            sa      = maximum((saturationupper - saturationlower)/covscale, eps)  #saturation as a proportion of remaining space
            nlinnaivey = (naivey - liny) / covscale #Naively covered proportion of the remaining space

            nliny = maximum(2*sa/(1+exp(-2*nlinnaivey/sa))-sa, 0)*covscale #nonlinear component of coverage, needs to be scaled back by covscale 
            
            y = (liny + nliny)*popsize
            # y = (2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize
        else:
            if (len(saturationlower)!=nyrs or len(saturationupper)!=nyrs):
                raise OptimaException('If passing multiple year arguments at once, must also pass multiple saturation arguments') 
            y = zeros((nyrs,npts))
            for yr in range(nyrs):
                naivey = x/maximum(eps, popsize[yr]*u[yr]) #naive coverage (just total spend/unit cost as a proportion of the population)
                liny  = minimum(naivey, saturationlower[yr]) #linear component of coverage (naive cover, or lower saturation limit if that's lower)
                
                covscale = maximum((1.-saturationlower[yr]), eps) #this is the remaining proportion of the coverage space that needs to be scaled nonlinearly
                sa      = maximum((saturationupper[yr] - saturationlower[yr])/covscale, eps)  #saturation as a proportion of remaining space
                nlinnaivey = (naivey - liny) / covscale #Naively covered proportion of the remaining space
        
                nliny = maximum(2*sa/(1+exp(-2*nlinnaivey/sa))-sa, 0)*covscale #nonlinear component of coverage, needs to be scaled back by covscale 
                
                y[yr,:] = (liny + nliny)*popsize[yr]
                # y[yr,:] = (2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr]
            
        return maximum(y, eps)

    def inversefunction(self, x, ccopar, popsize, eps=None, saturationlower=None, saturationupper=None):
        '''Returns spending in a given year for a given coverage amount.
        Linear coverage up to saturationlower, scaling non-linearly to saturationupper'''
        
        if eps is None: eps = Settings().eps # Warning, use project-nonspecific eps

        # Get the values that are always there
        u  = promotetoarray(ccopar['unitcost'])
        s  = promotetoarray(ccopar['saturation'])
        pf = promotetoarray(ccopar['popfactor'])
        popsize = promotetoarray(popsize)

        nyrs,npts = len(u),len(x)             
        
        #if saturationlowwer and saturationupper are not specified, default to previous behaviour using fully non-linear scaling to the median saturation value
        if saturationlower is None:
            saturationlower = zeros(npts)
        if saturationupper is None:
            saturationupper = maximum(saturationlower, s)
            
        eps = array([eps]*npts)
        
        if nyrs==npts:
            linx  = minimum(x/popsize, saturationlower)*popsize #NUMBER of coverage that would have been achieved with linear cost-coverage (everything below saturationlower)
            nlinx = maximum(x/popsize - saturationlower, 0)*popsize #NUMBER of coverage that needs to be costed based on non-linear cost-coverage (everything above saturationlower and below saturationupper)

            liny = linx*u #proportion of linear spending = number of people covered * unit cost
            
            satnumber = popsize * (saturationupper - saturationlower) #The number of people that would be covered by the nonlinear scaling if fully saturated
            
            nliny = -0.5*satnumber*u*log(maximum(satnumber-nlinx,eps)/maximum((satnumber+nlinx), eps)) #proportion of spending at non-linear scaling
            
            y = liny + nliny
            # y = -0.5*popsize*s*u*log(maximum(s*popsize-x,0)/(s*popsize+x))
        else:
            if (len(saturationlower)!=nyrs or len(saturationupper)!=nyrs):
                raise OptimaException('If passing multiple year arguments at once, must also pass multiple saturation arguments')
            y = zeros((nyrs,npts))
            for yr in range(nyrs):
                linx  = minimum(x/popsize[yr], saturationlower[yr])*popsize[yr] #NUMBER of coverage that would have been achieved with linear cost-coverage (everything below saturationlower)
                nlinx = maximum(x/popsize[yr] - saturationlower[yr], 0)*popsize[yr] #NUMBER of coverage that needs to be costed based on non-linear cost-coverage (everything above saturationlower and below saturationupper)
        
                liny = linx*u[yr] #proportion of linear spending = number of people covered * unit cost
                
                satnumber = popsize[yr] * (saturationupper[yr] - saturationlower[yr]) #The number of people that would be covered by the nonlinear scaling if fully saturated
                
                nliny = -0.5*satnumber*u[yr]*log(maximum(satnumber-nlinx,eps)/maximum((satnumber+nlinx), eps)) #proportion of spending at non-linear scaling
                
                y[yr,:] = liny + nliny
                # y[yr,:] = -0.5*popsize[yr]*s[yr]*u[yr]*log(maximum(s[yr]*popsize[yr]-x,0)/(s[yr]*popsize[yr]+x))
        
        return maximum(y, eps)
            

########################################################
# COVERAGE OUTCOME FUNCTIONS
########################################################
class Covout(CCOF):
    '''Coverage-outcome objects'''

    def function(self,x,ccopar,popsize):
        pass

    def inversefunction(self, x, ccopar, popsize):
        pass

