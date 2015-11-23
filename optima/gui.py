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
from pylab import ceil, sqrt, transpose, array
import sys
translate =  QtGui.QApplication.translate
global app
global main


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, resultslist):
        self.resultslist = resultslist
        
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.mplwindow = QtGui.QWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mplwindow.sizePolicy().hasHeightForWidth())
        self.mplwindow.setSizePolicy(sizePolicy)
        self.mplwindow.setObjectName("mplwindow")
        self.mplvl = QtGui.QVBoxLayout(self.mplwindow)
        self.mplvl.setMargin(0)
        self.mplvl.setObjectName("mplvl")
        self.gridLayout.addWidget(self.mplwindow, 0, 0, -1, 1)
        
        self.checkboxes = {}
        count = -1;
        for key in resultslist[0].epikeys:
            for subkey in resultslist[0].episubkeys:
                count += 1
                name = key+'-'+subkey
                self.checkboxes[name] = QtGui.QCheckBox(self.centralwidget)
                self.checkboxes[name].setObjectName(name)
                self.checkboxes[name].setChecked(True)
                self.gridLayout.addWidget(self.checkboxes[name], count, 1, 1, 1)
        
        self.pushButton = QtGui.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("Plot")
        self.gridLayout.addWidget(self.pushButton, count+1, 1, 1, 1)        
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(translate("Optima Results GUI", "Optima Results GUI", None))
        self.pushButton.setText(translate("Optima Results GUI", "Plot", None))
        for key in self.resultslist[0].epikeys:
            for subkey in self.resultslist[0].episubkeys:
                self.checkboxes[key+'-'+subkey].setText(translate("Optima Results GUI", key+'-'+subkey, None))
        
        
        

        
class Main(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, resultslist):
        super(Main, self).__init__()
        self.setupUi(self, resultslist)
        self.fig_dict = {}
        self.pushButton.clicked.connect(self.changefig)
        fig = figure()
        self.addmpl(fig)
        self.resultslist = resultslist

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

    def changefig(self):
        ''' Main function that actually does plotting '''
        ischecked = []
        for key in self.resultslist[0].epikeys:
            for subkey in self.resultslist[0].episubkeys:
                if self.checkboxes[key+'-'+subkey].isChecked():
                    ischecked.append([key, subkey])
        
        # Calculate rows and columns of subplots
        nplots = len(ischecked)
        nrows = ceil(sqrt(nplots))
        ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
        
        # Do plotting
        f = figure()
        axes = []
        for i in range(nplots):
            axes.append(f.add_subplot(int(nrows), int(ncols), i+1))
            this = ischecked[i]
            for j in range(len(self.resultslist)):
                thisdata = getattr(getattr(self.resultslist[j],this[0]),this[1])[0]
                axes[-1].plot(self.resultslist[j].tvec, transpose(array(thisdata)), marker=self.resultslist[0].styles[j])
            axes[-1].set_ylabel(this[0]+' '+this[1])
            axes[-1].set_xlabel('Year')
        
        self.f = f
        self.rmmpl()
        self.addmpl(self.f)



def gui(resultslist):
    ''' Actual function to actually be used '''
    global app
    global main
    
    if type(resultslist) is not list: resultslist = [resultslist]
    resultslist[0].epikeys = ['prev', 'numplhiv', 'numinci', 'numdeath', 'numdiag']
    resultslist[0].episubkeys = ['tot','pops']
    resultslist[0].styles = ['o','s','x','+'] # Line plot styles
    app = QtGui.QApplication(sys.argv)
    main = Main(resultslist)
    main.show()


