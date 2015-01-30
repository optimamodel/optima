#!/usr/bin/python
"""
Run all tests of the sim. Yes Anna, I know this sucks, especially 
skipping the unit tests, but I want some way of running all the 
tests that will drop me into the debugger if it hits a bug. If 
you can think up a better way, which I'm sure you can, let me know :)

Version: 2015jan29 by cliffk
"""

from matplotlib.pylab import show, ion
ion()

# Make sure memory is handled OK
try:
    import resource, os
    freemem = 0.95*float(os.popen("free -b").readlines()[1].split()[3]) # Get free memory, set maximum to 95%
    resource.setrlimit(resource.RLIMIT_AS, (freemem, freemem)) # Limit memory usage
    print('  Note: RAM limited to %0.2f GB' % (freemem/1e9))
except:
    print('Attempt to limit memory failed; no matter.')


# Override default exception handling
import sys
def info(type, value, tb):
   if hasattr(sys, 'ps1') or not sys.stderr.isatty(): # we are in interactive mode or we don't have a tty-like device, so we call the default hook
      sys.__excepthook__(type, value, tb)
   else:
      import traceback, pdb
      traceback.print_exception(type, value, tb) # we are NOT in interactive mode, print the exception...
      pdb.pm() # ...then start the debugger in post-mortem mode.
sys.excepthook = info


# Run all tests
from glob import glob
from time import sleep
from sys import argv
if len(argv)==1:
    files = glob('test_*.py')
else:
    files = argv[1:]
for thisfile in files:
   if (thisfile != 'test_programs.py') and (thisfile != 'test_makeworkbook.py'):
      print('''
      \n\n\n\n\n\n\n\n\n
      ###################################################
      IMPORTING %s
      ###################################################
      ''' % thisfile)
      sleep(1)
      execfile(thisfile)

show()
