#!/usr/bin/python

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

import os

class ConfigFileError(Exception): pass


class Config:
	def __init__(self, filename=None, defaults={}, forceDefaults=False, autotypes=False):
		self._filename = filename
		self._config = defaults.copy()
		self._force = forceDefaults
		self._autotypes = autotypes
		# Compat
		self.config = self._config
		self.load = self._load
		self.reload = self._load
		# Load config
		self._load()

	def keys(self):
		return self.list()
	def __iter__(self):
		for key in self._config:
			print(repr(key))
			yield key
	def _load(self, filename=None):
		if not filename:
			filename = self._filename
		if not filename:
			if self._config:
				return
			else:
				raise RuntimeError("No filename specified")
		#print "Loading config: %r"%(filename,)
		inobj = []
		for line in open(filename,"rb").readlines():
			line = line.decode("utf8")
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			#line = line.split("#")[0].strip()
			#if line.strip().startswith("#"): continue
			if len(line.split()) == 2 and line.split()[1] == "{":
				inobj.append(line.split()[0])
				continue
			if line == "}" and inobj:
				inobj.pop()
				continue
			if not "=" in line:
				raise ConfigFileError("No equalsign (=) on line: %r"%line)
			key, value = line.split("=",1)
			key = ".".join(inobj+[key])
			if self._force:
				if not key.strip() in self._config:
					raise ConfigFileError("Key %r not in defaults and force is True"%key)
			value = value.strip()
			if self._autotypes is True:
				value = self._getTyped(value)
			self._config[key.strip()] = value

	def _getTyped(self, value):
		if "," in value:
			tmp = []
			for val in value.split(","):
				obj = self._getTyped(val.strip())
				if obj != "":
					tmp.append(obj)
			value = tmp
		else:
			try:
				tmp = int(value)
				return tmp
			except Exception as e:
				pass
			try:
				tmp = float(value)
				return tmp
			except Exception as e:
				pass
		return value
	def __nonzero__(self):
		return bool(self._config)
	def __eq__(self, other):
		if isinstance(other, Config):
			return self._config == other._config
		else:
			return False
	def __contains__(self, key):
		keys = [x.split(".")[0] for x in self._config]
		return key in self._config or key in keys

	def __getitem__(self, key):
		keys = [x for x in self._config if x.startswith(key+".")]
		if keys:
			d = dict([(x.split(".",1)[-1],y) for x,y in self._config.items() if x in keys])
			return Config(defaults = d)
		return self._config[key]

	def __getattr__(self, key):
		return self[key]
	def __str__(self):
		return self.__repr__()
	def __repr__(self):
		return str(self._config)

	def get(self, key, default=None):
		keys = [x for x in self._config if x.startswith(key+".")]
		if keys:
			d = dict([(x.split(".",1)[-1],y) for x,y in self._config.items() if x in keys])
			return Config(defaults = d)
		return self._config.get(key,default)
	
	def setdefault(self, key, default):
		return self._config.setdefault(key, default)
	def list(self, filter=None):
		keys = set([x.split(".")[0] for x in self._config])
		if filter:
			return sorted([x for x in keys if x.startswith(filter)])
		return sorted(keys)
	def items(self):
		return self._config.items()

class EnvironConfig(Config):
	def _load(self):
		found = False
		for key, value in os.environ.items():
			if key.lower().startswith("cfg_"):
				key = key[4:].replace("_",".")
				self._config[key] = value
				found = True
		if found is False:
			raise ValueError("No config found in Environment")

if __name__ == "__main__":
	c = Config("daemonctl.test.conf")
	#print(c.apa.mandel.get("1").grejs)
	#print(c.get("programname"))
	#print(c["programname"])
	#print(c.apa.mandel["1"].grejs)
	#print(c.list("modules"))
	#print(c.logpath)
	d = dict(hej=1)
	d.update(c)
	print(d)
