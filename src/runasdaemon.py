#!/usr/bin/env python
# vim: ts=4 sw=4 et

import sys
import os
from traceback import format_exc, print_exc
from time import sleep, strftime, time
from glob import glob
from subprocess import Popen,PIPE,STDOUT
from .logwriter import LogWriter
from .daemon import daemonize
from .parsetrace import TraceParser
from pwd import getpwnam
from socket import SHUT_RDWR

try:
    # Use the setproctitle module if it's installed
    from setproctitle import setproctitle
except Exception:
    try:
        from ctypes import cdll, byref, create_string_buffer, string_at, memmove, memset
        def setproctitle(newname):
            newname = newname.replace(" ","") # Remove spaces as they may induce crashing
            libc = cdll.LoadLibrary('libc.so.6')
            buff = create_string_buffer(len(newname)+1)
            if not hasattr(__builtins__,"unicode"):
                newname = newname.encode("utf-8")
            buff.value = newname
            libc.prctl(15, byref(buff), 0, 0, 0)
            try:
                # Need linux kernel 3.5 or above for this to work
                argaddr = int(open("/proc/self/stat").read().split()[47])
                args = open("/proc/self/cmdline").read()
                argc = args.count("\x00")
                totallen = len(args)
                clipedname = newname[:totallen-1]
                memset(argaddr, 0, totallen)
                memmove(argaddr, clipedname, len(clipedname))
            except Exception:
                # Old kernel, no argv addr
                pass
    except Exception:
        setproctitle = lambda x: None


