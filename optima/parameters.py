"""
This module defines the Constant, Metapar, Timepar, and Popsizepar classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, the Parameterset class.

Version: 2.1 (2017apr04)
"""

from numpy import array, nan, isnan, isfinite, zeros, ones, argmax, mean, log, polyfit, exp, maximum, minimum, Inf, linspace, median, shape, append, logical_and, isin, multiply
from numpy.random import uniform, normal, seed
from optima import OptimaException, version, compareversions, Link, odict, dataframe, printv, sanitize, uuid, today, getdate, makefilepath, smoothinterp, dcp, defaultrepr, isnumber, findinds, findnearest, getvaliddata, promotetoarray, promotetolist, inclusiverange # Utilities
from optima import Settings, getresults, convertlimits, gettvecdt, loadpartable, loadtranstable # Heftier functions
import optima as op
from sciris import cp

defaultsmoothness = 1.0 # The number of years of smoothing to do by default
generalkeys = ['male', 'female', 'popkeys', 'injects', 'fromto', 'transmatrix'] # General parameter keys that are just copied
staticmatrixkeys = ['birthtransit','agetransit','risktransit'] # Static keys that are also copied, but differently :)

# WARNING: the parameters that override one another are hardcoded here.
# If more parameters are added that override others or if model.py is changed, they should be added here
overridingpars = odict([('propdx',['hivtest','aidstest']),
                        ('propcare',['linktocare','aidslinktocare','leavecare','aidsleavecare','returntocare','aidstest']),
                        ('proptx',['numtx']),
                        ('propsupp',['treatfail','regainvs','numvlmon']),
                        ('proppmtct',['numpmtct']),
                        ('fixpropdx',['hivtest','aidstest']),
                        ('fixpropcare',['linktocare','aidslinktocare','leavecare','aidsleavecare','returntocare','aidstest']),
                        ('fixproptx',['numtx']),
                        ('fixpropsupp',['treatfail','regainvs','numvlmon']),
                        ('fixproppmtct',['numpmtct']) ])


#################################################################################################################################
### Define the parameter set
#################################################################################################################################



