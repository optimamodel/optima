"""
Create a good test project

Version: 2016feb11
"""

import optima as op
infile = 'exercise_optimization.prj'
outfile = 'exercise_optimization.prj'
P = op.loadobj(infile)
#P.progsets[0].reconcile(parset=P.parsets[0], year=2016, maxiters=500)
#P = op.saveobj(outfile,P)

P.optimize(maxtime=20)
op.pygui(P.results[-1])