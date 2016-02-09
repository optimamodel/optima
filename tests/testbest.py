"""
Create a good test project

Version: 2016feb08
"""

from optima import defaultprogset, Program, Programset, Parscen, Budgetscen, defaults, pygui, Project, dcp, plotpars, plotpeople, saveobj # analysis:ignore

## Options
docalibrate = 1 # Whether or not to run autofitting
manualfit = 0
runscenarios = 0 # Run scenarios
optimize = 0
dosave = 0
filename = 'best.prj'

def createproject(name):
    ''' Function for creatinlg the best project the world has ever seen. '''
    # Make project and store results from default sim
    P = Project(spreadsheet='concentrated.xlsx')
    
    caspships = P.parsets['default'].pars[0]['condcas'].y.keys()
    pops = P.parsets[0].popkeys
    
    allcaspships = [{'param': 'condcas', 'pop': caspship} for caspship in caspships]
    
    Condoms = Program(short='Condoms', targetpars=allcaspships, targetpops=pops, category='Prevention', name='Condom promotion and distribution', criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    # Extract commercial partnerships that include at least one female sex worker
    fsw_compships = []
    for fsw in fswlist:
        for compship in compships:
            if fsw in compship:
                fsw_compships.append(compship)    
    
    FSW_programs = Program(short='FSW programs',
                  targetpars=[{'param': 'condcom', 'pop': compship} for compship in fsw_compships] + [{'param': 'condcas', 'pop': caspship} for caspship in fsw_caspships] + [{'param': 'hivtest', 'pop': pop} for pop in fswlist],
                  targetpops=fswlist,
                  category='Prevention',
                  name='Programs for female sex workers and clients',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
                  
    HTC = Program(short='HTC',
                  targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                  targetpops=pops,
                  category='Care and treatment',
                  name='HIV testing and counseling',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    ART = Program(short='ART',
                  targetpars=[{'param': 'numtx', 'pop': 'tot'}],# for pop in pops],
                  targetpops=pops,
                  category='Care and treatment',
                  name='Antiretroviral therapy',
                  criteria = {'hivstatus': 'allstates', 'pregnant': False})
    
    Other = Program(short='Other',
                  category='Other',
                  name='Other')
    
    R = Programset(programs=[Condoms, FSW_programs, HTC, ART, Other])
    
    Condoms.costcovfn.addccopar({'saturation': (0.75,0.75), 't': 2016.0, 'unitcost': (3,7)})
    FSW_programs.costcovfn.addccopar({'saturation': (0.9,0.9), 't': 2016.0, 'unitcost': (25,35)})
    HTC.costcovfn.addccopar({'saturation': (0.85,0.95), 't': 2016.0, 'unitcost': (10,20)})    
    ART.costcovfn.addccopar({'saturation': (0.9,0.9), 't': 2016.0, 'unitcost': (100,200)})

    

    # Get a default progset 
    
    R.programs['Condoms'].costcovdata =      {'t':[2014],'cost':[1.3e7],'coverage':[3e5]}
    R.programs['FSW programs'].costcovdata = {'t':[2014],'cost':[2.5e6],'coverage':[1e9]}
    R.programs['HTC'].costcovdata =          {'t':[2014],'cost':[1e7],'coverage':[1.3e6]}
    R.programs['ART'].costcovdata =          {'t':[2014],'cost':[2e7],'coverage':[2e4]}
    R.programs['Other'].costcovdata =        {'t':[2014],'cost':[1.5e7],'coverage':[None]}
    
    # Add program effects
    R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept':  (0.2,0.25), 't': 2016.0, 'Condoms':(0.35,0.45), 'FSW programs':(0.75,0.85)})
    R.covout['condcas'][('F 15+','Clients')].addccopar({'intercept': (0.25,0.3), 't': 2016.0, 'Condoms':(0.85,0.95)})
    R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept':    (0.3,0.35), 't': 2016.0, 'Condoms':(0.50,0.55), 'FSW programs':(0.59,0.65)})
    R.covout['condcas'][('F 15+', 'M 15+')].addccopar({'intercept':  (0.30,0.35), 't': 2016.0, 'Condoms':(0.45,0.50)})
    R.covout['condcas'][('F 15+', 'PWID')].addccopar({'intercept':   (0.15,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.1,0.15), 't': 2016.0, 'Condoms':(0.55,0.65)})

    R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'FSW programs':(0.9,0.95)})

    R.covout['hivtest']['FSW'].addccopar({'intercept': (0.20,0.30), 't': 2016.0, 'HTC': (0.90,0.95), 'FSW programs':(0.90,0.95)})
    R.covout['hivtest']['Clients'].addccopar({'intercept': (0.05,0.10), 't': 2016.0, 'HTC': (0.40,0.60)})
    R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.01,0.02), 't': 2016.0, 'HTC': (0.20,0.30)})
    R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.01,0.02), 't': 2016.0, 'HTC': (0.20,0.30)})
    R.covout['hivtest']['PWID'].addccopar({'intercept': (0.10,0.15), 't': 2016.0, 'HTC': (0.70,0.80)})
    R.covout['hivtest']['MSM'].addccopar({'intercept': (0.10,0.15), 't': 2016.0, 'HTC': (0.70,0.80)})

    R.covout['numtx']['tot'].addccopar({'intercept': (10.0,15.0), 't': 2016.0})
    
    # Store this program set in the project
    P.addprogset(R)





P = createproject('concentrated')




## Calibration
if docalibrate: 
    P.autofit(name='default', maxiters=60)
    pygui(P.parsets[-1].getresults())
else: 
    P.parsets[0].pars[0]['force'].y[:] = [ 1.8  ,  1.1  ,  0.875,  0.775,  1.45 ,  0.6  ]
    P.runsim()

if manualfit: P.manualfit()



if runscenarios:
    defaultbudget = P.progsets['default'].getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    nobudget = dcp(defaultbudget)
    for key in nobudget: nobudget[key] *= 1e-6
    scenlist = [
#        Parscen(name='Current conditions', parsetname='default', pars=[]),
        Budgetscen(name='No budget', parsetname='default', progsetname='default', t=[2016], budget=nobudget),
#        Budgetscen(name='Current budget', parsetname='default', progsetname='default', t=[2016], budget=defaultbudget),
        Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.addscenlist(scenlist)
    P.runscenarios() 
#    plotpeople(P, P.results[-1].raw[-1][0]['people'])
    apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
    pygui(P.results[-1], toplot='default')



if optimize:
    P.optimize(maxtime=20)
    pygui(P.results[-1])
    

if dosave:
    saveobj(filename,P)