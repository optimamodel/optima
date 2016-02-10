"""
Do random tests.

Version: 2016feb09
"""

from pylab import ones, shape, array

import optima as op
P = op.defaults.defaultproject('best')
progset = P.progsets[0]
parset = P.parsets[0]
year = 2015
#P.progsets[0].reconcile(parset=P.parsets[0], year=2016)

modpars = progset.cco2odict(t=year)
output1 = progset.compareoutcomes(parset=parset, year=year, doprint=True)
pararray = modpars[:]
factors = ones((shape(pararray)[0],1))
factors += 0.5
newmodpars = op.dcp(modpars)
newmodpars[:] = pararray*factors
progset.odict2cco(newmodpars)
output2 = progset.compareoutcomes(parset=parset, year=year, doprint=True)

outarr1 =  array(array(output1,dtype=object)[:,-1],dtype=float)
outarr2 =  array(array(output2,dtype=object)[:,-1],dtype=float)

