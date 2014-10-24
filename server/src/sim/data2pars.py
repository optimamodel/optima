"""
DATA2PARS

This function turns the data into model parameters.

Version: 2014oct16
"""

def data2pars(data,verbose=True):
    
    
    
    ###############################################################################
    ## Preliminaries
    ###############################################################################

    print('Converting data to parameters...')
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    from pylab import array, isnan, zeros, shape, mean
    
    def sanitize(arraywithnans):
        """ Sanitize input to remove NaNs. Warning, does not work on multidimensional data!! """
        arraywithnans = array(arraywithnans) # Make sure it's an array
        sanitized = arraywithnans[~isnan(arraywithnans)]
        return sanitized
        
    def data2par(dataarray):
        """ Take an array of data and turn it into default parameters -- here, just take the means """
        nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops or 1)
        
        output = struct() # Create structure
        output.t = 1 # Set default time pameter -- constant (1) by default
        output.p = zeros(nrows) # Initialize arra for holding population parameters
        
        for r in xrange(nrows): 
            output.p[r] = mean(sanitize(dataarray[r])) # Calculate mean for each population
        
        return output
    
    P = struct() # Initialize parameters structure
    
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    ## Epidemilogy parameters -- most are data
    P.popsize = data2par(data.epi.popsize) # Population size -- TODO: don't take average for this!
    P.hivprev = data2par(data.epi.hivprev) # Initial HIV prevalence -- TODO: don't take average for this
    P.stiprev = data2par(data.epi.stiprev) # STI prevalence
    ## TB prevalence @@@
    
    ## Testing parameters -- most are data
    P.hivtest = data2par(data.txrx.testrate) # HIV testing rates
    P.aidstest = data2par(data.txrx.aidstestrate) # AIDS testing rates
    
    ## Sexual behavior parameters -- all are parameters so can loop over all
    for parname in data.sex.keys():
        P[parname] = data2par(data.sex[parname])
    
    ## Drug behavior parameters
    P.numinject = data2par(data.drug.numinject)
    P.ost = data2par(data.drug.ost)
    P.sharing = data2par(data.drug.sharing)
    
    ## Matrices can be used directly
    P.pships = data.pships
    P.transit = data.transit
    
    ## Constants...just take the best value for now -- TODO: use the uncertainty
    P.const = struct()
    for parname in data.const.keys():
        if type(data.const[parname])==struct:
            P.const[parname] = struct()
            for parname2 in data.const[parname].keys():
                P.const[parname][parname2] = data.const[parname][parname2][0] # Taking best value only, hence the 0
        else:
            P.const[parname] = data.const[parname][0]

    if verbose: print('  ...done converting data to parameters.')
    
    return P