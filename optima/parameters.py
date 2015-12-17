"""
This module defines the Parameter and Parameterset classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, respetively.

Version: 2015dec17 by cliffk
"""


from numpy import array, isnan, zeros, shape, argmax, mean, log, polyfit, exp, arange
from optima import odict, printv, sanitize, uuid, today, getdate, smoothinterp, dcp, objectid

eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero


def popgrow(exppars, tvec):
    ''' Return a time vector for a population growth '''
    return exppars[0]*exp(tvec*exppars[1]) # Simple exponential growth


def data2popsize(dataarray, data, keys):
    par = Popsizepar()
    par.name = 'popsize' # Store the name of the parameter
    par.m = 1 # Set metaparameter to 1
    
    # Parse data into consistent form
    sanitizedy = odict() # Initialize to be empty
    sanitizedt = odict() # Initialize to be empty
    for row,key in enumerate(keys):
        sanitizedy[key] = sanitize(dataarray[row]) # Store each extant value
        sanitizedt[key] = array(data['years'])[~isnan(dataarray[row])] # Store each year

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
    par.name = parname # Store the name of the parameter
    par.m = 1 # Set metaparameter to 1
    par.y = odict() # Initialize array for holding parameters
    par.t = odict() # Initialize array for holding time points
    for row,key in enumerate(keys):
        validdata = ~isnan(data[parname][row])
        if sum(validdata): # There's at least one data point -- WARNING, is this ok?
            par.y[key] = sanitize(data[parname][row]) # Store each extant value
            par.t[key] = array(data['years'])[~isnan(data[parname][row])] # Store each year
        else: # Blank, assume zero -- WARNING, is this ok?
            par.y[key] = array([0])
            par.t[key] = array([0])
    
    return par



def dataindex(parname, data, index, keys):
    """ Take an array of data return either the first or last (...or some other) non-NaN entry """
    par = odict() # Create structure
    for row,key in enumerate(keys):
        par[key] = sanitize(data[parname][row])[index] # Return the specified index -- usually either the first [0] or last [-1]
    
    return par




def gettotalacts(simpars, npts):
        totalacts = dict()
        
        popsize = simpars['popsize']
    
        for act in ['reg', 'cas', 'com', 'inj']:
            npops = len(simpars['popsize'][:,0]) # WARNING, what is this?
            npop=len(popsize); # Number of populations
            mixmatrix = simpars['part'+act]
            symmetricmatrix=zeros((npop,npop));
            for pop1 in range(npop):
                for pop2 in range(npop):
                    symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))
    
            a = zeros((npops,npops,npts))
            numacts = simpars['numacts'+act]
            for t in range(npts):
                a[:,:,t] = reconcileacts(symmetricmatrix.copy(), popsize[:,t], numacts[:,t]) # Note use of copy()
    
            totalacts[act] = a
        
        return totalacts
    
    
def reconcileacts(symmetricmatrix,popsize,popacts):

    # Make sure the dimensions all agree
    npop=len(popsize); # Number of populations
    
    for pop1 in range(npop):
        symmetricmatrix[pop1,:]=symmetricmatrix[pop1,:]*popsize[pop1];
    
    # Divide by the sum of the column to normalize the probability, then
    # multiply by the number of acts and population size to get total number of
    # acts
    for pop1 in range(npop):
        symmetricmatrix[:,pop1]=popsize[pop1]*popacts[pop1]*symmetricmatrix[:,pop1] / float(eps+sum(symmetricmatrix[:,pop1]))
    
    # Reconcile different estimates of number of acts, which must balance
    pshipacts=zeros((npop,npop));
    for pop1 in range(npop):
        for pop2 in range(npop):
            balanced = (symmetricmatrix[pop1,pop2] * popsize[pop1] + symmetricmatrix[pop2,pop1] * popsize[pop2])/(popsize[pop1]+popsize[pop2]); # here are two estimates for each interaction; reconcile them here
            pshipacts[pop2,pop1] = balanced/popsize[pop2]; # Divide by population size to get per-person estimate
            pshipacts[pop1,pop2] = balanced/popsize[pop1]; # ...and for the other population

    return pshipacts




            
            
        








