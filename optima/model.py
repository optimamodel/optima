## Imports
from math import pow as mpow
from numpy import zeros, exp, maximum, minimum, hstack, inf
from optima import OptimaException, printv, tic, toc, dcp, odict, findinds, makesimpars, Resultset

def model(simpars=None, settings=None, verbose=2, safetymargin=0.8, benchmark=False):
    """
    This function runs the model. Safetymargin is how close to get to moving all people from a compartment in a single timestep.
    
    Version: 2016jan05 by cliffk
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
    if simpars is None: raise OptimaException('model() requires simpars as an input')
    if settings is None: raise OptimaException('model() requires settings as an input')
    popkeys    = simpars['popkeys']
    npops      = len(popkeys)
    simpars    = dcp(simpars)
    tvec       = simpars['tvec']
    dt         = simpars['dt']      # Shorten dt
    npts       = len(tvec) # Number of time points
    ncd4       = settings.ncd4      # Shorten number of CD4 states
    nstates    = settings.nstates   # Shorten number of health states
    people     = zeros((nstates, npops, npts)) # Matrix to hold everything
    allpeople  = zeros((npops, npts)) # Population sizes
    effhivprev = zeros((npops, 1))    # HIV effective prevalence (prevalence times infectiousness)
    inhomo     = zeros(npops)    # Inhomogeneity calculations
    usecascade = settings.usecascade # Whether or not the full treatment cascade should be used
    
    # Initialize arrays
    raw               = odict()    # Sim output structure
    raw['tvec']       = tvec
    raw['popkeys']    = popkeys
    raw['sexinci']    = zeros((npops, npts)) # Incidence through sex
    raw['injinci']    = zeros((npops, npts)) # Incidence through injecting
    raw['inci']       = zeros((npops, npts)) # Total incidence
    raw['births']     = zeros((1, npts))     # Number of births
    raw['mtct']       = zeros((1, npts))     # Number of mother-to-child transmissions
    raw['diag']       = zeros((npops, npts)) # Number diagnosed per timestep
    raw['newtreat']   = zeros((npops, npts)) # Number initiating ART1 per timestep
    raw['death']      = zeros((npops, npts)) # Number of deaths per timestep
    raw['otherdeath'] = zeros((npops, npts)) # Number of other deaths per timestep
    
    # Biological and failure parameters -- death etc
    prog       = simpars['progacute':'proggt50'] # WARNING, this relies on simpars being an odict, and the parameters being read in in the correct order!
    recov      = simpars['recovgt500':'recovgt50']
    death      = simpars['deathacute':'deathlt50']
    cd4trans   = simpars['cd4transacute':'cd4translt50']
    deathtx    = simpars['deathtreat']   # Death rate whilst on treatment


    # Defined for total (not by populations) and time dependent [npts]
    if usecascade:
        successprop = simpars['successprop']   # Proportion of people on ART with viral suppression (P)
        biofailure  = simpars['biofailure']    # biological treatment failure rate (P/T) [npts]
        pdhivcare   = simpars['pdhivcare'] # Percentage of all people who have been diagnosed with HIV who are in care [npts]

    
    # Calculate other things outside the loop
    cd4trans /= cd4transnorm # Normalize CD4 transmission
    dxfactor = simpars['effdx'] * cd4trans # Include diagnosis efficacy
    if usecascade:
        efftxunsupp = simpars['efftxunsupp'] * dxfactor # (~30%) reduction in transmission probability for usVL
        efftxsupp  = simpars['efftxsupp']  * dxfactor # (~96%) reduction in transmission probability for sVL
    else:
        txfactor = simpars['efftxsupp']*simpars['successprop'] + simpars['efftxunsupp']*(1-simpars['successprop']) # Roughly calculate treatment efficacy based on ART success rate; should be 92%*90% = 80%, close to 70% we had been using

    # Disease state indices
    uncirc   = settings.uncirc # Susceptible, uncircumcised
    circ     = settings.circ # Susceptible, circumcised
    sus      = settings.sus   # Susceptible, both circumcised and uncircumcised
    undx     = settings.undx  # Undiagnosed
    dx       = settings.dx    # Diagnosed
    allplhiv = settings.allplhiv
    if usecascade:
        care = settings.care  # in Care
        usvl = settings.usvl  # On-Treatment - Unsuppressed Viral Load
        svl  = settings.svl   # On-Treatment - Suppressed Viral Load
        lost = settings.lost  # Not on ART (anymore) and lost to follow-up
        off  = settings.off   # off-ART but still in care
    else:
        tx   = settings.tx  # Treatment -- equal to settings.svl, but this is clearer

    popsize = dcp(simpars['popsize']) # Population sizes
    
    # Infection propabilities
    transinj = simpars['transinj']      # Injecting

    # Population characteristics
    male = simpars['male']          # Boolean array, true for males
    female = simpars['female']      # Boolean array, true for females
    injects = simpars['injects']    # Boolean array, true for PWID
    

    # Intervention uptake (P=proportion, N=number)
    sharing  = simpars['sharing']   # Sharing injecting equiptment (P)
    numtx    = simpars['numtx']     # 1st line treatement (N) -- tx already used for index of people on treatment [npts]
    hivtest  = simpars['hivtest']   # HIV testing (P) [npop,npts]
    aidstest = simpars['aidstest']  # HIV testing in AIDS stage (P) [npts]
    circum   = simpars['circum']    # Prevalence of circumcision (P)
    stiprev  = simpars['stiprev']   # Prevalence of STIs (P)
    prep     = simpars['prep']      # Prevalence of PrEP (P)

    # Uptake of OST
    numost = simpars['numost']                  # Number of people on OST (N)
    if any(injects):
        numpwid = popsize[injects,:].sum(axis=0)  # Total number of PWID
        try: ostprev = numost/numpwid           # Proportion of PWID on OST (P)
        except: raise OptimaException('Cannot divide by the number of PWID')
    else:
        if sum(numost): raise OptimaException('You have entered non-zero value for the number of PWID on OST, but you have not specified any populations who inject')
        else: ostprev = 0.
    
    # Further potential effects on transmission
    effsti    = simpars['effsti'] * stiprev  # STI effect
    effcirc   = simpars['effcirc'] * circum  # Circumcision effect
    effprep   = simpars['effprep'] * prep    # PrEP effect
    effcondom = simpars['effcondom']         # Condom effect
    effost    = simpars['effost'] * ostprev  # OST effect
    
    # Calculations...used to be inside time loop
    circeff = 1 - effcirc*circum
    prepeff = 1 - effprep
    osteff = 1 - effost
    stieff  = 1 + effsti

    
    # Behavioural transitions between stages [npop,npts]
    if usecascade:
        immediatecare = simpars['immediatecare'] # Linkage to care from diagnosis within 1 month (%) (P)
        linktocare    = simpars['linktocare']    # rate of linkage to care (P/T)
        leavecare     = simpars['leavecare']     # Proportion of people in care then lost to follow-up per year (P/T)
        stoprate      = simpars['stoprate']      # Percentage of people who receive ART in year who stop taking ART (%/year) (P/T)

    # Force of infection metaparameter
    force = simpars['force']
    inhomopar = simpars['inhomo'] # WARNING, name is not consistent -- should be "inhomo"
    
    
    
    
    
    
    
    ###########################################
    # Set initial epidemic conditions 
    ###########################################
    
    # Set parameters
    prevtoforceinf = 0.1 # Assume force-of-infection is proportional to prevalence -- 0.1 means that if prevalence is 10%, annual force-of-infection is 1%
    efftreatmentrate = 0.1 # Inverse of average duration of treatment in years...I think
    fraccare = 0.5 #Assumed fraction of those who have stopped ART (but are still alive) who are in care (as opposed to unreachable/lost)
    
    # Shorten key variables
    initpeople = zeros((nstates, npops)) 
    allinfected = simpars['popsize'][:,0] * simpars['initprev'][:] # Set initial infected population
    
    # Can calculate equilibrium for each population separately
    for p in range(npops):
        # Set up basic calculations
        popinfected = allinfected[p]
        uninfected = simpars['popsize'][p,0] - popinfected # Set initial susceptible population -- easy peasy! -- should this have F['popsize'] involved?
        uncircumcised = uninfected*(1-simpars['circum'][p,0])
        circumcised = uninfected*simpars['circum'][p,0]
        
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
        progratios = hstack([prog, simpars['deathlt50']]) # For last rate, use CD4<50 death as dominant rate
        progratios = (1/progratios)  / sum(1/progratios) # Normalize
        recovratios = hstack([inf, recov, efftreatmentrate]) # Not sure if this is right...inf since no progression to acute, treatmentrate since main entry here -- check
        recovratios = (1/recovratios)  / sum(1/recovratios) # Normalize
        
        # Final calculations
        undiagnosed *= progratios
        diagnosed *= progratios
        treatment *= recovratios
        
        # Populated equilibrated array
        initpeople[uncirc, p] = uncircumcised
        initpeople[circ, p] = circumcised
        initpeople[undx, p] = undiagnosed
        if usecascade:
            initpeople[dx, p]   = diagnosed * (1.-immediatecare[p,0])
            initpeople[care, p] = diagnosed * immediatecare[p,0]
            initpeople[usvl, p] = treatment * (1.-successprop[0])
            initpeople[svl,  p] = treatment * successprop[0]
            #initpeople[lost, p] = 
            #initpeople[off,  p] = 
        else:
            initpeople[dx, p] = diagnosed
            initpeople[tx, p] = treatment
    
        if not((initpeople>=0).all()): # If not every element is a real number >0, throw an error
            err = 'Non-positive people found during epidemic initialization!'  
            raise OptimaException(err)
            
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
            if     male[this['pop1']] and   male[this['pop2']]: this['trans'] = (simpars['transmmi'] + simpars['transmmr'])/2.0 # Note: this looks horrible and stupid but it's correct! Ask Kedz
            elif   male[this['pop1']] and female[this['pop2']]: this['trans'] = simpars['transmfi']  
            elif female[this['pop1']] and   male[this['pop2']]: this['trans'] = simpars['transmfr']
            else: raise OptimaException('Not able to figure out the sex of "%s" and "%s"' % (key[0], key[1]))
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
            if not(allpeople[pop,t]>0): raise OptimaException('No people in population %i at timestep %i (time %0.1f)' % (pop, t, tvec[t]))
            effundx = sum(cd4trans * people[undx,pop,t]); # Effective number of infecious undiagnosed people
            effdx   = sum(dxfactor * people[dx,pop,t]) # ...and diagnosed/failed
            if usecascade:
                effcare = sum(dxfactor * people[care,pop,t]) # the diagnosis efficacy also applies to those in care??
                efftxus = sum(efftxunsupp * people[usvl,pop,t]) # ...and treated
                efftxs  = sum(efftxsupp  * people[svl,pop,t]) # ...and suppressed viral load
                efflost = sum(dxfactor * people[lost,pop,t]) # the diagnosis efficacy also applies to those lost to follow-up??
                effoff  = sum(dxfactor * people[off,pop,t])  # the diagnosis efficacy also applies to those off-ART but in care??
                # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
                effhivprev[pop] = (effundx+effdx+effcare+efftxus+efftxs+efflost+effoff) / allpeople[pop,t]
            else:
                efftx   = sum(txfactor[t] * people[tx,pop,t]) # ...and treated
                effhivprev[pop] = (effundx+effdx+efftx) / allpeople[pop,t] # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count

            if not(effhivprev[pop]>=0): raise OptimaException('HIV prevalence invalid in population %s! (=%f)' % (pop, effhivprev[pop]))
        
        ## Calculate inhomogeneity in the force-of-infection based on prevalence
        for pop in range(npops):
            c = inhomopar[pop]
            thisprev = sum(people[allplhiv,pop,t]) / allpeople[pop,t] 
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
            thisosteff = osteff[t]
            
            thisforceinf = 1 - mpow((1-transinj), (dt*sharing[pop1,t]*effinj*thisosteff*effhivprev[pop2])) 
            forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-thisforceinf)
        
        if not(all(forceinfvec>=0)):
            invalid = [simpars['popkeys'][i] for i in findinds(forceinfvec<0)]
            errormsg = 'Force-of-infection is invalid in population %s' % invalid
            raise OptimaException(errormsg)
            

        
        ###############################################################################
        ## The ODEs
        ###############################################################################
    
        ## Set up
    
        # New infections -- through pre-calculated force of infection
        newinfections = forceinfvec * force * inhomo * people[0,:,t] # Will be useful to define this way when calculating 'cost per new infection'
    
        # Initalise / reset arrays
        dU = []; dD = []
        if usecascade: dC = []; dUSVL = []; dSVL = []; dL = []; dO = []; # Reset differences for cascade compartments
        else: dT = []; # Reset differences for simple compartments
        testingrate  = [0] * ncd4
        newdiagnoses = [0] * ncd4
        if usecascade:
            newtreatCU   = [0] * ncd4
            newtreatOU   = [0] * ncd4
            newlinkcare  = [0] * ncd4
            reengagecareDC = [0] * ncd4
            reengagecareLO = [0] * ncd4
            leavecareCD  = [0] * ncd4
            leavecareOL  = [0] * ncd4
            virallysupp  = [0] * ncd4
            failing      = [0] * ncd4
            stopUSlost   = [0] * ncd4
            stopSVLlost  = [0] * ncd4
            stopUSincare = [0] * ncd4
            stopSVLincare = [0] * ncd4
        else:
            newtreat     = [0] * ncd4

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
            raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 
        dU[0] = dU[0] + newinfections # Now add newly infected people
        

        ############################################################################################################
        ## Here, split and decide whether or not to use the cascade for the rest of the ODEs to solve
        ############################################################################################################
        if usecascade:

            ## Diagnosed
            currentdiagnosed = people[dx,:,t] # Find how many people are diagnosed
            totcurrentpdhiv     = people[[dx,care,usvl,svl,lost,off],:,t].sum() # How many people are pdhiv (regardless of pop or cd4count)
            totcurrentincare    = people[[care,usvl,svl,off],:,t].sum() # How many people are in some form of care (regardless of pop or cd4count)
            totshouldbeincare   = totcurrentpdhiv * pdhivcare[t]
            totmoveintocare     = totshouldbeincare - totcurrentincare
            totcurrentnotincare = totcurrentpdhiv - totcurrentincare
            fracnocarediag = currentdiagnosed / (eps+totcurrentnotincare) # fraction of off-care PDHIV in prelim-diagnosis stage (D/(D+L)) (by cd4 & pop)
            for cd4 in range(ncd4):
                if cd4>0: 
                    progin = dt*prog[cd4-1]*people[dx[cd4-1],:,t]
                else: 
                    progin = 0 # Cannot progress into acute stage
                if cd4<ncd4-1: 
                    progout = dt*prog[cd4]*people[dx[cd4],:,t]
                else: 
                    progout = 0 # Cannot progress out of AIDS stage
                hivdeaths   = dt * people[dx[cd4],:,t] * death[cd4]
                otherdeaths = dt * people[dx[cd4],:,t] * background
                inflows = progin + newdiagnoses[cd4]*(1.-immediatecare[:,t]) # some go immediately into care after testing
                #outflows = progout + hivdeaths + otherdeaths
                newlinkcare[cd4] = currentdiagnosed[cd4,:]*linktocare[:,t]*dt # diagnosed moving into care
                outflows = progout + hivdeaths + otherdeaths + newlinkcare[cd4]
                reengagecareDC[cd4] = totmoveintocare * fracnocarediag[cd4,:]
                reengagecareDC[cd4] = minimum(reengagecareDC[cd4], safetymargin*(currentdiagnosed[cd4,:]+inflows-outflows)) # Ensure you don't remove everyone in diagnosed compartment
                reengagecareDC[cd4] = maximum(reengagecareDC[cd4], -safetymargin*people[care[cd4],:,t]) # Ensure you don't remove everyone in the care compartment
                outflows += reengagecareDC[cd4]
                dD.append(inflows - outflows)
                raw['death'][:,t]  += hivdeaths/dt # Save annual HIV deaths 
                raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 


            ## In-Care
            currentincare = people[care,:,t] # how many people currently in care (by population)
            currentoff    = people[off,:,t]
            totcurrentnotreat = (currentincare + currentoff).sum()
            newtreattot = numtx[t] - people[[usvl,svl],:,t].sum() # Calculate difference between current people on treatment and people needed
            for cd4 in range(ncd4):
                if cd4>0: 
                    progin = dt*prog[cd4-1]*people[care[cd4-1],:,t]
                else: 
                    progin = 0 # Cannot progress into acute stage
                if cd4<ncd4-1: 
                    progout = dt*prog[cd4]*people[care[cd4],:,t]
                else: 
                    progout = 0 # Cannot progress out of AIDS stage
                hivdeaths   = dt * people[care[cd4],:,t] * death[cd4]
                otherdeaths = dt * people[care[cd4],:,t] * background
                leavecareCD[cd4] = dt * people[care[cd4],:,t] * leavecare[:,t]
                inflows = progin + newdiagnoses[cd4]*immediatecare[:,t] + newlinkcare[cd4] + reengagecareDC[cd4]
                outflows = progout + hivdeaths + otherdeaths + leavecareCD[cd4]
                newtreatCU[cd4] = newtreattot * currentincare[cd4,:] / (eps+totcurrentnotreat) # Pull out evenly among incare
                newtreatCU[cd4] = minimum(newtreatCU[cd4], safetymargin*(currentincare[cd4,:]+inflows-outflows)) # Allow it to go negative
                newtreatCU[cd4] = maximum(newtreatCU[cd4], -safetymargin*people[usvl[cd4],:,t]) # Make sure it doesn't exceed the number of people in the treatment compartment
                dC.append(inflows - outflows - newtreatCU[cd4])
                dD[cd4] += leavecareCD[cd4]
                raw['newtreat'][:,t] += newtreatCU[cd4]/dt # Save annual treatment initiation
                raw['death'][:,t]  += hivdeaths/dt # Save annual HIV deaths 
                raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 
            

            ## Unsuppressed Viral Load (having begun treatment)
            currentunsupp    = people[usvl,:,t]
            totcurrentunsupp = currentunsupp.sum()
            currentsupp      = people[svl,:,t]
            totcurrentsupp   = currentsupp.sum()
            totcurrenttreat  = totcurrentsupp + totcurrentunsupp
            totshouldbesupp  = totcurrenttreat * successprop[t]
            totmovetosupp    = totshouldbesupp - totcurrentsupp
            for cd4 in range(ncd4):
                if (cd4>0 and cd4<ncd4-1): # CD4>0 stops people from moving back into acute
                    recovin = dt*recov[cd4-1]*people[usvl[cd4+1],:,t]
                else: 
                    recovin = 0 # Cannot recover in to acute or AIDS stage
                if cd4>1: # CD4>1 stops people from moving back into acute
                    recovout = dt*recov[cd4-2]*people[usvl[cd4],:,t]
                else: 
                    recovout = 0 # Cannot recover out of gt500 stage (or acute stage)
                hivdeaths         = dt * people[usvl[cd4],:,t] * death[cd4] * deathtx # Use death by CD4 state if lower than death on treatment
                otherdeaths       = dt * people[usvl[cd4],:,t] * background
                virallysupp[cd4]  = totmovetosupp * currentunsupp[cd4,:] / (eps+totcurrentunsupp)
                fracalive           = 1. - death[cd4]*deathtx - background
                stopUSincare[cd4] = dt * people[usvl[cd4],:,t] * stoprate[:,t] * fracalive * fraccare  # People stopping ART but still in care
                stopUSlost[cd4]   = dt * people[usvl[cd4],:,t] * stoprate[:,t] * fracalive * (1.-fraccare)  # People stopping ART and lost to followup
                inflows = recovin + newtreatCU[cd4]
                outflows = recovout + hivdeaths + otherdeaths + stopUSincare[cd4] + stopUSlost[cd4] + virallysupp[cd4]
                dUSVL.append(inflows - outflows)
                raw['death'][:,t] += hivdeaths/dt # Save annual HIV deaths 
                raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 
            

            ## Suppressed Viral Load
            for cd4 in range(ncd4):
                if (cd4>0 and cd4<ncd4-1): # CD4>0 stops people from moving back into acute
                    recovin = dt*recov[cd4-1]*people[svl[cd4+1],:,t]
                else: 
                    recovin = 0 # Cannot recover in to acute or AIDS stage
                if cd4>1: # CD4>1 stops people from moving back into acute
                    recovout = dt*recov[cd4-2]*people[svl[cd4],:,t]
                else: 
                    recovout = 0 # Cannot recover out of gt500 stage (or acute stage)
                hivdeaths          = dt * currentsupp[cd4,:] * death[cd4]
                otherdeaths        = dt * currentsupp[cd4,:] * background
                failing[cd4]       = dt * currentsupp[cd4,:] * biofailure[t]
                fracalive       = 1. - death[cd4] - background
                stopSVLincare[cd4] = dt * currentsupp[cd4,:] * stoprate[:,t] * fracalive * fraccare  # People stopping ART but still in care
                stopSVLlost[cd4]   = dt * currentsupp[cd4,:] * stoprate[:,t] * fracalive * (1.-fraccare)  # People stopping ART and lost to followup
                inflows = recovin + virallysupp[cd4]
                outflows = recovout + hivdeaths + otherdeaths + failing[cd4] + stopSVLincare[cd4] + stopSVLlost[cd4]
                dSVL.append(inflows - outflows)
                dUSVL[cd4] += failing[cd4]
                raw['death'][:,t]  += hivdeaths/dt # Save annual HIV deaths 
                raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 


            ## Lost to follow-up (and not in care)
            fracnocarelost = people[lost,:,t] / (eps+totcurrentnotincare) # fraction of off-care PDHIV in off-ART lost     stage (L/(D+L)) (by cd4 & pop)
            for cd4 in range(ncd4):
                if cd4>0: 
                    progin = dt*prog[cd4-1]*people[lost[cd4-1],:,t]
                else: 
                    progin = 0 # Cannot progress into acute stage
                if cd4<ncd4-1: 
                    progout = dt*prog[cd4]*people[lost[cd4],:,t]
                else: 
                    progout = 0 # Cannot progress out of AIDS stage
                hivdeaths   = dt * people[lost[cd4],:,t] * death[cd4]
                otherdeaths = dt * people[lost[cd4],:,t] * background
                inflows  = progin + stopSVLlost[cd4] + stopUSlost[cd4] + leavecareOL[cd4]
                outflows = progout + hivdeaths + otherdeaths
                reengagecareLO[cd4] = totmoveintocare * fracnocarelost[cd4,:]
                reengagecareLO[cd4] = minimum(reengagecareLO[cd4], safetymargin*(people[lost[cd4],:,t]+inflows-outflows)) # Ensure you don't remove everyone in Lost compartment
                reengagecareLO[cd4] = maximum(reengagecareLO[cd4], -safetymargin*people[off[cd4],:,t]) # Ensure you don't remove everyone in the off-ART compartment
                outflows += reengagecareLO[cd4]
                dL.append(inflows - outflows) 
                raw['death'][:,t]  += hivdeaths/dt # Save annual HIV deaths 
                raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 


            ## Off ART but in care
            for cd4 in range(ncd4):
                if cd4>0: 
                    progin = dt*prog[cd4-1]*people[off[cd4-1],:,t]
                else: 
                    progin = 0 # Cannot progress into acute stage
                if cd4<ncd4-1: 
                    progout = dt*prog[cd4]*people[off[cd4],:,t]
                else: 
                    progout = 0 # Cannot progress out of AIDS stage
                hivdeaths   = dt * people[off[cd4],:,t] * death[cd4]
                otherdeaths = dt * people[off[cd4],:,t] * background
                leavecareOL[cd4] = dt * people[off[cd4],:,t] * leavecare[:,t]
                inflows  = progin + reengagecareLO[cd4] + stopSVLincare[cd4] + stopUSincare[cd4] # + reengage
                outflows = progout + hivdeaths + otherdeaths + leavecareOL[cd4]
                newtreatOU[cd4] = newtreattot * currentoff[cd4,:] / (eps+totcurrentnotreat) # Pull out evenly among incare
                newtreatOU[cd4] = minimum(newtreatOU[cd4], safetymargin*(currentincare[cd4,:]+inflows-outflows)) # Allow it to go negative
                newtreatOU[cd4] = maximum(newtreatOU[cd4], -safetymargin*people[usvl[cd4],:,t]) # Make sure it doesn't exceed the number of people in the treatment compartment
                dO.append(inflows - outflows - newtreatOU[cd4])
                dL[cd4] += leavecareOL[cd4] 
                dUSVL[cd4] += newtreatOU[cd4]
                raw['death'][:,t]  += hivdeaths/dt # Save annual HIV deaths 
                raw['otherdeath'][:,t] += otherdeaths/dt    # Save annual other deaths 




        # Or, do not use the cascade
        else: 

            ## Diagnosed
            newtreattot = numtx[t] - people[tx,:,t].sum() # Calculate difference between current people on treatment and people needed
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
                newtreat[cd4] = newtreattot * currentdiagnosed[cd4,:] / (eps+currentdiagnosed.sum()) # Pull out evenly among diagnosed
                hivdeaths   = dt * people[dx[cd4],:,t] * death[cd4]
                otherdeaths = dt * people[dx[cd4],:,t] * background
                inflows = progin + newdiagnoses[cd4]
                outflows = progout + hivdeaths + otherdeaths
                newtreat[cd4] = minimum(newtreat[cd4], safetymargin*(currentdiagnosed[cd4,:]+inflows-outflows)) # Allow it to go negative
                newtreat[cd4] = maximum(newtreat[cd4], -safetymargin*people[tx[cd4],:,t]) # Make sure it doesn't exceed the number of people in the treatment compartment
                dD.append(inflows - outflows - newtreat[cd4])
                raw['newtreat'][:,t] += newtreat[cd4]/dt # Save annual treatment initiation
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
                dT.append(recovin - recovout + newtreat[cd4] - hivdeaths - otherdeaths)
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
                if usecascade:
                    change[care[cd4],:] = dC[cd4]
                    change[usvl[cd4],:] = dUSVL[cd4]
                    change[svl[cd4],:]  = dSVL[cd4]
                    change[lost[cd4],:] = dL[cd4] 
                    change[off[cd4],:]  = dO[cd4]
                else:
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





def runmodel(project=None, simpars=None, pars=None, parset=None, progset=None, budget=None, budgetyears=None, settings=None, start=2000, end=2030, dt=0.2, tvec=None, name=None, uid=None, data=None, verbose=2):
    ''' 
    Convenience function for running the model. Requires input of either "simpars" or "pars"; and for including the data,
    requires input of either "project" or "data". All other inputs are optional.
    
    Version: 2016jan23 by cliffk    
    '''
    if simpars is None:
        if pars is None: raise OptimaException('runmodel() requires either simpars or pars input; neither was provided')
        simpars = makesimpars(pars, start=start, end=end, dt=dt, tvec=tvec, name=name, uid=uid)
    if settings is None:
        try: settings = project.settings 
        except: raise OptimaException('Could not get settings from project "%s" supplied to runmodel()' % project)
    raw = model(simpars=simpars, settings=settings, verbose=verbose) # THIS IS SPINAL OPTIMA
    results = Resultset(project=project, raw=raw, parset=parset, progset=progset, budget=budget, budgetyears=budgetyears, simpars=simpars, data=data, domake=True) # Create structure for storing results
    return results
