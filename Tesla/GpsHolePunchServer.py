#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

# from PyQt6.QtCore import QObject, QThread

import socket, os, time
from subprocess import Popen, PIPE
from ast import literal_eval
from threading import Thread
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)
from socketserver import ThreadingMixIn





UDP_IP = "192.168.0.2"
HOUSE_IP = "72.211.113.6"
PTOL_IP = '80.255.11.139'
# TODO:SETTINGS — hardcoded port → Tesla/settings tab
PTOL_PORT = 23232
# TODO:SETTINGS — hardcoded port → Tesla/settings tab
HOUSE_PORT = 32323
# TODO:SETTINGS — hardcoded port → Tesla/settings tab
UDP_PORT = 5555
dataList = []
dataDict = {}

class Sockets(object):

    def __init__(self,
                 contents=None,
                 socketType="UDP",
                 ipAddy=None,
                 ipPort=None,
                 face='local',
                 send=False,
                 collect=False,
                 parent=None):
        super(Sockets, self).__init__()
        object.__init__(self)

        self.PHONE_WIFI_IP = '192.168.43.1'
        self.PHONE_BLUE_IP = '192.168.44.1'
        self.PHONE_USB_IP = ''
        self.BUFFER_SIZE = 1024

        if not ipAddy:

            try:
                if face == 'local':

                    self.LOCAL_IP = self.getLocalIP()
                    print(self.LOCAL_IP)
                    # TODO:SETTINGS — hardcoded port → Tesla/settings tab
                    self.LOCAL_PORT = 5555

                elif face == 'public':
                    self.PUBLIC_IP = self.getPublicIP()
                    print(self.PUBLIC_IP)
                    # TODO:SETTINGS — hardcoded port → Tesla/settings tab
                    self.PUBLIC_PORT = 32323

            except IndexError:
                print("INDEX ERROR")

                pass

            if face == 'local':
                self.ip = self.LOCAL_IP
                self.port = self.LOCAL_PORT

            elif face == 'public':
                self.ip = self.PUBLIC_IP
                self.port = self.PUBLIC_PORT

            elif face == 'jarvis':
                self.ip = '216.155.155.108'
                # TODO:SETTINGS — hardcoded port → Tesla/settings tab
                self.port = 23232

            elif face == 'ptolemy':
                self.ip = '80.255.11.139'
                # TODO:SETTINGS — hardcoded port → Tesla/settings tab
                self.port = 32323

            elif face == 'phonewifi':
                self.ip = self.PHONE_USB_IP
                # TODO:SETTINGS — hardcoded port → Tesla/settings tab
                self.port = 32323

        else:
            self.ip = ipAddy
            self.port = ipPort


        print("USING:", self.ip, self.port)


        self.contents = contents
        self.socketType = socketType
        self.face = face
        self.send = send
        self.collect = collect

        if socketType == 'TCP':
            print('Opening TCP Socket')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # TCP

        elif socketType == 'UDP':
            print('Opening UDP Socket')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # UDP

        print('Binding Socket to ' + str(self.ip) + ',' + str(self.port))
        if not send:

            self.sockReceive()

        else:

            self.sockSend()

    # Add a 'Get Wireless Interface' function TODO
    def getLocalIP(self, iface='vnet0:0'):#bnep0'):#wlp2s0'):
        process = Popen(
            args="ifconfig -a {0} | grep 'inet '".format(iface),
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()[0].replace(b"        ", b"").split(b" ")[1]
        pass

    def getPublicIP(self):
        process = Popen(
            args="dig +short myip.opendns.com @resolver1.opendns.com",
            stdout=PIPE,
            stderr=PIPE,
            shell=True
        )
        return process.communicate()[0].replace(b"\n", b"")

    def sockReceive(self):

        self.sock.bind((self.ip, self.port))
        print('Socket Listening :', self.ip, self.port)

        while True:
            data, addr = self.sock.recvfrom(self.BUFFER_SIZE)

            self.sendIp = addr[0]
            self.sendPort = addr[1]
            if data.startswith(b'{'):

                dictionary = self.dataFix(data)
                dictionary[b'senderip'] = addr[0]
                dictionary[b'senderport'] = addr[1]
                with open('location.txt', 'w') as f:
                    f.write(str(dictionary))
                    f.close()

            print(data, addr)
            
            # if dictionary:
            #     for i in dictionary:
            #         print(i, dictionary[i])

            
            if data.decode() == 'collect':
                print('Returning Fire to:', self.sendIp)
                self.returnSock()
        pass

    def sockSend(self):

        self.sock.connect((self.ip, self.port))
        self.sock.send(str(self.contents).encode())
        pass

    def dataFix(self, data):

        dataList = data[1:-1].split(b', ')
        for i in dataList:
            # print(i)
            i = i.split(b': ')
            # print("I = ", i)
            dataDict[i[0][1:-1]] = float(i[1])


        return dataDict

    def returnSock(self):

        with open('location.txt', 'r') as f:
            dictionary = f.read()
            f.close()
        time.sleep(2)
        ReturnSock = Sockets(contents=dictionary, ipAddy=self.sendIp, ipPort=32323, send=True)





print("Creating Socket")
MySock = Sockets(face='ptolemy')
# MySock = Sockets(contents=b"Sockmessage Recieved", ipAddy=addr[0], ipPort=addr[1],  send=True)
