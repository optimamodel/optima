# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import sys
sys.path.append('../tests')
import add_optima_paths
import defaults
import region
import sim

r = region.Region.load('./regions/lilongwe.json')
s = sim.Sim('Base',r)
s.run()
s.plotresults()
