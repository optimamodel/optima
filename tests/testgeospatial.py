"""
Test script to see if geospatial analysis works.
Note that GUI can be extremely dangerous, as it redirects stdout!
Make sure that GUI is exited normally, otherwise stdout reference will be lost until console reset...

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016feb05
"""



## Define tests to run here!!!
tests = [
#'dcworkshop',
#'forcerefresh',
#'makeprojects',
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

filename1 = 'test1.prj'
filename2 = 'test2.prj'


##############################################################################
## The tests
##############################################################################

T = tic()


if 'dcworkshop' in tests:
    
    t = tic()
    print('DC Workshop Special Test - Wooo...!')
    from optima import *    
    
    P1 = loadobj('.\Mozambique_Center.prj')
    P2 = loadobj('.\Mozambique_North.prj')
    P3 = loadobj('.\Mozambique_South.prj')
    
#    hereyougokedz1 = [(u'Females 15-49', u'Clients'), (u'Males 15-49', u'FSW'),  
#                 (u'Females 15-49', u'Males 15-49'), (u'Females 50+', u'Males 50+'),
#                 (u'Females 0-14', u'Males 0-14'), (u'Males 50+', u'Females 15-49'), (u'Females 50+', u'Males 15-49')]
#                 
#    hereyougokedz2 = [(u'Males 15-49', u'PWID'), (u'Females 50+', u'PWID'), (u'Females 15-49', u'PWID')]
#
#    for lolkedz in hereyougokedz1: 
#        P1.progsets[0].covout['condcas'][lolkedz].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC':(0.45,0.55)})
#        
#    for lolkedz in hereyougokedz2: 
#        P2.progsets[0].covout['condcas'][lolkedz].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'PWID programs':(0.45,0.55)})
#        P3.progsets[0].covout['condcas'][lolkedz].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'PWID programs':(0.45,0.55)})
#    
#    P3.progsets[0].programs[1].costcovfn.addccopar({'saturation': (0.8, 1.0), 't': 2015, 'unitcost': (30, 50)})
    
    

    F = Portfolio(projects=[P1,P2,P3])
    F.genBOCs()
    
    done(t)
   


## Make projects test
if 'makeprojects' in tests:
    t = tic()
    print('Running makeprojects...')
    from optima import saveobj, defaults
    import os

    projtypes = ['generalized', 'concentrated']
    filenames = ['geotestproj1.prj','geotestproj2.prj']
    
    for i in range(len(projtypes)):
        thisfile = filenames[i]
        refreshtest = 'forcerefresh' in tests
        notexiststest = not(os.path.exists(thisfile))
        if refreshtest or notexiststest:
            print('You are rerunning "%s" because forcerefresh=%s and notexists=%s' % (thisfile, refreshtest, notexiststest)) 
            thisproj = defaults.defaultproject(projtypes[i], name='District %i'%(i+1))
            thisproj.genBOC(maxtime=3)
            saveobj(thisfile, thisproj)
    
    done(t)






## Project creation test
if 'makeportfolio' in tests:
    t = tic()
    print('Running make portfolio test...')
    from optima import Portfolio
    from optima.defaults import defaultproject
    
    P1 = defaultproject('concentrated')
    P2 = defaultproject('concentrated')

    P1.progsets[0].rmprogram('OST')
    P2.progsets[0].rmprogram('OST')
    P2.progsets[0].rmprogram('HTC')

    F = Portfolio(projects=[P1,P2])

    done(t)




## BOC generation test
if 'generateBOCs' in tests:
    t = tic()

    print('Running BOC generation test...')
    from optima import saveobj
    
    F.genBOCs(progsetnames=['default','default'], parsetnames=['default','default'], maxtime=3)#,forceregen = True)#, maxtime = 20)
    F.plotBOCs()
    
    print('Saving projects with BOCs...')
    saveobj(filename1, P1)
    saveobj(filename2, P2)
    
    done(t)




if 'rungui' in tests and doplot:
    t = tic()

    print('Running geo GUI test...')
    from optima import geogui
    if __name__ == '__main__':      # Required when multiprocessing.
        geogui()
    
    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
    