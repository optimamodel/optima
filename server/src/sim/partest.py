import optima.ccocs as ccocs
import optima
import numpy
from copy import deepcopy
r = optima.Project.load_json('./projects/georgia_working.json')

default = r.data['origalloc']
s1  = optima.Sim('Default',r)
s2  = optima.SimBudget2('Default',r,default)

r.programsets[0]['FSW programs'].coverage_outcome['FSW']['condomcom'].fe_params = [0.95,0.95,1,1]
r.programsets[0]['FSW programs'].plot(sim=s2) # Plot the cost-coverage curve