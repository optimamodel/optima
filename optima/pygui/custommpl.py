from PyQt4.uic import loadUiType as loaduitype
from matplotlib.figure import Figure as figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as canvas, NavigationToolbar2QT as toolbar

Ui_MainWindow, QMainWindow = loaduitype('window.ui')

        
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}
        self.mplfigs.itemClicked.connect(self.changefig)
        fig = figure()
        self.addmpl(fig)

    def changefig(self, item):
        text = item.text()
        self.rmmpl()
        self.addmpl(self.fig_dict[text])

    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.mplfigs.addItem(name)

    def addmpl(self, fig):
        self.canvas = canvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = toolbar(self.canvas, self.mplwindow, coordinates=True)
        self.mplvl.addWidget(self.toolbar)
# This is the alternate toolbar placement. Susbstitute the three lines above
# for these lines to see the different look.
#        self.toolbar = toolbar(self.canvas, self, coordinates=True)
#        self.addToolBar(self.toolbar)

    def rmmpl(self,):
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()


if __name__ == '__main__':
    import sys
    from PyQt4 import QtGui
    import numpy as np

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
    main = Main()
    main.addfig('One plot', fig1)
    main.addfig('Two plots', fig2)
    main.addfig('Pcolormesh', fig3)
    main.show()
    sys.exit(app.exec_())

