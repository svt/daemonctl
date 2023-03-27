#!/usr/bin/env python

from __future__ import print_function
import common
from time import time as now, asctime as ascnow

from socket import create_connection
from pysvt.hmux import HMUXHandler

from src import dts

dts.init(usecfg=False, usenewpoll=True)
#dts.init(usecfg=False)

start = now()

class TestClient:
    def __init__(self, name):
        self.name = name
        self.sock = create_connection(("google.com",80))
        self.sock.send("GET /\r\n\r\n")
        #dts.socketpoller.add(self.sock, self.sockcb)
    def getSockets(self):
        if self.sock is not None:
            return [self.sock]
        return []
    def handleSockets(self, socks):
        for s in socks:
            if s is self.sock:
                self.poll()
    def sockcb(self, sock):
        self.poll()
    def poll(self):
        data = self.sock.recv(65535)
        if not data:
            #dts.socketpoller.remove(self.sock)
            self.sock = None
            print("Timed: %r"%(now()-start))
        print("%r got '%s...'"%(self.name,data[:10]))

class TestServer:
    def __init__(self):
        self.hmux = HMUXHandler(11223,None, "\r\n",self.hmuxcb,self.hmuxcon,clientToCallback=True)
        dts.addModule(self.hmux)
    def hmuxcon(self, client):
        print("Connect: %r"%(client.addr,))
    def hmuxcb(self, data, src, client):
        print("CB: %r %r %r"%(data,src,client.addr))
        client.send("OK CLIENT\r\n")
        #self.hmux.send("OK ALL\r\n")
        return "OK RETURN\r\n"

def testclient():
    for n in range(50):
        tc = TestClient("Client(%r)"%(n,))
        dts.addModule(tc)

def testserver():
    ts = TestServer()


testserver()
dts.serve_forever()
