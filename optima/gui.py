'''
GUI

A "quick" Python GUI for plotting the results.

Usage:

results = P.runsim()
from gui import gui # put this in P?
gui(results)

Version: 2015nov02 by cliffk
'''


## Imports
from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure as figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as canvas, NavigationToolbar2QT as toolbar
from pylab import floor, rand
import sys
import numpy as np
translate =  QtGui.QApplication.translate



class Ui_MainWindow(object):
    def setupUi(self, MainWindow, results):
        
        self.epikeys = ['prev','numplhiv']
        self.episubkeys = ['tot','pops']
#        nplots = 
        
        
        
        MainWindow.setObjectName(("MainWindow"))
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(("gridLayout"))
        self.mplwindow = QtGui.QWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mplwindow.sizePolicy().hasHeightForWidth())
        self.mplwindow.setSizePolicy(sizePolicy)
        self.mplwindow.setObjectName(("mplwindow"))
        self.mplvl = QtGui.QVBoxLayout(self.mplwindow)
        self.mplvl.setMargin(0)
        self.mplvl.setObjectName(("mplvl"))
        self.gridLayout.addWidget(self.mplwindow, 5, 2, 1, 1)
        
        self.checkboxes = {}
        count = -1;
        for key in self.epikeys:
            for subkey in self.episubkeys:
                count += 1
                name = key+subkey
                self.checkboxes[name] = QtGui.QCheckBox(self.centralwidget)
                self.checkboxes[name].setObjectName(name)
                self.gridLayout.addWidget(self.checkboxes[name], count, 1, 1, 1)
        
        self.pushButton = QtGui.QPushButton(self.centralwidget)
        self.pushButton.setObjectName(("pushButton"))
        self.gridLayout.addWidget(self.pushButton, count+1, 1, 1, 1)        
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(translate("Optima Results GUI", "Optima Results GUI", None))
        self.pushButton.setText(translate("Optima Results GUI", "Plot", None))
        for key in self.epikeys:
            for subkey in self.episubkeys:
                self.checkboxes[key+subkey].setText(translate("Optima Results GUI", key+' '+subkey, None))
        
        
        

        
class Main(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, results):
        super(Main, self).__init__()
        self.setupUi(self, results)
        self.fig_dict = {}
        self.pushButton.clicked.connect(self.changefig)
        fig = figure()
        self.addmpl(fig)

    def changefig(self):
        text = self.fig_dict.keys()[int(floor(len(self.fig_dict.keys())*rand()))]
        self.rmmpl()
        self.addmpl(self.fig_dict[text])

    def addfig(self, name, fig):
        self.fig_dict[name] = fig

    def addmpl(self, fig):
        self.canvas = canvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = toolbar(self.canvas, self.mplwindow, coordinates=True)
        self.mplvl.addWidget(self.toolbar)

    def rmmpl(self):
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()


if __name__ == '__main__':
    from project import Project
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim()
    
    
    
    
#    for key in epikeys:
#        totdata  = getattr(results,key).tot[0] # WARNING, shouldn't need the zero
#        popsdata = getattr(results,key).pops[0]
#        
#        figs.append(figure())
        
        
        
        
    
    
    
    
    fig1 = figure()
    ax1f1 = fig1.add_subplot(111)
    ax1f1.plot(np.random.rand(5))

    fig2 = figure()
    ax1f2 = fig2.add_subplot(121)
    ax1f2.plot(np.random.rand(5))
    ax2f2 = fig2.add_subplot(122)
    ax2f2.plot(np.random.rand(10))

    fig3 = figure()
    ax1f3 = fig3.add_subplot(111)
    ax1f3.pcolormesh(np.random.rand(20,20))

    app = QtGui.QApplication(sys.argv)
    main = Main(results)
    main.addfig('One plot', fig1)
    main.addfig('Two plots', fig2)
    main.addfig('Pcolormesh', fig3)
    main.show()

