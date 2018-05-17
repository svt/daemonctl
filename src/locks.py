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



import os,sys
from time import time,sleep
if sys.version_info[0] >= 3:
    from io import BytesIO as StringIO
else:
    from StringIO import StringIO

class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.locked = False
        self.tfp = None
        self.rfp = None

    def __enter__(self):
        self.lock()
        return self

    def __exit__(self, exception, exarg,traceback):
        self.unlock()

    def hasLock(self):
        lockPID=int(open(self.lockfile).readline().strip())
        return os.getpid() == lockPID

    def lock(self, force=False, timeout=10):
        if self.locked:
            raise RuntimeError("Already locked.")
        start = time()
        self.lockfile = self.filename+".lock"
        gotLock = False
        while not gotLock and time()-start < timeout:
            if not force and os.path.exists(self.lockfile):
                lines = open(self.lockfile).readlines()
                if len(lines) >= 3:
                    lockPID = lines[0].strip()
                    lockProg = lines[1].strip()
                    lockTime = lines[2].strip()
                else:
                    raise RuntimeError("Corrupt lockfile: %r"%self.lockfile)
                cmdfile = "/proc/%s/cmdline"%lockPID
                print(cmdfile)
                if os.path.exists(cmdfile):
                    prog = open(cmdfile).read().split('\x00')[0]
                    if prog == lockProg:
                        t = int(time()-int(lockTime))
                        if timeout:
                            sleep(0.1)
                            continue
                        else:
                            raise RuntimeError("File locked by running application %s seconds ago."%t)
                    else:
                        print("Lockfile not locked by current holder of PID-number.")
                else:
                    print("Stale lockfile. PID does not exists.")
            gotLock = True
        fp = open(self.lockfile,"w")
        fp.write("\n".join([str(os.getpid()), open("/proc/%s/cmdline"%os.getpid()).read().split('\x00')[0], str(int(time()))])+"\n")
        fp.close()
        try:
            self.rfp = open(self.filename)
        except IOError:
            self.rfp = StringIO("")
        self.locked = True

    def unlock(self):
        if self.locked:
            if not self.hasLock():
                raise RuntimeError("Someone has stolen the lock.")
            self.rfp.close()
            if self.tfp:
                self.tfp.close()
                os.rename(self.tempfile,self.filename)
            self.tfp = None
            self.rfp = None
            os.unlink(self.lockfile)
            self.locked = False
        else:
            raise RuntimeError("File not locked.")

    def write(self, data):
        if not self.locked:
            raise RuntimeError("File not locked.")
        if not self.hasLock():
            raise RuntimeError("Someone has stolen the lock.")
        if not self.tfp:
            self.tempfile = self.filename+".tmp"
            self.tfp = open(self.tempfile,"w")
        self.tfp.write(data)

    def readlines(self):
        if not self.locked:
            raise RuntimeError("File not locked.")
        return self.rfp.readlines()
    def read(self, size=-1):
        if not self.locked:
            raise RuntimeError("File not locked.")
        return self.rfp.read(size)

    def close(self):
        self.unlock()

