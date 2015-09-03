import optima
import liboptima.utils
from timevarying import timevarying
import numpy
r = optima.Project.load_json('./projects/Dedza.json')

# This function tests the program calculation
r.save('asdf.bin')
r = optima.Project.load('asdf.bin')

# Make an example budget from the default allocation
a = r.D['data']['origalloc']
budget = timevarying(a,nprogs=len(a), tvec=r.options['partvec'], totalspend=sum(a))


# Make a second programset, for fun
s1 = optima.SimBudget('SimBudget',r,budget)
s2 = optima.SimBudget2('SimBudget2',r,budget)

optima.plot([s1,s2])

# s1.initialise()
# s2.initialise()
# liboptima.utils.dict_equal(s1.parsmodel,s2.parsmodel,True)

# pset = r.fetch(s2.programset)

# s1.run()
# sb = optima.SimBox('Plot',r)
# sb.simlist = [s1,s2]
# sb.runallsims()
# sb.viewmultiresults()
