"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016jan23
"""
from PyQt4 import QtGui
global geoguiwindow
geoguiwindow = None

def geogui():
    
    global geoguiwindow
    
    geoguiwindow = QtGui.QWidget() # Create panel widget
    wid = 600.0
    hei = 600.0
    geoguiwindow.setGeometry(100, 100, wid, hei)
    
    makesheetbutton  = QtGui.QPushButton('Create geospatial spreadsheet', parent=geoguiwindow)
    genprojbutton = QtGui.QPushButton('Generate projects from spreadsheet', parent=geoguiwindow)
    loadbutton = QtGui.QPushButton('Load portfolio', parent=geoguiwindow)
    rungeobutton = QtGui.QPushButton('Run geospatial analysis', parent=geoguiwindow)
    exportbutton = QtGui.QPushButton('Export results', parent=geoguiwindow)
    closebutton = QtGui.QPushButton('Close', parent=geoguiwindow)
    
    left = wid/4.
    right = wid*2/3.
    makesheetbutton.move(left, hei-50)
    genprojbutton.move(right, hei-50)
    loadbutton.move(left, hei-100)
    rungeobutton.move(right, hei-100)
    exportbutton.move(left, 50)
    closebutton.move(right, 50)
    
    
#    keepbutton.move(0+buttonoffset, buttonheight)
#    resetbutton.move(200+buttonoffset, buttonheight)
#    closebutton.move(400+buttonoffset, buttonheight)
#    
#    keepbutton.clicked.connect(keeppars)
#    resetbutton.clicked.connect(resetpars)
#    closebutton.clicked.connect(closewindows)
    geoguiwindow.show()