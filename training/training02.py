"""
Simple calibration for Optima
"""

# Import Optima
from optima import Project, plotpars

# Create the project, load the spreadsheet, and run the model
P = Project(name='My second project', spreadsheet='../tests/concentrated.xlsx')

# Run automatic fitting
P.autofit(name='autofit', orig=0, what=['init','popsize','force','const'], maxtime=120)

# Plot the results
plotpars([P.parsets[0], P.parsets[1]])