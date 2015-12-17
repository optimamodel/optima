"""
This module defines the Parameter and Parameterset classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, respetively.

Version: 2015dec17 by cliffk
"""


from numpy import array, isnan, zeros, shape, argmax, mean, log, polyfit, exp, arange
from optima import odict, printv, sanitize, uuid, today, getdate, smoothinterp, dcp, objectid

eps = 1e-3 # TODO WARNING KLUDGY avoid divide-by-zero



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



def dataindex(dataarray, index, keys):
    """ Take an array of data return either the first or last (...or some other) non-NaN entry """
    par = odict() # Create structure
    for row,key in enumerate(keys):
        par[key] = sanitize(dataarray[row])[index] # Return the specified index -- usually either the first [0] or last [-1]
    
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
    pars['initprev'] = dataindex(data['hivprev'], bestindex, popkeys, by='pop') # Pull out first available HIV prevalence point
    pars['popsize'] = data2popsize(data['popsize'], data, popkeys, by='pop')
    
    # Epidemilogy parameters -- most are data
    pars['stiprev'] = data2timepar('stiprev', data, popkeys, by='pop') # STI prevalence
    pars['death']  = data2timepar(pars['death'], popkeys, by='pop')  # Death rates
    pars['tbprev'] = data2timepar(pars['tbprev'], popkeys, by='pop') # TB prevalence
    
    # Testing parameters -- most are data
    pars['hivtest'] = data2timepar(pars['hivtest'], popkeys, by='pop') # HIV testing rates
    pars['aidstest'] = data2timepar(pars['aidstest'], totkey, by='tot') # AIDS testing rates
    pars['txtotal'] = data2timepar(pars['numtx'], totkey, by='tot') # Number of people on first-line treatment -- 0 since overall not by population

    # MTCT parameters
    pars['numpmtct'] = data2timepar(pars['numpmtct'], totkey, by='tot')
    pars['breast']   = data2timepar(pars['breast'], totkey, by='tot')  
    pars['birth']    = data2timepar(pars['birth'], popkeys, by='pop')
    for key in list(set(popkeys)-set(fpopkeys)): # Births are only female: add zeros
        pars['birth'].y[key] = array([0])
        pars['birth'].t[key] = array([0])
    
    # Sexual behavior parameters -- all are parameters so can loop over all
    pars['numactsreg'] = datapar2simpar(pars['numactsreg'], popkeys) 
    pars['numactscas'] = datapar2simpar(pars['numactscas'], popkeys) 
    pars['numactscom'] = datapar2simpar(pars['numactscom'], popkeys) 
    pars['numactsinj'] = datapar2simpar(pars['numinject'], popkeys) 
    pars['condomreg']  = datapar2simpar(pars['condomreg'], popkeys) 
    pars['condomcas']  = datapar2simpar(pars['condomcas'], popkeys) 
    pars['condomcom']  = datapar2simpar(pars['condomcom'], popkeys) 
    
    # Circumcision parameters
    pars['circum'] = data2timepar(pars['circum'], mpopkeys, by='pop') # Circumcision percentage
    for key in list(set(popkeys)-set(mpopkeys)): # Circumcision is only male
        pars['circum'].y[key] = array([0])
        pars['circum'].t[key] = array([0])
    
    # Drug behavior parameters
    pars['numost'] = data2timepar(pars['numost'], totkey, by='tot')
    pars['sharing'] = data2timepar(pars['sharing'], popkeys, by='pop')
    
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
    for parname in ['partreg', 'partcas', 'partcom', 'partinj', 'transit']:
        pars[parname] = odict()
        for i,key1 in enumerate(popkeys):
            for j,key2 in enumerate(popkeys):
                if array(data[parname])[i,j]>0:
                    pars[parname][(key1,key2)] = array(data[parname])[i,j] # Convert from matrix to odict with tuple keys
        
        array(data[parname])
    
    
    
    
    
    printv('...done converting data to parameters.', 2, verbose)
    
    return pars









def popgrow(exppars, tvec):
    ''' Return a time vector for a population growth '''
    return exppars[0]*exp(tvec*exppars[1]) # Simple exponential growth









class Timepar(object):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, name=None, t=None, y=None, m=1, by=None):
        if t is None: t = odict()
        if y is None: y = odict()
        self.name = name
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1
        self.by = by # Whether it's total, by pop, or by partnership
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += '   Time points: %s\n'    % self.t
        output += '        Values: %s\n'    % self.y
        output += ' Metaparameter: %s\n'    % self.m
        return output



