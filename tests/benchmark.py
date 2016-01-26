"""
BENCHMARK

Check how long a single iteration of model.py takes, and store
to a log file so changes that affect how long the model takes
to run can be easily pinpointed.

Version: 2016jan25
"""

from pylab import loadtxt, savetxt, vstack, array
from optima import Project, gitinfo, sigfig, today, getdate
from time import time

## Settings
hashlen = 7
filename = 'benchmark.txt'
dosave = True

## Run the model
P = Project(spreadsheet='test7pops.xlsx', dorun=False)
t = time()
P.runsim()
elapsed = time()-t

## Gather the output data
elapsedstr = sigfig(elapsed, 3)
todaystr = getdate(today()).replace(' ','_')
gitbranch, gitversion = gitinfo()
gitversion = gitversion[:hashlen]
thisout = array([elapsedstr, todaystr, gitversion, gitbranch])

## Save, but only if hash not already in file
if dosave:
    output = loadtxt(filename, dtype=str)
    if gitversion not in output[:,2]: # Don't append multiple entries per commit
        output = vstack([output, thisout]) # WARNING, will fail if not at least 2 entries in ouput already (to specify dimensionality)
        savetxt(filename, output, fmt='%s')

print('Done benchmarking: model runtime was %s s.' % elapsedstr)