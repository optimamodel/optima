# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 04:34:26 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from utils import tic, toc
from project import Project
from pylab import sort
from os import listdir
from multiprocessing import Process,freeze_support

usebatch = True


def calculate_boc_for_project(projectname, integer):
    print('============ Starting project %s (%i) =============' % (projectname, integer))
    t = tic()
    targetproject = Project.load('./projects/' + projectname + '.json')           # Load up a project from the json file.
    targetproject.recalculateBOC()
    targetproject.save('./projects/' + projectname + '.json')
    toc(t)
    print('============ Done with project %s =============' % projectname)
    
if __name__ == '__main__':
    freeze_support()
    processes = []
    districts = sort([x.split('.')[0] for x in listdir('./projects/') if x.endswith('.json')])
    for i,district in enumerate(districts):
        if usebatch:
            p = Process(target=calculate_boc_for_project, args=(district,i))
            p.start()
            processes.append(p)
        else:
            calculate_boc_for_project(district,i)

    if usebatch:
        for p in processes:
            p.join()


print('DONE.')



