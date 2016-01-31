"""
Test the cascade

Version: 2016jan30 by cliffk
"""



## Define tests to run here!!!
tests = [
'compare',
'90-90-90'
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
    
    toplot = ['prev-tot', 'numinci-sta', 'numplhiv-sta', 'numtreat-sta', 'cascade'] # Specify what plots to display here
    
    import optima as op
    P = op.Project(spreadsheet='generalized.xlsx')
    P.settings.usecascade = False
    pp = tic()
    P.runsim()
    toc(pp, label='model run without cascade')
    
    Q = op.Project(spreadsheet='generalized.xlsx')
    Q.settings.usecascade = True
    qq = tic()
    Q.runsim()
    toc(qq, label='model run with cascade')
    
    if doplot:
        op.gui.plotpeople(P, P.results[-1].raw[0]['people'], animate=False, figsize=(16,10), num='No cascade')
        op.gui.plotpeople(Q, Q.results[-1].raw[0]['people'], animate=False, figsize=(16,10), num='With cascade')
    
    done(t)








print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
