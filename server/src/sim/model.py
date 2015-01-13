 ## Imports
from numpy import array, zeros, exp, maximum, minimum # For creating arrays
from bunch import Bunch as struct # Replicate Matlab-like structure behavior
from printv import printv
from math import pow as mpow

def model(G, M, F, opt, initstate=None, verbose=2): # extraoutput is to calculate death rates etc.
    """
    This function runs the model.
    
    Version: 2014nov26 by cliffk
    """
    printv('Running model...', 1, verbose)

    ###############################################################################
    ## Setup
    ###############################################################################
    
    eps = 1e-3 # Define another small number to avoid divide-by-zero errors
    
    ## Initialize basic quantities
    S       = struct()     # Sim output structure
    S.tvec  = opt.tvec     # Append time vector
    dt      = opt.dt       # Shorten dt
    npts    = len(S.tvec)  # Number of time points
    npops   = G.npops      # Shorten number of pops
    ncd4    = G.ncd4       # Shorten number of CD4 states
    nstates = G.nstates    # Shorten number of health states
    
    ## Initialize arrays
    people     = zeros((nstates, npops, npts)) # Matrix to hold everything
    allpeople  = zeros((npops, npts)) # Population sizes
    S.sexinci  = zeros((npops, npts)) # Incidene through sex
    S.injinci  = zeros((npops, npts)) # Incidene through injecting
    S.inci     = zeros((npops, npts)) # Total incidence
    S.prev     = zeros((npops, npts)) # Prevalence by population
    S.allprev  = zeros((1, npts))     # Overall prevalence
    S.births   = zeros((1, npts))     # Number of births
    S.mtct     = zeros((1, npts))     # Number of mother-to-child transmissions
    S.dx       = zeros((npops, npts)) # Number diagnosed per timestep
    S.newtx1   = zeros((npops, npts)) # Number initiating ART1 per timestep
    S.newtx2   = zeros((npops, npts)) # Number initiating ART2 per timestep
    S.death    = zeros((npops, npts)) # Number of deaths per timestep
    effhivprev = zeros((npops, 1))    # HIV effective prevalence (prevalence times infectiousness)

    ## Set initial epidemic conditions 
    ## Set initial epidemic conditions
    turnofftrans = not(isinstance(initstate, type(None))) # Has the initial state been provided?
    if not(turnofftrans):
        people[:,:,0] = equilibrate(G, M, array(F.init)) # No it hasn't, so run equilibration
    else:
        people[:,:,0] = initstate # Yes it has, so use it.
    
    ## Calculate other things outside the loop
    cd4trans = h2a(G, M.const.cd4trans) # Convert a dictionary to an array
    dxfactor = M.const.eff.dx * cd4trans # Include diagnosis efficacy
    txfactor = M.const.eff.tx * dxfactor # And treatment efficacy
    
    ## Metaparameters to get nice diagnosis fits
    dxtime  = fit2time(F.dx,  S.tvec)
    
    # Shorten variables and remove dict calls to make things faster
    sus  = G.sus
    undx = G.undx
    dx   = G.dx
    tx1  = G.tx1
    fail = G.fail
    tx2  = G.tx2
    male = G.meta.pops.male
    mmi  = M.const.trans.mmi # Male -> male insertive
    mfi  = M.const.trans.mfi # Male -> female insertive
    mmr  = M.const.trans.mmr # Male -> male receptive
    mfr  = M.const.trans.mfr # Male -> female receptive
    mtcb = M.const.trans.mtctbreast   # MTCT with breastfeeding
    mtcn = M.const.trans.mtctnobreast # MTCT no breastfeeding
    effsti    = M.const.eff.sti * M.stiprevulc # TODO -- AS: don't like the way STI prevalence can be > 100%
    effcirc   = (1 - M.const.eff.circ) * M.circum
    effprep   = (1 - M.const.eff.prep) * M.prep
    effcondom = 1 - M.const.eff.condom
    effpmtct  = 1 - M.const.eff.pmtct
    transinj  = M.const.trans.inj
    pshipsinj = M.pships.inj
    pships    = M.pships
    totalacts = M.totalacts
    condom    = M.condom
    sharing   = M.sharing
    numpmtct  = M.numpmtct