class Parameterset(object):
    ''' Class to hold all parameters and information on how they were generated, and perform operations on them'''
    
    def __init__(self, name='default', project=None, progsetname=None, budget=None, start=None, end=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uid = uuid() # ID
        self.projectref = Link(project) # Store pointer for the project, if available
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.pars = None
        self.popkeys = [] # List of populations
        self.posterior = odict() # an odict, comparable to pars, for storing posterior values of m -- WARNING, not used yet
        self.resultsref = None # Store pointer to results
        self.progsetname = progsetname # Store the name of the progset that generated the parset, if any
        self.budget = budget # Store the budget that generated the parset, if any
        self.start = start # Store the startyear of the parset
        self.end = end # Store the endyear of the parset
        self.isfixed = None # Store whether props are fixed or not
        
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output  = defaultrepr(self)
        output += 'Parameter set name: %s\n'    % self.name
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '============================================================\n'
        return output
    
    
    def getresults(self, die=True):
        ''' Method for getting the results '''
        if self.resultsref is not None and self.projectref() is not None:
            results = getresults(project=self.projectref(), pointer=self.resultsref, die=die)
            return results
        else:
            raise OptimaException('No results associated with this parameter set')
    
    
    def getcovpars(self):
        '''Method for getting a list of coverage-only parameters'''
        coveragepars = [par.short for par in self.pars.values() if isinstance(par, Par) and par.iscoveragepar()]
        return coveragepars


    def getprogdefaultpars(self):
        '''Method for getting a list of parameters that have defaults when there are no parameters'''
        progdefaultpars = [par.short for par in self.pars.values() if isinstance(par, Par) and par.isprogdefaultpar()]
        return progdefaultpars


    def parkeys(self):
        ''' Return a list of the keys in pars that are actually parameter objects '''
        parslist = []
        for key,par in self.pars.items():
            if issubclass(type(par), Par):
                parslist.append(key)
        return parslist
    
    
    def makepars(self, data=None, fix=True, verbose=2, start=None, end=None):
        self.pars = makepars(data=data, verbose=verbose) # Initialize as list with single entry
        self.fixprops(fix=fix)
        self.popkeys = dcp(self.pars['popkeys']) # Store population keys more accessibly
        if start is None: self.start = data['years'][0] # Store the start year -- if not supplied, use beginning of data
        else:             self.start = start
        if end is None:   self.end   = Settings().endyear # Store the end year -- if not supplied, use default
        else:             self.end   = end
        return None


    def interp(self, keys=None, start=None, end=2030, dt=0.2, tvec=None, smoothness=20, asarray=True, samples=None, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose),
        
        if start is None: start = self.start

        simparslist = []
        if isnumber(tvec): tvec = array([tvec]) # Convert to 1-element array -- WARNING, not sure if this is necessary or should be handled lower down
        if samples is None: samples = [None]
        for sample in samples:
            simpars = makesimpars(pars=self.pars, name=self.name, keys=keys, start=start, end=end, dt=dt, tvec=tvec, smoothness=smoothness, asarray=asarray, sample=sample, verbose=verbose)
            simparslist.append(simpars) # Wrap up
        
        return simparslist
    
    
    def updateprior(self):
        ''' Update the prior for all of the variables '''
        for key in self.parkeys():
            self.pars[key].updateprior()
        return None
    
    
    def fixprops(self, fix=None, which=None, startyear=None):
        '''
        Fix or unfix the proportions of people on ART and suppressed.
        
        To fix:   P.parset().fixprops()
        To unfix: P.parset().fixprops(False)
        
        You can also specify a start year. "which" can be a string
        or a list of strings, to specify which of ['dx','tx','supp','pmtct','care']
        you want to fix.
        '''
        if fix is None:
            fix = True # By default, do fix
        self.isfixed = fix # Store fixed status
        if   which is None:  which = ['tx','supp','pmtct']
        elif which == 'all': which = ['dx','tx','supp','pmtct','care']
        else:                which = promotetolist(which)
        if startyear is None:
            if fix:  startyear = self.pars['numtx'].t['tot'][-1]
            else:    startyear = 2100
        if 'dx'    in which: self.pars['fixpropdx'].t    = startyear
        if 'tx'    in which: self.pars['fixproptx'].t    = startyear
        if 'supp'  in which: self.pars['fixpropsupp'].t  = startyear # Doesn't make sense to assume proportion on treatment without assuming proportion suppressed....also, crashes otherwise :)
        if 'pmtct' in which: self.pars['fixproppmtct'].t = startyear
        if 'care'  in which: self.pars['fixpropcare'].t  = startyear
        return None
        
    
    def usedataprops(self, use=None, which=None):
        '''
        Use the data in the Optional indicators tab to create parameters for proportions of people in cascade stages
        
        To fix:   P.parset().usedataprops()
        To unfix: P.parset().usedataprops(False)
        To fix specific props:   P.parset().usedataprops('supp')

        '''
        if use is None: use = True # By default, use the data
        if   which is None:  which = ['supp'] # By default, only use the indicator on the proportion suppressed
        elif which == 'all': which = ['dx','tx','supp']
        else:                which = promotetolist(which)
        
        data = self.projectref().data
        if use:
            for key in which:
                tmp = data2timepar(data=data['optprop'+key], years=data['years'], keys=self.pars['prop'+key].t.keys(), name='tmp', short='tmp')
                self.pars['prop'+key].y = tmp.y
                self.pars['prop'+key].t = tmp.t
        else:
            for key in which:
                self.pars['prop'+key].y[0] = array([nan])
                self.pars['prop'+key].t[0] = array([0.0])

        return None


    def printpars(self, output=False):
        outstr = ''
        count = 0
        for par in self.pars.values():
            if hasattr(par,'p'): print('WARNING, population size not implemented!')
            if hasattr(par,'y'):
                if hasattr(par.y, 'keys'):
                    count += 1
                    if len(par.keys())>1:
                        outstr += '%3i: %s\n' % (count, par.name)
                        for key in par.keys():
                            outstr += '     %s = %s\n' % (key, par.y[key])
                    elif len(par.keys())==1:
                        outstr += '%3i: %s = %s\n\n' % (count, par.name, par.y[0])
                    elif len(par.keys())==0:
                        outstr += '%3i: %s = (empty)' % (count, par.name)
                    else:
                        print('WARNING, not sure what to do with %s: %s' % (par.name, par.y))
                else:
                    count += 1
                    outstr += '%3i: %s = %s\n\n' % (count, par.name, par.y)
        print(outstr)
        if output: return outstr
        else: return None


    def listattributes(self):
        ''' Go through all the parameters and make a list of their possible attributes '''
        
        maxlen = 20
        pars = self.pars
        
        print('\n\n\n')
        print('CONTENTS OF PARS, BY TYPE:')
        partypes = []
        for key in pars: partypes.append(type(pars[key]))
        partypes = set(partypes)
        count1 = 0
        count2 = 0
        for partype in set(partypes): 
            count1 += 1
            print('  %i..%s' % (count1, str(partype)))
            for key in pars:
                if type(pars[key])==partype:
                    count2 += 1
                    print('      %i.... %s' % (count2, str(key)))
        
        print('\n\n\n')
        print('ATTRIBUTES:')
        attributes = {}
        for key in self.parkeys():
            theseattr = list(pars[key].__dict__.keys())
            for attr in theseattr:
                if attr not in attributes.keys(): attributes[attr] = []
                attributes[attr].append(getattr(pars[key], attr))
        for key in attributes:
            print('  ..%s' % key)
        print('\n\n')
        for key in attributes:
            count = 0
            print('  ..%s' % key)
            items = []
            for item in attributes[key]:
                try: 
                    string = str(item)
                    if string not in items: 
                        if len(string)>maxlen: string = string[:maxlen]
                        items.append(string) 
                except: 
                    items.append('Failed to append item')
            for item in items:
                count += 1
                print('      %i....%s' % (count, str(item)))
        return None


    def manualfitlists(self, parsubset=None, advanced=None):
        ''' WARNING -- not sure if this function is needed; if it is needed, it should be combined with manualgui,py '''
        if not self.pars:
            raise OptimaException("No parameters available!")
    
        # Check parname subset is valid
        if parsubset is None:
            tmppars = self.pars
        else:
            if type(parsubset)==str: parsubset=[parsubset]
            if parsubset and type(parsubset) not in (list, str):
                raise OptimaException("Expecting parsubset to be a list or a string!")
            for item in parsubset:
                if item not in [par.short for par in self.pars.values() if hasattr(par,'manual') and par.manual!='no']:
                    raise OptimaException("Parameter %s is not a manual parameter.")
            tmppars = {par.short:par for par in self.pars.values() if hasattr(par,'manual') and par.manual!='no' and par.short in parsubset}
            
        mflists = {'keys': [], 'subkeys': [], 'types': [], 'values': [], 'labels': []}
        keylist = mflists['keys']
        subkeylist = mflists['subkeys']
        typelist = mflists['types']
        valuelist = mflists['values']
        labellist = mflists['labels']
        
        for key in tmppars.keys():
            par = tmppars[key]
            if hasattr(par, 'manual') and par.manual != 'no':  # Don't worry if it doesn't work, not everything in tmppars is actually a parameter
                if par.manual=='meta':
                    if advanced: # By default, don't include these
                        keylist.append(key)
                        subkeylist.append(None)
                        typelist.append('meta')
                        valuelist.append(par.m)
                        labellist.append('%s: meta' % par.name)
                elif par.manual=='const':
                    keylist.append(key)
                    subkeylist.append(None)
                    typelist.append('const')
                    valuelist.append(par.y)
                    labellist.append(par.name)
                elif par.manual=='advanced': # These are also constants, but skip by default
                    if advanced:
                        keylist.append(key)
                        subkeylist.append(None)
                        typelist.append('const')
                        valuelist.append(par.y)
                        labellist.append(par.name)
                elif par.manual=='year':
                    keylist.append(key)
                    subkeylist.append(None)
                    typelist.append('year')
                    valuelist.append(par.t)
                    labellist.append(par.name)
                elif par.manual=='pop':
                    for subkey in par.keys():
                        keylist.append(key)
                        subkeylist.append(subkey)
                        typelist.append('pop')
                        valuelist.append(par.y[subkey])
                        labellist.append('%s: %s' % (par.name, str(subkey)))
                elif par.manual=='exp':
                    for subkey in par.keys():
                        keylist.append(key)
                        subkeylist.append(subkey)
                        typelist.append('exp')
                        valuelist.append(par.y[subkey][0]) #Initial population size - editing exponent would be more useful but runs into negative numbers that the FE doesn't like as they're outside of the parameter bounds
                        labellist.append('%s: %s' % (par.name, str(subkey)))
                else:
                    print('Parameter type "%s" not implemented!' % par.manual)
    
        return mflists
    
    
    ## Define update step
    def update(self, mflists, verbose=2):
        ''' Update Parameterset with new results -- WARNING, duplicates the function in gui.py!!!! '''
        if not self.pars:
            raise OptimaException("No parameters available!")
    
        tmppars = self.pars
    
        keylist    = mflists['keys']
        subkeylist = mflists['subkeys']
        typelist   = mflists['types']
        valuelist  = mflists['values']
        
        ## Loop over all parameters and update them
        for (key, subkey, ptype, value) in zip(keylist, subkeylist, typelist, valuelist):
            if ptype=='meta':  # Metaparameters
                tmppars[key].m = float(value)
                printv('%s.m = %s' % (key, value), 4, verbose)
            elif ptype=='pop':  # Populations or partnerships
                tmppars[key].y[subkey] = float(value)
                printv('%s.y[%s] = %s' % (key, subkey, value), 4, verbose)
            elif ptype=='exp':  # Population growth
                tmppars[key].y[subkey] = float(value)
                printv('%s.y[%s] = %s' % (key, subkey, value), 4, verbose)
            elif ptype in ['const', 'advanced']:  # Constants
                tmppars[key].y = float(value)
                printv('%s.y = %s' % (key, value), 4, verbose)
            elif ptype=='year':  # Year parameters
                tmppars[key].t = float(value)
                printv('%s.t = %s' % (key, value), 4, verbose)
            else:
                errormsg = 'Parameter type "%s" not implemented!' % ptype
                raise OptimaException(errormsg)
    
                # parset.interp() and calculate results are supposed to be called from the outside
    
    def export(self, filename=None, folder=None, compare=None):
        '''
        Little function to export code for the current parameter set. To use, do something like:
        
        pars = P.pars()
        
        and then paste in the output of this function.
        
        If compare is not None, then only print out parameter values that differ. Most useful for
        comparing to default, e.g.
        P.parsets[-1].export(compare='default')
        '''
        cpars, cvalues = None, None
        if compare is not None:
            try: 
                cpars = self.projectref().parsets[compare].pars
            except: 
                print('Could not compare parset %s to parset %s; printing all parameters' % (self.name, compare))
                compare = None
        
        def oneline(values): return str(values).replace('\n',' ') 
        
        output = ''
        for parname,par in self.pars.items():
            prefix2 = None # Handle the fact that some parameters need more than one line to print
            values2 = None
            cvalues2 = None
            if hasattr(par,'manual'):
                if par.manual=='pop': 
                    values = par.y[:].tolist()
                    prefix = "pars['%s'].y[:] = " % parname
                    if cpars is not None: cvalues = cpars[parname].y[:].tolist()
                elif par.manual in ['const', 'advanced']: 
                    values = par.y
                    prefix = "pars['%s'].y = " % parname
                    if cpars is not None: cvalues = cpars[parname].y
                elif par.manual=='year': 
                    values = par.t
                    prefix = "pars['%s'].t = " % parname
                    if cpars is not None: cvalues = cpars[parname].t
                elif par.manual=='meta':
                    values = par.m
                    prefix = "pars['%s'].m = " % parname
                    if cpars is not None: cvalues = cpars[parname].m
                elif par.manual=='exp':
                    values = par.y[:].tolist()
                    prefix = "pars['%s'].y[:] = " % parname
                    
                    values2 = par.e[:].tolist()
                    prefix2 = "pars['%s'].e[:] = " % parname
                    if cpars is not None: 
                        cvalues  = cpars[parname].y[:].tolist()
                        cvalues2 = cpars[parname].e[:].tolist()
                elif par.manual=='no':
                    values = None
                else: 
                    print('Parameter manual type "%s" not implemented' % par.manual)
                    values = None
                if values is not None:
                    if compare is None or (values!=cvalues) or (values2!=cvalues2):
                        output += prefix+oneline(values)+'\n'
                        if prefix2 is not None:
                            output += prefix2+oneline(values2)+'\n'
        
        if filename is not None:
            fullpath = makefilepath(filename=filename, folder=folder, default=self.name, ext='par')
            with open(fullpath, 'w') as f:
                f.write(output)
            return fullpath
        else:
            return output






#################################################################################################################################
### Define the other classes
#################################################################################################################################

class Par(object):
    '''
    The base class for epidemiological model parameters.
    
    There are four subclasses:
        * Constant objects store a single scalar value in y and an uncertainty sample in ysample -- e.g., transmfi
        * Metapar objects store an odict of y values, have a single metaparameter m, and an odict of ysample -- e.g., force
        * Timepar objects store an odict of y values, have a single metaparameter m, and uncertainty scalar msample -- e.g., condcas
        * Popsizepar objects are like Timepar objects except have odicts of i (intercept) and e (exponent) values
        * Yearpar objects store a single time value -- e.g., fixpropdx
    
    These four thus have different structures (where [] denotes dict):
        * Constants   have y, ysample
        * Metapars    have y[], ysample[], m, msample
        * Timepars    have y[], t[], m, msample
        * Popsizepars have y[], t[], start[], e[], m, msample
        * Yearpars    have t
    
    Consequently, some of them have different sample(), updateprior(), and interp() methods; in brief:
        * Constants have sample() = ysample, interp() = y
        * Metapars have sample() = ysample[], interp() = m*y[] if usemeta=True, else y[]
        * Timepars have sample() = msample, interp() = m*y[] if usemeta=True, else y[]
        * Popsizepars have sample() = msample, interp() = m*i[]*exp(e[]) if usemeta=True, else i[]*exp(e[])
        * Yearpars have no sampling methods, and interp() = t
    
    Version: 2016nov06 
    '''
    def __init__(self, short=None, name=None, limits=(0.,1.), by=None, manual='', fromdata=None, m=1.0, progdefault=None, prior=None, verbose=None, **defaultargs): # "type" data needed for parameter table, but doesn't need to be stored
        ''' To initialize with a prior, prior should be a dict with keys 'dist' and 'pars' '''
        self.short = short # The short name, e.g. "hivtest"
        self.name = name # The full name, e.g. "HIV testing rate"
        self.limits = limits # The limits, e.g. (0,1) -- a tuple since immutable
        self.by = by # Whether it's by population, partnership, or total
        self.manual = manual # Whether or not this parameter can be manually fitted: options are '', 'meta', 'pop', 'exp', etc...
        self.fromdata = fromdata # Whether or not the parameter is made from data
        self.progdefault = progdefault # Whether or not the parameter has a default value when not targeted by programs
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.msample = None # The latest sampled version of the metaparameter -- None unless uncertainty has been run, and only used for uncertainty runs 
        if prior is None:             self.prior = Dist() # Not supplied, create default distribution
        elif isinstance(prior, dict): self.prior = Dist(**prior) # Supplied as a dict, use it to create a distribution
        elif isinstance(prior, Dist): self.prior = prior # Supplied as a distribution, use directly
        else:
            errormsg = 'Prior must either be None, a Dist, or a dict with keys "dist" and "pars", not %s' % type(prior)
            raise OptimaException(errormsg)
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output
    
    def iscoveragepar(self):
        ''' Determine whether it's a coverage parameter'''
        return True if self.limits[1] == 'maxpopsize' else False

    def isprogdefaultpar(self):
        ''' Determine whether it's a parameter that has a default value when there are no programs targeting it'''
        return True if self.progdefault is not None else False


class Constant(Par):
    ''' The definition of a single constant parameter, which may or may not vary by population '''
    
    def __init__(self, y=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        del self.m # These don't exist for the Constant class
        del self.msample 
        self.y = y # y-value data, e.g. 0.3
        self.ysample = None # y-value data generated from the prior, e.g. 0.24353
    
    def keys(self):
        ''' Constants don't have any keys '''
        return None 
    
    def sample(self, randseed=None):
        ''' Recalculate ysample '''
        self.ysample = self.prior.sample(n=1, randseed=randseed)[0]
        return None
    
    def updateprior(self, verbose=2):
        ''' Update the prior parameters to match the metaparameter, so e.g. can recalibrate and then do uncertainty '''
        if self.prior.dist=='uniform':
            tmppars = array(self.prior.pars) # Convert to array for numerical magic
            priorrange = array((0.9, 1.1)) if (tmppars == (0., 0.)).all() else tmppars/(tmppars.mean())
            self.prior.pars = tuple(self.y*priorrange) # Recenter the limits around the mean
            printv('Priors updated for %s' % self.short, 3, verbose)
        else:
            errormsg = 'Distribution "%s" not defined; available choices are: uniform or bust, bro!' % self.dist
            raise OptimaException(errormsg)
        return None
    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=False, randseed=None, usemeta=True, popkeys=None): # Keyword arguments are for consistency but not actually used
        """
        Take parameters and turn them into model parameters -- here, just return a constant value at every time point
        
        There are however 3 options with the interpolation:
            * False -- use existing y value
            * 'old' -- use existing ysample value
            * 'new' -- recalculate ysample value
        """
        # Figure out sample
        if not sample: 
            y = self.y
        else:
            if sample=='new' or self.ysample is None: self.sample(randseed=randseed) # msample doesn't exist, make it
            y = self.ysample
            
        # Do interpolation
        dt = gettvecdt(tvec=tvec, dt=dt, justdt=True) # Method for getting dt
        output = applylimits(par=self, y=y, limits=self.limits, dt=dt)
        if not asarray: output = odict([('tot',output)])
        return output



class Metapar(Par):
    ''' The definition of a single metaparameter, such as force of infection, which usually does vary by population '''

    def __init__(self, y=None, prior=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        self.y = y # y-value data, e.g. {'FSW:'0.3, 'MSM':0.7}
        self.ysample = None
        if isinstance(prior, dict):
            self.prior = prior
        elif prior is None:
            self.prior = odict()
            for key in self.keys():
                self.prior[key] = Dist() # Initialize with defaults
        else:
            errormsg = 'Prior for metaparameters must be an odict, not %s' % type(prior)
            raise OptimaException(errormsg)
            
    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.y.keys()
    
    def sample(self, randseed=None):
        ''' Recalculate ysample '''
        self.ysample = odict()
        for key in self.keys():
            self.ysample[key] = self.prior[key].sample(randseed=randseed)[0]
        return None
    
    def updateprior(self, verbose=2):
        ''' Update the prior parameters to match the y values, so e.g. can recalibrate and then do uncertainty '''
        for key in self.keys():
            if self.prior[key].dist=='uniform':
                tmppars = array(self.prior[key].pars) # Convert to array for numerical magic
                priorrange = array((0.9, 1.1)) if (tmppars == (0., 0.)).all() else tmppars/(tmppars.mean())
                self.prior[key].pars = tuple(self.y[key]*priorrange) # Recenter the limits around the mean
                printv('Priors updated for %s' % self.short, 3, verbose)
            else:
                errormsg = 'Distribution "%s" not defined; available choices are: uniform or bust, bro!' % self.dist
                raise OptimaException(errormsg)
        return None
    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None, randseed=None, usemeta=True, popkeys=None): # Keyword arguments are for consistency but not actually used
        """ Take parameters and turn them into model parameters -- here, just return a constant value at every time point """
        
        # Figure out sample
        if not sample: 
            y = self.y
        else:
            if sample=='new' or self.ysample is None: self.sample(randseed=randseed) # msample doesn't exist, make it
            y = self.ysample
                
        dt = gettvecdt(tvec=tvec, dt=dt, justdt=True) # Method for getting dt
        outkeys = getoutkeys(self, popkeys) # Get the list of keys for the output
        if asarray: output = zeros(len(outkeys))
        else: output = odict()
        meta = self.m if usemeta else 1.0

        for pop,key in enumerate(outkeys): # Loop over each population, always returning an [npops x npts] array
            if key in self.keys(): yval = y[key]*meta
            else:                  yval = 0. # Population not present, set to zero
            yinterp = applylimits(par=self, y=yval, limits=self.limits, dt=dt) 
            if asarray: output[pop] = yinterp
            else:       output[key] = yinterp
        return output
    


class Timepar(Par):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, t=None, y=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        if t is None: t = odict()
        if y is None: y = odict()
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]

    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.y.keys()
    
    def df(self, key=None, data=None):
        '''
        Return t,y data as a data frame; or if data is supplied, replace current t,y values.
        Example: use df() to export data, work with it as a dataframe, and then import it back in:
        aidstest = P.pars()['aidstest'].df()
        aidstest.addrow([2005, 0.3])
        P.pars()['aidstest'].df(data=aidstest)
        '''
        if key is None: key = self.keys()[0] # Pull out first key if not specified -- e.g., 'tot'
        output = dataframe(['t','y'], [self.t[key], self.y[key]])
        if data is not None:
            if isinstance(data, dataframe):
                self.t[key] = array(data['t'],dtype=float)
                self.y[key] = array(data['y'],dtype=float)
            else:
                errormsg = 'Data argument must be a dataframe, not "%s"' % type(data)
                raise OptimaException(errormsg)
            return None
        else:
            return output
    
    def sample(self, randseed=None):
        ''' Recalculate msample '''
        self.msample = self.prior.sample(n=1, randseed=randseed)[0]
        return None
    
    def updateprior(self, verbose=2):
        ''' Update the prior parameters to match the metaparameter, so e.g. can recalibrate and then do uncertainty '''
        if self.prior.dist=='uniform':
            tmppars = array(self.prior.pars) # Convert to array for numerical magic
            self.prior.pars = tuple(self.m*tmppars/tmppars.mean()) # Recenter the limits around the mean
            printv('Priors updated for %s' % self.short, 3, verbose)
        else:
            errormsg = 'Distribution "%s" not defined; available choices are: uniform or bust, bro!' % self.dist
            raise OptimaException(errormsg)
        return None
    
    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None, randseed=None, usemeta=True, popkeys=None):
        """ Take parameters and turn them into model parameters """
        
        # Validate input
        if tvec is None: 
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        if smoothness is None: smoothness = int(defaultsmoothness/dt) # Handle smoothness
        outkeys = getoutkeys(self, popkeys) # Get the list of keys for the output
        
        # Figure out metaparameter
        if not usemeta:
            meta = 1.0
        else:
            if not sample:
                meta = self.m
            else:
                if sample=='new' or self.msample is None: self.sample(randseed=randseed) # msample doesn't exist, make it
                meta = self.msample
        
        # Set things up and do the interpolation
        npops = len(outkeys)
        if self.by=='pship': asarray= False # Force odict since too dangerous otherwise
        if asarray: output = zeros((npops,len(tvec)))
        else:       output = odict()

        for pop,key in enumerate(outkeys): # Loop over each population, always returning an [npops x npts] array
            if key in self.keys():
                yinterp = meta * smoothinterp(tvec, self.t[key], self.y[key], smoothness=smoothness) # Use interpolation
                yinterp = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
            else:
                yinterp = zeros(len(tvec)) # Population not present, just set to zero
            if asarray: output[pop,:] = yinterp
            else:       output[key]   = yinterp
        if npops==1 and self.by=='tot' and asarray: return output[0,:] # npops should always be 1 if by==tot, but just be doubly sure
        else: return output



