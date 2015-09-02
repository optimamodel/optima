# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 01:01:23 2015

@author: cliffk
"""
import add_optima_paths # analysis:ignore
from portfolio import loadportfolio


filename = 'malawi-gpa.npz'

print('Loading...')
p1 = loadportfolio(filename)

print('Running...')
p1.geoprioanalysis(usebatch=True)                # Run the GPA algorithm.

print('Saving...')
p1.save('malawi-gpa-done')

print('Done.')
