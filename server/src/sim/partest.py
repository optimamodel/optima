import optima.ccocs as ccocs
import optima
import numpy
from copy import deepcopy
r = optima.Project.load_json('./projects/Dedza.json')

default = r.data['origalloc']
s1  = optima.Sim('Default',r)
s2  = optima.SimBudget2('Default',r,default)

r.programsets[0]['FSW programs'].plot_single('FSW',sim=s2) # Plot the cost-coverage curve