import os
import unittest
from makeworkbook import OptimaWorkbook, SheetRange, TitledRange, make_populations_range, make_ref_years_range, OptimaGraphTable
import xlsxwriter

populations = [ \
    {'short_name':'MSM','name':'Men who have sex with men', \
    'male': True, 'female': False, 'injects':False, 'sexmen':False, 'sexwomen':True, 'sexworker':False, 'client':False}, \
    {'short_name':'FSW','name':'Female sex workers', \
    'male': False, 'female': True, 'injects':False, 'sexmen':True, 'sexwomen':False, 'sexworker':True, 'client':False}, \
    {'short_name':'Male PWID','name':'Men who have sex with men', \
    'male': True, 'female': False, 'injects':True, 'sexmen':True, 'sexwomen':False, 'sexworker':False, 'client':False}]
programs = [{'name':'Needle-syringe programs', 'short_name': 'NSP', 'saturating': True}, \
    {'name':'Opiate substition therapy', 'short_name': 'OST', 'saturating': False}, \
    {'name':'Programs for men who have sex with men', 'short_name': 'MSM programs', 'saturating': True}]

class TestOptimaWorkbook(unittest.TestCase):

    def test_create_workboook_with_defaults(self):
        book = OptimaWorkbook('test_example', populations, programs)
        path = '/tmp/test_example.xlsx'
        if os.path.exists(path):
          os.remove(path)
        book.create(path)
        self.assertTrue(os.path.exists('/tmp/test_example.xlsx'))

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

class TestOptimaGraphTable(unittest.TestCase):

    def test_create_table(self):
        sheet = [{
            "name":"GRAPH DATA",
            "columns":[{'title':'one', 'data':[1,2,3]}, \
            {'title':'two', 'data':[2,3,5]},{'title':'three', 'data':["a","b","c"]}]
        }]
        table = OptimaGraphTable('Beautiful graph', sheet)
        path = '/tmp/test_graph.xlsx'
        if os.path.exists(path):
          os.remove(path)
        table.create(path)
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()