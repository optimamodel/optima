# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from portfolio import Portfolio
from region import Region

p1 = Portfolio('test')
p1.appendregion(Region.load('./regions/Georgia good.json'))
p1.appendregion(Region.load('./regions/Haiti.json'))

r1 = p1.regionlist[0]
r2 = p1.regionlist[1]

p1.geoprioanalysis()
