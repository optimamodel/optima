import add_optima_paths
import program
import region
import sim
import numpy
from timevarying import timevarying
import programset
import simbox

# This function tests the program calculation
# r = region.Region.load_json('./regions/Dedza.json')
# r.save('asdf.bin')
r = region.Region.load('asdf.bin')

# Make an example budget from the default allocation
a = r.D['data']['origalloc']
budget = timevarying(a,nprogs=len(a), tvec=r.options['partvec'], totalspend=sum(a))

# Make a second programset, for fun
r.programsets.append(programset.ProgramSet.import_legacy('New',r.metadata['programs']))
s1 = sim.SimBudget('SimBudget',r,budget)
s2 = sim.SimBudget2('SimBudget2',r,budget,programset=r.programsets[1].uuid)

s1.initialise()
s2.initialise()
from extra_utils import dict_equal
dict_equal(s1.parsmodel,s2.parsmodel,True)
s1.run()
sb = simbox.SimBox('Plot',r)
sb.simlist = [s1,s2]
sb.runallsims()
sb.viewmultiresults()