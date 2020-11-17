#!/usr/bin/python
# coding: utf8
# vim: ts=4 sw=4 et bg=dark

"""
  This file is part of daemonctl.
  Copyright (C) 2018 SVT
  
  daemonctl is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  daemonctl is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 
  You should have received a copy of the GNU General Public License
  along with daemonctl.  If not, see <http://www.gnu.org/licenses/>.

"""



import sys,os
import logging
from select import select
from optparse import OptionParser
from os import path
from traceback import print_exc
from socket import gethostname
from threading import Thread
from .daemonlog import Logger,LogLevel
from .daemonconfig import Config, EnvironConfig

# SVT specific
try:
    from pysvt.herrchef import HerrChef
except Exception as e:
    # Probably not an error
    HerrChef = None
    pass

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
            except (BadOptionError,AmbiguousOptionError) as e:
                largs.append(e.opt_str)

global msgsrv
modname = None # Registered name of module
msgsrv = None  # Connection to the msgsrv
msgcb = None   # Global message callback
hc = None      # HerrChef instance
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

def init(modulename=None, autoreload=False, usecfg=True,cfgtypes=False,logformat=None,loglevel=None,basiclogger=True,version=None):
    """Initializes logging and other subsystems"""
    global modname,msgsrv,stopconditions,opts,args,storage,log,cfg,configfile,hc
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
        if usecfg in ["env","environ"]:
            try:
                cfg = EnvironConfig()
            except Exception:
                log.warn("Could not load config from environment")
                log.exc()
        elif usecfg:
            if usecfg is True:
                cfgname = modulename
            else:
                cfgname = usecfg
            configfile = os.path.join(opts.configpath,cfgname+".conf")
            if os.path.exists(configfile):
                try:
                    cfg = Config(configfile,autotypes=cfgtypes)
                except Exception:
                    log.warn("Could not read config file")
                    log.exc()
            else:
                log.debug("Could not find config file %r"%(configfile,))
        if HerrChef is not None and version is not None:
            hc = HerrChef(modulename.split("-")[0],version)
            hc.start()
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

def poll(timeout):
    inl = sum([x.getSockets() for x in sockModules],[])
    ins,outs,errs = select(inl,[],[],timeout)
    for m in sockModules:
        m.handleSockets(ins)

def serve_forever():
    """Starts mainloop. Handles modules"""
    global timeout
    try:
        while not shouldStop():
            poll(timeout)
    except KeyboardInterrupt:
        log.info("Exiting. CTRL-C pressed")

def start_thread(daemonize=True):
    global main_thread
    def serve_and_exit():
        serve_forever()
        os._exit(0)
    main_thread = Thread(target=serve_forever)
    main_thread.daemon = daemonize
    main_thread.start()

