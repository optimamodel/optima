"""
Defines the default parameters for each program.

Version: 2016jan28
"""
from optima import OptimaException, Project, Program, Programset


spreadsheetpath = '../tests/' # WARNING, will this work on all systems? If not can just move XLSX files into the Optima directory I suppose...

def defaultprograms(project, addpars=False, addcostcov=False, filterprograms=None):
    ''' Make some default programs'''
    
    # Shorten variable names
    pops = project.data['pops']['short']
    malelist = [pops[i] for i in range(len(pops)) if project.data['pops']['male'][i]]
    pwidlist = [pops[i] for i in range(len(pops)) if project.data['pops']['injects'][i]]
    fswlist = [pops[i] for i in range(len(pops)) if project.data['pops']['sexworker'][i]]

    regpships = project.parsets['default'].pars[0]['condreg'].y.keys()
    caspships = project.parsets['default'].pars[0]['condcas'].y.keys()
    compships = project.parsets['default'].pars[0]['condcom'].y.keys()
    
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
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  category='Prevention',
                  name='Condom promotion and distribution',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    SBCC = Program(short='SBCC',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  category='Prevention',
                  name='Social and behavior change communication',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    STI = Program(short='STI',
                  targetpars=[{'param': 'stiprev', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  category='Prevention',
                  name='Diagnosis and treatment of sexually transmissible infections',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    VMMC = Program(short='VMMC',
                  targetpars=[{'param': 'circum', 'pop': male} for male in malelist],
                  targetpops=malelist,
                  category='Prevention',
                  name='Voluntary medical male circumcision',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})              
                  
    FSW_programs = Program(short='FSW programs',
                  targetpars=[{'param': 'condcom', 'pop': compship} for compship in fsw_compships] + [{'param': 'condcas', 'pop': caspship} for caspship in fsw_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in fswlist],
                  targetpops=fswlist,
                  category='Prevention',
                  name='Programs for female sex workers and clients',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                 
    MSM_programs = Program(short='MSM programs',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in msm_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in msmlist],
                  targetpops=msmlist,
                  category='Prevention',
                  name='Programs for men who have sex with men',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PWID_programs = Program(short='PWID programs',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in pwid_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in pwidlist] + [{'param': 'sharing', 'pop': pop} for pop in pwidlist],
                  targetpops=pwidlist,
                  category='Prevention',
                  name='Programs for people who inject drugs',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    OST = Program(short='OST',
                  targetpars=[{'param': 'numost', 'pop': 'tot'}],
                  targetpops=['tot'],
                  category='Prevention',
                  name='Opiate substitution therapy',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    NSP = Program(short='NSP',
                  targetpars=[{'param': 'sharing', 'pop': pop} for pop in pwidlist],
                  targetpops=pwidlist,
                  category='Prevention',
                  name='Needle-syringe programs',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    Cash_transfers = Program(short='Cash transfers',
                  targetpars=[{'param': 'actscas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  category='Prevention',
                  name='Cash transfers for HIV risk reduction',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PrEP = Program(short='PrEP',
                  targetpars=[{'param': 'prep', 'pop':  pop} for pop in pops],
                  targetpops=pops,
                  category='Prevention',
                  name='Pre-exposure prophylaxis',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PEP = Program(name='PEP',
                  category='Care and treatment',
                  short='PEP',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200', 'gt350'], 'pregnant': False})
                  
    HTC = Program(short='HTC',
                  targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  category='Care and treatment',
                  name='HIV testing and counseling',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    ART = Program(short='ART',
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}],# for pop in pops],
                  targetpops=['tot'],
                  category='Care and treatment',
                  name='Antiretroviral therapy',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200', 'gt350'], 'pregnant': False})
    
    PMTCT = Program(short='PMTCT',
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}, {'param': 'numpmtct', 'pop': 'tot'}],
                  targetpops=['tot'],
                  category='Care and treatment',
                  name='Prevention of mother-to-child transmission',
                  criteria = {'hivstatus': 'allstates', 'pregnant': True})
                  
    OVC = Program(short='OVC',
                  category='Care and treatment',
                  name='Orphans and vulnerable children',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    Other_care = Program(short='Other care',
                  category='Care and treatment',
                  name='Other HIV care',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200'], 'pregnant': False})
    
    MGMT = Program(short='MGMT',
                  category='Management and administration',
                  name='Management')
    
    HR = Program(short='HR',
                  category='Management and administration',
                  name='HR and training')
    
    ENV = Program(short='ENV',
                  category='Management and administration',
                  name='Enabling environment')
    
    SP = Program(short='SP',
                  category='Other',
                  name='Social protection')
    
    ME = Program(short='ME',
                  category='Other',
                  name='Monitoring, evaluation, surveillance, and research')
    
    INFR = Program(short='INFR',
                  category='Other',
                  name='Health infrastructure')
    
    Other = Program(short='Other',
                  category='Other',
                  name='Other')
                  
    if addpars:
        Condoms.costcovfn.addccopar({'saturation': (0.75,0.75),
                                 't': 2016.0,
                                 'unitcost': (30,40)})
    
        SBCC.costcovfn.addccopar({'saturation': (0.6,0.6),
                                 't': 2016.0,
                                 'unitcost': (20,30)})
    
        STI.costcovfn.addccopar({'saturation': (0.6,0.6),
                                 't': 2016.0,
                                 'unitcost': (30,40)})
                                 
        VMMC.costcovfn.addccopar({'saturation': (1.,1.),
                                 't': 2016.0,
                                 'unitcost': (5,8)})
                                 
        FSW_programs.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (50,80)})
                                 
        MSM_programs.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (60,90)})
                                 
        PWID_programs.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (60,90)})
                                 
        OST.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (600,1000)})
                                 
        NSP.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (60,100)})
                                 
        Cash_transfers.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (600,800)})
                                 
        PrEP.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (100,200)})
                                 
        HTC.costcovfn.addccopar({'saturation': (0.55,0.55),
                                 't': 2016.0,
                                 'unitcost': (10,20)})
                                 
        ART.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (200,400)})
                                 
        PMTCT.costcovfn.addccopar({'saturation': (0.9,0.9),
                                 't': 2016.0,
                                 'unitcost': (600,800)})
                                 
    if addcostcov:
        
        Condoms.addcostcovdatum({'t':2016,'cost':1e7,'coverage':3e5})
        SBCC.addcostcovdatum({'t':2016,'cost':1e7,'coverage':3e5})
        STI.addcostcovdatum({'t':2016,'cost':1e7,'coverage':3e5})
        VMMC.addcostcovdatum({'t':2016,'cost':1e7,'coverage':3e5})
        FSW_programs.addcostcovdatum({'t':2016,'cost':1e6,'coverage':15000})
        MSM_programs.addcostcovdatum({'t':2016,'cost':2e6,'coverage':25000})
        PWID_programs.addcostcovdatum({'t':2016,'cost':2e6,'coverage':25000})
        OST.addcostcovdatum({'t':2016,'cost':2e6,'coverage':25000})
        NSP.addcostcovdatum({'t':2016,'cost':2e6,'coverage':25000})
        Cash_transfers.addcostcovdatum({'t':2016,'cost':2e6,'coverage':25000})
        PrEP.addcostcovdatum({'t':2016,'cost':2e6,'coverage':25000})
        HTC.addcostcovdatum({'t':2016,'cost':2e7,'coverage':1.3e6})
        ART.addcostcovdatum({'t':2016,'cost':1e6,'coverage':3308.})
        PMTCT.addcostcovdatum({'t':2016,'cost':4e6,'coverage':5500})

        OVC.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        Other_care.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        MGMT.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        HR.addcostcovdatum({'t':2016,'cost':5e5,'coverage':None})
        ENV.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        SP.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        ME.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        INFR.addcostcovdatum({'t':2016,'cost':1e7,'coverage':None})
        Other.addcostcovdatum({'t':2016,'cost':5e5,'coverage':None})
        
    allprograms = [Condoms, SBCC, STI, VMMC, FSW_programs, MSM_programs, PWID_programs, OST, NSP, Cash_transfers, PrEP, PEP, HTC, ART, PMTCT, OVC, Other_care, MGMT, HR, ENV, SP, ME, INFR, Other]

    if filterprograms:
        finalprograms = [prog for prog in allprograms if prog.short in filterprograms]
    
    return finalprograms if filterprograms else allprograms
    




