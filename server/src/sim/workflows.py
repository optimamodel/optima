import optima,liboptima # Get everything
from optima import Project,Sim,SimParameter,SimBudget2,ProgramSet # Shortcuts for particular items

selected_workflows = [8,9]

############## 
# Workflow 1 - Initialization

# Initialization - from XLSX
# r = project.Project('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
# r.makeworkbook('../projects/Haiti_Test.xlsx') # Write to a dummy file for test purposes
# r.loadworkbook('../projects/Haiti.xlsx')

# Initialization - from saved sim
P = Project.load_json('./projects/Dedza.json')

############## 
#  Workflow 1a - Save components to share with other users

P.programsets[0].save('example_ccocs.bin')
liboptima.save(P.calibrations[0],'example_parameters.bin')
P.save('myproject.bin')

############## 
# Workflow 2 - Minimal epidemic projection workflow

if 2 in selected_workflows:
	optima.plot(Sim('Example',P))

############## 
# Workflow 3 - Minimal parameter scenarios workflow

if 3 in selected_workflows:
	sim1 = Sim('Base',P)
	sim2 = SimParameter('Test & Treat only',P)
	sim2.create_override(['propaware'],'all',2020,2030,0.9,0.9)
	sim2.create_override(['death'],'all',2015,2030,0.1,0.9)
	optima.plot([sim1,sim2])

############## 
# Workflow 4 - Minimal budget/coverage scenarios workflow

if 4 in selected_workflows:
	sim1 = SimBudget2('Test',P,P.data['origalloc'])
	optima.plot(sim1)

############## 
# Workflow 5 - Minimal optimization workflow

if 5 in selected_workflows:
	sb = P.createsimbox('Opt', isopt = True, createdefault = True)
	P.runsimbox(sb)
	sb.plotallsims()


############## 
# Workflow 6 - Minimal optimization sequence with uncertainties

if 6 in selected_workflows:
	raise Exception('Calibration has not been implemented yet')

############## 
# Workflow 7 - Typical sequence

if 7 in selected_workflows:
	raise Exception('Calibration has not been implemented yet')

############## 
# Workflow 8 - Loading someone else's programs

if 8 in selected_workflows:
	ccocs2 = ProgramSet.load('example_ccocs.bin')
	P.programsets.append(ccocs2)
	sim1 = SimBudget2('Test',P,P.data['origalloc'],programset=ccocs2.uuid)
	optima.plot(sim1)

############## 
# Workflow 9 - Loading someone else's parameters/calibration

if 9 in selected_workflows:
	cal = liboptima.load('example_parameters.bin')
	P.calibrations.append(cal)
	sim1 = SimBudget2('Test',P,P.data['origalloc'],calibration=cal['uuid'])
	optima.plot(sim1)

############## 
# Workflow 10 - Comparing different calibrations

if 10 in selected_workflows:
	raise Exception('Todo')

############## 
# Workflow 10 - Comparing different allocs

if 10 in selected_workflows:
	raise Exception('Todo')

