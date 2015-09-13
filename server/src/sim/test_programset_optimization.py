import optima,liboptima
from timevarying import timevarying

# r = optima.Project.load_json('./projects/Dedza.json')
# r.save('asdf.bin')
r = optima.Project.load('asdf.bin')
opt = optima.Optimization('Example',r,calibration=r.calibrations[0],programset=r.programsets[0],initial_alloc=r.D['data']['origalloc']) # Make a sim, implicitly selecting a calibration and programset/ccocs
opt.optimize(timelimit = 5)
optima.plot([opt.initial_sim,opt.optimized_sim])
