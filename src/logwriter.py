#!/usr/bin/wnv python

from __future__ import print_function

import os
import sys
import json
from time import asctime
from datetime import datetime


class LogWriter:
    def __init__(self, filename, maxSize = 100000000, numFiles=4, jsonlog=False):
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
        if sys.version_info[0] >= 3:
            self.fixData = bytes
        else:
            self.fixData = lambda x:x
    def write(self, data,level=False):
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
                data = "No level for data: %r"%data
        if not level in self.levels:
            self.write("Log level %r unknown, using UNKNOWN instead\n"%level,"WARNING")
            level = "UNKNOWN"
        with open(self.filename,"a") as fp:
            if fp.tell() > self.maxSize:
                num = 11
                rotFile = "%s.%d"%(self.filename,num)
                if os.path.exists(rotFile):
                    os.unlink(rotFile)
                for num in range(self.numFiles,0,-1):
                    rotFile = "%s.%d"%(self.filename,num)
                    rotNext = "%s.%d"%(self.filename,num+1)
                    if os.path.exists(rotFile):
                        os.rename(rotFile,rotNext)
                os.rename(self.filename,"%s.1"%self.filename)
                return self.write(data)
            if self.jsonlog:
                    dictdata = {
                        "@timestamp":datetime.utcnow().isoformat()+"Z",
                        "@version":1,
                        "message":data,
                        "level":level,
                        }
                    jsondata = json.dumps(dictdata).replace("\n","")+"\n"
                    return fp.write(jsondata)
            else:
                    return fp.write("%s;%s;%s\n"%(asctime(),level,data))

