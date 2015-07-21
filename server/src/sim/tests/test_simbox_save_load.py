import add_optima_paths
import defaults
import region
import sim
import simbox

r = region.Region.load('./regions/indonesia_bali.json')
r.createsimbox('normal',isopt = False, createdefault = False)
r.createsimbox('opt',isopt = True, createdefault =  False)
r.save('./test.json')
print r.simboxlist
r2 = region.Region.load('./test.json')
print r2.simboxlist