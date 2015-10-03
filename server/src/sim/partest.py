import optima.ccocs as ccocs
import optima
import numpy
from copy import deepcopy
r = optima.Project.load_json('./projects/Malawi 150820.json')
#r = optima.Project.load_json('./projects/Dedza.json')

s  = optima.SimBudget2('Default',r)

# s.program_end_year = 2020
# s.budget[0,:] = numpy.linspace(1,1e6,len(r.options['partvec']))
# r.programsets[0]['FSW programs'].coverage_outcome['FSW']['condomcom'].fe_params = [0.975,0.975,1,1]

r.programsets[0]['ART'].plot(sim=s) # Plot the cost-coverage curve