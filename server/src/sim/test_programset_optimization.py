import optima,liboptima
from timevarying import timevarying

# r = optima.Project.load_json('./projects/Dedza.json')
# r.save('asdf.bin')
r = Project.load('asdf.bin')
s = optima.SimBudget2('Example',r,r.D['data']['origalloc']) # Make a sim, implicitly selecting a calibration and programset/ccocs
opt = optima.Optimization('Demo',r,s) # You have to pass in a Sim so that the optimization knows which calibration and programset/ccocs to use
opt.optimize()
optima.plot([opt.initial_sim,opt.optimized_sim])
