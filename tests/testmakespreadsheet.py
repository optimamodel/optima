#!/usr/bin/env python

"""
A more standard version of testing if the spreadsheet works

Version: 2016feb06 by cliffk
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
#'makeprogramspreadsheet',
'checkexisting',
#'makespreadsheetwithdata',
#'unittests',
]

dosave = True


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


## Just test a basic spreadsheet creation
if 'makespreadsheet' in tests:
    t = tic()
    print('Running makespreadsheet test...')
    
    from optima import makespreadsheet
    from os import remove
    filename = 'tmpspreadsheet.xlsx'
    makespreadsheet(filename, pops=2)
    if not dosave: remove(filename)
        
    done(t)




if 'makeprogramspreadsheet' in tests:
    t = tic()
    
    print('Making programs spreadsheet ...')
    from optima import defaultproject, makeprogramspreadsheet

    P = defaultproject('best',addprogset=True,addcostcovdata=False,addcostcovpars=False,addcovoutpars=False)
    R = P.progsets[0]
    filename = 'tmpprogramspreadsheet.xlsx'
    progs = [{'short':program.short, 'name':program.name, 'targetpops': program.targetpops} for program in R.programs.values()]
    makeprogramspreadsheet(filename, pops=P.data['pops']['short'], progs=progs)
    if not dosave: remove(filename)
    done()



## Test that the default spreadsheets match the new ones being created
if 'checkexisting' in tests:
    t = tic()
    print('Running check existing spreadsheets test...')
    
    ## Define the sheets to check and how many populations
    tocheck = {'simple':2, 'generalized':7, 'concentrated':6}
    prefix = '_tmp' # THe prefix to add to these files for the purposes of checking
    checksheets = True # Whether or not to check that the numbers and names of the sheets match
    checkblocks = True # Whether or not to check that the names of each block match
    checkconstants = True # Whether or not to check that the Constants sheet is identical
    checkrows = False # Whether or not to check that the number of rows in each sheet is as expected; set to False by default since depends on number of female populations, plus doesn't matter

    
    ## Imports
    from optima import makespreadsheet
    from xlrd import open_workbook
    from os import remove
    
    ## Housekeeping
    ntocheck = len(tocheck)
    tochecknames = [name+'.xlsx' for name in tocheck.keys()]
    freshnames = [prefix+name for name in tochecknames]
    
    ## Create the spreadsheets
    for name,pops in tocheck.items():
        makespreadsheet(prefix+name+'.xlsx', pops=pops)
    
    ## Read in each spreasheet and do the tests
    for ntc in range(ntocheck):
        orig = open_workbook(tochecknames[ntc])
        new  = open_workbook(freshnames[ntc])
        
        ## Check sheets names
        if checksheets:
            orignames = orig.sheet_names()
            newnames = new.sheet_names()
            if  orignames!=newnames:
                errormsg = 'Sheet names do not match for spreadsheet "%s"!' % tochecknames[ntc]
                if len(orignames)==len(newnames):
                    for s in range(len(orignames)):
                        if orignames[s]!=newnames[s]:
                            errormsg += '\nOriginal: %s | New: %s' % (orignames[s], newnames[s])
                else:
                    errormsg += '\nOriginal:\n'
                    errormsg += str(orig.sheet_names())
                    errormsg += '\nNew:\n'
                    errormsg += str(new.sheet_names())
                raise Exception(errormsg)
            print('Sheet names are OK for spreadsheet "%s"!' % tochecknames[ntc])
        
        
        ## Check block names
        if checkblocks:
            nsheets = len(orignames)
            for s in range(nsheets):
                origsheet = orig.sheet_by_index(s)
                newsheet  = new.sheet_by_index(s)
                origcol = []
                newcol = []
                ocv = origsheet.col_values(0)
                ncv = newsheet.col_values(0)
                for val in ocv: 
                    if len(val): 
                        origcol.append(val)
                for val in ncv: 
                    if len(val): 
                        newcol.append(val)
                
                if origcol!=newcol:
                    if len(origcol)==len(newcol):
                        errormsg = 'Block names differ for spreadsheet "%s"!' % tochecknames[ntc]
                        for r in range(len(origcol)):
                            if origcol[r]!=newcol[r]:
                                errormsg += '\nOriginal: %s | New: %s' % (origcol[r], newcol[r])
                    else:
                        errormsg = 'Number of block names differs for spreadsheet "%s"!' % tochecknames[ntc]
                        errormsg += '\nOriginal:\n'
                        errormsg += str(origcol)
                        errormsg += '\nNew:\n'
                        errormsg += str(newcol)
                        raise Exception(errormsg)
            print('Block names are OK for spreadsheet "%s"!' % tochecknames[ntc])
        
        ## Check constants
        if checkconstants:
            origconst = orig.sheet_by_name('Constants')
            newconst  = new.sheet_by_name('Constants')
            nrows = origconst.nrows
            if nrows!=newconst.nrows: 
                errormsg = 'Number of rows for constants differ for spreadsheet "%s"!' % tochecknames[ntc]
                errormsg += '\nOriginal: %i; new: %i' % (nrows, newconst.nrows)
                raise Exception(errormsg)
            else:
                for r in range(nrows):
                    orv = origconst.row_values(r)
                    nrv = newconst.row_values(r)
                    if orv!=nrv:
                        errormsg = 'Row content differs for spreadsheet "%s"!' % tochecknames[ntc]
                        errormsg += '\nOriginal:\n'
                        errormsg += str(orv)
                        errormsg += '\nNew:\n'
                        errormsg += str(nrv)
                        raise Exception(errormsg)
            print('Constants are OK for spreadsheet "%s"!' % tochecknames[ntc])
                
    ## Tidy up
    if not dosave:
        for name in freshnames:
            print('Removing temporary file "%s"...' % name)
            remove(name)
    
    done(t)



## Make a spreadsheet from a project
if 'makespreadsheetwithdata' in tests:
    t = tic()
    print('Running makespreadsheetwithdata test...')
    
    from optima import makespreadsheet, defaultproject, Project
    from os import remove

    # Create simple project
    P = defaultproject('best')
    P.runsim(debug=True)
    
    # Modify pop names
    pops = []
    npops = len(P.data['pops']['short'])
    newpopnames = ['SW', 'Clients', 'MSM', 'MWID', 'M 15+', 'F 15+']
    for pop in range(npops):
        pops.append({'short':newpopnames[pop],
                     'name':P.data['pops']['long'][pop],
                     'male':bool(P.data['pops']['male'][pop]),
                     'female':bool(P.data['pops']['female'][pop]),
                     'age_from':P.data['pops']['age'][pop][0],
                     'age_to':P.data['pops']['age'][pop][1]})

    filename = 'tmpspreadsheet.xlsx'
    P.makespreadsheet(filename, pops=pops)
    
    # Try reloading the spreadsheet you just made
    Q = Project(spreadsheet='tmpspreadsheet.xlsx', dorun=False)
    Q.pars()['force'] = P.pars()['force']
    Q.runsim(debug=True)    

    if not dosave: remove(filename)
        
    done(t)