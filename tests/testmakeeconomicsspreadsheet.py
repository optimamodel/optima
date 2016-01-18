import os
import unittest
from optima.makespreadsheet import EconomicsSpreadsheet

class TestOptimaSpreadsheet(unittest.TestCase):

    def test_create_spreadsheet_with_defaults(self):
        import xlrd
        book = EconomicsSpreadsheet('testeconomics')
        path = '/tmp/testeconomics.xlsx'
        if os.path.exists(path):
          os.remove(path)
        book.create(path)
        self.assertTrue(os.path.exists('/tmp/testeconomics.xlsx'))
        workbook = xlrd.open_workbook(path)
        for name, value in book.sheet_names.iteritems():
            self.assertTrue(workbook.sheet_by_name(value) is not None)


if __name__ == '__main__':
    unittest.main()