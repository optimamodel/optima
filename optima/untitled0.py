# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 18:02:27 2015

@author: cliffk
"""

from optima import *

P = Project()
P.data = loadspreadsheet('test.xlsx')
parset = Parameterset()
parset.makeparsfromdata(P.data) # Create parameters
P.addparset('default', parset)
p = P.parsets[0].pars[0]
simpars = P.parsets[0].interp()


print('Done.')