#!/usr/bin/env python2
# vim: ts=4 sw=4 et
# From user4815162342 on stackoverflow
# https://stackoverflow.com/questions/13210436/get-full-traceback

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



import sys

class FauxTb(object):
    def __init__(self, tb_frame, tb_lineno, tb_next):
        self.tb_frame = tb_frame
        self.tb_lineno = tb_lineno
        self.tb_next = tb_next

def current_stack(skip=0):
    try: 1/0
    except ZeroDivisionError:
        f = sys.exc_info()[2].tb_frame
    for i in xrange(skip + 2):
        f = f.f_back
    lst = []
    while f is not None:
        lst.append((f, f.f_lineno))
        f = f.f_back
    return lst

def extend_traceback(tb, stack):
    """Extend traceback with stack info."""
    head = tb
    for tb_frame, tb_lineno in stack:
        head = FauxTb(tb_frame, tb_lineno, head)
    return head

def full_exc_info(skip=0):
    """Like sys.exc_info, but includes the full traceback."""
    t, v, tb = sys.exc_info()
    full_tb = extend_traceback(tb, current_stack(skip+1))
    return t, v, full_tb