def makeparsfromdata(data, verbose=2):
    """
    Translates the raw data (which were read from the spreadsheet). into
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
    pars['initprev'] = dataindex('hivprev', data, bestindex, popkeys, by='pop') # Pull out first available HIV prevalence point
    pars['popsize'] = data2popsize('popsize', data, popkeys, by='pop')
    
    # Epidemilogy parameters -- most are data
    pars['stiprev'] = data2timepar('stiprev', data, popkeys, by='pop') # STI prevalence
    pars['death']  = data2timepar('death', data, popkeys, by='pop')  # Death rates
    pars['tbprev'] = data2timepar('tbprev', data, popkeys, by='pop') # TB prevalence
    
    # Testing parameters -- most are data
    pars['hivtest'] = data2timepar('hivtest', data, popkeys, by='pop') # HIV testing rates
    pars['aidstest'] = data2timepar('aidstest', data, totkey, by='tot') # AIDS testing rates
    pars['txtotal'] = data2timepar('numtx', data, totkey, by='tot') # Number of people on first-line treatment -- 0 since overall not by population

    # MTCT parameters
    pars['numpmtct'] = data2timepar('numpmtct', data, totkey, by='tot')
    pars['breast']   = data2timepar('breast', data, totkey, by='tot')  
    pars['birth']    = data2timepar('birth', data, popkeys, by='pop')
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
    pars['prep'] = data2timepar(pars['prep'], popkeys, by='pop')
    
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
    
    # Matrices can be used almost directly
    for parname in ['transit']: # Will probably include birth matrices in here too...
        pars[parname] = odict()
        for i,key1 in enumerate(popkeys):
            for j,key2 in enumerate(popkeys):
                if array(data[parname])[i,j]>0:
                    pars[parname][(key1,key2)] = array(data[parname])[i,j] # Convert from matrix to odict with tuple keys
        
    # Sexual behavior parameters -- all are parameters so can loop over all
    for act in ['reg','cas','com','inj']:
        theseacts = data['numacts'+act]
        thesepships = data['part'+act]
        pars['acts'+act] = gettotalacts(theseacts, thesepships, pars['popsize'])
#    pars['numactsreg'] = datapar2simpar(pars['numactsreg'], popkeys) 
#    pars['numactscas'] = datapar2simpar(pars['numactscas'], popkeys) 
#    pars['numactscom'] = datapar2simpar(pars['numactscom'], popkeys) 
#    pars['numactsinj'] = datapar2simpar(pars['numinject'], popkeys) 
#    pars['condomreg']  = datapar2simpar(pars['condomreg'], popkeys) 
#    pars['condomcas']  = datapar2simpar(pars['condomcas'], popkeys) 
#    pars['condomcom']  = datapar2simpar(pars['condomcom'], popkeys) 
    
    
    
    
    
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
        output += '           Name: %s\n'    % self.name
        output += '         Values: %s\n'    % self.y
        output += '    Time points: %s\n'    % self.t
        output += '  Metaparameter: %s\n'    % self.m
        output += 'Time/value keys: %s\n'    % self.y.keys()
        return output
    
    def interp(self, tvec, smoothness=5):
        """ Take parameters and turn them into model parameters """
        keys = self.y.keys()
        npops = len(keys)
        output = zeros((npops,len(tvec)))
        dt = tvec[1]-tvec[0] # Assume constant 
        for pop,key in enumerate(keys): # Loop over each population, always returning an [npops x npts] array
            output[pop,:] = self.m * smoothinterp(tvec, self.t[pop], self.y[pop], smoothness=int(smoothness*1.0/dt)) # Use interpolation
        else: return output






class Popsizepar(object):
    ''' The definition of the population size parameter '''
    
    def __init__(self, name=None, p=None, m=1, start=2000):
        if p is None: p = odict()
        self.name = name # Going to be "popsize"
        self.p = p # Exponential fit parameters
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.start = start # Year for which population growth start is calibrated to
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '\n'
        output += '          Name: %s\n'    % self.name
        output += 'Fit parameters: %s\n'    % self.p
        output += ' Metaparameter: %s\n'    % self.m
        output += '    Start year: %s\n'    % self.start
        return output

    def interp(self, tvec):
        """ Take population size parameter and turn it into a model parameters """  
        keys = self.y.keys()
        npops = len(keys)
        output = zeros((npops,len(tvec)))
        for pop,key in enumerate(keys):
            output[pop,:] = self.m * popgrow(self.p[key], tvec-self.start)
        return output






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
        self.popkeys = dcp(self.pars[-1].popkeys) # Store population keys
        return None


    def interp(self, ind=0, start=2000, end=2030, dt=0.2, tvec=None, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose)
        
        pars = self.pars[ind] # Shorten name of parameters thing
        simpars = odict() # Used to be called M
        if tvec is not None: simpars['tvec'] = tvec
        else: simpars['tvec'] = arange(start, end+dt, dt) # Store time vector with the model parameters
        simpars['popkeys'] = dcp(self.popkeys)
        
        for key in pars.keys():
            try: simpars[key] = pars[key].interp(tvec=simpars['tvec']) # WARNING, probably a better way to do this, but  avoids need to give explicit list
            except: simpars[key] = dcp(pars[key]) # If interpolation doesn't work, just copy it
        
        ## Metaparameters -- convert from odict to array -- WARNING
        simpars['force'] = array(simpars['force'][:])
        simpars['inhomo'] = array(simpars['inhomo'][:])
        
        printv('...done making model parameters.', 2, verbose)
        return simpars