"""
Defines the default parameters for each program.

Version: 2016jan28
"""
import os
import optima as op
from optima import OptimaException, Project, Program, Programset, printv, dcp, Parscen, Budgetscen, findinds
try: from optima import pygui # Only used for demo.py, don't worry if can't be imported
except: pass


def defaultprograms(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    ''' Make some default programs'''
    
    # Shorten variable names
    pops = project.data['pops']['short']
    malelist = [pop for popno,pop in enumerate(pops) if project.data['pops']['male'][popno]]
    pwidlist = [pop for popno,pop in enumerate(pops) if project.pars()['injects'][popno]]
    fswlist = [pop for popno,pop in enumerate(pops) if project.pars()['sexworker'][popno]]

    regpships = project.pars()['condreg'].y.keys()
    caspships = project.pars()['condcas'].y.keys()
    compships = project.pars()['condcom'].y.keys()
    
    # Extract casual partnerships that include at least one female sex worker
    fsw_caspships = []
    for fsw in fswlist:
        for caspship in caspships:
            if fsw in caspship:
                fsw_caspships.append(caspship)

    # Extract commercial partnerships that include at least one female sex worker
    fsw_compships = []
    for fsw in fswlist:
        for compship in compships:
            if fsw in compship:
                fsw_compships.append(compship)

    # Extract men who have sex with men
    msmlist = []
    for pship in regpships+caspships+compships:
        if pship[0] in malelist and pship[1] in malelist:
            msmlist.append(pship[0])
    msmlist = list(set(msmlist))

    # Extract casual partnerships that include at least one man who has sex with men
    msm_caspships = []
    for msm in msmlist:
        for caspship in caspships:
            if msm in caspship:
                msm_caspships.append(caspship)

    # Extract casual partnerships that include at least one person who injects drugs
    pwid_caspships = []
    for pwid in pwidlist:
        for caspship in caspships:
            if pwid in caspship:
                pwid_caspships.append(caspship)
    
    # Set up default programs
    Condoms = Program(short='Condoms',
                  name='Condom promotion and distribution',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    SBCC = Program(short='SBCC',
                  name='Social and behavior change communication',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    STI = Program(short='STI',
                  name='Diagnosis and treatment of sexually transmissible infections',
                  category='Prevention',
                  targetpars=[{'param': 'stiprev', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    VMMC = Program(short='VMMC',
                  name='Voluntary medical male circumcision',
                  category='Prevention',
                  targetpars=[{'param': 'numcirc', 'pop': male} for male in malelist],
                  targetpops=malelist,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})              
                  
    FSW_programs = Program(short='FSW programs',
                  name='Programs for female sex workers and clients',
                  category='Prevention',
                  targetpars=[{'param': 'condcom', 'pop': compship} for compship in fsw_compships] + [{'param': 'condcas', 'pop': caspship} for caspship in fsw_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in fswlist],
                  targetpops=fswlist,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                 
    MSM_programs = Program(short='MSM programs',
                  name='Programs for men who have sex with men',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in msm_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in msmlist],
                  targetpops=msmlist,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PWID_programs = Program(short='PWID programs',
                  name='Programs for people who inject drugs',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in pwid_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in pwidlist] + [{'param': 'sharing', 'pop': pop} for pop in pwidlist],
                  targetpops=pwidlist,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    OST = Program(short='OST',
                  name='Opiate substitution therapy',
                  category='Prevention',
                  targetpars=[{'param': 'numost', 'pop': 'tot'}],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    NSP = Program(short='NSP',
                  name='Needle-syringe programs',
                  category='Prevention',
                  targetpars=[{'param': 'sharing', 'pop': pop} for pop in pwidlist],
                  targetpops=pwidlist,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    Cash = Program(short='Cash transfers',
                  name='Cash transfers for HIV risk reduction',
                  category='Prevention',
                  targetpars=[{'param': 'actscas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PrEP = Program(short='PrEP',
                  name='Pre-exposure prophylaxis',
                  category='Prevention',
                  targetpars=[{'param': 'prep', 'pop':  pop} for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PEP = Program(short='PEP',
                  name='Post-exposure prophylaxis',
                  category='Care and treatment',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200', 'gt350'], 'pregnant': False})
                  
    HTC = Program(short='HTC',
                  name='HIV testing and counseling',
                  category='Care and treatment',
                  targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    ART = Program(short='ART',
                  name='Antiretroviral therapy',
                  category='Care and treatment',
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}],# for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    PMTCT = Program(short='PMTCT',
                  name='Prevention of mother-to-child transmission',
                  category='Care and treatment',
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}, {'param': 'numpmtct', 'pop': 'tot'}],
                  targetpops=pops,
                  criteria = {'hivstatus': 'allstates', 'pregnant': True})
                  
    OVC = Program(short='OVC',
                  name='Orphans and vulnerable children',
                  category='Care and treatment',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    Other_care = Program(short='Other care',
                  name='Other HIV care',
                  category='Care and treatment',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200'], 'pregnant': False})
    
    MGMT = Program(short='MGMT',
                  name='Management',
                  category='Management and administration')
    
    HR = Program(short='HR',
                 name='HR and training',
                 category='Management and administration')
    
    ENV = Program(short='ENV',
                  name='Enabling environment',
                  category='Management and administration')
    
    SP = Program(short='SP',
                 name='Social protection',
                 category='Other')
    
    ME = Program(short='ME',
                 name='Monitoring, evaluation, surveillance, and research',
                 category='Other')
    
    INFR = Program(short='INFR',
                   name='Health infrastructure',
                   category='Other')
    
    Other = Program(short='Other',
                    name='Other',
                    category='Other')
                  
    if addcostcovpars:
        Condoms.costcovfn.addccopar({'saturation': (0.75,0.75),
                                 't': 2016.0,
                                 'unitcost': (3,7)})
    
        SBCC.costcovfn.addccopar({'saturation': (0.6,0.6),
                                 't': 2016.0,
                                 'unitcost': (8,12)})
    
        STI.costcovfn.addccopar({'saturation': (0.6,0.6),
                                 't': 2016.0,
                                 'unitcost': (15,20)})
                                 
        VMMC.costcovfn.addccopar({'saturation': (.5,.6),
                                 't': 2016.0,
                                 'unitcost': (15,25)})
                                 
        FSW_programs.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (25,35)})
                                 
        MSM_programs.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (25,35)})
                                 
        PWID_programs.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (25,35)})
                                 
        OST.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (100,200)})
                                 
        NSP.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (10,20)})
                                 
        Cash.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (50,80)})
                                 
        PrEP.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (100,200)})
                                 
        HTC.costcovfn.addccopar({'saturation': (0.85,0.95),
                                 't': 2016.0,
                                 'unitcost': (5,10)})
                                 
        ART.costcovfn.addccopar({'saturation': (0.99,0.99),
                                 't': 2016.0,
                                 'unitcost': (400,800)})
                                 
        PMTCT.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (100,200)})
                                 
    if addcostcovdata:
        
        Condoms.addcostcovdatum({'t':2014,'cost':1e7,'coverage':3e5})
        SBCC.addcostcovdatum({'t':2014,'cost':1e7,'coverage':3e5})
        STI.addcostcovdatum({'t':2014,'cost':1e7,'coverage':3e5})
        VMMC.addcostcovdatum({'t':2014,'cost':1e7,'coverage':3e5})
        FSW_programs.addcostcovdatum({'t':2014,'cost':8e6,'coverage':240000})
        MSM_programs.addcostcovdatum({'t':2014,'cost':8e6,'coverage':240000})
        PWID_programs.addcostcovdatum({'t':2014,'cost':2e6,'coverage':25000})
        OST.addcostcovdatum({'t':2014,'cost':2e6,'coverage':25000})
        NSP.addcostcovdatum({'t':2014,'cost':2e6,'coverage':25000})
        Cash.addcostcovdatum({'t':2014,'cost':2e6,'coverage':25000})
        PrEP.addcostcovdatum({'t':2014,'cost':2e6,'coverage':25000})
        HTC.addcostcovdatum({'t':2014,'cost':2e7,'coverage':1.3e6})
        ART.addcostcovdatum({'t':2014,'cost':1e6,'coverage':3308.})
        PMTCT.addcostcovdatum({'t':2014,'cost':4e6,'coverage':5500})

        OVC.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        Other_care.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        MGMT.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        HR.addcostcovdatum({'t':2014,'cost':5e5,'coverage':None})
        ENV.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        SP.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        ME.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        INFR.addcostcovdatum({'t':2014,'cost':1e7,'coverage':None})
        Other.addcostcovdatum({'t':2014,'cost':5e5,'coverage':None})
        
    allprograms = [Condoms, SBCC, STI, VMMC, FSW_programs, MSM_programs, PWID_programs, OST, NSP, Cash, PrEP, PEP, HTC, ART, PMTCT, OVC, Other_care, MGMT, HR, ENV, SP, ME, INFR, Other]

    if filterprograms: # Only select those programs in filterprograms
        finalprograms = [program for program in allprograms if program.short in filterprograms]
    
    return finalprograms if filterprograms else allprograms
    




