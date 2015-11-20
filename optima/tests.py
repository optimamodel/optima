"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov01 by cliffk
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
'makeproject',
'saveload',
'loadspreadsheet',
'runsim',
'makeprograms']
#'gui'
#]

numericalassertions = True # Whether or not to actually run things and test their values
doplot = True # Whether or not to show diagnostic plots

runalltests=True

##############################################################################
## Initialization
##############################################################################

from utils import tic, toc, blank, pd # analysis:ignore

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


## Spreadsheet creation test
if 'makespreadsheet' in tests:
    t = tic()
    print('Running make spreadsheet test...')
    from makespreadsheet import makespreadsheet
    makespreadsheet()
    done(t)



## Project creation test
if 'makeproject' in tests:
    t = tic()
    print('Running make project test...')
    from project import Project
    P = Project()
    print(P)
    done(t)




## Project save/load test
if 'saveload' in tests:
    t = tic()
    print('Running save/load test...')
    
    from utils import save, load
    from project import Project
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    save(P, filename)
    
    print('  Checking loading...')
    Q = load(filename)
    
    done(t)




## Load spreadsheet test
if 'loadspreadsheet' in tests:
    t = tic()
    print('Running loadspreadsheet test...')
    from project import Project
    
    print('  Create a project from a spreadsheet')
    P = Project(spreadsheet='test.xlsx')
    
    print('  Load a project, then load a spreadsheet')
    Q = Project()
    Q.loadspreadsheet('test.xlsx')
    
    if numericalassertions:
        assert Q.data['const']['effcondom'][0]==0.05, 'Condom efficacy not 95% or not being read in properly'
    
    done(t)




## Run simulation test
if 'runsim' or 'gui' in tests:
    t = tic()
    print('Running runsim test...')
    
    from project import Project
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim('default')
    
    done(t)


