"""
This module defines the Parameter and Parameterset classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, respetively.

Version: 2015nov23 by cliffk
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




def data2timepar(parname, dataarray, data, keys):
    """ Take an array of data and turn it into default parameters -- here, just take the means """
    par = Timepar() # Create structure
    par.name = parname # Store the name of the parameter
    par.m = 1 # Set metaparameter to 1
    par.y = odict() # Initialize array for holding parameters
    par.t = odict() # Initialize array for holding time points
    for row,key in enumerate(keys):
        validdata = ~isnan(dataarray[row])
        if sum(validdata): # There's at least one data point -- WARNING, is this ok?
            par.y[key] = sanitize(dataarray[row]) # Store each extant value
            par.t[key] = array(data['years'])[~isnan(dataarray[row])] # Store each year
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







def makeparsfromdata(data, verbose=2):
    """
    Translates the raw data (which were read from the spreadsheet). into
    parameters that can be used in the model. These data are then used to update 
    the corresponding model (project). This method should be called before a 
    simulation is run.
    
    Version: 2015nov22 by cliffk
    """
    
    printv('Converting data to parameters...', 1, verbose)
    
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    pars = odict()
    popkeys = data['pops']['short'] # Convert to a normal string and to lower case...maybe not necessary
    totkey = ['tot'] # Define a key for when not separated by population
    pars['popkeys'] = dcp(popkeys)
    
    ## Key parameters
    bestindex = 0 # Define index for 'best' data, as opposed to high or low -- WARNING, kludgy, should use all
    pars['initprev'] = dataindex(data['hivprev'][bestindex], 0, popkeys) # Pull out first available HIV prevalence point
    pars['popsize'] = data2popsize(data['popsize'][bestindex], data, popkeys)
    
    ## Parameters that can be converted automatically
    sheets = data['meta']['sheets']
    for parname in sheets['Other epidemiology'] + sheets['Testing & treatment'] + sheets['Sexual behavior'] + sheets['Injecting behavior']:
        printv('Converting data parameter %s...' % parname, 3, verbose)
        nrows = shape(data[parname])[0]
        
        # Check how many rows there are, handle special cases, and die if it doesn't match
        if parname=='birth':
            keys = [popkeys[i] for i in range(len(popkeys)) if data['pops']['female'][i]]
        elif parname=='circum':
            keys = [popkeys[i] for i in range(len(popkeys)) if data['pops']['male'][i]]
        elif nrows==1: 
            keys = totkey
        elif nrows==len(popkeys): 
            keys = popkeys
        else:
            errormsg = 'Unable to figure out size of parameter "%s"\n' % parname
            errormsg += '(number of rows = %i; number of populations = %i)' % (nrows, len(popkeys))
            raise Exception(errormsg)
        pars[parname] = data2timepar(parname, data[parname], data, keys)
        if parname in ['birth', 'circum']: # For these two, have to expand to all populations
            missingkeys = list(set(popkeys)-set(keys))
            for key in missingkeys:
                pars[parname].y[key] = array([0])
                pars[parname].t[key] = array([0])
    

    ## WARNING, not sure what to do with these
    for parname in ['partreg', 'partcas', 'partcom', 'partinj', 'transit']:
        printv('Converting data parameter %s...' % parname, 3, verbose)
        pars[parname] = data[parname]
    
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
    
    # Store male/female properties
    pars['male'] = array(data['pops']['male']).astype(bool) # Male populations 
    pars['female'] = array(data['pops']['female']).astype(bool) # Male populations
    
    printv('...done converting data to parameters.', 2, verbose)
    
    return pars





def totalacts(simpars, npts):
        totalacts = dict()
        
        popsize = simpars['popsize']
    
        for act in ['reg','cas','com','inj']:
            npops = len(simpars['popsize'][:,0])
            npop=len(popsize); # Number of populations
            mixmatrix = simpars['part'+act]
            symmetricmatrix=zeros((npop,npop));
            for pop1 in range(npop):
                for pop2 in range(npop):
                    symmetricmatrix[pop1,pop2] = symmetricmatrix[pop1,pop2] + (mixmatrix[pop1,pop2] + mixmatrix[pop2,pop1]) / float(eps+((mixmatrix[pop1,pop2]>0)+(mixmatrix[pop2,pop1]>0)))
    
            a = zeros((npops,npops,npts))
            numacts = simpars['numacts'][act]
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



def popgrow(exppars, tvec):
    ''' Return a time vector for a population growth '''
    return exppars[0]*exp(tvec*exppars[1]) # Simple exponential growth









class Timepar(object):
    ''' The definition of a single time-varying parameter, which may or may not vary by population '''
    
    def __init__(self, t=None, y=None, m=1):
        if t is None: t = odict()
        if y is None: y = odict()
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += '   Time points: %s\n'    % self.t
        output += '        Values: %s\n'    % self.y
        output += ' Metaparameter: %s\n'    % self.m
        return output



class Popsizepar(object):
    ''' The definition of the population size parameter '''
    
    def __init__(self, p=None, m=1):
        if p is None: p = odict()
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
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = objectid(self)
        output += '\n'
        output += 'Parameter set name: %s\n'    % self.name
        output += '    Number of runs: %s\n'    % len(self.pars)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '              UUID: %s\n'    % self.uuid
        return output
    
    
    
    def makeparsfromdata(self, data, verbose=2):
        self.pars.append(makeparsfromdata(data, verbose=verbose))
        return None




    def interp(self, ind=0, start=2000, end=2030, dt=0.2, tvec=None, verbose=2):
        """ Prepares model parameters to run the simulation. """
        printv('Making model parameters...', 1, verbose)
        
        P = self.pars[ind] # Shorten name of parameters thing
        simpars = odict() # Used to be called M
        if tvec is not None: simpars['tvec'] = tvec
        else: simpars['tvec'] = arange(start, end+dt, dt) # Store time vector with the model parameters
        popkeys = dcp(P['popkeys'])
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
        simpars['popsize'] = popsize2simpar(P['popsize'], popkeys) # Population size
        simpars['initprev'] = P['initprev'] # Initial HIV prevalence
        simpars['stiprev'] = datapar2simpar(P['stiprev'], popkeys) # STI prevalence
        simpars['death']  = datapar2simpar(P['death'], popkeys)  # Death rates
        simpars['tbprev'] = datapar2simpar(P['tbprev'], popkeys) # TB prevalence
        
        ## Testing parameters -- most are data
        simpars['hivtest'] = datapar2simpar(P['hivtest'], popkeys) # HIV testing rates
        simpars['aidstest'] = datapar2simpar(P['aidstest'], tot) # AIDS testing rates
        simpars['tx'] = datapar2simpar(P['numtx'], tot, smoothness=int(1/dt)) # Number of people on first-line treatment -- 0 since overall not by population
    
        ## MTCT parameters
        simpars['numpmtct'] = datapar2simpar(P['numpmtct'], tot)
        simpars['birth']    = datapar2simpar(P['birth'], popkeys)
        simpars['breast']   = datapar2simpar(P['breast'], tot)  
        
        ## Sexual behavior parameters -- all are parameters so can loop over all
        simpars['numacts'] = odict()
        simpars['condom']  = odict()
        simpars['numacts']['reg'] = datapar2simpar(P['numactsreg'], popkeys) 
        simpars['numacts']['cas'] = datapar2simpar(P['numactscas'], popkeys) 
        simpars['numacts']['com'] = datapar2simpar(P['numactscom'], popkeys) 
        simpars['numacts']['inj'] = datapar2simpar(P['numinject'], popkeys) 
        simpars['condom']['reg']  = datapar2simpar(P['condomreg'], popkeys) 
        simpars['condom']['cas']  = datapar2simpar(P['condomcas'], popkeys) 
        simpars['condom']['com']  = datapar2simpar(P['condomcom'], popkeys) 
        
        ## Circumcision parameters
        simpars['circum']    = datapar2simpar(P['circum'], popkeys) # Circumcision percentage
        if  'numcircum' in P.keys():
            simpars['numcircum'] = datapar2simpar(P['numcircum'], tot) # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
        else:
            simpars['numcircum'] = zeros(shape(simpars['tvec'])) # Number to be circumcised -- to be populated by the relevant CCOC at non-zero allocations
        
        ## Drug behavior parameters
        simpars['numost'] = datapar2simpar(P['numost'], tot)
        simpars['sharing'] = datapar2simpar(P['sharing'], popkeys)
        
        ## Other intervention parameters (proportion of the populations, not absolute numbers)
        simpars['prep'] = datapar2simpar(P['prep'], popkeys)
        
        ## Matrices can be used almost directly
        for parname in ['partreg', 'partcas', 'partcom', 'partinj', 'transit']:
            simpars[parname] = array(P[parname])
        
        ## Constants...can be used directly
        simpars['const'] = P['const']
        
        ## Calculate total acts
        simpars['totalacts'] = totalacts(simpars, npts)
        
        ## Program parameters not related to data
        simpars['propaware'] = zeros(shape(simpars['hivtest'])) # Initialize proportion of PLHIV aware of their status
        simpars['txtotal'] = zeros(shape(simpars['tx'])) # Initialize total number of people on treatment
        
        ## Metaparameters
        simpars['force'] = array(P['force'][:])
        simpars['inhomo'] = array(P['inhomo'][:])
        
        ## Other things that can be used directly as well
        simpars['male'] = P['male']
        simpars['female'] = P['female']

        printv('...done making model parameters.', 2, verbose)
        return simpars
    
    
            
        


    
