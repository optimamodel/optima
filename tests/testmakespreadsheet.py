"""
A more standard version of testing if the spreadsheet works

Version: 2016jan19 by cliffk
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
'checkexisting',
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





## Test that the default spreadsheets match the new ones being created
if 'checkexisting' in tests:
    t = tic()
    print('Running check existing spreadsheets test...')
    
    ## Define the sheets to check and how many populations
    tocheck = {'simple':2, 'generalized':7, 'concentrated':8}
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
    for name in freshnames:
        print('Removing temporary file "%s"...' % name)
        remove(name)
    
    done(t)











##############################################################################
## Anna's original unit tests
##############################################################################



import os
import unittest
from optima.makespreadsheet import OptimaSpreadsheet, SheetRange, TitledRange, make_populations_range, make_ref_years_range, OptimaGraphTable
import xlsxwriter

populations = [{"name": "Female sex workers", "short": "FSW", "female": True, "male": False, "are_from": 15, "age_to": 49}, \
    {"name": "Clients of sex workers", "short": "Clients", "female": False, "male": True, "are_from": 15, "age_to": 49}, \
    {"name": "Men who have sex with men", "short": "MSM", "female": False, "male": True, "are_from": 15, "age_to": 49}, \
    {"name": "Males who inject drugs", "short": "Male PWID", "female": False, "male": True, "are_from": 15, "age_to": 49}, \
    {"name": "Other males [enter age]", "short": "Other males", "female": False, "male": True, "are_from": 0, "age_to": 0}, \
    {"name": "Other females [enter age]", "short": "Other females", "female": True, "male": False, "are_from": 0, "age_to": 0}]

class TestOptimaSpreadsheet(unittest.TestCase):

    def test_create_spreadsheet_with_defaults(self):
        import xlrd
        book = OptimaSpreadsheet('test_example', populations)
        path = '/tmp/test_example.xlsx'
        if os.path.exists(path):
          os.remove(path)
        book.create(path)
        self.assertTrue(os.path.exists('/tmp/test_example.xlsx'))
        workbook = xlrd.open_workbook(path)
        for name, value in book.sheet_names.iteritems():
            self.assertTrue(workbook.sheet_by_name(value) is not None)

    def test_range_references(self):
        range = SheetRange(0,0,5,5)
        refs = range.param_refs("Test Sheet", 0)
        print(refs)
        #taking param refs from the 1st column
        expected_refs = ["='Test Sheet'!$A$1", "='Test Sheet'!$A$2", "='Test Sheet'!$A$3", "='Test Sheet'!$A$4", "='Test Sheet'!$A$5"]
        self.assertEqual(refs, expected_refs)

    def test_ref_years_range(self):
        path = '/tmp/test_ref_years_range.xlsx'
        populations = ['General males', 'General females', 'Female sex workers']
        if os.path.exists(path):
          os.remove(path)
        book = xlsxwriter.Workbook(path)
        test_sheet = book.add_worksheet('Test Sheet')
        content = make_populations_range('Populations', populations)
        content_range = TitledRange(test_sheet, 0, content)
        ref_content = make_ref_years_range('Coverage', content_range, 2000, 2015)
        return ref_content



class TestOptimaGraphTable(unittest.TestCase):

    def test_create_table(self):
        sheet = [{
            "name":"GRAPH DATA",
            "columns":[{'title':'one', 'data':[1,2,3]}, \
            {'title':'two', 'data':[2,3,5]},{'title':'three', 'data':["a","b","c"]}]
        }]
        table = OptimaGraphTable(sheet)
        path = '/tmp/test_graph.xlsx'
        if os.path.exists(path):
          os.remove(path)
        table.create(path)
        self.assertTrue(os.path.exists(path))



class TestEconSpreadsheet(unittest.TestCase):
    def test_create_econspreadsheet_with_defaults(self):
        import xlrd
        from optima.makespreadsheet import EconomicsSpreadsheet
        book = EconomicsSpreadsheet('testeconomics')
        path = '/tmp/testeconomics.xlsx'
        if os.path.exists(path):
          os.remove(path)
        book.create(path)
        self.assertTrue(os.path.exists('/tmp/testeconomics.xlsx'))
        workbook = xlrd.open_workbook(path)
        for name, value in book.sheet_names.iteritems():
            self.assertTrue(workbook.sheet_by_name(value) is not None)



if 'unittests' in tests: # Actually run the unit tests
    from pylab import isinteractive
    if not isinteractive():
        unittest.main()
    else:
        print('Note:\nTo run makespreadsheet unit tests, do not run in\ninteractive mode, for your console will die :(')