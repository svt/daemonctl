#!/usr/bin/env python


package = "src"

from optparse import OptionParser
from re import compile
vre = compile("([0-9]+)\.([0-9]+)\.([0-9]+)([a-z]?)([0-9]*)")

op = OptionParser()
# dev (d) is unsupported by PEP 440
#op.add_option("--dev",help="Bump dev version",action="store_true")
op.add_option("--rc",help="Bump rc version",action="store_true")
op.add_option("--alpha",help="Bump alpha version",action="store_true")
op.add_option("--beta",help="Bump beta version",action="store_true")
op.add_option("--patch",help="Bump patch version",action="store_true")
op.add_option("--minor",help="Bump minor version",action="store_true")
op.add_option("--major",help="Bump major version",action="store_true")
op.add_option("--release",help="Set release version",action="store_true")

o,a = op.parse_args()

versionfile ="%s/__init__.py"%(package,)
code = open(versionfile).read()
#print(code)
exec(code)
#__version__ = "1.2.5a10"
print(__version__)
match = vre.match(__version__)
print(match.group(5))

version = __version__
major = int(match.group(1))
minor = int(match.group(2))
patch = int(match.group(3))
pre = match.group(4)
prever = match.group(5)
if prever:
	prever = int(prever)+1
else:
	prever = 1

#if o.dev:
#	if pre != "d": prever = 1
#	pre = "d"
#	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
if o.alpha:
	if pre != "a": prever = 1
	pre = "a"
	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
elif o.beta:
	if pre != "b": prever = 1
	pre = "b"
	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
elif o.rc:
	if pre != "c": prever = 1
	pre = "c"
	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
elif o.patch:
	pre = "a"
	prever = 1
	patch += 1
	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
elif o.minor:
	pre = "a"
	prever = 1
	patch = 0
	minor += 1
	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
elif o.major:
	pre = "a"
	prever = 1
	patch = 0
	minor = 0
	major += 1
	version = "%d.%d.%d%s%d"%(major,minor,patch,pre,prever)
if o.release:
	version = "%d.%d.%d"%(major,minor,patch)

print version
buff = ""
for line in open(versionfile).readlines():
	if line.startswith("__version__"):
		buff += "__version__ = '%s'\n"%version
	else:
		buff += line
open(versionfile,"wb").write(buff)

