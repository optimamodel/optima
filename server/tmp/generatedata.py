"""
GENERATEDATA

Example function for generating data.

Version: 2014oct16
"""

def generatedata(numpoints):
    x = [float(p) for p in range(numpoints)]
    y = [float(p)**(0.5) for p in range(numpoints)]
    return x, y