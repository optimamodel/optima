# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region
import sim

def create_scenarios():
	r = region.Region.load('./regions/georgia_working.json')

	# Make the simulations
	sim1 = sim.Sim('Base',r)
	sim2 = sim.SimParameter('Test & Treat only',r)
	sim2.create_override(['propaware'],'all',2015,2030,0.6,0.9)
	sim2.create_override(['txtotal'],'all',2015,2030,0.4,0.81)

	# Put them in a simbox, run them, and plot results

	sbox.runallsims()
	sbox.viewmultiresults()

def save_and_load_scenarios():
	r = region.Region.load('./regions/georgia_working.json')
	r.simboxlist = []
	sim1 = sim.Sim('Base',r)
	sim2 = sim.SimParameter('Test & Treat only',r)
	sim2.create_override(['propaware'],'all',2015,2030,0.6,0.9)
	sbox = r.createsimbox('Test scenarios')
	sbox.simlist = [sim1,sim2]
	r.save('./regions/georgia_working_updated.json')
	r2 = region.Region.load('./regions/georgia_working_updated.json')

	print r.simboxlist[0].simlist[0]
	print r.simboxlist[0].simlist[1]
	print r2.simboxlist[0].simlist[0]
	print r2.simboxlist[0].simlist[1]
	print r.simboxlist[0].simlist[1].parameter_overrides[0]
	print r2.simboxlist[0].simlist[1].parameter_overrides[0]

	#sbox = r.simboxlist[0]
	#sbox.runallsims()
	#sbox.viewmultiresults()

def run_existing():
	r = region.Region.load('./regions/georgia_working.json')
	sbox = r.simboxlist[0]
	sbox.runallsims()
	sbox.viewmultiresults()

#save_and_load_scenarios()
run_existing()