#    numost    = M.numost
#    numart    = M.numart
    prog      = h2a(G, M.const.prog)   # Disease progression rates
    recov     = h2a(G, M.const.recov)  # Recovery rates
    death     = h2a(G, M.const.death)  # HIV death rates
    deathtx   = M.const.death.treat # Death rate whilst on treatment

    M.tbprev = M.tbprev + 1  
    
    efftb     = M.const.death.tb * M.tbprev # Increase in death due to TB coinfection
#    sym       = M.transit.sym
    asym      = M.transit.asym
    hivtest   = M.hivtest
    aidstest  = M.aidstest
    Mtx1      = M.tx1 # tx1 already used for index of people on treatment
    Mtx2      = M.tx2
    failfirst  = M.const.fail.first
    failsecond = M.const.fail.second
    Fforce    = array(F.force)
    
    # Initialize the list of sex acts so it doesn't have to happen in the time loop
    sexactslist = []
    for popM in range(npops):
        sexactslist.append([])
        for popF in range(npops):
            sexactslist[popM].append([])
            for act in ['reg','cas','com']:
                if pships[act][popM,popF]>0: # Ignore if this isn't a valid partnership for this sexual act type
                    sexactslist[popM][popF].append(act)
    
    ###############################################################################
    ## Run the model -- numerically integrate over time
    ###############################################################################

    # Loop over time
    for t in range(npts): # Skip the last timestep for people since we don't need to know what happens after that
        printv('Timestep %i of %i' % (t+1, npts), 8, verbose)
        
        ## Calculate "effective" HIV prevalence -- taking diagnosis and treatment into account
        for pop in range(npops): # Loop over each population group
            allpeople[pop,t] = sum(people[:,pop,t]) # All people in this population group at this time point
            if not(allpeople[pop,t]>0): raise Exception('No people in population %i at timestep %i (time %0.1f)' % (pop, t, S['tvec'][t]))
            effundx = sum(cd4trans * people[undx,pop,t]); # Effective number of infecious undiagnosed people
            effdx   = sum(dxfactor * (people[dx,pop,t]+people[fail,pop,t])) # ...and diagnosed/failed
            efftx   = sum(txfactor * (people[tx1,pop,t]+people[tx2,pop,t])) # ...and treated
            effhivprev[pop] = (effundx+effdx+efftx) / allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effhivprev[pop]>=0): 
#                import pdb; pdb.set_trace()
                raise Exception('HIV prevalence invalid in population %s! (=%f)' % (pop, effhivprev[pop]))
        
        # Also calculate effective MTCT transmissibility
        effmtct  = mtcb*M.breast[t] + mtcn*(1-M.breast[t]) # Effective MTCT transmission
        pmtcteff = (1 - effpmtct) * effmtct # Effective MTCT transmission whilst on PMTCT
        
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
                circeffM = 1 - effcirc[popM,t] # Effect of circumcision for insertive male -- # TODO: check this is capturing what we want, i.e shouldn't it only be for susceptibles?
                circeffF = 1                   # Trivial circumcision effect for female or receptive male
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
        
        ## Injecting partnerships
        
        # Transmission effects
