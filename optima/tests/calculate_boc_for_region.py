# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from region import Region

def calculate_boc_for_region(regionname):

    targetregion = Region.load('./regions/' + regionname + '.json')           # Load up a Region from the json file.
    targetregion.recalculateBOC()
    targetregion.save('./regions/' + regionname + '.json')