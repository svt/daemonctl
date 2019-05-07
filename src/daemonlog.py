#!/usr/bin/python
# -*- coding: utf8 -*-
# vim: ts=4 sw=4 et bg=dark
#
# Module for handling fancy logging
#

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

from sys import exc_info
from threading import current_thread
from traceback import format_exc, format_exception, format_stack
from .fulltb import full_exc_info

if not __builtins__.get("unicode"):
    #__builtins__.unicode = str
    unicode = str
    py2 = False
    print("Emulate py2")
else:
    py2 = True

class LogLevel:
    NONE = "NONE"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    ALL = "ALL"

    levels = {
        NONE:0,
        CRITICAL:10,
        ERROR:20,
        WARNING:30,
        INFO:40,
        DEBUG:50,
        TRACE:100,
        ALL:1000,
    }

class Logger:
    level = LogLevel
    def __init__(self, name=None, format=None, level=LogLevel.ALL):
        self.setName(name)
        self.setFormat(format)
        self.setLevel(level)
        self.setEncoding("utf8")
    def setEncoding(self, encoding):
        self.encoding = encoding
    def setName(self, name):
        self.name = name
    def setFormat(self, format=None):
        if format is None:
            self.format = "%(name)s;%(message)s"
        else:
            self.format = format
    def setLevel(self, level):
        self.level = level
        self.levelid = LogLevel.levels.get(level,0)
    def log(self, level, logtext):
        levelid = LogLevel.levels.get(level,0)
        if levelid > self.levelid:
            return
        name = self.name
        thread = current_thread().name
        if not isinstance(logtext,unicode):
            logtext = unicode(logtext,encoding=self.encoding)
            #logtext = unicode(logtext).encode(self.encoding)
        if py2:
            logtext = logtext.encode(self.encoding)
        for message in logtext.split("\n"):
            print("%s;%s"%(level,self.format%locals()))
    def crit(self, msg):
        self.log(LogLevel.CRITICAL,msg)
    def warn(self, msg):
        self.log(LogLevel.WARNING,msg)
    def info(self, msg):
        self.log(LogLevel.INFO,msg)
    def debug(self, msg):
        self.log(LogLevel.DEBUG,msg)
    def exc(self, level=LogLevel.WARNING):
        self.log(level,format_exc())
    def fullexc(self, level=LogLevel.WARNING):
        self.log(level,"".join(format_exception(*full_exc_info(1))))
    
if __name__ == '__main__':
    # Remove relative import before testing
    import traceback
    log = Logger("Testlogger")
    def apa():
        try:
            raise RuntimeError("Test")
        except Exception as e:
            log.fullexc()
    def apa2():
        apa()
    apa2()


