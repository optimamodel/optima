"""
Test the cascade

Version: 2016jan23 by cliffk
"""



## Define tests to run here!!!
tests = [
'compare',
'simple',
'cascade'
]


##############################################################################
## Initialization -- same for every test script -- WARNING, should these be in testheader.py called by exec(open('testheader.py').read())?
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

T = tic()


##############################################################################
## The tests
##############################################################################





#####################################################################################################
if 'compare' in tests:
    t = tic()
    print('Running comparison test...')
    
    toplot = ['prev-tot', 'numinci-sta', 'numplhiv-sta', 'numtreat-sta'] # Specify what plots to display here
    
    from optima import Project
    P = Project(spreadsheet='generalized.xlsx')
    P.settings.usecascade = False
    pp = tic()
    P.runsim()
    toc(pp, label='model run without cascade')
    
    Q = Project(spreadsheet='generalized.xlsx')
    Q.settings.usecascade = True
    qq = tic()
    Q.runsim()
    toc(qq, label='model run with cascade')
    
    
    
    if doplot:
        from optima import plotresults
        plotresults(P.results[-1], toplot=toplot, figsize=(16,10), num='No cascade')
        plotresults(Q.results[-1], toplot=toplot, figsize=(16,10), num='With cascade')
    
    done(t)



if 'simple' in tests:
    t = tic()
    print('Running simple test...')
    from optima import Project
    P = Project(spreadsheet='simple.xlsx')
    P.settings.usecascade = False
    qq = tic()
    results = P.runsim()
    toc(qq, label='model run with cascade')
    if doplot:
        settings = P.settings
        from numpy import linspace
        tvec = linspace(settings.start, settings.end, round((settings.end-settings.start)/settings.dt)+1)
        from matplotlib import pyplot as plt
        alldx = results.raw[0]['people'][settings.alldx,:,:].sum(axis=(0,1))
        plhiv = results.raw[0]['people'][settings.allplhiv,:,:].sum(axis=(0,1))
        treat = results.raw[0]['people'][settings.alltx,:,:].sum(axis=(0,1))

        fig = plt.figure()
        plt.plot(tvec,plhiv,label='PLHIV')
        plt.plot(tvec,alldx,label='All diagnosed')
        plt.plot(tvec,treat,label='on treatment')
        plt.legend(loc='best')
        fig.savefig("simple_all.png")

    done(t)





if 'cascade' in tests:
    t = tic()
    print('Running cascade test...')
    from optima import Project, plotting
    Q = Project(spreadsheet='cascade2p.xlsx')
    Q.settings.usecascade = True
    qq = tic()
    results = Q.runsim()
    toc(qq, label='model run with cascade')
    
    #toplot = ['prev-tot', 'numinci-sta', 'numplhiv-sta', 'numtreat-sta'] # Specify what plots to display here
    if doplot:
        """
        from optima import plotresults
        plotresults(P.results[-1], toplot=toplot, figsize=(16,10), num='No cascade')
        plotresults(Q.results[-1], toplot=toplot, figsize=(16,10), num='With cascade')
        """
        settings = Q.settings
        from numpy import linspace
        tvec = linspace(settings.start, settings.end, round((settings.end-settings.start)/settings.dt)+1)
        plotting.plotcascade(results=results)

        from matplotlib import pyplot as plt


        alive   = results.raw[0]['people'][settings.allstates,:,:].sum(axis=(0,1))
        sus     = results.raw[0]['people'][settings.sus,:,:].sum(axis=(0,1))
        alldx   = results.raw[0]['people'][settings.alldx,:,:].sum(axis=(0,1))
        diag    = results.raw[0]['people'][settings.dx,:,:].sum(axis=(0,1))
        care    = results.raw[0]['people'][settings.care,:,:].sum(axis=(0,1))
        allcare = results.raw[0]['people'][settings.allcare,:,:].sum(axis=(0,1))
        plhiv   = results.raw[0]['people'][settings.allplhiv,:,:].sum(axis=(0,1))
        treat   = results.raw[0]['people'][settings.alltx,:,:].sum(axis=(0,1))
        supp    = results.raw[0]['people'][settings.svl,:,:].sum(axis=(0,1))
        lost    = results.raw[0]['people'][settings.lost,:,:].sum(axis=(0,1))
        off     = results.raw[0]['people'][settings.off,:,:].sum(axis=(0,1))
        deadhiv = (results.raw[0]['death'][:,:].sum(axis=0)).cumsum()
        deadoth = (results.raw[0]['otherdeath'][:,:].sum(axis=0)).cumsum()

        fig = plt.figure()
        plt.plot(tvec,plhiv,label='PLHIV')
        plt.plot(tvec,alldx,label='all diagnosed')
        #plt.plot(tvec,diag,label='diagnosed but not in care/pre-treatment')
        #plt.plot(tvec,care,label='care')
        plt.plot(tvec,allcare,label='all in care')
        plt.plot(tvec,treat,label='on treatment')
        plt.plot(tvec,supp,label='suppressed viral load')
        #plt.plot(tvec,lost,label='off ART, not in care')
        #plt.plot(tvec,off,label='off ART in care')
        plt.legend(loc='best')
        fig.savefig("cascade_all.png")


        fig = plt.figure()
        plt.plot(tvec,alive,label='alive')
        plt.plot(tvec,sus,label='susceptibles')
        plt.plot(tvec,deadhiv,label='dead (HIV)')
        plt.plot(tvec,deadoth,label='dead (other)')
        plt.legend(loc='best')
        fig.savefig("cascade_general.png")
        

    done(t)






print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
