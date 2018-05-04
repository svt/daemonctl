#!/usr/bin/env python
# coding: utf8
# vim: ts=4 sw=4 et bg=dark


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

