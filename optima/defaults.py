"""
Defines the default parameters for each program.

Version: 2016jan28
"""
import os
from numpy import array
from optima import OptimaException, Project, Program, Programset, printv
try: from optima import pygui # Only used for demo.py, don't worry if can't be imported
except: pass



def defaultprograms(project, addcostcovpars=False, addcostcovdata=False, filterprograms=None):
    ''' Make some default programs'''
    
    # Shorten variable names
    pops = project.pars()['popkeys']
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
                  )
    
    SBCC = Program(short='SBCC',
                  name='Social and behavior change communication',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  )
                  
    STI = Program(short='STI',
                  name='Diagnosis and treatment of sexually transmissible infections',
                  category='Prevention',
                  targetpars=[{'param': 'stiprev', 'pop': pop} for pop in pops],
                  )
    
    VMMC = Program(short='VMMC',
                  name='Voluntary medical male circumcision',
                  category='Prevention',
                  targetpars=[{'param': 'numcirc', 'pop': male} for male in malelist],
                  targetpops=malelist)              
                  
    FSW = Program(short='FSW programs',
                  name='Programs for female sex workers and clients',
                  category='Prevention',
                  targetpars=[{'param': 'condcom', 'pop': compship} for compship in fsw_compships] + [{'param': 'condcas', 'pop': caspship} for caspship in fsw_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in fswlist],
                  targetpops=fswlist)
                 
    MSM = Program(short='MSM programs',
                  name='Programs for men who have sex with men',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in msm_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in msmlist],
                  targetpops=msmlist)
                  
    PWID = Program(short='PWID programs',
                  name='Programs for people who inject drugs',
                  category='Prevention',
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in pwid_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in pwidlist] + [{'param': 'sharing', 'pop': pop} for pop in pwidlist],
                  targetpops=pwidlist)
                  
    OST = Program(short='OST',
                  name='Opiate substitution therapy',
                  category='Prevention',
                  targetpars='numost',
                  )
                  
    NSP = Program(short='NSP',
                  name='Needle-syringe programs',
                  category='Prevention',
                  targetpars=[{'param': 'sharing', 'pop': pop} for pop in pwidlist],
                  targetpops=pwidlist)
                  
    Cash = Program(short='Cash transfers',
                  name='Cash transfers for HIV risk reduction',
                  category='Prevention',
                  targetpars=[{'param': 'actscas', 'pop': caspship} for caspship in caspships],
                  )
                  
    PrEP = Program(short='PrEP',
                  name='Pre-exposure prophylaxis',
                  category='Prevention',
                  targetpars=[{'param': 'prep', 'pop':  pop} for pop in pops],
                  )
                  
    PEP = Program(short='PEP',
                  name='Post-exposure prophylaxis',
                  category='Care and treatment')
                  
    HTC = Program(short='HTC',
                  name='HIV testing and counseling',
                  category='Care and treatment',
                  targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                  )
    
    ART = Program(short='ART',
                  name='Antiretroviral therapy',
                  category='Care and treatment',
                  targetpars='numtx',
                  )
    
    Lab = Program(short='Lab',
                  name='Lab monitoring',
                  category='Care and treatment',
                  targetpars='numvlmon',
                  )
    
    Adherence = Program(short='Adherence',
                  name='Adherence support',
                  category='Care and treatment',
                  targetpars=[{'param': 'leavecare', 'pop': pop} for pop in pops],
                  )
    
    Tracing = Program(short='Tracing',
                  name='Pre-ART tracing',
                  category='Care and treatment',
                  targetpars=[{'param': 'linktocare', 'pop': pop} for pop in pops],
                  )
    
    PMTCT = Program(short='PMTCT',
                  name='Prevention of mother-to-child transmission',
                  category='Care and treatment',
                  targetpars=['numtx', 'numpmtct'],
                  )
                  
    OVC = Program(short='OVC',
                  name='Orphans and vulnerable children',
                  category='Care and treatment')
    
    Other_care = Program(short='Other care',
                  name='Other HIV care',
                  category='Care and treatment')
    
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
        year = 2016.
        Condoms.update(  saturation=0.74,        year=year, unitcost=(3,7))
        SBCC.update(     saturation=0.6,         year=year, unitcost=(8,12))
        STI.update(      saturation=0.6,         year=year, unitcost=(15,20))
        VMMC.update(     saturation=(.5,.6),     year=year, unitcost=(15,25))
        FSW.update(      saturation=0.9,         year=year, unitcost=(25,35))
        MSM.update(      saturation=0.9,         year=year, unitcost=(25,35))
        PWID.update(     saturation=0.3,         year=year, unitcost=(25,35))
        OST.update(      saturation=0.3,         year=year, unitcost=(100,200))
        NSP.update(      saturation=0.3,         year=year, unitcost=(10,20))
        Cash.update(     saturation=0.3,         year=year, unitcost=(50,80))
        PrEP.update(     saturation=0.3,         year=year, unitcost=(100,200))
        HTC.update(      saturation=(0.85,0.95), year=year, unitcost=(5,10))
        ART.update(      saturation=0.99,        year=year, unitcost=(400,800))
        Lab.update(      saturation=0.99,        year=year, unitcost=(40,80))
        Adherence.update(saturation=0.99,        year=year, unitcost=(20,50))
        Tracing.update(  saturation=0.99,        year=year, unitcost=(20,50))
        PMTCT.update(    saturation=0.9,         year=year, unitcost=(100,200))
                                 
    if addcostcovdata:
        datayear = 2014
        Condoms.update(  datayear=datayear, spend=1e7, coverage=3e5)
        SBCC.update(     datayear=datayear, spend=1e7, coverage=3e5)
        STI.update(      datayear=datayear, spend=1e7, coverage=3e5)
        VMMC.update(     datayear=datayear, spend=1e7, coverage=3e5)
        FSW.update(      datayear=datayear, spend=8e6, coverage=240000)
        MSM.update(      datayear=datayear, spend=8e6, coverage=240000)
        PWID.update(     datayear=datayear, spend=2e6, coverage=25000)
        OST.update(      datayear=datayear, spend=2e6, coverage=25000)
        NSP.update(      datayear=datayear, spend=2e6, coverage=25000)
        Cash.update(     datayear=datayear, spend=2e6, coverage=25000)
        PrEP.update(     datayear=datayear, spend=2e6, coverage=25000)
        HTC.update(      datayear=datayear, spend=2e7, coverage=1.3e6)
        ART.update(      datayear=datayear, spend=1e6, coverage=3308)
        Lab.update(      datayear=datayear, spend=1e5, coverage=2000)
        Adherence.update(datayear=datayear, spend=1e5, coverage=2000)
        Tracing.update(  datayear=datayear, spend=2e1, coverage=2000)
        PMTCT.update(    datayear=datayear, spend=4e6, coverage=5500)

        OVC.update(       datayear=datayear, basespend=1e7)
        MGMT.update(      datayear=datayear, basespend=1e7)
        HR.update(        datayear=datayear, basespend=5e5)
        ENV.update(       datayear=datayear, basespend=1e7)
        SP.update(        datayear=datayear, basespend=1e7)
        ME.update(        datayear=datayear, basespend=1e7)
        INFR.update(      datayear=datayear, basespend=1e7)
        Other_care.update(datayear=datayear, basespend=1e7)
        Other.update(     datayear=datayear, basespend=5e5)
        
    allprograms = [Condoms, SBCC, STI, VMMC, FSW, MSM, PWID, OST, NSP, Cash, PrEP, PEP, HTC, ART, Lab, Adherence, Tracing, PMTCT, OVC, Other_care, MGMT, HR, ENV, SP, ME, INFR, Other]

    if filterprograms: # Only select those programs in filterprograms
        finalprograms = [program for program in allprograms if program.short in filterprograms]
        return finalprograms
    
    return allprograms
    




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
        P.pars()['force'].y[:] = [3.5, 1.5, 1.5, 1.7, 3.0, 0.4]
        if dorun: P.runsim() # Run after calibration
    
        # Get a default progset 
        R = defaultprogset(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=['Condoms', 'FSW programs', 'HTC', 'ART', 'Lab', 'Adherence', 'Tracing', 'Other'])
        
        # Add program effects
        R.addcovout(par='condcas',    pop=('Clients', 'FSW'),  lowerlim=(0.20,0.25), upperlim=0.95, progs={'Condoms':(0.35,0.45), 'FSW programs':(0.75,0.85)})
        R.addcovout(par='condcas',    pop=('Clients','F 15+'), lowerlim=(0.25,0.30), upperlim=0.95, progs={'Condoms':(0.85,0.95)})
        R.addcovout(par='condcas',    pop=('M 15+', 'FSW'),    lowerlim=(0.30,0.35), upperlim=0.95, progs={'Condoms':(0.50,0.55), 'FSW programs':(0.59,0.65)})
        R.addcovout(par='condcas',    pop=('M 15+','F 15+'),   lowerlim=(0.30,0.35), upperlim=0.95, progs={'Condoms':(0.45,0.50)})
        R.addcovout(par='condcas',    pop=('PWID','F 15+'),    lowerlim=(0.15,0.20), upperlim=0.95, progs={'Condoms':(0.35,0.45)})
        R.addcovout(par='condcas',    pop=('MSM', 'MSM'),      lowerlim=(0.10,0.15), upperlim=0.95, progs={'Condoms':(0.55,0.65)})
        R.addcovout(par='condcom',    pop=('Clients', 'FSW'),  lowerlim=(0.30,0.35), upperlim=0.95, progs={'FSW programs':(0.9,0.95)})
        R.addcovout(par='hivtest',    pop='FSW',               lowerlim=(0.30,0.40), upperlim=0.95, progs={'HTC': (0.90,0.95), 'FSW programs':(0.90,0.95)})
        R.addcovout(par='hivtest',    pop='Clients',           lowerlim=(0.10,0.15), upperlim=0.95, progs={'HTC': (0.40,0.60)})
        R.addcovout(par='hivtest',    pop='M 15+',             lowerlim=(0.01,0.02), upperlim=0.95, progs={'HTC': (0.20,0.30)})
        R.addcovout(par='hivtest',    pop='F 15+',             lowerlim=(0.01,0.02), upperlim=0.95, progs={'HTC': (0.20,0.30)})
        R.addcovout(par='hivtest',    pop='PWID',              lowerlim=(0.10,0.15), upperlim=0.95, progs={'HTC': (0.80,0.90)})
        R.addcovout(par='hivtest',    pop='MSM',               lowerlim=(0.12,0.20), upperlim=0.95, progs={'HTC': (0.80,0.90)})
        R.addcovout(par='leavecare',  pop='FSW',               lowerlim=(0.30,0.40), upperlim=0.95, progs={'Adherence': (0.05,0.1)})
        R.addcovout(par='leavecare',  pop='Clients',           lowerlim=(0.30,0.40), upperlim=0.95, progs={'Adherence': (0.05,0.1)})
        R.addcovout(par='leavecare',  pop='M 15+',             lowerlim=(0.30,0.40), upperlim=0.95, progs={'Adherence': (0.05,0.1)})
        R.addcovout(par='leavecare',  pop='F 15+',             lowerlim=(0.30,0.40), upperlim=0.95, progs={'Adherence': (0.05,0.1)})
        R.addcovout(par='leavecare',  pop='PWID',              lowerlim=(0.50,0.60), upperlim=0.95, progs={'Adherence': (0.3,0.4)})
        R.addcovout(par='leavecare',  pop='MSM',               lowerlim=(0.30,0.40), upperlim=0.95, progs={'Adherence': (0.05,0.1)})
        R.addcovout(par='linktocare', pop='FSW',               lowerlim=(1.40,1.60), upperlim=0.95, progs={'Tracing': (0.1,0.3)})
        R.addcovout(par='linktocare', pop='Clients',           lowerlim=(1.40,1.60), upperlim=0.95, progs={'Tracing': (0.1,0.3)})
        R.addcovout(par='linktocare', pop='M 15+',             lowerlim=(1.40,1.60), upperlim=0.95, progs={'Tracing': (0.1,0.3)})
        R.addcovout(par='linktocare', pop='F 15+',             lowerlim=(1.40,1.60), upperlim=0.95, progs={'Tracing': (0.1,0.3)})
        R.addcovout(par='linktocare', pop='PWID',              lowerlim=(1.40,1.60), upperlim=0.95, progs={'Tracing': (0.1,0.3)})
        R.addcovout(par='linktocare', pop='MSM',               lowerlim=(1.40,1.60), upperlim=0.95, progs={'Tracing': (0.1,0.3)})
    
        # Store this program set in the project
        P.addprogset(R)
    
    
    
    