class Popsizepar(Par):
    ''' The definition of the population size parameter '''
    
    def __init__(self, e=None, m=1.0, start=None, t=None, y=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        if e is None: e = odict()
        if t is None: t = odict()
        if y is None: y = odict()
        if start is None: start = odict()
        self.e = e # Exponential fit exponent, e.g. 0.03
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.start = start # Year for which population growth start is calibrated : this is the year that exponential population growth starts; before this exact (interpolated) data values are assumed to be correct
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Population sizes, e.g. [2002, 2008]
    
    def keys(self):
        ''' Return the valid keys for using with this parameter '''
        return self.y.keys()
    
    def sample(self, randseed=None):
        ''' Recalculate msample -- same as Timepar'''
        self.msample = self.prior.sample(n=1, randseed=randseed)[0]
        return None
    
    def updateprior(self, verbose=2):
        ''' Update the prior parameters to match the metaparameter -- same as Timepar '''
        if self.prior.dist=='uniform':
            tmppars = array(self.prior.pars) # Convert to array for numerical magic
            self.prior.pars = tuple(self.m*tmppars/tmppars.mean()) # Recenter the limits around the mean
            printv('Priors updated for %s' % self.short, 3, verbose)
        else:
            errormsg = 'Distribution "%s" not defined; available choices are: uniform or bust, bro!' % self.dist
            raise OptimaException(errormsg)
        return None

    def interp(self, tvec=None, dt=None, smoothness=None, asarray=True, sample=None, randseed=None, usemeta=True, popkeys=None): # WARNING: smoothness isn't used, but kept for consistency with other methods...
        """ Take population size parameter and turn it into a model parameters """

        # Validate input
        if tvec is None: #Warning, may be able to send an empty list/array here instead?
            errormsg = 'Cannot interpolate parameter "%s" with no time vector specified' % self.name
            raise OptimaException(errormsg)
        tvec, dt = gettvecdt(tvec=tvec, dt=dt) # Method for getting these as best possible
        outkeys = getoutkeys(self, popkeys) # Get the list of keys for the output
        
        # Figure out metaparameter
        if not usemeta:
            meta = 1.0
        else:
            if not sample:
                meta = self.m
            else:
                if sample=='new' or self.msample is None: self.sample(randseed=randseed) # msample doesn't exist, make it
                meta = self.msample
                
                
        # Do interpolation
        npops = len(outkeys)
        if asarray: output = zeros((npops,len(tvec)))
        else: output = odict()
        for pop,key in enumerate(outkeys):
            if min(tvec) != self.start[key]:
                localtvec = linspace(self.t[key][0], max(tvec), (int(max(tvec)/dt)-int(self.t[key][0]/dt))+1) #TODO all populations should be precalculated somewhere else, going to be slow to keep regenerating this?
            else:
                localtvec = tvec
            
            if key in self.keys():
                # if self.start[key] == tvec[0]: #just apply the pure exponential growth
                #     yinterp= meta * self.y[key][0] * grow(self.e[key], array(tvec)-self.start[key]) 
                # else:
                #1. Linear interpolation between data points to tvec until self.forcegrowth[key]
                yinterp = meta * smoothinterp(localtvec, self.t[key], self.y[key], smoothness=0) # Use interpolation without smoothness so that it aligns exactly with a starting point for 
                #2. Replace linear interpolation after self.start
                expstartind = findnearest(localtvec, self.start[key])
                if compareversions(version,"2.12.0") < 0:  # old behaviour, the exponential is applied unnecessarily if only one t value is given
                    yinterp[expstartind:] = yinterp[expstartind] * grow(self.e[key], array(localtvec[expstartind:])-self.start[key]) #don't apply meta again (it's already factored into the linear part)
                else:  # New behaviour, exponential applied at the proper timestep
                    if abs(localtvec[expstartind] - self.start[key]) < dt: # Check localtvec[expstartind] is close enough to self.start[key], otherwise self.start[key] is not in localtvec
                        yinterp[expstartind:] = yinterp[expstartind] * grow(self.e[key], array(localtvec[expstartind:])-self.start[key]) #don't apply meta again (it's already factored into the linear part)
                #3. Apply limits
                yinterp = applylimits(par=self, y=yinterp, limits=self.limits, dt=dt)
            else:
                yinterp = zeros(len(tvec))

            yinterpreturn = yinterp[isin(localtvec,tvec)]
            
            if asarray: output[pop,:] = yinterpreturn
            else:       output[key] = yinterpreturn
        return output



class Yearpar(Par):
    ''' The definition of a single year parameter'''
    
    def __init__(self, t=None, **defaultargs):
        Par.__init__(self, **defaultargs)
        del self.m # These don't exist for this class
        del self.msample 
        self.prior = None
        self.t = t # y-value data, e.g. 0.3
    
    def keys(self):
        return None 
    
    def sample(self, randseed=None):
        ''' No sampling, so simply return the value '''
        return self.t
    
    def updateprior(self, verbose=2):
        '''No prior, so return nothing'''
        return None
    
    def interp(self, tvec=None, dt=None, smoothness=None, sample=None, randseed=None, asarray=True, usemeta=True, popkeys=None): # Keyword arguments are for consistency but not actually used
        '''No interpolation, so simply return the value'''
        return self.t



class Dist(object):
    ''' Define a distribution object for drawing samples from, usually to create a prior '''
    def __init__(self, dist=None, pars=None):
        self.dist = dist if dist is not None else 'uniform'
        self.pars = promotetoarray(pars) if pars is not None else array([0.9, 1.1]) # This is arbitrary, of course
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = defaultrepr(self)
        return output
    
    def sample(self, n=1, randseed=None):
        ''' Draw random samples from the specified distribution '''
        if randseed is not None: seed(randseed) # Reset the random seed, if specified
        if self.dist=='uniform':
            samples = uniform(low=self.pars[0], high=self.pars[1], size=n)
            return samples
        if self.dist=='normal':
            return normal(loc=self.pars[0], scale=self.pars[1], size=n)
        else:
            errormsg = 'Distribution "%s" not defined; available choices are: uniform, normal' % self.dist
            raise OptimaException(errormsg)



#############################################################################################################################
### Functions for handling the parameters
#############################################################################################################################

def getoutkeys(par=None, popkeys=None):
    ''' Small method to decide whether to return 'tot', a subset of population keys, or all population keys '''
    if par.by in ['mpop','fpop'] and popkeys is not None:
        return popkeys # Expand male or female only keys to all
    else:
        return par.keys() # Or just return the default
            

def grow(exponent, tvec):
    ''' Return a time vector for a population growth '''
    return exp(tvec*exponent) # Simple exponential growth


def getvalidyears(years, validdata, defaultind=0):
    ''' Return the years that are valid based on the validity of the input data '''
    if sum(validdata): # There's at least one data point entered
        if len(years)==len(validdata): # They're the same length: use for logical indexing
            validyears = array(array(years)[validdata]) # Store each year
        elif len(validdata)==1: # They're different lengths and it has length 1: it's an assumption
            validyears = array([array(years)[defaultind]]) # Use the default index; usually either 0 (start) or -1 (end)
    else: validyears = array([0.0]) # No valid years, return 0 -- NOT an empty array, as you might expect!
    return validyears



def data2prev(data=None, keys=None, index=0, blh=0, **defaultargs): # WARNING, "blh" means "best low high", currently upper and lower limits are being thrown away, which is OK here...?
    """ Take an array of data return either the first or last (...or some other) non-NaN entry -- used for initial HIV prevalence only so far... """
    par = Metapar(y=odict([(key,None) for key in keys]), **defaultargs) # Create structure -- need key:None for prior
    for row,key in enumerate(keys):
        par.y[key] = sanitize(data['hivprev'][blh][row])[index] # Return the specified index -- usually either the first [0] or last [-1]
        par.prior[key].pars *= par.y[key] # Get prior in right range
    return par



def data2popsize(data=None, keys=None, blh=0, uniformgrowth=False, doplot=False, **defaultargs):
    ''' Convert population size data into population size parameters '''
    par = Popsizepar(m=1, **defaultargs)
    
    # Parse data into consistent form
    sanitizedy = odict() # Initialize to be empty
    sanitizedt = odict() # Initialize to be empty
    for row,key in enumerate(keys):
        sanitizedy[key] = sanitize(data['popsize'][blh][row]) # Store each extant value
        sanitizedt[key] = array(data['years'])[~isnan(data['popsize'][blh][row])] # Store each year

        par.y[key] = sanitizedy[key]
        par.t[key] = sanitizedt[key]
    
    # Store a list of population sizes that have at least 2 data points
    atleast2datapoints = [] 
    for key in keys:
        if len(sanitizedy[key])>=2:
            atleast2datapoints.append(key)
    if len(atleast2datapoints)==0:
        errormsg = 'Not more than one data point entered for any population size\n'
        errormsg += 'To estimate growth trends, at least one population must have at least 2 data points'
        raise OptimaException(errormsg)
        
    largestpopkey = atleast2datapoints[argmax([mean(sanitizedy[key]) for key in atleast2datapoints])] # Find largest population size (for at least 2 data points)
    
    # Perform 2-parameter exponential fit to data
    startyear = data['years'][0]
    par.start = odict({pop: data['years'][0] for pop in keys})
    tdata = odict()
    ydata = odict()
    for key in atleast2datapoints:
        tdata[key] = sanitizedt[key]-startyear
        ydata[key] = log(sanitizedy[key])
        try:
            w = ones(shape(ydata[key])) #weighting for the data points
            if startyear in par.t[key] and par.t[key][0] == startyear: #we have a population size specified in the first year of data, so fit exponential growth from that
                ind = findnearest(par.t[key], startyear)    
                w[ind] = 100000
            
            fitpars = polyfit(tdata[key], ydata[key], 1, w=w)
            if not startyear in par.t[key]:
                par.t[key] = append([startyear], par.t[key])
                par.y[key] = append([exp(fitpars[1])], par.y[key]) # Intercept/initial value
            
            par.e[key] = fitpars[0] # Exponent
        except:
            errormsg = 'Fitting population size data for population "%s" failed' % key
            raise OptimaException(errormsg)
    
    # Handle populations that have only a single data point
    only1datapoint = list(set(keys)-set(atleast2datapoints))
    thisyear = odict()
    thispopsize = odict()
    for key in only1datapoint:
        largest_i = par.y[largestpopkey][0] # Get the parameters from the largest population
        largest_e = par.e[largestpopkey]
        if len(sanitizedt[key]) != 1:
            errormsg = 'Error interpreting population size for population "%s"\n' % key
            errormsg += 'Please ensure at least one time point is entered'
            raise OptimaException(errormsg)
        thisyear[key] = sanitizedt[key][0]
        thispopsize[key] = sanitizedy[key][0]
        largestthatyear = largest_i*grow(largest_e, thisyear[key]-startyear)
        par.y[key] = array([largest_i*thispopsize[key]/largestthatyear]) # Scale population size)
        par.t[key] = array([startyear])
        par.e[key] = largest_e # Copy exponent
    par.y.sort(keys) # Sort to regain the original key order -- WARNING, causes horrendous problems later if this isn't done!
    par.t.sort(keys)
    par.e.sort(keys)
    
    if uniformgrowth:
        for key in keys:
            par.e[key] = par.e[largestpopkey] # Reset exponent to match the largest population
            meanpopulationsize = mean(sanitizedy[key]) # Calculate the mean of all the data
            weightedyear = mean(sanitizedy[key][:]*sanitizedt[key][:])/meanpopulationsize # Calculate the "mean year"
            par.y[key] = array([meanpopulationsize*(1+par.e[key])**(startyear-weightedyear)]) # Project backwards to starting population size
            par.t[key] = array([startyear])
    
    for key in keys:
        par.y[key][0] = round(par.y[key][0]) # Fractional people look weird
        
    if doplot:
        from pylab import figure, subplot, plot, scatter, arange, show, title
        nplots = len(par.keys())
        figure()
        tvec = arange(data['years'][0], data['years'][-1]+1)
        yvec = par.interp(tvec=tvec)
        for k,key in enumerate(par.keys()):
            subplot(nplots,1,k+1)
            if key in atleast2datapoints: scatter(tdata[key]+startyear, exp(ydata[key]))
            elif key in only1datapoint: scatter(thisyear[key], thispopsize[key])
            else: raise OptimaException('This population is nonexistent')
            plot(tvec, yvec[k])
            title('Pop size: ' + key)
            print([par.y[key][0], par.e[key]])
            show()
    
    return par



def data2timepar(data=None, years=None, keys=None, defaultind=0, verbose=2, **defaultargs):
    """ Take an array of data and turn it into default parameters -- here, just take the means """
    # Check that at minimum, name and short were specified, since can't proceed otherwise
    try: 
        name, short = defaultargs['name'], defaultargs['short']
    except: 
        errormsg = 'Cannot create a time parameter without keyword arguments "name" and "short"! \n\nArguments:\n %s' % defaultargs.items()
        raise OptimaException(errormsg)

    # Process data
    if isinstance(data,dict): # The entire structure has been passed
        thisdata = data[short]
        years = data['years']
    elif isinstance(data,list): # Just the relevant entry has been passed
        thisdata = data
        
    par = Timepar(m=1.0, y=odict(), t=odict(), **defaultargs) # Create structure
    for row,key in enumerate(keys):
        try:
            validdata = ~isnan(thisdata[row]) # WARNING, this could all be greatly simplified!!!! Shouldn't need to call this and sanitize()
            par.t[key] = getvaliddata(years, validdata, defaultind=defaultind) 
            if sum(validdata): 
                par.y[key] = sanitize(thisdata[row])
            else:
                printv('data2timepar(): no data for parameter "%s", key "%s"' % (name, key), 3, verbose) # Probably ok...
                par.y[key] = array([0.0]) # Blank, assume zero -- WARNING, is this ok?
                par.t[key] = array([0.0])
        except:
            errormsg = 'Error converting time parameter "%s", key "%s"' % (name, key)
            printv(errormsg, 1, verbose)
            raise

    return par


## Acts
def balance(act=None, which=None, data=None, popkeys=None, fpopkeys=None, mpopkeys=None, limits=None, popsizepar=None, eps=None):
    ''' 
    Combine the different estimates for the number of acts or condom use and return the "average" value.
    
    Set which='numacts' to compute for number of acts, which='condom' to compute for condom.
    '''
    if eps is None: eps = Settings().eps   # If not supplied (it won't be), get from default settings  
    
    if which not in ['numacts','condom']: raise OptimaException('Can only balance numacts or condom, not "%s"' % which)
    mixmatrix = array(data['part'+act]) # Get the partnerships matrix
    npops = len(popkeys) # Figure out the number of populations
    symmetricmatrix = zeros((npops,npops));
    for pop1 in range(npops):
        for pop2 in range(npops):
            if which=='numacts': symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))
            if which=='condom': symmetricmatrix[pop1,pop2] = bool(symmetricmatrix[pop1,pop2] + mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1])

    if which == 'numacts' and act != 'inj': # Check for F->M acts and F->F acts
        for pop1 in range(npops):
            for pop2 in range(npops):
                if mixmatrix[pop1,pop2] > 0 and popkeys[pop1] in fpopkeys:
                    actname = 'Regular' if act == 'reg' else 'Casual' if act == 'cas' else 'Commercial'
                    pop2type = 'M' if popkeys[pop2] in mpopkeys else 'F'
                    print(f'\nWARNING!!: In the Partnerships & transitions sheet in the databook, there is a F->{pop2type} insertive partnership in the {actname} acts matrix from {popkeys[pop1]} to {popkeys[pop2]}')
                    if pop2type == 'M': print(f'This should normally go the other way around. So move the {mixmatrix[pop1, pop2]} from the ({popkeys[pop1]} row, {popkeys[pop2]} column) into the ({popkeys[pop2]} row, {popkeys[pop1]} column)')
                    print('If you don\'t adjust this, the model may not work properly!!\n')

    # Decide which years to use -- use the earliest year, the latest year, and the most time points available
    yearstouse = []    
    for row in range(npops): yearstouse.append(getvaliddata(data['years'], data[which+act][row]))
    minyear = Inf
    maxyear = -Inf
    npts = 1 # Don't use fewer than 1 point
    for row in range(npops):
        minyear = minimum(minyear, min(yearstouse[row]))
        maxyear = maximum(maxyear, max(yearstouse[row]))
        npts = maximum(npts, len(yearstouse[row]))
    if minyear==Inf:  minyear = data['years'][0] # If not set, reset to beginning
    if maxyear==-Inf: maxyear = data['years'][-1] # If not set, reset to end
    ctrlpts = linspace(minyear, maxyear, npts).round() # Force to be integer...WARNING, guess it doesn't have to be?
    
    # Interpolate over population acts data for each year
    tmppar = data2timepar(name='tmp', short=which+act, limits=(0,'maxacts'), data=data[which+act], years=data['years'], keys=popkeys, by='pop', verbose=0) # Temporary parameter for storing acts
    tmpsim = tmppar.interp(tvec=ctrlpts)
    if which=='numacts': popsize = popsizepar.interp(tvec=ctrlpts)
    npts = len(ctrlpts)
    
    # Compute the balanced acts
    output = zeros((npops,npops,npts))
    for t in range(npts):
        if which=='numacts':
            smatrix = dcp(symmetricmatrix) # Initialize
            psize = popsize[:,t]
            popacts = tmpsim[:,t]

            ## The below commented out code makes it so that the numbers in the Partnership matrices in the databook
            ## don't get multiplied by popsizes before being balanced
            # popsize_div_mean_2d = psize[:,None] / psize.max() # divide by max is just so numbers don't blow up / shrink causing roundoff errors
            # smatrix = smatrix / multiply(popsize_div_mean_2d,popsize_div_mean_2d.T) # divide the partnership a,b by the product of the popsizes a,b

            for pop1 in range(npops): smatrix[pop1,:] = smatrix[pop1,:]*psize[pop1] # Yes, this needs to be separate! Don't try to put in the next for loop, the indices are opposite!
            for pop1 in range(npops): smatrix[:,pop1] = psize[pop1]*popacts[pop1]*smatrix[:,pop1] / float(eps+sum(smatrix[:,pop1])) # Divide by the sum of the column to normalize the probability, then multiply by the number of acts and population size to get total number of acts
        
        # Reconcile different estimates of number of acts, which must balance
        balancedmatrix = zeros((npops, npops))
        proportioninsertive = zeros((npops, npops))
        thispoint = zeros((npops,npops));
        for pop1 in range(npops):
            for pop2 in range(npops):
                if compareversions(version,"2.12.0") >= 0: # New behaviour
                    if which=='numacts' and act != 'inj': # The total number of acts = insertive + receptive, we only keep insertive in actsreg etc
                        balancedmatrix[pop1,pop2] = (smatrix[pop1,pop2] * psize[pop1] + smatrix[pop2,pop1] * psize[pop2])/(psize[pop1]+psize[pop2]) # here are two estimates for each interaction; reconcile them here
                        proportioninsertive[pop1,pop2] = mixmatrix[pop1,pop2] / (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) \
                                                                if (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) > 0 else 1.
                        thispoint[pop1,pop2] = balancedmatrix[pop1,pop2] * proportioninsertive[pop1,pop2] / psize[pop1]
                    if which=='numacts' and act == 'inj': # We want the total number of acts = total number of injections, so we keep all
                        balanced = (smatrix[pop1,pop2] * psize[pop1] + smatrix[pop2,pop1] * psize[pop2])/(psize[pop1]+psize[pop2]) # here are two estimates for each interaction; reconcile them here
                        thispoint[pop1,pop2] = balanced/psize[pop1]
                else: # Old behaviour
                    if which=='numacts':
                        balanced = (smatrix[pop1,pop2] * psize[pop1] + smatrix[pop2,pop1] * psize[pop2])/(psize[pop1]+psize[pop2]) # here are two estimates for each interaction; reconcile them here
                        thispoint[pop2,pop1] = balanced/psize[pop2] # Divide by population size to get per-person estimate
                        thispoint[pop1,pop2] = balanced/psize[pop1] # ...and for the other population

                if which=='condom':
                    thispoint[pop1,pop2] = (tmpsim[pop1,t]+tmpsim[pop2,t])/2.0
                    thispoint[pop2,pop1] = thispoint[pop1,pop2]

        output[:,:,t] = thispoint
    
    return output, ctrlpts








