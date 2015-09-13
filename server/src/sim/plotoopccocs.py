# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 18:36:39 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from project import Project
import os
from numpy import sort
from sim import Sim
from plotccocs import makecc, plotprogramcurves

# List all the json files in the projects sub-directory.
templist = sort([x for x in os.listdir('./projects/') if x.endswith('.json')])
r1 = Project.load('./projects/' + templist[0])

s = Sim('test-sim',r1)
s.initialise()
S = s.run()[0]

D = dict()
D['G'] = r1.metadata
D['data'] = r1.data
D['opt'] = r1.options
D['programs'] = r1.metadata['programs']
D['P'] = s.parsdata
D['S'] = S
D['M'] = s.parsmodel

selection = range(0,2)
for i,program in enumerate(D['programs']):
    if i in selection:
        if len(program['effects'])>0:
            plotdata_cc, D = makecc(D=D, progname=program['name'])
            plotprogramcurves(D=D, progname=program['name'], doclose=False)