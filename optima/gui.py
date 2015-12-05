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
from pylab import ceil, sqrt, subplots, close, isinteractive, ion, ioff, array
import sys
translate =  QtGui.QApplication.translate
global app
global main


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, guidata):
        self.guidata = guidata
        
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
        for key in guidata.epikeys:
            for subkey in guidata.episubkeys:
                count += 1
                name = key+'-'+subkey
                self.checkboxes[name] = QtGui.QCheckBox(self.centralwidget)
                self.checkboxes[name].setObjectName(name)
                self.checkboxes[name].setChecked(False) # Set whether boxes are checked or not by default
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
        for key in self.guidata.epikeys:
            for subkey in self.guidata.episubkeys:
                self.checkboxes[key+'-'+subkey].setText(translate("Optima Results GUI", key+'-'+subkey, None))
        
        
        

        
class Main(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, guidata):
        super(Main, self).__init__()
        self.setupUi(self, guidata)
        self.fig_dict = {}
        self.pushButton.clicked.connect(self.changefig)
        fig = figure()
        self.addmpl(fig)
        self.guidata = guidata

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
        for key in self.guidata.epikeys:
            for subkey in self.guidata.episubkeys:
                if self.checkboxes[key+'-'+subkey].isChecked():
                    ischecked.append(key+'-'+subkey)
        
        # Calculate rows and columns of subplots
        nplots = len(ischecked)
        nrows = int(ceil(sqrt(nplots)))
        ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
        
        # Do plotting
        if nplots>0: # Don't do anything if no plots
            wasinteractive = isinteractive()
            if wasinteractive: ioff()
            fig, fakeaxes = subplots(ncols, nrows, sharex='all') # Create figure with correct number of plots
            close(fig)
            if wasinteractive: ion()
            if nplots==1: fakeaxes = array(fakeaxes) # Convert to array so iterable
            for fa in fakeaxes.flatten(): fig._axstack.remove(fa) # Remove placeholder axes
            
            # Actually create plots
            plots = self.guidata.results.makeplots(ischecked)

            for p in range(len(plots)):
                thisplot = plots[p].axes[0]
                fig._axstack.add(fig._make_key(thisplot), thisplot)
                thisplot.change_geometry(nrows,ncols,p+1)
        else:
            fig = figure() # Blank figure
        
        self.fig = fig
        self.rmmpl()
        self.addmpl(self.fig)



def gui(results):
    ''' Actual function to actually be used '''
    global app
    global main
    
    # Define options for selection
    epikeys = results.main.keys()
    episubkeys = ['tot','pops'] # Would be best not to hard-code this...
    
    class GUIdata:
        def __init__(self, results, epikeys, episubkeys):
            self.results = results
            self.epikeys = epikeys
            self.episubkeys = episubkeys
    
    guidata = GUIdata(results, epikeys, episubkeys)
    
    
    app = QtGui.QApplication(sys.argv)
    main = Main(guidata)
    main.show()


