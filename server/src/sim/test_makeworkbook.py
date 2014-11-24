import os
import unittest
from makeworkbook import OptimaWorkbook, SheetRange, TitledRange, make_programs_range, make_populations_range, make_ref_years_range
import xlsxwriter

populations = [ \
    {'internal_name':'MSM', 'short_name':'MSM','name':'Men who have sex with men', \
    'male': True, 'female': False, 'injects':False, 'hetero':False, 'homo':True, 'sexworker':False, 'client':False}, \
    {'internal_name':'FSW', 'short_name':'FSW','name':'Female sex workers', \
    'male': False, 'female': True, 'injects':False, 'hetero':True, 'homo':False, 'sexworker':True, 'client':False}, \
    {'internal_name':'MWID', 'short_name':'Male PWID','name':'Men who have sex with men', \
    'male': True, 'female': False, 'injects':True, 'hetero':True, 'homo':False, 'sexworker':False, 'client':False}]
programs = [{'name':'Needle-syringe programs', 'internal_name':'NSP', 'short_name': 'NSP', 'saturating': True}, \
    {'name':'Opiate substition therapy', 'internal_name':'OST', 'short_name': 'OST', 'saturating': False}, \
    {'name':'Programs for men who have sex with men', 'internal_name':'MSM', 'short_name': 'MSM programs', 'saturating': True}]

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
        refs = range.param_refs("Test Sheet")
        print(refs)
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
        names = ref_content.row_names
        self.assertEqual(ref_content.row_names, ["='Test Sheet'!$C$3", "='Test Sheet'!$C$4", "='Test Sheet'!$C$5"])

if __name__ == '__main__':
    unittest.main()