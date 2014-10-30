"""
MODEL

This function runs the model.

Version: 2014sep25
"""



def model(G, M, options, verbose=2): # extraoutput is to calculate death rates etc.

    if verbose>=1: print('Running model...')
    

    
    ###############################################################################
    ## Setup
    ###############################################################################


    ## Imports
    from matplotlib.pylab import array, zeros # For creating arrays
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    
    ## Initialize basic quantities and arrays
    S = struct() # Sim output structure
    S.tvec = options.tvec # Time vector
    dt = options.dt # Shorten dt
    npts = len(S.tvec) # Number of time points
    
    people = zeros((G.nstates, G.npops, npts)) # Initialize matrix to hold everything
    allpeople = zeros((G.npops, npts))
    people[0, :, 0] = M.popsize[:,0] * (1-M.hivprev[:,0]) # Set initial population sizes
    people[1, :, 0] = M.popsize[:,0] * M.hivprev[:,0] # Set initial population sizes -- # TODO: equilibrate
    effhivprev = zeros((G.npops,1)) # HIV effective prevalence (prevalence times infectiousness)
    dU = []; dD = []; dT1 = []; dF = []; dT2 = [] # Initialize differences
    
    
    ## Convert a health state structure to an array
    def h2a(parstruct):
        healthstates = ['acute','gt500','gt350','gt200','aids'] # TODO, don't redefine these or hard-code them
        outarray = []
        for state in healthstates:
            try: outarray.append(parstruct[state])
            except: print('State %s not found' % state)
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
                stieffM = 1 + M.const.eff.sti*M.stiprev[popM,t] # STI prevalence effect
                stieffF = 1 + M.const.eff.sti*M.stiprev[popF,t] # STI prevalence effect
                transM = M.const.trans.mmi if G.meta.pops.male[popF] else M.const.trans.mfi
                transF = M.const.trans.mmr if G.meta.pops.male[popF] else M.const.trans.mfr
                
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
                if M.pships.drug[pop1,pop2]>0:
                    numacts1 = M.sharing[t] * M.totalacts.drug[pop1,pop2,t] / 2 # Number of acts per person per year -- /2 since otherwise double-count# TODO
                    numacts2 = M.sharing[t] * M.totalacts.drug[pop2,pop1,t] / 2 # Number of acts per person per year
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
        
        
        ## Undiagnosed
        for cd4 in range(G.ncd4):
            progin = dt*prog[cd4-1]*people[G.undx[cd4-1],:,t] if cd4>0 else 0
            progout = dt*prog[cd4] *people[G.undx[cd4],:,t] if cd4<G.ncd4-1 else 0
            testingrate = M.hivtest[:,t] if cd4<G.ncd4-1 else dt*M.aidstest[t]
            newdiagnoses = dt*testingrate * people[G.undx[cd4],:,t]
            hivdeaths = dt*death[cd4]*people[G.undx[cd4],:,t]; 
            dU.append(progin-progout - hivdeaths - newdiagnoses - dt*M.const.death.background*people[G.undx[cd4],:,t])
        dU[0] = dU[0] - dS # Add newly infected people
        
    
        ## Diagnosed
        for cd4 in range(G.ncd4):
            progin  = dt*prog[cd4-1]*people[G.dx[cd4-1],:,t] if cd4>0 else 0
            progout = dt*prog[cd4]  *people[G.dx[cd4],:,t] if cd4<G.ncd4-1 else 0
            testingrate = M.hivtest[:,t] if cd4<G.ncd4-1 else dt*M.aidstest[t]
            newdiagnoses = dt*testingrate * people[G.undx[cd4],:,t]
            newtreat = dt*M.tx1[t] * people[G.dx[cd4],:,t]
            hivdeaths = dt*death[cd4]*people[G.dx[cd4],:,t]
            dD.append(progin-progout + newdiagnoses - newtreat - hivdeaths - dt*M.const.death.background*people[G.dx[cd4],:,t])
        
    
        ## 1st-line treatment
        for cd4 in range(G.ncd4):
            recovin = dt*recov[cd4]*people[G.tx1[cd4+1],:,t) if (cd4<G.ncd4 and cd4>0) else 0
            recovout = dt*recov[cd4]*people[G.tx1[cd4],:,t) if (cd4<G.ncd4 and cd4>0) else 0
            if cd4>1,       recovout=dt*pm.recoveryrate(cd4-1)*people(G.tx1(cd4),:,t);   else recovout=0; end
            peopletotakeoffart = fractionofpeopletotakeoffart*people(G.tx1(cd4),:,t);
            newtreat=dt*pm.treatment1rate(cd4,t)*people(G.dx(cd4),:,t) - peopletotakeoffart*G.maxrate*dt; # WARNING, KLUDGY way to avoid errors by reducing maximum rate
            hivdeaths=dt*pm.deathtreatment*people(G.tx1(cd4),:,t); S.hivdeaths(:,t)=S.hivdeaths(:,t)+hivdeaths'/dt;
            dT1{cd4}=recovin - recovout + newtreat - hivdeaths - (dt*pm.deathbackground+dt*pm.treatment1failurerate).*people(G.tx1(cd4),:,t);

