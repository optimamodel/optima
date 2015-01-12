def makedatapars(D, verbose=2):
    """
    Translates the raw data (which were read from the spreadsheet). into
    parameters that can be used in the model. These are then used 
    These data are then used to update the corresponding model (project).
    This method should be called before any simulation can run.
    
    Version: 2014nov25 by cliffk
    """
    
    ###############################################################################
    ## Preliminaries
    ###############################################################################

    
    from printv import printv
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    from numpy import array, isnan, zeros, shape, mean, arange
    from utils import sanitize
    printv('Converting data to parameters...', 1, verbose)
    
    
    
        
    
    def data2par(dataarray, usetime=False):
        """ Take an array of data and turn it into default parameters -- here, just take the means """
        nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
        output = struct() # Create structure
        output.p = [0]*nrows # Initialize array for holding population parameters
        if usetime:
            output.t = [0]*nrows # Initialize array for holding time parameters
            for r in xrange(nrows): 
                output.p[r] = sanitize(dataarray[r]) # Store each extant value
                output.t[r] = arange(D.G.datastart, D.G.dataend+1)[~isnan(dataarray[r])] # Store each year

        else:
            for r in xrange(nrows): 
                output.p[r] = mean(sanitize(dataarray[r])) # Calculate mean for each population
        
        return output

    def dataindex(dataarray, index):
        """ Take an array of data return either the first or last (...or some other) non-NaN entry """
        nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
        output = zeros(nrows) # Create structure
        for r in xrange(nrows): 
            output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
        
        return output
    
    
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    D.P = struct() # Initialize parameters structure
    D.P.__doc__ = 'Parameters that have been directly derived from the data, which are then used to create the model parameters'
    
    ## Key parameters
    for parname in D.data.key.keys():
        printv('Converting data parameter %s...' % parname, 2, verbose)
        D.P[parname] = dataindex(D.data.key[parname][0], 0) # Population size and prevalence -- # TODO: use uncertainties!
    
    ## Loop over parameters that can be converted automatically
    for parclass in ['epi', 'txrx', 'sex', 'inj']:
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        for parname in D.data[parclass].keys():
            printv('Converting data parameter %s...' % parname, 4, verbose)
            if parname in ['numfirstline','numsecondline']:
                D.P[parname] = data2par(D.data[parclass][parname], usetime=True)
            else:
                D.P[parname] = data2par(D.data[parclass][parname])
    
    ## Matrices can be used directly
    for parclass in ['pships', 'transit']:
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        D.P[parclass] = D.data[parclass]
    
    ## Constants...just take the best value for now -- # TODO: use the uncertainty
    for uberclass in ['const', 'cost']:
        D.P[uberclass] = struct()
        for parclass in D.data[uberclass].keys():
            printv('Converting data parameter %s...' % parclass, 3, verbose)
            if type(D.data[uberclass][parclass])==struct: 
                D.P[uberclass][parclass] = struct()
                for parname in D.data[uberclass][parclass].keys():
                    printv('Converting data parameter %s...' % parname, 4, verbose)
                    D.P[uberclass][parclass][parname] = D.data[uberclass][parclass][parname][0] # Taking best value only, hence the 0
    
    ## Program cost data
    D.A = [struct()] # Initialize allocations list
    D.A[0].alloc = zeros(D.G.nprogs)
    for prog in range(D.G.nprogs): #TODO CK which one of the branches should be left?
        if D.data.meta.progs.saturating[prog]:
            totalcost = D.data.costcov.cost[prog]
            totalcost = array(totalcost)
            totalcost = totalcost[~isnan(totalcost)]
            totalcost = totalcost[-1]
            D.A[0].alloc[prog] = totalcost
        else:
            unitcost, cov = D.data.costcov.cost[prog], D.data.costcov.cov[prog] 
            unitcost, cov = array(unitcost), array(cov)
            unitcost, cov = unitcost[~isnan(unitcost)], cov[~isnan(cov)]
            unitcost, cov = unitcost[-1], cov[-1]
            totalcost = unitcost*cov
            D.A[0].alloc[prog] = totalcost
            
    
    ## TODO: disutility, economic data etc.
            
            
    
    ###############################################################################
    ## Set up general parameters
    ###############################################################################
    D.G.meta = D.data.meta # Copy metadata
    D.G.ncd4 = len(D.data.const.cd4trans) # Get number of CD4 states from the length of a reliable field, like CD4-related transmissibility
    D.G.nstates = 1+D.G.ncd4*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
    
    # Define CD4 states
    D.G.sus  = arange(0,1)
    D.G.undx = arange(0*D.G.ncd4+1, 1*D.G.ncd4+1)
    D.G.dx   = arange(1*D.G.ncd4+1, 2*D.G.ncd4+1)
    D.G.tx1  = arange(2*D.G.ncd4+1, 3*D.G.ncd4+1)
    D.G.fail = arange(3*D.G.ncd4+1, 4*D.G.ncd4+1)
    D.G.tx2  = arange(4*D.G.ncd4+1, 5*D.G.ncd4+1)
    
    # Define male populations
    D.G.male = zeros(D.G.npops)
    for key in ['reg', 'cas', 'com']:
        D.G.male += array(D.data.pships[key]).sum(axis=1) # Find insertive acts
    D.G.male = D.G.male>0 # Convert to Boolean array
    
    # Define injecting populations
    D.G.pwid = zeros(D.G.npops)
    for ax in [0,1]:
        D.G.pwid += array(D.data.pships.inj).sum(axis=ax) # Find injecting acts
    D.G.pwid = D.G.pwid>0 # Convert to Boolean array


    printv('...done converting data to parameters.', 2, verbose)
    
    return D
