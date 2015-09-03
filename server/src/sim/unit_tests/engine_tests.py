import sys
import os
sys.path.append('../tests')
import add_optima_paths
import unittest
import project
import extra_utils

import os
prepend_path = os.path.dirname(os.path.realpath(__file__)) + '/'

def compare_cached_project(fcn,regenerate = False):
	# This function takes in a function object that generates a saveable
	# object, which must be comparable using dict_equal

	test_name = fcn.__name__
	new_obj = fcn()
	fname = prepend_path + 'cache_' + test_name + '.bin'
	if regenerate or not os.path.isfile(fname): # Test existance more nicely
		# Write to file
		new_obj.save(fname)
		return False # Is there a magic value to return to filter the results?
	else:
		old_obj = project.Project.load(fname)
		return extra_utils.dict_equal(old_obj,new_obj,verbose=True)

class TestProject(unittest.TestCase):

	def test_from_json(self):
		# Test running a simulation from JSON
		def testfcn():
			r = project.Project.load('../tests/projects/Haiti.json')
			# r.createsimbox('Simbox 1')
			# r.simboxlist[-1].createsim('sim1') 
			# r.runsimbox(r.simboxlist[-1])
			return r
		self.assertTrue(compare_cached_project(testfcn))


	# def test_saving_and_loading():
	# 	r = project.Project.load('./projects/Haiti.json') # Load old style JSON
	# 	r.save('./projects/Haiti_newstyle.json')
	# 	r2 = project.Project.load('./projects/Haiti_newstyle.json') # Load new style JSON
	# 	r2.createsimbox('Simbox 1')
	# 	r2.simboxlist[0].createsim('sim1')
	# 	r2.runsimbox(r2.simboxlist[0])
	# 	r2.save('./projects/Haiti_newstyle_withsim.json')
	# 	r3 = project.Project.load('./projects/Haiti_newstyle_withsim.json') # Load new style JSON
	# 	print r
	# 	print r3
	# 	print r3.simboxlist[0].simlist[0].processed

	# def test_from_xlsx():
	# 	# Test running a simulation from XLSX
	# 	r = project.Project('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
	# 	r.makeworkbook('./projects/Haiti_Test.xlsx') # Write to a dummy file for test purposes
	# 	r.loadworkbook('./projects/Haiti.xlsx')
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