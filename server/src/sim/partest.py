import optima.ccocs as ccocs
import optima
import numpy
from copy import deepcopy
r = optima.Project.load('indonesia.bin')

default = r.data['origalloc']
s1  = optima.Sim('Default',r)
s2  = optima.SimBudget2('Default',r,default)
s2.plot_pars()


