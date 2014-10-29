"""
MAKEMODELPARS

Calculate all acts and reconcile them between populations.

Version: 2014oct29
"""

def makemodelpars(P, options, verbose=2):
    if verbose>=1: print('Making model parameters...')
    
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    M = struct()
    M.__doc__ = 'Model parameters to be used directly in the model, calculated from data parameters P.'

    if verbose>=2: print('  ...done making model parameters.')
    return M
