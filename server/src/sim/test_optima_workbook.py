import os
import unittest
from optima_workbook import OptimaWorkbook

class TestOptimaWorkbook(unittest.TestCase):
  def test_create_workboook_with_defaults(self):
    populations = ['General males', 'General females', 'Female sex workers']
    programs = ['Behavior change', 'Needle-syringe program', 'HIV counseling and testing']
    book = OptimaWorkbook('test_example', populations, programs)
    path = '/tmp/test_example.xlsx'
    if os.path.exists(path):
      os.remove(path)
    book.create(path)
    self.assertTrue(os.path.exists('/tmp/test_example.xlsx'))


if __name__ == '__main__':
    unittest.main()