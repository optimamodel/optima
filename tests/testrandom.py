"""
Create a good test project

Version: 2016feb11
"""

import optima as op
from numpy import array, nan

P = op.defaultproject('best',dorun=False)
P.pars()['proptx'].t[0]= array([0.,2020., 2030.])
P.pars()['proptx'].y[0]= array([nan,.9,.95])
P.pars()['fixpropdx'].y = 2014.
P.pars()['propdx'].t[0]= array([0.,2020., 2030.])
P.pars()['propdx'].y[0]= array([nan,.9,.95])
P.runsim(debug=True)
P.results[-1].export()