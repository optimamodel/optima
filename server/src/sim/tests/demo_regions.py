# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region

r = region.Region('test',defaults.pops,defaults.progs,defaults.datastart,defaults.dataend)
r.loadDfrom('./regions/Haiti.json')
r.createsimbox('Simbox 1')
r.runsimbox(r.simboxlist[0])
