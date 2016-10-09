## Imports
from numpy import zeros, exp, maximum, minimum, inf, isinf, array, isnan, einsum, floor, ones, power as npow, concatenate as cat
from optima import OptimaException, printv, dcp, odict, findinds, makesimpars, Resultset

def model(simpars=None, settings=None, verbose=None, die=False, debug=False, initpeople=None):
    """
    Runs Optima's epidemiological model.
    
    Version: 1.7 (2016sep14)
    """
    
    ##################################################################################################################
    ### Setup 
    ##################################################################################################################

    # Initialize basic quantities
    if simpars is None: raise OptimaException('model() requires simpars as an input')
    if settings is None: raise OptimaException('model() requires settings as an input')

    popkeys         = simpars['popkeys']
    npops           = len(popkeys)
    simpars         = dcp(simpars)
    tvec            = simpars['tvec']
    dt              = float(simpars['dt'])          # Shorten dt and make absolutely sure it's a float
    npts            = len(tvec)                     # Number of time points
    ncd4            = settings.ncd4                 # Shorten number of CD4 states
    nstates         = settings.nstates              # Shorten number of health states
    people          = zeros((nstates, npops, npts)) # Matrix to hold everything
    allpeople       = zeros((npops, npts))          # Population sizes
    effallprev      = zeros((nstates, npops))       # HIV effective prevalence (prevalence times infectiousness), by health state
    inhomo          = zeros(npops)                  # Inhomogeneity calculations
    new_movers      = zeros((ncd4, npops))          # Initialise a place to store the number of people that shift into a new compartment (e.g. number of treatment initiators)
    eps             = settings.eps                  # Define another small number to avoid divide-by-zero errors
    forcepopsize    = settings.forcepopsize         # Whether or not to force the population size to match the parameters
    rawtransit      = simpars['rawtransit']         # Raw transitions
    to, prob        = 0,1                           # Indices for entries of rawtransit elements that reference the states that once moves TO and the PROBABILITY of moving
		
    if verbose is None: verbose = settings.verbose # Verbosity of output
    
    # Would be at the top of the script, but need to figure out verbose first
    printv('Running model...', 1, verbose)
    
    # Initialize raw arrays -- reporting annual quantities (so need to divide by dt!)
    raw_inci        = zeros((npops, npts))          # Total incidence acquired by each population
    raw_inciby      = zeros((nstates, npts))        # Total incidence transmitted by each health state
    raw_births      = zeros((npops, npts))          # Total number of births to each population
    raw_mtct        = zeros((npops, npts))          # Number of mother-to-child transmissions to each population
    raw_hivbirths   = zeros((npops, npts))          # Number of births to HIV+ pregnant women
    raw_receivepmtct= zeros((npops, npts))          # Initialise a place to store the number of people in each population receiving PMTCT
    raw_diag        = zeros((npops, npts))          # Number diagnosed per timestep
    raw_newcare     = zeros((npops, npts))          # Number newly in care per timestep
    raw_newtreat    = zeros((npops, npts))          # Number initiating ART per timestep
    raw_newsupp     = zeros((npops, npts))          # Number newly suppressed per timestep
    raw_death       = zeros((npops, npts))          # Number of deaths per timestep
    raw_otherdeath  = zeros((npops, npts))          # Number of other deaths per timestep
    
    # Biological and failure parameters -- death etc
    prog            = maximum(eps,1-exp(-dt/array([simpars['progacute'], simpars['proggt500'], simpars['proggt350'], simpars['proggt200'], simpars['proggt50'],inf]) ))
    svlrecov        = maximum(eps,1-exp(-dt/array([inf,inf,simpars['svlrecovgt350'], simpars['svlrecovgt200'], simpars['svlrecovgt50'], simpars['svlrecovlt50']])))
    deathhiv        = array([simpars['deathacute'],simpars['deathgt500'],simpars['deathgt350'],simpars['deathgt200'],simpars['deathgt50'],simpars['deathlt50']])
    deathsvl        = simpars['deathsvl']           # Death rate whilst on suppressive ART
    deathusvl       = simpars['deathusvl']          # Death rate whilst on unsuppressive ART
    cd4trans        = array([simpars['cd4transacute'], simpars['cd4transgt500'], simpars['cd4transgt350'], simpars['cd4transgt200'], simpars['cd4transgt50'], simpars['cd4translt50']])
    deathprob       = zeros((nstates))              # Initialise death probability array
    background      = simpars['death']*dt

    # Cascade-related parameters
    treatvs         = 1.-exp(-dt/(maximum(eps,simpars['treatvs'])))       # Probability of becoming virally suppressed after 1 time step
    treatfail       = simpars['treatfail']*dt                             # Probability of treatment failure in 1 time step
    freqvlmon       = 1.-exp(-dt*simpars['freqvlmon'])                    # Probability of getting virally monitored in 1 time step
    linktocare      = 1.-exp(-dt/(maximum(eps,simpars['linktocare'])))    # Probability of being linked to care in 1 time step
    leavecare       = simpars['leavecare']*dt                             # Proportion of people lost to follow-up per year
        
    # Disease state indices
    susreg          = settings.susreg               # Susceptible, regular
    progcirc        = settings.progcirc             # Susceptible, programmatically circumcised
    sus             = settings.sus                  # Susceptible, both circumcised and uncircumcised
    undx            = settings.undx                 # Undiagnosed
    dx              = settings.dx                   # Diagnosed
    alldx           = settings.alldx                # All diagnosed
    allcare         = settings.allcare              # All in care
    alltx           = settings.alltx                # All on treatment
    allplhiv        = settings.allplhiv             # All PLHIV
    notonart        = settings.notonart             # All PLHIV who are not on ART    
    care            = settings.care                 # In care
    usvl            = settings.usvl                 # On treatment - Unsuppressed Viral Load
    svl             = settings.svl                  # On treatment - Suppressed Viral Load
    lost            = settings.lost                 # Not on ART (anymore) and lost to follow-up
    acute           = settings.acute                # Acute
    gt500           = settings.gt500                # >500
    gt350           = settings.gt350                # >350
    gt200           = settings.gt200                # >200
    gt50            = settings.gt50                 # >50
    lt50            = settings.lt50                 # <50
    aidsind         = settings.aidsind              # AIDS
    allcd4          = [acute,gt500,gt350,gt200,gt50,lt50]
    dxstates        = [dx,care,usvl,svl,lost]
    carestates      = [care,usvl,svl]
    txstates        = [usvl,svl]
    
    if debug and len(sus)!=2:
        errormsg = 'Definition of susceptibles has changed: expecting regular circumcised + VMMC, but actually length %i' % len(sus)
        raise OptimaException(errormsg)

    # Births, deaths and transitions
    birth           = simpars['birth']*dt           # Multiply birth rates by dt
    agetransit      = simpars['agetransit']      # Multiply age transition rates by dt
    risktransit     = simpars['risktransit']        # Don't multiply risk trnsitions by dt! These are stored as the mean number of years before transitioning, and we incorporate dt later
    birthtransit    = simpars['birthtransit']       # Don't multiply the birth transitions by dt as have already multiplied birth rates by dt
    
    # Shorten to lists of key tuples so don't have to iterate over every population twice for every timestep
    risktransitlist,agetransitlist = [],[]
    for p1 in range(npops):
        for p2 in range(npops):
            if agetransit[p1,p2]:   agetransitlist.append((p1,p2, (1.-exp(-dt/agetransit[p1,p2]))))
            if risktransit[p1,p2]: risktransitlist.append((p1,p2,(1.-exp(-dt/risktransit[p1,p2]))))
    
    # Figure out which populations have age inflows -- don't force population
    ageinflows   = agetransit.sum(axis=0)               # Find populations with age inflows
    birthinflows = birthtransit.sum(axis=0)             # Find populations with birth inflows
    noinflows = findinds(ageinflows+birthinflows==0)    # Find populations with no inflows

    # Begin calculation of transmission probabilities -- continued in time loop
    cd4trans *= settings.transnorm                            # Normalize CD4 transmission
    dxfactor = (1.-simpars['effdx'])                    # Include diagnosis efficacy
    efftxunsupp = (1.-simpars['efftxunsupp'])*dxfactor  # Reduction in transmission probability for usVL
    efftxsupp = (1.-simpars['efftxsupp'])*dxfactor      # Reduction in transmission probability for sVL
    alltrans = zeros(nstates)
    alltrans[undx] = cd4trans
    alltrans[dx] = cd4trans*dxfactor
    alltrans[care] = cd4trans*dxfactor
    alltrans[usvl] = cd4trans*dxfactor*efftxunsupp
    alltrans[svl] = cd4trans*dxfactor*efftxsupp
    alltrans[lost] = cd4trans*dxfactor
    
    # Proportion aware and treated (for 90/90/90)
    propdx      = simpars['propdx']
    propcare    = simpars['propcare']
    proptx      = simpars['proptx']
    propsupp    = simpars['propsupp']
    proppmtct   = simpars['proppmtct']
    
    # These all have the same format, so we put them in tuples of (proptype, data structure for storing output, state below, state in question, states above (inclusing state in question), numerator, denominator, data structure for storing new moveres)
    propdx_list     = ('propdx',propdx, undx, dx, dxstates, alldx, allplhiv, raw_diag)
    propcare_list   = ('propcare',propcare, dx, care, carestates, allcare, alldx, raw_newcare)
    proptx_list     = ('proptx',proptx, care, usvl,  txstates, alltx, allcare, raw_newtreat)
    propsupp_list   = ('propsupp',propsupp, usvl, svl, svl, svl, alltx, raw_newsupp)
            
    # Population sizes
    popsize = dcp(simpars['popsize'])
    
    # Population characteristics
    male    = simpars['male']       # Boolean array, true for males
    female  = simpars['female']     # Boolean array, true for females
    injects = simpars['injects']    # Boolean array, true for PWID

    # Intervention uptake (P=proportion, N=number)
    sharing   = simpars['sharing']      # Sharing injecting equiptment (P)
    numtx     = simpars['numtx']        # 1st line treatement (N) -- tx already used for index of people on treatment [npts]
    hivtest   = simpars['hivtest']*dt   # HIV testing (P) [npop,npts]
    aidstest  = simpars['aidstest']*dt  # HIV testing in AIDS stage (P) [npts]
    numcirc   = simpars['numcirc']      # Number of programmatic circumcisions performed (N)
    numpmtct  = simpars['numpmtct']     # Number of people receiving PMTCT (N)
    
    # Uptake of OST
    numost = simpars['numost']                  # Number of people on OST (N)
    if any(injects):
        numpwid = popsize[injects,:].sum(axis=0)  # Total number of PWID
        try: 
            ostprev = numost/numpwid # Proportion of PWID on OST (P)
            ostprev = minimum(ostprev, 1.0) # Don't let more than 100% of PWID be on OST :)
        except: 
            errormsg = 'Cannot divide by the number of PWID (numost=%f, numpwid=5f' % (numost, numpwid)
            if die: raise OptimaException(errormsg)
            else: 
                printv(errormsg, 1, verbose)
                ostprev = zeros(npts) # Reset to zero
    else: # No one injects
        if numost.sum(): 
            errormsg = 'You have entered non-zero value for the number of PWID on OST, but you have not specified any populations who inject'
            if die: raise OptimaException(errormsg)
            else: 
                printv(errormsg, 1, verbose)
                ostprev = zeros(npts)
        else: # No one on OST
            ostprev = zeros(npts)
    
    # Other interventions
    transinj  = simpars['transinj']                         # Injecting transition probability
    effcondom = simpars['effcondom']                        # Condom effect
    circeff   = 1 - simpars['propcirc']*simpars['effcirc']  # Circumcision efficacy in group where a certain proportion of people are circumcised (susreg group)
    circconst = 1 - simpars['effcirc']                      # Circumcision efficacy in group where everyone is circumcised (progcirc group)
    prepeff   = 1 - simpars['effprep']*simpars['prep']      # PrEP effect
    osteff    = 1 - simpars['effost']*ostprev               # OST effect
    stieff    = 1 + simpars['effsti']*simpars['stiprev']    # STI effect
    effmtct   = simpars['mtctbreast']*simpars['breast'] + simpars['mtctnobreast']*(1-simpars['breast']) # Effective MTCT transmission
    pmtcteff  = (1 - simpars['effpmtct']) * effmtct         # Effective MTCT transmission whilst on PMTCT

    allcirceff = einsum('i,j',[1,circconst],male)+einsum('i,j',[1,1],female)
    alleff = einsum('ab,ab,ab,ca->abc',prepeff,stieff,circeff,allcirceff)

    # Force of infection metaparameter
    force = simpars['force']
    inhomopar = simpars['inhomo']



    ##################################################################################################################
    ### Make time-constant, dt-dependent transitions 
    ##################################################################################################################

    ## Progression and deaths for people not on ART
    for fromstate in notonart:
        fromhealthstate = [(fromstate in j) for j in allcd4].index(True) # CD4 count of fromstate
        for ts, tostate in enumerate(rawtransit[fromstate][to]): # Iterate over the states you could be going to  
            if fromstate not in lt50: # Cannot progress from this state
                if any([(tostate in j) and (fromstate in j) for j in allcd4]):
                    rawtransit[fromstate][prob][ts] *= 1.-prog[fromhealthstate]
                else:
                    rawtransit[fromstate][prob][ts] *= prog[fromhealthstate]
    
            # Death probabilities
            rawtransit[fromstate][1][ts] *= 1.-deathhiv[fromhealthstate]*dt 
            deathprob[fromstate] = deathhiv[fromhealthstate]*dt
            
    ## Recovery and deaths for people on suppressive ART
    for fromstate in svl:
        fromhealthstate = [(fromstate in j) for j in allcd4].index(True) # CD4 count of fromstate
        for ts, tostate in enumerate(rawtransit[fromstate][to]): # Iterate over the states you could be going to  
            if (fromstate not in acute) and (fromstate not in gt500): # You don't recover from these states
                if any([(tostate in j) and (fromstate in j) for j in allcd4]):
                    rawtransit[fromstate][prob][ts] = 1.-svlrecov[fromhealthstate]
                else:
                    rawtransit[fromstate][prob][ts] = svlrecov[fromhealthstate]
        
            if fromstate in acute: # You can progress from acute
                if tostate in acute:
                    rawtransit[fromstate][prob][ts] = 1.-prog[0]
                elif tostate in gt500:
                    rawtransit[fromstate][prob][ts] = prog[0]
    
            # Death probabilities
            rawtransit[fromstate][prob][ts] *= (1.-deathhiv[fromhealthstate]*deathsvl*dt)    
            deathprob[fromstate] = deathhiv[fromhealthstate]*deathsvl*dt
            

    # Recovery and progression and deaths for people on unsuppressive ART
    for fromstate in usvl:
        fromhealthstate = [(fromstate in j) for j in allcd4].index(True) # CD4 count of fromstate
    
        # Iterate over the states you could be going to  
        for ts, tostate in enumerate(rawtransit[fromstate][to]):
            if fromstate in acute: # You can progress from acute
                if tostate in acute:
                    rawtransit[fromstate][prob][ts] = 1.-prog[0]
                elif tostate in gt500:
                    rawtransit[fromstate][prob][ts] = prog[0]
            elif fromstate in gt500: 
                if tostate in gt500:
                    rawtransit[fromstate][prob][ts] = 1.-simpars['usvlproggt500']*dt
                elif tostate in gt350:
                    rawtransit[fromstate][prob][ts] = simpars['usvlproggt500']*dt
            elif fromstate in gt350:
                if tostate in gt500:
                    rawtransit[fromstate][prob][ts] = simpars['usvlrecovgt350']*dt
                elif tostate in gt350:
                    rawtransit[fromstate][prob][ts] = 1.-simpars['usvlrecovgt350']*dt-simpars['usvlproggt350']*dt
                elif tostate in gt200:
                    rawtransit[fromstate][prob][ts] = simpars['usvlproggt350']*dt
            elif fromstate in gt200:
                if tostate in gt350:
                    rawtransit[fromstate][prob][ts] = simpars['usvlrecovgt200']*dt
                elif tostate in gt200:
                    rawtransit[fromstate][prob][ts] = 1.-simpars['usvlrecovgt200']*dt-simpars['usvlproggt200']*dt
                elif tostate in gt50:
                    rawtransit[fromstate][prob][ts] = simpars['usvlproggt200']*dt
            elif fromstate in gt50:
                if tostate in gt200:
                    rawtransit[fromstate][prob][ts] = simpars['usvlrecovgt50']*dt
                elif tostate in gt50:
                    rawtransit[fromstate][prob][ts] = 1.-simpars['usvlrecovgt50']*dt-simpars['usvlproggt50']*dt
                elif tostate in lt50:
                    rawtransit[fromstate][prob][ts] = simpars['usvlproggt50']*dt
            elif fromstate in lt50:
                if tostate in gt50:
                    rawtransit[fromstate][prob][ts] = simpars['usvlrecovlt50']*dt
                elif tostate in lt50:
                    rawtransit[fromstate][prob][ts] = 1.-simpars['usvlrecovlt50']*dt
                                    
            # Death probabilities
            rawtransit[fromstate][prob][ts] *= 1.-deathhiv[fromhealthstate]*deathusvl*dt
            deathprob[fromstate] = deathhiv[fromhealthstate]*deathusvl*dt

  

  
    #################################################################################################################
    ### Set initial epidemic conditions 
    #################################################################################################################
    
    # NB, to debug, use: for h in range(len(settings.statelabels)): print(settings.statelabels[h], sum(initpeople[h,:]))
    
    # Set parameters
    averagedurationinfected = 8.0/2.0   # Assumed duration of undiagnosed HIV pre-AIDS...used for calculating ratio of diagnosed to undiagnosed. WARNING, KLUDGY
    efftreatmentrate = 0.1  # Inverse of average duration of treatment in years...I think

    # Check wither the initial distribution was specified
    if initpeople:
        if debug and initpeople.shape != (nstates, npops):
            errormsg = 'Wrong shape of init distribution: should be (%i, %i) but is %s' % (nstates, npops, initpeople.shape)
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 1, verbose)
                initpeople = None
    
    # If it wasn't specified, or if there's something wrong with it, determine what it should be here
    if not initpeople:

        initpeople = zeros((nstates, npops)) # Initialise
        allinfected = simpars['popsize'][:,0] * simpars['initprev'][:] # Set initial infected population
        initnumtx = minimum(simpars['numtx'][0], allinfected.sum()/(1+eps)) # Don't allow there to be more people on treatment than infected
        uninfected = simpars['popsize'][:,0] - allinfected
        if sum(allinfected): fractotal = allinfected / sum(allinfected) # Fractional total of infected people in this population
        else:                fractotal = zeros(npops) # If there's no one infected, reset to 0
        treatment = initnumtx * fractotal # Number of people on 1st-line treatment
        if debug and any(treatment>allinfected): # More people on treatment than ever infected
            errormsg = 'More people on treatment (%f) than infected (%f)!' % (treatment, allinfected)
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 1, verbose)
                treatment = maximum(allinfected, treatment)

        nevertreated = allinfected - treatment
        fracundiagnosed = exp(-averagedurationinfected*simpars['hivtest'][:,0])
        
        # Set rates within
        progratios = cat([prog[:-1], [simpars['deathlt50']]]) # For last rate, use CD4<50 death as dominant rate
        progratios = (1./progratios)  / sum(1./progratios) # Normalize
        recovratios = cat([svlrecov[1:], [efftreatmentrate]])
        recovratios = (1./recovratios)  / sum(1./recovratios) # Normalize
 
        # Final calculations
        undiagnosed = einsum('i,i,j->ji',nevertreated,fracundiagnosed,progratios)
        diagnosed = einsum('i,i,j->ji',nevertreated,1.-fracundiagnosed,progratios)
        treatment = einsum('i,j->ji',treatment,recovratios)
        
        # Populated equilibrated array
        initpeople[susreg, :]      = uninfected
        initpeople[progcirc, :]    = zeros(npops) # This is just to make it explicit that the circ compartment only keeps track of people who are programmatically circumcised while the model is running
        initpeople[undx, :]        = undiagnosed
        initpeople[dx, :]          = diagnosed*(1.-linktocare[:,0])
        initpeople[care, :]        = diagnosed*linktocare[:,0]
        initpeople[usvl, :]        = treatment * (1.-treatvs)
        initpeople[svl, :]         = treatment * treatvs

    if debug and not(initpeople.all()>=0): # If not every element is a real number >0, throw an error
        errormsg = 'Non-positive people found during epidemic initialization! Here are the people:\n%s' % initpeople
        if die: raise OptimaException(errormsg)
        else:
            printv(errormsg, 1, verbose)
            initpeople[initpeople<0] = 0.0
            
    people[:,:,0] = initpeople
    
    ##################################################################################################################
    ### Compute the effective numbers of acts outside the time loop
    ##################################################################################################################
    sexactslist = []
    injactslist = []
    
    # Sex
    for act in ['reg','cas','com']:
        for key in simpars['acts'+act]:
            this = odict()
            this['wholeacts'] = floor(dt*simpars['acts'+act][key])
            this['fracacts'] = dt*simpars['acts'+act][key] - this['wholeacts'] # Probability of an additional act

            if simpars['cond'+act].get(key) is not None:
                condkey = simpars['cond'+act][key]
            elif simpars['cond'+act].get((key[1],key[0])) is not None:
                condkey = simpars['cond'+act][(key[1],key[0])]
            else:
                errormsg = 'Cannot find condom use between "%s" and "%s", assuming there is none.' % (key[0], key[1]) # NB, this might not be the most reasonable assumption
                if die: raise OptimaException(errormsg)
                else: 
                    printv(errormsg, 1, verbose)
                    condkey = 0.0
                
            this['cond'] = 1.0 - condkey*effcondom
            this['pop1'] = popkeys.index(key[0])
            this['pop2'] = popkeys.index(key[1])
            if     male[this['pop1']] and   male[this['pop2']]: this['trans'] = (simpars['transmmi'] + simpars['transmmr'])/2.0 # Note: this looks horrible and stupid but it's correct! Ask Kedz
            elif   male[this['pop1']] and female[this['pop2']]: this['trans'] = simpars['transmfi']  
            elif female[this['pop1']] and   male[this['pop2']]: this['trans'] = simpars['transmfr']
            else:
                errormsg = 'Not able to figure out the sex of "%s" and "%s"' % (key[0], key[1])
                printv(errormsg, 3, verbose)
                this['trans'] = (simpars['transmmi'] + simpars['transmmr'] + simpars['transmfi'] + simpars['transmfr'])/4.0 # May as well just assume all transmissions apply equally - will undersestimate if pop is predominantly biologically male and oversestimate if pop is predominantly biologically female                     
                    
            sexactslist.append(this)
            
            # Error checking
            for key in ['wholeacts', 'fracacts', 'cond']:
                if debug and not(all(this[key]>=0)):
                    errormsg = 'Invalid sexual behavior parameter "%s": values are:\n%s' % (key, this[key])
                    if die: raise OptimaException(errormsg)
                    else: 
                        printv(errormsg, 1, verbose)
                        this[key][this[key]<0] = 0.0 # Reset values
    
    # Injection
    for key in simpars['actsinj']:
        this = odict()
        this['wholeacts'] = floor(dt*simpars['actsinj'][key])
        this['fracacts'] = dt*simpars['actsinj'][key] - this['wholeacts']
        
        this['pop1'] = popkeys.index(key[0])
        this['pop2'] = popkeys.index(key[1])
        injactslist.append(this)
    
    # Convert from dicts to tuples to be faster
    for i,this in enumerate(sexactslist): sexactslist[i] = tuple([this['pop1'],this['pop2'],this['wholeacts'],this['fracacts'],this['cond'],this['trans']])
    for i,this in enumerate(injactslist): injactslist[i] = tuple([this['pop1'],this['pop2'],this['wholeacts'],this['fracacts']])
    
    
    ## Births precalculation
    birthslist = []
    for p1 in range(npops): 
        alleligbirthrate = einsum('i,j->j',birthtransit[p1, :],birth[p1, :])
        for p2 in range(npops):
            birthrates = birthtransit[p1, p2] * birth[p1, :]
            if birthrates.any():
                birthslist.append(tuple([p1,p2,birthrates,alleligbirthrate]))
                
                

    ##################################################################################################################
    ### Run the model 
    ##################################################################################################################

    for t in range(npts): # Loop over time
        printv('Timestep %i of %i' % (t+1, npts), 4, verbose)
        
        ## Make a copy of the transitions for this timestep
        thistransit = dcp(rawtransit)

        ## Calculate "effective" HIV prevalence -- taking diagnosis and treatment into account
        allpeople[:,t] = people[:, :, t].sum(axis=0)
        if debug and not( all(allpeople[:,t]>0)):
            errormsg = 'No people in populations %s at timestep %i (time %0.1f)' % (findinds(allpeople[:,t]<=0), t, tvec[t])
            if die: raise OptimaException(errormsg)
            else: printv(errormsg, 1, verbose)
                
        effallprev[:,:] = einsum('i,ij->ij',alltrans,people[:,:,t]) / allpeople[:,t]                            
        if debug and not((effallprev[:,:]>=0).all()): 
            errormsg = 'HIV prevalence invalid in populations %s!' % (findinds(effallprev[:,:]<0))
            if die: raise OptimaException(errormsg)
            else:
                printv(errormsg, 1, verbose)
                effallprev = minimum(effallprev,eps)

        ## Calculate inhomogeneity in the force-of-infection based on prevalence
        thisprev = people[allplhiv,:,t].sum(axis=0) / allpeople[:,t] 
        inhomo = (inhomopar+eps) / (exp(inhomopar+eps)-1) * exp(inhomopar*(1-thisprev)) # Don't shift the mean, but make it maybe nonlinear based on prevalence
        
        ###############################################################################
        ## Calculate probability of getting infected
        ###############################################################################
        
        # Probability of getting infected. In the first stage of construction, we actually store this as the probability of NOT getting infected
        # First dimension: infection acquired by (circumcision status). Second dimension:  infection acquired by (pop). Third dimension: infection caused by (pop). Fourth dimension: infection caused by (health/treatment state)
        forceinffull = ones((len(sus), npops, nstates, npops))

        # Loop over all acts (partnership pairs) -- probability of pop1 getting infected by pop2
        for pop1,pop2,wholeacts,fracacts,cond,thistrans in sexactslist:

            thisforceinfsex = (1-fracacts[t]*thistrans*cond[t]*einsum('a,b',alleff[pop1,t,:],effallprev[:,pop2]))
            if wholeacts[t]: thisforceinfsex  *= npow((1-thistrans*cond[t]*einsum('a,b',alleff[pop1,t,:],effallprev[:,pop2])), int(wholeacts[t]))
            forceinffull[:,pop1,:,pop2] *= thisforceinfsex 
            
            if debug and not(forceinffull[:,pop1,:,pop2].all>=0):
                errormsg = 'Sexual force-of-infection is invalid between populations %s and %s, time %0.1f, FOI:\n%s)' % (popkeys[pop1], popkeys[pop2], tvec[t], forceinffull[:,pop1,:,pop2])
                for var in ['thistrans', 'circeff[pop1,t]', 'prepeff[pop1,t]', 'stieff[pop1,t]', 'cond', 'wholeacts', 'fracacts', 'effallprev[:,pop2]']:
                    errormsg += '\n%20s = %f' % (var, eval(var)) # Print out extra debugging information
                raise OptimaException(errormsg)

        # Injection-related infections -- probability of pop1 getting infected by pop2
        for pop1,pop2,wholeacts,fracacts in injactslist:
            
            thisforceinfinj = 1-sharing[pop1,t]*fracacts[t]*transinj*osteff[t]*effallprev[:,pop2]
            if wholeacts[t]: thisforceinfinj *= npow((1-transinj*sharing[pop1,t]*osteff[t]*effallprev[:,pop2]), int(wholeacts[t]))

            for index in sus: # Assign the same probability of getting infected by injection to both circs and uncircs, as it doesn't matter
                forceinffull[index,pop1,:,pop2] *= thisforceinfinj
            
            if debug and not(forceinffull[:,pop1,:,pop2].all>=0):
                errormsg = 'Injecting force-of-infection is invalid between populations %s and %s, time %0.1f, FOI:\n%s)' % (popkeys[pop1], popkeys[pop2], tvec[t], forceinffull[:,pop1,:,pop2])
                for var in ['transinj', 'sharing[pop1,t]', 'wholeacts', 'fracacts', 'osteff[t]', 'effallprev[:,pop2]']:
                    errormsg += '\n%20s = %f' % (var, eval(var)) # Print out extra debugging information
                raise OptimaException(errormsg)
        
        # Probability of getting infected is one minus forceinffull times any scaling factors
        forceinffull = einsum('ijkl,j,j->ijkl', 1.-forceinffull, force, inhomo)
        infections_to = forceinffull.sum(axis=(2,3)) # Infections acquired through sex and injecting - by population who gets infected
        infections_by = forceinffull.sum(axis=(1,3)) # Infections transmitted through sex and injecting - by health state who transmits

        if debug and abs(infections_to.sum() - infections_by.sum()) > 1:
            errormsg = 'Probability of someone getting infected (%f) is not equal to probability of someone causing an infection (%f) at time %i' % (infections_by.sum(), infections_to.sum(), t)
            if die: raise OptimaException(errormsg)
            else: printv(errormsg, 1, verbose)
            
        # Add these transition probabilities to the main array - WARNING, UGLY, FIX
        thistransit[susreg][prob][susreg] = 1. - infections_to[0]
        thistransit[susreg][prob][thistransit[susreg][to].index(undx[0])] = infections_to[0]
        thistransit[progcirc][prob][susreg] = 1. - infections_to[1]
        thistransit[progcirc][prob][thistransit[susreg][to].index(undx[0])] = infections_to[1]


        ##############################################################################################################
        ### Calculate probabilities of shifting along cascade IF programmatically determined
        ##############################################################################################################

        # Deaths
        for state in range(nstates):
            thistransit[state][prob] = (1.-background[:,t])*thistransit[state][prob]

        # Undiagnosed to diagnosed
        if isnan(propdx[t]):
            dxprob = [hivtest[:,t]]*ncd4
            dxprob[aidsind:] = maximum(aidstest[t],hivtest[:,t])
        else: dxprob = zeros(ncd4)
        
        for cd4, fromstate in enumerate(undx):
            for ts, tostate in enumerate(thistransit[fromstate][to]):
                if tostate in undx: # Probability of not being tested
                    thistransit[fromstate][prob][ts] *= (1.-dxprob[cd4])
                else: # Probability of being tested
                    thistransit[fromstate][prob][ts] *= dxprob[cd4]
                    raw_diag[:,t] += people[fromstate,:,t]*thistransit[fromstate][prob][ts]/dt

        # Diagnosed to care
        careprob = linktocare[:,t] if isnan(propcare[t]) else 0.
        for fromstate in dx:
            for ts, tostate in enumerate(thistransit[fromstate][to]):
                if tostate in dx: # Probability of not moving into care
                    thistransit[fromstate][prob][ts] *= (1.-careprob)
                else: # Probability of moving into care
                    thistransit[fromstate][prob][ts] *= careprob

        # Care to lost
        lossprob = leavecare[:,t] if isnan(propcare[t]) else 0.
        for fromstate in care:
            for ts, tostate in enumerate(thistransit[fromstate][to]):
                if tostate in care: # Probability of not being lost and remaining in care
                    thistransit[fromstate][prob][ts] *= (1.-lossprob)
                else: # Probability of being lost
                    thistransit[fromstate][prob][ts] *= lossprob
    
        # Lost to care
        careprob = linktocare[:,t] if isnan(propcare[t]) else 0.
        for fromstate in lost:
            for ts, tostate in enumerate(thistransit[fromstate][to]):
                if tostate in lost: # Probability of not being lost and remaining in care
                    thistransit[fromstate][prob][ts] *= (1.-careprob)
                else: # Probability of being lost
                    thistransit[fromstate][prob][ts] *= careprob
    
        # USVL to SVL
        svlprob = freqvlmon[t] if isnan(propsupp[t]) else 0.
        for fromstate in usvl:
            for ts, tostate in enumerate(thistransit[fromstate][to]):
                if tostate in usvl: # Probability of remaining unsuppressed
                    thistransit[fromstate][prob][ts] *= (1.-svlprob)
                else: # Probability of becoming suppressed
                    thistransit[fromstate][prob][ts] *= svlprob
                                
        # SVL to USVL
        usvlprob = treatfail if isnan(propsupp[t]) else 0.
        for fromstate in svl:
            for ts, tostate in enumerate(thistransit[fromstate][to]):
                if tostate in svl: # Probability of remaining suppressed
                    thistransit[fromstate][prob][ts] *= (1.-usvlprob)
                else: # Probability of becoming unsuppressed
                    thistransit[fromstate][prob][ts] *= usvlprob


        # Check that probabilities all sum to 1
        if debug and not all([(abs(thistransit[j][prob].sum(axis=0)/(1.-background[:,t])+deathprob[j]-ones(npops))<eps).all() for j in range(nstates)]):
            wrongstatesindices = [j for j in range(nstates) if not (abs(thistransit[j][prob].sum(axis=0)/(1.-background[:,t])+deathprob[j]-ones(npops))<eps).all()]
            wrongstates = [settings.statelabels[j] for j in wrongstatesindices]
            wrongprobs = array([thistransit[j][prob].sum(axis=0)/(1.-background[:,t])+deathprob[j] for j in wrongstatesindices])
            errormsg = 'model(): Transitions do not sum to 1 at time t=%f for states %s: sums are \n%s' % (tvec[t], wrongstates, wrongprobs)
            raise OptimaException(errormsg)
            
        # Check that no probabilities are less than 0
        if debug and any([(thistransit[k][prob]<0).any() for k in range(nstates)]):
            wrongstatesindices = [k for k in range(nstates) if (thistransit[k][prob]<0.).any()]
            wrongstates = [settings.statelabels[j] for j in wrongstatesindices]
            wrongprobs = array([thistransit[j][1] for j in wrongstatesindices])
            errormsg = 'model(): Transitions are less than 0 at time t=%f for states %s: sums are \n%s' % (tvec[t], wrongstates, wrongprobs)
            raise OptimaException(errormsg)
            
            
        ## Shift people as required
        if t<npts-1:
            for fromstate, transition in enumerate(thistransit):
                people[transition[to],:,t+1] += people[fromstate,:,t]*transition[prob]


        ## Calculate main indicators
        raw_death[:,t]      = einsum('ij,i->j',  people[:,:,t], deathprob)/dt
        raw_otherdeath[:,t] = einsum('ij,j->j',  people[:,:,t], background[:,t])/dt
        raw_inci[:,t]       = people[susreg,:,t]*thistransit[susreg][prob][thistransit[susreg][to].index(undx[0])] + people[susreg,:,t]*thistransit[progcirc][prob][thistransit[progcirc][to].index(undx[0])]/dt
        raw_inciby[:,t]     = einsum('ij,ki->i', people[:,:,t], infections_by)/dt
        

        ## Calculate births
        for p1,p2,birthrates,alleligbirthrate in birthslist:
            thisbirthrate = birthrates[t]
            peopledx = people[alldx, p1, t].sum() # Assign to a variable since used twice
            popbirths      = thisbirthrate * people[:, p1, t].sum()
            mtctundx       = thisbirthrate * people[undx, p1, t].sum() * effmtct[t] # Births to undiagnosed mothers
            mtcttx         = thisbirthrate * people[alltx, p1, t].sum()  * pmtcteff[t] # Births to mothers on treatment
            thiseligbirths = thisbirthrate * peopledx # Births to diagnosed mothers eligible for PMTCT

            if isnan(proppmtct[t]): # Proportion on PMTCT is not specified: use number
                thisreceivepmtct = min(numpmtct[t]*float(thiseligbirths)/(alleligbirthrate[t]*peopledx+eps), thiseligbirths) # Births protected by PMTCT -- constrained by number eligible 
                mtctdx = (thiseligbirths - thisreceivepmtct) * effmtct[t] # MTCT from those diagnosed not receiving PMTCT
                mtctpmtct = thisreceivepmtct * pmtcteff[t] # MTCT from those receiving PMTCT
            else: # Proportion on PMTCT is specified, ignore number
                if isinf(proppmtct[t]): # If the prop value is infinity, we use last timestep's value
                    if t==0: calcprop=0.
                    else:
                        calcpmtctprop = raw_receivepmtct[:,t-1].sum()/raw_hivbirths[:,t-1].sum()
                else: calcpmtctprop = proppmtct[t]                
                mtctdx = (thiseligbirths * (1-calcpmtctprop)) * effmtct[t] # MTCT from those diagnosed not receiving PMTCT
                mtctpmtct = (thiseligbirths * calcpmtctprop) * pmtcteff[t] # MTCT from those receiving PMTCT
                thisreceivepmtct = thiseligbirths * calcpmtctprop
            popmtct = mtctundx + mtctdx + mtcttx + mtctpmtct # Total MTCT, adding up all components         
            
            raw_receivepmtct[p1, t] += thisreceivepmtct/dt 
            raw_mtct[p2, t] += popmtct/dt
            raw_births[p2, t] += popbirths/dt
            raw_hivbirths[p1, t] += thiseligbirths/dt
            
        raw_inci[:,t] += raw_mtct[:,t] # Update incidence based on PMTCT calculation


        ###############################################################################
        ## Shift numbers of people (circs, treatment, age transitions, risk transitions, prop scenarios)
        ###############################################################################
        if t<npts-1:
            
            ## Births 
            people[undx[0], :, t+1] += raw_mtct[:, t]*dt # HIV+ babies assigned to undiagnosed compartment -- WARNING, shouldn't use a raw variable in a calculation, that's for output
            people[susreg, :, t+1] += (raw_births[:,t] - raw_mtct[:, t])*dt  # HIV- babies assigned to uncircumcised compartment

            ## Circumcision 
            circppl = minimum(numcirc[:,t+1], people[susreg,:,t+1])
            people[susreg,:,t+1]   -= circppl
            people[progcirc,:,t+1] += circppl 


            ## Age-related transitions
            for p1,p2,thisagetransprob in agetransitlist:
                peopleleaving = people[:, p1, t+1] * thisagetransprob
                if debug and (peopleleaving > people[:, p1, t+1]).any():
                    errormsg = 'Age transitions between pops %s and %s at time %i are too high: the age transitions you specified say that %f%% of the population should age in a single time-step.' % (popkeys[p1], popkeys[p2], t+1, agetransit[p1, p2]*100.)
                    if die: raise OptimaException(errormsg)
                    else:
                        printv(errormsg, 1, verbose)
                        peopleleaving = minimum(peopleleaving, people[:, p1, t]) # Ensure positive                     
                people[:, p1, t+1] -= peopleleaving # Take away from pop1...
                people[:, p2, t+1] += peopleleaving # ... then add to pop2

            
            ## Risk-related transitions
            for p1,p2,thisrisktransprob in risktransitlist:
                peoplemoving1 = people[:, p1, t+1] * thisrisktransprob  # Number of other people who are moving pop1 -> pop2
                peoplemoving2 = people[:, p2, t+1] * thisrisktransprob * (sum(people[:, p1, t+1])/sum(people[:, p2, t+1])) # Number of people who moving pop2 -> pop1, correcting for population size
                # Symmetric flow in totality, but the state distribution will ideally change.                
                people[:, p1, t+1] += peoplemoving2 - peoplemoving1 # NOTE: this should not cause negative people; peoplemoving1 is guaranteed to be strictly greater than 0 and strictly less that people[:, p1, t+1]
                people[:, p2, t+1] += peoplemoving1 - peoplemoving2 # NOTE: this should not cause negative people; peoplemoving2 is guaranteed to be strictly greater than 0 and strictly less that people[:, p2, t+1]
            
            
            ###############################################################################
            ## Reconcile population sizes
            ###############################################################################
            
            # Reconcile population sizes for populations with no inflows
            thissusreg = people[susreg,noinflows,t+1] # WARNING, will break if susreg is not a scalar index!
            thisprogcirc = people[progcirc,noinflows,t+1]
            allsus = thissusreg+thisprogcirc
            newpeople = popsize[noinflows,t+1] - people[:,:,t+1][:,noinflows].sum(axis=0) # Number of people to add according to simpars['popsize'] (can be negative)
            people[susreg,noinflows,t+1]   += newpeople*thissusreg/allsus # Add new people
            people[progcirc,noinflows,t+1] += newpeople*thisprogcirc/allsus # Add new people
                        
            # Check population sizes are correct
            actualpeople = people[:,:,t+1][:,noinflows].sum()
            wantedpeople = popsize[noinflows,t+1].sum()
            if debug and abs(actualpeople-wantedpeople)>1.0: # Nearest person is fiiiiine
                errormsg = 'model(): Population size inconsistent at time t=%f: %f vs. %f' % (tvec[t+1], actualpeople, wantedpeople)
                raise OptimaException(errormsg)
            
            # If required, scale population sizes to exactly match the parameters
            if forcepopsize:
                relerr = 0.1 # Set relative error tolerance
                for p in range(npops):
                    susnotonart = cat([sus,notonart])
                    actualpeople = people[susnotonart,p,t+1].sum()
                    wantedpeople = popsize[p,t+1] - people[alltx,p,t+1].sum()
                    if actualpeople==0: raise Exception("ERROR: no people.")
                    ratio = wantedpeople/actualpeople
                    people[susnotonart,p,t+1] *= ratio # Scale to match
                    if abs(ratio-1)>relerr:
                        errormsg = 'Warning, ratio of population sizes is nowhere near 1 (t=%f, pop=%s, wanted=%f, actual=%f, ratio=%f)' % (t+1, popkeys[p], wantedpeople, actualpeople, ratio)
                        if die: raise OptimaException(errormsg)
                        else: printv(errormsg, 1, verbose=verbose)
            

            ###########################################################################
            ## Proportions
            ###########################################################################

            for name,prop,lowerstate,tostate,higherstates,num,denom,raw_new in [propdx_list,propcare_list,proptx_list,propsupp_list]:
                
                if name is 'proptx' or ~isnan(prop[t+1]): #In this section, we shift numbers of people (as opposed to shifting proportions). If any of the prop parameters are non-nan, that means that some number of people will need to shift. However, treatment is special because it is always set by shifting numbers. That's why we have this condition here.

                    # Move the people who started treatment last timestep from usvl to svl
                    if name is 'proptx':
                        if isnan(propsupp[t+1]):
                            newlysuppressed = raw_newtreat[:,t].sum()*dt*treatvs/people[usvl,:,t+1].sum()*people[usvl,:,t+1]
                            people[svl, :,t+1] += newlysuppressed # Shift last period's new initiators into SVL compartment... 
                            people[usvl,:,t+1] -= newlysuppressed # ... and out of USVL compartment, according to treatvs
                            
                        if isnan(prop[t+1]): wanted = numtx[t+1] # If proptx is nan, we use numtx
            
                    # Figure out how many people we currently have
                    actual          = people[num,:,t+1].sum()
                    available       = people[denom,:,t+1].sum()
                    ppltomoveup     = people[lowerstate,:,t+1]

                    # Figure out how many people we want
                    if isinf(prop[t+1]): # If the prop value is infinity, we use last timestep's value
                        calcprop = people[num,:,t].sum()/people[denom,:,t].sum()
                        wanted = calcprop*available
                    if not isnan(prop[t+1]) and not isinf(prop[t+1]): # If the prop value is finite, we use it
                        wanted = prop[t+1]*available

                    # Reconcile the differences between the number we have and the number we want
                    diff = wanted - actual # Wanted number less actual number 
                    if diff>0.: # We need to move people UP the cascade 
                        new_movers      = zeros((ncd4,npops)) 
                        for cd4 in reversed(range(ncd4)): # Going backwards so that lower CD4 counts move up the cascade first
                            if diff>eps: # Move people until you have the right proportions
                                tomove = min(diff, sum(ppltomoveup[cd4,:])) # Figure out how many spots are available
                                new_movers[cd4,:] = tomove * (ppltomoveup[cd4,:]) / (eps+sum(ppltomoveup[cd4,:])) # Pull out evenly from each population
                                diff -= new_movers[cd4,:].sum() # Adjust the number of available spots
                        people[lowerstate,:,t+1] -= new_movers # Shift people out of the lower state... 
                        people[tostate,:,t+1] += new_movers # ... and into the higher state
                        raw_new[:,t] += new_movers.sum(axis=0)/dt # Save new movers
    
                    else: # We need to move people DOWN the cascade
                        for state in higherstates: # Start with the first higher state
                            if abs(diff)>eps: 
                                tomove = max(diff, -people[state,:,t+1].sum()) # Figure out how many spots are available
                                new_movers = tomove*people[state,:,t+1]/(eps+people[state,:,t+1].sum()) # Figure out the distribution of people to move
                                diff -= new_movers.sum() # Adjust the number of available spots
                                people[lowerstate,:,t+1] -= new_movers # Shift people into the lower state... 
                                people[state,:,t+1] += new_movers # ... and out of the higher state
            


            # Check no negative people
            if debug and not((people[:,:,t+1]>=0).all()): # If not every element is a real number >0, throw an error
                for errstate in range(nstates): # Loop over all heath states
                    for errpop in range(npops): # Loop over all populations
                        if not(people[errstate,errpop,t+1]>=0):
                            errormsg = 'WARNING, Non-positive people found!\npeople[%i, %i, %i] = people[%s, %s, %s] = %s and thistransit[%i] = %s' % (errstate, errpop, t+1, settings.statelabels[errstate], popkeys[errpop], tvec[t+1], people[errstate,errpop,t+1], errstate, thistransit[errstate])
                            if die: raise OptimaException(errormsg)
                            else: 
                                printv(errormsg, 1, verbose=verbose)
                                people[errstate,errpop,t+1] = 0.0 # Reset
                                
        raw_diag[:,-1] = raw_diag[:,-2] # Stop new diagnoses being zero in the final year... 
                
    
    raw                 = odict()    # Sim output structure
    raw['tvec']         = tvec
    raw['popkeys']      = popkeys
    raw['people']       = people
    raw['inci']         = raw_inci
    raw['inciby']       = raw_inciby
    raw['mtct']         = raw_mtct
    raw['births']       = raw_births
    raw['hivbirths']    = raw_hivbirths
    raw['receivepmtct'] = raw_receivepmtct
    raw['diag']         = raw_diag
    raw['newtreat']     = raw_newtreat
    raw['death']        = raw_death
    raw['otherdeath']   = raw_otherdeath
    
    
    return raw # Return raw results