def defaultprogset(P, addcostcovpars=False, addcostcovdata=False, filterprograms=None, verbose=2):
    ''' Make a default programset (for testing optimisations)'''
    programs = defaultprograms(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=filterprograms)
    R = Programset(programs=programs, project=P)   
    return R




def defaultproject(which='best', addprogset=True, addcostcovdata=True, usestandardcostcovdata=False, addcostcovpars=True, usestandardcostcovpars=False, addcovoutpars=True, verbose=2, **kwargs):
    ''' 
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing 
    
    Version: 2016mar24
    '''
    
    
    # Figure out the path 
    optimapath = op.__file__
    parentdir = optimapath.split(os.sep)[:-2] # exclude /optima/__init__.pyc
    testdir = parentdir + ['tests'+os.sep]
    spreadsheetpath = os.sep.join(testdir)
    
    
    ##########################################################################################################################
    ## Simple
    ##########################################################################################################################
    
    if which=='simple':
        printv('Creating simple epidemic project...', 2, verbose)
        P = Project(spreadsheet=spreadsheetpath+'simple.xlsx', verbose=verbose, **kwargs)
    




    ##########################################################################################################################
    ## Concentrated
    ##########################################################################################################################
    elif which in ['best','concentrated']:
        printv('Creating concentrated example...', 2, verbose)
        # Make project and store results from default sim
        dorun = kwargs.get('dorun',True) # Use specified dorun setting, otherwise assume true
        kwargs['dorun'] = False # Don't run now, run after calibration
        P = Project(spreadsheet=spreadsheetpath+'concentrated.xlsx', verbose=verbose, **kwargs)
        
        # "Calibrate"
        P.parsets[0].pars[0]['force'].y[:] = [3.50, 1.50, 1.50, 2.00, 3.00, 1.00]
        if dorun: P.runsim() # Run after calibration
    
        # Get a default progset 
        R = defaultprogset(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=['Condoms', 'FSW programs', 'HTC', 'ART', 'Other'])
        
        R.programs['Condoms'].costcovdata =      {'t':[2014],'cost':[1.3e7],'coverage':[3e5]}
        R.programs['FSW programs'].costcovdata = {'t':[2014],'cost':[2.5e6],'coverage':[1e9]}
        R.programs['HTC'].costcovdata =          {'t':[2014],'cost':[1e7],'coverage':[1.3e6]}
        R.programs['ART'].costcovdata =          {'t':[2014],'cost':[2e7],'coverage':[2e4]}
        R.programs['Other'].costcovdata =        {'t':[2014],'cost':[1.5e7],'coverage':[None]}
        
        # Add program effects
        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept':  (0.2,0.25), 't': 2016.0, 'Condoms':(0.35,0.45), 'FSW programs':(0.75,0.85)})
        R.covout['condcas'][('F 15+','Clients')].addccopar({'intercept': (0.25,0.3), 't': 2016.0, 'Condoms':(0.85,0.95)})
        R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept':    (0.3,0.35), 't': 2016.0, 'Condoms':(0.50,0.55), 'FSW programs':(0.59,0.65)})
        R.covout['condcas'][('F 15+', 'M 15+')].addccopar({'intercept':  (0.30,0.35), 't': 2016.0, 'Condoms':(0.45,0.50)})
        R.covout['condcas'][('F 15+', 'PWID')].addccopar({'intercept':   (0.15,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.1,0.15), 't': 2016.0, 'Condoms':(0.55,0.65)})
    
        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'FSW programs':(0.9,0.95)})
    
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'HTC': (0.90,0.95), 'FSW programs':(0.90,0.95)})
        R.covout['hivtest']['Clients'].addccopar({'intercept': (0.10,0.15), 't': 2016.0, 'HTC': (0.40,0.60)})
        R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.01,0.02), 't': 2016.0, 'HTC': (0.20,0.30)})
        R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.01,0.02), 't': 2016.0, 'HTC': (0.20,0.30)})
        R.covout['hivtest']['PWID'].addccopar({'intercept': (0.10,0.15), 't': 2016.0, 'HTC': (0.80,0.90)})
        R.covout['hivtest']['MSM'].addccopar({'intercept': (0.12,0.20), 't': 2016.0, 'HTC': (0.80,0.90)})
    
        R.covout['numtx']['tot'].addccopar({'intercept': (10.0,15.0), 't': 2016.0})
        
        # Store this program set in the project
        P.addprogset(R)
    
    
    
    
    ##########################################################################################################################
    ## Generalized
    ##########################################################################################################################
    elif which=='generalized':
        printv('Creating generalized epidemic project...', 2, verbose)
        P = Project(spreadsheet=spreadsheetpath+'generalized.xlsx', verbose=verbose, **kwargs)

        # Get a default progset 
        R = defaultprogset(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=['Condoms', 'FSW programs', 'MSM programs', 'ART', 'PMTCT', 'VMMC', 'MGMT', 'Other'])

        pops = P.data['pops']['short']
        adultlist = [pops[i] for i in range(len(pops)) if P.data['pops']['age'][i][0]>0]
        
        # Fix up costs
        R.programs['ART'].costcovfn.addccopar({'saturation': (0.9,0.9),
                         't': 2016.0,
                         'unitcost': (1000,2000)}, overwrite=True)
                         
        R.programs['PMTCT'].costcovfn.addccopar({'saturation': (0.9,0.9),
                         't': 2016.0,
                         'unitcost': (5000,8000)}, overwrite=True)

        # Add different modalities of testing
        HTC_workplace = Program(short='HTC workplace',
                      targetpars=[{'param': 'hivtest', 'pop': pop} for pop in ['M 15-49','F 15-49', 'M 50+', 'F 50+', 'Clients']],
                      targetpops=['M 15-49','F 15-49', 'M 50+', 'F 50+', 'Clients'],
                      category='Care and treatment',
                      name='HIV testing and counseling - workplace programs',
                      criteria = {'hivstatus': 'allstates', 'pregnant': False})
        
        HTC_mobile = Program(short='HTC mobile',
                      targetpars=[{'param': 'hivtest', 'pop': pop} for pop in adultlist],
                      targetpops=adultlist,
                      category='Care and treatment',
                      name='HIV testing and counseling - mobile clinics',
                      criteria = {'hivstatus': 'allstates', 'pregnant': False})
        
        HTC_medical = Program(short='HTC medical',
                      targetpars=[{'param': 'hivtest', 'pop': pop} for pop in adultlist],
                      targetpops=adultlist,
                      category='Care and treatment',
                      name='HIV testing and counseling - medical facilities',
                      criteria = {'hivstatus': 'allstates', 'pregnant': False})


        HTC_workplace.costcovfn.addccopar({'saturation': (0.2,0.3),
                                 't': 2016.0,
                                 'unitcost': (10,12)})
        HTC_mobile.costcovfn.addccopar({'saturation': (0.5,0.6),
                                 't': 2016.0,
                                 'unitcost': (6,10)})
        HTC_medical.costcovfn.addccopar({'saturation': (0.4,0.6),
                                 't': 2016.0,
                                 'unitcost': (4,8)})

        HTC_workplace.addcostcovdatum({'t':2014,'cost':1e7,'coverage':9e6})
        HTC_mobile.addcostcovdatum({'t':2014,'cost':1e6,'coverage':2e5})
        HTC_medical.addcostcovdatum({'t':2014,'cost':1e6,'coverage':4e5})
        
        R.addprograms(newprograms=[HTC_workplace, HTC_mobile, HTC_medical])

        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('F 50+', 'Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15-49', 'Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 15-49', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('F 15-49', 'M 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 50+', 'M 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 50+', 'FSW')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('M 50+', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 50+', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65), 'MSM programs':(0.75,0.85)})

        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})
    
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 
                                              't': 2016.0,
                                              'HTC mobile': (0.85,0.9),
                                              'HTC medical': (0.65,0.75),
                                              'FSW programs':(0.95,0.99)})
                                                
        R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1),
                                              't': 2016.0,
                                              'HTC mobile': (0.85,0.9),
                                              'HTC medical': (0.65,0.75),
                                              'MSM programs':(0.95,0.99)})
                                              
        R.covout['hivtest']['Clients'].addccopar({'intercept': (0.05,0.1),
                                                  't': 2016.0,
                                                  'HTC workplace': (0.85,0.9),
                                                  'HTC mobile': (0.85,0.9),
                                                  'HTC medical': (0.65,0.75)})
                                                  
        R.covout['hivtest']['M 15-49'].addccopar({'intercept': (0.35,0.4),
                                                  't': 2016.0,
                                                  'HTC workplace': (0.85,0.9),
                                                  'HTC mobile': (0.85,0.9),
                                                  'HTC medical': (0.85,0.95)})

        R.covout['hivtest']['F 15-49'].addccopar({'intercept': (0.35,0.4),
                                                  't': 2016.0, 
                                                  'HTC workplace': (0.85,0.9),
                                                  'HTC mobile': (0.85,0.9),
                                                  'HTC medical': (0.85,0.95)})

        R.covout['hivtest']['M 50+'].addccopar({'intercept': (0.15,0.2), 
                                                't': 2016.0,
                                                  'HTC workplace': (0.85,0.9),
                                                  'HTC mobile': (0.85,0.9),
                                                  'HTC medical': (0.65,0.75)})

        R.covout['hivtest']['F 50+'].addccopar({'intercept': (0.15,0.2),
                                                't': 2016.0,
                                                  'HTC workplace': (0.85,0.9),
                                                  'HTC mobile': (0.85,0.9),
                                                  'HTC medical': (0.65,0.75)})

        R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
        R.covout['numpmtct']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})

        R.covout['numcirc']['MSM'].addccopar({'intercept': (0,0), 't': 2016.0})
        R.covout['numcirc']['Clients'].addccopar({'intercept': (0,0), 't': 2016.0})
        R.covout['numcirc']['M 15-49'].addccopar({'intercept': (0,0), 't': 2016.0})
        R.covout['numcirc']['M 50+'].addccopar({'intercept': (0,0), 't': 2016.0})
        R.covout['numcirc']['M 0-14'].addccopar({'intercept': (0,0), 't': 2016.0})


        P.addprogset(name='default', progset=R)
        
        
        # Do a super-manual calibration
        P.parsets[0].pars[0]['inhomo'].y[:] = 0.2
    
    
    
    else:
        raise OptimaException('Default project type "%s" not understood: choices are "simple", "generalized", or "concentrated"' % which)
    
    
    return P



