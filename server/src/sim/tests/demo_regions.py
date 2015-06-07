# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region

def test_from_json():
	# Test running a simulation from JSON
	r = region.Region.load('./regions/Haiti.json')
	r.createsimbox('Simbox 1')
	r.simboxlist[0].createsim('sim1') 
	r.runsimbox(r.simboxlist[0])
	return r


def test_saving_and_loading():
	r = region.Region.load('./regions/Haiti.json') # Load old style JSON
	r.save('./regions/Haiti_newstyle.json')
	r2 = region.Region.load('./regions/Haiti_newstyle.json') # Load new style JSON
	r2.createsimbox('Simbox 1')
	r2.simboxlist[0].createsim('sim1')
	r2.runsimbox(r2.simboxlist[0])
	r2.save('./regions/Haiti_newstyle_withsim.json')
	r3 = region.Region.load('./regions/Haiti_newstyle_withsim.json') # Load new style JSON
	print r
	print r3
	print r3.simboxlist[0].simlist[0].processed

def test_from_xlsx():
	# Test running a simulation from XLSX
	r = region.Region('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
	r.makeworkbook('./regions/Haiti_Test.xlsx') # Write to a dummy file for test purposes
	r.loadworkbook('./regions/Haiti.xlsx')
	r.createsimbox('Simbox 1')
	r.simboxlist[0].createsim('sim1') # This is really confusing....
	r.runsimbox(r.simboxlist[0])

def test_uncerresults():
	r = test_from_json()
	r.simboxlist[0].plotallsims()


def test_multiresults():
	r = test_from_json()
	r.simboxlist[0].createsim('sim2') # This should really be r.simboxlist.createsim('sim_name') ...
	r.runsimbox(r.simboxlist[0])
	r.simboxlist[0].viewmultiresults(r.metadata)

test_saving_and_loading()
test_from_json()
test_from_xlsx()
test_uncerresults()
test_multiresults()
