"""
This module defines the Timepar, Popsizepar, and Constant classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, the Parameterset class.

Version: 2015dec21 by cliffk
"""


from numpy import array, isnan, zeros, argmax, mean, log, polyfit, exp, arange, maximum, minimum, Inf, linspace
from optima import odict, printv, sanitize, uuid, today, getdate, smoothinterp, dcp, objectid

eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero



def popgrow(exppars, tvec):
    ''' Return a time vector for a population growth '''
    return exppars[0]*exp(tvec*exppars[1]) # Simple exponential growth



def data2prev(parname, data, index, keys, by=None, blh=0): # WARNING, "blh" means "best low high", currently upper and lower limits are being thrown away, which is OK here...?
    """ Take an array of data return either the first or last (...or some other) non-NaN entry -- used for initial HIV prevalence only so far... """
    par = Constant(name=parname, y=odict(), by=by) # Create structure
    for row,key in enumerate(keys):
        par.y[key] = sanitize(data[parname][blh][row])[index] # Return the specified index -- usually either the first [0] or last [-1]

    return par



def data2popsize(parname, data, keys, by=None, blh=0):
    ''' Convert population size data into population size parameters '''
    par = Popsizepar(name=parname, m=1, by=by)
    
    # Parse data into consistent form
    sanitizedy = odict() # Initialize to be empty
    sanitizedt = odict() # Initialize to be empty
    for row,key in enumerate(keys):
        sanitizedy[key] = sanitize(data[parname][blh][row]) # Store each extant value
        sanitizedt[key] = array(data['years'])[~isnan(data[parname][blh][row])] # Store each year

    largestpop = argmax([mean(sanitizedy[key]) for key in keys]) # Find largest population size
    
    # Store a list of population sizes that have at least 2 data points
    atleast2datapoints = [] 
    for key in keys:
        if len(sanitizedy[key])>=2:
            atleast2datapoints.append(key)
    if len(atleast2datapoints)==0:
        errormsg = 'Not more than one data point entered for any population size\n'
        errormsg += 'To estimate growth trends, at least one population must have at least 2 data points'
        raise Exception(errormsg)
    
    # Perform 2-parameter exponential fit to data
    startyear = data['years'][0]
    par.start = data['years'][0]
    for key in atleast2datapoints:
        tdata = sanitizedt[key]-startyear
        ydata = log(sanitizedy[key])
        try:
            fitpars = polyfit(tdata, ydata, 1)
            par.p[key] = array([exp(fitpars[1]), fitpars[0]])
        except:
            errormsg = 'Fitting population size data for population "%s" failed' % key
            raise Exception(errormsg)
    
    # ...do weighting based on number of data points and/or population size?
    
    # Handle populations that have only a single data point
    only1datapoint = list(set(keys)-set(atleast2datapoints))
    for key in only1datapoint:
        largestpars = par.p[largestpop] # Get the parameters from the largest population
        if len(sanitizedt[key]) != 1:
            errormsg = 'Error interpreting population size for population "%s"\n' % key
            errormsg += 'Please ensure at least one time point is entered'
            raise Exception(errormsg)
        thisyear = sanitizedt[key][0]
        thispopsize = sanitizedy[key][0]
        largestthatyear = popgrow(largestpars, thisyear-startyear)
        par.p[key] = [largestpars[0]*thispopsize/largestthatyear, largestpars[0]]
    
    return par




def data2timepar(parname, data, keys, by=None):
    """ Take an array of data and turn it into default parameters -- here, just take the means """
    par = Timepar(name=parname, m=1, y=odict(), t=odict(), by=by) # Create structure
    for row,key in enumerate(keys):
        validdata = ~isnan(data[parname][row])
        if sum(validdata): # There's at least one data point -- WARNING, is this ok?
            par.y[key] = sanitize(data[parname][row]) # Store each extant value
            par.t[key] = array(data['years'])[~isnan(data[parname][row])] # Store each year
        else: # Blank, assume zero -- WARNING, is this ok?
            par.y[key] = array([0])
            par.t[key] = array([0])
    
    return par








    








