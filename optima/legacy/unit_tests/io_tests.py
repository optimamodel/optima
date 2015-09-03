import sys
sys.path.append('../tests')
import add_optima_paths
from extra_utils import dict_equal
import unittest
import numpy
import dataio_binary

class TestDataIO(unittest.TestCase):

	def test_basic(self):
		x = 1
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_list(self):
		x = [2]
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_tuple(self):
		x = (3)
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_mixed(self):
		x = [(3),[4]]
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_numpy_float(self):
		x = numpy.float64(1)
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_numpy_array(self):
		x = numpy.array([1,2,3])
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_numpy_nan(self):
		x = numpy.nan
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_numpy_array_nan(self):
		x = numpy.array([1,numpy.nan,2])
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

	def test_none(self):
		x = None
		dataio_binary.save(x,'./cache.json')
		y = dataio_binary.load('./cache.json')
		self.assertTrue(dict_equal(x,y,verbose=True))

if __name__ == '__main__':
    unittest.main()