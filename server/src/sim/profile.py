"""
Profile model.py; see:
    https://zapier.com/engineering/profiling-python-boss/

Requires line_profiler, available from:
    https://pypi.python.org/pypi/line_profiler/

or:
    sudo pip install line_profiler

Usage:
    python profile.py

Version: 2014nov26 by cliffk
"""

print('Profiling...')

from line_profiler import LineProfiler
from model import model
from makemodelpars import makemodelpars
from time import time
from dataio import loaddata

D = loaddata('/tmp/projects/example.prj', verbose=0)
D['M'] = makemodelpars(D['P'], D['opt'], verbose=0)

t=time()
S = model(D['G'], D['M'], D['F'][0], D['opt'], verbose=0)
print('Total time for running model: %0.3f s' % (time()-t))


def do_profile(follow=[]):
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



@do_profile(follow=[model]) # Add decorator to runmodel function
def runmodel():
    S = model(D['G'], D['M'], D['F'][0], D['opt'], verbose=0)
    return S

result = runmodel()





print('Done.')