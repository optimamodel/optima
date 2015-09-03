# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from project import Project

def calculate_boc_for_project(projectname):

    targetproject = Project.load('./projects/' + projectname + '.json')           # Load up a Project from the json file.
    targetproject.recalculateBOC()
    targetproject.save('./projects/' + projectname + '.json')