class RunAsDaemon:
    def __init__(self, name, id, command, runpath, logfile=None, pidfile=None, loop = True, interval=2.0, allwayskill=False, runas=None, venv=None,jsonlog=False,logsize=100000,numlogs=4,sendtrace=None,signum=9, logrestarts=True):
        self.name = name
        self.id = id
        self.command = command
        self.runpath = runpath
        self.logfile = logfile
        self.pidfile = pidfile
        self.loop = loop
        self.interval = interval
        self.allwayskill = allwayskill
        self.logrestarts = logrestarts
        self.traceparser = None
        self.runas = runas
        self.venv = venv
        self.jsonlog = jsonlog
        self.signum = signum
        #print("LOGFILE:"+repr(logfile))
        #print("PIDFILE:"+repr(pidfile))
        self.log = LogWriter(logfile,maxSize=logsize,numFiles=numlogs,jsonlog=jsonlog)
        self.pid = None
        if sendtrace is None:
            pass
        elif sendtrace == "herrchef":
            #print("Sending traces to herrchef")
            self.setTraceCallback(lambda data: self.larmToHerrChef(data[-1].strip(),2))
        else:
            print("Unknown sendtrace option %r"%(sendtrace,))
        self.pid = self.readPID()
    
    def readPID(self):
        try:
            if os.path.exists(self.pidfile):
                return int(open(self.pidfile).read())
            return None
        except:
            self.log.write(format_exc())
            return None
    def sendToHerrChef(self, command, message="", level=None):
        try:
            from pysvt.herrchef import HerrChef
        except Exception:
            return
        try:
            import logging
            rl = logging.getLogger("")
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            rl.addHandler(h)
            rl.setLevel(logging.WARNING)
            hc = HerrChef(self.name,command)
            curtime = strftime("%Y-%m-%d;%H:%M:%S")
            reporthost = hc.reporthost
            name = self.name
            if level is not None:
                info = "%s;%s"%(level,message)
            else:
                info = message
            larm = "%(command)s;%(curtime)s;%(reporthost)s;%(name)s;%(info)s\r\n"%locals()
            hc.connect()
            if not hc.connected:
                return
            hc.send(larm)
            hc.socket.shutdown(SHUT_RDWR)
            hc.socket.close()
        except Exception as e:
            print("Warning: Could not contact herrchef %r"%(e,))
    def reportToHerrChef(self, command):
        self.sendToHerrChef(command)
    def larmToHerrChef(self, message, level):
        self.sendToHerrChef("LARM", message, level)
    def setTraceCallback(self, callback):
        self.traceparser = TraceParser(callback)

    def parseLine(self, line):
        try:
            if self.traceparser is not None:
                self.traceparser.parse(line)
        except Exception as e:
            print("Error in traceparser: %s"%(e,))

    def running(self):
        if self.pid:
            if os.path.exists("/proc/%s/cmdline"%self.pid):
                try:
                    cmdline = open("/proc/%s/cmdline"%self.pid).read()
                except:
                    return False
                return True
            else:
                return False
        else:
            return False

    def run(self):
        self.reportToHerrChef("START")
        stopfile = "%s.stop"%self.pidfile
        if os.path.exists(stopfile):
            os.unlink(stopfile)
        if not daemonize():
            while not self.readPID():
                sleep(0.01)
            return
        sys.stdout = self.log
        sys.stderr = self.log
        first = True
        setproctitle("daemonctl_"+self.name )
        try:
            self.pid = os.getpid()
            open(self.pidfile,"w").write(str(self.pid))
            self.log.write("INFO;Starting daemon")
            while self.loop or first:
                first = False
                try:
                    id = self.id
                    pidfile = self.pidfile
                    logfile = self.logfile
                    cmd = self.command%vars()
                    if self.venv:
                        cmd = "source %s/bin/activate;%s"%(self.venv,cmd)
                    if self.runpath:
                        os.chdir(self.runpath)
                    if self.runas != None:
                        user = getpwnam(self.runas)
                        os.chown(logfile,user.pw_uid,0)
                        os.setgroups([])
                        os.setgid(user.pw_gid)
                        os.setuid(user.pw_uid)
                    os.environ["PYTHONIOENCODING"] = "utf-8"
                    proc = Popen(cmd,shell=True,stdout=PIPE,stderr=STDOUT,stdin=PIPE)
                    foo,fp = (proc.stdin,proc.stdout)
                    data = True
                    while data:
                        data = fp.readline()
                        if data:
                            try:
                                self.log.write(data)
                                self.parseLine(data)
                            except Exception:
                                # No space left?
                                pass
                except:
                    self.log.write("ERROR;Exception: %s"%format_exc())
                if self.logrestarts:
                    self.log.write("INFO;Command ended\n")
                if self.checkStopfile():
                    self.endloop()
                elif self.loop:
                    if self.loopWait() and self.logrestarts:
                        self.log.write("INFO;Restarting\n")
                else:
                    self.log.write("CRITICAL;Daemon died\n")
        except:
            self.log.write(format_exc())
        if os.path.exists(self.pidfile):
            os.unlink(self.pidfile)
        sys.exit()
    def checkStopfile(self):
        return os.path.exists("%s.stop"%self.pidfile)
    def endloop(self):
        self.loop = False
        os.unlink("%s.stop"%self.pidfile)
        self.log.write("INFO;Stopping daemon")
    def loopWait(self):
        next = time() + self.interval
        while next > time():
            if self.checkStopfile():
                self.endloop()
                return False
            sleep(0.1)
        return True

    def findChildren(self, pid=None):
        if pid is None:
            pid = self.pid
        children = []
        for statusfile in glob("/proc/*/status"):
            try:
                with open(statusfile) as fp:
                    lines = fp.readlines()
                    status = dict([(y.strip(),z.strip()) for y,z in [x.strip().split(":",1) for x in lines if ":" in x]])
                    childpid = status["Pid"]
                    ppid = status["PPid"]
                    if ppid == str(pid):
                        children.append(childpid)
                        children += self.findChildren(childpid)
            except IOError as e:
                if e.errno == 2:
                    pass
                else:
                    print_exc()
            except:
                print("Not OSError or IOError")
                print_exc()
        return children
        
    def killProcessTree(self,pid=None):
        pids = self.findChildren(pid)
        for pid in pids:
            print("Killing pid: %s"%(pid,))
            try:
                os.kill(int(pid),self.signum)
            except OSError as e:
                if e.errno == 3:
                    pass
                else:
                    print_exc()
        return len(pids)

    def stop(self, force=False, sigterm = False):
        self.reportToHerrChef("STOP")
        if sigterm:
            self.signum = 15
        if not force or sigterm:
            open("%s.stop"%self.pidfile,"w").write(str(self.pid))
        if force or self.allwayskill:
            children = self.killProcessTree()
            print("Killed %s child processes"%children)
            if not sigterm:
                try:
                    os.kill(self.pid,self.signum)
                except OSError as e:
                    if e.errno == 3:
                        pass
                    else:
                        print_exc()
                except:
                    print_exc()
                if os.path.exists(self.pidfile):
                    os.unlink(self.pidfile)


