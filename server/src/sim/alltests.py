#!/usr/bin/python
"""
Run all tests of the sim. Yes Anna, I know this sucks, especially 
skipping the unit tests, but I want some way of running all the 
tests that will drop me into the debugger if it hits a bug. If 
you can think up a better way, which I'm sure you can, let me know :)

Version: 2015jan19 by cliffk
"""

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
files = glob('test_*.py')
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
