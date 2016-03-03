"""
Simple calibration for Optima
"""

# Import Optima
from optima import Project, plotresults, plotpars, pygui

# Create the project, load the spreadsheet, and run the model
P = Project(name='My second project', spreadsheet='../tests/concentrated.xlsx')

# Run automatic fitting
P.autofit(name='autofit', orig=0, what=['force'], maxtime=60)

# Plot the results
plotresults(P.results[0]) # Default parameters
pygui(P.results[1]) # Automatic calibration
#plotpars([P.parsets[0], P.parsets[1]])

