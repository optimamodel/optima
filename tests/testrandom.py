"""
Do random tests.

Version: 2016feb09
"""

from line_profiler import LineProfiler

import optima as op
P = op.defaults.defaultproject('best')
ps = P.parsets[0]
tofollow = P.progsets[0].getoutcomes


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
    
    
    
    @do_profile(follow=[tofollow]) # Add decorator to runmodel function
    def runsimwrapper(): 
        P.progsets[0].reconcile(parset=ps, year=2016, optmethod='asd', maxiters=10)
    runsimwrapper()
    
    print('Done.')

profile()
