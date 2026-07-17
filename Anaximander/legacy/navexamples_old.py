
import socket

directions[0]['legs'][0]['steps']

placesNearby['results'][0]['name'] & ['formatted_address']
placesNearby['results'][0]['geometry']['location']

{
    'distance': {'text': '1.8 mi', 'value': 2929},
    'duration': {'text': '5 mins', 'value': 315},
    'end_location': {'lat': 29.9733752, 'lng': -90.0608046},
    'html_instructions': 'Turn <b>left</b> at the 3rd cross street onto <b>N Claiborne Ave</b>',
    'maneuver': 'turn-left',
    'polyline': {'points': '}o|uD|dodPk@bEg@tDk@|Dk@bEg@nDc@`Dc@tCa@|Cg@pDq@xEe@lDaA|GM~@]bC[|BUzA?BEZKl@In@EVEZCLANMv@In@YnBE\\i@zDk@|DKh@?dAL`FL`FJhE@\\?NLhELbFL~EJ~EDbALfFLbFH`DB|@'},
    'start_location': {'lat': 29.9700651, 'lng': -90.03103270000001},
    'travel_mode': 'DRIVING'
}
UDP_IP = "192.168.0.2"
HOUSE_IP = "72.211.113.6"
HOUSE_PORT = 32323
UDP_PORT = 5555
dataList = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
data, addr = sock.recvfrom(1024)
latLong = data.split(b',')
# print(data)

# if int(latLong[1]) == 1:
#     print(float(latLong[2]), float(latLong[3]))
# else:
#     data, addr = sock.recvfrom(1024)
while int(latLong[1]) != 1:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    latLong = data.split(b',')
    if int(latLong[1]) == 1:
        dataList.append(float(latLong[2]))
        dataList.append(float(latLong[3]))
        print(dataList)
#
# print(data)
    # if findThis[1] == b' 1':
    #     print(float(findThis[2]), float(findThis[3]))
    # if data.startswith(b'$GNRMC'):
    #     print(data)
    # dataList.append(data)
    # print("received message:", data)


class NETThread(QThread):

    #Signals
    netStatFinished = pyqtSignal(tuple)


    def __init__(self, parent, type, *args):
        super(NETThread, self).__init__()
        QThread.__init__(self)

        print("WORK THREAD")
        # print("CALLBACK: ", callback)

        self.NETCore = parent
        # print(self.NETCore)
        self.type = type
        self.args = []
        # print(args)
        for arg in args:
            self.args.append(arg)

        # self.netStatFinished.connect(callback)



    def run(self):

        if self.type == 1:
            # print("NETSTAT")
            self.netStat(self.args[0])

    def netStat(self, interface):

        # while True:


        netStats1 = psutil.net_io_counters(True)
        # print(netStats1)
        netTx = netStats1[interface.decode()][0]
        netRx = netStats1[interface.decode()][1]
        time.sleep(0.1)

        netStats2 = psutil.net_io_counters(True)
        nextnetTx = netStats2[interface.decode()][0]
        nextnetRx = netStats2[interface.decode()][1]

        inputTx = int(nextnetTx) - int(netTx)
        inputRx = int(nextnetRx) - int(netRx)

        # print("RESULTS", (inputTx, inputRx))
        # self.answer = Results((inputTx, inputRx))
        # self.NETCore.netStatRate = (inputTx, inputRx)
        self.NETCore.returnRate((inputTx, inputRx))
        # self.netStatFinished.emit((inputTx, inputRx))

        # return (inputTx, inputRx)



QMainWindow
QMessageBox
QDesktopWidget
QIcon
QListWidget
QWidget
QAction
qApp
QFont
QGridLayout
QEvent
QUrl
QImage
QImageReader
QTextDocument
QTextImageFormat
QTextCursor
Qt
QCursor
QInputDialog
QColor


import os, socket

homeIP = '72.211.133.6'
homePort = 32323
localIP = '192.168.0.2'
localPort = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect((localIP, localPort))
sock.send(b"This is my first socket message")


self.displayItem = self.layout.addWidget(self.display, 0, 0, 10, 10)
        self.powerItem = self.layout.addWidget(self.powerBtn, 11, 0, 1, 1)
        self.alexandriaItem = self.layout.addWidget(self.alexandriaBtn, 11, 1, 1, 1)
        self.archimedesItem = self.layout.addWidget(self.archimedesBtn, 11, 2, 1, 1)
        self.anaximanderItem = self.layout.addWidget(self.anaximanderBtn, 11, 3, 1, 1)
        self.callimachusItem = self.layout.addWidget(self.callimachusBtn, 11, 4, 1, 1)
        self.kryptosItem = self.layout.addWidget(self.kryptosBtn, 11, 5, 1, 1)
        self.musaeumItem = self.layout.addWidget(self.musaeumBtn, 11, 6, 1, 1)
        self.phaleronItem = self.layout.addWidget(self.phaleronBtn, 11, 7, 1, 1)
        self.pharosItem = self.layout.addWidget(self.pharosBtn, 11, 8, 1, 1)
        self.teslaItem = self.layout.addWidget(self.teslaBtn, 11, 9, 1, 1)
        self.clockItem = self.layout.addWidget(self.clock, 12, 0, 1, 10)





(void)deform
{
  Vertex2f  vi;   // Current input vertex
  Vertex3f  v1;   // First stage of the deformation
  Vertex3f *vo;   // Pointer to the finished vertex
CGFloat R, r, beta;
  for (ushort ii = 0; ii < numVertices_; ii++)
  {
    // Get the current input vertex.
    vi    = inputMesh_[ii];
    // Radius of the circle circumscribed by vertex (vi.x, vi.y) around A on the x-y plane
    R     = sqrt(vi.x * vi.x + pow(vi.y - A, 2));
    // Now get the radius of the cone cross section intersected by our vertex in 3D space.
    r     = R * sin(theta);
    // Angle subtended by arc |ST| on the cone cross section.
    beta  = asin(vi.x / R) / sin(theta);

// *** MAGIC!!! ***
v1.x  = r * sin(beta);
v1.y  = R + A - r * (1 - cos(beta)) * sin(theta);
v1.z  = r * (1 - cos(beta)) * cos(theta);
// Apply a basic rotation transform around the y axis to rotate the curled page.


 // These two steps could be combined through simple substitution, but are left
    // separate to keep the math simple for debugging and illustrative purposes.
    vo    = &outputMesh_[ii];
    vo->x = (v1.x * cos(rho) - v1.z * sin(rho));
    vo->y =  v1.y;
    vo->z = (v1.x * sin(rho) + v1.z * cos(rho));
  }
}




BOOKMARGIN
DOUBLEBOOKWIDTH
BOOKHEIGHT
BOOKWIDTH