"""
Test the cascade

Version: 2016jan23 by cliffk
"""



## Define tests to run here!!!
tests = [
#'compare',
'comparesimple'
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



if 'comparesimple' in tests:
    t = tic()
    print('Running comparison test...')
    
    toplot = ['prev-tot', 'numinci-sta', 'numplhiv-sta', 'numtreat-sta'] # Specify what plots to display here
    
    from optima import Project
    Q = Project(spreadsheet='cascade2p.xlsx')
    Q.settings.usecascade = True
    qq = tic()
    Q.runsim()
    toc(qq, label='model run with cascade')
    
    
    if doplot:
        """
        from optima import plotresults
        plotresults(P.results[-1], toplot=toplot, figsize=(16,10), num='No cascade')
        plotresults(Q.results[-1], toplot=toplot, figsize=(16,10), num='With cascade')
        """
        settings = Q.settings
        from numpy import linspace
        tvec = linspace(settings.start, settings.end, round((settings.end-settings.start)/settings.dt)+1)

        plhiv = Q.results.raw[0]['people'][settings.allplhiv,:,:].sum(axis=(0,1))
        alldx = Q.results.raw[0]['people'][settings.alldx,:,:].sum(axis=(0,1))
        care = Q.results.raw[0]['people'][settings.care,:,:].sum(axis=(0,1))

        from pylab import figure, plot
        figure()
        plot(tvec,care)
        
        
    done(t)






print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
