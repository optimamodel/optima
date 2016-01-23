"""
Defines the default parameters for each program.

Version: 2016jan23 by cliffk
"""
from optima import Program, Programset

def defaultprograms(P, addpars=False, addcostcov=False, filterprograms=None):
    ''' Make some default programs'''
    
    # Shorten variable names
    pops = P.data['pops']['short']
    malepops = [P.data['pops']['short'][pop] for pop in range(P.data['npops']) if P.data['pops']['male'][pop]]
    femalepops = [P.data['pops']['short'][pop] for pop in range(P.data['npops']) if P.data['pops']['female'][pop]]
    caspships = P.data['pships']['cas']
    compships = P.data['pships']['com']
#    regpships = P.data['pships']['reg']
#    injpships = P.data['pships']['inj']
    
    # Set up default programs
    Condoms = Program(short='Condoms',
                  project=P,
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  category='Prevention',
                  name='Condom promotion and distribution',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    SBCC = Program(short='SBCC',
                  project=P,
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  category='Prevention',
                  name='Social and behavior change communication',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    STI = Program(short='STI',
                  project=P,
                  targetpars=[{'param': 'stiprev', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  category='Prevention',
                  name='Diagnosis and treatment of sexually transmissible infections',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    VMMC = Program(short='VMMC',
                  project=P,
                  targetpars=[{'param': 'circum', 'pop': malepop} for malepop in malepops],
                  targetpops=malepops,
                  category='Prevention',
                  name='Voluntary medical male circumcision',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})              
                  
    FSW_programs = Program(short='FSW_programs',
                  project=P,
                  targetpars=[{'param': 'condcom', 'pop': compship} for compship in [x for x in compships if 'FSW' in x]] + [{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'FSW' in x]] + [{'param': 'hivtest', 'pop': 'FSW'}],
                  targetpops=['FSW'],
                  category='Prevention',
                  name='Programs for female sex workers and clients',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                 
    MSM_programs = Program(short='MSM_programs',
                  project=P,
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'MSM' in x]] + [{'param': 'hivtest', 'pop': 'MSM'}],
                  targetpops=['MSM'],
                  category='Prevention',
                  name='Programs for men who have sex with men',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PWID_programs = Program(short='PWID_programs',
                  project=P,
                  targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'PWID' in x]] + [{'param': 'hivtest', 'pop': 'PWID'}] + [{'param': 'sharing', 'pop': 'PWID'}],
                  targetpops=['PWID'],
                  category='Prevention',
                  name='Programs for people who inject drugs',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    OST = Program(short='OST',
                  project=P,
                  targetpars=[{'param': 'numost', 'pop': 'PWID'}],
                  targetpops=['PWID'],
                  category='Prevention',
                  name='Opiate substitution therapy',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    NSP = Program(short='NSP',
                  project=P,
                  targetpars=[{'param': 'sharing', 'pop': 'PWID'}],
                  targetpops=['PWID'],
                  category='Prevention',
                  name='Needle-syringe programs',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    Cash_transfers = Program(short='Cash_transfers',
                  project=P,
                  targetpars=[{'param': 'actscas', 'pop': caspship} for caspship in caspships],
                  targetpops=pops,
                  category='Prevention',
                  name='Cash transfers for HIV risk reduction',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    PrEP = Program(short='PrEP',
                  project=P,
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
                  project=P,
                  targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  category='Care and treatment',
                  name='HIV testing and counseling',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    ART = Program(short='ART',
                  project=P,
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}],# for pop in pops],
                  targetpops=['tot'],
                  category='Care and treatment',
                  name='Antiretroviral therapy',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200', 'gt350'], 'pregnant': False})
    
    PMTCT = Program(short='PMTCT',
                  project=P,
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}, {'param': 'numpmtct', 'pop': 'tot'}],
                  targetpops=['tot'],
                  category='Care and treatment',
                  name='Prevention of mother-to-child transmission',
                  criteria = {'hivstatus': 'allstates', 'pregnant': True})
                  
    OVC = Program(short='OVC',
                  project=P,
                  category='Care and treatment',
                  name='Orphans and vulnerable children',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    Other_care = Program(short='Other_care',
                  project=P,
                  category='Care and treatment',
                  name='Other HIV care',
                  criteria = {'hivstatus': ['lt50', 'gt50', 'gt200'], 'pregnant': False})
    
    MGMT = Program(short='MGMT',
                  project=P,
                  category='Management and administration',
                  name='Management')
    
    HR = Program(short='HR',
                  project=P,
                  category='Management and administration',
                  name='HR and training')
    
    ENV = Program(short='ENV',
                  project=P,
                  category='Management and administration',
                  name='Enabling environment')
    
    SP = Program(short='SP',
                  project=P,
                  category='Other',
                  name='Social protection')
    
    ME = Program(short='ME',
                  project=P,
                  category='Other',
                  name='Monitoring, evaluation, surveillance, and research')
    
    INFR = Program(short='INFR',
                  project=P,
                  category='Other',
                  name='Health infrastructure')
    
    Other = Program(short='Other',
                  project=P,
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
                                 
        VMMC.costcovfn.addccopar({'saturation': (0.3,0.3),
                                 't': 2016.0,
                                 'unitcost': (50,80)})
                                 
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
