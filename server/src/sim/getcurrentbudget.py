def getcurrentbudget(D, alloc=None, randseed=None):
    """
    Purpose: get the parameters corresponding to a given allocation. If no allocation is specified, this function also estimates the current budget
    Inputs: D, alloc (optional)
    Returns: D
    Version: 2014nov30
    """
    from makeccocs import ccoeqn, cceqn, cc2eqn, cco2eqn, coverage_params, makesamples
    from numpy import nan, zeros, array, isnan
    from utils import sanitize, perturb
    
     # Set defaults, stored as [median, lower bound, upperbound]. ONLY for use in BE. In FE, if ccocs haven't been defined then the user won't get to this step
    default_convertedccparams = [[0.8, 4.9e-06], [0.8, 4.7e-06], [0.8, 5.1e-06]]
    default_convertedccoparams = [[0.8, 4.9e-06, 0.4, 0.8, 0], [0.8, 4.7e-06, 5.1e-06, 0.4, 0.8, 0], [0.8, 4.9e-06, 0.4, 0.8, 0]]

    npts = len(D['opt']['partvec']) # Number of parameter points

    # Initialise currentbudget if needed
    allocprovided = not(isinstance(alloc,type(None)))

    # Initialise currentcoverage and currentnonhivdalys
    currentcoverage = zeros((D['G']['nprogs'], npts))
    currentnonhivdalysaverted = zeros(npts)

    # Initialise parameter structure (same as D['P'])
    for param in D['P'].keys():
        if isinstance(D['P'][param], dict) and 'p' in D['P'][param].keys():
            D['P'][param]['c'] = nan+zeros((len(D['P'][param]['p']), npts))

    # Loop over programs
    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        
        # Get allocation - either it's been passed in, or we figure it out from the data
        totalcost = alloc[prognumber, :] if allocprovided else sanitize(D['data']['costcov']['cost'][prognumber]).tolist()

        # Extract and sum the number of non-HIV-related DALYs 
        nonhivdalys = D['programs'][prognumber]['nonhivdalys']
        program_ccparams = D['programs'][prognumber]['convertedccparams']
        use_default_ccparams = not program_ccparams or (not isinstance(program_ccparams, list) and isnan(program_ccparams))

        # Extract the converted cost-coverage parameters... or if there aren't any, use defaults (for sim only; FE produces warning)
        convertedccparams = program_ccparams if not use_default_ccparams else default_convertedccparams
        if randseed>=0: convertedccparams[0][1] = array(perturb(1,(array(convertedccparams[2][1])-array(convertedccparams[1][1]))/2., randseed=randseed)) - 1 + array(convertedccparams[0][1])
        currentcoverage[prognumber, :] = cc2eqn(totalcost, convertedccparams[0]) if len(convertedccparams[0])==2 else cceqn(totalcost, convertedccparams[0])
        currentnonhivdalysaverted += nonhivdalys*currentcoverage[prognumber, :]

        # Loop over effects
        for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):

            # Get population and parameter info
            popname, parname = effect['popname'], effect['param']
            
            # Is the affected parameter coverage?
            if parname in coverage_params:
                D['P'][parname]['c'][:] = currentcoverage[prognumber]
            # ... or not?
            else:
                try: # Get population number...
                    popnumber = D['data']['meta']['pops']['short'].index(popname)
                except: # ... or raise error if it isn't recognised
                    print('Cannot recognise population %s, it is not in %s' % (popname, D['data']['meta']['pops']['short']))
                try: # Use parameters if there... 
                    convertedccoparams = effect['convertedccoparams']
                    if randseed>=0:
                        try: 
                            convertedccoparams[0][1] = array(perturb(1,(convertedccoparams[2][1]-convertedccoparams[1][1])/2, randseed=randseed)) - 1 + convertedccoparams[0][1]
                            convertedccoparams[-1], convertedccoparams[-2] = makesamples(effect['coparams'], effect['convertedcoparams'][0], effect['convertedcoparams'][1], effect['convertedcoparams'][2], effect['convertedcoparams'][3], randseed=randseed)
                        except: 
                            print('Random sampling for CCOCs failed for program %s, makesamples failed with parameters %s and %s' % (progname, effect.coparams, effect.convertedcoparams))
                            convertedccoparams = default_convertedccoparams
                except: # ... or use defaults if parameters are not there
                    print('Calculating parameter from CCOCs failed for program %s; cost-outcome curve does not exist for population %s, parameters %s' % (progname, effect['popname'], effect['param']))
                    convertedccoparams = default_convertedccoparams

                D['P'][parname]['c'][popnumber] = cco2eqn(totalcost, convertedccoparams[0]) if len(convertedccparams[0])==2 else ccoeqn(totalcost, convertedccoparams[0])            

    return D, currentcoverage, currentnonhivdalysaverted
    