def defaultprogset(P, addpars=False, addcostcov=False, filterprograms=None):
    ''' Make a default programset (for testing optimisations)'''
    programs = defaultprograms(P, addpars=addpars, addcostcov=addcostcov, filterprograms=filterprograms)
    R = Programset(programs=programs)   
    return R




def defaultproject(which='simple', addprogset=True, **kwargs):
    ''' 
    Options for easily creating default projects based on different spreadsheets, including
    program information -- useful for testing 
    
    Version: 2016jan28
    '''
    
    
    
    ##########################################################################################################################
    ## Simple
    ##########################################################################################################################
    
    if which=='simple':
        print('Creating simple epidemic project...')
        P = Project(spreadsheet=spreadsheetpath+'simple.xlsx', **kwargs)
    
    
    
    
    
    
    ##########################################################################################################################
    ## Generalized
    ##########################################################################################################################
    elif which=='generalized':
        print('Creating generalized epidemic project...')
        P = Project(spreadsheet=spreadsheetpath+'generalized.xlsx', **kwargs)

        # Get a default progset 
        R = defaultprogset(P, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW programs', 'HTC', 'ART', 'PMTCT', 'VMMC'])
        
        # Modify target pars and pops
        R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'M 0-14'})
        R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'F 0-14'})
        R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('M 0-14'))
        R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('F 0-14'))
        R.updateprogset()

        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('FSW', 'Clients')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('Clients', 'F 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 50+', 'Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('Clients', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15-49', 'Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 15-49', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('FSW', 'M 15-49')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('M 15-49', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15-49', 'M 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 15-49', 'F 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 50+', 'M 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 50+', 'FSW')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('FSW', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 50+', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15-49', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('M 50+', 'F 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 50+', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65)})

        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})
        R.covout['condcom'][('FSW', 'Clients')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})
    
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99), 'FSW programs':(0.95,0.99)})
        R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99), 'MSM programs':(0.95,0.99)})
        R.covout['hivtest']['Clients'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['M 15-49'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['F 15-49'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['M 50+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['F 50+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})

        R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
        R.covout['numpmtct']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})

        R.covout['circum']['MSM'].addccopar({'intercept': (0.8,0.9), 't': 2016.0, 'VMMC': (0.95,0.99)})
        R.covout['circum']['Clients'].addccopar({'intercept': (0.8,0.9), 't': 2016.0, 'VMMC': (0.95,0.99)})
        R.covout['circum']['M 15-49'].addccopar({'intercept': (0.8,0.9), 't': 2016.0, 'VMMC': (0.95,0.99)})
        R.covout['circum']['M 50+'].addccopar({'intercept': (0.8,0.9), 't': 2016.0, 'VMMC': (0.95,0.99)})
        R.covout['circum']['M 0-14'].addccopar({'intercept': (0.8,0.9), 't': 2016.0, 'VMMC': (0.95,0.99)})


        P.addprogset(name='default', progset=R)
    
    
    
    ##########################################################################################################################
    ## Concentrated
    ##########################################################################################################################
    elif which=='concentrated':
        # Make project and store results from default sim
        P = Project(spreadsheet=spreadsheetpath+'concentrated.xlsx', **kwargs)
    
        # Get a default progset 
        R = defaultprogset(P, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW programs', 'HTC', 'ART', 'OST'])
        
        # Modify target pars and pops
        R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'M 0-14'})
        R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'F 0-14'})
        R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('M 0-14'))
        R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('F 0-14'))
        R.updateprogset()
    
        # Add program effects
        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('FSW', 'Clients')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('Clients', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15+','Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65), 'MSM programs':(0.75,0.85)})
        R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('FSW', 'M 15+')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
        R.covout['condcas'][('M 15+', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15+', 'M 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('F 15+', 'PWID')].addccopar({'intercept': (0.1,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('PWID', 'F 15+')].addccopar({'intercept': (0.1,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})
    
        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})
        R.covout['condcom'][('FSW', 'Clients')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})
    
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99), 'FSW programs':(0.95,0.99)})
        R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99), 'MSM programs':(0.95,0.99)})
        R.covout['hivtest']['Clients'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['PWID'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99)})
    
        R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
        R.covout['numost']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
        
        # Store this program set in the project
        P.addprogset(R)
    
    
    
    else:
        raise OptimaException('Default project type "%s" not understood: choices are "simple", "generalized", or "concentrated"' % which)
    
    
    return P