"""
Test script to see if geospatial analysis works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan20 by davidkedz
"""



## Define tests to run here!!!
tests = [
#'forcerefresh',
'makeportfolio',
'generateBOCs',
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
    from optima import Portfolio, Project, loadobj
    from optima.defaults import defaultprogset
    F = Portfolio()
    
    try:
        print('Loading projects...')
        P1 = loadobj('test7popsARTandHTC.prj')
        P2 = loadobj('test7popsART.prj')
    except:
        print('Project files cannot be found.\nNow generating from scratch...')
        P1 = Project(name='Test with ART and HTC', spreadsheet='test7pops.xlsx')
        P2 = Project(name='Test with ART only', spreadsheet='test7pops.xlsx')
        
        # THIS PROGSET CONSTRUCTION IS MOMENTARY UNTIL NICE EXAMPLE PRJ FILES EXIST.
        # ----------
        R = defaultprogset(P1, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW_programs', 'HTC', 'ART'])
    
        R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'M 0-14'})
        R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'F 0-14'})
        R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('M 0-14'))
        R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('F 0-14'))
        R.updateprogset()
    
        R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
        R.covout['condcas'][('Clients', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65), 'MSM_programs':(0.75,0.85)})
        R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
        R.covout['condcas'][('M 15+', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
        R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW_programs':(0.9,0.95)})
        R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99), 'FSW_programs':(0.95,0.99)})
        R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99), 'MSM_programs':(0.95,0.99)})
        R.covout['hivtest']['Clients'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
        R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
        P1.addprogset(name='default', progset=R)
        R.rmprogram('HTC')
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
    F.genBOCs(objectives)
    F.plotBOCs(objectives)    
    
    print('Saving projects with BOCs...')
    saveobj('test7popsARTandHTC.prj', P1)
    saveobj('test7popsART.prj', P2)
    
    done(t)





print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)