#!/usr/bin/env python
# -*- coding: utf8 -*-
# vim: ts=4 sw=4 et bg=dark

# Module for loading modules through pip entry points (daemonctl.modules entry group)

from pkg_resources import iter_entry_points
import os
import sys
import json
from subprocess import Popen
from pprint import pprint
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
    #print "MODS:",modules
    entry = modules.get(entryname)
    #print "Entry:",entry
    #sys.argv = [entry.name,"--id",entry.name]
    func = entry.load()
    #print "Func:",func
    modname = entry.module_name.split(".",1)[0]
    try:
        path = getpath(modname)
        #print "Path:",path
        os.chdir(path)
    except Exception as e:
        print("WARNING:Could not find/set module path %r"%(e,))
    print("INFO;Starting '%s'"%(entry,))
    func()

def list_entry():
    for name,mod in getentrylist().items():
        #print dir(mod)
        #print mod.module_name
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
        print mod.name,json.dumps(cfg)

def run_entry(name):
    run(name)

def autostart():
    path = os.path.dirname(__file__)
    frm = os.path.join(path,"daemonctl.init")
    to = "/etc/init.d/daemonctl"
    data = open(frm,"rb").read()
    open(to,"wb").write(data)
    os.chmod(to,0755)
    proc = Popen(["systemctl","enable","daemonctl"])
    proc.communicate()

def createinit():
    try:
        from sipy import ostool
        tool = ostool.OSTool()
    except:
        print "Error: Could not import sipy"
        return
    for name in getentrylist():
        #if not os.path.exists(os.path.join("/etc/init.d/",name)):
        if tool.createInit(name) == True:
            print "Created init-script for "+name

def main():
    # Tests
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
        args = ["pip","install",o.install,"-i","http://pypi.svt.se/simple","--upgrade",]
        if not o.oldpip:
            args += ["--trusted-host","pypi.svt.se"]
        if o.force:
            args.append("--force")
        if o.pre:
            args.append("--pre")
        proc = Popen(args)
        proc.communicate()
    else:
        op.error("Must specify operation")

if __name__ == "__main__":
    main()