def makepars(data=None, verbose=2, die=True, fixprops=None):
    """
    Translates the raw data (which were read from the spreadsheet) into
    parameters that can be used in the model. These data are then used to update 
    the corresponding model (project). This method should be called before a 
    simulation is run.
    
    Version: 2017jun03
    """
    
    printv('Converting data to parameters...', 1, verbose)
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    pars = odict()
    
    # Shorten information on which populations are male, which are female, which inject, which provide commercial sex
    pars['male'] = array(data['pops']['male']).astype(bool) # Male populations 
    pars['female'] = array(data['pops']['female']).astype(bool) # Female populations
    
    # Set up keys
    totkey = ['tot'] # Define a key for when not separated by population
    popkeys = data['pops']['short'] # Convert to a normal string and to lower case...maybe not necessary
    fpopkeys = [popkey for popno,popkey in enumerate(popkeys) if data['pops']['female'][popno]]
    mpopkeys = [popkey for popno,popkey in enumerate(popkeys) if data['pops']['male'][popno]]
    pars['popkeys'] = dcp(popkeys)
    pars['age'] = array(data['pops']['age'])
    
    
    # Read in parameters automatically
    try: 
        rawpars = loadpartable() # Read the parameters structure
    except OptimaException as E: 
        errormsg = 'Could not load parameter table: "%s"' % repr(E)
        raise OptimaException(errormsg)
        
    pars['fromto'], pars['transmatrix'] = loadtranstable(npops=len(popkeys)) # Read the transitions
        
    for rawpar in rawpars: # Iterate over all automatically read in parameters
        printv('Converting data parameter "%s"...' % rawpar['short'], 3, verbose)
        
        try: # Optionally keep going if some parameters fail
        
            # Shorten key variables
            partype = rawpar.pop('partype')
            parname = rawpar['short']
            by = rawpar['by']
            fromdata = rawpar['fromdata']
            rawpar['verbose'] = verbose # Easiest way to pass it in
            rawpar['progdefault'] = None if rawpar['progdefault'] == '' else rawpar['progdefault']

            # Decide what the keys are
            if   by=='tot' : keys = totkey
            elif by=='pop' : keys = popkeys
            elif by=='fpop': keys = fpopkeys
            elif by=='mpop': keys = mpopkeys
            else:            keys = [] # They're not necessarily empty, e.g. by partnership, but too complicated to figure out here
            
            # Decide how to handle it based on parameter type
            if partype=='initprev': # Initialize prevalence only
                pars['initprev'] = data2prev(data=data, keys=keys, **rawpar) # Pull out first available HIV prevalence point
            
            elif partype=='popsize': # Population size 
                pars['popsize'] = data2popsize(data=data, keys=keys, **rawpar)
            
            elif partype=='timepar': # Otherwise it's a regular time par, made from data
                domake = False # By default, don't make the parameter
                if by!='pship' and fromdata: domake = True # If it's not a partnership parameter and it's made from data, then make it
                if domake:
                    pars[parname] = data2timepar(data=data, keys=keys, **rawpar) 
                else:
                    pars[parname] = Timepar(y=odict([(key,array([nan])) for key in keys]), t=odict([(key,array([0.0])) for key in keys]), **rawpar) # Create structure
            
            elif partype=='constant': # The constants, e.g. transmfi
                best = data[parname][0] if fromdata else nan
                low = data[parname][1] if fromdata else nan
                high = data[parname][2] if fromdata else nan
                thisprior = {'dist':'uniform', 'pars':(low, high)} if fromdata else None
                pars[parname] = Constant(y=best, prior=thisprior, **rawpar)
            
            elif partype=='meta': # Force-of-infection, inhomogeneity, relative HIV-related death rates, and transitions
                pars[parname] = Metapar(y=odict([(key,None) for key in keys]), **rawpar)
                
            elif partype=='yearpar': # Years to fix proportions of people at different cascade stages
                pars[parname] = Yearpar(t=nan, **rawpar)
            
        except Exception as E:
            errormsg = 'Failed to convert parameter %s:\n%s' % (parname, repr(E))
            if die: raise OptimaException(errormsg)
            else: printv(errormsg, 1, verbose)

    
    ###############################################################################
    ## Tidy up -- things that can't be converted automatically
    ###############################################################################
    
    # Birth transitions - these are stored as the proportion of transitions, which is constant, and is multiplied by time-varying birth rates in model.py
    npopkeys = len(popkeys)
    birthtransit = zeros((npopkeys,npopkeys))
    c = 0
    for pkno,popkey in enumerate(popkeys):
        if data['pops']['female'][pkno]: # WARNING, really ugly
            for colno,col in enumerate(data['birthtransit'][c]):
                if sum(data['birthtransit'][c]):
                    birthtransit[pkno,colno] = col/sum(data['birthtransit'][c])
            c += 1
    pars['birthtransit'] = birthtransit 

    # Aging transitions - these are stored as the proportion of transitions, which is constant, and is multiplied by time-varying age rates in model.py
    agetransit = zeros((npopkeys,npopkeys))
    c = 0
    for pkno,popkey in enumerate(popkeys):
        for colno,col in enumerate(data['agetransit'][c]):
            if sum(data['agetransit'][c]):
                agetransit[pkno,colno] = col/sum(data['agetransit'][c])
        c += 1    
    pars['agetransit'] = agetransit

    # Risk transitions - these are time-constant
    pars['risktransit'] = array(data['risktransit'])
    
    # Circumcision
    for key in pars['numcirc'].keys():
        pars['numcirc'].y[key] = array([0.0]) # Set to 0 for all populations, since program parameter only
    
    # Fix treatment from final data year
    for key in ['fixproptx', 'fixpropsupp', 'fixpropdx', 'fixpropcare', 'fixproppmtct']:
        pars[key].t = 2100 # TODO: don't use these, so just set to (hopefully) well past the end of the analysis

    # Set the values of parameters that aren't from data
    pars['transnorm'].y = 0.43 # See analyses/misc/calculatecd4transnorm.py for calculation
    pars['transnorm'].prior.pars *= pars['transnorm'].y # Scale default range
    
    pars['forcepopsize'].y = 0 # Whether or not to force the population size to match the parameters
    pars['allcd4eligibletx'].t = 2100. # Whether or not to preferentially put people on treatment from lower CD4 counts - the final year of this
    pars['initcd4weight'].y = 1. # How to initialize the epidemic weighting either toward lower (with <1 values) or higher (with >1 values) CD4 counts based on the maturity of the epidemic
    pars['relhivbirth'].y = 1. # Relative likelihood that females with HIV give birth (relative to the overall birth rate)

    pars['rrcomorbiditydeathtx'].prior.pars = array([1.0, 1.0]) #Don't sample
    pars['forcepopsize'].prior.pars = array([0.0, 0.0]) #Don't sample
    
    for key in popkeys: # Define values for each population
        pars['force'].y[key] = 1.0
        pars['hivdeath'].y[key] = 1.0
        pars['inhomo'].y[key] = 0.0
        pars['inhomo'].prior[key].pars = array([0.0, 0.3]) # Arbitrary
        pars['rrcomorbiditydeathtx'].y[key] = 1.0
        
    # Impose limits on force and transnorm so their values don't get too extreme (note, force.m functions identically to transnorm.y, but use the latter)
    for foipar in ['force','transnorm']:
        pars[foipar].limits = (0.05, 50) # Arbitrary
    
    
    # Handle acts
    tmpacts = odict()
    tmpcond = odict()
    tmpactspts = odict()
    tmpcondpts = odict()
    for act in ['reg','cas','com', 'inj']: # Number of acts
        actsname = 'acts'+act
        tmpacts[act], tmpactspts[act] = balance(act=act, which='numacts', data=data, popkeys=popkeys, fpopkeys=fpopkeys, mpopkeys=mpopkeys, popsizepar=pars['popsize'])
    for act in ['reg','cas','com']: # Condom use
        condname = 'cond'+act
        tmpcond[act], tmpcondpts[act] = balance(act=act, which='condom', data=data, popkeys=popkeys, fpopkeys=fpopkeys, mpopkeys=mpopkeys)
        
    # Convert matrices to lists of of population-pair keys
    for act in ['reg', 'cas', 'com', 'inj']: # Will probably include birth matrices in here too...
        actsname = 'acts'+act
        condname = 'cond'+act
        for i,key1 in enumerate(popkeys):
            for j,key2 in enumerate(popkeys):
                if sum(array(tmpacts[act])[i,j,:])>0:
                    pars[actsname].y[(key1,key2)] = array(tmpacts[act])[i,j,:]
                    pars[actsname].t[(key1,key2)] = array(tmpactspts[act])
                    if act!='inj':
                        if (key2, key1) not in pars[condname].y.keys(): # For condom use, only store one of the pair
                            pars[condname].y[(key1,key2)] = array(tmpcond[act])[i,j,:]
                            pars[condname].t[(key1,key2)] = array(tmpcondpts[act])

    # Store information about injecting populations -- needs to be here since relies on other calculations
    pars['injects'] = array([pop in [pop1 for (pop1,pop2) in pars['actsinj'].keys()] for pop in pars['popkeys']])
    
    return pars

