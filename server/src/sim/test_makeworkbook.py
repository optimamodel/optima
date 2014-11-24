import os
import unittest
from makeworkbook import OptimaWorkbook, SheetRange, TitledRange, make_parameter_range, make_ref_years_range
import xlsxwriter

class TestOptimaWorkbook(unittest.TestCase):
  def test_create_workboook_with_defaults(self):
    populations = [{'name':'General males'}, {'name':'General females'}, {'name':'Female sex workers'}]
    programs = [{'name':'Behavior change', 'acronym':'BEH'}, {'name':'Needle-syringe program', 'acronym':'NSP'}, \
    {'name':'HIV counseling and testing', 'acronym':'HIVCT'}]
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
    content = make_parameter_range('Populations', populations)
    content_range = TitledRange(test_sheet, 0, content)
    ref_content = make_ref_years_range('Coverage', content_range, 2000, 2015)
    names = ref_content.row_names
    self.assertEqual(ref_content.row_names, ["='Test Sheet'!$C$3", "='Test Sheet'!$C$4", "='Test Sheet'!$C$5"])

if __name__ == '__main__':
    unittest.main()