#    ##########################################################################################################################
#    ## Generalized
#    ##########################################################################################################################
#    elif which=='generalized':
#        printv('Creating generalized epidemic project...', 2, verbose)
#        P = Project(spreadsheet=spreadsheetpath+'generalized.xlsx', verbose=verbose, **kwargs)
#
#        # Get a default progset 
#        R = defaultprogset(P, addcostcovpars=addcostcovpars, addcostcovdata=addcostcovdata, filterprograms=['Condoms', 'FSW programs', 'MSM programs', 'ART', 'Lab', 'PMTCT', 'VMMC', 'MGMT', 'Other'])
#
#        pops = P.data['pops']['short']
#        adultlist = [pops[i] for i in range(len(pops)) if P.data['pops']['age'][i][0]>0]
#        
#        # Fix up costs
#        R.programs['ART'].update(saturation=(0.9,0.9),
#                         year=year,
#                         unitcost=(1000,2000)}, overwrite=True)
#                         
#        R.programs['PMTCT'].update(saturation=(0.9,0.9),
#                         year=year,
#                         unitcost=(5000,8000)}, overwrite=True)
#
#        # Add different modalities of testing
#        HTC_workplace = Program(short='HTC workplace',
#                      targetpars=[{'param': 'hivtest', 'pop': pop} for pop in ['M 15-49','F 15-49', 'M 50+', 'F 50+', 'Clients']],
#                      targetpops=['M 15-49','F 15-49', 'M 50+', 'F 50+', 'Clients'],
#                      category='Care and treatment',
#                      name='HIV testing and counseling - workplace programs',
#                      criteria = {'hivstatus': 'allstates', 'pregnant': False})
#        
#        HTC_mobile = Program(short='HTC mobile',
#                      targetpars=[{'param': 'hivtest', 'pop': pop} for pop in adultlist],
#                      targetpops=adultlist,
#                      category='Care and treatment',
#                      name='HIV testing and counseling - mobile clinics',
#                      criteria = {'hivstatus': 'allstates', 'pregnant': False})
#        
#        HTC_medical = Program(short='HTC medical',
#                      targetpars=[{'param': 'hivtest', 'pop': pop} for pop in adultlist],
#                      targetpops=adultlist,
#                      category='Care and treatment',
#                      name='HIV testing and counseling - medical facilities',
#                      criteria = {'hivstatus': 'allstates', 'pregnant': False})
#
#
#        HTC_workplace.update(saturation=(0.2,0.3),
#                                 year=year,
#                                 unitcost=(10,12)})
#        HTC_mobile.update(saturation=(0.5,0.6),
#                                 year=year,
#                                 unitcost=(6,10)})
#        HTC_medical.update(saturation=(0.4,0.6),
#                                 year=year,
#                                 unitcost=(4,8)})
#
#        HTC_workplace.update(spend=1e7,coverage=9e6})
#        HTC_mobile.update(spend=1e6,coverage=2e5})
#        HTC_medical.update(spend=1e6,coverage=4e5})
#        
#        R.addprograms(newprograms=[HTC_workplace, HTC_mobile, HTC_medical])
#
#        R.addcovout['condcas'][('Clients', 'FSW'), lowerlim= (0.3,0.35), year=year, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
#        R.addcovout['condcas'][('Clients','F 50+'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45)})
#        R.addcovout['condcas'][('Clients','F 15-49'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45)})
#        R.addcovout['condcas'][('M 15-49', 'FSW'), lowerlim= (0.3,0.35), year=year, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
#        R.addcovout['condcas'][('M 15-49','F 15-49'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45)})
#        R.addcovout['condcas'][('M 15-49','F 50+'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45)})
#        R.addcovout['condcas'][('M 50+', 'FSW'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45), 'FSW programs':(0.55,0.65)})
#        R.addcovout['condcas'][('M 50+', 'F 15-49'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45)})
#        R.addcovout['condcas'][('M 50+','F 50+'), lowerlim= (0.2,0.3), year=year, 'Condoms':(0.35,0.45)})
#        R.addcovout['condcas'][('MSM', 'MSM'), lowerlim= (0.5,0.55), year=year, 'Condoms':(0.55,0.65), 'MSM programs':(0.75,0.85)})
#
#        R.addcovout['condcom'][('Clients', 'FSW'), lowerlim= (0.6,0.65), year=year, 'FSW programs':(0.9,0.95)})
#    
#        R.addcovout['hivtest']['FSW', lowerlim= (0.35,0.45), 
#                                              year=year,
#                                              'HTC mobile': (0.85,0.9),
#                                              'HTC medical': (0.65,0.75),
#                                              'FSW programs':(0.95,0.99)})
#                                                
#        R.addcovout['hivtest']['MSM', lowerlim= (0.05,0.1),
#                                              year=year,
#                                              'HTC mobile': (0.85,0.9),
#                                              'HTC medical': (0.65,0.75),
#                                              'MSM programs':(0.95,0.99)})
#                                              
#        R.addcovout['hivtest']['Clients', lowerlim= (0.05,0.1),
#                                                  year=year,
#                                                  'HTC workplace': (0.85,0.9),
#                                                  'HTC mobile': (0.85,0.9),
#                                                  'HTC medical': (0.65,0.75)})
#                                                  
#        R.addcovout['hivtest']['M 15-49', lowerlim= (0.35,0.4),
#                                                  year=year,
#                                                  'HTC workplace': (0.85,0.9),
#                                                  'HTC mobile': (0.85,0.9),
#                                                  'HTC medical': (0.85,0.95)})
#
#        R.addcovout['hivtest']['F 15-49', lowerlim= (0.35,0.4),
#                                                  year=year, 
#                                                  'HTC workplace': (0.85,0.9),
#                                                  'HTC mobile': (0.85,0.9),
#                                                  'HTC medical': (0.85,0.95)})
#
#        R.addcovout['hivtest']['M 50+', lowerlim= (0.15,0.2), 
#                                                year=year,
#                                                  'HTC workplace': (0.85,0.9),
#                                                  'HTC mobile': (0.85,0.9),
#                                                  'HTC medical': (0.65,0.75)})
#
#        R.addcovout['hivtest']['F 50+', lowerlim= (0.15,0.2),
#                                                year=year,
#                                                  'HTC workplace': (0.85,0.9),
#                                                  'HTC mobile': (0.85,0.9),
#                                                  'HTC medical': (0.65,0.75)})
#
#        R.addcovout['numtx']['tot', lowerlim= (100.0,150.0), year=year})
#        R.addcovout['numpmtct']['tot', lowerlim= (100.0,150.0), year=year})
#        R.addcovout('numvlmon']['tot', lowerlim= (100.0,150.0), year=year})
#
#        R.addcovout['numcirc']['MSM', lowerlim= (0,0), year=year})
#        R.addcovout['numcirc']['Clients', lowerlim= (0,0), year=year})
#        R.addcovout['numcirc']['M 15-49', lowerlim= (0,0), year=year})
#        R.addcovout['numcirc']['M 50+', lowerlim= (0,0), year=year})
#        R.addcovout['numcirc']['M 0-14', lowerlim= (0,0), year=year})
#
#
#        P.addprogset(name='default', progset=R)
#        
#        
#        # Do a super-manual calibration
#        P.pars()['inhomo'].y[:] = 0.2
    
    
    
    else:
        raise OptimaException('Default project type "%s" not understood: choices are "simple", "generalized", or "concentrated"' % which)
    
    
    return P



def demo(doplot=True, **kwargs):
    ''' Do a simple demo of Optima -- similar to simple.py '''
    P = defaultproject(**kwargs)
    if doplot: pygui(P)
    return P
