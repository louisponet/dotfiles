import logging

from .event import Listener
from .processors import ProcessorProvider


logger = logging.getLogger(__name__)


class Plugin(Listener, ProcessorProvider):
    root_class = None

    def __init__(self, app):
        self.init_listener()
        self.app = app

    def enable_filter(self, filter_name):
        try:
            f = self._filters[filter_name]
            f.active = True
        except KeyError:
            pass

    def disable_filter(self, filter_name):
        try:
            f = self._filters[filter_name]
            f.active = False
        except KeyError:
            pass

    def toggle_filter(self, filter_name):
        try:
            f = self._filters[filter_name]
            f.active = not f.active
        except KeyError:
            pass

    def bindings_for_mode(self, mode, keybindings):
        for name in dir(self):
            if name == "node":
                continue
            meth = getattr(self, name)
            if not getattr(meth, "is_action", False) or meth.mode != mode:
                continue
            for b in meth.default_bindings:
                keybindings.add(*b, **meth.kwargs)(meth)

    def process_node(self, node, reg):
        for p in sorted([p for p in reg.values() if p.active],
                        key=lambda x: x.order):
            p(node)

    def filter(self, node):
        for p in sorted([p for p in self._filters.values() if p.active],
                        key=lambda x: x.order):
            if not p(node):
                return False
        return True

    def adorn(self, node):
        return self.process_node(node, self._adorners)

    def set_root(self, root):
        """Hook called by the app when the root is set/changed.
        Usualy all configuration goes here instead of __init__
        """
        pass

    @property
    def node(self):
        return self.app.node

    def start_watchers(self):
        pass

    def stop_watchers(self):
        pass

    def restart_watchers(self):
        self.stop_watchers()
        self.start_watchers()
