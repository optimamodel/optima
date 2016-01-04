# -*- coding: utf-8 -*-
"""
Recursively deletes all .pyc in directory and subdirectories.

Created on Fri Sep 18 19:46:12 2015

@author: David Kedziora
"""

import os
        
def cleanfolder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path) and file_path.endswith('.pyc'):
                print('Deleting: %s' % file_path)
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                cleanfolder(file_path)
        except Exception, e:
            print e
            
cleanfolder('.')