"""
MODEL

This function runs the model.

Version: 2014sep25
"""



def model(G, P, options, verbose=2): # extraoutput is to calculate death rates etc.

    if verbose>=1: print('Running model...')
    

    
    ###############################################################################
    ## Setup
    ###############################################################################


    ## Imports
    from matplotlib.pylab import array, zeros, arange # For creating arrays
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    
    ## Initialize basic quantities and arrays
    S = struct() # Sim output structure
    S.tvec = options.tvec # Time vector
    dt = options.dt # Shorten dt
    npts = len(S.tvec) # Number of time points
    
    people = zeros((G.nstates, G.npops, npts)) # Initialize matrix to hold everything
    allpeople = zeros((G.npops, npts))
    people[0, :, 0] = P.popsize.p * (1-P.hivprev.p) # Set initial population sizes -- # TODO: calculate properly
    people[1, :, 0] = P.popsize.p * P.hivprev.p # Set initial population sizes
    effhivprevalence = zeros((G.npops,1)) # HIV effective prevalence (prevalence times infectiousness)
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
    cd4trans = h2a(P.const.cd4trans) # Convert a dictionary to an array
    dxfactor = P.const.eff.dx * cd4trans # Include diagnosis efficacy
    txfactor = P.const.eff.tx * dxfactor # And treatment efficacy
    
    
    
    
    
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
            effhivprevalence[pop]=(effundx+effdx+efftx)/allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effhivprevalence[pop]>=0): raise Exception('HIV prevalence invalid in population %s! (=%f)' % (pop,effhivprevalence[pop]) )
        
        ## Calculate force-of-infection (forceinf)
        forceinfvec = zeros(G.npops) # Initialize force-of-infection vector for each population group
        # Sexual partnerships
        for psh in range(Q.nsexpartnerships): # Loop over all sexual partnerships
            
            # Amazingly, the code runs faster if these are pulled out of the equations for forceinf!
            popM = Q.sexpartnershippop[psh,1]; # "Male" population (e.g. 5 = CSW)
            popF = Q.sexpartnershippop[psh,2]; # "Female" population (e.g. 10 = FIDU), but includes MSM and waria
            numacts = dt*Q.numacts[psh,:,t]; # Number of acts per person per year; 2nd dimension is insertive vs. receptive
            condomeffect=1-pm.condomprob(psh,t)*pm.condomefficacy; # Condom use
            circumcisioneffectM=1-pm.circumcisionefficacy*pm.circumcisionprob(popM,t); # Effect of circumcisionumcision
            circumcisioneffectF=1; # circumcision has no effect on the receptive population
            otherinterventioneffectM=1;# Turn off for now 1-pm.otherinterventionefficacy*pm.otherinterventionprob(popM,t); # An "other" intervention, e.g. PEP
            otherinterventioneffectF=1;# Turn off for now 1-pm.otherinterventionefficacy*pm.otherinterventionprob(popF,t); # An "other" intervention, e.g. PEP
            stieffectM=1+pm.stitransincrease*pm.stiprevalence(popM,t); # STI prevalence effect
            stieffectF=1+pm.stitransincrease*pm.stiprevalence(popF,t);
            transmissibilityM=pm.sexpartnershiptrans(psh,1); # Insertive transmissibility
            transmissibilityF=pm.sexpartnershiptrans(psh,2); # Receptive transmissibility
            
            forceinfM = 1 - (1-transmissibilityM*circumcisioneffectM*stieffectM*otherinterventioneffectM) ^ (numacts(1)*condomeffect*effectivehivprevalence(popF)); #/populationsizeM); # The chance of person B infecting person A; pm.cst{psh}(3)=trans; only males are protected by circumcisionumcision
            forceinfF = 1 - (1-transmissibilityF*circumcisioneffectF*stieffectF*otherinterventioneffectF) ^ (numacts(2)*condomeffect*effectivehivprevalence(popM)); #/populationsizeF); # The chance of person A infecting person B
            if any([forceinfM forceinfF]~=median([[forceinfM forceinfF];[0 0];[1 1]])), badforceinf('sex'), end # Error checking: make sure both values lie between 0 and 1
            
            forceinfvec(popM)=1-(1-forceinfvec(popM))*(1-forceinfM); # Calculate the new "male" forceinf, ensuring that it never gets above 1
            forceinfvec(popF)=1-(1-forceinfvec(popF))*(1-forceinfF); # Calculate the new "female" forceinf
            
            if extraoutput # Store information for calculating how many infections are caused by each population
                forceinfmatrix(popM,popF)=1-(1-forceinfmatrix(popM,popF))*(1-forceinfF); # Calculate how many people the male population infected
                forceinfmatrix(popF,popM)=1-(1-forceinfmatrix(popF,popM))*(1-forceinfM); # Calculate how many people the female population infected
            end
        end
        
        
        # Injecting partnerships
        for psh=1:pg.ninjpartnerships # Loop over all injecting partnerships
            
            # Amazingly, the code runs faster if these are pulled out of the equations for forceinf!
            popM=pm.injpartnershippop(psh,1); # "Male" population (e.g. 5 = CSW)
            popF=pm.injpartnershippop(psh,2); # "Female" population (e.g. 10 = FIDU), but includes MSM and waria
            baseforceinfM=pm.transinjecting;
            baseforceinfF=pm.transinjecting;
            cleaningeffect=1-pm.syringecleaningefficacy*pm.syringecleaningprob(t);
            methadoneeffect=1-pm.methadoneefficacy*pm.methadoneprob(t);
            numsharedinjections=dt*pm.numinjectionpairs(psh,:,t)*pm.syringesharingprob(t);
           
            # WARNING, be careful about population size here too
            forceinfM=1 - (1-baseforceinfM*cleaningeffect) ^ (numsharedinjections(1)*methadoneeffect * effectivehivprevalence(popF)); #/populationsizeM); # Force of infection
            forceinfF=1 - (1-baseforceinfF*cleaningeffect) ^ (numsharedinjections(2)*methadoneeffect * effectivehivprevalence(popM)); #/populationsizeF); # Force of infection
            if any([forceinfM forceinfF]~=median([[forceinfM forceinfF];[0 0];[1 1]])), badforceinf('inj'), end # Error checking: make sure both values lie between 0 and 1
            
            forceinfvec(popM)=1-(1-forceinfvec(popM))*(1-forceinfM); # Calculate the new "male" forceinf, ensuring that it never gets above 1
            forceinfvec(popF)=1-(1-forceinfvec(popF))*(1-forceinfF); # Calculate the new "female" forceinf
            
            if extraoutput # Store information for calculating how many infections are caused by each population
                forceinfmatrix(popM,popF)=1-(1-forceinfmatrix(popM,popF))*(1-forceinfF); # Calculate how many people the male population infected
                forceinfmatrix(popF,popM)=1-(1-forceinfmatrix(popF,popM))*(1-forceinfM); # Calculate how many people the female population infected
            end
            
        end
    
    
    
        ###############################################################################
        ## The ODEs
        ###############################################################################
    
        ## Susceptibles
        dS = -forceinfvec * people[0,:,t] # Change in number of susceptibles -- note, death rate already taken into account in pm.totalpop and dt
        dU = []; dD = []; dT1 = []; dF = []; dT2 = []; 
        
        ## Undiagnosed
        
        for cd4 in range(G.ncd4):
            print('hi')
            progin = dt*h2a(P.const.prog)[cd4-1]*people[G.undx[cd4-1],:,t] if cd4>0 else 0
            progout = dt*h2a(P.const.prog)[cd4]  *people[G.undx[cd4],:,t] if cd4<G.ncd4-1 else 0
            testingrate = dt*P.hivtest.p[0] if cd4<G.ncd4-1 else dt*P.aidstest.p # TODO: Fix testing!
            hivdeaths = dt*h2a(P.const.death)[cd4]*people[G.undx[cd4],:,t]; 
            dU.append(progin-progout - hivdeaths - (dt*P.const.death.background+testingrate)*people[G.undx[cd4],:,t])
        dU[0] = dU[0] + forceinfvec*people[0,:,t] # Add newly infected people
    
        ## Diagnosed
        for cd4 in range(G.ncd4):
            progin = dt*h2a(P.const.prog)[cd4-1]*people[G.dx[cd4-1],:,t] if cd4>0 else 0
            progout = dt*h2a(P.const.prog)[cd4] *people[G.dx[cd4],:,t] if cd4<G.ncd4-1 else 0
            testingrate = dt*P.hivtest.p[0] if cd4<G.ncd4-1 else dt*P.aidstest.p # TODO: Fix testing!
            newdiagnoses = testingrate * people[G.undx[cd4],:,t]
            hivdeaths = dt*h2a(P.const.death)[cd4]*people[G.dx[cd4],:,t]
            dD.append(progin-progout + newdiagnoses - hivdeaths - (dt*P.const.death.background)*people[G.dx[cd4],:,t]) # TODO: treatment
    
    
        # 1st-line treatment
        for cd4=1:G.ncd4
            if cd4<G.ncd4, recovin=dt*pm.recoveryrate(cd4)   *people(G.tx1(cd4+1),:,t); else  recovin=0; end
            if cd4>1,       recovout=dt*pm.recoveryrate(cd4-1)*people(G.tx1(cd4),:,t);   else recovout=0; end
            peopletotakeoffart = fractionofpeopletotakeoffart*people(G.tx1(cd4),:,t);
            newtreat=dt*pm.treatment1rate(cd4,t)*people(G.dx(cd4),:,t) - peopletotakeoffart*G.maxrate*dt; # WARNING, KLUDGY way to avoid errors by reducing maximum rate
            hivdeaths=dt*pm.deathtreatment*people(G.tx1(cd4),:,t); S.hivdeaths(:,t)=S.hivdeaths(:,t)+hivdeaths'/dt;
            dT1{cd4}=recovin - recovout + newtreat - hivdeaths - (dt*pm.deathbackground+dt*pm.treatment1failurerate).*people(G.tx1(cd4),:,t);
            if extraoutput
                S.newtreat1(:,t)=S.newtreat1(:,t)+squeeze(newtreat)'/dt; 
                S.tx1bycd4(cd4,:,t)=S.tx1bycd4(cd4,:,t)+newtreat/dt;
                S.deathsbycd4(cd4,:,t)=S.deathsbycd4(cd4,:,t)+hivdeaths/dt;
            end
        end
    
        # Treatment failure
        for cd4=1:G.ncd4
            if cd4>1,        progin=dt*pm.progressionrate(cd4-1)*people(G.fail(cd4-1),:,t); else  progin=0; end
            if cd4<G.ncd4, progout=dt*pm.progressionrate(cd4)  *people(G.fail(cd4),:,t);   else progout=0; end
            peopletotakeoffart = fractionofpeopletotakeoffart*people(G.tx1(cd4),:,t)*G.maxrate*dt;
            hivdeaths=dt*pm.deathhiv(cd4)*people(G.fail(cd4),:,t); S.hivdeaths(:,t)=S.hivdeaths(:,t)+hivdeaths'/dt;
            dF{cd4}=progin-progout + peopletotakeoffart - hivdeaths + dt*pm.treatment1failurerate*people(G.tx1(cd4),:,t) + dt*pm.treatment2failurerate*people(G.tx2(cd4),:,t) - (dt*pm.deathbackground+dt*pm.treatment2rate(t)).*people(G.fail(cd4),:,t);
    
        end
    
        # 2nd-line treatment
        for cd4=1:G.ncd4
            if cd4<G.ncd4, recovin=dt*pm.recoveryrate(cd4)   *people(G.tx2(cd4+1),:,t); else  recovin=0; end
            if cd4>1,       recovout=dt*pm.recoveryrate(cd4-1)*people(G.tx2(cd4),:,t);   else recovout=0; end
            newtreat=dt*pm.treatment2rate(t).*people(G.fail(cd4),:,t);
            hivdeaths=dt*pm.deathtreatment*people(G.tx2(cd4),:,t); S.hivdeaths(:,t)=S.hivdeaths(:,t)+hivdeaths'/dt;
            dT2{cd4}=recovin-recovout + newtreat - hivdeaths - (dt*pm.deathbackground+dt*pm.treatment2failurerate).*people(G.tx2(cd4),:,t);
        end    
        
    
        
        
        ## Update next time point and check for errors
        if t<G.npts
            change=[dS;vertcat(dU{:});vertcat(dD{:});vertcat(dT1{:});vertcat(dF{:});vertcat(dT2{:})]; # Combine all changes into a single array
            people(:,:,t+1)=people(:,:,t)+change; # Update people array unless it's the last timestep
            # Calculate correct population size
            newpeople=pm.populationsize(:,t+1)'-squeeze(sum(people(:,:,t+1),1)); # Was just the difference in pm.populationsize -- which could be totally different from the actual number of people!
            for j=1:G.npops # Loop over each population, since some might grow and others might shrink
                if newpeople(j)>=0 # People are entering: they enter the susceptible population
                    people(1,j,t+1)=people(1,j,t+1)+newpeople(j); # Number of people entering is the difference between the current model population size and the next time step's defined population size
                else # People are leaving: they leave from each health state equally
                    people(:,j,t+1)=people(:,j,t+1)*pm.populationsize(j,t)/sum(people(:,j,t));
                end
            end
            if ~all(all(people(:,:,t+1)>=0)), badpeople(), end # If not every element is a real number >0, throw an error
        end
    
    end
    
    if verbose>=2: print('  ...done running model.')
    return S