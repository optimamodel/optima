import sys
sys.path.append('../tests')
import add_optima_paths
from dataio import tojson,fromjson,savedata,loaddata
from extra_utils import dict_equal
import unittest
import numpy

class TestDataIO(unittest.TestCase):

	def test_basic(self):
		x = 1
		savedata('./cache.json',x)
		y = loaddata('./cache.json',x)
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_list(self):
		x = [2]
		savedata('./cache.json',x)
		y = loaddata('./cache.json',x)
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_tuple(self):
		x = (3)
		savedata('./cache.json',x)
		y = loaddata('./cache.json',x)
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_mixed(self):
		x = [(3),[4]]
		savedata('./cache.json',x)
		y = loaddata('./cache.json',x)
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_numpy_float(self):
		x = numpy.float64(1)
		savedata('./cache.json',x)
		y = loaddata('./cache.json',x)
		self.assertTrue(dict_equal(x,y,verbose=True))

if __name__ == '__main__':
    unittest.main()