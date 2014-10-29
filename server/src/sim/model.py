"""
MODEL

This function runs the model.

Version: 2014sep25
"""



def model(G, P, verbose=2): # extraoutput is to calculate death rates etc.

    if verbose>=1: print('Running model...')


    ###############################################################################
    ## Setup
    ###############################################################################

    ## Imports
    from matplotlib.pylab import array, zeros, r_ # For creating arrays
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    sim = struct()
    sim.popnames = ['GM','GF','FSW','CSW','MSM','PWID']
    ## /TEMP
    
    
    ## Initialize basic quantities and arrays
    people = zeros((G.nstates, G.npops, G.npts)) # Initialize matrix to hold everything
    sim.allpeople = zeros((G.npops, G.npts))
    people[0, :, 0] = P.popsize.p * (1-P.hivprev.p) # Set initial population sizes -- TODO: calculate properly
    people[1, :, 0] = P.popsize.p * P.hivprev.p # Set initial population sizes
    effectivehivprevalence = zeros((G.npops,1)) # HIV effective prevalence (prevalence times infectiousness)
    dt = G.timestep;
    
    
    ###############################################################################
    ## Stuff I don't quite know what to do with -- not crap but not in the best place either
    ###############################################################################
    
    ## Convert a health state structure to an array
    def h2a(parstruct):
        healthstates = ['acute','gt500','gt350','gt200','aids'] # TODO, don't redefine these or hard-code them
        outarray = []
        for state in healthstates:
            try: outarray.append(parstruct[state])
            except: print('State %s not found' % state)
        return array(outarray)
    
    ## Calculate other things outside the loop
    dxfactor = P.const.eff.dx * h2a(P.const.cd4trans)
    
    # TODO: calculate properly, reconciling acts
    tmpnumactsvec = zeros(G.npops)
    tmpforceinfvec = zeros(G.npops)
    for pop in range(G.npops): # TODO: only loop over actual partnerhsips
        tmpnumactsvec[pop] = P.condomreg.p[pop]*P.numactsreg.p[pop] + P.condomcas.p[pop] * P.numactscas.p[pop] + P.condomcom.p[pop] * P.numactscom.p[pop]
        tmpforceinfvec[pop] = P.const.trans.mfr # TODO: use something real
    
    
    
    ###############################################################################
    ## Run the model -- numerically integrate over time
    ###############################################################################
    
    
    
    for t in range(G.npts): # Loop over time; we'll skip the last timestep for people since we don't need to know what happens after that
        
        
        ## Calculate HIV prevalence
        
        for pop in range(G.npops): # Loop over each population group
            sim.allpeople[pop,t] = sum(people[:,pop,t]) # All people in this population group at this time point
            effectiveundiag = sum(h2a(P.const.cd4trans) * people[G.undiag,pop,t]); # Effective number of infecious undiagnosed people
            effectivediag   = sum(dxfactor * (people[G.diag,pop,t]+people[G.fail,pop,t])); # ...and diagnosed/failed
            effectivetreat  = sum(P.const.eff.tx * dxfactor * (people[G.treat1,pop,t]+people[G.treat2,pop,t])) # ...and treated
            effectivehivprevalence[pop]=(effectiveundiag+effectivediag+effectivetreat)/sim.allpeople[pop,t]; # Calculate HIV "prevalence", scaled for infectiousness based on CD4 count; assume that treatment failure infectiousness is same as corresponding CD4 count
            if not(effectivehivprevalence[pop]>=0): 
                raise Exception('HIV prevalence invalid in %s! (=%f)' % (sim.popnames[pop],effectivehivprevalence[pop]) )
        
        ## Calculate force-of-infection (forceinf)
        forceinfvec = zeros(G.npops) # Initialize force-of-infection vector for each population group
        for pop in range(G.npops):    
            forceinfvec[pop] = tmpnumactsvec[pop]*tmpforceinfvec[pop] # TODO: um, calculate properly....
    
    
    
        ###############################################################################
        ## The ODEs
        ###############################################################################
    
        ## Susceptibles
        dS = -forceinfvec * people[0,:,t] # Change in number of susceptibles -- note, death rate already taken into account in pm.totalpop and dt
        dU = []; dD = []; dT1 = []; dF = []; dT2 = []; 
        
        ## Undiagnosed
        
        for cd4 in range(G.ncd4):
            print('hi')
            progin = dt*h2a(P.const.prog)[cd4-1]*people[G.undiag[cd4-1],:,t] if cd4>0 else 0
            progout = dt*h2a(P.const.prog)[cd4]  *people[G.undiag[cd4],:,t] if cd4<G.ncd4-1 else 0
            testingrate = dt*P.hivtest.p[0] if cd4<G.ncd4-1 else dt*P.aidstest.p # TODO: Fix testing!
            hivdeaths = dt*h2a(P.const.death)[cd4]*people[G.undiag[cd4],:,t]; 
            dU.append(progin-progout - hivdeaths - (dt*P.const.death.background+testingrate)*people[G.undiag[cd4],:,t])
        dU[0] = dU[0] + forceinfvec*people[0,:,t] # Add newly infected people
    
        ## Diagnosed
        for cd4 in range(G.ncd4):
            progin = dt*h2a(P.const.prog)[cd4-1]*people[G.diag[cd4-1],:,t] if cd4>0 else 0
            progout = dt*h2a(P.const.prog)[cd4] *people[G.diag[cd4],:,t] if cd4<G.ncd4-1 else 0
            testingrate = dt*P.hivtest.p[0] if cd4<G.ncd4-1 else dt*P.aidstest.p # TODO: Fix testing!
            newdiagnoses = testingrate * people[G.undiag[cd4],:,t]
            hivdeaths = dt*h2a(P.const.death)[cd4]*people[G.diag[cd4],:,t]
            dD.append(progin-progout + newdiagnoses - hivdeaths - (dt*P.const.death.background)*people[G.diag[cd4],:,t]) # TODO: treatment
    
    #
    #    # 1st-line treatment
    #    for cd4=1:G.ncd4
    #        if cd4<G.ncd4, recovin=dt*pm.recoveryrate(cd4)   *people(G.treat1(cd4+1),:,t); else  recovin=0; end
    #        if cd4>1,       recovout=dt*pm.recoveryrate(cd4-1)*people(G.treat1(cd4),:,t);   else recovout=0; end
    #        peopletotakeoffart = fractionofpeopletotakeoffart*people(G.treat1(cd4),:,t);
    #        newtreat=dt*pm.treatment1rate(cd4,t)*people(G.diag(cd4),:,t) - peopletotakeoffart*G.maxrate*dt; # WARNING, KLUDGY way to avoid errors by reducing maximum rate
    #        hivdeaths=dt*pm.deathtreatment*people(G.treat1(cd4),:,t); sim.hivdeaths(:,t)=sim.hivdeaths(:,t)+hivdeaths'/dt;
    #        dT1{cd4}=recovin - recovout + newtreat - hivdeaths - (dt*pm.deathbackground+dt*pm.treatment1failurerate).*people(G.treat1(cd4),:,t);
    #        if extraoutput
    #            sim.newtreat1(:,t)=sim.newtreat1(:,t)+squeeze(newtreat)'/dt; 
    #            sim.tx1bycd4(cd4,:,t)=sim.tx1bycd4(cd4,:,t)+newtreat/dt;
    #            sim.deathsbycd4(cd4,:,t)=sim.deathsbycd4(cd4,:,t)+hivdeaths/dt;
    #        end
    #    end
    #
    #    # Treatment failure
    #    for cd4=1:G.ncd4
    #        if cd4>1,        progin=dt*pm.progressionrate(cd4-1)*people(G.fail(cd4-1),:,t); else  progin=0; end
    #        if cd4<G.ncd4, progout=dt*pm.progressionrate(cd4)  *people(G.fail(cd4),:,t);   else progout=0; end
    #        peopletotakeoffart = fractionofpeopletotakeoffart*people(G.treat1(cd4),:,t)*G.maxrate*dt;
    #        hivdeaths=dt*pm.deathhiv(cd4)*people(G.fail(cd4),:,t); sim.hivdeaths(:,t)=sim.hivdeaths(:,t)+hivdeaths'/dt;
    #        dF{cd4}=progin-progout + peopletotakeoffart - hivdeaths + dt*pm.treatment1failurerate*people(G.treat1(cd4),:,t) + dt*pm.treatment2failurerate*people(G.treat2(cd4),:,t) - (dt*pm.deathbackground+dt*pm.treatment2rate(t)).*people(G.fail(cd4),:,t);
    #
    #    end
    #
    #    # 2nd-line treatment
    #    for cd4=1:G.ncd4
    #        if cd4<G.ncd4, recovin=dt*pm.recoveryrate(cd4)   *people(G.treat2(cd4+1),:,t); else  recovin=0; end
    #        if cd4>1,       recovout=dt*pm.recoveryrate(cd4-1)*people(G.treat2(cd4),:,t);   else recovout=0; end
    #        newtreat=dt*pm.treatment2rate(t).*people(G.fail(cd4),:,t);
    #        hivdeaths=dt*pm.deathtreatment*people(G.treat2(cd4),:,t); sim.hivdeaths(:,t)=sim.hivdeaths(:,t)+hivdeaths'/dt;
    #        dT2{cd4}=recovin-recovout + newtreat - hivdeaths - (dt*pm.deathbackground+dt*pm.treatment2failurerate).*people(G.treat2(cd4),:,t);
    #    end    
    #    
    #
    #    
    #    
    #    ## Update next time point and check for errors
    #    if t<G.npts
    #        change=[dS;vertcat(dU{:});vertcat(dD{:});vertcat(dT1{:});vertcat(dF{:});vertcat(dT2{:})]; # Combine all changes into a single array
    #        people(:,:,t+1)=people(:,:,t)+change; # Update people array unless it's the last timestep
    #        # Calculate correct population size
    #        newpeople=pm.populationsize(:,t+1)'-squeeze(sum(people(:,:,t+1),1)); # Was just the difference in pm.populationsize -- which could be totally different from the actual number of people!
    #        for j=1:G.npops # Loop over each population, since some might grow and others might shrink
    #            if newpeople(j)>=0 # People are entering: they enter the susceptible population
    #                people(1,j,t+1)=people(1,j,t+1)+newpeople(j); # Number of people entering is the difference between the current model population size and the next time step's defined population size
    #            else # People are leaving: they leave from each health state equally
    #                people(:,j,t+1)=people(:,j,t+1)*pm.populationsize(j,t)/sum(people(:,j,t));
    #            end
    #        end
    #        if ~all(all(people(:,:,t+1)>=0)), badpeople(), end # If not every element is a real number >0, throw an error
    #    end
    #
    #end
    
    if verbose>=2: print('  ...done running model.')