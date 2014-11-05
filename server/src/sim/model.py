def model(G, M, options, verbose=2): # extraoutput is to calculate death rates etc.
    """
    MODEL
    
    This function runs the model.
    
    Version: 2014nov05 by cliffk
    """

    
    
    ###############################################################################
    ## Setup
    ###############################################################################


    ## Imports
    from matplotlib.pylab import array, zeros # For creating arrays
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    from printv import printv
    printv('Running model...', 1, verbose)
    
    
    ## Initialize basic quantities and arrays
    S = struct() # Sim output structure
    S.tvec = options.tvec # Time vector
    dt = options.dt # Shorten dt
    npts = len(S.tvec) # Number of time points
    
    people = zeros((G.nstates, G.npops, npts)) # Initialize matrix to hold everything
    allpeople = zeros((G.npops, npts))
    S.inci = zeros((G.npops, npts))
    S.dx = zeros((G.npops, npts))
    S.newtx1 = zeros((G.npops, npts))
    S.newtx2 = zeros((G.npops, npts))
    S.death = zeros((G.npops, npts))
    people[0, :, 0] = M.popsize[:,0] * (1-M.hivprev[:,0]) # Set initial population sizes
    people[1, :, 0] = M.popsize[:,0] * M.hivprev[:,0] # Set initial population sizes -- # TODO: equilibrate
    effhivprev = zeros((G.npops,1)) # HIV effective prevalence (prevalence times infectiousness)
    dU = []; dD = []; dT1 = []; dF = []; dT2 = [] # Initialize differences
    
    
    ## Convert a health state structure to an array
    def h2a(parstruct):
        healthstates = ['acute','gt500','gt350','gt200','aids'] # TODO, don't redefine these or hard-code them
        outarray = []
        for state in healthstates:
            try: 
                outarray.append(parstruct[state])
            except: 
                printv('State %s not found' % state, 4, verbose)
        return array(outarray)
    
    
    ## Calculate other things outside the loop
    cd4trans = h2a(M.const.cd4trans) # Convert a dictionary to an array
    dxfactor = M.const.eff.dx * cd4trans # Include diagnosis efficacy
    txfactor = M.const.eff.tx * dxfactor # And treatment efficacy
    
    
    
    
    
    ###############################################################################
    ## Run the model -- numerically integrate over time
    ###############################################################################
    
    for t in range(npts): # Loop over time; we'll skip the last timestep for people since we don't need to know what happens after that
        
        
        ## Calculate HIV prevalence
        for pop in range(G.npops): # Loop over each population group
            allpeople[pop,t] = sum(people[:,pop,t]) # All people in this population group at this time point
            if not(allpeople[pop,t]>0): raise Exception('No people in population %i at timestep %i (time %0.1f)' % (pop, t, S.tvec[t]))
            effundx = sum(cd4trans * people[G.undx,pop,t]); # Effective number of infecious undiagnosed people
            effdx   = sum(dxfactor * (people[G.dx,pop,t]+people[G.fail,pop,t])) # ...and diagnosed/failed
            efftx   = sum(txfactor * (people[G.tx1,pop,t]+people[G.tx2,pop,t])) # ...and treated
            effhivprev[pop]=(effundx+effdx+efftx)/allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effhivprev[pop]>=0): raise Exception('HIV prevalence invalid in population %s! (=%f)' % (pop,effhivprev[pop]) )
        
        ###############################################################################
        ## Calculate force-of-infection (forceinf)
        forceinfvec = zeros(G.npops) # Initialize force-of-infection vector for each population group
        
        # Sexual partnerships -- # TODO make more efficient
        for popM in range(G.npops):
            for popF in range(G.npops):
                
                circeff = 1 - M.const.eff.circ*M.circum[popM,t] # Effect of circumcision
                stieffM = 1 + M.const.eff.sti*M.stiprevulc[popM,t] # STI prevalence effect
                stieffF = 1 + M.const.eff.sti*M.stiprevulc[popF,t] # STI prevalence effect
                transM = M.const.trans.mmi if G.male[popF] else M.const.trans.mfi
                transF = M.const.trans.mmr if G.male[popF] else M.const.trans.mfr
                
                for act in ['reg','cas','com']:
                    if M.pships[act][popM,popF]>0:
                        numactsM = M.totalacts[act][popM,popF,t]; # Number of acts per person per year
                        numactsF = M.totalacts[act][popF,popM,t]; # Number of acts per person per year
                        condomprob = (M.condom[act][popM,t] + M.condom[act][popF,t]) / 2 # Reconcile condom probability
                        condomeff = 1-condomprob*M.const.eff.condom; # Condom use
                        forceinfM = 1 - (1-transM*circeff*stieffM) ** (dt*numactsM*condomeff*effhivprev[popF]) # The chance of person B infecting person A
                        forceinfF = 1 - (1-transF*circeff*stieffF) ** (dt*numactsF*condomeff*effhivprev[popM]) # The chance of person B infecting person A
                        forceinfvec[popM] = 1 - (1-forceinfvec[popM]) * (1-forceinfM); # Calculate the new "male" forceinf, ensuring that it never gets above 1
                        forceinfvec[popF] = 1 - (1-forceinfvec[popF]) * (1-forceinfF); # Calculate the new "male" forceinf, ensuring that it never gets above 1
                        if not(all(forceinfvec>=0)): raise Exception('Sexual force-of-infection is invalid')
        
        
        # Injecting partnerships -- # TODO make more efficient
