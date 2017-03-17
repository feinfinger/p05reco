# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import p05tools.file as ft
import dxchange


class findOverlap():
    """
    Class findOverlap can be used to find the overlap in a 360 sinogram.

    Usage:
        - use method getSino() to import sinogram data (Felix read_dat format)
          this will automaticaly build a mosaic of the sinogram where you can
          compare the edges in the upper 1/3 and lower 2/3 od the whole mosaic.
        - move the middle part left and right using the shift(shift) method
          until the edges fit well together
        - if you want to cut at a different point, use the shift(shift,
          cutoffset) or shift(cutoffset=value) method, which will add a shift
          and offset to the current total shift and cutoffset
        - every use of the shift method will print the current total shift,
          which is the overlap
        - once you have found a good value enter this value as:
            uelapp : value
          in reconlog.txt and continue the reconstruction
    """
    def __init__(self):
        self.overlap = 0
        self.cutoffset = 0
        self.colorlevels = [-0.2, 1]

        ## make the initial plot
        self.app = QtGui.QApplication([])

        ## Create window with GraphicsView widget
        self.win = QtGui.QMainWindow()
        ## show widget alone in its own window
        self.win.show()
        self.win.setWindowTitle('Find sino overlap')

        self.cw = QtGui.QWidget()
        self.win.setCentralWidget(self.cw)

        self.layout = QtGui.QGridLayout()
        self.cw.setLayout(self.layout)
        self.layout.setSpacing(0)

        self.view = pg.GraphicsView()
        self.viewbox = pg.ViewBox()
        self.viewbox.setAspectLocked()
        self.view.setCentralItem(self.viewbox)
        self.layout.addWidget(self.view, 0, 0)

        self.HLwidget = pg.HistogramLUTWidget()
        self.layout.addWidget(self.HLwidget, 0, 1)

        #self.view = self.win.addViewBox()

        ## lock the aspect ratio so pixels are always square
        #self.view.setAspectLocked(True)

        ## Create image item
        self.img = pg.ImageItem(border='w')
        self.viewbox.addItem(self.img)
        self.HLwidget.setImageItem(self.img)

        ## set initial view bounds
        #self.view.setRange(QtCore.QRectF(0, 0, 800, 800))

        #pg.mkQApp()
        #self.view = pg.ImageView()
        #self.view.show()

    def getSino(self, slice=None, fileName=None):
        """
        Load a sinogram (Felix read_dat) into memory, build a mosaic and plot
        it. get_sino() without a filename will open a file dialog.
        """
        self.data = dxchange.read_hdf5(fileName, 'exchange/data')
        if not slice:
            slice = self.data.shape[1] // 2
        if np.mod(self.data.shape[0],2) == 1:
            self.sino = self.data[:-1, slice, :]
        else:
            self.sino = self.data[:,slice,:]
        self.buildMosaic()
        self.shift()

    def buildMosaic(self):
        """
        build a mosaic of the sinogram in order to compare the edges.
        """
        # prepare sinos
        # cut sino in half and flip lower part around y axis:
        # sino_1
        # sino_2    (flipped around y axis)
        sino_ylen = self.sino.shape[0]

        sino_1 = self.sino[:sino_ylen/2, ::-1]
        sino_2 = self.sino[sino_ylen/2:, :]
        # roll both parts with either both overlap and cutoffset or only
        # cutoffset
        sino_1_roll = np.roll(sino_1, self.cutoffset, axis=1)
        sino_2_roll = np.roll(sino_2, self.overlap + self.cutoffset, axis=1)
        # build mosaic lower part left, upper part right
        self.mosaic = np.concatenate((sino_2_roll, sino_1_roll), axis=1)
        self.mosaic = np.rot90(self.mosaic)

    def shift(self, shift=0, cutoffset=0, colorlevels=None):
        """
        shift(shift, cutoffset) add shift and offset to the current total
        shift and offset, recalculates the mosaic and updates the plot on
        screen.
        """
        if colorlevels:
            self.colorlevels = colorlevels
        self.overlap += shift
        self.cutoffset += cutoffset
        self.buildMosaic()
        self.img.setImage(self.mosaic)
        self.img.setLevels(self.colorlevels)
        #self.view.setImage(self.mosaic)
        print('total shift: %i' % self.overlap)
        print('total cutpoint offset: %i' % self.cutoffset)

    def showOrig(self):
        self.img.setImage(self.sino)


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()