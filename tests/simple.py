"""
The simplest possible test of Optima.
"""

import optima as op
P = op.defaultproject()
P.runsim()
op.pygui(P)