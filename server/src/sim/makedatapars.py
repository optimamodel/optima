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
    D.G.meta = D.data.meta # Copy metadata
    
    ## Key parameters
    for parname in D.data.key.keys():
        printv('Converting data parameter %s...' % parname, 2, verbose)
        D.P[parname] = dataindex(D.data.key[parname][0], 0) # Population size and prevalence -- # TODO: use uncertainties!
    
    ## Loop over parameters that can be converted automatically
    for parclass in ['epi', 'txrx', 'sex', 'inj']:
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        for parname in D.data[parclass].keys():
            printv('Converting data parameter %s...' % parname, 4, verbose)
            if parname in ['numfirstline','numsecondline','txelig']:
                D.P[parname] = data2par(D.data[parclass][parname], usetime=True)
            else:
                D.P[parname] = data2par(D.data[parclass][parname])
    
    
    ## Matrices can be used directly
    for parclass in ['pships', 'transit']:
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        D.P[parclass] = D.data[parclass]
    
    ## Constants...just take the best value for now -- # TODO: use the uncertainty
    D.P.const = struct()
    for parclass in D.data.const.keys():
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        if type(D.data.const[parclass])==struct: 
            D.P.const[parclass] = struct()
            for parname in D.data.const[parclass].keys():
                printv('Converting data parameter %s...' % parname, 4, verbose)
                D.P.const[parclass][parname] = D.data.const[parclass][parname][0] # Taking best value only, hence the 0
    
    ## Program cost data
    D.data.origalloc = zeros(D.G.nprogs)
    for prog in range(D.G.nprogs):
        totalcost = D.data.costcov.cost[prog]
        totalcost = array(totalcost)
        totalcost = totalcost[~isnan(totalcost)]
        totalcost = totalcost[-1]
        D.data.origalloc[prog] = totalcost
    
    
    ## Change sizes of circumcision and births
    def popexpand(origarray, popbool):
        """ For variables that are only defined for certain populations, expand to the full array. WARNING, doesn't work for time """
        from copy import deepcopy
        newarray = deepcopy(origarray)
        newarray.p = zeros(shape(D.G.meta.pops.male))
        if 't' in newarray.keys(): raise Exception('Shouldn''t be using time')
        count = -1
        for i,tf in enumerate(popbool):
            if tf:
                count += 1
                newarray.p[i] = origarray.p[count]
        
        return newarray
    
    D.P.birth     = popexpand(D.P.birth,     array(D.G.meta.pops.female)==1)
    D.P.circum    = popexpand(D.P.circum,    array(D.G.meta.pops.male)==1)
#    D.P.numcircum = popexpand(D.P.numcircum, array(D.G.meta.pops.male)==1)
            
            

    printv('...done converting data to parameters.', 2, verbose)
    
    return D
