import optima,liboptima
from timevarying import timevarying

# This function tests the program calculation
#r = optima.Project.load_json('./projects/Dedza.json')
r = optima.Project.load_json('tests/regions/projects/georgia_working.json')

# Loading binary files is faster, so uncomment below to save and then use
# a binary project
# r.save('asdf.bin')
#r = Project.load('asdf.bin')

# Make an example budget from the default allocation
a = r.D['data']['origalloc']
budget = timevarying(a,nprogs=len(a), tvec=r.options['partvec'], totalspend=sum(a))

# Make a second programset, for fun
r.programsets.append(optima.ProgramSet.import_legacy('New',r.metadata['programs']))

# Create some Sims
s1 = optima.SimBudget('SimBudget',r,budget)
s2 = optima.SimBudget2('SimBudget2',r,budget,programset=r.programsets[1].uuid)

# Compare their model parameters
s1.initialise()
s2.initialise()
liboptima.utils.dict_equal(s1.parsmodel,s2.parsmodel,True)

# Retrieve the programs/CCOCs used by a particular Sim
pset = r.fetch(s2.programset)

# Run the simulations and plot their outputs
optima.plot([s1,s2])