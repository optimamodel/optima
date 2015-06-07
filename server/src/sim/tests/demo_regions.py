# This demonstration creates a region, saves a corresponding XLSX file
# and then loads it back again
import add_optima_paths
import region

import defaults
r = region.Region('test',defaults.pops,defaults.progs,defaults.datastart,defaults.dataend)
