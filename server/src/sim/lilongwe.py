# This demonstration creates a project, saves a corresponding XLSX file
# and then loads it back again
import sys
sys.path.append('../tests')
import add_optima_paths
import defaults
import project
import sim

r = project.Project.load('./projects/lilongwe.json')
s = sim.Sim('Base',r)
s.run()
s.plotresults()
