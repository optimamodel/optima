"""
Version:
"""
import optima as op
from pylab import *

start = 2000.
end = 2020.
year = 2015.0

print('####################DEMO###########################')
P = op.demo(0)

#P.pars()['numvlmon'].y[:] *= 0 # Uncomment this out to watch the discrepancy (almost) completely disappear...

#P.settings.dt = 0.02 # If timestep is smaller, the discrepancy is proportionally smaller

print('####################FIRST RUN###########################')
t = op.tic()
res1 = op.runmodel(project=P, pars=P.pars(), start=start, end=end, keepraw=True)
op.toc(t)

ind = op.findinds(res1.raw[0]['tvec'], year)
initpeople = res1.raw[0]['people'][:,:,ind]

print('####################SECOND RUN###########################')

t = op.tic()
res2 = op.runmodel(project=P, pars=P.pars(), start=year, end=end, keepraw=True, initpeople=initpeople)
op.toc(t)


z=1
print('max difference between model runs at first timestep, should be 0:')
print((res1.raw[0]['people'][:,:,ind+z]-res2.raw[0]['people'][:,:,array([0+z])]).squeeze().max())