def getreceptiveactsfrominsertive(insertivepar, popsizetimes, popsizeinterped, popkeys, popsizeargs):
    receptivepar = cp(insertivepar)
    receptivepar.t = odict()
    receptivepar.y = odict()

    timeindsdict = {time:ind for ind, time in enumerate(popsizetimes)}

    for partnership, times in insertivepar.t.items():
        timeinds = [timeindsdict[time] for time in times]
        popsizeA = popsizeinterped[popkeys.index(partnership[0])][timeinds]
        popsizeB = popsizeinterped[popkeys.index(partnership[1])][timeinds]

        receptiveactsperB = insertivepar.y[partnership] * popsizeA / popsizeB
        reversedpartnership = (partnership[1], partnership[0])
        receptivepar.t[reversedpartnership] = times
        receptivepar.y[reversedpartnership] = receptiveactsperB

    return receptivepar



def makesimpars(pars, name=None, keys=None, start=None, end=None, dt=None, tvec=None, settings=None, smoothness=None, asarray=True, sample=None, tosample=None, randseed=None, verbose=2):
    ''' 
    A function for taking a single set of parameters and returning the interpolated versions -- used
    very directly in Parameterset.
    
    Version: 2017mar01
    '''
    
    # Handle inputs and initialization
    simpars = odict() 
    simpars['parsetname'] = name
    if keys is None: keys = list(pars.keys()) # Just get all keys
    if type(keys)==str: keys = [keys] # Listify if string
    if tvec is not None: simpars['tvec'] = tvec
    elif settings is not None: simpars['tvec'] = settings.maketvec(start=start, end=end, dt=dt)
    else: simpars['tvec'] = inclusiverange(start=start, stop=end, step=dt) # Store time vector with the model parameters
    if len(simpars['tvec'])>1: dt = simpars['tvec'][1] - simpars['tvec'][0] # Recalculate dt since must match tvec
    simpars['dt'] = dt  # Store dt
    if smoothness is None: smoothness = int(defaultsmoothness/dt)
    tosample = promotetolist(tosample) # Convert to list
    popkeys = pars['popkeys'] # Used for interpolation
    
    # Copy default keys by default
    for key in generalkeys: simpars[key] = dcp(pars[key])
    for key in staticmatrixkeys: simpars[key] = dcp(array(pars[key]))

    # Loop over requested keys
    for key in keys: # Loop over all keys
        if compareversions(version,"2.12.0") >= 0 and key in ['actsreg', 'actscas', 'actscom', 'actsreginsertive', 'actscasinsertive', 'actscominsertive', 'actsregreceptive', 'actscasreceptive', 'actscomreceptive']:
            continue  # New behaviour, the above pars are handled in the next loop
        if isinstance(pars[key], Par): # Check that it is actually a parameter -- it could be the popkeys odict, for example
            thissample = sample # Make a copy of it to check it against the list of things we are sampling
            if tosample and tosample[0] is not None and key not in tosample: thissample = False # Don't sample from unselected parameters -- tosample[0] since it's been promoted to a list
            try:
                simpars[key] = pars[key].interp(tvec=simpars['tvec'], dt=dt, popkeys=popkeys, smoothness=smoothness, asarray=asarray, sample=thissample, randseed=randseed)
            except OptimaException as E:
                errormsg = 'Could not figure out how to interpolate parameter "%s"' % key
                errormsg += 'Error: "%s"' % repr(E)
                raise OptimaException(errormsg)

    if compareversions(version,"2.12.0") >= 0:
        # Special treatment for actsreg, actscas, actscom because they contain only insertive acts and so we need to calculate the receptive acts
        # Get the popsize at the times when the acts are set. Need the popsize for the receptive act calculation
        alltimes = set()
        for key in ['actsreg', 'actscas', 'actscom']:
            for times in pars[key].t.values():
                alltimes.update(set(times))
        alltimes = array(sorted(list(alltimes)))

        popsizesample = sample
        if tosample and tosample[0] is not None and 'popsize' not in tosample: popsizesample = False

        if len(alltimes):
            popsizeinterped = pars['popsize'].interp(tvec=alltimes, dt=dt, popkeys=popkeys, smoothness=smoothness, asarray=True, sample=popsizesample, randseed=randseed)
        else: popsizeinterped = None

        for key in keys:
            if key in ['actsreg', 'actscas', 'actscom', 'actsreginsertive', 'actscasinsertive', 'actscominsertive', 'actsregreceptive', 'actscasreceptive', 'actscomreceptive']:
                if 'popsize' not in keys:
                    raise OptimaException(f'In order to makesimpars for "{key}", "popsize" needs to be in the keys to be included in the simpars.')
                key = key[0:7]

                insertivepar = pars[key]  # actsreg only contains insertive acts, eg. actsreg[(popA, popB)] = c is c insertive acts for each person in popA
                receptivepar = getreceptiveactsfrominsertive(insertivepar, alltimes, popsizeinterped, popkeys=popkeys, popsizeargs=popsizeargs)

                insertivekey = key + 'insertive'
                receptivekey = key + 'receptive'

                insertivesample, receptivesample = sample, sample
                if tosample and tosample[0] is not None: # We have a list of keys to check
                    thissample = key in tosample
                    insertivesample = thissample or insertivekey in tosample
                    receptivesample = thissample or receptivekey in tosample

                try:
                    simpars[insertivekey] = insertivepar.interp(sample=insertivesample, tvec=simpars['tvec'], dt=dt, popkeys=popkeys, smoothness=smoothness, asarray=asarray, randseed=randseed)
                    simpars[receptivekey] = receptivepar.interp(sample=receptivesample, tvec=simpars['tvec'], dt=dt, popkeys=popkeys, smoothness=smoothness, asarray=asarray, randseed=randseed)
                except OptimaException as E:
                    errormsg = 'Could not figure out how to interpolate parameter "%s"' % key
                    errormsg += 'Error: "%s"' % repr(E)
                    raise OptimaException(errormsg)


    return simpars