#        metheff = 1 - M.const.eff.meth*M.ost[t] # TODO: methadone should be subtracted from population size
        for pop1 in range(G.npops):
            for pop2 in range(G.npops):
                if M.pships.inj[pop1,pop2]>0:
                    numacts1 = M.sharing[t] * M.totalacts.inj[pop1,pop2,t] / 2 # Number of acts per person per year -- /2 since otherwise double-count# TODO
                    numacts2 = M.sharing[t] * M.totalacts.inj[pop2,pop1,t] / 2 # Number of acts per person per year
                    forceinf1 = 1 - (1-M.const.trans.inj) ** (dt*numacts1*effhivprev[pop2]) # Force of infection
                    forceinf2 = 1 - (1-M.const.trans.inj) ** (dt*numacts2*effhivprev[pop1]) # Force of infection
                    forceinfvec[pop1] = 1 - (1-forceinfvec[pop1]) * (1-forceinf1) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    forceinfvec[pop2] = 1 - (1-forceinfvec[pop2]) * (1-forceinf2) # Calculate the new "male" forceinf, ensuring that it never gets above 1
                    if not(all(forceinfvec>=0)): raise Exception('Injecting force-of-infection is invalid')
        
        
        
        
        
        
        ###############################################################################
        ## The ODEs
        ###############################################################################
    
        ## Susceptibles
        dS = -forceinfvec * people[0,:,t] # Change in number of susceptibles -- note, death rate already taken into account in pm.totalpop and dt
        dU = []; dD = []; dT1 = []; dF = []; dT2 = []; 
        
        prog = h2a(M.const.prog)
        death = h2a(M.const.death)
        recov = h2a(M.const.recov)
        testingrate = [0]*G.ncd4
        newdiagnoses = [0]*G.ncd4
        newtreat1 = [0]*G.ncd4
        newtreat2 = [0]*G.ncd4
        newfail1 = [0]*G.ncd4
        newfail2 = [0]*G.ncd4
        background = M.death[:,t]
        
        
        
        
        ## Undiagnosed
        for cd4 in range(G.ncd4):
            if cd4>0: 
                progin = dt*prog[cd4-1]*people[G.undx[cd4-1],:,t]
            else: 
                progin = 0
            if cd4<G.ncd4-1: 
                progout = dt*prog[cd4] *people[G.undx[cd4],:,t]
                testingrate[cd4] = M.hivtest[:,t]
            else: 
                progout = 0
                testingrate[cd4] = dt*M.aidstest[t]
            newdiagnoses[cd4] = dt*testingrate[cd4] * people[G.undx[cd4],:,t]
            S.tx[:,t] += newdiagnoses[cd4]/dt # Save annual diagnoses data
            hivdeaths = dt*death[cd4]*people[G.undx[cd4],:,t]
            S.death[:,t] += hivdeaths[cd4]/dt # Save annual diagnoses data
            dU.append(progin-progout - hivdeaths - newdiagnoses[cd4] - dt*background*people[G.undx[cd4],:,t])
            
        dU[0] = dU[0] - dS # Add newly infected people
        
    
        ## Diagnosed
        for cd4 in range(G.ncd4):
            if cd4>0: 
                progin  = dt*prog[cd4-1]*people[G.dx[cd4-1],:,t]
            else: 
                progin = 0
            if cd4<G.ncd4-1: 
                progout = dt*prog[cd4]*people[G.dx[cd4],:,t]
            else: 
                progout = 0
            newtreat1[cd4] = dt*M.tx1[t] * people[G.dx[cd4],:,t]
            S.newtx1[:,t] += newtreat1[cd4]/dt # Save annual diagnoses data
            hivdeaths = dt*death[cd4]*people[G.dx[cd4],:,t]
            S.death[:,t] += hivdeaths[cd4]/dt # Save annual diagnoses data
            dD.append(progin-progout + newdiagnoses[cd4] - newtreat1[cd4] - hivdeaths - dt*background*people[G.dx[cd4],:,t])
        
    
        ## 1st-line treatment
        for cd4 in range(G.ncd4):
            if (cd4>0 and cd4<G.ncd4-1): # CD4>0 stops people from moving back into acute
                recovin = dt*recov[cd4-1]*people[G.tx1[cd4+1],:,t]
            else: 
                recovin = 0 
            if cd4>1: # CD4>1 stops people from moving back into acute
                recovout = dt*recov[cd4-2]*people[G.tx1[cd4],:,t]
            else: 
                recovout = 0
            newfail1[cd4] = dt*M.const.fail.first * people[G.tx1[cd4],:,t]
            hivdeaths = dt*death[cd4]*people[G.tx1[cd4],:,t]
            S.death[:,t] += hivdeaths[cd4]/dt # Save annual deats data
            dT1.append(recovin - recovout + newtreat1[cd4] - newfail1[cd4] - hivdeaths - dt*background*people[G.tx1[cd4],:,t])

    
        ## Treatment failure
        for cd4 in range(G.ncd4):
            if cd4>0:
                progin = dt*prog[cd4-1]*people[G.fail[cd4-1],:,t] 
            else: 
                progin = 0
            if cd4<G.ncd4-1: 
                progout = dt*prog[cd4]*people[G.fail[cd4],:,t] 
            else: 
                progout = 0
            newtreat2[cd4] = dt*M.tx2[t] * people[G.fail[cd4],:,t]
            S.newtx2[:,t] += newtreat2[cd4]/dt # Save annual treatment data
            newfail2[cd4] = dt*M.const.fail.second * people[G.tx2[cd4],:,t]
            hivdeaths = dt*death[cd4]*people[G.fail[cd4],:,t]
            S.death[:,t] += hivdeaths[cd4]/dt # Save annual deaths data
            dF.append(progin - progout + newfail1[cd4] + newfail2[cd4] - newtreat2[cd4] - hivdeaths - dt*background*people[G.fail[cd4],:,t])
        
     
        ## 2nd-line treatment
        for cd4 in range(G.ncd4):
            if (cd4>0 and cd4<G.ncd4-1): # CD4>0 stops people from moving back into acute
                recovin = dt*recov[cd4-1]*people[G.tx2[cd4+1],:,t]
            else: 
                recovin = 0 
            if cd4>1: # CD4>1 stops people from moving back into acute
                recovout = dt*recov[cd4-2]*people[G.tx2[cd4],:,t]
            else: 
                recovout = 0
            hivdeaths = dt*death[cd4]*people[G.tx2[cd4],:,t]
            S.death[:,t] += hivdeaths[cd4]/dt # Save annual deaths data
            dT2.append(recovin - recovout + newtreat2[cd4] - newfail2[cd4] - hivdeaths - dt*background*people[G.tx2[cd4],:,t])
        
     
        ## Update next time point and check for errors
        if t<npts-1:
            change = zeros((G.nstates,G.npops))
            change[G.sus,:] = dS
            for cd4 in range(G.ncd4): # TODO: this could be made much more efficient
                change[G.undx[cd4],:] = dU[cd4]
                change[G.dx[cd4],:] = dD[cd4]
                change[G.tx1[cd4],:] = dT1[cd4]
                change[G.fail[cd4],:] = dF[cd4]
                change[G.tx2[cd4],:] = dT2[cd4]
            people[:,:,t+1] = people[:,:,t] + change # Update people array unless it's the last timestep
            # Calculate correct population size
            newpeople = M.popsize[:,t+1] # Was just the difference in pm.populationsize -- which could be totally different from the actual number of people!
            for pop in range(G.npops): # Loop over each population, since some might grow and others might shrink
                if newpeople[pop]>=0: # People are entering: they enter the susceptible population
                    people[0,pop,t+1] += newpeople[pop] # Number of people entering is the difference between the current model population size and the next time step's defined population size
                else: # People are leaving: they leave from each health state equally
                    people[:,pop,t+1] *= M.popsize[pop,t]/sum(people[:,pop,t]);
            if not((people[:,:,t+1]>=0).all()):
                raise Exception('Non-positive people found') # If not every element is a real number >0, throw an error
    
    S.people = people # Copy final people array
    printv('  ...done running model.', 2, verbose)
    return S