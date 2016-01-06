"""
Defines the default parameters for each program.

Version: 2016jan05 by robynstuart
"""
from optima import Project, Program

# Load a project
P = Project(spreadsheet='test7pops.xlsx')

# Shorten variable names
pops = P.data['pops']['short']
malepops = [P.data['pops']['short'][pop] for pop in range(P.data['npops']) if P.data['pops']['male'][pop]]
femalepops = [P.data['pops']['short'][pop] for pop in range(P.data['npops']) if P.data['pops']['female'][pop]]
regpships = P.data['pships']['reg']
caspships = P.data['pships']['cas']
compships = P.data['pships']['com']
injpships = P.data['pships']['inj']

# Set up default programs
Condoms = Program(name='Condoms',
              targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
              targetpops=pops,
              category='Prevention',
              short_name='Condoms',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})

SBCC = Program(name='SBCC',
              targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
              targetpops=pops,
              category='Prevention',
              short_name='SBCC',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
STI = Program(name='STI',
              targetpars=[{'param': 'stiprev', 'pop': pop} for pop in pops],
              targetpops=pops,
              category='Prevention',
              short_name='STI',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})

VMMC = Program(name='VMMC',
              targetpars=[{'param': 'circum', 'pop': malepop} for malepop in malepops],
              targetpops=malepops,
              category='Prevention',
              short_name='VMMC',
              criteria = {'hivstatus': 'alluninf', 'pregnant': False})              
              
FSW_programs = Program(name='FSW_programs',
              targetpars=[{'param': 'condcom', 'pop': compship} for compship in [x for x in caspships if 'FSW' in x]] + [{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'FSW' in x]] + [{'param': 'hivtest', 'pop': 'FSW'}],
              targetpops=['FSW'],
              category='Prevention',
              short_name='FSW programs',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
             
MSM_programs = Program(name='MSM_programs',
              targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'MSM' in x]] + [{'param': 'hivtest', 'pop': 'MSM'}],
              targetpops=['MSM'],
              category='Prevention',
              short_name='MSM programs',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
PWID_programs = Program(name='PWID_programs',
              targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'PWID' in x]] + [{'param': 'hivtest', 'pop': 'PWID'}] + [{'param': 'sharing', 'pop': 'PWID'}],
              targetpops=['PWID'],
              category='Prevention',
              short_name='PWID programs',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
OST = Program(name='OST',
              targetpars=[{'param': 'numost', 'pop': 'PWID'}],
              targetpops=['PWID'],
              category='Prevention',
              short_name='OST',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
NSP = Program(name='PWID_programs',
              targetpars=[{'param': 'sharing', 'pop': 'PWID'}],
              targetpops=['PWID'],
              category='Prevention',
              short_name='NSP',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
Cash_transfers = Program(name='Cash_transfers',
              targetpars=[{'param': 'actscas', 'pop': caspship} for caspship in caspships],
              targetpops=pops,
              category='Prevention',
              short_name='Cash transfers',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
PrEP = Program(name='PrEP',
              targetpars=[{'param': 'prep', 'pop':  pop} for pop in pops],
              targetpops=pops,
              category='Prevention',
              short_name='PrEP',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})
              
PEP = Program(name='PEP',
              category='Care and treatment',
              short_name='PEP',
              criteria = {'hivstatus': ['aids', 'gt50', 'gt200', 'gt350'], 'pregnant': False})
              
HTC = Program(name='HTC',
              targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
              targetpops=pops,
              category='Care and treatment',
              short_name='HTC',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})

ART = Program(name='ART',
              targetpars=[{'param': 'numtx', 'pop': pop} for pop in pops],
              targetpops=pops,
              category='Care and treatment',
              short_name='ART',
              criteria = {'hivstatus': ['aids', 'gt50', 'gt200', 'gt350'], 'pregnant': False})

PMTCT = Program(name='PMTCT',
              targetpars=[{'param': 'numtx', 'pop': pop} for pop in femalepops] + [{'param': 'numpmtct', 'pop': pop} for pop in femalepops],
              targetpops=femalepops,
              category='Care and treatment',
              short_name='PMTCT',
              criteria = {'hivstatus': 'allstates', 'pregnant': True})
              
OVC = Program(name='OVC',
              category='Care and treatment',
              short_name='OVC',
              criteria = {'hivstatus': 'allstates', 'pregnant': False})

Other_care = Program(name='Other_care',
              category='Care and treatment',
              short_name='Other care',
              criteria = {'hivstatus': ['aids', 'gt50', 'gt200'], 'pregnant': False})

MGMT = Program(name='MGMT',
              category='Management and administration',
              short_name='MGMT')

HR = Program(name='HR',
              category='Management and administration',
              short_name='HR')

ENV = Program(name='ENV',
              category='Management and administration',
              short_name='ENV')

SP = Program(name='SP',
              category='Other',
              short_name='SP')

ME = Program(name='ME',
              category='Other',
              short_name='ME')

INFR = Program(name='INFR',
              category='Other',
              short_name='INFR')

Other = Program(name='Other',
              category='Other',
              short_name='Other')