def makeparsfromdata(data, verbose=2):
    """
    Translates the raw data (which were read from the spreadsheet) into
    parameters that can be used in the model. These data are then used to update 
    the corresponding model (project). This method should be called before a 
    simulation is run.
    
    Version: 2015dec17 by cliffk
    """
    
    printv('Converting data to parameters...', 1, verbose)
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    pars = odict()
    
    # Shorten information on which populations are male, which are female
    pars['male'] = array(data['pops']['male']).astype(bool) # Male populations 
    pars['female'] = array(data['pops']['female']).astype(bool) # Female populations
    
    # Set up keys
    totkey = ['tot'] # Define a key for when not separated by population
    popkeys = data['pops']['short'] # Convert to a normal string and to lower case...maybe not necessary
    fpopkeys = [popkeys[i] for i in range(len(popkeys)) if pars['female'][i]]
    mpopkeys = [popkeys[i] for i in range(len(popkeys)) if pars['male'][i]]
    pars['popkeys'] = dcp(popkeys)
    
    # Key parameters
    bestindex = 0 # Define index for 'best' data, as opposed to high or low -- WARNING, kludgy, should use all
    pars['initprev'] = data2prev('hivprev', data, bestindex, popkeys, by='pop') # Pull out first available HIV prevalence point
    pars['popsize'] = data2popsize('popsize', data, popkeys, by='pop')
    
    # Epidemilogy parameters -- most are data
    pars['stiprev'] = data2timepar('stiprev', data, popkeys, by='pop') # STI prevalence
    pars['death']  = data2timepar('death', data, popkeys, by='pop')  # Death rates
    pars['tbprev'] = data2timepar('tbprev', data, popkeys, by='pop') # TB prevalence
    
    # Testing parameters -- most are data
    pars['hivtest'] = data2timepar('hivtest', data, popkeys, by='pop') # HIV testing rates
    pars['aidstest'] = data2timepar('aidstest', data, totkey, by='tot') # AIDS testing rates
    pars['numtx'] = data2timepar('numtx', data, totkey, by='tot') # Number of people on first-line treatment -- WARNING, will need to change

    # MTCT parameters
    pars['numpmtct'] = data2timepar('numpmtct', data, totkey, by='tot')
    pars['breast']   = data2timepar('breast', data, totkey, by='tot')  
    pars['birth']    = data2timepar('birth', data, fpopkeys, by='pop')
    for key in list(set(popkeys)-set(fpopkeys)): # Births are only female: add zeros
        pars['birth'].y[key] = array([0])
        pars['birth'].t[key] = array([0])
    
    # Circumcision parameters
    pars['circum'] = data2timepar('circum', data, mpopkeys, by='pop') # Circumcision percentage
    for key in list(set(popkeys)-set(mpopkeys)): # Circumcision is only male
        pars['circum'].y[key] = array([0])
        pars['circum'].t[key] = array([0])
    
    # Drug behavior parameters
    pars['numost'] = data2timepar('numost', data, totkey, by='tot')
    pars['sharing'] = data2timepar('sharing', data, popkeys, by='pop')
    
    # Other intervention parameters (proportion of the populations, not absolute numbers)
    pars['prep'] = data2timepar('prep', data, popkeys, by='pop')
    
    # Constants
    pars['const'] = odict()
    for parname in data['const'].keys():
        printv('Converting data parameter %s...' % parname, 3, verbose)
        pars['const'][parname] = data['const'][parname][0] # Taking best value only, hence the 0

    # Initialize metaparameters
    pars['force'] = odict()
    pars['inhomo'] = odict()
    for key in popkeys:
        pars['force'][key] = 1
        pars['inhomo'][key] = 0
    
    # Risk-related population transitions
    pars['transit'] = odict() # Will probably include birth matrices in here too...
    for i,key1 in enumerate(popkeys):
        for j,key2 in enumerate(popkeys):
            pars['transit'][(key1,key2)] = array(data['transit'])[i,j] 
    
    
    ## Acts
    def balance(act, which=None, popsizepar=None):
        ''' 
        Combine the different estimates for the number of acts or condom use and return the "average" value.
        
        Set which='numacts' to compute for number of acts, which='condom' to compute for condom.
        '''
        if which not in ['numacts','condom']: raise Exception('Can only balance numacts or condom, not "%s"' % which)
        mixmatrix = array(data['part'+act]) # Get the partnerships matrix
        npops = len(popkeys) # Figure out the number of populations
        symmetricmatrix = zeros((npops,npops));
        for pop1 in range(npops):
            for pop2 in range(npops):
                if which=='numacts': symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))
                if which=='condom': symmetricmatrix[pop1,pop2] = bool(symmetricmatrix[pop1,pop2] + mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1])
            
        # Decide which years to use -- use the earliest year, the latest year, and the most time points available
        yearstouse = []
        for row in range(npops):
            yearstouse.append(array(data['years'])[~isnan(data[which+act][row])]   )
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
        tmppar = data2timepar(which+act, data, popkeys, by='pop') # Temporary parameter for storing acts
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
                for pop1 in range(npops): smatrix[pop1,:] = smatrix[pop1,:]*psize[pop1] # Yes, this needs to be separate! Don't try to put in the next for loop, the indices are opposite!
                for pop1 in range(npops): smatrix[:,pop1] = psize[pop1]*popacts[pop1]*smatrix[:,pop1] / float(eps+sum(smatrix[:,pop1])) # Divide by the sum of the column to normalize the probability, then multiply by the number of acts and population size to get total number of acts
            
            # Reconcile different estimates of number of acts, which must balance
            thispoint = zeros((npops,npops));
            for pop1 in range(npops):
                for pop2 in range(npops):
                    if which=='numacts':
                        balanced = (smatrix[pop1,pop2] * psize[pop1] + smatrix[pop2,pop1] * psize[pop2])/(psize[pop1]+psize[pop2]) # here are two estimates for each interaction; reconcile them here
                        thispoint[pop2,pop1] = balanced/psize[pop2] # Divide by population size to get per-person estimate
                        thispoint[pop1,pop2] = balanced/psize[pop1] # ...and for the other population
                    if which=='condom':
                        thispoint[pop1,pop2] = (tmpsim[pop1,t]+tmpsim[pop2,t])/2.0
                        thispoint[pop2,pop1] = thispoint[pop1,pop2]
        
            output[:,:,t] = thispoint
        
        return output, ctrlpts
        
    # Sexual behavior parameters
    tmpacts = odict()
    tmpcond = odict()
    tmpactspts = odict()
    tmpcondpts = odict()
    for act in ['reg','cas','com', 'inj']: # Number of acts
        actsname = 'acts'+act
        tmpacts[act], tmpactspts[act] = balance(act, 'numacts', pars['popsize'])
        pars[actsname] = Timepar(name=actsname, m=1, y=odict(), t=odict(), by='pship') # Create structure
    for act in ['reg','cas','com']: # Condom use
        condname = 'cond'+act
        tmpcond[act], tmpcondpts[act] = balance(act, 'condom')
        pars[condname] = Timepar(name=condname, m=1, y=odict(), t=odict(), by='pship') # Create structure
        
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
                        pars[condname].y[(key1,key2)] = array(tmpcond[act])[i,j,:]
                        pars[condname].t[(key1,key2)] = array(tmpcondpts[act])
    

    
    
    
    
    
    printv('...done converting data to parameters.', 2, verbose)
    
    return pars



















