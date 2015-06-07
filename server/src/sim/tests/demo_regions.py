# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region

r = region.Region('test',defaults.pops,defaults.progs,defaults.datastart,defaults.dataend)

haiti = region.Region('Haiti',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])

haiti.makeworkbook('./regions/Haiti_Test.xlsx')
haiti.loadworkbook('./regions/Haiti.xlsx')

r.loadDfrom('./regions/Haiti.json')
r.createsimbox('Simbox 1')
r.runsimbox(r.simboxlist[0])
