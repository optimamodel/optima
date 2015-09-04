###############################################################################
##### 2.0 STATUS: works, but need to tidy up
###############################################################################

def makeparams(data, verbose=2):
    """
    Translates the raw data (which were read from the spreadsheet). into
    parameters that can be used in the model. These data are then used to update 
    the corresponding model (project). This method should be called before a 
    simulation is run.
    
    Version: 2015sep04 by cliffk
    """
    
    ###############################################################################
    ## Preliminaries
    ###############################################################################

    
    from utils import printv
    from numpy import array as ar, isnan, zeros, shape, mean
    from utils import sanitize
    printv('Converting data to parameters...', 1, verbose)
    
    
    
        
    
    def data2par(dataarray, usetime=True):
        """ Take an array of data and turn it into default parameters -- here, just take the means """
        nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
        output = dict() # Create structure
        output['p'] = [0]*nrows # Initialize array for holding population parameters
        if usetime:
            output['t'] = [0]*nrows # Initialize array for holding time parameters
            for r in range(nrows): 
                validdata = ~isnan(dataarray[r])
                if sum(validdata): # There's at least one data point
                    output['p'][r] = sanitize(dataarray[r]) # Store each extant value
                    output['t'][r] = ar(data['epiyears'])[~isnan(dataarray[r])] # Store each year
                else: # Blank, assume zero
                    output['p'][r] = ar([0])
                    output['t'][r] = ar([0])

        else:
            print('TMP6666')
            for r in range(nrows): 
                output['p'][r] = mean(sanitize(dataarray[r])) # Calculate mean for each population
                print('TMP223')
        
        return output

    def dataindex(dataarray, index):
        """ Take an array of data return either the first or last (...or some other) non-NaN entry """
        nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
        output = zeros(nrows) # Create structure
        for r in range(nrows): 
            output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
        
        return output
    
    
    
    
    ###############################################################################
    ## Loop over quantities
    ###############################################################################
    
    params = dict() # Initialize parameters structure
    
    ## Key parameters
    for parname in data['key'].keys():
        printv('Converting data parameter %s...' % parname, 2, verbose)
        params[parname] = dataindex(data['key'][parname][0], 0) # Population size and prevalence -- # TODO: use uncertainties!
    
    ## Loop over parameters that can be converted automatically
    for parclass in ['epi', 'txrx', 'sex', 'inj']:
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        for parname in data[parclass].keys():
            printv('Converting data parameter %s...' % parname, 4, verbose)
            if parname in ['numfirstline','numsecondline','txelig']:
                params[parname] = data2par(data[parclass][parname], usetime=True)
            else:
                params[parname] = data2par(data[parclass][parname], usetime=True) # TMP
    
    
    ## Matrices can be used directly
    for parclass in ['pships', 'transit']:
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        params[parclass] = data[parclass]
    
    ## Constants...just take the best value for now -- # TODO: use the uncertainty
    params['const'] = dict()
    for parclass in data['const'].keys():
        printv('Converting data parameter %s...' % parclass, 3, verbose)
        if type(data['const'][parclass])==dict: 
            params['const'][parclass] = dict()
            for parname in data['const'][parclass].keys():
                printv('Converting data parameter %s...' % parname, 4, verbose)
                params['const'][parclass][parname] = data['const'][parclass][parname][0] # Taking best value only, hence the 0
    
#    ## Add a data parameter for number circumcised, if VMMC is a program
#    if  'VMMC' in [p['name'] for p in D['programs']]:
#        printv('Making a data parameter for numcircum', 2, verbose)
#        prognumber = [p['name'] for p in D['programs']].index('VMMC')
#        params['numcircum'] = data2par([data['costcov']['cov'][prognumber]], usetime=True)
    
    ## Change sizes of circumcision and births
    def popexpand(origarray, popbool):
        """ For variables that are only defined for certain populations, expand to the full array. WARNING, doesn't work for time """
        from copy import deepcopy
        newarray = deepcopy(origarray)
        if 't' in newarray.keys(): 
            newarray['p'] = [ar([0]) for i in range(len(data['popprog']['pops']['male']))]
            newarray['t'] = [ar([0]) for i in range(len(data['popprog']['pops']['male']))]
            count = -1
            if hasattr(popbool,'__iter__'): # May or may not be a list
                for i,tf in enumerate(popbool):
                    if tf:
                        count += 1
                        newarray['p'][i] = origarray['p'][count]
                        newarray['t'][i] = origarray['t'][count]
        else: 
            newarray['p'] = zeros(shape(data['popprog']['pops']['male']))
            count = -1
            if hasattr(popbool,'__iter__'): # May or may not be a list
                for i,tf in enumerate(popbool):
                    if tf:
                        count += 1
                        newarray['p'][i] = origarray['p'][count]
        
        return newarray
    
    params['birth']     = popexpand(params['birth'],     ar(data['popprog']['pops']['female'])==1)
    params['circum']    = popexpand(params['circum'],    ar(data['popprog']['pops']['male'])==1)
            
            

    printv('...done converting data to parameters.', 2, verbose)
    
    return params