class Popsizepar(object):
    ''' The definition of the population size parameter '''
    
    def __init__(self, name=None, p=None, m=1):
        if p is None: p = odict()
        self.name = name
        self.p = p # Exponential fit parameters
        self.m = m # Multiplicative metaparameter, e.g. 1
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += 'Fit parameters: %s\n'    % self.p
        output += ' Metaparameter: %s\n'    % self.m
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
        popkeys = dcp(self.popkeys)
        tot = ['tot'] # WARNING, this is kludgy
        simpars['popkeys'] = popkeys
        npts = len(simpars['tvec']) # Number of time points
        
        
        def popsize2simpar(par, keys):
            """ Take population size and turn it into a model parameters """    
            npops = len(keys)
            output = zeros((npops,npts))
            for pop,key in enumerate(keys):
                output[pop,:] = par.m * popgrow(par.p[key], simpars['tvec']-start)
            return output
            
            
        
        def datapar2simpar(datapar, keys, smoothness=5*int(1/dt)):
            """ Take parameters and turn them into model parameters """
            npops = len(keys)
            output = zeros((npops,npts))
            for pop,key in enumerate(keys):
                output[pop,:] = datapar.m * smoothinterp(simpars['tvec'], datapar.t[pop], datapar.y[pop], smoothness=smoothness) # Use interpolation
            if npops==1: return output[0] # Return 1D vector if only a single 'population'
            else: return output
        
        
        
        
        ## Epidemilogy parameters -- most are data
        simpars['popsize'] = popsize2simpar(pars['popsize'], popkeys) # Population size
        simpars['initprev'] = pars['initprev'] # Initial HIV prevalence
        simpars['stiprev'] = datapar2simpar(pars['stiprev'], popkeys) # STI prevalence
        simpars['death']  = datapar2simpar(pars['death'], popkeys)  # Death rates
        simpars['tbprev'] = datapar2simpar(pars['tbprev'], popkeys) # TB prevalence
        
        ## Testing parameters -- most are data
        simpars['hivtest'] = datapar2simpar(pars['hivtest'], popkeys) # HIV testing rates
        simpars['aidstest'] = datapar2simpar(pars['aidstest'], tot) # AIDS testing rates
        simpars['tx'] = datapar2simpar(pars['numtx'], tot, smoothness=int(1/dt)) # Number of people on first-line treatment -- 0 since overall not by population
    
        ## MTCT parameters
        simpars['numpmtct'] = datapar2simpar(pars['numpmtct'], tot)
        simpars['birth']    = datapar2simpar(pars['birth'], popkeys)
        simpars['breast']   = datapar2simpar(pars['breast'], tot)  
        
        ## Sexual behavior parameters -- all are parameters so can loop over all
        simpars['numactsreg'] = datapar2simpar(pars['numactsreg'], popkeys) 
        simpars['numactscas'] = datapar2simpar(pars['numactscas'], popkeys) 
        simpars['numactscom'] = datapar2simpar(pars['numactscom'], popkeys) 
        simpars['numactsinj'] = datapar2simpar(pars['numinject'], popkeys) 
        simpars['condomreg']  = datapar2simpar(pars['condomreg'], popkeys) 
        simpars['condomcas']  = datapar2simpar(pars['condomcas'], popkeys) 
        simpars['condomcom']  = datapar2simpar(pars['condomcom'], popkeys) 
        
        ## Circumcision parameters
        simpars['circum']    = datapar2simpar(pars['circum'], popkeys) # Circumcision percentage
        if  'numcircum' in pars.keys():
            simpars['numcircum'] = datapar2simpar(pars['numcircum'], tot) # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
        else:
            simpars['numcircum'] = zeros(shape(simpars['tvec'])) # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
        
        ## Drug behavior parameters
        simpars['numost'] = datapar2simpar(pars['numost'], tot)
        simpars['sharing'] = datapar2simpar(pars['sharing'], popkeys)
        
        ## Other intervention parameters (proportion of the populations, not absolute numbers)
        simpars['prep'] = datapar2simpar(pars['prep'], popkeys)
        
        ## Matrices can be used almost directly
        for parname in ['partreg', 'partcas', 'partcom', 'partinj', 'transit']:
            simpars[parname] = array(pars[parname])
        
        ## Constants...can be used directly
        simpars['const'] = pars['const']
        
        ## Calculate total acts
        totalacts = gettotalacts(simpars, npts)
        for act in ['reg','cas','com','inj']:
            simpars['totalacts'+act] = totalacts[act]
        
        ## Program parameters not related to data
        simpars['propaware'] = zeros(shape(simpars['hivtest'])) # Initialize proportion of PLHIV aware of their status
        simpars['txtotal'] = zeros(shape(simpars['tx'])) # Initialize total number of people on treatment
        
        ## Metaparameters
        simpars['force'] = array(pars['force'][:])
        simpars['inhomo'] = array(pars['inhomo'][:])
        
        ## Other things that can be used directly as well
        simpars['male'] = pars['male']
        simpars['female'] = pars['female']

        printv('...done making model parameters.', 2, verbose)
        return simpars
    
    
            
        


    
