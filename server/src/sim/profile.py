"""
Profile model.py -- see https://zapier.com/engineering/profiling-python-boss/

Requires line_profiler, available from
https://pypi.python.org/pypi/line_profiler/

or
sudo pip install line_profiler

Version: 2014nov26 by cliffk
"""

print('Profiling...')

from line_profiler import LineProfiler

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

from dataio import loaddata
D = loaddata('/tmp/projects/example.prj')

from makemodelpars import makemodelpars
D.M = makemodelpars(D.P, D.opt)

from model import model


@do_profile(follow=[model])
def runmodel():
    S = model(D.G, D.M, D.F[0], D.opt, verbose=0)
    return S

result = runmodel()


print('Done.')