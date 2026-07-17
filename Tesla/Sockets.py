#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from PyQt6.QtCore import QObject, QThread

import socket
from subprocess import Popen, PIPE
from threading import Thread
# TODO:BUILD — replace formlayout with PGui dialog (formlayout removed)
from socketserver import ThreadingMixIn



# use sockets to ping cell phone python program todo

class SocketThread(QThread):

    def __init__(self, parent=None):
        super(SocketThread, self).__init__(parent)
        QThread.__init__(self)

        self.Socket = parent
        print(self.Socket)

        self.ip = self.Socket.ip
        self.port = self.Socket.port
        self.sock = self.Socket.sock
        self.buffer = self.Socket.BUFFER_SIZE

        print(" New thread started for " + self.ip + ":" + str(self.port))

    def run(self):

        pass


    def fileXfer(self):
        filename = 'mytext.txt'
        f = open(filename, 'rb')
        while True:
            l = f.read(self.buffer)
            while (l):
                self.sock.send(l)
                # print('Sent ',repr(l))
                l = f.read(self.buffer)
            if not l:
                f.close()
                self.sock.close()
                break
        pass


class Sockets(QObject):

    def __init__(self, contents=None, socketType="UDP", local=True, send=False, parent=None):
        super(Sockets, self).__init__(parent)
        object.__init__(self)

        self.LOCAL_IP = self.getLocalIP()
        # TODO:SETTINGS — hardcoded port → Tesla/settings tab
        self.LOCAL_PORT = 5555
        self.PUBLIC_IP = self.getPublicIP()
        # TODO:SETTINGS — hardcoded port → Tesla/settings tab
        self.PUBLIC_PORT = 32323
        self.PHONE_IP = '174.235.132.59'
        self.BUFFER_SIZE = 1024

        if local:
            self.ip = self.LOCAL_IP
            self.port = self.LOCAL_PORT

        elif not local:
            self.ip = self.PUBLIC_IP
            self.port = self.PUBLIC_PORT

        print("LOCAL : ", self.LOCAL_IP, self.LOCAL_PORT)
        print("PUBLIC : ", self.PUBLIC_IP, self.PUBLIC_PORT)

        self.contents = contents
        self.socketType = socketType
        self.local = local
        self.send = send

        if socketType == 'TCP':
            print('Opening TCP Socket')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # TCP

        elif socketType == 'UDP':
            print('Opening UDP Socket')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # UDP

        print('Binding Socket')
        if not send:

            self.sockReceive()

        elif send:

            self.sockSend()

    # Add a 'Get Wireless Interface' function TODO
    def getLocalIP(self, iface='wlp2s0'):
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
        print('Socket Listening')

        while True:
            data, addr = self.sock.recvfrom(self.BUFFER_SIZE)

            print(data, addr)
        pass

    def sockSend(self):

        self.sock.connect((self.ip, self.port))

        pass

print("Creating Socket")
MySock = Sockets()

