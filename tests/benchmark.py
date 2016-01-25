"""
BENCHMARK

Check how long a single iteration of model.py takes.

Version: 2016jan25
"""


from pylab import loadtxt, savetxt, vstack, array
from optima import Project, gitinfo, tic, sigfig, today, getdate

hashlen = 7
filename = 'benchmark.txt'
dosave = True

P = Project(spreadsheet='test7pops.xlsx', dorun=False)
t = tic()
P.runsim()
elapsed = tic()-t

elapsedstr = sigfig(elapsed, 3)
todaystr = getdate(today()).replace(' ','_')
gitbranch, gitversion = gitinfo()
gitversion = gitversion[:hashlen]
thisout = array([elapsedstr, todaystr, gitversion, gitbranch])

if dosave:
    output = loadtxt(filename, dtype=str)
    if 1:#gitversion not in output[:,2]: # Don't append multiple entries per commit
        output = vstack([output, thisout])
        savetxt(filename, output, fmt='%s')

print('Done benchmarking: model runtime was %s s.' % elapsedstr)