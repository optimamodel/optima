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

Version: 2016jan29
"""

dobenchmark = True
doprofile = False
functiontoprofile = 'model' # If running profiling, choose which function to line profile


############################################################################################################################
## Benchmarking
############################################################################################################################
if dobenchmark:
    print('Benchmarking...')
    
    from pylab import loadtxt, savetxt, vstack, array
    from optima import Project, gitinfo, sigfig, today, getdate
    from time import time
    
    ## Settings
    hashlen = 7
    filename = 'benchmark.txt'
    dosave = True
    
    ## Run the model
    P = Project(spreadsheet='generalized.xlsx', dorun=False)
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



############################################################################################################################
## Profiling
############################################################################################################################
if doprofile:
    def profile():
        print('Profiling...')
        
        from line_profiler import LineProfiler
        from optima import Project, model
        
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
            P = Project(spreadsheet='generalized.xlsx', dorun=False)
            P.runsim()
        runsimwrapper()
        
        print('Done.')
    
    profile()