"""
Training wheels for Optima.
"""

# Import Optima
from optima import Project, plotresults, saveobj

# Create the project, load the spreadsheet, and run the model
P = Project(name='My first project', spreadsheet='../tests/simple.xlsx')

# Plot the results
plotresults(P.results[0])

# Print information about the project
print(P)

# Save the project
saveobj('MyFirstProject.prj',P)