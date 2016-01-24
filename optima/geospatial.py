"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016jan23
"""

from PyQt4 import QtGui
from pylab import figure, close
global geoguiwindow
geoguiwindow = None

def geogui():
    '''
    Open the GUI for doing geospatial analysis.
    
    Version: 2016jan23
    '''
    global geoguiwindow
    
    ## Set parameters
    wid = 300.0
    hei = 400.0
    top = 20
    spacing = 40
    left = 20.
    right = wid*2/3.
    
    ## Housekeeping
    fig = figure(); close(fig) # Open and close figure...dumb, no? Otherwise get "QWidget: Must construct a QApplication before a QPaintDevice"
    geoguiwindow = QtGui.QWidget() # Create panel widget
    geoguiwindow.setGeometry(100, 100, wid, hei)
    geoguiwindow.setWindowTitle('Optima geospatial analysis')
    
    ## Define buttons
    makesheetbutton = QtGui.QPushButton('Create geospatial spreadsheet', parent=geoguiwindow)
    genprojbutton   = QtGui.QPushButton('Generate projects from spreadsheet', parent=geoguiwindow)
    loadbutton      = QtGui.QPushButton('Load portfolio', parent=geoguiwindow)
    rungeobutton    = QtGui.QPushButton('Run geospatial analysis', parent=geoguiwindow)
    exportbutton    = QtGui.QPushButton('Export results', parent=geoguiwindow)
    closebutton     = QtGui.QPushButton('Close', parent=geoguiwindow)
    
    ## Set button locations
    makesheetbutton.move(left, top+spacing*0)
    genprojbutton.move(left, top+spacing*1)
    loadbutton.move(left, top+spacing*2)
    rungeobutton.move(left, top+spacing*3)
    exportbutton.move(left, hei-spacing)
    closebutton.move(right, hei-spacing)
    
    ## Define functions
#    makesheetbutton.clicked.connect()
#    genprojbutton.clicked.connect()
#    loadbutton.clicked.connect()
#    rungeobutton.clicked.connect()
#    exportbutton.clicked.connect()
    closebutton.clicked.connect(geoguiwindow.close)
    
    
#    keepbutton.move(0+buttonoffset, buttonheight)
#    resetbutton.move(200+buttonoffset, buttonheight)
#    closebutton.move(400+buttonoffset, buttonheight)
#    
#    keepbutton.clicked.connect(keeppars)
#    resetbutton.clicked.connect(resetpars)
#    closebutton.clicked.connect(closewindows)
    geoguiwindow.show()