#    
#        # Treatment failure
#        for cd4 in range(G.ncd4):
#            if cd4>1,        progin=dt*pm.progressionrate(cd4-1)*people(G.fail(cd4-1),:,t); else  progin=0; end
#            if cd4<G.ncd4, progout=dt*pm.progressionrate(cd4)  *people(G.fail(cd4),:,t);   else progout=0; end
#            peopletotakeoffart = fractionofpeopletotakeoffart*people(G.tx1(cd4),:,t)*G.maxrate*dt;
#            hivdeaths=dt*pm.deathhiv(cd4)*people(G.fail(cd4),:,t); S.hivdeaths(:,t)=S.hivdeaths(:,t)+hivdeaths'/dt;
#            dF{cd4}=progin-progout + peopletotakeoffart - hivdeaths + dt*pm.treatment1failurerate*people(G.tx1(cd4),:,t) + dt*pm.treatment2failurerate*people(G.tx2(cd4),:,t) - (dt*pm.deathbackground+dt*pm.treatment2rate(t)).*people(G.fail(cd4),:,t);
#    
#        # 2nd-line treatment
#        for cd4 in range(G.ncd4):
#            if cd4<G.ncd4, recovin=dt*pm.recoveryrate(cd4)   *people(G.tx2(cd4+1),:,t); else  recovin=0; end
#            if cd4>1,       recovout=dt*pm.recoveryrate(cd4-1)*people(G.tx2(cd4),:,t);   else recovout=0; end
#            newtreat=dt*pm.treatment2rate(t).*people(G.fail(cd4),:,t);
#            hivdeaths=dt*pm.deathtreatment*people(G.tx2(cd4),:,t); S.hivdeaths(:,t)=S.hivdeaths(:,t)+hivdeaths'/dt;
#            dT2{cd4}=recovin-recovout + newtreat - hivdeaths - (dt*pm.deathbackground+dt*pm.treatment2failurerate).*people(G.tx2(cd4),:,t);
        
#    
#        
#        
#        ## Update next time point and check for errors
#        if t<G.npts
#            change=[dS;vertcat(dU{:});vertcat(dD{:});vertcat(dT1{:});vertcat(dF{:});vertcat(dT2{:})]; # Combine all changes into a single array
#            people(:,:,t+1)=people(:,:,t)+change; # Update people array unless it's the last timestep
#            # Calculate correct population size
#            newpeople=pm.populationsize(:,t+1)'-squeeze(sum(people(:,:,t+1),1)); # Was just the difference in pm.populationsize -- which could be totally different from the actual number of people!
#            for j=1:G.npops # Loop over each population, since some might grow and others might shrink
#                if newpeople(j)>=0 # People are entering: they enter the susceptible population
#                    people(1,j,t+1)=people(1,j,t+1)+newpeople(j); # Number of people entering is the difference between the current model population size and the next time step's defined population size
#                else # People are leaving: they leave from each health state equally
#                    people(:,j,t+1)=people(:,j,t+1)*pm.populationsize(j,t)/sum(people(:,j,t));
#                end
#            end
#            if ~all(all(people(:,:,t+1)>=0)), badpeople(), end # If not every element is a real number >0, throw an error
#        end
#    
#    end
    
    if verbose>=2: print('  ...done running model.')
    return S