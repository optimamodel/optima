import os
import unittest
from makespreadsheet import OptimaSpreadsheet, SheetRange, TitledRange, make_populations_range, make_ref_years_range, OptimaGraphTable
import xlsxwriter

populations = [{"name": "Female sex workers", "short": "FSW", "female": True, "male": False, "agefrom": 15, "ageto": 49}, \
    {"name": "Clients of sex workers", "short": "Clients", "female": False, "male": True, "agefrom": 15, "ageto": 49}, \
    {"name": "Men who have sex with men", "short": "MSM", "female": False, "male": True, "agefrom": 15, "ageto": 49}, \
    {"name": "Males who inject drugs", "short": "MWID", "female": False, "male": True, "agefrom": 15, "ageto": 49}, \
    {"name": "Other males 15-49", "short": "Other males", "female": False, "male": True, "agefrom": 15, "ageto": 49}, \
    {"name": "Other females 15-49", "short": "Other females", "female": True, "male": False, "agefrom": 15, "ageto": 49}]

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
        make_ref_years_range('Coverage', content_range, 2000, 2015)

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


if __name__ == '__main__':
    unittest.main()