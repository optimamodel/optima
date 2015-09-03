import sys
sys.path.append('..')
import optima
from liboptima.utils import dict_equal
from copy import deepcopy
import unittest
import numpy

class TestDictEqual(unittest.TestCase):

	def test_mismatched_types_str(self):
		d1 = {'a':1}
		d2 = 'a'
		self.assertFalse(dict_equal(d1,d2))

	def test_mismatched_types_tuple(self):
		d1 = {'a':1}
		d2 = {'a':(1,)}
		self.assertFalse(dict_equal(d1,d2))

	def test_skip_uuid(self):
		d1 = {'a':1,'UUID':'1'}
		d2 = {'a':1,'UUID':'2'}
		self.assertTrue(dict_equal(d1,d2))

	def test_empty(self):
		d1 = {'a':1}
		d2 = []
		self.assertFalse(dict_equal(d1,d2))

	def test_mismatched_keys(self):
		d1 = {'a':1}
		d2 = {'b':1}
		self.assertFalse(dict_equal(d1,d2))

	def test_list_basic(self):
		d1 = [1,2,3]
		d2 = [1,2,3]
		self.assertTrue(dict_equal(d1,d2))

	def test_list_basic_false(self):
		d1 = [1,2,3]
		d2 = [1,2,4]
		self.assertFalse(dict_equal(d1,d2))

	def test_list_nested_true(self):
		d1 = [[1,2],[3,4]]
		d2 = [[1,2],[3,4]]
		self.assertTrue(dict_equal(d1,d2))

	def test_list_nested_false(self):
		d1 = [[1,2],[3,4]]
		d2 = [[1,3],[3,4]]
		self.assertFalse(dict_equal(d1,d2))

	def test_list_nested_mismatch(self):
		d1 = [[1,2],[3,4]]
		d2 = [[1,3],[3,4,5]]
		self.assertFalse(dict_equal(d1,d2))

	def test_list_nested_mismatch_levels(self):
		d1 = [[1,2],[3,4]]
		d2 = [[1,3],[3,4,[5]]]
		self.assertFalse(dict_equal(d1,d2))

	def test_nested_basic(self):
		d1 = {'a':1,'b':{'c':1}}
		d2 = {'a':1,'b':{'c':1}}
		self.assertTrue(dict_equal(d1,d2))

	def test_nested_basic_false(self):
		d1 = {'a':1,'b':{'c':1}}
		d2 = {'a':1,'b':{'c':2}}
		self.assertFalse(dict_equal(d1,d2))

	def test_nested_basic_keymismatch(self):
		d1 = {'a':1,'b':{'c':1}}
		d2 = {'a':1,'b':{'d':1}}
		self.assertFalse(dict_equal(d1,d2))

	def test_base_basic(self):
		d1 = {'a':1,'b':2}
		d2 = {'a':1,'b':2}
		self.assertTrue(dict_equal(d1,d2))

	def test_base_basic_false(self):
		d1 = {'a':1,'b':2}
		d2 = {'a':1,'b':3}
		self.assertFalse(dict_equal(d1,d2))

	def test_base_mixed_types(self):
		d1 = {'b':2,'c':[3,4],'a':1}
		d2 = {'b':2,'c':[3,4],'a':1}
		self.assertTrue(dict_equal(d1,d2))

	def test_base_mixed_types_false(self):
		d1 = {'b':2,'c':[3,4],'a':1}
		d2 = {'b':2,'c':[3,5],'a':1}
		self.assertFalse(dict_equal(d1,d2))

	def test_numpy_arrays(self):
		a = numpy.array([1, 2, 3])
		b = numpy.array([1, 2, 3])
		self.assertTrue(dict_equal(a,b))

		a = numpy.array([1, 2, 3])
		b = numpy.array([1, 2, 4])
		self.assertFalse(dict_equal(a,b))

		a = numpy.array([1, 2, 3])
		b = numpy.array([1, 2, 3, 4])
		self.assertFalse(dict_equal(a,b))

		a = numpy.array([[1, 2], [3,4]])
		b = numpy.array([[1, 2], [3,4]])
		self.assertTrue(dict_equal(a,b))

		a = numpy.array([[1, 2], [3,4]])
		b = numpy.array([[1, 2], [3,5]])
		self.assertFalse(dict_equal(a,b))

		a = numpy.array([[1, 2], [3,4]])
		b = numpy.array([[1, 2], [3,5]])
		self.assertFalse(dict_equal(a,b))

		a = numpy.array([[1, 2], [3,4]])
		b = numpy.array([[1, 2,3], [3,5,6]])
		self.assertFalse(dict_equal(a,b))

	def test_basic_nan(self):
		a = numpy.nan
		b = 1
		c = 1.0
		d = numpy.nan
		self.assertTrue(dict_equal(a,d))
		self.assertFalse(dict_equal(a,b))
		self.assertFalse(dict_equal(a,c))

	def test_array_nan(self):
		a = numpy.array([[1, 2], [3,4]])
		b = numpy.array([[1, numpy.nan], [3,4]])
		c = numpy.array([[1, numpy.nan], [3,4]])
		d = numpy.array([[numpy.nan,1], [3,4]])

		self.assertFalse(dict_equal(a,b))
		self.assertTrue(dict_equal(b,c))
		self.assertFalse(dict_equal(c,d))

	# def test_region(self):
	# 	r = region.Region.load('../tests/regions/Haiti.json');
	# 	d1 = r.todict()
	# 	d2 = r.todict()
	# 	r2 = region.Region.load('../tests/regions/Sudan.json');
	# 	d3 = r2.todict()
	# 	self.assertTrue(dict_equal(d1,d2))
	# 	self.assertFalse(dict_equal(d1,d3))
	# 	r.createsimbox('Simbox 1')
	# 	d4 = r.todict()
	# 	self.assertFalse(dict_equal(d1,d4))

if __name__ == '__main__':
    unittest.main()
