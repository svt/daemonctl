#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 et bg=dark

import os
from setuptools import setup
#import fastentrypoints
import src

def read(filename):
    try:
        return open(os.path.join(os.path.dirname(__file__),filename)).read()
    except:
        return "Missing readme"
package = src.appname
scripts = getattr(src,"scripts",[])
daemonctl = getattr(src,"daemonctl",[])

setup(
    name=package,
    version=src.__version__,
    author=src.author,
    author_email=src.author_email,
    license="SVT internal",
    keywords="Python example package",
    url="https://github.com/SVT/daemonctl",
    long_description=read("README.md"),
    packages = [package],
    package_dir={package:"src"},
    include_package_data=True,
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.6",
    ],
    data_files = [
        ("/etc/bash_completion.d/",["src/daemonctl.complete"]),
    ],
    entry_points = {
        "console_scripts":scripts,
        "daemonctl.modules":daemonctl,
    },
    install_requires=src.dependencies,
)

