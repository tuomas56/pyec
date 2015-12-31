"""
(c) Tuomas Laakkonen 2015

pyec.packet.packet
A packet class with serialization.
Uses metaclasses to provide an easy way to construct packet classes.
"""
from inspect import Parameter, Signature
from collections import OrderedDict
from pyec.packet.varint import pack, unpack_stream
from functools import partial
import struct

class Descriptor:
	"""Implements the descriptor protocol, does nothing,
	used only as base class."""
	def __init__(self, name=None):
		self.name = name

	def __get__(self, instance, cls):
		return instance.__dict__[self.name]

	def __set__(self, instance, value):
		instance.__dict__[self.name] = value

class Field:
	"""Abstract class. Fields can be serialized from an instance and
	deserialized from a stream."""
	def _serialize(self, inst):
		raise NotImplementedError()

	def _deserialize(self, stream):
		raise NotImplementedError()

class TypedField(Descriptor, Field):
	"""Check for correct type in __set__ (this doesn't matter in __get__)"""
	_type = object
	def __set__(self, instance, value):
		if not isinstance(value, self._type):
			raise TypeError("Expected type %s, got type %s" % (self._type.__name__, type(value).__name__))
		super().__set__(instance, value)

class Int(TypedField):
	_type = int

	def _serialize(self, inst):
		return pack(inst)

	def _deserialize(self, stream):
		return unpack_stream(stream)

class Float(TypedField):
	_type = float

	def _serialize(self, inst):
		return struct.pack('!d', inst)

	def _deserialize(self, stream):
		return struct.unpack_from('!d', stream), stream

class LDField(TypedField):
	"""A field that is encoded in the format length + data."""
	def _serialize(self, inst):
		data = self._ld_serialize(inst)
		return pack(len(data)) + data

	def _deserialize(self, stream):
		length, stream = unpack_stream(stream)
		data = stream.read(length)
		return self._ld_deserialize(data), stream


class String(LDField):
	_type = str

	def _ld_serialize(self, inst):
		return inst.encode()

	def _ld_deserialize(self, data):
		return data.decode()

class Bytes(LDField):
	_type = bytes

	def _ld_serialize(self, inst):
		return inst

	def _ld_deserialize(self, data):
		return data

class Registry:
	def __init__(self):
		self._normal = {}
		self._reverse = {}

	def register(self, obj):
		self._normal[obj.__name__] = obj
		self._reverse[obj] = obj.__name__

	def get_obj(self, id):
		return self._normal[id]

	def get_id(self, obj):
		return self._reverse[obj]

def make_signature(names):
	"""Make a namedtuple-like signature from a list of field names."""
	return Signature(Parameter(name, Parameter.POSITIONAL_OR_KEYWORD)
					 for name in names)

class PacketMeta(type):
	REGISTRY = Registry()

	@classmethod
	def __prepare__(cls, name, bases):
		return OrderedDict()
		#so that the fields are kept ordered

	def __new__(cls, name, bases, clsdict):
		fields = [key for key, val in clsdict.items() if isinstance(val, Descriptor)]
		#these are ordered because of __prepare__.
		for field in fields:
			clsdict[field].name = field
			#change the names from default
		clsobj = super().__new__(cls, name, bases, dict(clsdict))
		#no need for the additional overhead of OrderedDict, so just change it back
		#to a plain dict.
		sig = make_signature(fields)
		setattr(clsobj, '__signature__', sig)
		#__signature__ is used instead of _signature because several methods
		#like functools.wraps and inspect.* check for this.
		setattr(clsobj, '_fields', fields)
		PacketMeta.REGISTRY.register(clsobj)
		return clsobj

class Packet(metaclass=PacketMeta):
	"""A serializeable, arbitrary data container, that consists of fields."""
	def __init__(self, *args, **kwargs):
		bound = self.__signature__.bind(*args, **kwargs)
		#have inspect do all the nasty arg checking for us.
		for name, val in bound.arguments.items():
			setattr(self, name, val)

	def __repr__(self):
		values = zip(self._fields, map(str, map(partial(getattr, self), self._fields)))
		values = ', '.join(map('='.join, values))
		return '%s(%s)' % (type(self).__name__, values)

	def __eq__(self, other):
		return all(getattr(self, field) == getattr(other, field) for field in self._fields)

	def serialize(self):
		"""Packets serialize to the format:
			pid + data
		Where pid is the ld-varint-encoded packet id.
		The data is composed of fields."""
		pid = PacketMeta.REGISTRY.get_id(self.__class__)
		data = []
		for field in self._fields:
			f = self.__class__.__dict__[field]
			val = getattr(self, field)
			data.append(f._serialize(val))
		data = b''.join(data)
		return pack(len(pid)) + pid.encode() + data

	@staticmethod
	def deserialize(stream):
		pid_len, stream = unpack_stream(stream)
		pid = stream.read(pid_len).decode()
		pcls = PacketMeta.REGISTRY.get_obj(pid)
		fields = []
		for field in pcls._fields:
			f, stream = pcls.__dict__[field]._deserialize(stream)
			fields.append(f)
		return pcls(*fields)

__all__ = ['TypedField', 'Int', 'String', 'Float', 'Bytes', 'LDField', 'Packet']
