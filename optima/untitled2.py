# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 20:30:28 2015

@author: cliffk
"""

from pylab import figure
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from matplotlib import use
use("Qt4Agg") # This program works with Qt only

#fig = figure() # Open figure
panel = QtGui.QWidget() # Create panel widget
 
#hbox = QtGui.QHBoxLayout(panel) # Create some kind of box
#root = fig.canvas.manager.window # Get window of the figure
#dock = QtGui.QDockWidget("control", root) # Dock the widget to the window
#hbox.addWidget(textbox) # Add the textbox to the "hbox"
#panel.setLayout(hbox) # Add the "hbox" to the "panel"
#root.addDockWidget(Qt.BottomDockWidgetArea, dock) # Um, and do it again
#dock.setWidget(panel) # Yeah, and again
panel.setGeometry(300, 300, 250, 150)
textbox = QtGui.QLineEdit(parent = panel) # Actually create the text edit box
textbox.move(50, 50) 
panel.show()