class Timepar(object):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, name=None, t=None, y=None, m=1, by=None):
        if t is None: t = odict()
        if y is None: y = odict()
        self.name = name
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.by = by # Whether it's total ('tot'), by population ('pop'), or by partnership ('pship')
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += ' name: %s\n'    % self.name
        output += '    y: %s\n'    % self.y
        output += '    t: %s\n'    % self.t
        output += '    m: %s\n'    % self.m
        output += ' keys: %s\n'    % self.y.keys()
        return output
    
    def interp(self, tvec, smoothness=20):
        """ Take parameters and turn them into model parameters """
        keys = self.y.keys()
        npops = len(keys)
        output = zeros((npops,len(tvec)))
        for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
            output[pop,:] = self.m * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=smoothness) # Use interpolation
        if npops==1: return output[0,:]
        else: return output






class Popsizepar(object):
    ''' The definition of the population size parameter '''
    
    def __init__(self, name=None, p=None, m=1, start=2000, by=None):
        if p is None: p = odict()
        self.name = name # Going to be "popsize"
        self.p = p # Exponential fit parameters
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.start = start # Year for which population growth start is calibrated to
        self.by = by # Whether it's by population, partnership, etc...
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '\n'
        output += '          Name: %s\n'    % self.name
        output += 'Fit parameters: %s\n'    % self.p
        output += '    Start year: %s\n'    % self.start
        output += ' Metaparameter: %s\n'    % self.m
        output += 'Parameter keys: %s\n'    % self.p.keys()
        return output

    def interp(self, tvec, smoothness=None): # WARNING: smoothness isn't used, but kept for consistency with other methods...
        """ Take population size parameter and turn it into a model parameters """  
        keys = self.p.keys()
        npops = len(keys)
        output = zeros((npops,len(tvec)))
        for pop,key in enumerate(keys):
            output[pop,:] = self.m * popgrow(self.p[key], array(tvec)-self.start)
        return output



