# This function calls viewuncerresults if given a Sim
# It calls viewuncerresults if given a list of Sims with more than 1 Sim
import sim
import simbox

def plot(sims):
	# Put a lone sim into a list
	if isinstance(sims,sim.Sim):
		sims = [sims]

	# If the sim hasn't been run, then run the sim
	for s in sims:
		if not s.processed:
			print "Sim %s has not been run - doing it now" % (s.name)
			s.run()

	if len(sims) == 1:
		sims[0].plotresults()
	else:
		# You can't just use viewmultiresults, a lot of tempD stuff is contained in SimBox
		# So we just make the plot via a SimBox - makes no difference to the user anyway
		sbox = simbox.SimBox('temp',sims[0].getproject()) 
		sbox.simlist = sims
		sbox.viewmultiresults()

