#!/usr/bin/env python
# coding: utf8
# vim: ts=4 sw=4 et bg=dark

from subprocess import Popen,PIPE,STDOUT

class DaemonCLTError(Exception): pass

class DaemonCTL:
    def __init__(self, cmd="daemonctl"):
        self.cmd = cmd
    def _call(self, *args):
        proc = Popen([self.cmd]+list(args),stdout=PIPE, stderr=PIPE)
        o,e = proc.communicate()
        if e:
            raise DaemonCLTError(e)
        return o
    def hide(self, name):
        return self._call("hide",name)
    def show(self, name):
        return self._call("show",name)
    def start(self, name):
        extra = ["--exact","--showall"]
        return self._call("start",name,*extra)
    def stop(self, name, force=False):
        extra = ["--exact","--showall"]
        if force: extra.append("--force")
        return self._call("stop",name,*extra)
    def restart(self, name, force=False):
        extra = ["--exact","--showall"]
        if force: extra.append("--force")
        self._call("restart",name,*extra)
    def status(self, name="",showall=False):
        extra = ["--regex"]
        if showall: extra.append("--showall")
        left = None
        if isinstance(name,list):
            left = list(name)
            filter = "|".join(["^%s$"%f for f in name])
        else:
            filter = name
        lines = self._call("csvstatus",filter,*extra).split("\n")
        head = lines.pop(0).split(",")
        for line in lines:
            if not line: continue
            sp = line.split(",")
            obj = dict(zip(head,sp))
            if left is not None:
                try:
                    left.remove(obj.get("name"))
                except Exception as e:
                    print e
            running = bool(int(obj.get("running",0)))
            if running:
                obj["running"] = running
                obj["logchange"] = float(obj.get("logchange",-1))
                obj["starttime"] = float(obj.get("starttime",-1))
                obj["pid"] = int(obj.get("pid",-1))
                obj["found"] = True
            else:
                obj = {
                        "running":running,
                        "found":True,
                        "name":obj["name"],
                        }
            yield obj
        if left is not None:
            for l in left:
                yield {"name":l,"found":False}

if __name__ == '__main__':
    def printStatus():
        for l in d.status(["haserver","apa"],showall=showall): print l
    d = DaemonCTL()
    showall = False
    #printStatus()
    print d.start("apa")
    #print d.stop("haserver")
    #printStatus()
    #print d.start("haserver")
    #printStatus()
        
