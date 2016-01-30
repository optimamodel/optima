"""
A more standard version of testing if the spreadsheet works

Version: 2016jan19 by cliffk
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
'unittests',
]

dosave = False


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


if 'makespreadsheet' in tests:
    t = tic()
    print('Running makespreadsheet test...')
    
    from optima import makespreadsheet
    from os import remove
    filename = 'tmpspreadsheet.xlsx'
    makespreadsheet(filename, pops=2)
    if not dosave: remove(filename)
        
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
    unittest.main()