#!/usr/bin/env python

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

import os
import sys
import errno
import json
from daemonctl import dts

myvenv = os.environ.get("VIRTUAL_ENV","")

dts.add_option("--list",help="List all modules",action="store_true")
dts.init("dctlmods",usecfg=False)

def msgctlCompat():
    import msgctl
    dtspath = os.path.dirname(os.path.realpath(msgctl.__file__))
    os.chdir(dtspath)
    os.environ["PYTHONPATH"] = ":".join(os.environ.get("PYTHONPATH","").split(":")+[dtspath])

class Module:
    def __init__(self, name, path):
        pass

class ModuleHandler:
    def __init__(self):
        self.modulepaths = ["/opt/daemonctl/modules","/usr/local/scripts/msgctl/modules"]
        self.moduleextentions = ["",".py",".pyc",".sh"]
        if myvenv:
            self.modulepaths.append(myvenv+"/modules")
    def createPaths(self):
        for path in self.modulepaths:
            try:
                os.makedirs(path)
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                else:
                    raise
    def getExeFile(self, modname, modpath):
        files = [modname, modname.split("-")[0]]
        for filename in files:
            for ext in self.moduleextentions:
                filepath = os.path.join(modpath,filename)+ext
                if os.path.isfile(filepath):
                    if os.access(filepath,os.X_OK):
                        return filepath
    def list(self):
        mods = {}
        for path in self.modulepaths:
            for modname in os.listdir(path):
                modpath = os.path.join(path,modname)
                if modname.startswith("."): continue
                if not os.path.isdir(modpath): continue
                modfiles = os.listdir(modpath)
                if ".disabled" in modfiles: continue
                modcfg = None
                if "daemonctl.conf" in modfiles:
                    modcfg = dts.Config(os.path.join(modpath,"daemonctl.conf"))
                    if modcfg is not None:
                        modcfg = modcfg.config
                # Feature request: Support exefile and args in config
                exefile = self.getExeFile(modname, modpath)
                if exefile is None: continue
                mods[modname] = dict(path=modpath, exefile=exefile, config=modcfg)
        return mods

def main():
    try:
        msgctlCompat()
    except:
        pass
    mh = ModuleHandler()
    mh.createPaths()
    mods = mh.list()
    if dts.opts.list:
        for name, opts in mods.items():
            cfg = opts.get("config")
            if cfg is None:
                print(name)
            else:
                cfgdump = json.dumps(cfg)
                print(name, cfgdump)
    modid = dts.opts.id
    if modid:
        mod = mods.get(modid)
        if mod is None:
            print("No such module id %r"%modid)
        else:
            exefile = mod["exefile"]
            modpath = mod["path"]
            modargs = [exefile] + sys.argv[1:]
            os.chdir(modpath)
            os.execv(exefile, modargs)


if __name__ == '__main__':
    main()

# vim: ts=4 sw=4 et
