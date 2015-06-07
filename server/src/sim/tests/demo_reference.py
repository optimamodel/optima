# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import defaults
import region

r = region.Region('Haiti (from JSON)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
r.loadDfrom('./regions/Haiti.json')
r.createsimbox('Simbox 1')
r2 = r
r2.createsimbox('Simbox 2')
print r
print r2

# Both r and r2 now have 2 simboxes. This means only one copy of the region
# exists in memory. We could store a member variable
# sim.parent_region = r
# or 
# sim.parent_region = 
# (see https://docs.python.org/2/library/weakref.html)
# Which would make the simobjects standalone and would probably make the code
# significantly neater without adding to the memory demands of the code
# Saving and loading simulations would be a bit more tricky though - we should
# think carefully about that