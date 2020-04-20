#!/usr/bin/env python
# vim: ts=4 sw=4 et

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



from __future__ import print_function

import sys,os
#sys.path.append(os.environ["HAWRYSRUNDOWN_INC_DIR"])
from pwd import getpwnam
from .logwriter import LogWriter
from .runasdaemon import RunAsDaemon
from time import sleep,asctime,ctime
from traceback import format_exc,print_exc
from glob import glob
from subprocess import Popen,PIPE,STDOUT
from datetime import datetime
from optparse import OptionParser
from pprint import pprint
import re
import fnmatch
import json
import distutils
import distutils.spawn
from .daemonconfig import Config

myvenv = os.environ.get("VIRTUAL_ENV","")
configpath = os.environ.get("DAEMONCTL_CONFIG",myvenv+"/usr/local/etc/daemonctl.conf")

op = OptionParser()
op.add_option("-f","--force",action="store_true",default=False)
op.add_option("-r","--regex",help="Select daemons using regexp only",action="store_true",default=False)
op.add_option("-g","--glob",help="Select daemons using globbing only",action="store_true",default=False)
op.add_option("-e","--exact",help="Select daemons using exact match only",action="store_true",default=False)
op.add_option("-c","--config")
op.add_option("-a","--showall",help="Show hidden",action="store_true",default=False)
op.add_option("-v","--version",help="Print version",action="store_true",default=False)
opts,args = op.parse_args()

if opts.version:
    from . import __version__ as version
    print("Daemonctl version %s"%(version,))
    exit(0)

if not opts.regex and not opts.glob and not opts.exact:
    opts.regex = True
    opts.glob = True

if opts.config:
    configpath = opts.config

try:
    cfg = Config(configpath)
except:
    defaultconfig = os.path.join(os.path.dirname(__file__),"daemonctl.conf")
    #print("Loading conf from",defaultconfig)
    cfg = Config(defaultconfig)
#os.nice(10)

logdir = myvenv+cfg.logpath
piddir = myvenv+cfg.pidpath
if not os.path.exists(logdir):
    os.makedirs(logdir)
if not os.path.exists(piddir):
    os.makedirs(piddir)
try:
    os.chmod(logdir,0o1777)
except:
    pass

class Hidden:
    def __init__(self, config):
        self.config = config
        self.lst = set()
        try:
            self.load()
        except:
            pass
    def save(self):
        open(self.config,"w").write("\n".join(self.lst))
    def load(self):
        self.lst = set(open(self.config).read().decode("utf-8").split("\n"))
    def add(self, name):
        if sys.version_info[0] < 3 and isinstance(name,str): name = name.decode("utf-8")
        name = name.strip()
        self.lst.add(name)
        self.save()
    def remove(self, name):
        name = name.strip()
        if sys.version_info[0] < 3 and isinstance(name,str): name = name.decode("utf-8")
        self.lst.remove(name)
        self.save()
    def ishidden(self, name):
        name = name.strip()
        if sys.version_info[0] < 3 and isinstance(name,str): name = name.decode("utf-8")
        #pprint(name)
        #pprint(self.lst)
        return name in self.lst

log = LogWriter("%s/daemonctl.log"%logdir,numFiles=2,jsonlog=cfg.get("jsonlog",False))


def init():
    # Run once to ensure systemfiles are installed
    destfile = "daemonctl.complete"
    destpath = "/etc/bash_completion.d/"
    fulldest = os.path.join(destpath,destfile)
    if not os.path.exists(fulldest) and os.path.isdir(destpath):
        mypath = os.path.realpath(__file__)
        modpath = os.path.dirname(mypath)
        compfile = os.path.join(modpath,destfile)
        with open(compfile,"rb") as src:
            open(fulldest,"wb").write(src.read())


