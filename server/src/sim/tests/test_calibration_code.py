# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region
import sim
import simbox

# r1 = region.Region.load('./regions/georgia_working.json')
# sb0 = r1.createsimbox('Original', isopt = False, createdefault = True)
# r1.runsimbox(sb0)
# r1.save('./calibration_old.json')

# print 'LOADING OLD DATA'
original = region.Region.load('calibration_old.json')
print 'LOADING LEGACY DATA FOR NEW RUN'
r = region.Region.load('./regions/georgia_working.json')
sb = r.createsimbox('New', isopt = False, createdefault = True)
r.runsimbox(sb)

sb2 = simbox.SimBox('ASDF',r)
sb2.simlist = [r.simboxlist[1].simlist[0],original.simboxlist[1].simlist[0]]
sb2.viewmultiresults()
# s = sim.Sim('test1',r);
# s.run()
# s.plotresults()

# sb = simbox.SimBox('wrapper',r)
# sb.simlist = [s,s]
# sb..viewmultiresults()