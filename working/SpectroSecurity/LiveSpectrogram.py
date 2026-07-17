#!/usr/bin/python3


# from PyQt4 import QtCore, QtGui
# from PyQt4.QtCore import *
# from PyQt4.QtGui import *
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QGraphicsWidget
import numpy as np
import pyqtgraph as pg
import pyaudio

FS = 44100 #Hz
CHUNKSZ = 1024 #samples

class MicrophoneRecorder():
    def __init__(self, signal):
        self.signal = signal
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=FS,
                            input=True,
                            frames_per_buffer=CHUNKSZ)

    def read(self):
        data = self.stream.read(CHUNKSZ)
        y = np.fromstring(data, 'int16')
        self.signal.emit(y)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    
class SpectrogramWidget(pg.PlotWidget):
    read_collected = pyqtSignal(np.ndarray)
    def __init__(self, parent=None):
        super(SpectrogramWidget, self).__init__()
        
        self.parent = parent
        print("SPECTRO PARENT:", self.parent)
        
        self.__name__ = "SpectroWindow"
        

        self.img = pg.ImageItem()
        self.addItem(self.img)
        
        self.img_array = np.zeros((2000, int(CHUNKSZ/2+1)))
        
        # set no values or ticks on the axis for small display
        ax = self.getAxis('left')
        ax.setStyle(showValues=False, tickLength=0)
        ax.setPen([0, 0, 0, 0])
        ay = self.getAxis('bottom')
        ay.setStyle(showValues=False, tickLength=0)
        ay.setPen([0, 0, 0, 0])
        
        # disable mouse movement in viewbox
        vb = self.getViewBox()
        vb.setMouseEnabled(x=False, y=False)

        # bipolar colormap
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        # set colormap
        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])

        # setup the correct scaling for y-axis
        freq = np.arange((CHUNKSZ/2)+1)/(float(CHUNKSZ)/FS)
        yscale = 1.0/(self.img_array.shape[1]/freq[-1])
        self.img.scale((1./FS)*CHUNKSZ, yscale)

        # Set Labels
        # self.setLabel('left', 'Frequency', units='Hz')

        # prepare window for later use
        self.win = np.hanning(CHUNKSZ)
        self.show()

    def update(self, chunk):
        # normalized, windowed frequencies in data chunk
        spec = np.fft.rfft(chunk*self.win) / CHUNKSZ
        # get magnitude
        psd = abs(spec)
        # convert to dB scale
        psd = 20 * np.log10(psd)

        # roll down one and replace leading edge with new data
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = psd

        self.img.setImage(self.img_array, autoLevels=False)
        
    def mousePressEvent(self, ev):
        
        
        pass

if __name__ == '__main__':
    app = QApplication([])
    w = SpectrogramWidget()
    w.read_collected.connect(w.update)
    w.setGeometry(700, 700, 850, 850)
    w.setWindowFlags(Qt.CustomizeWindowHint)#Qt.FramelessWindowHint)
    w.show()

    mic = MicrophoneRecorder(w.read_collected)

    # time (seconds) between reads
    interval = FS/CHUNKSZ
    t = QTimer()
    t.timeout.connect(mic.read)
    t.start(1000/interval) #QTimer takes ms

    app.exec_()
    mic.close()