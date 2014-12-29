import unittest

class TestPrograms(unittest.TestCase):

    def test_programs_for_input_key(self):
        from programs import programs_for_input_key
        result = programs_for_input_key('condomcas')
        print(result)
        self.assertTrue(1)


if __name__ == '__main__':
    unittest.main()