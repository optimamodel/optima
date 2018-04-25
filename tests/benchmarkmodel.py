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

Version: 2018apr24
"""

dobenchmark = True
doprofile = True

# If running profiling, choose which function to line profile. 
functiontoprofile = 'model' # Choices are: model, runsim, makesimpars, interp
tobenchmark = 'runsim' # Choices are 'runsim' or 'runbudget'


############################################################################################################################
## Benchmarking
############################################################################################################################
if dobenchmark:
    print('Benchmarking...')
    
    from optima import demo, gitinfo, today, getdate, loadtext, savetext
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
    
    # Prelminaries
    P = demo(doplot=False, dorun=False)
    performance1 = cpubenchmark()
    t = time()

    # Run the model 
    if   tobenchmark == 'runsim':    P.runsim()
    elif tobenchmark == 'runbudget': P.runbudget()
    else: raise Exception('tobenchmark "%s" not recognized' % tobenchmark)

    elapsed = time()-t
    performance2 = cpubenchmark()
    performance = sum([performance1, performance2])/2. # Find average of before and after
    benchmarktxt = "for %s (benchmark:%0.2fm iterations/second)" % (tobenchmark, performance)
    print(benchmarktxt)
    
    # Gather the output data
    elapsedstr = '%0.3f' % elapsed
    todaystr = getdate(today()).replace(' ','_')
    gitbranch, gitversion = gitinfo()
    gitversion = gitversion[:hashlen]
    thisout = ' '.join([elapsedstr, todaystr, gitversion, gitbranch, benchmarktxt])
    
    # Save, but only if hash not already in file
    if dosave:
        output = loadtext(filename, splitlines=True)
        output.append(thisout)
        savetext(filename, output)
    
    print('Done benchmarking: model runtime was %s s.' % elapsedstr)



############################################################################################################################
## Profiling
############################################################################################################################
try: 
    import line_profiler # analysis:ignore
except: 
    print('WARNING: Line profiler "line_profiler" not available, not running line profiling')
    doprofile = False # Don't profile if it can't be loaded

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