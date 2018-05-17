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




import os
import resource

class DaemonizeError(Exception): pass

def daemonize():
   try:
      pid = os.fork()
   except OSError as e:
      raise DaemonizeError("%s [%d]" % (e.strerror, e.errno))

   if (pid == 0):
      os.setsid()

      try:
         pid = os.fork()
      except OSError as e:
         raise DaemonizeError("%s [%d]" % (e.strerror, e.errno))

      if (pid != 0):
         os._exit(0)
   else:
      return False

   fds = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
   if (fds == resource.RLIM_INFINITY):
      fds = 1024
  
   for fd in range(0, fds):
      try:
         os.close(fd)
      except OSError:
         pass

   # Redirect stdio to /dev/null
   os.open("/dev/null", os.O_RDWR) # stdin
   os.dup2(0, 1) # stdout
   os.dup2(0, 2) # stderr

   return True


