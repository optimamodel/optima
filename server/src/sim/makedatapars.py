"""
MAKEDATAPARS

This function turns the data into model parameters.

Version: 2014oct29
"""

def makedatapars(D, verbose=2):
    
    
    ###############################################################################
    ## Preliminaries
    ###############################################################################

    if verbose>=1: print('Converting data to parameters...')
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    from matplotlib.pylab import array, isnan, zeros, shape, mean
    
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
    
    
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    D.P = struct() # Initialize parameters structure
    D.P.__doc__ = 'Parameters that have been directly derived from the data, which are then used to create the model parameters'
    
    ## Epidemilogy parameters -- most are data
    D.P.popsize = data2par(D.data.epi.popsize) # Population size -- TODO: don't take average for this!
    D.P.hivprev = data2par(D.data.epi.hivprev) # Initial HIV prevalence -- TODO: don't take average for this
    D.P.stiprev = data2par(D.data.epi.stiprev) # STI prevalence
    ## TB prevalence @@@
    
    ## Testing parameters -- most are data
    D.P.hivtest = data2par(D.data.txrx.testrate) # HIV testing rates
    D.P.aidstest = data2par(D.data.txrx.aidstestrate) # AIDS testing rates
    
    ## Sexual behavior parameters -- all are parameters so can loop over all
    for parname in D.data.sex.keys():
        D.P[parname] = data2par(D.data.sex[parname])
    
    ## Drug behavior parameters
    D.P.numinject = data2par(D.data.drug.numinject)
    D.P.ost = data2par(D.data.drug.ost)
    D.P.sharing = data2par(D.data.drug.sharing)
    
    ## Matrices can be used directly
    D.P.pships = D.data.pships
    D.P.transit = D.data.transit
    
    ## Constants...just take the best value for now -- TODO: use the uncertainty
    D.P.const = struct()
    for parname in D.data.const.keys():
        if type(D.data.const[parname])==struct:
            D.P.const[parname] = struct()
            for parname2 in D.data.const[parname].keys():
                D.P.const[parname][parname2] = D.data.const[parname][parname2][0] # Taking best value only, hence the 0
        else:
            D.P.const[parname] = D.data.const[parname][0]
            
            
            
    
    ###############################################################################
    ## Set up general parameters
    ###############################################################################
    D.G.ncd4 = len(D.data.const.cd4trans) # Get number of CD4 states from the length of a reliable field, like CD4-related transmissibility
    D.G.nstates = 1+D.G.ncd4*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
    
    # Define CD4 states
    from matplotlib.pylab import arange
    D.G.sus  = arange(0,1)
    D.G.undx = arange(0*D.G.ncd4+1, 1*D.G.ncd4+1)
    D.G.dx   = arange(1*D.G.ncd4+1, 2*D.G.ncd4+1)
    D.G.tx1  = arange(2*D.G.ncd4+1, 3*D.G.ncd4+1)
    D.G.fail = arange(3*D.G.ncd4+1, 4*D.G.ncd4+1)
    D.G.tx2  = arange(4*D.G.ncd4+1, 5*D.G.ncd4+1)


    if verbose>=2: print('  ...done converting data to parameters.')
    
    return D
