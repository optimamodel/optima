import optima.ccocs as ccocs
import optima

r = optima.Project.load_json('projects/Dedza.json')

########## PLOTTING PROGRAMS
# There are many different options for plotting programs
# Recall that a programset contains programs that contain CCOCs pointing
# at various populations and parameters
# This example is designed to work with Dedza.json

# First, shorten the variable name by making a reference to the programset

pset = r.programsets[0] 

# First, consider the plots that could be made for FSW programs
# that affect condomcom in population FSW. This happens to be program 1
# in the list of programs. So we can do the following
pset.programs[1].plot_single('FSW') # Plot the cost-coverage curve
pset.programs[1].plot_single('FSW','condomcom') # Plot the coverage-outcome curve
pset.programs[1].plot_single('FSW','condomcom',cco=True) # Plot the cost-coverage-outcome curve

# The ProgramSet class has overloaded indexing, which enables programs to be accessed as though
# the ProgramSet was a dictionary. So instead of the above, we can do exactly the same thing with
pset['FSW programs'].plot_single('FSW','condomcom',cco=True) # Plot the cost-coverage-outcome curve
# This works because pset.programs[1].name == 'FSW programs'

# Now, we might want to plot all of the curves associated with a program. For this, use
pset['FSW programs'].plot()

########## PLOTTING PROGRAMSETS
# programset plotting is about superimposing programs that have overlapping coverage or effects
# Since legacy programs have no overlap, we need to artifically create some to demonstrate plotting
# Let's pretend that MSM programs somehow cover FSW and affect FSW-condomcom

pset['MSM programs'].cost_coverage['FSW'] = pset['MSM programs'].cost_coverage['MSM']
pset['MSM programs'].coverage_outcome['FSW']['condomcom'] = pset['MSM programs'].coverage_outcome['MSM']['condomcas']

# Now we can make some plots

pset.plot('FSW') # Superimpose programs covering FSW
pset.plot('FSW','condomcom') # Superimpose coverage-outcome curves for FSW-condomcom
pset.plot('FSW','condomcom',cco=True) # Superimpose cost-coverage-outcome curves for FSW-condomcom
pset.plot('Overall') # Superimpose coverage programs
