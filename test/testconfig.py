#!/usr/bin/env python

from __future__ import print_function

import common

from src.daemonconfig import Config, EnvironConfig


cfg = Config("testdata/test1.conf")
assert cfg.testconf.test1 == "apa1"

ecfg = EnvironConfig("testdata/teste.conf")

print(ecfg.testconf.test1)
