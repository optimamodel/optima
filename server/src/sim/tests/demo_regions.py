# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region

# Test running a simulation from JSON
r = region.Region('Haiti',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
r.loadDfrom('./regions/Haiti.json')
r.createsimbox('Simbox 1')
r.runsimbox(r.simboxlist[0])

# Test running a simulation from XLSX
r2 = region.Region('Haiti',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
r2.makeworkbook('./regions/Haiti_Test.xlsx') # Write to a dummy file for test purposes
r2.loadworkbook('./regions/Haiti.xlsx')
r2.createsimbox('Simbox 1')
r2.runsimbox(r2.simboxlist[0])