class Constant(object):
    ''' The definition of a single constant parameter, which may or may not vary by population '''
    
    def __init__(self, name=None, y=None, by=None):
        if y is None: y = odict()
        self.name = name
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.by = by # Whether it's total ('tot'), by population ('pop'), or by partnership ('pship')
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += '           Name: %s\n'    % self.name
        output += '         Values: %s\n'    % self.y
        output += 'Time/value keys: %s\n'    % self.y.keys()
        return output
    
    def interp(self, tvec=None, smoothness=None):
        """ Take parameters and turn them into model parameters -- here, just return a constant value at every time point """
        keys = self.y.keys()
        npops = len(keys)
        output = zeros(npops)
        for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
            output[pop] = self.y[pop] # Just copy y values
        else: return output




class Parameterset(object):
    ''' A full set of all parameters, possibly including multiple uncertainty runs '''
    
    def __init__(self, name='default', id=None):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.uuid = uuid() # ID
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.pars = [] # List of dicts holding Parameter objects -- only one if no uncertainty
        self.popkeys = [] # List of populations
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = objectid(self)
        output += 'Parameter set name: %s\n'    % self.name
        output += '    Number of runs: %s\n'    % len(self.pars)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '              UUID: %s\n'    % self.uuid
        return output
    
    
    
    def makeparsfromdata(self, data, verbose=2):
        self.pars.append(makeparsfromdata(data, verbose=verbose))
        self.popkeys = dcp(self.pars[-1]['popkeys']) # Store population keys
        return None


    def interp(self, ind=0, keys=None, start=2000, end=2030, dt=0.2, tvec=None, smoothness=20, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose)
        
        generalkeys = ['male', 'female', 'popkeys', 'const', 'force', 'inhomo']
        modelkeys = ['initprev', 'popsize', 'stiprev', 'death', 'tbprev', 'hivtest', 'aidstest', 'numtx', 'numpmtct', 'breast', 'birth', 'circum', 'numost', 'sharing', 'prep', 'actsreg', 'actscas', 'actscom', 'actsinj', 'condreg', 'condcas', 'condcom']
        if keys is None: keys = modelkeys
        
        pars = self.pars[ind] # Shorten name of parameters thing -- and only pull out a single parameter set
        simpars = odict() # Used to be called M
        if tvec is not None: simpars['tvec'] = tvec
        else: simpars['tvec'] = arange(start, end+dt, dt) # Store time vector with the model parameters
        simpars['popkeys'] = dcp(self.popkeys)
        
        # Copy default keys by default
        for key in generalkeys: simpars[key] = dcp(pars[key])
        for key in keys:
            try:
                simpars[key] = pars[key].interp(tvec=simpars['tvec'], smoothness=smoothness) # WARNING, want different smoothness for ART
            except:
                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

        
        
        ## Metaparameters -- convert from odict to array -- WARNING
        simpars['force'] = array(simpars['force'][:])
        simpars['inhomo'] = array(simpars['inhomo'][:])
        
        printv('...done making model parameters.', 2, verbose)
        return simpars