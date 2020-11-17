#!/usr/bin/env python
# -*- coding: utf8 -*-
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



# Module for loading modules through pip entry points (daemonctl.modules entry group)

from pkg_resources import iter_entry_points
import os
import sys
import json
from subprocess import Popen
from pprint import pprint
from . import daemonconfig
import imp

def getentrylist():
    modules = {}
    for ep in iter_entry_points("daemonctl.modules"):
        modname = ep.module_name.split(".",1)[0]
        modules[ep.name] = ep
    return modules

def getmodlist():
    modules = {}
    for ep in iter_entry_points("daemonctl.modules"):
        modname = ep.module_name.split(".",1)[0]
        modules[modname] = ep
    return modules

def getpath(modulename):
    #modulename = func.__module__.split(".")[0]
    path = imp.find_module(modulename)[1]
    return path

def createlinks(basepath="/usr/local/scripts"):
    try:
        os.makedirs(basepath)
    except:
        pass
    for name in list(getmodlist()) + ["daemonctl"]:
        linkdest = os.path.join(basepath,name)
        mpath = getpath(name)
        linksrc = mpath
        if not os.path.exists(linkdest):
            os.symlink(linksrc,linkdest)

def run(entryname):
    modules = getentrylist()
    entry = modules.get(entryname)
    func = entry.load()
    modname = entry.module_name.split(".",1)[0]
    try:
        path = getpath(modname)
        os.chdir(path)
    except Exception as e:
        print("WARNING:Could not find/set module path %r"%(e,))
    print("INFO;Starting '%s'"%(entry,))
    func()

def list_entry():
    for name,mod in getentrylist().items():
        modname = mod.module_name.split(".",1)[0]
        path = getpath(modname)
        cfgfile = os.path.join(path,"daemonctl.conf")
        if os.path.exists(cfgfile):
            cfg = dict([[y.strip() for y in line.split("#",1)[0].split("=",1)] 
                for line in open(cfgfile).readlines() if 
                    not line.strip().startswith("#") and
                    line.strip() != ""])
        else:
            cfg = {}
        print("%s %s"%(mod.name,json.dumps(cfg)))

def run_entry(name):
    run(name)

def autostart():
    path = os.path.dirname(__file__)
    frm = os.path.join(path,"daemonctl.init")
    to = "/etc/init.d/daemonctl"
    data = open(frm,"rb").read()
    open(to,"wb").write(data)
    os.chmod(to,0o755)
    proc = Popen(["systemctl","enable","daemonctl"])
    proc.communicate()

def createinit():
    try:
        from sipy import ostool
        tool = ostool.OSTool()
    except:
        print("Error: Could not import sipy")
        return
    for name in getentrylist():
        #if not os.path.exists(os.path.join("/etc/init.d/",name)):
        if tool.createInit(name) == True:
            print("Created init-script for "+name)

def main():
    try:
        cfg = daemonconfig.Config("/usr/local/etc/daemonctl.conf")
    except Exception as e:
        cfg = dict()
    import optparse
    op = optparse.OptionParser()
    op.add_option("--autostart",help="Create and activate daemonctl init-script",action="store_true")
    op.add_option("--createinit",help="Create init-scripts",action="store_true")
    op.add_option("--createlinks","-c",help="Create symlinks to module directories",action="store_true")
    op.add_option("--list","-l",help="List modules",action="store_true")
    op.add_option("--run","-r",help="Run module")
    op.add_option("--id",help="ID for run command")
    op.add_option("--stopfile","-s",help="Stopfile for run command")
    op.add_option("--install","-i",help="install with pip from local repo")
    op.add_option("--force",help="reinstall with pip from local repo",action="store_true")
    op.add_option("--pre","-p",help="send --pre to pip",action="store_true")
    op.add_option("--oldpip",help="Old pip doesn't use --trused-host",action="store_true")
    op.add_option("--pip",help="Use alternate pip",default="pip")
    op.add_option("--user","-u",help="Install as user",action="store_true")
    o,a = op.parse_args()
    if o.list:
        list_entry()
    elif o.autostart:
        autostart()
    elif o.createinit:
        createinit()
    elif o.createlinks:
        createlinks()
    elif o.run:
        runid = o.id or o.run
        sys.argv = [o.run,"--id",runid,"--stopfile",o.stopfile]
        run_entry(o.run)
    elif o.install:
        piphost = cfg.get("piphost","pypi")
        args = [o.pip,"install",o.install,"-i","http://%(piphost)s/simple"%locals(),"--upgrade","--disable-pip-version-check",]
        if not o.oldpip:
            args += ["--trusted-host",piphost]
            args.append("--disable-pip-version-check")
        if o.force:
            args.append("--force")
        if o.pre:
            args.append("--pre")
        if o.user:
            args.append("--user")
        proc = Popen(args)
        proc.communicate()
    else:
        op.error("Must specify operation")

if __name__ == "__main__":
    main()

