import add_optima_paths
import extra_utils
from copy import deepcopy

d1 = {'a':1,'b':2}
d2 = {'b':2,'a':1}
d3 = {'b':3,'a':1}

d4 = {'a':1,'b':2,'c':3}
d5 = {'b':2,'c':3,'a':1}
d6 = {'b':2,'c':[3,4],'a':1}

d7 = [[1,2],[3,4]]
d8 = [[1,2],[3,4]]
d9 = [[1,3],[3,4]]

print extra_utils.dict_equal(d1,d2) # true
print extra_utils.dict_equal(d1,d3) # false
print extra_utils.dict_equal(d4,d5) # true
print extra_utils.dict_equal(d5,d6) # false
print extra_utils.dict_equal(d7,d8) # true
print extra_utils.dict_equal(d8,d9) # false

import region

r = region.Region.load('./regions/Haiti.json');
d1 = r.todict()
d2 = r.todict()
r2 = region.Region.load('./regions/Sudan.json');
d3 = r2.todict()

print extra_utils.dict_equal(d1,d2) # true
print extra_utils.dict_equal(d2,d3) # false


print d1.keys()
print d2.keys()
print d3.keys()
print d4.keys()