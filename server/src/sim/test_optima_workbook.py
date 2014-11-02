import os
import unittest
from optima_workbook import OptimaWorkbook

class TestOptimaWorkbook(unittest.TestCase):
  def test_create_workboook_with_defaults(self):
    book = OptimaWorkbook('test_example')
    path = '/tmp/test_example.xlsx'
    if os.path.exists(path):
      os.remove(path)
    book.create(path)
    self.assertTrue(os.path.exists('/tmp/test_example.xlsx'))


if __name__ == '__main__':
    unittest.main()