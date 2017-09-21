"""
Defines the default parameters for each program.

Version: 2016jan28
"""
import os
from numpy import array, nan
from optima import OptimaException, Project, Program, Programset, printv, dcp, odict



def defaultprograms(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    ''' Make some default programs'''
    
    # Shorten variable names
    pops = project.pars()['popkeys']
    hivstates = project.settings.hivstates
    malelist   = array(pops)[project.pars()['male']].tolist()
    femalelist = array(pops)[project.pars()['female']].tolist()
    pwidlist   = array(pops)[project.pars()['injects']].tolist()
    regpships = project.pars()['condreg'].keys()
    caspships = project.pars()['condcas'].keys()
    compships = project.pars()['condcom'].keys()
    
    # Extract female sex workers
    fswlist = []
    for pship in compships:
        for pop in pship:
            if pop in femalelist:
                fswlist.append(pop)
    fswlist = list(set(fswlist))

    # Extract men who have sex with men
    msmlist = []
    for pship in regpships+caspships+compships:
        if pship[0] in malelist and pship[1] in malelist:
            msmlist += list(pship) # Add both populations
    msmlist = list(set(msmlist))
    
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
                  criteria = {'hivstatus': hivstates, 'pregnant': False})
    
    Lab = Program(short='Lab',
                  name='Lab monitoring',
                  category='Care and treatment',
                  targetpars=[{'param': 'numvlmon', 'pop': 'tot'}],# for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': hivstates, 'pregnant': False})
    
    Adherence = Program(short='Adherence',
                  name='Adherence support',
                  category='Care and treatment',
                  targetpars=[{'param': 'leavecare', 'pop': pop} for pop in pops],# for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': hivstates, 'pregnant': False})
    
    Tracing = Program(short='Tracing',
                  name='Pre-ART tracing',
                  category='Care and treatment',
                  targetpars=[{'param': 'linktocare', 'pop': pop} for pop in pops],# for pop in pops],
                  targetpops=pops,
                  criteria = {'hivstatus': hivstates, 'pregnant': False})
    
    PMTCT = Program(short='PMTCT',
                  name='Prevention of mother-to-child transmission',
                  category='Care and treatment',
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}, {'param': 'numpmtct', 'pop': 'tot'}],
                  targetpops=pops,
                  criteria = {'hivstatus': hivstates, 'pregnant': True})
                  
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
                                 
        Lab.costcovfn.addccopar({'saturation': (0.99,0.99),
                                 't': 2016.0,
                                 'unitcost': (40,80)})
                                 
        Adherence.costcovfn.addccopar({'saturation': (0.99,0.99),
                                 't': 2016.0,
                                 'unitcost': (20,50)})
                                 
        Tracing.costcovfn.addccopar({'saturation': (0.99,0.99),
                                 't': 2016.0,
                                 'unitcost': (20,50)})
                                 
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
        Lab.addcostcovdatum({'t':2014,'cost':1e5,'coverage':2000.})
        Adherence.addcostcovdatum({'t':2014,'cost':1e5,'coverage':2000.})
        Tracing.addcostcovdatum({'t':2014,'cost':2e1,'coverage':2000.})
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
        
    allprograms = [Condoms, SBCC, STI, VMMC, FSW_programs, MSM_programs, PWID_programs, OST, NSP, Cash, PrEP, PEP, HTC, ART, Lab, Adherence, Tracing, PMTCT, OVC, Other_care, MGMT, HR, ENV, SP, ME, INFR, Other]

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
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    spreadsheetpath = os.path.join(parentfolder, 'tests', '') # Empty last part puts a /
    
    
    ##########################################################################################################################
    ## Simple
    ##########################################################################################################################
    
    if which=='simple':
        printv('Creating simple epidemic project...', 2, verbose)
        
        # Set up project
        dorun = kwargs.get('dorun',True) # Use specified dorun setting, otherwise assume true
        kwargs['dorun'] = False # Don't run now, run after calibration
        P = Project(name='Simple (demo)', spreadsheet=spreadsheetpath+'simple.xlsx', verbose=verbose, **kwargs)
        P.pars()['transnorm'].y = 0.8 # "Calibration"
        P.pars()['fixproptx'].t = 2100 # For optimization to work
        if dorun: P.runsim() # Run after calibration
        
        # Programs
        R = defaultprogset(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=['HTC', 'ART'])
        R.programs['HTC'].costcovdata =          {'t':[2014],'cost':[20e6],'coverage':[1e6]}
        R.programs['ART'].costcovdata =          {'t':[2014],'cost': [2e6],'coverage':[1e4]}
        R.covout['hivtest']['M 15-49'].addccopar({'intercept': (0.01,0.01), 't': 2016.0, 'HTC': (0.30,0.30)})
        R.covout['hivtest']['F 15-49'].addccopar({'intercept': (0.01,0.01), 't': 2016.0, 'HTC': (0.30,0.30)})
        R.covout['numtx']['tot'].addccopar({'intercept': (10.0,10.0), 't': 2016.0})
        P.addprogset(R)
    




    ##########################################################################################################################
    ## Concentrated
    ##########################################################################################################################
    elif which in ['best','concentrated']:
        printv('Creating concentrated example...', 2, verbose)
        # Make project and store results from default sim
        dorun = kwargs.get('dorun',True) # Use specified dorun setting, otherwise assume true
        kwargs['dorun'] = False # Don't run now, run after calibration
        if which=='best': name = 'demo' # Just keep it simple
        else:             name = 'Concentrated (demo)' # If asked for concentrated, keep it in the name
        P = Project(name=name, spreadsheet=spreadsheetpath+'concentrated.xlsx', verbose=verbose, **kwargs)
        
        # "Calibrate"
        P.pars()['force'].y[:] = [3.5, 1.5, 1.5, 1.7, 3.0, 0.4]
        if dorun: P.runsim() # Run after calibration
    
        # Get a default progset 
        R = defaultprogset(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=['Condoms', 'FSW programs', 'HTC', 'ART', 'Lab', 'Adherence', 'Tracing', 'Other'])
        
        R.programs['Condoms'].costcovdata =      {'t':[2014],'cost':[1.3e7],'coverage':[3e5]}
        R.programs['FSW programs'].costcovdata = {'t':[2014],'cost':[2.5e6],'coverage':[1e9]}
        R.programs['HTC'].costcovdata =          {'t':[2014],'cost':[1e7],'coverage':[1.3e6]}
        R.programs['ART'].costcovdata =          {'t':[2014],'cost':[5e7],'coverage':[4.81e4]}
        R.programs['Lab'].costcovdata =          {'t':[2014],'cost':[1.3e6],'coverage':[1e4]}
        R.programs['Adherence'].costcovdata =    {'t':[2014],'cost':[1e6],'coverage':[1e4]}
        R.programs['Tracing'].costcovdata =      {'t':[2014],'cost':[8e5],'coverage':[1e4]}
        R.programs['Other'].costcovdata =        {'t':[2014],'cost':[1.5e7],'coverage':[None]}
        
        # Add program effects
        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept':  (0.2,0.25), 't': 2016.0, 'Condoms':(0.35,0.45), 'FSW programs':(0.75,0.85)})
        R.covout['condcas'][('Clients','F 15+')].addccopar({'intercept': (0.25,0.3), 't': 2016.0, 'Condoms':(0.85,0.95)})
        R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept':    (0.3,0.35), 't': 2016.0, 'Condoms':(0.50,0.55), 'FSW programs':(0.59,0.65)})
        R.covout['condcas'][('M 15+','F 15+')].addccopar({'intercept':  (0.30,0.35), 't': 2016.0, 'Condoms':(0.45,0.50)})
        R.covout['condcas'][('PWID','F 15+')].addccopar({'intercept':   (0.15,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.1,0.15), 't': 2016.0, 'Condoms':(0.55,0.65)})
    
        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'FSW programs':(0.9,0.95)})
    
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'HTC': (0.90,0.95), 'FSW programs':(0.90,0.95)})
        R.covout['hivtest']['Clients'].addccopar({'intercept': (0.10,0.15), 't': 2016.0, 'HTC': (0.40,0.60)})
        R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.01,0.02), 't': 2016.0, 'HTC': (0.20,0.30)})
        R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.01,0.02), 't': 2016.0, 'HTC': (0.20,0.30)})
        R.covout['hivtest']['PWID'].addccopar({'intercept': (0.10,0.15), 't': 2016.0, 'HTC': (0.80,0.90)})
        R.covout['hivtest']['MSM'].addccopar({'intercept': (0.12,0.20), 't': 2016.0, 'HTC': (0.80,0.90)})
    
        R.covout['numtx']['tot'].addccopar({'intercept': (10.0,15.0), 't': 2016.0})
        R.covout['numvlmon']['tot'].addccopar({'intercept': (10.0,15.0), 't': 2016.0})
        
        R.covout['leavecare']['FSW'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'Adherence': (0.05,0.1)})
        R.covout['leavecare']['Clients'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'Adherence': (0.05,0.1)})
        R.covout['leavecare']['M 15+'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'Adherence': (0.05,0.1)})
        R.covout['leavecare']['F 15+'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'Adherence': (0.05,0.1)})
        R.covout['leavecare']['PWID'].addccopar({'intercept': (0.50,0.60), 't': 2016.0, 'Adherence': (0.3,0.4)})
        R.covout['leavecare']['MSM'].addccopar({'intercept': (0.30,0.40), 't': 2016.0, 'Adherence': (0.05,0.1)})
    
        R.covout['linktocare']['FSW'].addccopar({'intercept': (1.40,1.60), 't': 2016.0, 'Tracing': (0.1,0.3)})
        R.covout['linktocare']['Clients'].addccopar({'intercept': (1.40,1.60), 't': 2016.0, 'Tracing': (0.1,0.3)})
        R.covout['linktocare']['M 15+'].addccopar({'intercept': (1.40,1.60), 't': 2016.0, 'Tracing': (0.1,0.3)})
        R.covout['linktocare']['F 15+'].addccopar({'intercept': (1.40,1.60), 't': 2016.0, 'Tracing': (0.1,0.3)})
        R.covout['linktocare']['PWID'].addccopar({'intercept': (1.40,1.60), 't': 2016.0, 'Tracing': (0.1,0.3)})
        R.covout['linktocare']['MSM'].addccopar({'intercept': (1.40,1.60), 't': 2016.0, 'Tracing': (0.1,0.3)})
    
        # Store this program set in the project
        P.addprogset(R)
    
    
    
    
    ##########################################################################################################################
    ## Generalized
    ##########################################################################################################################
    elif which=='generalized':

        printv('Creating generalized epidemic project...', 2, verbose)

        P = Project(name='Generalized (demo)', spreadsheet=spreadsheetpath+'generalized.xlsx', verbose=verbose, **kwargs)

        ## Calibrate
        defaultps = dcp(P.parsets[0]) # Copy the default parset
        P.rmparset(0) # Remove the default parset
    
        parset = dcp(defaultps)
        parset.name = 'Treatment fixed'
        pars = parset.pars
        pars['initprev'].y[:] = [0.7, 0.14, 0.28, 0.03, 0.03,
                                 0.022, 0.078, 0.046, 0.175, 0.18,
                                 0.245, 0.078, 0.13]
        pars['force'].y[:] = odict([('FSW', 3.59),
                                    ('Clients', 0.80),
                                    ('MSM', 0.19),
                                    ('Males 0-9', 0.),
                                    ('Females 0-9', 0.),
                                    ('Males 10-19', 0.95),
                                    ('Females 10-19', 1.09),
                                    ('Males 20-24', 0.76),
                                    ('Females 20-24', 1.81),
                                    ('Males 25-49', 2.),
                                    ('Females 25-49', 1.1),
                                    ('Males 50+', 1.18),
                                    ('Females 50+', 1.10)])
        pars['hivtest'].m = .5
        pars['fixpropdx'].t = 2100
        pars['fixpropcare'].t = 2100
        pars['fixproptx'].t = 2100
        pars['fixpropsupp'].t = 2100
        pars['fixproppmtct'].t = 2100
        pars['transnorm'].y = 0.85
        pars['mtctbreast'].y *= .5
        
        P.addparset(name='Treatment fixed',parset=parset)
    
        parset = dcp(defaultps)
        parset.name = 'Status quo'
        pars = parset.pars
        pars['initprev'].y[:] = [0.7, 0.14, 0.28, 0.03, 0.03,
                                 0.022, 0.078, 0.046, 0.175, 0.18,
                                 0.245, 0.078, 0.13]
        pars['force'].y[:] = odict([('FSW', 3.59),
                                    ('Clients', 0.80),
                                    ('MSM', 0.19),
                                    ('Males 0-9', 0.),
                                    ('Females 0-9', 0.),
                                    ('Males 10-19', 0.95),
                                    ('Females 10-19', 1.09),
                                    ('Males 20-24', 0.76),
                                    ('Females 20-24', 1.81),
                                    ('Males 25-49', 2.),
                                    ('Females 25-49', 1.1),
                                    ('Males 50+', 1.18),
                                    ('Females 50+', 1.10)])
        pars['hivtest'].m = .5
        pars['fixpropcare'].t = 2015
        pars['fixproptx'].t = 2015
        pars['fixpropsupp'].t = 2015
        pars['fixproppmtct'].t = 2015
        pars['transnorm'].y = 0.85
        pars['mtctbreast'].y *= .5
        
        P.addparset(name='Status quo',parset=parset)

        ### Add programs
        P.rmprogset(0)
        
        p0 = Program(short='VMMC',name='Voluntary medical male circumcision',targetpars=[{'param': 'numcirc', 'pop': 'Clients'}, {'param': 'numcirc', 'pop': 'MSM'}, {'param': 'numcirc', 'pop': 'Males 0-9'}, {'param': 'numcirc', 'pop': 'Males 10-19'}, {'param': 'numcirc', 'pop': 'Males 20-24'}, {'param': 'numcirc', 'pop': 'Males 25-49'}, {'param': 'numcirc', 'pop': 'Males 50+'}],targetpops=['Clients', 'MSM', 'Males 0-9', 'Males 10-19', 'Males 20-24', 'Males 25-49', 'Males 50+'])
        p0.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(86.25, 86.25)]), ])
        p0.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 0.0, 0.0, nan, nan, nan, 2590232.3247760157, 3241399.741655164, 3650750.2589196907, 25398000.0, 17168666.25, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, 304.0, 2454.0, 16923.0, 63604.0, 84604.0, 173992.0, 294466.0, 199057.0, nan, nan, nan, nan, nan, nan]), ])
    
        p1 = Program(short='FSW programs',name='Programs for female sex workers and clients',targetpars=[{'param': u'condcom', 'pop': (u'Clients', u'FSW')}, {'param': u'hivtest', 'pop': u'FSW'}, {'pop': (u'MSM', u'FSW'), 'param': u'condcom'}],targetpops=[u'FSW'])
        p1.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(35.5, 35.5)]), ])
        p1.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 1028950.0, 5372.0, nan, nan, nan, nan, nan, 0.0, 340000.0, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p2 = Program(short='MSM programs',name='Programs for men who have sex with men',targetpars=[{'param': u'condcas', 'pop': (u'MSM', u'MSM')}, {'param': u'hivtest', 'pop': u'MSM'}],targetpops=[u'MSM'])
        p2.costcovfn.ccopars = odict([('saturation', [(0.9, 0.9)]), ('t', [2016.0]), ('unitcost', [(45.95, 45.95)]), ])
        p2.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 0.0, 30000.0, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p3 = Program(short='HTC',name='HIV testing and counseling',targetpars=[{'param': u'hivtest', 'pop': u'Clients'}, {'param': u'hivtest', 'pop': u'Males 10-19'}, {'param': u'hivtest', 'pop': u'Females 10-19'}, {'param': u'hivtest', 'pop': u'Males 20-24'}, {'param': u'hivtest', 'pop': u'Females 20-24'}, {'param': u'hivtest', 'pop': u'Males 25-49'}, {'param': u'hivtest', 'pop': u'Females 25-49'}, {'param': u'hivtest', 'pop': u'Males 50+'}, {'param': u'hivtest', 'pop': u'Females 50+'}],targetpops=[u'Clients', u'Males 10-19', u'Females 10-19', u'Males 20-24', u'Females 20-24', u'Males 25-49', u'Females 25-49', u'Males 50+', u'Females 50+'])
        p3.costcovfn.ccopars = odict([('saturation', [(1.0, 1.0)]), ('t', [2016.0]), ('unitcost', [(8.67, 8.67)]), ])
        p3.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 3563387.0, 8298787.0, nan, nan, nan, 17450949.635453127, 15213442.58553639, 11015092.261536067, 17919000.0, 21269608.14, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, 63330.0, 195396.0, 234430.0, 336672.0, 511299.0, 1050137.0, 1327995.0, 1772043.0, 2138961.0, 2066216.0, 2453242.0, nan, nan, nan, nan, nan, nan]), ])
    
        p4 = Program(short='PMTCT',name='Prevention of mother-to-child transmission',targetpars=[{'param': u'numtx', 'pop': u'tot'}, {'param': u'numpmtct', 'pop': u'tot'}],targetpops=[u'tot'])
        p4.costcovfn.ccopars = odict([('saturation', [(1.0, 1.0)]), ('t', [2016.0]), ('unitcost', [(301.0, 301.0)]), ])
        p4.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 1162684.0, 17863894.0, nan, nan, nan, 12539141.068389883, 8846436.504648793, 10663078.844306767, 22317000.0, 20714820.0, 22630000.0, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, 6400.0, 18600.0, 25600.0, 35305.0, 40836.0, 58682.0, 76893.0, 82081.0, 84351.0, 74142.0, 68820.0, nan, nan, nan, nan, nan, nan]), ])
    
        p5 = Program(short='OVC',name='Orphans and vulnerable children',targetpars=[],targetpops=[])
        p5.costcovfn.ccopars = odict([])
        p5.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 4433886.0, 6040345.0, nan, nan, nan, 11800260.54603664, 10233132.823392816, 8695207.698483314, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p6 = Program(short='Other care',name='Other HIV care',targetpars=[],targetpops=[])
        p6.costcovfn.ccopars = odict([])
        p6.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 24898419.0, 70617361.0, nan, nan, nan, 99693899.17715785, 87842794.6223358, 89907327.7943011, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p7 = Program(short='MGMT',name='Management',targetpars=[],targetpops=[])
        p7.costcovfn.ccopars = odict([])
        p7.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 13327501.0, 14467461.0, nan, nan, nan, 59219639.49420474, 87783725.50017174, 98564359.87811732, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p8 = Program(short='HR',name='HR and training',targetpars=[],targetpops=[])
        p8.costcovfn.ccopars = odict([])
        p8.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 2283938.0, 2416843.0, nan, nan, nan, 4265531.61462586, 5696043.230539952, 6441875.143323964, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p9 = Program(short='ENV',name='Enabling environment',targetpars=[],targetpops=[])
        p9.costcovfn.ccopars = odict([])
        p9.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 2439883.0, 3664957.0, nan, nan, nan, 2869537.098369673, 15705860.930693801, 17856747.89784737, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p10 = Program(short='SP',name='Social protection',targetpars=[],targetpops=[])
        p10.costcovfn.ccopars = odict([])
        p10.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 20656371.0, 603704.0, nan, nan, nan, 806636.7712303394, 1456557.1223228585, 718961.7919982905, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p11 = Program(short='INFR',name='Health infrastructure',targetpars=[],targetpops=[])
        p11.costcovfn.ccopars = odict([])
        p11.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 0.0, 0.0, nan, nan, nan, 22471223.73384437, 2535305.8997030724, 3212318.1191333667, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p12 = Program(short='Condoms & SBCC',name='Condoms & SBCC',targetpars=[{'param': u'condcas', 'pop': (u'Males 10-19', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 50+', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Clients', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 50+')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Clients', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 50+', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 50+', u'Females 50+')}],targetpops=[u'Males 10-19', u'Males 25-49', u'Females 25-49', u'Females 10-19', u'Females 20-24', u'Males 20-24', u'Females 50+', u'Males 50+', u'Clients'])
        p12.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(4.5, 4.5)]), ])
        p12.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 20402012.0, 16159558.0, nan, nan, nan, 2899762.5797366896, 1267895.0977615763, 1504986, 27619000.0, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, 5240657.8067303784, 4717565.5467255022, nan, nan, nan, 631092.12248356279, 8146.7011712820877, 334441, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p13 = Program(short='M&E',name='M&E',targetpars=[],targetpops=[])
        p13.costcovfn.ccopars = odict([])
        p13.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 7296803.0, 16914297.0, nan, nan, nan, 15304548.92429977, 4083357.282855776, 5006095.810002067, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p14 = Program(short='Other Prevention',name='Other Prevention',targetpars=[],targetpops=[])
        p14.costcovfn.ccopars = odict([])
        p14.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 13187445.0, 11833823.0, nan, nan, nan, 52738704.14457255, 39361066.05302588, 42227024.62896632, nan, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p15 = Program(short='ART',name='Antiretroviral therapy',targetpars=[{'param': u'numtx', 'pop': u'tot'}],targetpops=[u'tot'])
        p15.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(270.0, 300.0)]), ])
        p15.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 25885685.0, 39021643.0, nan, nan, nan, 56453775.04472395, 72132041.93644492, 69209158.39479679, 148597000.0, 171792896.0, 177500000., nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, 57164.0, 81030.0, 149199.0, 219576.0, 283863.0, 344407.0, 415685.0, 480925.0, 580118.0, 671066.0, nan, nan, nan, nan, nan, nan]), ])
    
        R = Programset(programs=[p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,])
        R.covout['numcirc']['Clients'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['MSM'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 0-9'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 10-19'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 20-24'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 25-49'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 50+'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
    
        R.covout['condcom'][(u'Clients', u'FSW')].ccopars = odict([('intercept', [(0.6, 0.65)]), ('t', [2016]), (u'FSW programs', [(0.92, 0.97)]), ])
        R.covout['condcom'][(u'MSM', u'FSW')].ccopars = odict([('intercept', [array([ 0.25,  0.35])]), ('t', [2016.0]), (u'FSW programs', [ 0.8,  0.9]), ])
        R.covout['numtx']['tot'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'PMTCT', []), (u'ART', []), ])
        R.covout['numpmtct']['tot'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'PMTCT', []), ])
    
        R.covout['condcas'][(u'MSM', u'MSM')].ccopars = odict([('intercept', [(0.2, 0.25)]), ('t', [2016]), (u'MSM programs', [(0.9, 0.99)]), ])
        R.covout['condcas'][(u'Males 10-19', u'Females 20-24')].ccopars = odict([('intercept', [(0.1, 0.15)]), ('t', [2016]), (u'Condoms & SBCC', [(0.35, 0.45)]), ])
        R.covout['condcas'][(u'Males 10-19', u'Females 25-49')].ccopars = odict([('intercept', [(0.1, 0.15)]), ('t', [2016]), (u'Condoms & SBCC', [(0.35, 0.45)]), ])
        R.covout['condcas'][(u'Males 10-19', u'Females 10-19')].ccopars = odict([('intercept', [(0.1, 0.15)]), ('t', [2016]), (u'Condoms & SBCC', [(0.35, 0.4)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 10-19')].ccopars = odict([('intercept', [(0.15, 0.2)]), ('t', [2016]), (u'Condoms & SBCC', [(0.4, 0.5)]), ])
        R.covout['condcas'][(u'Males 20-24', u'Females 10-19')].ccopars = odict([('intercept', [(0.15, 0.2)]), ('t', [2016]), (u'Condoms & SBCC', [(0.4, 0.45)]), ])
        R.covout['condcas'][(u'Males 20-24', u'Females 25-49')].ccopars = odict([('intercept', [(0.05,  0.1)]), ('t', [2016.0]), (u'Condoms & SBCC', [( 0.4,  0.5)]), ])
        R.covout['condcas'][(u'Males 20-24', u'Females 20-24')].ccopars = odict([('intercept', [( 0.1,  0.15)]), ('t', [2016.0]), (u'Condoms & SBCC', [( 0.41,  0.5)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 20-24')].ccopars = odict([('intercept', [(0.1, 0.5)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.55)]), ])
        R.covout['condcas'][(u'Males 50+', u'Females 20-24')].ccopars = odict([('intercept', [( 0.25,  0.35)]), ('t', [2016.0]), (u'Condoms & SBCC', [(0.5,  0.56)]), ])
        R.covout['condcas'][(u'Clients', u'Females 20-24')].ccopars = odict([('intercept', [(0.2, 0.3)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.5)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 25-49')].ccopars = odict([('intercept', [(0.05, 0.1)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.5)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 50+')].ccopars = odict([('intercept', [( 0.23,  0.29)]), ('t', [2016.0]), (u'Condoms & SBCC', [( 0.6,  0.65)]), ])
        R.covout['condcas'][(u'Clients', u'Females 25-49',)].ccopars = odict([('intercept', [(0.15, 0.2)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.5)]), ])
        R.covout['condcas'][(u'Males 50+', u'Females 25-49')].ccopars = odict([('intercept', [( 0.2,  0.25)]), ('t', [2016.0]), (u'Condoms & SBCC', [(0.5,  0.6)]), ])
        R.covout['condcas'][(u'Males 50+', u'Females 50+')].ccopars = odict([('intercept', [(0.1725, 0.1725)]), ('t', [2016]), (u'Condoms & SBCC', [(0.52, 0.58)]), ])
    
        R.covout['hivtest']['FSW'].ccopars = odict([('intercept', [(0.05,  0.15)]), ('t', [2016.0]), (u'FSW programs', [(0.9,  0.99)]), ])
        R.covout['hivtest']['MSM'].ccopars = odict([('intercept', [(0.01,  0.03)]), ('t', [2016.0]), (u'MSM programs', [(0.55,  0.6)]), ])
        R.covout['hivtest']['Clients'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.2, 0.25)]), ])
        R.covout['hivtest']['Males 10-19'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.15, 0.25)]), ])
        R.covout['hivtest']['Females 10-19'].ccopars = odict([('intercept', [(0.01,  0.05)]), ('t', [2016.0]), (u'HTC', [(0.45,  0.55)]), ])
        R.covout['hivtest']['Males 20-24'].ccopars = odict([('intercept', [(0.01,  0.05)]), ('t', [2016.0]), (u'HTC', [(0.15,  0.25)]), ])
        R.covout['hivtest']['Females 20-24'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.45, 0.55)]), ])
        R.covout['hivtest']['Males 25-49'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.2, 0.35)]), ])
        R.covout['hivtest']['Females 25-49'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.45, 0.55)]), ])
        R.covout['hivtest']['Males 50+'].ccopars = odict([('intercept', [( 0.01,  0.05)]), ('t', [2016.0]), (u'HTC', [(0.25,  0.3)]), ])
        R.covout['hivtest']['Females 50+'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.45, 0.55)]), ])
    
        P.addprogset(name='Default',progset=R)
    
        p0 = Program(short='VMMC',name='Voluntary medical male circumcision',targetpars=[{'pop': 'Clients', 'param': 'numcirc'}, {'pop': 'MSM', 'param': 'numcirc'}, {'pop': 'Males 0-9', 'param': 'numcirc'}, {'pop': 'Males 10-19', 'param': 'numcirc'}, {'pop': 'Males 20-24', 'param': 'numcirc'}, {'pop': 'Males 25-49', 'param': 'numcirc'}, {'pop': 'Males 50+', 'param': 'numcirc'}],targetpops=['Clients', 'MSM', 'Males 0-9', 'Males 10-19', 'Males 20-24', 'Males 25-49', 'Males 50+'])
        p0.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(86.25, 86.25)]), ])
        p0.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 0.0, 0.0, nan, nan, nan, 2590232.3247760157, 3241399.741655164, 3650750.2589196907, 25398000.0, 17168666.25, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, 304.0, 2454.0, 16923.0, 63604.0, 84604.0, 173992.0, 294466.0, 199057.0, nan, nan, nan, nan, nan, nan]), ])
    
        p1 = Program(short='FSW programs',name='Programs for female sex workers and clients',targetpars=[{'pop': (u'Clients', u'FSW'), 'param': u'condcom'}, {'pop': u'FSW', 'param': u'hivtest'}, {'param': u'condcom', 'pop': (u'MSM', u'FSW')}],targetpops=[u'FSW'])
        p1.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(35.5, 35.5)]), ])
        p1.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 1028950.0, 5372.0, nan, nan, nan, nan, nan, 0.0, 340000.0, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p2 = Program(short='MSM programs',name='Programs for men who have sex with men',targetpars=[{'pop': (u'MSM', u'MSM'), 'param': u'condcas'}, {'pop': u'MSM', 'param': u'hivtest'}],targetpops=[u'MSM'])
        p2.costcovfn.ccopars = odict([('saturation', [(0.9, 0.9)]), ('t', [2016.0]), ('unitcost', [(45.95, 45.95)]), ])
        p2.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 0.0, 30000.0, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        p3 = Program(short='HTC',name='HIV testing and counseling',targetpars=[{'pop': u'Clients', 'param': u'hivtest'}, {'pop': u'Males 10-19', 'param': u'hivtest'}, {'pop': u'Females 10-19', 'param': u'hivtest'}, {'pop': u'Males 20-24', 'param': u'hivtest'}, {'pop': u'Females 20-24', 'param': u'hivtest'}, {'pop': u'Males 25-49', 'param': u'hivtest'}, {'pop': u'Females 25-49', 'param': u'hivtest'}, {'pop': u'Males 50+', 'param': u'hivtest'}, {'pop': u'Females 50+', 'param': u'hivtest'}],targetpops=[u'Clients', u'Males 10-19', u'Females 10-19', u'Males 20-24', u'Females 20-24', u'Males 25-49', u'Females 25-49', u'Males 50+', u'Females 50+'])
        p3.costcovfn.ccopars = odict([('saturation', [(1.0, 1.0)]), ('t', [2016.0]), ('unitcost', [(8.67, 8.67)]), ])
        p3.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 3563387.0, 8298787.0, nan, nan, nan, 17450949.635453127, 15213442.58553639, 11015092.261536067, 17919000.0, 21269608.14, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, 63330.0, 195396.0, 234430.0, 336672.0, 511299.0, 1050137.0, 1327995.0, 1772043.0, 2138961.0, 2066216.0, 2453242.0, nan, nan, nan, nan, nan, nan]), ])
    
        p4 = Program(short='Condoms & SBCC',name='Condoms & SBCC',targetpars=[{'param': u'condcas', 'pop': (u'Males 10-19', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 50+', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Clients', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 20-24')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 10-19')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 50+')}, {'param': u'condcas', 'pop': (u'Males 20-24', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Clients', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 25-49', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 10-19', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 50+', u'Females 25-49')}, {'param': u'condcas', 'pop': (u'Males 50+', u'Females 50+')}],targetpops=[u'Males 10-19', u'Males 25-49', u'Females 25-49', u'Females 10-19', u'Females 20-24', u'Males 20-24', u'Females 50+', u'Males 50+', u'Clients'])
        p4.costcovfn.ccopars = odict([('saturation', [(0.85, 0.95)]), ('t', [2016.0]), ('unitcost', [(4.5, 4.5)]), ])
        p4.costcovdata = odict([('cost', [nan, nan, nan, nan, nan, 20402012.0, 16159558.0, nan, nan, nan, 2899762.5797366896, 1267895.0977615763, 1504986, 27619000.0, nan, nan, nan, nan, nan, nan, nan]), ('t', [2000.0, 2001.0, 2002.0, 2003.0, 2004.0, 2005.0, 2006.0, 2007.0, 2008.0, 2009.0, 2010.0, 2011.0, 2012.0, 2013.0, 2014.0, 2015.0, 2016.0, 2017.0, 2018.0, 2019.0, 2020.0]), ('coverage', [nan, nan, nan, nan, nan, 5240657.8067303784, 4717565.5467255022, nan, nan, nan, 631092.12248356279, 8146.7011712820877, 334441, nan, nan, nan, nan, nan, nan, nan, nan]), ])
    
        R = Programset(programs=[p0,p1,p2,p3,p4,])
        R.covout['numcirc']['Clients'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['MSM'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 0-9'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 10-19'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 20-24'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 25-49'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
        R.covout['numcirc']['Males 50+'].ccopars = odict([('intercept', [(0.0, 0.0)]), ('t', [2016]), (u'VMMC', []), ])
    
        R.covout['condcom'][(u'Clients', u'FSW')].ccopars = odict([('intercept', [(0.6, 0.65)]), ('t', [2016]), (u'FSW programs', [(0.92, 0.97)]), ])
        R.covout['condcom'][(u'MSM', u'FSW')].ccopars = odict([('intercept', [array([ 0.25,  0.35])]), ('t', [2016.0]), (u'FSW programs', [ 0.8,  0.9]), ])
    
        R.covout['condcas'][(u'MSM', u'MSM')].ccopars = odict([('intercept', [(0.2, 0.25)]), ('t', [2016]), (u'MSM programs', [(0.9, 0.99)]), ])
        R.covout['condcas'][(u'Males 10-19', u'Females 20-24')].ccopars = odict([('intercept', [(0.1, 0.15)]), ('t', [2016]), (u'Condoms & SBCC', [(0.35, 0.45)]), ])
        R.covout['condcas'][(u'Males 10-19', u'Females 25-49')].ccopars = odict([('intercept', [(0.1, 0.15)]), ('t', [2016]), (u'Condoms & SBCC', [(0.35, 0.45)]), ])
        R.covout['condcas'][(u'Males 10-19', u'Females 10-19')].ccopars = odict([('intercept', [(0.1, 0.15)]), ('t', [2016]), (u'Condoms & SBCC', [(0.35, 0.4)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 10-19')].ccopars = odict([('intercept', [(0.15, 0.2)]), ('t', [2016]), (u'Condoms & SBCC', [(0.4, 0.5)]), ])
        R.covout['condcas'][(u'Males 20-24', u'Females 10-19')].ccopars = odict([('intercept', [(0.15, 0.2)]), ('t', [2016]), (u'Condoms & SBCC', [(0.4, 0.45)]), ])
        R.covout['condcas'][(u'Males 20-24', u'Females 25-49')].ccopars = odict([('intercept', [(0.05,  0.1)]), ('t', [2016.0]), (u'Condoms & SBCC', [( 0.4,  0.5)]), ])
        R.covout['condcas'][(u'Males 20-24', u'Females 20-24')].ccopars = odict([('intercept', [( 0.1,  0.15)]), ('t', [2016.0]), (u'Condoms & SBCC', [( 0.41,  0.5)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 20-24')].ccopars = odict([('intercept', [(0.1, 0.5)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.55)]), ])
        R.covout['condcas'][(u'Males 50+', u'Females 20-24')].ccopars = odict([('intercept', [( 0.25,  0.35)]), ('t', [2016.0]), (u'Condoms & SBCC', [(0.5,  0.56)]), ])
        R.covout['condcas'][(u'Clients', u'Females 20-24')].ccopars = odict([('intercept', [(0.2, 0.3)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.5)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 25-49')].ccopars = odict([('intercept', [(0.05, 0.1)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.5)]), ])
        R.covout['condcas'][(u'Males 25-49', u'Females 50+')].ccopars = odict([('intercept', [( 0.23,  0.29)]), ('t', [2016.0]), (u'Condoms & SBCC', [( 0.6,  0.65)]), ])
        R.covout['condcas'][(u'Clients', u'Females 25-49',)].ccopars = odict([('intercept', [(0.15, 0.2)]), ('t', [2016]), (u'Condoms & SBCC', [(0.45, 0.5)]), ])
        R.covout['condcas'][(u'Males 50+', u'Females 25-49')].ccopars = odict([('intercept', [( 0.2,  0.25)]), ('t', [2016.0]), (u'Condoms & SBCC', [(0.5,  0.6)]), ])
        R.covout['condcas'][(u'Males 50+', u'Females 50+')].ccopars = odict([('intercept', [(0.1725, 0.1725)]), ('t', [2016]), (u'Condoms & SBCC', [(0.52, 0.58)]), ])
    
        R.covout['hivtest']['FSW'].ccopars = odict([('intercept', [(0.05,  0.15)]), ('t', [2016.0]), (u'FSW programs', [(0.9,  0.99)]), ])
        R.covout['hivtest']['MSM'].ccopars = odict([('intercept', [(0.01,  0.03)]), ('t', [2016.0]), (u'MSM programs', [(0.55,  0.6)]), ])
        R.covout['hivtest']['Clients'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.2, 0.25)]), ])
        R.covout['hivtest']['Males 10-19'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.15, 0.25)]), ])
        R.covout['hivtest']['Females 10-19'].ccopars = odict([('intercept', [(0.01,  0.05)]), ('t', [2016.0]), (u'HTC', [(0.45,  0.55)]), ])
        R.covout['hivtest']['Males 20-24'].ccopars = odict([('intercept', [(0.01,  0.05)]), ('t', [2016.0]), (u'HTC', [(0.15,  0.25)]), ])
        R.covout['hivtest']['Females 20-24'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.45, 0.55)]), ])
        R.covout['hivtest']['Males 25-49'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.2, 0.35)]), ])
        R.covout['hivtest']['Females 25-49'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.45, 0.55)]), ])
        R.covout['hivtest']['Males 50+'].ccopars = odict([('intercept', [( 0.01,  0.05)]), ('t', [2016.0]), (u'HTC', [(0.25,  0.3)]), ])
        R.covout['hivtest']['Females 50+'].ccopars = odict([('intercept', [(0.01, 0.05)]), ('t', [2016]), (u'HTC', [(0.45, 0.55)]), ])
    
        P.addprogset(name='Without treatment',progset=R)
    
    
    else:
        raise OptimaException('Default project type "%s" not understood: choices are "simple", "generalized", or "concentrated"' % which)
    
    
    return P



def demo(doplot=True, **kwargs):
    ''' Do a simple demo of Optima -- similar to simple.py '''
    P = defaultproject(**kwargs)
    if doplot: 
        try:    import optima as op # Only used for demo.py, don't worry if can't be imported
        except: print('pygui could not be imported: unable to plot')
        op.pygui(P)
    return P
