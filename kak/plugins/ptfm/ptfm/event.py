from weakref import WeakSet
from types import FunctionType


class listen:
    def __init__(self, event):
        self.event = event

    def __call__(self, fn):
        fn.event = self.event
        return fn


class Listener:
    def init_listener(self):
        self._event_listeners = {}
        for name in dir(self.__class__):
            attr = getattr(self.__class__, name)
            if isinstance(attr, FunctionType):
                if hasattr(attr, "event"):
                    self._event_listeners.setdefault(attr.event, []).append(attr)
                    Manager.subscribe(attr.event, self)

    def receive_event(self, event, **data):
        for listener in self._event_listeners[event]:
            listener(self, **data)


class Manager:
    subsciptions = {}

    @classmethod
    def subscribe(cls, event, listener):
        cls.subsciptions.setdefault(event, WeakSet()).add(listener)

    @classmethod
    def emit(cls, event, **data):
        for listener in cls.subsciptions.get(event, []):
            listener.receive_event(event, **data)


emit = Manager.emit
