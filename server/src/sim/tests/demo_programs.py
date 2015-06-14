import add_optima_paths
import program
import region
import sim
r = region.Region.load('./regions/georgia_working.json')
s = sim.SimBudget2('Test',r)

print s.program_set
print s.budget