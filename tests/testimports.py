'''
TESTIMPORTS

A tiny script to check that all the imports in Optima are working.

Version: 2016jan14 by cliffk
'''

print('Testing imports...'),
import __builtin__
__builtin__._failsilently = False
import optima # analysis:ignore
print('they all passed, I suppose.')