#        metheff = 1 - M.const.eff.meth*M.ost[t] # TODO: methadone should be subtracted from population size
        # Iterate through partnership pairs
        for pop1 in range(npops):
            for pop2 in range(npops):
                if pshipsinj[pop1,pop2]>0: # Ignore if this isn't a valid injecting partnership
                    sharingprob = (sharing[pop1,t] + sharing[pop2,t]) / 2 # Reconcile sharing probability
                    numacts1 = sharingprob * totalacts['inj'][pop1,pop2,t] / 2 # Number of acts per person per year -- /2 since otherwise double-count
                    numacts2 = sharingprob * totalacts['inj'][pop2,pop1,t] / 2 # Number of acts per person per year
                    forceinf1 = 1 - mpow((1-transinj), (dt*numacts1*effhivprev[pop2])) # The chance of "2" infecting "1"
                    forceinf2 = 1 - mpow((1-transinj), (dt*numacts2*effhivprev[pop1])) # The chance of "1" infecting "2"
                    forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-forceinf1) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    forceinfvec[pop2] = 1 - (1-forceinfvec[pop2]) * (1-forceinf2) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    if not(all(forceinfvec>=0)): raise Exception('Injecting force-of-infection is invalid')
        
        ###############################################################################
        ## Calculate mother-to-child-transmission
        ###############################################################################
        
        # We have two ways to calculate number of births...
        if (asym<0).any(): # Method 1 -- children are being modelled directly
            print('working on it...') # Use negative entries in transitions matrix
        else: # Method 2 -- children are not being modelled directly
            birthrate = M.birth[:,t] # Use birthrate parameter from input spreadsheet
        S['births'][0,t] = sum(birthrate * allpeople[:,t])
        mtcttx       = sum(birthrate * sum(people[tx1,:,t] +people[tx2,:,t]))  * pmtcteff # MTCT from those on treatment (not eligible for PMTCT)
        mtctundx     = sum(birthrate * sum(people[undx,:,t]+people[fail,:,t])) * effmtct  # MTCT from those undiagnosed or failed (also not eligible)
        birthselig   = sum(birthrate * sum(people[dx,:,t]))   # Births to diagnosed mothers eligible for PMTCT
        receivepmtct = min(numpmtct[t], birthselig)           # Births protected by PMTCT -- constrained by number eligible 
        mtctdx       = (birthselig - receivepmtct) * effmtct  # MTCT from those diagnosed not receiving PMTCT
        mtctpmtct    = receivepmtct * pmtcteff                # MTCT from those receiving PMTCT
        S['mtct'][0,t] = mtctundx + mtctdx + mtcttx + mtctpmtct # Total MTCT, adding up all components 
        
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
            newdiagnoses[cd4] = dt * people[undx[cd4],:,t] * testingrate[cd4] * dxtime[t]
            hivtbdeath  = minimum((1 + efftb[:,t]) * death[cd4], 1)
            hivdeaths   = dt * people[undx[cd4],:,t] * hivtbdeath
            otherdeaths = dt * people[undx[cd4],:,t] * background
            dU.append(progin - progout - newdiagnoses[cd4] - hivdeaths - otherdeaths) # Add in new infections after loop
            if ((dU[cd4]+people[undx[cd4],:,t])<0).any():
                dU[cd4] = maximum(dU[cd4], -people[undx[cd4],:,t]) # Ensure it doesn't go below 0 -- # TODO kludgy
                printv('Prevented negative people in undiagnosed at timestep %i' % t, 10, verbose)
            S['dx'][:,t]    += newdiagnoses[cd4]/dt # Save annual diagnoses 
            S['death'][:,t] += hivdeaths[cd4]/dt    # Save annual HIV deaths 
        dU[0] = dU[0] + newinfections # Now add newly infected people
        
        ## Diagnosed
        newtreat1tot = Mtx1[t] - people[tx1,:,t].sum() # Calculate difference between current people on treatment and people needed
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
            newtreat1[cd4] = newtreat1tot * currentdiagnosed[cd4,:] / (eps+currentdiagnosed.sum()) # Pull out evenly among diagnosed -- WARNING # TODO implement CD4 cutoffs
            hivtbdeath  = minimum((1 + efftb[:,t]) * death[cd4], 1)
            hivdeaths   = dt * people[undx[cd4],:,t] * hivtbdeath
            otherdeaths = dt * people[undx[cd4],:,t] * background
            inflows = progin + newdiagnoses[cd4]
            outflows = progout + hivdeaths + otherdeaths
            newtreat1[cd4] = maximum(0, minimum(newtreat1[cd4], currentdiagnosed[cd4,:]+inflows-outflows)) # Make sure it doesn't go negative
            dD.append(inflows - outflows - newtreat1[cd4])
            if ((dD[cd4]+people[dx[cd4],:,t])<0).any():
                dD[cd4] = maximum(dD[cd4], -people[dx[cd4],:,t]) # Ensure it doesn't go below 0 -- # TODO kludgy
                printv('Prevented negative people in diagnosed at timestep %i' % t, 10, verbose)
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
            newfail1[cd4] = dt * people[tx1[cd4],:,t] * failfirst
            hivtbdeath  = minimum((1 + efftb[:,t]) * death[cd4], 1)
            tbtxdeath   = minimum((1 + efftb[:,t]) * deathtx, 1)
            hivdeaths   = dt * people[tx1[cd4],:,t] * minimum(hivtbdeath, tbtxdeath) # Use death by CD4 state if lower than death on treatment
            otherdeaths = dt * people[tx1[cd4],:,t] * background
            dT1.append(recovin - recovout + newtreat1[cd4] - newfail1[cd4] - hivdeaths - otherdeaths)
            if ((dT1[cd4]+people[tx1[cd4],:,t])<0).any():
                dT1[cd4] = maximum(dT1[cd4], -people[tx1[cd4],:,t]) # Ensure it doesn't go below 0 -- # TODO kludgy
                printv('Prevented negative people in treatment 1 at timestep %i' % t, 10, verbose)
            S['death'][:,t] += hivdeaths[cd4]/dt # Save annual HIV deaths 

        ## Treatment failure
        newtreat2tot = Mtx2[t] - people[tx2,:,t].sum() # Calculate difference between current people on treatment and people needed
        currentfailed = people[fail,:,t] # Find how many people are diagnosed
        for cd4 in range(ncd4):
            if cd4>0:
                progin = dt*prog[cd4-1]*people[fail[cd4-1],:,t] 
            else: 
                progin = 0 # Cannot progress into acute stage
            if cd4<ncd4-1: 
                progout = dt*prog[cd4]*people[fail[cd4],:,t] 
            else: 
                progout = 0 # Cannot progress out of AIDS stage
            newtreat2[cd4] = newtreat2tot * currentfailed[cd4,:] / (eps+currentfailed.sum()) # Pull out evenly among diagnosed
            newfail2[cd4]  = dt * people[tx2[cd4] ,:,t] * failsecond # Newly failed from ART2
            hivtbdeath  = minimum((1 + efftb[:,t]) * death[cd4], 1)
            hivdeaths   = dt * people[fail[cd4],:,t] * hivtbdeath
            otherdeaths = dt * people[fail[cd4],:,t] * background
            inflows = progin + newfail1[cd4] + newfail2[cd4]
            outflows = progout + hivdeaths + otherdeaths
            
            newtreat2[cd4] = maximum(0, minimum(newtreat2[cd4], currentfailed[cd4,:]+inflows-outflows)) # Make sure it doesn't go negative
            dF.append(inflows - outflows - newtreat2[cd4])
            if ((dF[cd4]+people[fail[cd4],:,t])<0).any():
                dF[cd4] = maximum(dF[cd4], -people[fail[cd4],:,t]) # Ensure it doesn't go below 0 -- # TODO kludgy
                printv('Prevented negative people in failure at timestep %i' % t, 10, verbose)
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
            hivtbdeath  = minimum((1 + efftb[:,t]) * death[cd4], 1)
            tbtxdeath   = minimum((1 + efftb[:,t]) * deathtx, 1)
            hivdeaths   = dt * people[tx2[cd4],:,t] * minimum(hivtbdeath, tbtxdeath) # Use death by CD4 state if lower than death on treatment
            otherdeaths = dt * people[tx2[cd4],:,t] * background
            dT2.append(recovin - recovout + newtreat2[cd4] - newfail2[cd4] - hivdeaths - otherdeaths)
            if ((dT2[cd4]+people[tx2[cd4],:,t])<0).any():
                dT2[cd4] = maximum(dT2[cd4], -people[tx2[cd4],:,t]) # Ensure it doesn't go below 0 -- # TODO kludgy
                printv('Prevented negative people in treatment 2 at timestep %i' % t, 10, verbose)
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
                print('Non-positive people found') # If not every element is a real number >0, throw an error
