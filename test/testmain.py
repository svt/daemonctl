#!/usr/bin/env python

from __future__ import print_function
import common
import sys
import os
from time import sleep

class FakeChef:
	def __init__(self, name):
		self.name = name
		self.reporthost = "testhost"
		class FakeSock:
			def shutdown(self, opt):
				return None
			def close(self):
				return None
		self.socket = FakeSock()
	def send(self, message):
		print("INFO;FAKELARM: %s"%(message,))

try:
	import pysvt.herrchef
	pysvt.herrchef.HerrChef = FakeChef
except:
	print("No herrchef")

basepath = os.path.realpath(".") + "/"

if not "reload" in dir(__builtins__):
	from importlib import reload

def test(args):
	sys.argv = args
	import src
	reload(src)
	import src.main
	reload(src.main)
	from src.main import main
	def fakeModules():
		mypath = basepath
		return dict(
				fakedyn = dict(
					name = "%(id)s",
					type = "dynamic",
					loop = "True",
					logpath = basepath,
					pidpath = basepath,
					loopinterval = "1",
					listcmd = "echo 'd1\nd2\nd3 {\"logrestarts\":\"false\"}'",
					execcmd = "echo Output from %(id)s",
					),
				print_trace = dict(
					name = "%(id)s",
					type = "dynamic",
					loop = "True",
					logpath = basepath,
					pidpath = basepath,
					loopinterval = "1",
					listcmd = "echo 'st {\"sendtrace\":\"herrchef\"}\nnotworking'",
					execcmd = "python %(mypath)s/print_trace.py"%locals(),
					),
				fakesingle = dict(
					name = "single1",
					type = "single",
					loop = "True",
					loopinterval = "1.5",
					logpath = basepath,
					pidpath = basepath,
					execcmd = "echo Command output: single"
					),
				)
	src.main.getModules = fakeModules
	main()

def runmany(args,names):
	for name in names:
		testargs = args+[name]
		test(testargs)
def startstop(name, wait=0):
	if not isinstance(name, list):
		names = [name]
	else:
		names = name
	runmany(["main","start"],names)
	test(["main","status"])
	sleep(wait)
	runmany(["main","stop"],names)

test(sys.argv)
#test(["main","status"])
#startstop("d1")
#startstop(["d2","d3","single1"],2)
#startstop("st",1)