def applylimits(y, par=None, limits=None, dt=None, warn=True, verbose=2):
    ''' 
    A function to intelligently apply limits (supplied as [low, high] list or tuple) to an output.
    
    Needs dt as input since that determines maxrate.
    
    Version: 2016jan30
    '''
    
    # If parameter object is supplied, use it directly
    parname = ''
    if par is not None:
        if limits is None: limits = par.limits
        parname = par.name
        
    # If no limits supplied, don't do anything
    if limits is None:
        printv('No limits supplied for parameter "%s"' % parname, 4, verbose)
        return y
    
    if dt is None:
        if warn: raise OptimaException('No timestep specified: required for convertlimits()')
        else: dt = 0.2 # WARNING, should probably not hard code this, although with the warning, and being conservative, probably OK
    
    # Convert any text in limits to a numerical value
    limits = convertlimits(limits=limits, dt=dt, verbose=verbose)
    
    # Apply limits, preserving original class -- WARNING, need to handle nans
    if isnumber(y):
        if ~isfinite(y): return y # Give up
        newy = median([limits[0], y, limits[1]])
        if warn and newy!=y: printv('Note, parameter value "%s" reset from %f to %f' % (parname, y, newy), 3, verbose)
    elif shape(y):
        newy = array(y) # Make sure it's an array and not a list
        infiniteinds = findinds(~isfinite(newy))
        infinitevals = newy[infiniteinds] # Store these for safe keeping
        if len(infiniteinds): newy[infiniteinds] = limits[0] # Temporarily reset -- value shouldn't matter
        newy[newy<limits[0]] = limits[0]
        newy[newy>limits[1]] = limits[1]
        newy[infiniteinds] = infinitevals # And stick them back in
        if warn and any(newy!=array(y)) and verbose >= 3:
            printv('Note, parameter "%s" value reset from:\n%s\nto:\n%s' % (parname, y, newy), 3, verbose)
    else:
        if warn: raise OptimaException('Data type "%s" not understood for applying limits for parameter "%s"' % (type(y), parname))
        else: newy = array(y)
    
    if shape(newy)!=shape(y):
        errormsg = 'Something went wrong with applying limits for parameter "%s":\ninput and output do not have the same shape:\n%s vs. %s' % (parname, shape(y), shape(newy))
        raise OptimaException(errormsg)
    
    return newy





