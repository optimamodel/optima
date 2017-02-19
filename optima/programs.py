"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2017feb19
"""

from optima import OptimaException, Link, Settings, odict, dataframe, objrepr, promotetoarray, promotetolist, defaultrepr, checktype, isnumber
from numpy.random import uniform, seed, get_state
from numpy import array


class Programset(object):
    """
    Object to store all programs. Coverage-outcome data and functions belong to the program set, 
    while cost-coverage data/functions belong to the individual programs.
    """

    def __init__(self, name='default', parsetname=-1, project=None, programs=None, covout=None):
        ''' Initialize '''
        if project is None:
            errormsg = 'To create a program set, you must supply a project as an argument'
            raise OptimaException(errormsg)
        
        self.name = name
        self.programs = odict()
        self.covout = odict()
        self.parsetname = parsetname # Store the parset name
        self.projectref = Link(project) # Store pointer for the project, if available
        if programs is not None: self.addprograms(programs)
        if covout is not None: self.addcovout(covout)
#        self.denominators = self.setdenominators() # Calculate the denominators for different coverage values
        return None

    def __repr__(self):
        """ Print out useful information"""
        output = objrepr(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % self.programs.keys()
        output += '      Programs valid: %s\n'    % self.checkprograms()
        output += '        Covout valid: %s\n'    % self.checkcovout()
        output += '============================================================\n'
        return output
    
    
    def addprograms(self, progs=None, replace=False):
        ''' Add a list of programs '''
        if progs is not None:
            progs = promotetolist(progs)
        else:
            errormsg = 'Programs to add should not be None'
            raise OptimaException(errormsg)
        if replace:
            self.programs = odict()
        for prog in progs:
            if isinstance(prog, dict):
                prog = Program(**prog)
            if type(prog)!=Program:
                errormsg = 'Programs to add must be either dicts or program objects, not %s' % type(prog)
                raise OptimaException(errormsg)
            self.programs[prog.short] = prog
        return None


    def rmprograms(self, progs=None, die=True):
        ''' Remove one or more programs '''
        if progs is None:
            self.programs = odict() # Remove them all
        progs = promotetolist(progs)
        for prog in progs:
            try:
                self.programs.pop[prog]
            except:
                errormsg = 'Could not remove program named %s' % prog
                if die: raise OptimaException(errormsg)
                else: print(errormsg)
            for co in self.covout.values(): # Remove from coverage-outcome functions too
                co.progs.pop(prog, None)
        
        
        return None
    
    
    def addcovout(self):
        ''' add coverage-outcome parameter '''
        pass

    def defaultbudget(self, total=True):
        ''' Get default budget -- either per program or total '''
        if total:      budget = 0
        else: budget = odict()
        for prog in self.programs.values():
            if total: budget += prog.spend
            else:     budget[prog.short] = prog.spend
        return budget

    def coverage2budget(self):
        ''' get budget from coverage '''
        pass

    def budget2coverage(self):
        ''' get coverage from budget '''
        pass

    def reconcile(self):
        ''' reconcile with parset '''
        pass

    def compareoutcomes(self):
        ''' compare textually '''
        pass
    
    def check(self):
        ''' checks that all costcov and covout data is entered '''
        pass



class Program(object):
    '''
    Defines a single program. Example:
    
    FSW = Program(short='FSW', 
               name='FSW programs', 
               category='Prevention', 
               datayear=2016,
               spend=1.34e6, 
               basespend=0, 
               coverage=67000, 
               sauration=0.9, 
               unitcost={'year':2015, 'val':21.43}, 
               targetpops='FSW', # NB, can be a list
               targetpars=('condcom', ('Clients', 'FSW'))
               )
    
    Values can be set later using the update() method, e.g.:
        FSW.update(spend=1.34e6, coverage=67000)       
    
    There is considerable flexibility in how the unitcost and targetpars are specified. For example, with targetpars:
        targetpars = 'numtx' # Sets numtx, assumes 'tot'
        targetpars = ('numtx', 'tot')
        targetpars = {'param':'numtx', 'pop':tot}
        targetpars = ['numtx', 'numpmtct'] # Assumes 'tot' population for both
        targetpars = ['numtx', 'pop'] # NOT valid since assumes a list is a list of parameters
    
    With unitcost:
        unitcost = 21.43 # Assumes current year and no uncertainty
        unitcost = (11.43, 31.43) # Assumes current year, calculates uncertainty
        unitcost = {'year':2017, 'val':(21.43, 11.43, 31.43)} # Sets everything (order doesn't matter)
        unitcost = {'year':2017, 'val':{'best':21.43, 'low':11.43, 'high':31.43}} # Sets everything another way
        unitcost = [{'year':2017, 'val':21.43}, {'year':2018, 'val':16.22}] # Can supply multiple years
    
    Version: 2017feb18 by cliffk  
    '''
    
    def __init__(self, short=None, name=None, category=None, datayear=None, spend=None, basespend=None, coverage=None, unitcost=None, year=None, saturation=None, targetpops=None, targetpars=None):
        
        # Initialize all values so you can see what the structure is
        self.short      = None # short name
        self.name       = None # full name
        self.category   = None # spending category
        self.spend      = None # latest or estimated expenditure
        self.basespend  = None # non-optimizable spending
        self.coverage   = None # latest or estimated coverage (? -- not used)
        self.datayear   = None # Year for which spending and coverage data are available
        self.unitcost   = None # dataframe -- note, 'year' if supplied (not necessary) is stored inside here
        self.saturation = None # saturation coverage value
        self.targetpops = None # key(s) for targeted populations
        self.targetpars = None # which parameters are targeted
        
        # Actually populate the values
        self.update(short=short, name=name, category=category, datayear=datayear, spend=spend, basespend=basespend, coverage=coverage, unitcost=unitcost, year=year, saturation=saturation, targetpops=targetpops, targetpars=targetpars)
        return None
    
    
    def __repr__(self):
        ''' Print the object nicely '''
        output = defaultrepr(self)
        return output
    
    
    def update(self, short=None, name=None, category=None, datayear=None, spend=None, basespend=None, coverage=None, saturation=None, unitcost=None, year=None, targetpops=None, targetpars=None):
        ''' Add data to a program, or otherwise update the values. Same syntax as init(). '''
        
        def settargetpars(targetpars=None):
            ''' Handle targetpars -- a little complicated since it's a list of dicts '''
            targetparkeys = ['param', 'pop']
            targetpars = promotetolist(targetpars) # Let's make sure it's a list before going further
            for tp,targetpar in enumerate(targetpars):
                if isinstance(targetpar, dict): # It's a dict, as it needs to be
                    thesekeys = sorted(targetpar.keys())
                    if thesekeys==targetparkeys: # Keys are correct -- main usage case!!
                        targetpars[tp] = targetpar
                    else:
                        errormsg = 'Keys for a target parameter must be %s, not %s' % (targetparkeys, thesekeys)
                        raise OptimaException(errormsg)
                elif isinstance(targetpar, basestring): # It's a single string: assume only the parameter is specified
                    targetpars[tp] = {'param':targetpar, 'pop':'tot'} # Assume 'tot'
                elif isinstance(targetpar, tuple): # It's a list, assume it's in the usual order
                    if len(targetpar)==2:
                        targetpars[tp] = {'param':targetpar[0], 'pop':targetpar[1]} # If a list or tuple, assume this order
                    else:
                        errormsg = 'When supplying a targetpar as a list or tuple, it must have length 2, not %s' % len(targetpar)
                        raise OptimaException(errormsg)
                else:
                    errormsg = 'Targetpar must be string, tuple, or dict, not %s' % type(targetpar)
                    raise OptimaException(errormsg)
            self.targetpars = targetpars # Actually set it
            return None
        
        def setunitcost(unitcost=None, year=None):
            ''' Handle the unit cost, also complicated since have to convert to a dataframe '''
            unitcostkeys = ['year', 'best', 'low', 'high']
            if self.unitcost is None: self.unitcost = dataframe(cols=unitcostkeys) # Create dataframe
            if isinstance(unitcost, dataframe): self.unitcost = unitcost # Right format already: use directly
            elif isinstance(unitcost, (list, tuple, array([]))): # It's a list of....something, either a single year with uncertainty bounds or multiple years
                if isnumber(unitcost[0]): # It's a number (or at least the first entry is): convert to values and use
                    if year is None: year = Settings().now # If no year is supplied, reset it
                    best,low,high = Val(unitcost).get('all') # Convert it to a Val to do proper error checking and set best, low, high correctly
                    self.unitcost.addrow([year, best, low, high])
                else: # It's not a list of numbers, so have to iterate
                    for uc in unitcost: # Actually a list of unit costs
                        if isinstance(uc, dict): setunitcost(uc) # It's a dict: iterate recursively to add unit costs
                        else:
                            errormsg = 'Could not understand list of unit costs: expecting list of floats or list of dicts, not list containing %s' % uc
                            raise OptimaException(errormsg)
            elif isinstance(unitcost, dict): # Other main usage case -- it's a dict
                blh = [unitcost.get(key) for key in ['best', 'low', 'high']] # Get an array of values...
                best,low,high = Val(blh).get('all') # ... then sanitize them via Val
                self.unitcost.addrow([unitcost.get('year',year), best, low, high]) # Actually add to dataframe
            else:
                errormsg = 'Expecting unit cost of type dataframe, list/tuple/array, or dict, not %s' % type(unitcost)
                raise OptimaException(errormsg)
            return None
                    
        # Actually set everything
        if short      is not None: self.short      = checktype(short,    'string') # short name
        if name       is not None: self.name       = checktype(name,     'string') # full name
        if category   is not None: self.category   = checktype(category, 'string') # spending category
        if spend      is not None: self.spend      = checktype(spend,     'number') # latest or estimated expenditure
        if basespend  is not None: self.basespend  = checktype(basespend, 'number') # non-optimizable spending
        if coverage   is not None: self.coverage   = checktype(coverage,  'number') # latest or estimated coverage (? -- not used)
        if datayear   is not None: self.datayear   = checktype(datayear,  'number') # latest or estimated coverage (? -- not used)
        if saturation is not None: self.saturation = Val(saturation) # saturation coverage value
        if targetpops is not None: self.targetpops = promotetolist(targetpops, 'string') # key(s) for targeted populations
        if targetpars is not None: settargetpars(targetpars) # targeted parameters
        if unitcost   is not None: setunitcost(unitcost, year) # unit cost(s)
        
        return None
        
        

class Covout(object):
    '''
    A coverage-outcome object -- cost-outcome objects are incorporated in programs. Example:
    
    Covout(par='condcom',
           pop=('Clients','FSW'),
           lowerlim=0.4,
           upperlim=[0.95,0.9,0.99],
           progs={'FSW':0.9, 'SBCC':0.5}
           )
    
    Generally, progset-level methods would be used to manipulate these objects, rather than directly.
    
    Version: 2017feb18 by cliffk
    '''
    
    def __init__(self, par=None, pop=None, lowerlim=None, upperlim=None, progs=None):
        self.par = par
        self.pop = pop
        self.lowerlim = Val(lowerlim)
        self.upperlim = Val(upperlim)
        self.progs = odict()
        if progs is not None: self.add(progs)
        return None
    
    def add(self, prog=None, val=None):
        ''' 
        Accepts either
        self.add([{'FSW':[0.3,0.1,0.4]}, {'SBCC':[0.1,0.05,0.15]}])
        or
        self.add('FSW', 0.3)
        '''
        if isinstance(prog, dict):
            for key,val in prog.items():
                self.progs[key] = Val(val)
        elif isinstance(prog, (list, tuple)):
            for key,val in prog:
                self.progs[key] = Val(val)
        elif isinstance(prog, basestring) and val is not None:
            self.progs[prog] = Val(val)
        else:
            errormsg = 'Could not understand prog=%s and val=%s' % (prog, val)
            raise OptimaException(errormsg)
        return None
            




class Val(object):
    '''
    A single value including uncertainty -- seems insanely complicated for what it does, I know!
    
    Can be set the following ways:
    v = Val(0.3)
    v = Val([0.2, 0.4])
    v = Val([0.3, 0.2, 0.4])
    v = Val(best=0.3, low=0.2, high=0.4)
    
    Can be called the following ways:
    v() # returns 0.3
    v('best') # returns 0.3
    v(what='best') # returns 0.3
    v('rand') # returns value between low and high (assuming uniform distribution)
    
    Can be updated the following ways:
    v(0.33) # resets best
    v([0.22, 0.44]) # resets everything
    v(best=0.33) # resets best
    
    Version: 2017feb18 by cliffk
    '''
    
    def __init__(self, best=None, low=None, high=None, dist=None):
        ''' Allow the object to be initialized, but keep the same infrastructure for updating '''
        self.best = None
        self.low = None
        self.high = None
        self.dist = None
        self.update(best=best, low=low, high=high, dist=dist)
        return None
    
    
    def __call__(self, *args, **kwargs):
        ''' Convenience function for both update and get '''
        
        # If it's None or if the key is a string (e.g. 'best'), get the values:
        if len(args)+len(kwargs)==0 or 'what' in kwargs or (len(args) and type(args[0])==str):
            return self.get(*args, **kwargs)
        else: # Otherwise, try to set the values
            self.update(*args, **kwargs)
    
    
    def update(self, best=None, low=None, high=None, dist=None):
        ''' Actually set the values -- very convoluted, but should be flexible and work :)'''
        
        # Reset these values if already supplied
        if best is None and self.best is not None: best = self.best
        if low  is None and self.low  is not None: low  = self.low 
        if high is None and self.high is not None: high = self.high 
        if dist is None and self.dist is not None: dist = self.dist
        
        # Handle values
        if best is None: # Best is not supplied, so use high and low, e.g. Val(low=0.2, high=0.4)
            if low is None or high is None:
                errormsg = 'If not supplying a best value, you must supply both low and high values'
                raise OptimaException(errormsg)
            else:
                best = (low+high)/2. # Take the average
        elif isinstance(best, dict):
            self.update(**best) # Assume it's a dict of args, e.g. Val({'best':0.3, 'low':0.2, 'high':0.4})
        else: # Best is supplied
            best = promotetoarray(best)
            if len(best)==1: # Only a single value supplied, e.g. Val(0.3)
                best = best[0] # Convert back to number
                if low is None: low = best # If these are missing, just replace them with best
                if high is None: high = best
            elif len(best)==2: # If length 2, assume high-low supplied, e.g. Val([0.2, 0.4])
                if low is not None and high is not None:
                    errormsg = 'If first argument has length 2, you cannot supply high and low values'
                    raise OptimaException(errormsg)
                low = best[0]
                high = best[1]
                best = (low+high)/2.
            elif len(best)==3: # Assume it's called like Val([0.3, 0.2, 0.4])
                low, best, high = sorted(best) # Allows values to be provided in any order
            else:
                errormsg = 'Could not understand input of best=%s, low=%s, high=%s' % (best, low, high)
                raise OptimaException(errormsg)
        
        # Handle distributions
        validdists = ['uniform']
        if dist is None: dist = validdists[0]
        if dist not in validdists:
            errormsg = 'Distribution "%s" not valid; choices are: %s' % (dist, validdists)
            raise OptimaException(errormsg) 
        
        # Store values
        self.best = best
        self.low  = low
        self.high = high
        self.dist = dist
        if not low<=best<=high:
            errormsg = 'Values are out of order (check that low=%s <= best=%s <= high=%s)' % (low, best, high)
            raise OptimaException(errormsg) 
        
        return None
    
    
    def get(self, what=None, n=1):
        '''
        Get the value from this distribution. Examples (with best=0.3, low=0.2, high=0.4):
        
        val.get() # returns 0.3
        val.get('best') # returns 0.3
        val.get(['low', 'best',' high']) # returns [0.2, 0.3, 0.4]
        val.get('rand') # returns, say, 0.3664
        val.get('all') # returns [0.3, 0.2, 0.4]
        
        The seed() call should ensure pseudorandomness.
        '''
        
        if what is None or what is 'best': val = self.best# Haha this is funny but works
        elif what is 'low':                val = self.low
        elif what is 'high':               val = self.high
        elif what is 'all':                val = [self.best, self.low, self.high]
        elif what in ['rand','random']:
            seed(get_state()[1][0])
            if self.dist=='uniform':       val = uniform(low=self.low, high=self.high, size=n)
            else:
                errormsg = 'Distribution %s is not implemented, sorry' % self.dist
                raise OptimaException(errormsg)
        elif type(what)==list:             val = [self.get(wh) for wh in what]# Allow multiple values to be used
        else:
            errormsg = 'Could not understand %s, expecting a string or list' % what
            raise OptimaException(errormsg)
        return val
    
    
