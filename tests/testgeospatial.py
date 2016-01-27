"""
Test script to see if geospatial analysis works.
Note that GUI can be extremely dangerous, as it redirects stdout!
Make sure that GUI is exited normally, otherwise stdout reference will be lost until console reset...

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan20 by davidkedz
"""



## Define tests to run here!!!
tests = [
#'forcerefresh',
#'makeportfolio',
#'generateBOCs',
'rungui',
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




## Force refresh test
if 'forcerefresh' in tests:
    t = tic()
    print('Running force refresh test...')
    from os import remove
    
    try:
        print('Deleting project files to be used in this test...')
        remove('test7popsARTandHTC.prj')
        remove('test7popsART.prj')
    except OSError:
        print('No relevant project files can be found...')
    
    done(t)




## Project creation test
if 'makeportfolio' in tests:
    t = tic()
    print('Running make portfolio test...')
    from optima import Portfolio, Project, Program, Programset, loadobj
    from copy import deepcopy as dcp
    F = Portfolio()
    
    try:
        print('Loading projects...')
        P1 = loadobj('test7popsFSWandCon.prj')
        P2 = loadobj('test7popsCon.prj')
    except:
        print('Project files cannot be found.\nNow generating from scratch...')
        P1 = Project(name='Test with Condoms and FSW Programs', spreadsheet='test7pops.xlsx')
        P2 = Project(name='Test with Condoms only', spreadsheet='test7pops.xlsx')
        
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
        
        R = dcp(R)
        R.rmprogram('FSW programs')        
        
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
    from optima import Project, saveobj
    from optima import defaultobjectives
    
    objectives = defaultobjectives()
#    objectives['inciweight'] = 5
    F.genBOCs(objectives)#,forceregen = True)#, maxtime = 20)
    F.plotBOCs(objectives)    
    
    print('Saving projects with BOCs...')
    saveobj('test7popsFSWandCon.prj', P1)
    saveobj('test7popsCon.prj', P2)
    
    done(t)




if 'rungui' in tests and doplot:
    from optima import Project, Portfolio, geogui, saveobj
    
#    P = Project(spreadsheet='test.xlsx')
#    Q = Project(spreadsheet='test.xlsx')
#    F = Portfolio()
#    for proj in [P, Q]: F.addproject(proj)
#    saveobj('test2.prj', P)
#    saveobj('test7.prj', Q)
#    saveobj('test.prt', F)
    print('Opening geospatial GUI. It will run after tests are completed.')



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)

# The actual GUI is delayed until after the rest of test output, otherwise that too will be displayed in the widget.
if 'rungui' in tests:
    geogui()