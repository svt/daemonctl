import sys
import os
from traceback import format_exc, print_exc
from time import sleep
from glob import glob
from subprocess import Popen,PIPE,STDOUT
from .logwriter import LogWriter
from .daemon import daemonize
from pwd import getpwnam

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
    def __init__(self, name, id, command, runpath, logfile=None, pidfile=None, loop = True, interval=2.0, allwayskill=False, runas=None, venv=None,jsonlog=False,logsize=100000,numlogs=4):
        self.name = name
        self.id = id
        self.command = command
        self.runpath = runpath
        self.logfile = logfile
        self.pidfile = pidfile
        self.loop = loop
        self.interval = interval
        self.allwayskill = allwayskill
        self.runas = runas
        self.venv = venv
        self.jsonlog = jsonlog
        self.log = LogWriter(logfile,maxSize=logsize,numFiles=numlogs,jsonlog=jsonlog)
        self.pid = None
        try:
            if os.path.exists(self.pidfile):
                self.pid = int(open(self.pidfile).read())
        except:
            self.log.write(format_exc())
    
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
        stopfile = "%s.stop"%self.pidfile
        if os.path.exists(stopfile):
            os.unlink(stopfile)
        if not daemonize():
            return
        sys.stdout = self.log
        sys.stderr = self.log
        first = True
        setproctitle("daemonctl_"+self.name )
        try:
            self.pid = os.getpid()
            open(self.pidfile,"w").write(str(self.pid))
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
                            except Exception:
                                # No space left?
                                pass
                except:
                    self.log.write("ERROR;Exception: %s"%format_exc())
                self.log.write("INFO;Command ended\n")
                if os.path.exists("%s.stop"%self.pidfile):
                    self.loop = False
                    os.unlink("%s.stop"%self.pidfile)
                elif self.loop:
                    sleep(self.interval)
                    self.log.write("INFO;Restarting\n")
                else:
                    self.log.write("CRITICAL;Daemon died\n")
                    
        except:
            self.log.write(format_exc())
        if os.path.exists(self.pidfile):
            os.unlink(self.pidfile)
        sys.exit()

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
                os.kill(int(pid),9)
            except OSError as e:
                if e.errno == 3:
                    pass
                else:
                    print_exc()
        return len(pids)

    def stop(self, force=False):
        if force or self.allwayskill:
            children = self.killProcessTree()
            print("Killed %s child processes"%children)
            try:
                os.kill(self.pid,9)
            except OSError as e:
                if e.errno == 3:
                    pass
                else:
                    print_exc()
            except:
                print_exc()
            if os.path.exists(self.pidfile):
                os.unlink(self.pidfile)
        else:
            open("%s.stop"%self.pidfile,"w").write(str(self.pid))


