import sys
import os
sys.path.append('../tests')
import add_optima_paths
import unittest
import region
import extra_utils

def compare_cached_region(fcn,regenerate = False):
	# This function takes in a function object that returns a region 
	# If cached output
	test_name = fcn.__name__
	test_region = fcn()
	fname = './cache_' + test_name
	if regenerate or fname.replace('./','') not in os.listdir(os.getcwd()): # Test existance more nicely
		# Write to file
		test_region.save(fname)
		return False # Is there a magic value to return to filter the results?
	else:
		previous_region = region.Region.load(fname)
		return extra_utils.dict_equal(test_region.todict(),previous_region.todict())

class TestRegion(unittest.TestCase):

	def test_from_json(self):
		# Test running a simulation from JSON
		def testfcn():
			r = region.Region.load('../tests/regions/Haiti.json')
			r.createsimbox('Simbox 1')
			r.simboxlist[-1].createsim('sim1') 
			r.runsimbox(r.simboxlist[-1])
			return r
		self.assertTrue(compare_cached_region(testfcn))


	# def test_saving_and_loading():
	# 	r = region.Region.load('./regions/Haiti.json') # Load old style JSON
	# 	r.save('./regions/Haiti_newstyle.json')
	# 	r2 = region.Region.load('./regions/Haiti_newstyle.json') # Load new style JSON
	# 	r2.createsimbox('Simbox 1')
	# 	r2.simboxlist[0].createsim('sim1')
	# 	r2.runsimbox(r2.simboxlist[0])
	# 	r2.save('./regions/Haiti_newstyle_withsim.json')
	# 	r3 = region.Region.load('./regions/Haiti_newstyle_withsim.json') # Load new style JSON
	# 	print r
	# 	print r3
	# 	print r3.simboxlist[0].simlist[0].processed

	# def test_from_xlsx():
	# 	# Test running a simulation from XLSX
	# 	r = region.Region('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
	# 	r.makeworkbook('./regions/Haiti_Test.xlsx') # Write to a dummy file for test purposes
	# 	r.loadworkbook('./regions/Haiti.xlsx')
	# 	r.createsimbox('Simbox 1')
	# 	r.simboxlist[0].createsim('sim1') # This is really confusing....
	# 	r.runsimbox(r.simboxlist[0])

	# def test_uncerresults():
	# 	r = test_from_json()
	# 	r.simboxlist[-1].plotallsims()


	# def test_multiresults():
	# 	r = test_from_json()
	# 	r.simboxlist[0].createsim('sim2') # This should really be r.simboxlist.createsim('sim_name') ...
	# 	r.runsimbox(r.simboxlist[0])
	# 	r.simboxlist[0].viewmultiresults()


if __name__ == '__main__':
    unittest.main()