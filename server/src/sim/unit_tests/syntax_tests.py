# This script just runs various commands to ensure that the syntax isn't broken
# and that commands run to completion without fatal errors
# Tests in here perform minimal, if any, validation of variable values

import sys
sys.path.append('..')
import unittest
import numpy
import optima, liboptima
from optima import Project,Sim,SimParameter,SimBudget2,ProgramSet # Shortcuts for particular items
from liboptima.utils import dict_equal

P = Project.load_json('../projects/Dedza.json')
P.save('test_temp_project.bin')

class TestSyntax(unittest.TestCase):

	def test_portfolio_save_load(self):
		r1 = optima.Project.load_json('../projects/Dedza.json')
		r2 = optima.Project.load_json('../projects/Dowa.json')
		tempsimbox1 = r1.createsimbox('GPA1', isopt = True, createdefault = True)
		tempsimbox2 = r2.createsimbox('GPA2', isopt = True, createdefault = True)
		
		p1 = optima.Portfolio('test')
		p1.appendproject(r1)
		p1.appendproject(r2)
		p1.gpalist = [tempsimbox1,tempsimbox2]
		print p1.gpalist
		p1.save('cache.bin')
		p2 = optima.Portfolio.load('cache.bin')
		print p2.gpalist

	def test_saving_and_loading(self):
		r = optima.Project.load_json('../projects/Dedza.json') # Load old style JSON
		r.save_json('../projects/Dedza_newstyle.json')
		r2 = optima.Project.load_json('../projects/Dedza_newstyle.json') # Load new style JSON
		r2.createsimbox('Simbox 1')
		r2.simboxlist[0].createsim('sim1')
		r2.runsimbox(r2.simboxlist[0])
		r2.save('../projects/Dedza_newstyle_withsim.bin')
		r3 = optima.Project.load('../projects/Dedza_newstyle_withsim.bin') # Load new style JSON
		print r
		print r3
		print r3.simboxlist[0].simlist[0].processed

	def test_saving_and_loading_binary(self):
		r = optima.Project.load_json('../projects/Dedza.json') # Load old style JSON
		r.save('../projects/Dedza_newstyle.bin')
		r2 = optima.Project.load('../projects/Dedza_newstyle.bin') # Load new style JSON
		r2.createsimbox('Simbox 1')
		r2.simboxlist[0].createsim('sim1')
		r2.runsimbox(r2.simboxlist[0])
		r2.save('../projects/Dedza_newstyle_withsim.bin')
		r3 = optima.Project.load('../projects/Dedza_newstyle_withsim.bin') # Load new style JSON
		print r
		print r3
		print r3.simboxlist[0].simlist[0].processed

		# Test sim.viewuncerresults
		r3.simboxlist[0].simlist[0].plotresults(show_wait=False)

		# Test simbox.viewmultiresults
		r3.simboxlist[0].createsim('sim2') # This should really be r.simboxlist.createsim('sim_name') ...
		r3.runsimbox(r3.simboxlist[0])
		r3.simboxlist[0].viewmultiresults(show_wait=False)

	### EXAMPLE WORKFLOWS

	def test_1(self): #  Workflow 1a - Save components to share with other users
		P = Project.load('test_temp_project.bin')
		P.programsets[0].save('example_ccocs.bin')
		liboptima.save(P.calibrations[0],'example_parameters.bin')
		P.save('myproject.bin')
		
	def test_2(self): # Workflow 2 - Minimal epidemic projection workflow
		P = Project.load('test_temp_project.bin')
		optima.plot(Sim('Example',P),show_wait=False)	

	def test_3(self):	# Workflow 3 - Minimal parameter scenarios workflow
		P = Project.load('test_temp_project.bin')
		sim1 = Sim('Base',P)
		sim2 = SimParameter('Test & Treat only',P)
		sim2.create_override(['propaware'],'all',2020,2030,0.9,0.9)
		sim2.create_override(['death'],'all',2015,2030,0.1,0.9)
		optima.plot([sim1,sim2],show_wait=False)	

	def test_4(self):	# Workflow 4 - Minimal budget/coverage scenarios workflow
		P = Project.load('test_temp_project.bin')
		sim1 = SimBudget2('Test',P,P.data['origalloc'])
		optima.plot(sim1,show_wait=False)	

	def test_5(self):	# Workflow 5 - Minimal optimization workflow
		P = Project.load('test_temp_project.bin')
		sb = P.createsimbox('Opt', isopt = True, createdefault = True)
		P.runsimbox(sb)
		sb.plotallsims(show_wait=False)

	def test_8(self): # Workflow 8 - Loading someone else's programs
		P = Project.load('test_temp_project.bin')
		ccocs2 = ProgramSet.load('example_ccocs.bin')
		P.programsets.append(ccocs2)
		sim1 = SimBudget2('Test',P,P.data['origalloc'],programset=ccocs2.uuid)
		optima.plot(sim1,show_wait=False)

	def test_9(self): # Workflow 9 - Loading someone else's parameters/calibration
		P = Project.load('test_temp_project.bin')
		cal = liboptima.load('example_parameters.bin')
		P.calibrations.append(cal)
		sim1 = SimBudget2('Test',P,P.data['origalloc'],calibration=cal['uuid'])
		optima.plot(sim1,show_wait=False)

	def test_optimization_from_sim(self): # Workflow 9 - Loading someone else's parameters/calibration
		r = optima.Project.load_json('./projects/Dedza.json')
		opt = optima.Optimization('Example',r,calibration=r.calibrations[0],programset=r.programsets[0],initial_alloc=r.data['origalloc']) # Make a sim, implicitly selecting a calibration and programset/ccocs
		opt.optimize(timelimit = 5)
		optima.plot([opt.initial_sim,opt.optimized_sim],show_wait=False)

	def test_optimization_from_pset_and_cal(self): # Workflow 9 - Loading someone else's parameters/calibration
		r = optima.Project.load_json('./projects/Dedza.json')
		s = optima.SimBudget2('test',r)
		opt = optima.Optimization('Example',r,sim=s)
		opt.optimize(timelimit = 5)
		optima.plot([opt.initial_sim,opt.optimized_sim],show_wait=False)



	# def test_from_xlsx(self):
	# 	# Test running a simulation from XLSX
	# 	r = project.Project('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
	# 	r.makeworkbook('../projects/Haiti_Test.xlsx') # Write to a dummy file for test purposes
	# 	r.loadworkbook('../projects/Haiti.xlsx')
	# 	r.createsimbox('Simbox 1')
	# 	r.simboxlist[0].createsim('sim1') # This is really confusing....
	# 	r.runsimbox(r.simboxlist[0])

	

if __name__ == '__main__':
    unittest.main()