#                import pdb; pdb.set_trace() not going to fly in web context
                raise Exception('Non-positive people found: %s %s' % (pop, people))
                
    # Append final people array to sim output
    S['people'] = people

    printv('  ...done running model.', 2, verbose)
    return S







###############################################################################
## Helper functions
###############################################################################

def h2a(G, parstruct, verbose=2):
    """ Convert a health state structure to an array """
    outarray = []
    for state in G.healthstates:
        try: 
            outarray.append(parstruct[state])
        except: 
            printv('State %s not found' % state, 10, verbose)
    return array(outarray)

def fit2time(pars, tvec):
    """ Calculate fitted time series from fitted parameters """
    A = pars[0]
    B = pars[1]
    C = pars[2]
    D = pars[3]
    timeseries = (B-A)/(1+exp(-(tvec-C)/D))+A;
    return timeseries
    
def equilibrate(G, M, Finit):
    """
    Calculate the quilibrium point by estimating the ratio of input and output 
    rates for each of the health states.
    
    Usage:
        G = general parameters
        M = model parameters
        Finit = fitted parameters for initial prevalence
        initpeople = nstates x npops array
    
    Version: 2014nov26
    """
    from numpy import zeros, hstack, inf
    
    # Set parameters
    prevtoforceinf = 0.1 # Assume force-of-infection is proportional to prevalence -- 0.1 means that if prevalence is 10%, annual force-of-infection is 1%
    efftreatmentrate = 0.1 # Inverse of average duration of treatment in years...I think
    failratio = 0.3 # Put fewer people than expected on failure because ART is relatively new...or something
    
    # Shorten key variables
    hivprev = M.hivprev
    initpeople = zeros((G['nstates'],G['npops']))
    
    # Can calculate equilibrium for each population separately
    for p in range(G['npops']):
        # Set up basic calculations
        uninfected = M['popsize'][p,0] * (1-hivprev[p]) # Set initial susceptible population -- easy peasy!
        allinfected = M['popsize'][:,0] * hivprev[:] * Finit[:] # Set initial infected population
        popinfected = allinfected[p]
        
        # Treatment & treatment failure
        fractotal =  popinfected / sum(allinfected) # Fractional total of infected people in this population
        treatment1 = M['tx1'][0] * fractotal # Number of people on 1st-line treatment
        treatment2 = M['tx2'][0] * fractotal # Number of people on 2nd-line treatment
        treatfail = treatment1 * M['const']['fail']['first'] * efftreatmentrate * failratio # Number of people with treatment failure -- # TODO: check
        totaltreat = treatment1 + treatment2 + treatfail
        if totaltreat > popinfected: # More people on treatment than ever infected, uh oh!
            treatment1 *= popinfected/totaltreat
            treatment2 *= popinfected/totaltreat
            treatfail *= popinfected/totaltreat
            totaltreat = popinfected
        
        # Diagnosed & undiagnosed
        nevertreated = popinfected - totaltreat
        assumedforceinf = hivprev[p]*prevtoforceinf # To calculate ratio of people in the initial category, need to estimate the force-of-infection
        undxdxrates = assumedforceinf + M['hivtest'][p,0] # Ratio of undiagnosed to diagnosed
        undiagnosed = nevertreated * assumedforceinf / undxdxrates     
        diagnosed = nevertreated * M['hivtest'][p,0] / undxdxrates
        
        # Set rates within
        progratios = hstack([h2a(G, M['const']['prog']), M['const']['death']['aids']]) # For last rate, use AIDS death as dominant rate
        progratios = (1/progratios)  / sum(1/progratios) # Normalize
        recovratios = hstack([inf, h2a(G, M['const']['recov']), efftreatmentrate]) # Not sure if this is right...inf since no progression to acute, treatmentrate since main entry here # TODO check
        recovratios = (1/recovratios)  / sum(1/recovratios) # Normalize
        
        # Final calculations
        undiagnosed *= progratios
        diagnosed *= progratios
        treatment1 *= recovratios
        treatfail *= progratios
        treatment2 *= recovratios
        
        # Populated equilibrated array
        initpeople[G['sus'], p] = uninfected
        initpeople[G['undx'], p] = undiagnosed
        initpeople[G['dx'], p] = diagnosed
        initpeople[G['tx1'], p] = treatment1
        initpeople[G['fail'], p] = treatfail
        initpeople[G['tx2'], p] = treatment2
    
        if not((initpeople>=0).all()):
                    print('Non-positive people found') # If not every element is a real number >0, throw an error
                    import pdb; pdb.set_trace()
        
    return initpeople