def comparepars(pars1=None, pars2=None):
    ''' 
    Function to compare two sets of pars. Example usage:
    comparepars(P.parsets[0], P.parsets[1])
    '''
    if type(pars1)==Parameterset: pars1 = pars1.pars # If parset is supplied instead of pars, use that instead
    if type(pars2)==Parameterset: pars2 = pars2.pars
    keys = list(pars1.keys())
    nkeys = 0
    count = 0
    for key in keys:
        if hasattr(pars1[key],'y'):
            nkeys += 1
            if str(pars1[key].y) != str(pars2[key].y): # Convert to string representation for testing equality
                count += 1
                msg = 'Parameter "%s" differs:\n' % key
                msg += '%s\n' % pars1[key].y
                msg += 'vs\n'
                msg += '%s\n' % pars2[key].y
                msg += '\n\n'
                print(msg)
    if count==0: print('All %i parameters match' % nkeys)
    else:        print('%i of %i parameters did not match' % (count, nkeys))
    return None



def comparesimpars(pars1=None, pars2=None, inds=Ellipsis, inds2=Ellipsis):
    ''' 
    Function to compare two sets of simpars, like what's stored in results.
    
    Example:
        import optima as op
        P = op.demo(0)
        P.copyparset(0,'new')
        P.pars('new')['numtx'].y[:] *= 1.5
        R1 = P.runsim('default', keepraw=True)
        R2 = P.runsim('new', keepraw=True)
        op.comparesimpars(R1.simpars, R2.simpars)
    '''
    if type(pars1)==list: pars1 = pars1[0] # If a list is supplied, pull out just the dict
    if type(pars2)==list: pars2 = pars2[0]
    keys = pars1.keys()
    nkeys = 0
    count = 0
    for key in keys:
        nkeys += 1
        thispar1 = pars1[key]
        thispar2 = pars2[key]
        if isinstance(thispar1,dict): keys2 = thispar1.keys()
        else: keys2 = [None]
        for key2 in keys2:
            if key2 is not None:
                this1 = array(thispar1[key2])
                this2 = array(thispar2[key2])
                key2str = '(%s)' % str(key2)
            else:
                this1 = array(thispar1)
                this2 = array(thispar2)
                key2str = ''
            if len(shape(this1))==2:
                pars1str = str(this1[inds2][inds])
                pars2str = str(this2[inds2][inds])
            elif len(shape(this1))==1:
                pars1str = str(this1[inds])
                pars2str = str(this2[inds])
            else:
                pars1str = str(this1)
                pars2str = str(this2)
            if pars1str != pars2str: # Convert to string representation for testing equality
                count += 1
                dividerlen = 70
                bigdivide    = '='*dividerlen+'\n'
                littledivide = '-'*int(dividerlen/2.0-4)
                msg  = '\n\n'+bigdivide
                msg += 'Parameter "%s" %s differs:\n\n' % (key, key2str)
                msg += '%s\n' % pars1str
                msg += littledivide + ' vs ' + littledivide + '\n'
                msg += '%s\n\n' % pars2str
                msg += bigdivide
                print(msg)
    if count==0: print('All %i parameters match' % nkeys)
    else:        print('%i of %i parameters did not match' % (count, nkeys))
    return None


