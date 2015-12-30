def foo():
    import numpy as np
    import matplotlib
    matplotlib.use("Qt4Agg") # This program works with Qt only
    import pylab as pl
    fig, ax1 = pl.subplots()
    
    t = np.linspace(0, 10, 200)
    
    line, = ax1.plot(t, np.sin(t))
    
    ### control panel ###
    from PyQt4 import QtGui
    from PyQt4 import QtCore
    from PyQt4.QtCore import Qt
    
    def update():
        freq = float(textbox.text())
        y = np.sin(2*np.pi*freq*t)
        line.set_data(t, y)
        fig.canvas.draw_idle()
    
    root = fig.canvas.manager.window
    panel = QtGui.QWidget()
    hbox = QtGui.QHBoxLayout(panel)
    textbox = QtGui.QLineEdit(parent = panel)
    textbox.textChanged.connect(update)
    hbox.addWidget(textbox)
    panel.setLayout(hbox)
    
    dock = QtGui.QDockWidget("control", root)
    root.addDockWidget(Qt.BottomDockWidgetArea, dock)
    dock.setWidget(panel)
    ######################
    
    pl.show()

foo()