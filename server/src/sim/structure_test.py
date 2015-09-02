import optima
import liboptima.utils
from timevarying import timevarying

r = optima.Region.load_json('./regions/Dedza.json')

# This function tests the program calculation
r.save('asdf.bin')
r = optima.Region.load('asdf.bin')

# Make an example budget from the default allocation
a = r.D['data']['origalloc']
budget = timevarying(a,nprogs=len(a), tvec=r.options['partvec'], totalspend=sum(a))

# Make a second programset, for fun
r.programsets.append(optima.ProgramSet.import_legacy('New',r.metadata['programs']))
s1 = optima.SimBudget('SimBudget',r,budget)
s2 = optima.SimBudget2('SimBudget2',r,budget,programset=r.programsets[1].uuid)

s1.initialise()
s2.initialise()
liboptima.utils.dict_equal(s1.parsmodel,s2.parsmodel,True)

pset = r.fetch(s2.programset)

s1.run()
sb = optima.SimBox('Plot',r)
sb.simlist = [s1,s2]
sb.runallsims()
sb.viewmultiresults()
