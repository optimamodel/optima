"""
MAKEDEFAULTS

A little set of functions for setting up various default projects for testing purposes.

Version: 2016jan27
"""

from optima import Project, Programset, Program
from optima.defaults import defaultprograms

def defaultprogset(P, addpars=False, addcostcov=False, filterprograms=None):
    ''' Make a default programset (for testing optimisations)'''
    programs = defaultprograms(P, addpars=addpars, addcostcov=addcostcov, filterprograms=filterprograms)
    R = Programset(programs=programs)   
    return R




def defaultproject(which='simple', addprogset=True):
    ''' Options for easily creating default projects -- useful for testing '''
    
    if which=='generalized':
        print('Creating generalized epidemic project...')
        P = Project(spreadsheet='generalized.xlsx')
        pops = P.data['pops']['short']
        caspships = P.data['pships']['cas']
        compships = P.data['pships']['com']
        
        condprog = Program(name='Condoms',
                      targetpars=[{'param': 'condcas', 'pop': caspship} for caspship in caspships],
                      targetpops=pops,
                      category='Prevention',
                      short='Condoms',
                      criteria = {'hivstatus': 'allstates', 'pregnant': False})    
                      
        fswprog = Program(name='FSW_programs',
                      targetpars=[{'param': 'condcom', 'pop': compship} for compship in [x for x in compships if 'FSW' in x]] + [{'param': 'condcas', 'pop': caspship} for caspship in [x for x in caspships if 'FSW' in x]] + [{'param': 'hivtest', 'pop': 'FSW'}],
                      targetpops=['FSW'],
                      category='Prevention',
                      short='FSW programs',
                      criteria = {'hivstatus': 'allstates', 'pregnant': False})
        
        condprog.costcovfn.addccopar({'saturation': (0.75,0.75), 't': 2016.0, 'unitcost': (30,40)})
        fswprog.costcovfn.addccopar({'saturation': (0.9,0.9), 't': 2016.0, 'unitcost': (50,80)})
        
        condprog.addcostcovdatum({'t':2015,
                                  'cost':2e6,
                                  'coverage':57143.})
        
        fswprog.addcostcovdatum({'t':2015,
                                  'cost':3e6,
                                  'coverage':45261.})
        
        R = Programset(programs=[condprog, fswprog]) 
        
        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
        R.covout['condcas'][('Clients', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65)})
        R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
        R.covout['condcas'][('M 15+', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW_programs':(0.9,0.95)})
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'FSW_programs':(0.6,0.65)})
        P.addprogset(name='default', progset=R)
    
    
    
    
    elif which=='concentrated':
        # Make project and store results from default sim
        P = Project(spreadsheet='concentrated.xlsx')
    
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
        
    
    
    return P