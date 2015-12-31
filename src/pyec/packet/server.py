"""
(c) Tuomas Laakkonen 2015

pyec.packet.server
Implements a socketserver based packet server.
"""

from functools import partial
from pyec.packet import Packet
import socketserver

class Event:
	"""A subscribable, triggerable event."""
	def __init__(self):
		self._handlers = []

	def register(self, handler):
		self._handlers.append(handler)

	def trigger(self, *args, **kwargs):
		for handler in self._handlers:
			handler(*args, **kwargs)

class EventHandler:
	"""A mixin handler class for multiple events.
	Supports JavaScript's standard .on syntax, used as either a decorator
	or by passing in a function."""

	def __init__(self, *args, **kwargs):
		self._events = {}
		return super().__init__(*args, **kwargs)

	def add_event(self, name):
		self._events[name] = Event()

	def on(self, name, func=None):
		if func is None:
			def _on(func):
				return self.on(name, func)
			return _on
		else:
			self._events[name].register(func)

	def trigger(self, name, *args, **kwargs):
		self._events[name].trigger(*args, **kwargs)

class PacketRequestHandler(socketserver.BaseRequestHandler):
	def handle(self):
		stream = self.request.makefile()
		stream.client_address = self.client_address
		while True:
			try:
				packet, stream = Packet.deserialize(stream)
			except:
				break
			self.server.trigger('data', packet, stream)

class PacketServer(EventHandler,  socketserver.ThreadingMixIn, socketserver.TCPServer):
	def __init__(self, server_address):
		super().__init__(server_address, PacketRequestHandler)
		self.add_event('connected')
		self.add_event('disconnected')
		self.add_event('data')

	def finish_request(self, *args):
		self.trigger('connected', *args)
		super().finish_request(*args)
		self.trigger('disconnected', *args)

__all__ = ['PacketServer', 'Event', 'EventHandler']
