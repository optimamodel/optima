def model(G, M, F, opt, verbose=2): # extraoutput is to calculate death rates etc.
    """
    This function runs the model.
    
    Version: 2014nov26 by cliffk
    """

    ###############################################################################
    ## Setup
    ###############################################################################

    ## Imports
    from numpy import array, zeros, exp, maximum # For creating arrays
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    from printv import printv
    from math import pow as mpow
    printv('Running model...', 1, verbose)
    
    ## Initialize basic quantities
    S       = struct()     # Sim output structure
    S.tvec  = opt.tvec # Append time vector
    dt      = opt.dt   # Shorten dt
    npts    = len(S.tvec)  # Number of time points
    npops   = G.npops      # Shorten number of pops
    ncd4    = G.ncd4       # Shorten number of CD4 states
    nstates = G.nstates   # Shorten number of health states
    
    ## Initialize arrays
    people     = zeros((nstates, npops, npts)) # Matrix to hold everything
    allpeople  = zeros((npops, npts)) # Population sizes
    S.sexinci  = zeros((npops, npts)) # Incidene through sex
    S.injinci  = zeros((npops, npts)) # Incidene through injecting
    S.inci     = zeros((npops, npts)) # Total incidence
    S.prev     = zeros((npops, npts)) # Prevalence by population
    S.allprev  = zeros((1, npts))     # Overall prevalence
    S.mtctbr   = zeros((1, npts))     # Breastfeeding MTCT
    S.mtctnobr = zeros((1, npts))     # Non-breastfeeding MTCT
    S.allmtct  = zeros((1, npts))     # Total MTCT
    S.dx       = zeros((npops, npts)) # Number diagnosed per timestep
    S.newtx1   = zeros((npops, npts)) # Number initiating ART1 per timestep
    S.newtx2   = zeros((npops, npts)) # Number initiating ART2 per timestep
    S.death    = zeros((npops, npts)) # Number of deaths per timestep
    effhivprev = zeros((npops, 1))    # HIV effective prevalence (prevalence times infectiousness)

    ## Set initial epidemic conditions 
    people[:,:,0] = equilibrate(people[:,:,0], M, array(F.init)) # Run equilibration
    
    ## Convert a health state structure to an array
    def h2a(parstruct):
        healthstates = ['acute','gt500','gt350','gt200','aids'] # TODO, don't redefine these or hard-code them
        outarray = []
        for state in healthstates:
            try: 
                outarray.append(parstruct[state])
            except: 
                printv('State %s not found' % state, 10, verbose)
        return array(outarray)
    
    ## Calculate other things outside the loop
    cd4trans = h2a(M.const.cd4trans) # Convert a dictionary to an array
    dxfactor = M.const.eff.dx * cd4trans # Include diagnosis efficacy
    txfactor = M.const.eff.tx * dxfactor # And treatment efficacy
    
    ## Calculate fitted time series from fitted parameters
    def fit2time(pars, tvec):
        A = pars[0]
        B = pars[1]
        C = pars[2]
        D = pars[3]
        timeseries = (B-A)/(1+exp(-(tvec-C)/D))+A;
        return timeseries
    
    ## Metaparameters to get nice dx and tx fits
    dxtime  = fit2time(F.dx,  S.tvec)
    tx1time = fit2time(F.tx1, S.tvec)
    tx2time = fit2time(F.tx2, S.tvec)
    
    ###############################################################################
    ## Run the model -- numerically integrate over time
    ###############################################################################
    
    # Shorten variables and remove dict calls to make things faster
    sus = G.sus
    undx = G.undx
    dx = G.dx
    tx1 = G.tx1
    fail = G.fail
    tx2 = G.tx2
    male = G.male
    mmi = M.const.trans.mmi
    mfi = M.const.trans.mfi
    mmr = M.const.trans.mmr
    mfr = M.const.trans.mfr
    effcirc = M.const.eff.circ*M.circum
    effsti = M.const.eff.sti * (M.stiprevulc + M.stiprevdis)
    effcondom = M.const.eff.condom
    transinj = M.const.trans.inj
    pshipsinj = M.pships.inj
    pships = M.pships
    totalacts = M.totalacts
    condom = M.condom
    sharing = M.sharing
    prog  = h2a(M.const.prog)  # Disease progression rates
    death = h2a(M.const.death) # HIV death rates
    recov = h2a(M.const.recov) # Recovery rates
    hivtest = M.hivtest
    aidstest = M.aidstest
    Mtx1 = M.tx1 # tx1 already used for index of people on treatment
    Mtx2 = M.tx2
    failfirst = M.const.fail.first
    failsecond = M.const.fail.second
    Fforce = array(F.force)
    
    # Initialize the list of sex acts so it doesn't have to happen in the time loop
    sexactslist = []
    for popM in range(npops):
        sexactslist.append([])
        for popF in range(npops):
            sexactslist[popM].append([])
            for act in ['reg','cas','com']:
                if pships[act][popM,popF]>0: # Ignore if this isn't a valid partnership for this sexual act type
                    sexactslist[popM][popF].append(act)
    
    # Loop over time
    for t in range(npts): # Skip the last timestep for people since we don't need to know what happens after that
        printv('Timestep %i of %i' % (t+1, npts), 5, verbose)
        
        ## Calculate "effective" HIV prevalence -- taking diagnosis and treatment into account
        for pop in range(npops): # Loop over each population group
            allpeople[pop,t] = sum(people[:,pop,t]) # All people in this population group at this time point
            if not(allpeople[pop,t]>0): raise Exception('No people in population %i at timestep %i (time %0.1f)' % (pop, t, S['tvec'][t]))
            effundx = sum(cd4trans * people[undx,pop,t]); # Effective number of infecious undiagnosed people
            effdx   = sum(dxfactor * (people[dx,pop,t]+people[fail,pop,t])) # ...and diagnosed/failed
            efftx   = sum(txfactor * (people[tx1,pop,t]+people[tx2,pop,t])) # ...and treated
            effhivprev[pop] = (effundx+effdx+efftx) / allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effhivprev[pop]>=0): raise Exception('HIV prevalence invalid in population %s! (=%f)' % (pop, effhivprev[pop]))
        
        ###############################################################################
        ## Calculate force-of-infection (forceinf)
        ###############################################################################
        
        # Reset force-of-infection vector for each population group
        forceinfvec = zeros(npops)
        
        ## Sexual partnerships
        
        # Iterate through partnership pairs
        for popM in range(npops):
            for popF in range(npops):
                
                # Transmissibility (depends on receptive population being male or female)
                transM = mmi if male[popF] else mfi # Insertive transmissibility
                transF = mmr if male[popF] else mfr # Receptive transmissibility

                # Transmission effects
                circeff = 1 - effcirc[popM,t] # Effect of circumcision -- # TODO: check this is capturing what we want, i.e shouldn't it only be for susceptibles?
                stieffM = 1 + effsti[popM,t]  # Male STI prevalence effect
                stieffF = 1 + effsti[popF,t] # Female STI prevalence effect
                
                # Iterate through the sexual act types
                for act in sexactslist[popM][popF]: # Ignore if this isn't a valid partnership for this sexual act type
                    numactsM = totalacts[act][popM,popF,t]; # Number of acts per person per year (insertive partner)
                    numactsF = totalacts[act][popF,popM,t]; # Number of acts per person per year (receptive partner)
                    condomprob = (condom[act][popM,t] + condom[act][popF,t]) / 2 # Reconcile condom probability
                    condomeff = 1 - condomprob*effcondom # Effect of condom use
                    forceinfM = 1 - mpow((1-transM*circeff*stieffM), (dt*numactsM*condomeff*effhivprev[popF])) # The chance of "female" infecting "male" -- # TODO: Implement PrEP etc here
                    forceinfF = 1 - mpow((1-transF*circeff*stieffF), (dt*numactsF*condomeff*effhivprev[popM])) # The chance of "male" infecting "female"
                    forceinfvec[popM] = 1 - (1-forceinfvec[popM]) * (1-forceinfM) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    forceinfvec[popF] = 1 - (1-forceinfvec[popF]) * (1-forceinfF) # Calculate the new "female" forceinf, ensuring that it never gets above 1
                    if not(all(forceinfvec>=0)): raise Exception('Sexual force-of-infection is invalid')
        
        ## Injecting partnerships -- # TODO make more efficient
        
        # Transmission effects
