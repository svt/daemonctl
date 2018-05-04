#!/usr/bin/python

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

if __name__ == "__main__":
	c = Config("/usr/local/etc/bandmigrering.conf")
	print(c.apa.mandel.get("1").grejs)
	print(c.get("programname"))
	print(c["programname"])
	print(c.apa.mandel["1"].grejs)
	print(c.list("ingest"))

