#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 et bg=dark

__version__ = '1.3.7a3'

appname = "daemonctl"
appdesc = "Utility and framework for simplifying application deployment and operation"
appversion = __version__
author = "Andreas Åkerlund"
author_email = "andreas.akerlund@svt.se"
dependencies = []
scripts = [
    "daemonctl = daemonctl.main:main",
    "dpiptool = daemonctl.piptool:main",
]
