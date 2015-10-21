import optima,liboptima
from timevarying import timevarying

# Convert project from google drive format to new binary format
# r = optima.Project.load_json('./projects/georgia-apr14-optim.json')
# r.save('./projects/georgia.bin')

# Initialize the objects
# TODO - could be refined by automatic fetching

initialize = False

def plot_optimization(project_uuid,optimization_uuid):
	r = optima.Project.load_db(project_uuid)
	opt = r.load_simbox(optimization_uuid)
	optima.plot([opt.initial_sim,opt.optimized_sim])
	return

def plot_simbox(project_uuid,simbox_uuid):
	r = optima.Project.load_db(project_uuid)
	sb = r.load_simbox(simbox_uuid)
	print r.simboxlist
	optima.plot(sb.simlist)
	return


if initialize:
	optima.db.makedb()

	r = optima.Project.load_json('./projects/Dedza.json')
	sb = r.createsimbox('test')
	sb.runallsims()
	sb2 = r.createsimbox('test2')
	sb2.runallsims()

	opt = optima.Optimization('Example',r,calibration=r.calibrations[0],programset=r.programsets[0],initial_alloc=r.data['origalloc']) # Make a sim, implicitly selecting a calibration and programset/ccocs
	opt.optimize(timelimit = 5)
	r.simboxlist.append(opt)

	r.save('demo_database_project.bin') # Save the database to a file
	r.save_db(save_all=True) # Save the project to the database

else:
	# Load the binary file, to show it works
	r1 = optima.Project.load('demo_database_project.bin')
	sb_uuids = [sb.uuid for sb in r1.simboxlist]

	print r1.simboxlist

	#print r1.uuid
	#print r1.simboxlist[0].uuid
	plot_simbox(r1.uuid,r1.simboxlist[0].uuid)
	#plot_optimization(r1.uuid,r1.simboxlist[-1].uuid)

	#optima.plot([r1.simboxlist[-1].initial_sim,r1.simboxlist[-1].optimized_sim])

