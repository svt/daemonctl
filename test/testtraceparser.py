#!/usr/bin/env python

from __future__ import print_function

import common

from src.parsetrace import TraceParser


result = []
def gotTrace(data):
	global result
	#print(repr(data))
	result += data

parser = TraceParser(gotTrace)

def stripline(line):
	if not line.strip():
		return ""
	line = line.split(";",1)[1]
	line = line.strip()
	return line

def addFile(filename):
	for line in open(filename).readlines():
		line = stripline(line)
		#print(line)
		parser.parse(line)

addFile("testdata/notrace.log")
addFile("testdata/onetrace.log")
addFile("testdata/printtrace.log")

expected = ['Traceback (most recent call last):', 'File "/usr/local/scripts/msgctl/modules/dbgw/dbgw.py", line 124, in run', 'self.client._sender_oldsend(data)', 'File "/usr/lib/python2.7/site-packages/pysvt/hmux.py", line 56, in send', 'self.socket.sendall(sd)', 'File "/usr/lib64/python2.7/socket.py", line 224, in meth', 'return getattr(self._sock,name)(*args)', 'timeout: timed out']

if result != expected:
	raise ValueError("Result doesn't match expected result")
else:
	print("OK")
