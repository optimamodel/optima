# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from portfolio import Portfolio
from project import Project
from os import listdir
from pylab import sort
import multiprocessing

usebatch = True

def loaddistrict(district):
    return Project.load('./projects/' + district + '.json')

if __name__ == '__main__':
    p1 = Portfolio('malawi-gpa')
    districts = sort([x.split('.')[0] for x in listdir('./projects/') if x.endswith('.json')])

    if usebatch:
        pool = multiprocessing.Pool()
        results = pool.map(loaddistrict, districts)
    else:
        results = [loaddistrict(x) for x in districts]
    
    [p1.appendproject(x) for x in results]

    print('Running GPA...')
    p1.geoprioanalysis(usebatch=True)                # Run the GPA algorithm.
    print('Saving portfolio...')
    p1.save('malawi-gpa')