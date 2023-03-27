#!/usr/bin/env python

from select import poll,POLLIN, POLLPRI, POLLERR, POLLHUP, POLLNVAL
from traceback import print_exc

class SocketPoller:
    def __init__(self):
        self.poller = poll()
        self.sockets = set()
        self.sockmap = dict()
        self.revmap = dict()
        self.callbacks = dict()
    def add(self, sock, callback):
        fileno = sock.fileno()
        self.poller.register(fileno)
        self.callbacks[fileno] = (sock, callback)
    def remove(self, sock):
        fileno = sock.fileno()
        self.poller.unregister(fileno)
        if fileno in self.callbacks:
            del self.callbacks[fileno]
    def update(self, sockets):
        sockets = set(sockets)
        for sock in sockets:
            if sock not in self.sockets:
                try:
                    self.poller.register(sock.fileno(), POLLIN|POLLPRI)
                    self.sockmap[sock.fileno()] = sock
                    self.revmap[sock] = sock.fileno()
                    self.sockets.add(sock)
                    #print("Socket added: %r"%(sock,))
                except Exception:
                    print_exc()
        for sock in set(self.sockets):
            if not sock in sockets:
                try:
                    fileno = self.revmap.get(sock)
                    self.poller.unregister(fileno)
                    self.sockets.remove(sock)
                    #print("Socket removed: %r"%(sock,))
                    if fileno in self.sockmap:
                        #print("Sockmap removed: %r"%(fileno,))
                        del self.sockmap[fileno]
                    if sock in self.revmap:
                        del self.revmap[sock]
                except Exception:
                    print_exc()
    def poll(self, sockets=None, timeout=None):
        if sockets is not None:
            self.update(sockets)
        socketlist = self.poller.poll(timeout)
        #print(socketlist)
        outsocks = []
        for fileno,event in socketlist:
            if (POLLIN & event) or (POLLPRI & event):
                sock = self.sockmap.get(fileno)
                if sock is not None:
                    outsocks.append(sock)
                else:
                    sock, cb = self.callbacks.get(fileno,(None,None))
                    if cb is not None:
                        try:
                            cb(sock)
                        except Exception:
                            print_exc()

            elif (POLLERR & event):
                print("Error on socket: %r"%(sock,))
            elif (POLLHUP & event):
                print("Socket hung up: %r"%(sock,))
        return outsocks


