# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 20:30:28 2015

@author: cliffk
"""

from pylab import figure, close
from PyQt4 import QtGui

global panel

def foo():
    
    global panel

    def update():
        print('hi!!!')
    
    fig = figure(); close(fig) # Open and close figure...dumb, no?
    panel = QtGui.QWidget() # Create panel widget
    panel.setGeometry(300, 300, 250, 150)
    textbox = QtGui.QLineEdit(parent = panel) # Actually create the text edit box
    textbox.move(50, 50)
    textbox.textChanged.connect(update) 
    
    
    panel.show()



foo()