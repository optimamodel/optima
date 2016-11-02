"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2016oct30
"""

from optima import OptimaException, printv, uuid, today, sigfig, dataframe, dcp, findinds, odict, Settings, sanitize, defaultrepr, gridcolormap, isnumber, promotetoarray, vec2obj, runmodel, asd, convertlimits, loadprogramspreadsheet, CCOpar, smoothinterp
from numpy import ones, prod, array, zeros, exp, log, linspace, append, nan, isnan, maximum, minimum, sort, argsort, concatenate as cat, transpose
from random import uniform

# [par.coverage for par in P.pars().values() if hasattr(par,'coverage')]

class Programset(object):
    """
    Object to store all programs. Coverage-outcome data and functions belong to the program set, 
    while cost-coverage data/functions belong to the individual programs.
    """

    def __init__(self, name='default', programs=None, project=None, verbose=2):
        """ Initialize """
        self.name = name
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.project = project # Store pointer for the project, if available
        self.programs = odict()
        self.covout = odict()
        if programs is not None: self.addprograms(programs, verbose=verbose)

    def __repr__(self):
        """ Print out useful information"""
        output = defaultrepr(self)
        return output
    
    def addprograms(self, programs=None, overwrite=True, verbose=2):
        if type(programs)!=list: programs = [programs] # Make into a list if a single program supplied
        for program in programs:
            if type(program)!=Program:
                errormsg = 'Can only add programs, not objects of type %s' % type(program)
                raise OptimaException(errormsg)
            if program.short in self.programs.keys() and not overwrite:
                errormsg = 'Program %s already exists in program set' % program.short
                raise OptimaException(errormsg)
            self.programs[program.short] = program
            printv('Added program "%s" to programset "%s"' % (program.short, self.name), 3, verbose)
        return None
        
    def rmprograms(self, programs=None):
        if type(programs)!=list: programs = [programs] # Make into a list if a single program supplied
        for program in programs:
            if type(program)==Program: program = program.short
            self.programs.pop(program)
        return None
    
    
    def addcovoutpar(self, parname=None, popname=None, covoutpar=None, verbose=2):
        try:
            zerocov = covoutpar.pop('zerocov') # Pull out the value at zero coverage
            fullcov = covoutpar.pop('fullcov') # Pull out the value at full coverage
        except:
            errormsg = 'Covout parameter must be dict with keys zerocov and fullcov at minimum; yours is:\n%s' % covoutpar
            raise OptimaException(errormsg)
        for key in covoutpar.keys(): # Check that all remaining keys are valid
            if key not in self.programs.keys():
                errormsg = 'Program key "%s" not found; available keys are:\n%s' % (key, self.programs.keys())
                raise OptimaException(errormsg)
        key = (parname, popname) # For a dict key, make a tuple from the parameter name and the population name
        self.covout[key] = Covout(parname=parname, popname=popname, zerocov=zerocov, fullcov=fullcov, progs=covoutpar) # Everything remaining is the programs
        printv('Added coverage-outcome parameter: %s' % covoutpar, 4, verbose)
        return None
    
        
    def defaultbudget(self, verbose=2):
        ''' Extract the most recent budget information for each program '''
        budget = odict()
        for progname,program in self.programs.items():
            try: 
                budget[progname] = program.costcovdata['cost',-1]
            except: 
                budget[progname] = 0.0
                printv('defaultbudget(): No cost data entered for program %s' % progname, 1, verbose)
        return budget
    
    
    def getcoverage(self, budget=None, year=None, parset=None, ind=0, fraction=True, verbose=2):
        ''' Return coverage based on a given budget. If None, then use default. '''
        coverage = odict()
        if budget is None: budget = self.defaultbudget(verbose=verbose)
        if year is None: year = self.project.settings.now
        if parset is None: parset = -1
        popsizes = self.project.parsets[parset].pars[ind]['popsize'].interp(tvec=year, asarray=False)
        
        for progname,program in self.programs.items():
            yearvec = program.costcovpars['year']
            unitcostvec = program.costcovpars['unitcost']
            print('NO NEED TO HANDLE TUPLES')
            saturationvec = program.costcovpars['saturation']
            unitcost = smoothinterp(newx=year, origx=yearvec, origy=unitcostvec)
            saturation = smoothinterp(newx=year, origx=yearvec, origy=saturationvec)
            linearpeoplecovered = budget[progname]/unitcost # Calculate the number of people covered purely linearly
            popsize = popsizes[program.targetpops].sum() # WARNING, need to implement criteria!
            fracpeoplecovered = linearpeoplecovered/popsize
            fracsquashed = squashfunc(fracpeoplecovered, 0, saturation) # Squash nonlinearly 
            if fraction: thiscoverage = fracsquashed
            else: thiscoverage = fracsquashed*popsize
            coverage[progname] = thiscoverage         
        
        return coverage
    
    
    def getoutcomes(self, coverage=None, budget=None, year=None, parset=None, sample='best', randseed=0, verbose=2):
        
        # Get year
        if year is None: year = self.project.settings.now
        
        if coverage is not None and budget is not None: # Check input arguments
            raise OptimaException('getoutcomes() accepts a coverage or a budget input, but not both')
        elif coverage is None: # Calculate coverage, using default if budget is not supplied
            coverage = self.getcoverage(budget=budget, year=year, parset=parset)
        
        pass


  
    def loadspreadsheet(self, filename, verbose=3):
        """Load a spreadsheet with cost and coverage data and parametres for the cost functions""" 
    
        ## Load data
        data = loadprogramspreadsheet(filename)
        data['years'] = array(data['years'])
        npops = len(data['pops'])
    
        ## Extract program names and check they match the ones in the progset
        prognames = [key for key in data.keys() if key not in ['meta','years','pops']]
        if set(prognames) != set(self.programs.keys()):
            errormsg = 'The short names of the programs in the spreadsheet (%s) must match the short names of the programs in the progset (%s).' % (prognames, self.programs.keys())
            raise OptimaException(errormsg)
        
        ## Load data 
        for prog in prognames:
            self.programs[prog].targetpops = [data['pops'][tp] for tp in range(npops) if data[prog]['targetpops'][tp]] # Set target populations
            costcovdata = {key:data[prog][key] for key in ['year','cost','coverage']}  # Load cost/coverage data
            self.programs[prog].addcostcovdata(costcovdata)
            
            if self.programs[prog].optimizable():
                # Creating CCOpars
                self.programs[prog].costcovpars
                self.programs[prog].costcovpars['unitcost'] = CCOpar(short='unitcost',name='Unit cost',y=odict(),t=odict(), limits=(0,1e9)) # Load unit cost assumptions
                self.programs[prog].costcovpars['saturation'] = CCOpar(short='saturation',name='Maximal attainable coverage',y=odict(),t=odict()) # Load unit cost assumptions
                for par in self.programs[prog].costcovpars.values():
                    bestvalues, bestinds = sanitize(data[prog][par.short]['best'], returninds=True) # We use the best estimates to populate the low and high, and then later we overwrite if there are actual estimates provided
                    bestyears = data['years'][bestinds]
                    for estimate in ['best','low','high']:
                        if len(bestinds): 
                            par.t[estimate] = bestyears
                            par.y[estimate] = bestvalues
                        else:
                            printv('No data for cost parameter "%s"' % (par.short), 3, verbose)
                            par.y[estimate] = array([nan])
                            par.t[estimate] = array([0.])
                        if estimate != 'best': # Here we overwrite the range data, if provided -- WARNING, could simplify all of this substantially!
                            rangevalues, rangeinds = sanitize(data[prog][par.short][estimate], returninds=True)
                            rangeyears = data['years'][rangeinds]
                            if not len(rangeinds): # If no data, use best estimates
                                rangevalues = bestvalues
                                rangeyears = bestyears
                            addsingleccopar(self.programs[prog].costcovpars, parname=par.short, values=rangevalues, years=rangeyears, estimate=estimate, overwrite=True)
                    
        return None


    def compareoutcomes(self, parset=None, year=None, ind=0, doprint=False):
        """ For every parameter affected by a program, return a list comparing the default parameter values with the budget ones """
        outcomes = self.getoutcomes(year=year, parset=parset, ind=ind)
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
    
    
    
    

class Program(object):
    """
    Defines a single program. 
    Can be initialized with:
    costcovpars, e.g. {'year': 2015, 'saturation': 0.9, 'unitcost': 40} # NOT ANY MORE
    targetpars, e.g. [{'param': 'hivtest', 'pop': 'FSW'}, {'param': 'hivtest', 'pop': 'MSM'}]
    targetpops, e.g. ['FSW','MSM']
    """

    def __init__(self, name=None, short=None, targetpars=None, targetpops=None, category=None, criteria=None):
        """Initialize"""
        self.name = name
        self.short = short
        self.uid = uuid()
        self.targetpars = targetpars if targetpars else []
        self.targetpops = targetpops if targetpops else []
        try:
            self.targetpartypes = list(set([thispar['param'] for thispar in self.targetpars])) if self.targetpars else []
        except:
            print("Error while initializing targetpartypes in program %s for targetpars %s" % (short, self.targetpars))
            self.targetpartypes = []
        self.category = category
        self.criteria = criteria
        self.costcovdata = dataframe(['year','cost','coverage']) # Initialize, but don't populate until later
        self.costcovpars = dataframe(['year','unitcost','saturation'])
        


    def __repr__(self):
        """ Print out useful info"""
        output = defaultrepr(self)
        output += '          Program name: %s\n'    % self.short
        output += '  Targeted populations: %s\n'    % self.targetpops
        output += '   Targeted parameters: %s\n'    % self.targetpars
        output += '\n'
        return output
    
    
    def addcostcovpar(self, costcovpar=None, overwrite=False, verbose=2):
        self.costcovpars.addrow(costcovpar, overwrite=overwrite)
        printv('Added cost-coverage parameter: %s' % costcovpar, 4, verbose)
        pass
    
    
    def addcostcovdata(self, costcovdata=None, overwrite=False, verbose=2):
        self.costcovdata.addrow(costcovdata, overwrite=overwrite)
        printv('Added cost-coverage data point: %s' % costcovdata, 4, verbose)
        return None
    
    
    def rmcostcovpar(self, year=None, verbose=2):
        self.costcovpar.rmrow(year)
        printv('Removed cost-coverage parameter point for %s' % year, 4, verbose)
        return None
    
    
    def rmcostcovdata(self, year=None, verbose=2):
        self.costcovdata.rmrow(year)
        printv('Removed cost-coverage data point for %s' % year, 4, verbose)
        return None


    def optimizable(self):
        ''' Simply determine whether or not a program can be optimized -- if it has any target parameters '''
        return True if self.targetpars else False
    
    



class Covout(object):
    ''' Object for storing coverage-outcome properties '''
    
    def __init__(self, parname=None, popname=None, zerocov=None, fullcov=None, progs=None):
        self.parname = parname
        self.popname = popname
        self.zerocov = zerocov
        self.fullcov = fullcov
        self.progs = odict(progs) # Allows for None, creating an empty odict
    
    def __repr__(self):
        return defaultrepr(self)
        

    
    
    






    
    
    
def reconcile(self, parset=None, year=None, ind=0, objective='mape', maxiters=400, maxtime=None, uselimits=True, verbose=2, **kwargs):
    """
    A method for automatically reconciling coverage-outcome parameters with model parameters.
    
    Example code to test:
    
    import optima as op
    P = op.defaults.defaultproject('best')
    P.progset().reconcile(year=2016, uselimits=False, verbose=4)
    """
    printv('Reconciling cost-coverage outcomes with model parameters....', 1, verbose)
    
    # Try defaults if none supplied
    if not hasattr(self,'project'):
        try: self.project = parset.project
        except: raise OptimaException('Could not find a usable project')
            
    if parset is None:
        try: parset = self.project.parset()
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
            limits = convertlimits(parset.pars[0][parname].limits, dt=settings.dt)
            parlower[k] = limits[0]
            parupper[k] = limits[1]
    if any(parupper<parlower): 
        problemind = findinds(parupper<parlower)
        errormsg = 'At least one lower limit is higher than one upper limit:\n%s %s' % (pardict.keys()[problemind], pardict[problemind])
        raise OptimaException(errormsg)
    
    # Prepare inputs to optimization method
    args = odict([('pardict',pardict), ('progset',self), ('parset',parset), ('year',year), ('ind',ind), ('objective',objective), ('verbose',verbose)])
    origmismatch = costfuncobjectivecalc(parmeans, **args) # Calculate initial mismatch too get initial probabilities (pinitial)
    parvecnew, fval, exitflag, output = asd(costfuncobjectivecalc, parmeans, args=args, xmin=parlower, xmax=parupper, MaxIter=maxiters, timelimit=maxtime, verbose=verbose, **kwargs)
    currentmismatch = costfuncobjectivecalc(parvecnew, **args) # Calculate initial mismatch, just, because
    
    # Wrap up
    pardict[:] = replicatevec(parvecnew)
    self.odict2cco(pardict,t=year) # Copy best values
    printv('Reconciliation reduced mismatch from %f to %f' % (origmismatch, currentmismatch), 2, verbose)
    return None
        
    

def costfuncobjectivecalc(parmeans=None, pardict=None, progset=None, parset=None, year=None, ind=None, objective=None, verbose=2, eps=1e-3):
    """ Calculate the mismatch between the budget-derived cost function parameter values and the model parameter values for a given year """
    pardict[:] = replicatevec(parmeans)
    progset.odict2cco(dcp(pardict), t=year)
    comparison = progset.compareoutcomes(parset=parset, year=year, ind=ind)
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



def squashfunc(x, lim1=0, lim2=1):
    ''' Calculate a saturating curve in the forward direction, e.g. cost to coverage '''
    y = 2/(1+exp(-2*x))-1 # Calculate point on curve -- x should be >0, y should be [0,1)
    y = y*(lim2-lim1)+lim1 # Scale to fall within [lim1,lim2)
    return y

def unsquashfunc(y, lim1=0, lim2=1):
    ''' Calculate a saturating curve in the inverse direction, e.g. coverage to cost '''
    y = y-lim1/(lim2-lim1) # Unscale y from [lim1,lim2) to [0,1)
    x = -0.5*log(2/(y+1)-1) # Calculate x, should be >0
    return x


def evalcostcov(ccopars=None, x=None, t=None, popsize=None, inverse=False, sample='best', eps=None, verbose=2):
    """ Evaluate the cost-coverage function and return either a coverage given a cost, or vice versa """
    x = promotetoarray(x)
    t = promotetoarray(t)
    if not len(x)==len(t):
        errormsg = 'x needs to be the same length as t, we assume one spending amount per time point.'
        raise OptimaException(errormsg)
    ccopar = getccopar(ccopars, t=t,sample=sample)
    
    u = array(ccopar['unitcost'])
    s = array(ccopar['saturation'])
    if eps is None: eps = Settings().eps # Warning, use project-nonspecific eps
    if isnumber(popsize): popsize = array([popsize])
    nyrs,npts = len(u),len(x)
    eps = zeros(npts)+eps
    
    if inverse: return covcostfunc(x, s, u, nyrs, npts, popsize, eps)
    else:       return costcovfunc(x, s, u, nyrs, npts, popsize, eps)
    

def costcovfunc(x, s, u, nyrs, npts, popsize, eps):
    """Returns coverage in a given year for a given spending amount."""
    if nyrs==npts: 
        y = maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
    else:
        y = zeros((nyrs,npts))
        for yr in range(nyrs):
            y[yr,:] = maximum((2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr],eps)
    return y


def covcostfunc(x, s, u, nyrs, npts, popsize, eps):
    """Returns cost in a given year for a given coverage amount."""
    if nyrs==npts: 
        y = maximum(-0.5*popsize*s*u*log(maximum(s*popsize-x,0)/(s*popsize+x)),eps)
    else:
        y = zeros((nyrs,npts))
        for yr in range(nyrs):
            y[yr,:] = maximum(-0.5*popsize[yr]*s[yr]*u[yr]*log(maximum(s[yr]*popsize[yr]-x,0)/(s[yr]*popsize[yr]+x)),eps)
    return y
