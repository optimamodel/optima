import sys

from PyQt4 import QtGui, QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from optima import (
    defaults, pygui, makeplots, OptimaException)



class MatplotlibFigureCanvas(FigureCanvas):

    def __init__(self, parent=None, dpi=100, figsize=(5,4)):
        self.figure = Figure(figsize=figsize, dpi=dpi)
        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(
            self,
            QtGui.QSizePolicy.Fixed,
            QtGui.QSizePolicy.Fixed)
        FigureCanvas.updateGeometry(self)

    def addAxes(self, axes):
        key = self.figure._make_key(axes)
        self.figure._axstack.add(key, axes)



class ScrollingFiguresWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setWindowTitle("Optima Result Graphs")

        # Determines location of window on opening
        self.setGeometry(5, 5, 900, 1000)

        self.buildMenus()

        # Build the scroll area
        self.centralWidget = QtGui.QWidget(self)
        self.centralWidget.setFocus()
        self.setCentralWidget(self.centralWidget)
        self.centralLayout = QtGui.QVBoxLayout(self.centralWidget)

        self.scrollArea = QtGui.QScrollArea(self.centralWidget)
        self.scrollArea.setFrameStyle(QtGui.QFrame.NoFrame)
        self.centralLayout.addWidget(self.scrollArea)

        self.scrollContents = QtGui.QWidget()
        self.scrollArea.setWidget(self.scrollContents)
        self.scrollArea.setWidgetResizable(True)

        self.scrollLayout = QtGui.QVBoxLayout(self.scrollContents)
        self.scrollLayout.setGeometry(QtCore.QRect(0, 0, 1000, 1000))
        self.scrollContents.setLayout(self.scrollLayout)

    def buildMenus(self):
        # On Macs, Exit and About are overriden by the 
        # OS so they won't appear if defined
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction('More Information', self.about)
        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction('More Information', self.about)

    def plotFigures(self, figures, figsize=(5, 4), dpi=100):
        for figure in figures:
            for axes in figure.axes:
                figWidget = QtGui.QWidget(self.scrollContents)
                figLayout = QtGui.QVBoxLayout()
                canvas = MatplotlibFigureCanvas(
                    figWidget, figsize=figsize, dpi=dpi)
                canvas.addAxes(axes)
                canvas.figure.patch.set_facecolor('white')
                figLayout.addWidget(canvas)
                figWidget.setLayout(figLayout)
                self.scrollLayout.addWidget(figWidget)
        
    def about(self):
        QtGui.QMessageBox.about(self, "About", "More message")



def pyqtshowresults(results):
    app = QtGui.QApplication(sys.argv)
    figures = makeplots(results, figsize=(3, 2)).values()

    # A slight delay is needed here for PyQT to initialize properly
    # which is provided by the previous line
    window = ScrollingFiguresWindow()
    window.plotFigures(figures, figsize=(8, 5), dpi=60)
    window.show()

    # run main loop for PyQT
    app.exec_()



P = defaults.defaultproject('concentrated')

pyqtshowresults(P.runsim())


# P = defaults.defaultproject('concentrated')
# results = P.runsim() # Showing another way of running
# print matplotlib.get_backend()
# pygui(results)
#
# P.manualfit()
#
# from optima import geogui
# geogui()
#




