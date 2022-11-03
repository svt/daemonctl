#!/usr/bin/env python
# coding: utf-8

from traceback import print_exc
from daemonctl import dts

dts.init(usecfg=False)

print("Before trace!")
print("This shouldn't be sent")

notafunc = "This is not a function"

def func5():
	# This should fail
	notafunc()

def func4():
	func5()

def func3():
	func4()

def func2():
	func3()

def func1():
	func2()

try:
	func1()
except Exception:
	print_exc()

print("After trace!")
print("This shouldn't be sent")
