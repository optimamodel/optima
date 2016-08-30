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
#'forcerefresh',
#'makeprojects',
#'makeportfolio',
#'generateBOCs',
#'rungui',
'runbackend'
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




if 'runbackend' in tests:
    from optima import defaultobjectives
    from optima.geospatial import makesheet, makeproj, create, addproj, saveport, loadport, rungeo, export, plotgeo

    print('\n\n\nCreating portfolio from subdivision spreadsheet.')
    makesheet(projectpath='./geo/blantyre.prj', spreadsheetpath='./geo/blantyre-split-blank.xlsx', copies=2, refyear=2017)
    makeproj(projectpath='./geo/blantyre.prj', spreadsheetpath='./geo/blantyre-split-filled.xlsx', destination='./geo')
    create(filepaths=['./geo/blantyre-district-1.prj','./geo/blantyre-district-2.prj'])
    
    print('\n\n\nCreating portfolio from projects (that already have BOCs).')
    create(filepaths=['./geo/blantyre.prj'])
    addproj(filepaths=['./geo/balaka.prj'])   # Use addportfolio argument if not wanting to work with globals.
    saveport(filepath='./geo/blantyre-balaka.prt')    # Use portfolio argument if not wanting to work with globals.

    print('\n\n\nRunning geospatial analysis.')
    gaobjectives = defaultobjectives(verbose=0)
    gaobjectives['budget'] = 15000000.0 # Reset
    portfolio = loadport(filepath='./geo/blantyre-balaka.prt')
    rungeo(portfolio=portfolio, objectives=gaobjectives, BOCtime=2)     # Use portfolio argument if not wanting to work with globals.
    export(filepath='./geo/blantyre-balaka-results.xlsx')
    plotgeo()



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
    