def sanitycheck(simpars=None, showdiff=True, threshold=0.1, eps=1e-6):
    '''
    Compare the current simpars with the default simpars, flagging
    potential differences. If simpars is None, generate it from the
    current parset. If showdiff is True, only show parameters that differ
    by more than the threshold amount (default, 10%). eps is just to
    avoid divide-by-zero errors and can be ignored, probably.
    
    Usage:
        sanitycheck(P)
    or
        result = P.runsim(keepraw=True) # Need keepraw or else it doesn't store simpars
        sanitycheck(result.simpars)
    '''
    if isinstance(simpars, op.Project): # It's actually a project
        thisproj = simpars # Rename so it's clearer
        try:    simpars = thisproj.result().simpars # Try to extract the simpars
        except: simpars = thisproj.runsim(keepraw=True, die=False).simpars # If not, rerun
            
    tmpproj = op.demo(dorun=False, doplot=False) # Can't import this earlier since not actually declared before
    tmpproj.runsim(keepraw=True)
    gsp = op.dcp(tmpproj.results[-1].simpars[0]) # "Good simpars"
    sp = simpars[0] # "Simpars"
    
    if set(sp.keys())!=set(gsp.keys()):
        errormsg = 'Keys do not match:'
        errormsg += 'Too many: %s' % (set(sp.keys())-set(gsp.keys()))
        errormsg += 'Missing: %s' % (set(gsp.keys())-set(sp.keys()))
        raise op.OptimaException(errormsg)
    
    outstr = ''
    skipped = []
    for k,key in enumerate(gsp.keys()):
        if op.checktype(sp[key], 'number'):
            spval = sp[key]
            gspval = gsp[key]
            ratio = (eps+spval)/(eps+gspval)
            if not showdiff or not(abs(1-ratio)<threshold):
                outstr += '\n\n%s\n%s (%03i/%03i)\n' % ('='*70, key, k, len(sp.keys())-1)
                outstr += 'Yours: %10s  Best: %10s Ratio: %10s\n' % (op.sigfig(spval), op.sigfig(gspval), op.sigfig(ratio))
            else:
                skipped.append(key)
        elif op.checktype(sp[key], 'arraylike') or op.checktype(sp[key], op.odict):
            if op.checktype(sp[key], op.odict):
                sp[key] = sp[key][:] # Try converting to an odict...
                gsp[key] = gsp[key][:] # Try converting to an odict...
            spmin = sp[key].min()
            spmax = sp[key].max()
            gspmin = gsp[key].min()
            gspmax = gsp[key].max()
            minratio = (eps+spmin)/(eps+gspmin)
            maxratio = (eps+spmax)/(eps+gspmax)
            if not showdiff or not(abs(1-minratio)<threshold) or not(abs(1-maxratio)<threshold):
                outstr += '\n\n%s\n%s (%03i/%03i)\n' % ('='*70, key, k, len(sp.keys())-1)
                outstr += 'Min-Yours: %10s  Min-Best: %10s Min-Ratio: %10s\n' % (op.sigfig(spmin), op.sigfig(gspmin), op.sigfig(minratio))
                outstr += 'Max-Yours: %10s  Max-Best: %10s Max-Ratio: %10s\n' % (op.sigfig(spmax), op.sigfig(gspmax), op.sigfig(maxratio))
            else:
                skipped.append(key)
        else:
            if not showdiff:
                outstr += '\n\n%s\n%s (%03i/%03i)\n' % ('='*70, key, k, len(sp.keys())-1)
                outstr += str(type(sp[key]))
            else:
                skipped.append(key)
        
    print(outstr)
    return outstr

def checkifparsoverridepars(origpars, targetpars, progstartyear=None, progendyear=None):
    '''
    Checks if the original parset has parameters that override parameters that
    are being targeted (by programs or by a parameter scenario).
    Args:
        origpars: odict of Par objects from the parset being used
        targetpars: list of short names of pars that are being changed or targeted (by a progset)
        progstartyear: time that the programs or optimization starts
        progendyear: time that the programs or optimization finishes (note orig pars can still affect the program even
                     if orig pars is only set after the program finishes because makesimpars extends it earlier).
                     Defaults to 2100
    Returns:
        An odict with keys that are the overriding parameters in origpars,
        and the values are the list of targetpars that each par overrides.
        eg: origpars['fixpropcare'] = 2022, targetpars = ['linktocare','returntocare','numpmtct'], progendyear = 2030
        returns: warning=True, outdict = {'fixpropdx':['linktocare','returntocare']},
                 times = {'fixpropdx':2022.}, vals = {'fixpropdx': 'fixed'}
    '''
    if progendyear is None: progendyear = 2100
    if progstartyear is None: progstartyear = progendyear # the function should still work with the start year = end year
    warning = False
    outdict, times, vals = odict(), odict(), odict()
    targetparsset = set(targetpars)
    for overriding, affectedpars in overridingpars.items():
        overridingpar = origpars[overriding]  # (overriding)pars, progendyear, (overriden)targetpartypes
        willoverride = False
        if isinstance(overridingpar, Timepar):
            tvals = array(overridingpar.t['tot'])
            yvals = array(overridingpar.y['tot'])
            timesset = tvals[~isnan(yvals)]
            timesnan = tvals[isnan(yvals)]
            if len(timesset) == 0: continue
            maxtimesetbefore = max(append(timesset[timesset<progstartyear], -1))
            mintimesetafter  = min(append(timesset[timesset>=progendyear], Inf))
            if logical_and(timesset>=progstartyear, timesset<progendyear).any(): # proportion is set during the programs
                willoverride = True
            elif maxtimesetbefore>=0 or isfinite(mintimesetafter): # the prop is set either before or after programs
                if not logical_and(maxtimesetbefore < timesnan, timesnan < mintimesetafter).any(): # need a nan after prop set before, or nan before prop set after
                    willoverride = True
        elif isinstance(overridingpar, Yearpar):
            tvals = overridingpar.t
            yvals = '"Fixed"' ### WARNING not really a value
            willoverride = overridingpar.t < progendyear

        if willoverride:  # the proportion is actually set so now we check if the programset targets any of the overriden parameters
            targetparsaffected = list(filter(lambda par: par in targetparsset, affectedpars))
            if len(targetparsaffected) > 0:
                warning = True
                outdict[overriding] = targetparsaffected
                times[overriding] = tvals
                vals[overriding] = yvals
    return warning, outdict, times, vals


def createwarningforoverride(origpars, warning, parsoverridingparsdict, overridetimes, overridevals, fortype='Progscen', formatfor='console',
                             progsetname=None, parsetname=None, progsbytargetpartype=None, progendyear=2100,
                             warningmessage=None, warningmessageplural=None,
                             recommendmessagefixed=None,recommendmessageprop=None):
    """
    A helper function that will take the output from checkifparsoverridepars(), plus the original pars, and create
    a warning message(s) for any parameters that are getting overriden.
    Can be used both for an Optimization (fortype='Progscen'), Budget Scenario (fortype='Progscen'), Coverage Scenario
    (fortype='Progscen'), or Parameter Scenario (fortype='Parscen').
    Args:
        origpars: odict of Par objects from the original parset being used:
        warning, parsoverridingparsdict, overridetimes, overridevals: the outputs from checkifparsoverridepars
        fortype: type of scenario this will be used for see above. (changes the default messages)
        formatfor: 'html' or 'console': html uses <p> ... </p><br><p>... to format the warning message, console uses \n
        progsetname: name of the progset that wants to target parameters that could be getting overridden.
        parsetname: name of the parset that may be overriding the progset.
        progsbytargetpartype: the output of Programset.progs_by_targetpartype(), make sure to call progset.gettargetpars()
                              and progset.gettargetpartypes(), before progset.progs_by_targetpartype()
        progendyear: the year the scenario / optimization ends.
    Returns:
        warning: whether or not there is a warning (same as the input warning)
        combinedwarningmsg: a string message of all the combined messages
        warningmessages: a warning message for each parameter that is overriden, made up of warningmessage + recommendmessage.
                         See the default formats below.

    """
    if not warning: return warning, '', []

    if formatfor == 'html': sep = '</p><p>'
    else: sep = '\n'

    warningmessages = []
    if warningmessage is None:
        if fortype == 'Parscen': warningmessage = 'Warning: This scenario trying to set "{affectedparname}" but the parameter set "{parsetname}" has "{overridingparname}" set to {valstr}'
        else:                    warningmessage = 'Warning: The program \'{programsnames}\' in program set "{progsetname}" targets the "{affectedparname}" but the parameter set "{parsetname}" has "{overridingparname}" set to {valstr} which is before the program ends in {progendyear} so this program will likely have no affect.'

    if warningmessageplural is None:  warningmessageplural  = 'Warning: The programs {programsnames} in program set "{progsetname}" target the "{affectedparname}" but the parameter set "{parsetname}" has "{overridingparname}" set to {valstr} which is before the programs end in {progendyear} so these programs will likely have no effect.'
    if recommendmessagefixed is None: recommendmessagefixed = 'It is recommended to make another parameter set that has "{overridingparname}" set to 2100.'
    if recommendmessageprop is None:  recommendmessageprop  = 'It is recommended to make another parameter set that doesn\'t have "{overridingparname}" set.'

    for overriding, affectedpars in parsoverridingparsdict.items():
        overridingpar = origpars[overriding]
        if isinstance(overridingpar, Yearpar):
            valstr = f"{overridetimes[overriding]}"
            recommendmessage = recommendmessagefixed
        elif isinstance(overridingpar, Timepar):
            tvals = overridingpar.t['tot']
            yvals = array(overridingpar.y['tot'])
            valstr = f"{yvals} in {tvals}"
            recommendmessage = recommendmessageprop
        for affected in affectedpars:
            if fortype == 'Parscen':
                warningmessages.append(warningmessage)
                progsaffectednames = ['Not a program'] # Kludgy, so that later doesn't produce an error, but this won't be used anyway
            else:
                progsaffectednames = [prog.short for prog in progsbytargetpartype[affected]]
                warningmessages.append(warningmessage if len(progsaffectednames) == 1 else warningmessageplural)
            warningmessages[-1] = warningmessages[-1] + sep + recommendmessage
            warningmessages[-1] = warningmessages[-1].format(programsnames=progsaffectednames if len(progsaffectednames)>1 else progsaffectednames[0],
                                                       progsetname=progsetname,
                                                       affectedparname=origpars[affected].name,
                                                       parsetname=parsetname,
                                                       overridingparname=overridingpar.name,
                                                       valstr=valstr,
                                                       progendyear=progendyear)

    if formatfor == 'html':
        warningmessages = ['<p>' + msg.replace('"','&quot;') + '</p>' for msg in warningmessages]
        combinedwarningmsg = '<br>'.join(warningmessages)  # Note that this defaults to '' if warningmessages is empty
    else:
        combinedwarningmsg = (sep+sep).join(warningmessages)  # Note that this defaults to '' if warningmessages is empty

    return warning, combinedwarningmsg, warningmessages







            
                