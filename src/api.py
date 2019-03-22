#!/usr/bin/env python
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
        if not isinstance(o,str):
            o = o.decode("UTF-8")
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
                    print(e)
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
        for l in d.status(["haserver","apa"],showall=showall): print(l)
    d = DaemonCTL()
    showall = False
    #printStatus()
    print(d.start("apa"))
        

