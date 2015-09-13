import optima,liboptima
from timevarying import timevarying

# Define a function to run optimize
def do_optimize(inputs):
	r = inputs[0]
	simbox_uuid = inputs[1]
	sb = r.fetch(simbox_uuid)

	# Run the SimBox depending on what type it is
	if isinstance(sb,optima.Optimization):
		sb.optimize(timelimit = 180)
	else:
		optbudget, optobj, optimized_sim = sb.optimise(sb.simlist[0], makenew = True, inputmaxiters = 1e3, inputtimelimit = 180)
	return r

if __name__ == "__main__":
	#Load the region
	r = optima.Project.load_json('./projects/Dedza.json')

	# Make the new optimization
	opt = optima.Optimization('Example',r,calibration=r.calibrations[0],programset=r.programsets[0],initial_alloc=r.D['data']['origalloc']) # Make a sim, implicitly selecting a calibration and programset/ccocs
	r.simboxlist.append(opt)

	# Make the old optimization
	sb = r.createsimbox('Legacy', isopt = True, createdefault = True)

	# Use the parallel_execute_simboxes method to run do_optimize() in parallel
	r.parallel_execute_simboxes(do_optimize,[opt,sb])

	## Use the lines below to save cached output so that the optimizations can be examined without recomputing each time
	# r.save('optim_test.bin')
	# r = optima.Project.load('optim_test.bin')
	# opt = r.simboxlist[0]
	# sb = r.simboxlist[1]

	print sum(opt.initial_alloc)
	print sum(opt.optimized_alloc)
	print sum(sb.simlist[0].alloc)
	print sum(sb.simlist[-1].alloc)

	optima.plot([opt.initial_sim,opt.optimized_sim,sb.simlist[0],sb.simlist[-1]])

