"""
Test script to see if geospatial analysis works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan20 by davidkedz
"""



## Define tests to run here!!!
tests = [
'makeportfolio',
'generateBOCs',
#'loadspreadsheet',
#'loadeconomics',
#'runsim'
]

##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()


## Project creation test
if 'makeportfolio' in tests:
    t = tic()
    print('Running make portfolio test...')
    from optima import Portfolio, Project, Programset, Program
    F = Portfolio()
    P1 = Project(spreadsheet='test7pops.xlsx')
    P2 = Project(spreadsheet='test7pops.xlsx')
    
    # THIS PROGSET CONSTRUCTION IS MOMENTARY UNTIL NICE EXAMPLE PRJ FILES EXIST.
    # ----------
    pops = P1.data['pops']['short']
    caspships = P1.data['pships']['cas']
    compships = P1.data['pships']['com']
    
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
    P1.addprogset(name='default', progset=R)
    P2.addprogset(name='default', progset=R)
    # ----------
    
    F.addproject(P1)
    F.addproject(P2)
    print(F)
    done(t)




## BOC generation test
if 'generateBOCs' in tests:
    t = tic()

    print('Running BOC generation test...')
    F.genBOCs()    
    
    done(t)





print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)