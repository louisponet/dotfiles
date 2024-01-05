from weakref import WeakKeyDictionary
from shutil import rmtree
import os
from pathlib import Path
import asyncio
from asyncio import CancelledError
import logging

import aionotify
from aionotify import Flags


from ptfm.event import listen, emit
from ptfm.node import TempNode, Branch, Leaf, Node, OPEN
from ptfm.plugin import Plugin
from ptfm.processors import filter, adorner, key_binding
from ptfm.builtins.ui.termui.mode import NAV_MODE


logger = logging.getLogger(__name__)


class FSNodeMixin:
    def __init__(self, path, parent=None):
        path = Path(path).absolute()
        self._basename = None
        self._dirname = None
        if self.is_branch:
            Branch.__init__(self, path, parent)
        else:
            Leaf.__init__(self, path, parent)

    @property
    def basename(self):
        if self._basename is None:
            self._basename = os.path.basename(self.path)
        return self._basename

    @basename.setter
    def basename(self, _):
        self._basename = None

    @property
    def dirname(self):
        if self._dirname is None:
            self._dirname = os.path.dirname(self.path)
        return self._dirname

    @dirname.setter
    def dirname(self, _):
        self._dirname = None

    def relative(self):
        return self.path.relative_to(self.root.path)


class Dir(FSNodeMixin, Branch):
    def __iter__(self):
        for c in self.children:
            if c.is_branch:
                yield c
        for c in self.children:
            if not c.is_branch:
                yield c

    @classmethod
    def add_node(cls, parent, after=None):
        new = NewFile(parent.path, parent)
        parent.insert_after(after, new)
        return new

    @classmethod
    def rm_node(cls, node):
        try:
            if node.is_branch:
                rmtree(str(node.path))
            else:
                node.path.unlink()
            return True
        except Exception:
            return False

    def load(self):
        self.children = []
        for n in self.iterdir():
            self.children.append(n)
        self.updated()

    def iterdir(self):
        for d in self.path.iterdir():
            if d.is_dir():
                yield Dir(d.absolute(), self)
            else:
                yield File(d.absolute(), self)

    def refresh(self) -> bool:
        paths = [p.absolute() for p in self.path.iterdir()]
        changes = False
        children = [c for c in self]
        for child in children:
            if child.path not in paths:
                self.remove(child)
                child.set_state("forget", True)
                changes = True
            else:
                paths.remove(child.path)
        for p in paths:
            changes = True
            if p.is_dir():
                self.append(Dir(p, self))
            else:
                self.append(File(p, self))
        if changes:
            self.updated()
        return changes

    def get_child(self, name):
        if not self.loaded:
            self.load()
        for c in self:
            if c.basename == name:
                return c
        return None

    def get_path(self, path):
        dir = self
        path = Path(path).absolute()
        rel = path.relative_to(self.path)
        for part in str(rel).split(os.sep):
            if not part:
                continue
            dir = dir.get_child(part)
            if dir is None:
                raise FileNotFoundError(part)
        return dir


class NewFile(TempNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_name = ""

    def commit(self, name):
        new = self.parent.path.joinpath(Path(name))
        if name.endswith("/"):
            new.mkdir(parents=True)
            new = Dir(new, self.parent)
        else:
            new.touch()
            new = File(new, self.parent)
        return new


class File(FSNodeMixin, Leaf):
    pass


class FS(Plugin):
    root_class = Dir

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ls_watchers_results = WeakKeyDictionary()
        self.watcher_task = None
        self.watcher_func = self._inotify_watcher
        self.buffers_task = None
        self._open_buffers = None

    @key_binding(NAV_MODE, "I")
    def toggle_hidden(self, event):
        self.toggle_filter("hidden_files")

    @filter(True)
    def hidden_files(self, node):
        if node.basename.startswith("."):
            return False
        return True

    @filter(False)
    def open_buffers(self, node):
        path = str(node.relative())
        if self._open_buffers is None:
            self._open_buffers = set(self.app.controler.open_buffers())
        if node.is_branch:
            for p in self._open_buffers:
                if p.startswith(path+"/"):
                    return True
        else:
            return path in self._open_buffers

    @adorner(True)
    def adorn_dir(self, node):
        if isinstance(node, Dir):
            node.style = "dirname"
            if node.parent is None:
                node.display_name = str(node.path.absolute())
            if node.display_name[-1] != "/":
                node.display_name += "/"

    @adorner(True)
    def adorn_tempnode(self, node):
        if isinstance(node, TempNode):
            node.style = "struct"

    @adorner(True)
    def adorn_deleted(self, node):
        if node.state["deleted"]:
            node.style = "struct"

    @listen("branch_closed")
    def branch_closed(self, node, **kwargs):
        # del self.watched_dirs[node]
        self.restart_watchers()

    @listen("branch_open")
    def branch_open(self, node, **kwargs):
        # self.watched_dirs[node] = 0
        self.restart_watchers()

    def get_watched_dirs(self):
        logger.debug("** get **")
        watched = Node.index.filter("status", OPEN).filter("displayed", True)
        try:
            watched = watched.union(Node.index.filter("fs.watch", True))
            for d in watched:
                logger.debug(d)
            logger.debug("** odne **")
            return watched
        except Exception:
            import traceback
            logger.debug(traceback.format_exc())

    def start_watchers(self):
        if self.watcher_task is None:
            self.watcher_task = asyncio.ensure_future(self.watcher_func())
            self.buffers_task = asyncio.ensure_future(self.watch_buffers())

    def stop_watchers(self):
        if self.watcher_task is not None:
            self.watcher_task.cancel()
        if self.buffers_task is not None:
            self.buffers_task.cancel()
        self.watcher_task = None
        self.buffers_task = None

    async def watch_buffers(self):
        async for ob in self.app.controler.watch_buffers():
            ob = set(ob)
            if ob != self._open_buffers:
                self._open_buffers = ob
                if self._filters["open_buffers"].active:
                    self.app.redraw()

    def change_detected(self, dir):
        self.app.redraw()
        emit("fs_change", node=dir)

    async def _watch_dir(self, dir):
        command = ["ls", "-a", str(dir.path)]
        proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            h = hash(stdout)
            if self.ls_watchers_results.setdefault(dir, 0) != h:
                self.ls_watchers_results[dir] = h
                dir.refresh()
                self.change_detected(dir)
                return True
        return False

    async def _dirs_watcher(self):
        await asyncio.gather(
            *[self._watch_dir(dir) for dir in self.get_watched_dirs()],
            return_exceptions=True)
        await asyncio.sleep(1)
        self.watcher_task = asyncio.ensure_future(self._dirs_watcher())

    async def _inotify_watch_dir(self, dir):
        path = str(dir.path)
        watcher = aionotify.Watcher()
        watcher.watch(path=path, flags=Flags.MODIFY |
                      Flags.CREATE |
                      Flags.DELETE |
                      Flags.ATTRIB |
                      Flags.MOVED_FROM |
                      Flags.MOVED_TO |
                      Flags.DELETE_SELF |
                      Flags.MOVE_SELF)
        try:
            await watcher.setup(asyncio.get_running_loop())
            while True:
                event = await watcher.get_event()
                if dir.loaded:
                    dir.refresh()
                self.change_detected(dir)
                if event.flags & (Flags.DELETE_SELF | Flags.MOVE_SELF):
                    return
        except CancelledError:
            watcher.close()
        except Exception:
            logger.exception("error in notifying")

    async def _inotify_watcher(self):
        await asyncio.gather(
            *[self._inotify_watch_dir(dir) for dir in self.get_watched_dirs()],
            return_exceptions=True)
