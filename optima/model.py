## Imports
from math import pow as mpow
from numpy import array, zeros, exp, maximum, minimum, median, hstack, inf, shape
from optima import printv, tic, toc, dcp, Resultset


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
    npops      = len(simpars['initprev']) # WARNING TEMP
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
    results         = Resultset()    # Sim output structure
    results.tvec    = simpars['tvec']   # Append time vector
    results.sexinci = zeros((npops, npts)) # Incidence through sex
    results.injinci = zeros((npops, npts)) # Incidence through injecting
    results.inci    = zeros((npops, npts)) # Total incidence
    results.births  = zeros((1, npts))     # Number of births
    results.mtct    = zeros((1, npts))     # Number of mother-to-child transmissions
    results.dx      = zeros((npops, npts)) # Number diagnosed per timestep
    results.newtx   = zeros((npops, npts)) # Number initiating ART1 per timestep
    results.death   = zeros((npops, npts)) # Number of deaths per timestep
    
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
    plhivind = settings.allplhiv # All PLHIV
    dxind    = settings.alldiag       # All people who have been diagnosed
    popsize = dcp(simpars['popsize']) # Population sizes
    male = array(simpars['male']).astype(bool) # Male populations
    
    # Infection propabilities
    mmi  = simpars['const']['transmmi']          # Male -> male insertive
    mfi  = simpars['const']['transmfi']          # Male -> female insertive
    mmr  = simpars['const']['transmmr']          # Male -> male receptive
    mfr  = simpars['const']['transmfr']          # Male -> female receptive
    mtcb = simpars['const']['mtctbreast']   # MTCT with breastfeeding
    mtcn = simpars['const']['mtctnobreast'] # MTCT no breastfeeding
    transinj = simpars['const']['transinj']      # Injecting
    
    # Further potential effects on transmission
    effsti    = simpars['const']['effsti'] * simpars['stiprev']  # STI effect
    effcirc   = 1 - simpars['const']['effcirc']            # Circumcision effect
    effprep   = (1 - simpars['const']['effprep']) * simpars['prep'] # PrEP effect
    effcondom = 1 - simpars['const']['effcondom']          # Condom effect
    effpmtct  = 1 - simpars['const']['effpmtct']           # PMTCT effect
    
    # Intervention uptake (P=proportion, N=number)
    sharing  = simpars['sharing']   # Sharing injecting equiptment (P)
    numpmtct = simpars['numpmtct']  # PMTCT (N)
    propcirc = simpars['circum']    # Proportion of men circumcised (P)
    tobecirc = simpars['numcircum'] # Number of men to be circumcised (N)
    mtx1     = simpars['numtx']       # 1st line treatement (N) -- tx already used for index of people on treatment
    hivtest  = simpars['hivtest']   # HIV testing (P)
    aidstest = simpars['aidstest']  # HIV testing in AIDS stage (P)
    transit   = simpars['transit'] # Asymmetric transitions
    
    # Force of infection metaparameter
    force = simpars['force']
    inhomopar = simpars['inhomo'] # WARNING, name is not consistent -- should be "inhomo"
    
    
    
    
    
    
    
    ###########################################
    # Set initial epidemic conditions 
    ###########################################
    
    def equilibrate():
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
            
        return initpeople
    
    people[:,:,0] = equilibrate() # No it hasn't, so run equilibration
    
    




    ###############################################################################
    ## Run the model -- numerically integrate over time
    ###############################################################################

    # Loop over time
    for t in range(npts): # Skip the last timestep for people since we don't need to know what happens after that
        printv('Timestep %i of %i' % (t+1, npts), 8, verbose)
        
        ## Calculate "effective" HIV prevalence -- taking diagnosis and treatment into account
        for pop in range(npops): # Loop over each population group
            allpeople[pop,t] = sum(people[:,pop,t]) # All people in this population group at this time point
            if not(allpeople[pop,t]>0): raise Exception('No people in population %i at timestep %i (time %0.1f)' % (pop, t, results.tvec[t]))
            effundx = sum(cd4trans * people[undx,pop,t]); # Effective number of infecious undiagnosed people
            effdx   = sum(dxfactor * people[dx,pop,t]) # ...and diagnosed/failed
            efftx   = sum(txfactor * people[tx,pop,t]) # ...and treated
            effhivprev[pop] = (effundx+effdx+efftx) / allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effhivprev[pop]>=0): 
                raise Exception('HIV prevalence invalid in population %s! (=%f)' % (pop, effhivprev[pop]))
        
        ## Calculate inhomogeneity in the force-of-infection based on prevalence
        for pop in range(npops):
            c = inhomopar[pop]
            thisprev = sum(people[1:,pop,t]) / allpeople[pop,t] # Probably a better way of doing this
            inhomo[pop] = (c+eps) / (exp(c+eps)-1) * exp(c*(1-thisprev)) # Don't shift the mean, but make it maybe nonlinear based on prevalence
        
        # Also calculate effective MTCT transmissibility
        effmtct  = mtcb*simpars['breast'][t] + mtcn*(1-simpars['breast'][t]) # Effective MTCT transmission
        pmtcteff = (1 - effpmtct) * effmtct # Effective MTCT transmission whilst on PMTCT
                
        
        ###############################################################################
        ## Calculate force-of-infection (forceinf)
        ###############################################################################
        
        # Reset force-of-infection vector for each population group
        forceinfvec = zeros(npops)
        
        ## Sexual partnerships...
        
        # Loop over all populations (for males)
        for popM in range(npops):
            
            # Circumcision
            circeffF = 1 # Trivial circumcision effect for female or receptive male
            circeffM = 1 - effcirc*propcirc[popM,t]
            
            # Loop over all populations (for females)
            for popF in range(npops):
                
                # Transmissibility (depends on receptive population being male or female)
                transM = mmi if male[popF] else mfi # Insertive transmissibility
                transF = mmr if male[popF] else mfr # Receptive transmissibility

                # Transmission effects                
                prepeffM = 1 - effprep[popM,t] # Male PrEP effect
                prepeffF = 1 - effprep[popF,t] # Female PrEP effect
                stieffM  = 1 + effsti[popM,t]  # Male STI prevalence effect
                stieffF  = 1 + effsti[popF,t]  # Female STI prevalence effect
                
                # Iterate through the sexual act types
                for act in sexactslist[popM][popF]: # Ignore if this isn't a valid partnership for this sexual act type
                    numactsM = totalacts[act][popM,popF,t]; # Number of acts per person per year (insertive partner)
                    numactsF = totalacts[act][popF,popM,t]; # Number of acts per person per year (receptive partner)
                    condomprob = (condom[act][popM,t] + condom[act][popF,t]) / 2 # Reconcile condom probability
                    condomeff = 1 - condomprob*effcondom # Effect of condom use
                    forceinfM = 1 - mpow((1-transM*circeffM*prepeffM*stieffM), (dt*numactsM*condomeff*effhivprev[popF])) # The chance of "female" infecting "male"
                    forceinfF = 1 - mpow((1-transF*circeffF*prepeffF*stieffF), (dt*numactsF*condomeff*effhivprev[popM])) # The chance of "male" infecting "female"
                    forceinfvec[popM] = 1 - (1-forceinfvec[popM]) * (1-forceinfM) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    forceinfvec[popF] = 1 - (1-forceinfvec[popF]) * (1-forceinfF) # Calculate the new "female" forceinf, ensuring that it never gets above 1
                    if not(all(forceinfvec>=0)): raise Exception('Sexual force-of-infection is invalid')
        
        ## Injecting partnerships...
        
       
       # Iterate through partnership pairs
        for pop1 in range(npops):
            for pop2 in range(npops):
                if pshipsinj[pop1,pop2]>0: # Ignore if this isn't a valid injecting partnership
                    numacts1 = sharing[pop1,t] * totalacts['inj'][pop1,pop2,t] / 2 # Number of acts per person per year -- /2 since otherwise double-count
                    numacts2 = sharing[pop2,t] * totalacts['inj'][pop2,pop1,t] / 2 # Number of acts per person per year
                    forceinf1 = 1 - mpow((1-transinj), (dt*numacts1*osteff*effhivprev[pop2])) # The chance of "2" infecting "1"
                    forceinf2 = 1 - mpow((1-transinj), (dt*numacts2*osteff*effhivprev[pop1])) # The chance of "1" infecting "2"
                    forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-forceinf1) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    forceinfvec[pop2] = 1 - (1-forceinfvec[pop2]) * (1-forceinf2) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    if not(all(forceinfvec>=0)): raise Exception('Injecting force-of-infection is invalid (transinj=%f, numacts1=%f, numacts2=%f, osteff=%f, effhivprev1=%f, effhivprev2=%f)'% (transinj, numacts1, numacts2, osteff, effhivprev[pop2], effhivprev[pop1]))
        


        
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
        results.inci[:,t] = (newinfections + mtctperpop)/float(dt)  # Store new infections AND new MTCT births

        ## Undiagnosed
        propdx = None
        if propaware[:,t].any(): # Only do this if nonzero
            currplhiv = people[plhivind,:,t].sum(axis=0)
            currdx = people[dxind,:,t].sum(axis=0)
            currundx = currplhiv[:] - currdx[:]
            fractiontodx = maximum(0, propaware[:,t] * currplhiv[:] - currdx[:] / (currundx[:] + eps)) # Don't allow to go negative
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
            if propdx is None: # No proportion diagnosed information, go with testing rate
                newdiagnoses[cd4] = dt * people[undx[cd4],:,t] * testingrate[cd4]
            else: # It exists, use what's calculated before
                newdiagnoses[cd4] = fractiontodx * people[undx[cd4],:,t]
            hivdeaths   = dt * people[undx[cd4],:,t] * death[cd4]
            otherdeaths = dt * people[undx[cd4],:,t] * background
            dU.append(progin - progout - newdiagnoses[cd4] - hivdeaths - otherdeaths) # Add in new infections after loop
            dU[cd4] = negativepeople('undiagnosed', dU[cd4], people[undx[cd4],:,t], t)
            results.dx[:,t]    += newdiagnoses[cd4]/dt # Save annual diagnoses 
            results.death[:,t] += hivdeaths/dt    # Save annual HIV deaths 
        dU[0] = dU[0] + newinfections # Now add newly infected people
        
        ## Diagnosed
        newtreat1tot = mtx1[t] - people[tx,:,t].sum() # Calculate difference between current people on treatment and people needed
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
            dD[cd4] = negativepeople('diagnosed', dD[cd4], people[dx[cd4],:,t], t)
            results.newtx1[:,t] += newtreat1[cd4]/dt # Save annual treatment initiation
            results.death[:,t]  += hivdeaths/dt # Save annual HIV deaths 
        
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
            results.death[:,t] += hivdeaths/dt # Save annual HIV deaths 
        


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
    results.people = people
    


    


    printv('  ...done running model.', 2, verbose)
    if benchmark: toc(starttime)
    return results
