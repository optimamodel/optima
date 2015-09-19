import optima.ccocs as ccocs
import optima
import numpy
from copy import deepcopy
r = optima.Project.load_json('./projects/Dedza.json')

default = r.data['origalloc']
s1  = optima.Sim('Default',r)
s2  = optima.SimBudget2('Default',r,default)

# s2.program_end_year = 2020
# s2.budget[0,:] = numpy.linspace(1,1e6,len(r.options['partvec']))
#r.programsets[0]['FSW programs'].coverage_outcome['FSW']['condomcom'].fe_params = [0.975,0.975,1,1]

r.programsets[0]['FSW programs'].plot(sim=s2) # Plot the cost-coverage curve