#        metheff = 1 - M.const.eff.meth*M.ost[t] # TODO: methadone should be subtracted from population size
        # Iterate through partnership pairs
        for pop1 in range(npops):
            for pop2 in range(npops):
                if pshipsinj[pop1,pop2]>0: # Ignore if this isn't a valid injecting partnership
                    numacts1 = sharing[t] * totalacts['inj'][pop1,pop2,t] / 2 # Number of acts per person per year -- /2 since otherwise double-count
                    numacts2 = sharing[t] * totalacts['inj'][pop2,pop1,t] / 2 # Number of acts per person per year
                    forceinf1 = 1 - mpow((1-transinj), (dt*numacts1*effhivprev[pop2])) # The chance of "2" infecting "1"
                    forceinf2 = 1 - mpow((1-transinj), (dt*numacts2*effhivprev[pop1])) # The chance of "1" infecting "2"
                    forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-forceinf1) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    forceinfvec[pop2] = 1 - (1-forceinfvec[pop2]) * (1-forceinf2) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    if not(all(forceinfvec>=0)): raise Exception('Injecting force-of-infection is invalid')
        
        
        
        
        
        
        ###############################################################################
        ## The ODEs
        ###############################################################################
    
        ## Set up
    
        # New infections -- through pre-calculated force of infection
        newinfections = forceinfvec * Fforce * people[0,:,t] # Will be useful to define this way when calculating 'cost per new infection'      
    
        # Initalise / reset arrays
        dU = []; dD = []; dT1 = []; dF = []; dT2 = [];  # Reset differences
        testingrate  = [0] * ncd4
        newdiagnoses = [0] * ncd4
        newtreat1    = [0] * ncd4
        newtreat2    = [0] * ncd4
        newfail1     = [0] * ncd4
        newfail2     = [0] * ncd4
        background   = M['death'][:, t] # TODO make OST effect this death rates
        
        ## Susceptibles
        dS = -newinfections # Change in number of susceptibles -- death rate already taken into account in pm.totalpop and dt
        S['inci'][:,t] = newinfections  # Store new infections


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
            newdiagnoses[cd4] = dt*people[undx[cd4],:,t]*testingrate[cd4]*dxtime[t]
            hivdeaths         = dt*people[undx[cd4],:,t]*death[cd4]
            otherdeaths       = dt*people[undx[cd4],:,t]*background
            dU.append(progin - progout - newdiagnoses[cd4] - hivdeaths - otherdeaths) # Add in new infections after loop
            S['dx'][:,t]    += newdiagnoses[cd4]/dt # Save annual diagnoses 
            S['death'][:,t] += hivdeaths[cd4]/dt    # Save annual HIV deaths 
        dU[0] = dU[0] + newinfections # Now add newly infected people
        
    
        ## Diagnosed
        for cd4 in range(ncd4):
            if cd4>0: 
                progin = dt*prog[cd4-1]*people[dx[cd4-1],:,t]
            else: 
                progin = 0 # Cannot progress into acute stage
            if cd4<ncd4-1: 
                progout = dt*prog[cd4]*people[dx[cd4],:,t]
            else: 
                progout = 0 # Cannot progress out of AIDS stage
            newtreat1[cd4] = dt*people[dx[cd4],:,t]*Mtx1[t]*tx1time[t] # TODO - shouldn't M.tx1 be broken down by CD4???
            hivdeaths      = dt*people[dx[cd4],:,t]*death[cd4]
            otherdeaths    = dt*people[dx[cd4],:,t]*background
            dD.append(progin - progout + newdiagnoses[cd4] - newtreat1[cd4] - hivdeaths - otherdeaths)
            S['newtx1'][:,t] += newtreat1[cd4]/dt # Save annual treatment initiation
            S['death'][:,t]  += hivdeaths[cd4]/dt # Save annual HIV deaths 
        
    
        ## 1st-line treatment
        for cd4 in range(ncd4):
            if (cd4>0 and cd4<ncd4-1): # CD4>0 stops people from moving back into acute
                recovin = dt*recov[cd4-1]*people[tx1[cd4+1],:,t]
            else: 
                recovin = 0 # Cannot recover in to acute or AIDS stage
            if cd4>1: # CD4>1 stops people from moving back into acute
                recovout = dt*recov[cd4-2]*people[tx1[cd4],:,t]
            else: 
                recovout = 0 # Cannot recover out of gt500 stage (or acute stage)
            newfail1[cd4] = dt*people[tx1[cd4],:,t]*failfirst 
            hivdeaths     = dt*people[tx1[cd4],:,t]*death[cd4]
            otherdeaths   = dt*people[tx1[cd4],:,t]*background
            dT1.append(recovin - recovout + newtreat1[cd4] - newfail1[cd4] - hivdeaths - otherdeaths)
            S['death'][:,t] += hivdeaths[cd4]/dt # Save annual HIV deaths 

    
        ## Treatment failure
        for cd4 in range(ncd4):
            if cd4>0:
                progin = dt*prog[cd4-1]*people[fail[cd4-1],:,t] 
            else: 
                progin = 0 # Cannot progress into acute stage
            if cd4<ncd4-1: 
                progout = dt*prog[cd4]*people[fail[cd4],:,t] 
            else: 
                progout = 0 # Cannot progress out of AIDS stage
            newtreat2[cd4] = dt*people[fail[cd4],:,t]*Mtx2[t]*tx2time[t]
            newfail2[cd4]  = dt*people[tx2[cd4] ,:,t]*failsecond # Newly failed from ART2
            hivdeaths      = dt*people[fail[cd4],:,t]*death[cd4]
            otherdeaths    = dt*people[fail[cd4],:,t]*background
            dF.append(progin - progout + newfail1[cd4] + newfail2[cd4] - newtreat2[cd4] - hivdeaths - otherdeaths)
            S['newtx2'][:,t] += newtreat2[cd4]/dt # Save annual treatment initiation
            S['death'][:,t]  += hivdeaths[cd4]/dt # Save annual HIV deaths
            

        ## 2nd-line treatment
        for cd4 in range(ncd4):
            if (cd4>0 and cd4<ncd4-1): # CD4>0 stops people from moving back into acute
                recovin = dt*recov[cd4-1]*people[tx2[cd4+1],:,t]
            else: 
                recovin = 0 # Cannot recover in to acute or AIDS stage
            if cd4>1: # CD4>1 stops people from moving back into acute
                recovout = dt*recov[cd4-2]*people[tx2[cd4],:,t]
            else: 
                recovout = 0 # Cannot recover out of gt500 stage (or acute stage)
            hivdeaths   = dt*people[tx2[cd4],:,t]*death[cd4]
            otherdeaths = dt*people[tx2[cd4],:,t]*background
            dT2.append(recovin - recovout + newtreat2[cd4] - newfail2[cd4] - hivdeaths - otherdeaths)
            S['death'][:,t] += hivdeaths[cd4]/dt # Save annual deaths data


        ###############################################################################
        ## Update next time point and check for errors
        ###############################################################################
        
        # Ignore the last time point, we don't want to update further
        if t<npts-1:
            change = zeros((nstates, npops))
            change[sus,:] = dS
            for cd4 in range(ncd4): # TODO: this could be made much more efficient
                change[undx[cd4],:] = dU[cd4]
                change[dx[cd4],:]   = dD[cd4]
                change[tx1[cd4],:]  = dT1[cd4]
                change[fail[cd4],:] = dF[cd4]
                change[tx2[cd4],:]  = dT2[cd4]
            people[:,:,t+1] = people[:,:,t] + change # Update people array
            newpeople = M.popsize[:,t+1]-people[:,:,t+1].sum(axis=0) # Number of people to add according to M.popsize (can be negative)
            for pop in range(npops): # Loop over each population, since some might grow and others might shrink
                if newpeople[pop]>=0: # People are entering: they enter the susceptible population
                    people[0,pop,t+1] += newpeople[pop]
                else: # People are leaving: they leave from each health state equally
                    people[:,pop,t+1] *= M.popsize[pop,t]/sum(people[:,pop,t]);
            if not((people[:,:,t+1]>=0).all()):
                raise Exception('Non-positive people found') # If not every element is a real number >0, throw an error
    
    # Append final people array to sim output
    S['people'] = people

    printv('  ...done running model.', 2, verbose)
    return S


def equilibrate(initpeople, M, Finit):
    initpeople[0, :] = M.popsize[:,0] * (1-M.hivprev) # Set initial susceptible population
    initpeople[1, :] = M.popsize[:,0] * M.hivprev * Finit # Set initial infected population
    return initpeople