def main():
    usage = """Usage: daemonctl <command> [daemon]
     Commands:
        start        Start daemons
        stop         Stop daemons ("-f" to force)
        restart      Restart daemons (stop+start)
        forcestop    Force daemons to stop (kill -9)
        status       Get daemon status
        enable       Enable an application
        disable      Disable an application
        hide         Hide daemon from status
        show         Unhide daemon from status
        tail         Tail a daemon log
        less         Less a daemon log
        csvstatus    Get daemon status in csv format
    """
    try:
        init()
    except Exception as e:
        print(e)
    if len(args) < 1:
        print(usage)
        sys.exit(1)

    filtertext = ".*"
    if len(args) > 1:
        if args[1] == "all":
            filtertext = ".*"
        else:
            filtertext = args[1]
    elif args[0] in ["status","csvstatus","list"]:
            filtertext = ".*"
    else:
        print("Please choose one or more daemons.")
        print("You can use regexp, full daemon names or the word 'all'")
        sys.exit(1)

    try:
        daemonfilter = re.compile(filtertext)
    except Exception as e:
        daemonfilter = None
        opts.regex = False
    daemons = dict()
    globalpath = cfg.get("modulepath",myvenv+"/usr/local/scripts/daemonctl/modules/")
    modules = {}

    dpip = dict(
        name = "%(id)s",
        execcmd = "dpiptool --run %(id)s --stopfile %(stopfile)s",
        type = "dynamic",
        listcmd = "dpiptool --list",
        loop = "1",
        interval = "10",
    )
    modules["dpip"] = dpip

    if "modules" in cfg:
        for modname in cfg.modules.list():
            mod = cfg.modules[modname]
            modules[modname] = mod
    if not myvenv and not "msgctl" in modules and distutils.spawn.find_executable("msgctl"):
        msgctl = dict(
            name = "%(id)s",
            type = "dynamic",
            loop = "True",
            interval = "5",
            listcmd = "msgctl --list",
            execcmd = "msgctl --id %(id)s --stopfile %(stopfile)s",
        )
        modules["msgctl"] = msgctl
    elif not "msgctl" in modules:
        # Builtin msgctl replacement
        dctlmods = dict(
            name = "%(id)s",
            type = "dynamic",
            loop = "True",
            interval = "5",
            listcmd = "dctlmods --list",
            execcmd = "dctlmods --id %(id)s --stopfile %(stopfile)s",
        )
        modules["dctlmods"] = dctlmods
            

    for modname,mod in modules.items():
        mt = mod.get("type","single")
        if mt == "single":
            cmd = mod.get("path",globalpath) + mod.get("execcmd")
            runpath = mod.get("path",None)
            logpath = mod.get("logpath",logdir)+mod.get("name")+".log"
            logsize = mod.get("logsize",50000000)
            logfiles = mod.get("logfiles",4)
            pidpath = mod.get("pidpath",piddir)+mod.get("name")+".pid"
            loop = 0 if mod.get("loop","0").lower() in ["0","false","off","no"] else 1
            interval = float(mod.get("loopinterval",10))
            forcekill = 0 if mod.get("forcekill","0").lower() in ["0","false","off","no"] else 1
            interval = float(mod.get("loopinterval",10))
            runas = mod.get("runas",None)
            venv = mod.get("virtualenv",None)
            jsonlog = 0 if mod.get("jsonlog","0").lower() in ["0","false","off","no"] else 1
            daemons[mod.get("name")] = (mod.get("name"), "", cmd, runpath, logpath, pidpath, loop, interval, forcekill, runas, venv, jsonlog, logsize, logfiles)
        else:
            path = mod.get("path")
            if path:
                listcmd = path + mod.get("listcmd")
            else:
                listcmd = mod.get("listcmd")
            for line in os.popen(listcmd):
                sp = line.split(None,1)
                id = sp.pop(0).strip()
                try:
                    icfg = json.loads(sp[0])
                except:
                    icfg = {}
                name = mod.get("name")%vars()
                if path:
                    cmd = path + mod.get("execcmd")
                    runpath = path
                else:
                    cmd = mod.get("execcmd")
                    runpath = "/tmp/"
                logpath = mod.get("logpath",logdir)+name+".log"
                pidpath = mod.get("pidpath",piddir)+name+".pid"
                logsize = mod.get("logsize",50000000)
                logfiles = mod.get("logfiles",4)
                loop = 0 if icfg.get("loop",mod.get("loop","0")).lower() in ["0","false","off","no"] else 1
                interval = float(icfg.get("loopinterval",mod.get("loopinterval",10)))
                forcekill = 0 if icfg.get("forcekill",mod.get("forcekill","0")).lower() in ["0","false","off","no"] else 1
                runas = icfg.get("runas",mod.get("runas",None))
                venv = icfg.get("virtualenv",mod.get("runas",None))
                jsonlog = 0 if icfg.get("jsonlog",mod.get("jsonlog","0")).lower() in ["0","false","off","no"] else 1
                #daemons[name] = (name, id, cmd, runpath, logpath, pidpath, loop, interval, forcekill, runas, venv, jsonlog)
                daemons[name] = (name, id, cmd, runpath, logpath, pidpath, loop, interval, forcekill, runas, venv, jsonlog, logsize, logfiles)
    #(id, command, logfile=None, pidfile=None, loop = True, interval=2.0, allwayskill=False)

    #daemons["deletedaemon"] = ("%s/deleteOld.py"%(bindir),"%s/deleteOld.log"%(logdir),"%s/deleteOld.pid"%(rundir))
    #print("List loaded")

    hide = Hidden(cfg.get("hidepath",myvenv+"/var/run/daemonctl/hide.list"))

    if len(args)>=1 and args[0] == "status":
        print("Daemon name                     Status, PID Number,             Start time         ,        Modification time of logfile")
        print("----------------------------------------------------------------------------------------------------------------------------")
    elif len(args)>=1 and args[0] == "csvstatus":
            print("name,running,pid,starttime,logchange,version")
    elif len(args)>=2 and args[0] == "hide":
        hide.add(args[1])
        print("Hiding %r"%args[1])
        exit(0)
    elif len(args)>=2 and args[0] == "show":
        hide.remove(args[1])
        print("Unhiding %r"%args[1])
        exit(0)
    elif len(args)>=2 and args[0] == "enable":
        name = args[1]
        base = name.split("-",1)[0]
        print("Enabling %s as %s"%(base,name))
        srcpath = myvenv+"/usr/local/scripts/%s"%(base,)
        destpath = myvenv+"/usr/local/scripts/msgctl/modules/%s"%(name,)
        if not os.path.exists(srcpath):
            print("No such application")
            exit(1)
        if os.path.exists(destpath):
            print("Application already enabled")
            exit(1)
        os.symlink(srcpath,destpath)
        print("%s enabled"%(name,))
        exit(0)
    elif len(args)>=2 and args[0] == "disable":
        name = args[1]
        print("Disabling %s"%(name,))
        destpath = myvenv+"/usr/local/scripts/msgctl/modules/%s"%(name,)
        if not os.path.exists(destpath):
            print("Application not enabled")
            exit(1)
        os.unlink(destpath)
        print("%s disabled"%(name,))
        exit(0)
    found = False
    for daemon,daemonargs in sorted(daemons.items()):
        hidden = hide.ishidden(daemon)
        if hidden and not opts.showall:
            continue
        if (not (opts.regex and daemonfilter.match(daemon))
          and not (opts.glob and fnmatch.fnmatch(daemon,filtertext))
          and not (opts.exact and daemon == filtertext)):
            continue
        found = True
        r = RunAsDaemon(*daemonargs)
        if len(args)>=1 and args[0] == "stop":
            if r.running():
                print("Stopping %s"%daemon)
                log.write("INFO;Stoping %s\n"%daemon)
                r.stop(opts.force)
                while r.running():
                    sleep(0.1)
            else:
                print("%s is not running"%daemon)
                continue
        elif len(args)>=1 and args[0] == "forcestop":
            if r.running():
                print("Killing %s"%daemon)
                log.write("INFO;Killing %s\n"%daemon)
                r.stop(force=True)
                while r.running():
                    sleep(0.1)
            else:
                print("%s is not running"%daemon)
                continue
        elif len(args)>=1 and args[0] == "tail":
            cmd = "tail -F %s"%r.logfile
            print("Running %r"%cmd)
            os.system(cmd)
        elif len(args)>=1 and args[0] == "less":
            cmd = "less %s"%r.logfile
            print("Running %r"%cmd)
            os.system(cmd)
        elif len(args)>=1 and args[0] == "status":
            try:
                starttime = os.stat(r.pidfile).st_mtime
                logchanged = os.stat(r.logfile).st_mtime
            except:
                starttime = 0
                logchanged = 0
            print("%s %s"%(daemon.ljust(30),"running, pid: %5s, since: %s, last activity: %s"%(r.pid,ctime(starttime), ctime(logchanged)) if r.running() else "not running"))
        elif len(args)>=1 and args[0] == "csvstatus":
            try:
                starttime = os.stat(r.pidfile).st_mtime
                logchanged = os.stat(r.logfile).st_mtime
            except:
                starttime = 0
                logchanged = 0
            version = ""
            changelog = os.path.join("/usr/local/scripts",r.id,"CHANGELOG")
            if os.path.exists(changelog):
                try:
                    version = open(changelog).readline().strip()
                except:
                    pass
            print("%s,%s"%(daemon,"1,%s,%s,%s,%s"%(r.pid,starttime,logchanged,version) if r.running() else "0,0,0,0,"))
        elif len(args)>=1 and args[0] == "list":
            print(daemon)
        elif len(args)>=1 and args[0] == "start":
            if r.running():
                print("%s is already running, not starting"%daemon)
            else:
                print("Starting %s"%daemon)
                log.write("INFO;Starting %s\n"%daemon)
                r.run()
        elif len(args)>=1 and args[0] == "restart":
            if r.running():
                print("Restarting %s"%daemon)
                log.write("INFO;Restarting %s (stop)\n"%daemon)
                r.stop(opts.force)
                while r.running():
                    sleep(0.1)
                log.write("INFO;Restarting %s (start)\n"%daemon)
                r.run()
                print("Restarted %s"%daemon)
            else:
                print("%s is not running"%daemon)
                continue
        elif len(args)>=1 and args[0] in ("hide","show","enable","disable"):
            pass
        else:
            print("Unknown command: %r"%args[0])
            print(usage)
            break
    if not found and not "csv" in args[0]:
        print("No daemon match %r"%(filtertext,),file=sys.stderr)
if __name__ == "__main__":
    main()

