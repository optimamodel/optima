import unittest

class TestPrograms(unittest.TestCase):

    def test_programs_for_input_key(self):
        from programs import programs_for_input_key
        result = programs_for_input_key('condomcas')
        self.assertTrue('MSM programs' in result.keys())
        self.assertTrue(result['MSM programs'] == ['MSM'])

if __name__ == '__main__':
    unittest.main()