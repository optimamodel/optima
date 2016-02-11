"""
Create a good test project

Version: 2016feb11
"""

import optima as op
filename = '/u/cliffk/unsw/optima/tests/exercise_optimization.prj'
P = op.loadobj(filename)
P.progsets[0].reconcile(parset=P.parsets[0], year=2016)

P.optimize(maxtime=20)
op.pygui(P.results[-1])