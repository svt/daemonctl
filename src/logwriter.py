#!/usr/bin/wnv python

from __future__ import print_function

import os
import sys
import json
import gzip
from time import asctime
from datetime import datetime


class LogWriter:
    def __init__(self, filename, maxSize = 100000000, numFiles=4, jsonlog=False, gzip=True):
        self.filename = filename
        self.maxSize = maxSize
        self.numFiles = numFiles
        self.levels = ["CRITICAL","ERROR","WARNING","UNKNOWN","INFO","DEBUG","DEBUG2","DEBUG3"]
        self.levelmap = {
            "CRITICAL":1000,
            "ERROR":950,
            "WARNING":900,
            "UNKNOWN":850,
            "INFO":800,
            "DEBUG":500,
            "DEBUG2":400,
            "DEBUG3":300,
            }
        self.jsonlog = jsonlog
        self.gzip = gzip
        if sys.version_info[0] < 3:
            self.fixData = lambda x:x
            self.prepareOut = lambda x:x
    def fixData(self, data):
        if isinstance(data, bytes):
            return repr(data)
        return data
    def prepareOut(self, fileobj):
        for data in fileobj:
            if not isinstance(data, bytes):
                yield bytes(data,"utf-8")
            else:
                yield data
    def write(self, data, level=False):
        data = self.fixData(data)
        if "\n" in data:
            lines = data.split("\n")
            for line in lines:
                self.write(line)
            return
        data = data.strip()
        if not data:
            return
        if not level:
            if ";" in    data[:10]:
                l = data.split(";")[0]
                if l in self.levels:
                    level = l
                    data = data[len(l)+1:]
                else:
                    level = "UNKNOWN"
                    #data = "No level for data: %r"%data
            else:
                level = "DEBUG"
                #data = "No level for data: %r"%data
        if not level in self.levels:
            self.write("Log level %r unknown, using UNKNOWN instead\n"%level,"WARNING")
            level = "UNKNOWN"
        with open(self.filename,"a") as fp:
            if fp.tell() > self.maxSize:
                num = self.numFiles + 1
                rotFile = "%s.%d"%(self.filename,num)
                rotFileGz = "%s.gz"%(rotFile,)
                if os.path.exists(rotFile):
                    os.unlink(rotFile)
                if os.path.exists(rotFileGz):
                    os.unlink(rotFileGz)
                for num in range(self.numFiles,-1,-1):
                    if num == 0:
                        rotFile = self.filename
                    else:
                        rotFile = "%s.%d"%(self.filename, num)
                    rotNext = "%s.%d"%(self.filename, num+1)
                    rotFileGz = "%s.gz"%(rotFile,)
                    rotNextGz = "%s.gz"%(rotNext,)
                    if os.path.exists(rotFile):
                        if self.gzip:
                            with open(rotFile) as srcFile:
                                with gzip.open(rotNextGz,"wb") as dstFile:
                                    dstFile.writelines(self.prepareOut(srcFile))
                            os.unlink(rotFile)
                        else:
                            os.rename(rotFile, rotNext)
                    if self.gzip and os.path.exists(rotFileGz):
                        os.rename(rotFileGz, rotNextGz)
                return self.write(data)
            if self.jsonlog:
                dictdata = {
                    "@timestamp":datetime.utcnow().isoformat()+"Z",
                    "@version":1,
                    "message":data,
                    "level":level,
                    }
                jsondata = json.dumps(dictdata).replace("\n","")+"\n"
                try:
                    return fp.write(jsondata)
                except Exception:
                    # Unable to write log (no space left on device?)
                    pass
            else:
                try:
                    timestamp = datetime.now().isoformat(" ")
                    return fp.write("%s;%s;%s\n"%(timestamp, level, data))
                except Exception:
                    # Unable to write log (no space left on device?)
                    pass

# vim: ts=4 sw=4 et
