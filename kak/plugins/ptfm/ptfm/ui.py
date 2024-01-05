import asyncio
from asyncio import CancelledError
import logging


logger = logging.getLogger(__name__)


class UI:
    def __init__(self, app=None):
        self.redraw_task = None
        self.redraw_cb = []

    def add_redraw_cb(self, fn, *args, **kwargs):
        self.redraw_cb.append((fn, args, kwargs))

    def run_redraw_cb(self):
        logger.debug("Run redraw callbacks")
        try:
            for fn, args, kwargs in self.redraw_cb:
                fn(*args, **kwargs)
        except Exception:
            logger.exception("Error in callback")
        finally:
            self.redraw_cb = []

    async def _async_redraw(self):
        try:
            await asyncio.sleep(0.05)
        except CancelledError:
            self.refresh()
        else:
            self.refresh()
        self.run_redraw_cb()
        self.redraw_task = None

    def redraw(self):

        if self.async_redraw_on:
            logger.debug("Redraw postponned")
            if self.redraw_task is None:
                self.redraw_task = asyncio.ensure_future(self._async_redraw())
        else:
            logger.debug("Immediate redraw")
            if self.redraw_task is not None:
                self.redraw_task.cancel()
                self.redraw_task = None
            self.refresh()
            self.run_redraw_cb()

    def quit(self):
        raise NotImplementedError()

    def show_msg(self, text):
        raise NotImplementedError()

    def set_status(self, text):
        raise NotImplementedError()

    def node_added(self, node):
        raise NotImplementedError()

    def refresh(self):
        raise NotImplementedError()

    def move_to_line(self, lineno):
        raise NotImplementedError()

    def lineno_to_index(self, lineno):
        raise NotImplementedError()

    def move_to_node(self, node):
        raise NotImplementedError()

    def move_to_parent(self):
        raise NotImplementedError()

    def reload(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()


class DummyBinding:
    def __init__(self):
        self.registries = []


class DumyUI():
    def __init__(self, app):
        self.app = app
        self.bindings = DummyBinding() 

    def quit(self):
        pass

    def show_msg(self, text):
        pass

    def set_status(self, text):
        pass

    def node_added(self, node):
        pass

    def redraw(self):
        pass

    def move_to_line(self, lineno):
        pass

    def lineno_to_index(self, lineno):
        pass

    def move_to_node(self, node):
        pass

    def move_to_parent(self):
        pass

    def reload(self):
        pass

    def run(self):
        pass
