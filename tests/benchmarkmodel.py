#!/usr/bin/env python
"""
BENCHMARKMODEL

Check how long a single iteration of model.py takes, and store
to a log file so changes that affect how long the model takes
to run can be easily pinpointed. 

Now also does profiling! See: https://zapier.com/engineering/profiling-python-boss/

Requires line_profiler, available from: 
    https://pypi.python.org/pypi/line_profiler/
or: 
    pip install line_profiler

Version: 2017oct30
"""

dobenchmark = True
doprofile = True

# If running profiling, choose which function to line profile. Choices are: model, runsim, makesimpars, interp
functiontoprofile = 'model' 


############################################################################################################################
## Benchmarking
############################################################################################################################
if dobenchmark:
    print('Benchmarking...')
    
    from pylab import loadtxt, savetxt, vstack, array
    from optima import demo, gitinfo, today, getdate
    from time import time
    
    # Settings
    hashlen = 7
    filename = 'benchmark.txt'
    dosave = True
    
    # Run a benchmarking test
    def cpubenchmark():
        starttime = time()
        tmp = [0+tmp for tmp in range(int(1e6))]
        endtime = time()
        performance = 1.0/(endtime-starttime)
        return performance
    
    # Run the model
    P = demo(0)
    performance1 = cpubenchmark()
    t = time()
    P.runsim()
    elapsed = time()-t
    performance2 = cpubenchmark()
    performance = sum([performance1, performance2])/2. # Find average of before and after
    benchmarktxt = "(benchmark:%0.2fm)" % performance
    print(benchmarktxt)
    
    # Gather the output data
    elapsedstr = '%0.3f' % elapsed
    todaystr = getdate(today()).replace(' ','_')
    gitbranch, gitversion = gitinfo()
    gitversion = gitversion[:hashlen]
    thisout = array([elapsedstr, todaystr, gitversion, gitbranch, benchmarktxt])
    
    # Save, but only if hash not already in file
    if dosave:
        output = loadtxt(filename, dtype=str)
        output = vstack([output, thisout]) # WARNING, will fail if not at least 2 entries in ouput already (to specify dimensionality)
        savetxt(filename, output, fmt='%s')
    
    print('Done benchmarking: model runtime was %s s.' % elapsedstr)



############################################################################################################################
## Profiling
############################################################################################################################
try: import line_profiler # analysis:ignore
except: doprofile = False # Don't profile if it can't be loaded
if doprofile:
    from line_profiler import LineProfiler
    from optima import Project, model, makesimpars, applylimits # analysis:ignore -- called by eval() function
    P = Project(spreadsheet='generalized.xlsx', dorun=False)
    runsim = P.runsim # analysis:ignore
    interp = P.pars()['hivtest'].interp
    
    def profile():
        print('Profiling...')

        def do_profile(follow=None):
          def inner(func):
              def profiled_func(*args, **kwargs):
                  try:
                      profiler = LineProfiler()
                      profiler.add_function(func)
                      for f in follow:
                          profiler.add_function(f)
                      profiler.enable_by_count()
                      return func(*args, **kwargs)
                  finally:
                      profiler.print_stats()
              return profiled_func
          return inner
        
        
        
        @do_profile(follow=[eval(functiontoprofile)]) # Add decorator to runmodel function
        def runsimwrapper(): 
            P.runsim()
        runsimwrapper()
        
        print('Done.')
    
    profile()

if 'elapsedstr' in locals():
    print('And to summarize, model runtime was %s s.' % elapsedstr)