def defaultscenarios(project=None, which='budgets', startyear=2016, endyear=2020, parset=-1, progset=-1):
    ''' Add default scenarios to a project...examples include min-max budgets and 90-90-90 '''
    
    if which=='budgets':
        defaultbudget = project.progsets[progset].getdefaultbudget()
        maxbudget = dcp(defaultbudget)
        nobudget = dcp(defaultbudget)
        for key in maxbudget: maxbudget[key] += 1e14
        for key in nobudget: nobudget[key] *= 1e-6
        scenlist = [
            Parscen(name='Current conditions', parsetname='default', pars=[]),
            Budgetscen(name='No budget', parsetname='default', progsetname='default', t=[startyear], budget=nobudget),
            Budgetscen(name='Current budget', parsetname='default', progsetname='default', t=[startyear], budget=defaultbudget),
            Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[startyear], budget=maxbudget),
            ]
    
    # WARNING, this may not entirely work
    if which=='90-90-90':
        project.runsim(parset) # Temporary, to get baseline
        res = project.parsets[parset].getresults()
        curryearind = findinds(res.tvec, startyear)
        currnumplhiv = res.main['numplhiv'].tot[0][curryearind]
        currnumdx =    res.main['numdiag'].tot[0][curryearind]
        currnumtx =    res.main['numtreat'].tot[0][curryearind]
        currpropdx = currnumdx/currnumplhiv
        currproptx = currnumtx/currnumdx
        currvs = project.parsets['default'].pars[0]['treatvs'].interp(startyear)
        
        scenlist = [
            Parscen(name='Current conditions', parsetname='default', pars=[]),
            Parscen(name='90-90-90',
                  parsetname='default',
                  pars=[
                  {'name': 'propdx',
                  'for': ['tot'],
                  'startyear': startyear,
                  'endyear': endyear,
                  'startval': currpropdx,
                  'endval': 0.9,
                  },
                  
                  {'name': 'proptx',
                  'for': ['tot'],
                  'startyear': startyear,
                  'endyear': endyear,
                  'startval': currproptx,
                  'endval': 0.9,
                  },
                  
                  {'name': 'treatvs',
                  'for': ['tot'],
                  'startyear': startyear,
                  'endyear': endyear,
                  'startval': currvs,
                  'endval': .9,
                  },
                    ]),]

    
    # Run the scenarios
    project.addscenlist(scenlist)
    project.runscenarios()
    return scenlist # Return it as well


def demo(doplot=True, **kwargs):
    ''' Do a simple demo of Optima -- similar to simple.py '''
    P = defaultproject(**kwargs)
    if doplot: pygui(P)
    return P