def runmodel(project=None, simpars=None, pars=None, parset=None, progset=None, budget=None, coverage=None, budgetyears=None, settings=None, start=None, end=None, dt=None, tvec=None, name=None, uid=None, data=None, debug=False, verbose=2):
    ''' 
    Convenience function for running the model. Requires input of either "simpars" or "pars"; and for including the data,
    requires input of either "project" or "data". All other inputs are optional.
    
    Version: 2016jan23 by cliffk    
    '''
    if settings is None:
        try: settings = project.settings 
        except: raise OptimaException('Could not get settings from project "%s" supplied to runmodel()' % project)
    if start is None: start = project.settings.start
    if end is None: end = project.settings.end
    if dt is None: dt = project.settings.dt
    if simpars is None:
        if pars is None: raise OptimaException('runmodel() requires either simpars or pars input; neither was provided')
        simpars = makesimpars(pars, start=start, end=end, dt=dt, tvec=tvec, name=name, uid=uid)

    try:
        raw = model(simpars=simpars, settings=settings, debug=debug, verbose=verbose) # RUN OPTIMA!!
    except: 
        printv('Running model failed; running again with debugging...', 1, verbose)
        raw = model(simpars=simpars, settings=settings, debug=True, verbose=verbose) # If it failed, run again, with tests
    results = Resultset(project=project, raw=raw, parset=parset, progset=progset, budget=budget, coverage=coverage, budgetyears=budgetyears, pars=pars, simpars=simpars, data=data, domake=True) # Create structure for storing results
    return results