## Project creation test
if 'makeprograms' in tests:
    t = tic()

    print('Running make programs test...')
    from programs import Program, Programset

    # First set up some programs. Programs need to be initialized with a name. Often they will also be initialized with targetpars and targetpops
    HTC = Program(name='HTC', targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],targetpops=['Females 15-49'])

    # Run additional tests if asked
    if runalltests:
        SBCC = Program(name='SBCC', targetpars=[{'param': 'condoms', 'pop': 'Females 15-49'}, {'param': 'hivtest', 'pop': 'Females 15-49'}], targetpops=['Females 15-49'])
        FSW = Program(name='FSW programs', targetpars=[{'param': 'hivtest', 'pop': 'FSW'},{'param': 'condoms', 'pop': 'FSW'}], targetpops=['FSW'])
        MGT = Program('MGT')
        ART = Program(name='ART', targetpars=[{'param': 'numtx', 'pop': 'Total'}],targetpops=['Total'])
    
        # Testing methods of program class
        # 1. Adding a target parameter to a program
        HTC.addtargetpar({'param': 'hivtest', 'pop': 'FSW'})
        HTC.addtargetpar({'param': 'hivtest', 'pop': 'Males 15-49'})
        ## NOTE that adding a targeted parameter does NOT automatically add a targeted population! Do this separately, e.g.
        HTC.targetpops.append('Males 15-49')
            
        # 2. Removing a target parameter from a program
        HTC.rmtargetpar({'param': 'hivtest', 'pop': 'FSW'})
    
        # 3. Add historical cost-coverage data point
        HTC.addcostcovdatum({'t':2013,'cost':1e6,'coverage':3e5})
    
        # 4. Overwrite historical cost-coverage data point
        HTC.addcostcovdatum({'t':2013,'cost':2e6,'coverage':3e5}, overwrite=True)
    
        # 5. Remove historical cost-coverage data point - specify year only
        HTC.rmcostcovdatum(2013)
    
        # 6. Add parameters for defining cost-coverage function.
        HTC.costcovfn.addccopar({'saturation': 0.8, 't': 2013.0, 'unitcost': 30})
        HTC.costcovfn.addccopar({'t': 2016.0, 'unitcost': 30})
        HTC.costcovfn.addccopar({'t': 2017.0, 'unitcost': 30})
    
        # 7. Overwrite parameters for defining cost-coverage function.
        HTC.costcovfn.addccopar({'t': 2016.0, 'unitcost': 25},overwrite=True)
    
        # 8. Remove parameters for defining cost-coverage function.
        HTC.costcovfn.rmccopar(2017)
    
        # 9. Get parameters for defining cost-coverage function for any given year (even if not explicitly entered).
        HTC.costcovfn.getccopar(2014)
    
        # 10. Get target population size
        HTC.gettargetpopsize(t=[2013,2015],P=P,parsetname='default')

        # 11. Evaluate cost-coverage function to get coverage for a given year, spending amount and population size
        from numpy import linspace
        HTC.getcoverage(x=linspace(0,1e6,11),t=[2013,2015],P=P,parsetname='default',total=False)
        # If you want to evaluate it for a particular population size, can also do...
        HTC.costcovfn.evaluate(x=1e6,popsize=1e5,t=2015)

    print('Running make programs set test...')
    R = Programset(programs={'HTC':HTC,'FSW programs':FSW,'MGT':MGT,'SBCC':SBCC})

    # Run additional tests if asked
    if runalltests:
        # Testing methods of program class
        # 1. Adding a program
        R.addprog({'ART':ART})
    
        # 2. Removing a program
        R.rmprog('ART')
        
        # 3. See which programs are optimizable
        R.optimizable()
    
        # 4. Produce a dictionary whose keys are populations targeted by some 
        #    program, and values are the programs that target them
        R.progs_by_targetpop()
    
        # 5. Produce a dictionary whose keys are paramter types targeted by some 
        #    program, and values are the programs that target them
        R.progs_by_targetpartype()
    
        # 6. Produce a dictionary whose keys are paramter types targeted by some 
        #    program, and values are dictionaries  whose keys are populations 
        #    targeted by some program, and values are the programs that target them
        R.progs_by_targetpar()
    
        # 7. Get a vector of coverage levels corresponding to a vector of program allocations
        from numpy import array
        budget={'HTC':array([2e5,3e5]),'FSW programs':array([1e5,2e5]),'MGT':array([2e5,3e5])}
        R.getprogcoverage(budget=budget,t=[2015,2016],P=P,parsetname='default')
        R.getpopcoverage(budget=budget,t=[2015,2016],P=P,parsetname='default')

        # 8. Add parameters for defining coverage-outcome function.
        R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.3, 't': 2013.0, 'HTC': 0.6, 'SBCC':0.1})
        R.covout['hivtest']['Males 15-49'].addccopar({'intercept': 0.3, 't': 2016.0, 'HTC': 0.65})
        R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.3, 't': 2015.0, 'HTC': 0.5, 'SBCC':0.15})
        R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.4, 't': 2017.0, 'HTC': 0.4, 'SBCC':0.2})
    
        # 9. Overwrite parameters for defining coverage-outcome function.
        R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.35, 't': 2015.0, 'HTC': 0.45, 'SBCC':0.15},overwrite=True)
    
        # 10. Remove parameters for defining coverage-outcome function.
        R.covout['hivtest']['Females 15-49'].rmccopar(2017)
        
        # 11. Get parameters for defining cost-coverage function for any given year (even if not explicitly entered).
        R.covout['hivtest']['Females 15-49'].getccopar(2014)

        # 12. Get a set of parameter values corresponding to a vector of program allocations
        R.getoutcomes(tvec=None,budget=None)

    done(t)


## Run the GUI
if 'gui' in tests:
    t = tic()
    print('Running GUI test...')
    
    try:
        from gui import gui
        gui(results)
    except:
        print('Backend GUI failed to load -- not critical')
    
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)