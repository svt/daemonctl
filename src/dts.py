#!/usr/bin/python
# coding: utf8
# vim: ts=4 sw=4 et bg=dark

import sys,os
import logging
from select import select
from optparse import OptionParser
from os import path
from traceback import print_exc
from socket import gethostname
from .daemonlog import Logger,LogLevel
from .daemonconfig import Config


class autoflush:
    def __init__(self, fp):
        self.fp = fp
    def write(self,data):
        self.fp.write(data)
        self.fp.flush()
    def __getattr__(self, attr):
        return getattr(self.fp,attr)
afo = autoflush(sys.stdout)
afe = autoflush(sys.stderr)

class stdinmod:
    def __init__(self, callback):
        self.cb = callback
    def getSockets(self):
        return [sys.stdin]
    def handleSockets(self,socks):
        for s in socks:
            if s == sys.stdin:
                text=raw_input()
                self.cb(text)

from optparse import (OptionParser,BadOptionError,AmbiguousOptionError)

class PassThroughOptionParser(OptionParser):
    def _process_args(self, largs, rargs, values):
        while rargs:
            try:
                OptionParser._process_args(self,largs,rargs,values)
            except (BadOptionError,AmbiguousOptionError), e:
                largs.append(e.opt_str)

global msgsrv
modname = None # Registered name of module
msgsrv = None  # Connection to the msgsrv
msgcb = None   # Global message callback
timeout = 1.0  # Timeout for select in mainloop
cfg = {}
configfile = ""
subs = {}
stopconditions = [] # List with function that can tell main loop to exit
log = Logger("main")

sockModules = [] # List of added socket modules
# Old
#shouldstop = False # Loop variable

storage = None

oparse = PassThroughOptionParser()
oparse.add_option("--stopfile",help="Stop file")
oparse.add_option("--getname",help="Get application name",action="store_true")
oparse.add_option("--id",help="Set instance id")
oparse.add_option("--configpath",help="Path to config file",default="/usr/local/etc/")

def _msgcb(msg):
    global subs
    queue = msg.get("queuename")
    sublist = []
    if queue in subs:
            sublist += subs[queue]
    if "*" in subs:
            sublist += subs["*"]
    #log.debug("SUBLIST: %r"%([repr(sub).split("(")[1].split(",")[0] for sub in sublist if "(" in repr(sub)],))
    #log.debug("Running %r"%(msg,))
    for sub in sublist:
        try:
            sub(msg)
        except Exception:
            print_exc()

class FileChanged:
    def __init__(self, filename):
        self.filename = filename
        self.mt = os.stat(filename).st_mtime
    def __call__(self):
        try:
            return self.mt != os.stat(self.filename).st_mtime
        except Exception:
            return False

def init(modulename=None, autoreload=False, usecfg=True,cfgtypes=False,logformat=None,loglevel=None,basiclogger=True):
    """Initializes logging and other subsystems"""
    global modname,msgsrv,stopconditions,opts,args,storage,log,cfg,configfile
    try:
        opts,args = oparse.parse_args()
        if modulename is None:
            modulename = opts.id
        if modulename is None:
            modulename = os.path.split(sys.argv[0])[-1].split(".")[0]
        if opts.getname:
            print(modulename)
            sys.exit()
        if basiclogger:
            logging.basicConfig()
        sys.stdout = afo
        sys.stderr = afe
        if opts.stopfile:
            stopconditions.append(lambda :path.exists(opts.stopfile))
        namelist = []
        namelist.append(gethostname())
        if modulename:
            namelist.append(modulename)
        if opts.id:
            namelist.append(opts.id)
        if not namelist:
            raise ValueError("You need a name or id to initiate daemontools")
        modname = ":".join(namelist)
        if loglevel is None:
            loglevel = LogLevel.ALL
        # Update logging
        log.setName(modname)
        log.setFormat(logformat)
        log.setLevel(loglevel)
        if autoreload:
            stopconditions.append(FileChanged(sys.argv[0]))
        if usecfg:
            if usecfg is True:
                cfgname = modulename
            else:
                cfgname = usecfg
            configfile = os.path.join(opts.configpath,modulename+".conf")
            if os.path.exists(configfile):
                try:
                    cfg = Config(configfile,autotypes=cfgtypes)
                except Exception:
                    log.warn("Could not read config file")
                    log.exc()
            else:
                log.debug("Could not find config file %r"%(configfile,))
    except Exception:
        log.exc()
    
def exit():
    """Releases module resources and flushes buffers"""

def add_option(*arg,**marg):
    global oparse
    oparse.add_option(*arg,**marg)

def addModule(m):
    """Add socket module"""
    if hasattr(m,"getSockets") and hasattr(m,"handleSockets"):
        sockModules.append(m)

def shouldStop():
    for sc in stopconditions:
        if sc():
            return True
    return False

def serve_forever():
    """Starts mainloop. Handles modules"""
    global timeout
    try:
        while not shouldStop():
            inl = sum([x.getSockets() for x in sockModules],[])
            ins,outs,errs = select(inl,[],[],timeout)
            for m in sockModules:
                m.handleSockets(ins)
    except KeyboardInterrupt:
        log.info("Exiting. CTRL-C pressed")

