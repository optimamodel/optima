## Imports
from math import pow as mpow
from numpy import zeros, exp, maximum, minimum, hstack, inf
from optima import printv, tic, toc, dcp, odict, findinds


def model(simpars, settings, verbose=2, safetymargin=0.8, benchmark=False):
    """
    This function runs the model. Safetymargin is how close to get to moving all people from a compartment in a single timestep.
    
    Version: 2015dec21 by cliffk
    """
    
    printv('Running model...', 1, verbose, newline=False)
    if benchmark: starttime = tic()


    ###############################################################################
    ## Setup
    ###############################################################################

    # Hard-coded parameters that hopefully don't matter too much
    eps = 1e-3 # Define another small number to avoid divide-by-zero errors
    cd4transnorm = 1.5 # Was 3.3 -- estimated overestimate of infectiousness by splitting transmissibility multiple ways -- see commit 57057b2486accd494ef9ce1379c87a6abfababbd for calculations
    
    # Initialize basic quantities
    popkeys    = simpars['popkeys']
    npops      = len(popkeys)
    simpars    = dcp(simpars)
    tvec       = simpars['tvec']
    dt         = tvec[1]-tvec[0]      # Shorten dt
    npts       = len(tvec) # Number of time points
    ncd4       = settings.ncd4      # Shorten number of CD4 states
    nstates    = settings.ncomparts   # Shorten number of health states
    people     = zeros((nstates, npops, npts)) # Matrix to hold everything
    allpeople  = zeros((npops, npts)) # Population sizes
    effhivprev = zeros((npops, 1))    # HIV effective prevalence (prevalence times infectiousness)
    inhomo     = zeros(npops)    # Inhomogeneity calculations
    
    # Initialize arrays
    raw             = odict()    # Sim output structure
    raw['tvec']     = tvec
    raw['popkeys']  = popkeys
    raw['sexinci']  = zeros((npops, npts)) # Incidence through sex
    raw['injinci']  = zeros((npops, npts)) # Incidence through injecting
    raw['inci']     = zeros((npops, npts)) # Total incidence
    raw['births']   = zeros((1, npts))     # Number of births
    raw['mtct']     = zeros((1, npts))     # Number of mother-to-child transmissions
    raw['diag']     = zeros((npops, npts)) # Number diagnosed per timestep
    raw['newtreat'] = zeros((npops, npts)) # Number initiating ART1 per timestep
    raw['death']    = zeros((npops, npts)) # Number of deaths per timestep
    
    # Biological and failure parameters -- death etc
    prog = simpars['const']['progacute':'proggt50']
    recov = simpars['const']['recovgt500':'recovgt50']
    death = simpars['const']['deathacute':'deathaids']
    cd4trans = simpars['const']['cd4transacute':'cd4transaids']
    deathtx    = simpars['const']['deathtreat']   # Death rate whilst on treatment
    
    # Calculate other things outside the loop
    cd4trans /= cd4transnorm # Normalize CD4 transmission
    dxfactor = simpars['const']['effdx'] * cd4trans # Include diagnosis efficacy
    txfactor = simpars['const']['efftx'] * dxfactor # And treatment efficacy

    # Disease state indices
    sus  = settings.uncirc  # Susceptible
    undx = settings.undiag # Undiagnosed
    dx   = settings.diag   # Diagnosed
    tx  = settings.treat  # Treatment -- 1st line
    popsize = dcp(simpars['popsize']) # Population sizes
    
    # Infection propabilities
    male = simpars['male']
    female = simpars['female']
    transinj = simpars['const']['transinj']      # Injecting
    
    # Further potential effects on transmission
    effsti    = simpars['const']['effsti'] * simpars['stiprev']  # STI effect
    effcirc   = 1 - simpars['const']['effcirc']            # Circumcision effect
    effprep   = (1 - simpars['const']['effprep']) * simpars['prep'] # PrEP effect
    effcondom = 1 - simpars['const']['effcondom']          # Condom effect
    
    # Intervention uptake (P=proportion, N=number)
    sharing  = simpars['sharing']   # Sharing injecting equiptment (P)
    numtx    = simpars['numtx']       # 1st line treatement (N) -- tx already used for index of people on treatment
    hivtest  = simpars['hivtest']   # HIV testing (P)
    aidstest = simpars['aidstest']  # HIV testing in AIDS stage (P)
    circum = simpars['circum']
    
    # Calculations...used to be inside time loop
    circeff = 1 - effcirc*circum
    prepeff = 1 - effprep
    stieff  = 1 + effsti
    
    # Force of infection metaparameter
    force = simpars['force']
    inhomopar = simpars['inhomo'] # WARNING, name is not consistent -- should be "inhomo"
    
    
    
    
    
    
    
    ###########################################
    # Set initial epidemic conditions 
    ###########################################
    
    # Set parameters
    prevtoforceinf = 0.1 # Assume force-of-infection is proportional to prevalence -- 0.1 means that if prevalence is 10%, annual force-of-infection is 1%
    efftreatmentrate = 0.1 # Inverse of average duration of treatment in years...I think
    
    # Shorten key variables
    initpeople = zeros((settings.ncomparts,npops)) 
    allinfected = simpars['popsize'][:,0] * simpars['initprev'][:] # Set initial infected population
    
    # Can calculate equilibrium for each population separately
    for p in range(npops):
        # Set up basic calculations
        popinfected = allinfected[p]
        uninfected = simpars['popsize'][p,0] - popinfected # Set initial susceptible population -- easy peasy! -- should this have F['popsize'] involved?
        
        # Treatment & treatment failure
        fractotal =  popinfected / sum(allinfected) # Fractional total of infected people in this population
        treatment = simpars['numtx'][0] * fractotal # Number of people on 1st-line treatment
        if treatment > popinfected: # More people on treatment than ever infected, uh oh!
            treatment = popinfected
        
        # Diagnosed & undiagnosed
        nevertreated = popinfected - treatment
        assumedforceinf = simpars['initprev'][p]*prevtoforceinf # To calculate ratio of people in the initial category, need to estimate the force-of-infection
        undxdxrates = assumedforceinf + simpars['hivtest'][p,0] # Ratio of undiagnosed to diagnosed
        undiagnosed = nevertreated * assumedforceinf / undxdxrates     
        diagnosed = nevertreated * simpars['hivtest'][p,0] / undxdxrates
        
        # Set rates within
        progratios = hstack([prog, simpars['const']['deathaids']]) # For last rate, use AIDS death as dominant rate
        progratios = (1/progratios)  / sum(1/progratios) # Normalize
        recovratios = hstack([inf, recov, efftreatmentrate]) # Not sure if this is right...inf since no progression to acute, treatmentrate since main entry here -- check
        recovratios = (1/recovratios)  / sum(1/recovratios) # Normalize
        
        # Final calculations
        undiagnosed *= progratios
        diagnosed *= progratios
        treatment *= recovratios
        
        # Populated equilibrated array
        initpeople[settings.uncirc, p] = uninfected
        initpeople[settings.undiag, p] = undiagnosed
        initpeople[settings.diag, p] = diagnosed
        initpeople[settings.treat, p] = treatment
    
        if not((initpeople>=0).all()): # If not every element is a real number >0, throw an error
            err = 'Non-positive people found during epidemic initialization!'  
            raise Exception(err)
            
    people[:,:,0] = initpeople # No it hasn't, so run equilibration
    
    
    ###############################################################################
    ## Compute the effective numbers of acts outside the time loop
    ###############################################################################
    sexactslist = []
    injactslist = []
    
    # Sex
    for act in ['reg','cas','com']:
        for key in simpars['acts'+act]:
            this = {}
            this['acts'] = simpars['acts'+act][key]
            this['cond'] = 1 - simpars['cond'+act][key]*effcondom
            this['pop1'] = popkeys.index(key[0])
            this['pop2'] = popkeys.index(key[1])
            if     male[this['pop1']] and   male[this['pop2']]: this['trans'] = simpars['const']['transmmi']
            # WARNING how to specify receptive male-male??
            elif   male[this['pop1']] and female[this['pop2']]: this['trans'] = simpars['const']['transmfi']  
            elif female[this['pop1']] and   male[this['pop2']]: this['trans'] = simpars['const']['transmfr']
            else: raise Exception('Not able to figure out the sex of "%s" and "%s"' % (key[0], key[1]))
            sexactslist.append(this)
    
    # Injection
    for key in simpars['actsinj']:
        this = {}
        this['acts'] = simpars['actsinj'][key]
        this['pop1'] = popkeys.index(key[0])
        this['pop2'] = popkeys.index(key[1])
        injactslist.append(this)
    
    
    




    ###############################################################################
    ## Run the model -- numerically integrate over time
    ###############################################################################

    for t in range(npts): # Loop over time
        printv('Timestep %i of %i' % (t+1, npts), 8, verbose)
        
        ## Calculate "effective" HIV prevalence -- taking diagnosis and treatment into account
        for pop in range(npops): # Loop over each population group
            allpeople[pop,t] = sum(people[:,pop,t]) # All people in this population group at this time point
            if not(allpeople[pop,t]>0): raise Exception('No people in population %i at timestep %i (time %0.1f)' % (pop, t, tvec[t]))
            effundx = sum(cd4trans * people[undx,pop,t]); # Effective number of infecious undiagnosed people
            effdx   = sum(dxfactor * people[dx,pop,t]) # ...and diagnosed/failed
            efftx   = sum(txfactor * people[tx,pop,t]) # ...and treated
            effhivprev[pop] = (effundx+effdx+efftx) / allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effhivprev[pop]>=0): raise Exception('HIV prevalence invalid in population %s! (=%f)' % (pop, effhivprev[pop]))
        
        ## Calculate inhomogeneity in the force-of-infection based on prevalence
        for pop in range(npops):
            c = inhomopar[pop]
            thisprev = sum(people[1:,pop,t]) / allpeople[pop,t] # Probably a better way of doing this
            inhomo[pop] = (c+eps) / (exp(c+eps)-1) * exp(c*(1-thisprev)) # Don't shift the mean, but make it maybe nonlinear based on prevalence
        
        
        
        
        
        
        
        ###############################################################################
        ## Calculate force-of-infection (forceinf)
        ###############################################################################
        
        # Reset force-of-infection vector for each population group
        forceinfvec = zeros(npops)
        
        # Loop over all acts (partnership pairs) -- force-of-infection in pop1 due to pop2
        for this in sexactslist:
            acts = this['acts'][t]
            cond = this['cond'][t]
            pop1 = this['pop1']
            pop2 = this['pop2']
            thistrans = this['trans']
            
            thisforceinf = 1 - mpow((1-thistrans*circeff[pop1,t]*prepeff[pop1,t]*stieff[pop1,t]), (dt*cond*acts*effhivprev[pop2]))
            forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-thisforceinf)          
            
        # Injection-related infections -- force-of-infection in pop1 due to pop2
        for this in injactslist:
            effinj = this['acts'][t]
            pop1 = this['pop1']
            pop2 = this['pop2']
            osteff = 1 # WARNING, TEMP osteff[pop1,t]
            
            thisforceinf = 1 - mpow((1-transinj), (dt*sharing[pop1,t]*effinj*osteff*effhivprev[pop2])) 
            forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-thisforceinf)
        
        if not(all(forceinfvec>=0)):
            invalid = [simpars['popkeys'][i] for i in findinds(forceinfvec<0)]
            errormsg = 'Force-of-infection is invalid in population %s' % invalid
            raise Exception(errormsg)
            




        
        ###############################################################################
        ## The ODEs
        ###############################################################################
    
        ## Set up
    
        # New infections -- through pre-calculated force of infection
        newinfections = forceinfvec * force * inhomo * people[0,:,t] # Will be useful to define this way when calculating 'cost per new infection'
    
        # Initalise / reset arrays
        dU = []; dD = []; dT = []; # Reset differences
        testingrate  = [0] * ncd4
        newdiagnoses = [0] * ncd4
        newtreat1    = [0] * ncd4
        background   = simpars['death'][:, t] # make OST effect this death rates
        
        ## Susceptibles
        dS = -newinfections # Change in number of susceptibles -- death rate already taken into account in pm.totalpop and dt
        raw['inci'][:,t] = (newinfections)/float(dt)  # Store new infections AND new MTCT births

        ## Undiagnosed
        for cd4 in range(ncd4):
            if cd4>0: 
                progin = dt*prog[cd4-1]*people[undx[cd4-1],:,t]
            else: 
                progin = 0 # Cannot progress into acute stage
            if cd4<ncd4-1: 
                progout = dt*prog[cd4]*people[undx[cd4],:,t]
                testingrate[cd4] = hivtest[:,t] # Population specific testing rates
            else: 
                progout = 0  # Cannot progress out of AIDS stage
                testingrate[cd4] = maximum(hivtest[:,t], aidstest[t]) # Testing rate in the AIDS stage (if larger!)
            newdiagnoses[cd4] = dt * people[undx[cd4],:,t] * testingrate[cd4]
            hivdeaths   = dt * people[undx[cd4],:,t] * death[cd4]
            otherdeaths = dt * people[undx[cd4],:,t] * background
            dU.append(progin - progout - newdiagnoses[cd4] - hivdeaths - otherdeaths) # Add in new infections after loop
            raw['diag'][:,t]    += newdiagnoses[cd4]/dt # Save annual diagnoses 
            raw['death'][:,t] += hivdeaths/dt    # Save annual HIV deaths 
        dU[0] = dU[0] + newinfections # Now add newly infected people
        
        ## Diagnosed
        newtreat1tot = numtx[t] - people[tx,:,t].sum() # Calculate difference between current people on treatment and people needed
        currentdiagnosed = people[dx,:,t] # Find how many people are diagnosed
        for cd4 in range(ncd4):
            if cd4>0: 
                progin = dt*prog[cd4-1]*people[dx[cd4-1],:,t]
            else: 
                progin = 0 # Cannot progress into acute stage
            if cd4<ncd4-1: 
                progout = dt*prog[cd4]*people[dx[cd4],:,t]
            else: 
                progout = 0 # Cannot progress out of AIDS stage
            newtreat1[cd4] = newtreat1tot * currentdiagnosed[cd4,:] / (eps+currentdiagnosed.sum()) # Pull out evenly among diagnosed
            hivdeaths   = dt * people[dx[cd4],:,t] * death[cd4]
            otherdeaths = dt * people[dx[cd4],:,t] * background
            inflows = progin + newdiagnoses[cd4]
            outflows = progout + hivdeaths + otherdeaths
            newtreat1[cd4] = minimum(newtreat1[cd4], safetymargin*(currentdiagnosed[cd4,:]+inflows-outflows)) # Allow it to go negative
            newtreat1[cd4] = maximum(newtreat1[cd4], -safetymargin*people[tx[cd4],:,t]) # Make sure it doesn't exceed the number of people in the treatment compartment
            dD.append(inflows - outflows - newtreat1[cd4])
            raw['newtreat'][:,t] += newtreat1[cd4]/dt # Save annual treatment initiation
            raw['death'][:,t]  += hivdeaths/dt # Save annual HIV deaths 
        
        ## 1st-line treatment
        for cd4 in range(ncd4):
            if (cd4>0 and cd4<ncd4-1): # CD4>0 stops people from moving back into acute
                recovin = dt*recov[cd4-1]*people[tx[cd4+1],:,t]
            else: 
                recovin = 0 # Cannot recover in to acute or AIDS stage
            if cd4>1: # CD4>1 stops people from moving back into acute
                recovout = dt*recov[cd4-2]*people[tx[cd4],:,t]
            else: 
                recovout = 0 # Cannot recover out of gt500 stage (or acute stage)
            hivdeaths   = dt * people[tx[cd4],:,t] * death[cd4] * deathtx # Use death by CD4 state if lower than death on treatment
            otherdeaths = dt * people[tx[cd4],:,t] * background
            dT.append(recovin - recovout + newtreat1[cd4] - hivdeaths - otherdeaths)
            raw['death'][:,t] += hivdeaths/dt # Save annual HIV deaths 
        


        ###############################################################################
        ## Update next time point and check for errors
        ###############################################################################
        
        # Ignore the last time point, we don't want to update further
        if t<npts-1:
            change = zeros((nstates, npops))
            change[sus,:] = dS
            for cd4 in range(ncd4): # this could be made much more efficient
                change[undx[cd4],:] = dU[cd4]
                change[dx[cd4],:]   = dD[cd4]
                change[tx[cd4],:]  = dT[cd4]
            people[:,:,t+1] = people[:,:,t] + change # Update people array
            newpeople = popsize[:,t+1]-people[:,:,t+1].sum(axis=0) # Number of people to add according to simpars['popsize'] (can be negative)
            for pop in range(npops): # Loop over each population, since some might grow and others might shrink
                if newpeople[pop]>=0: # People are entering: they enter the susceptible population
                    people[0,pop,t+1] += newpeople[pop]
                else: # People are leaving: they leave from susceptible still
                    if (people[0,pop,t+1] + newpeople[pop])>0: # Don't allow negative people
                        people[0,pop,t+1] += newpeople[pop]
                    else:
                        people[:,pop,t+1] *= popsize[pop,t]/sum(people[:,pop,t]);
            if not((people[:,:,t+1]>=0).all()): # If not every element is a real number >0, throw an error
                for errstate in range(nstates): # Loop over all heath states
                    for errpop in range(npops): # Loop over all populations
                        if not(people[errstate,errpop,t+1]>=0):
                            printv('WARNING, Non-positive people found: people[%s, %s, %s] = %s' % (errstate, errpop, t+1, people[errstate,errpop,t+1]), 4, verbose=verbose)
                            people[errstate,errpop,t+1] = 0 # Reset
                
    # Append final people array to sim output
    raw['people'] = people
    
    printv('  ...done running model.', 2, verbose)
    if benchmark: toc(starttime)
    return raw # Return raw results





def runmodel(simpars=None, pars=None, settings=None, start=2000, end=2030, dt=0.2, name=None, uuid=None):
    from optima import makesimpars, Resultset
    if simpars is None:
        if pars is None: raise Exception('runmodel() requires either simpars or pars input; neither provided')
        simpars = makesimpars(pars, start=start, end=end, name=name, uuid=uuid)
    raw = model(simpars, settings) # THIS IS SPINAL OPTIMA
    results = Resultset(project, simpars, raw) # Create structure for storing results
    results.make() # Generate derived results
    return results