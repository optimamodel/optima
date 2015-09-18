import optima,liboptima
from timevarying import timevarying
from copy import deepcopy
import numpy

r = optima.Project.load_json('./projects/Dedza.json')

print [x['short_name'] for x in r.metadata['inputprograms']]

# default = r.data['origalloc']
# nothing = numpy.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
# #art_only = deepcopy(default)
# art_only = deepcopy(nothing)
# art_only[4] = default[4];

# no_art = deepcopy(default)
# no_art[4] = 0
s  = optima.SimBudget2('Default',r,default)
s2 = optima.SimBudget2('ART only',r,art_only)
s3 = optima.SimBudget2('No ART',r,no_art)
s4 = optima.SimBudget2('Nothing',r,nothing)

s.run()
s2.run()
s3.run()
s4.run()

# optima.plot([s,s2,s3,s4])
# for prog in r.programsets[0].programs:
# 	prog.plot()