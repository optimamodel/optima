# This test loads an XLSX file
import sys
sys.path.append('../tests')
import add_optima_paths
import defaults
import region

r = region.Region('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
r.loadworkbook('./regions/Haiti.xlsx')
r.createsimbox('Simbox 1')
r.simboxlist[0].createsim('sim1') # This is really confusing....
r.runsimbox(r.simboxlist[0])