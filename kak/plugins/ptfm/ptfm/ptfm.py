#! python

import weakref
import asyncio
from shutil import copy2 as copy, copytree
from traceback import format_exc
import logging
import logging.config

from .command import command
from .node import Node
from .help import build_help
from .node import OPEN, CLOSED, TempNode
from .controler import DumyClientControler

logger = logging.getLogger(__name__)


class Tree:
    def __init__(self, root_def, plugins, ui, controler=None,
                 logging_config=None):
        self.ui = None
        self.curline = 0
        self.plugins = [p(self) for p in plugins]
        for p in self.plugins:
            if p.root_class is not None:
                self.root_class = p.root_class
                break
            else:
                raise ValueError("No plugin defines a root_class. "
                                 "Can't instanciate root")
        self._root = None
        self.root = self.root_class(root_def)
        self.last_state = self.state
        self.root.open()
        self.nodes = []
        self.update(False)
        self.ui = ui(self)
        self.commands = self.load_commands()
        self.controler = controler if controler else DumyClientControler()
        self.auto_goto = weakref.WeakKeyDictionary()

        # run.
        # self.ui.redraw()
        self.update_task = None
        self._root.update_consumers.append(self.schedule_update)
        Node.index.update_consumers.append(self.schedule_update)
        self.schedule_update()
        self.start_watchers()

    def run(self):
        self.ui.run()

    @property
    def state(self):
        return (self._root._version, Node.index.version)

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, new):
        if self.root is new:
            return
        self._root = new
        new.updated()
        for p in self.plugins:
            p.set_root(new)
        self.redraw()

    def schedule_update(self, redraw=True):
        if self.update_task is None:
            self.update_task = asyncio.ensure_future(self._update(redraw))

    async def _update(self, redraw):
        await asyncio.sleep(0.05)
        self.update(redraw=redraw)
        self.update_task = None

    def update(self, redraw=True):
        # logger.debug("***** update *****")
        try:
            Node.index.batch_toggle('displayed', True)
            # logger.debug(len(Node.index.filter("visible", True).filter("displayed", True)))
            # num = 0
            query = Node.index.filter('visible', True).filter("displayed", True)
            query = query.exclude("forget", True).sort(self.root.sort_key)
            for node in query.dynamic_iter():
                # num += 1
                if isinstance(node, TempNode) or node.parent is None:
                    continue
                node.displayed = self.filter(node)
        except Exception:
            logger.debug(format_exc())
        self.nodes = list(query)
        self.nodes.sort()
        # logger.debug(self.nodes)
        for node in self.nodes:
            node.tokens = []
            node.prefixes = set()
            node.sufixes = []
            node.style = ""
            self.adorn(node)
        if redraw:
            self.ui.redraw()
        return True
        # logger.debug(len(Node.index.filter("visible", True).filter("displayed", True)))
        # logger.debug("passes: ", num)

    def add_node(self, parent, after=None):
        new = self.root_class.add_node(parent, after)
        self.update()
        return new

    def adorn(self, node):
        if isinstance(node, TempNode):
            return
        for p in self.plugins:
            p.adorn(node)

    def load_commands(self):
        commands = {}
        command.gather(self, commands)
        command.gather(self.ui, commands)
        for p in self.plugins:
            command.gather(p, commands)
        return commands

    def help(self):
        self.controler.open_scratch(build_help(self),
                                    "PTFM Help",
                                    filetype="restructuredtext",
                                    goto=True
                                    )

    def filter(self, node):
        for p in self.plugins:
            if not p.filter(node):
                return False
        return True

    def start_watchers(self):
        for p in self.plugins:
            p.start_watchers()
        # self.updater_task = asyncio.ensure_future(self.updater())

    def stop_watchers(self):
        for p in self.plugins:
            p.stop_watchers()
        # self.updater_task.cancel()

    def redraw(self):
        if self.ui is None:
            return
        self.update()

    def commit_node(self, node, name):
        new = node.commit(name)
        if new is not node:
            node.parent.append(new)
            self.forget_node(node)
        return new

    def forget_node(self, node):
        changed = False
        try:
            self.nodes.remove(node)
            changed = True
        except ValueError:
            pass
        try:
            node.parent.remove(node)
            changed = True
        except Exception:
            pass
        if changed:
            node.set_state("forget", True)

    def rm_node(self, node):
        if self.root_class.rm_node(node):
            self.forget_node(node)

    def rm_deleted(self):
        to_delete = Node.index.filter("deleted", True)
        for node in to_delete:
            self.rm_node(node)

    def paste(self, dest):
        to_delete = Node.index.filter("deleted", True)
        for node in to_delete:
            if node.is_branch:
                copytree(str(node.path), str(dest.path.joinpath(node.basename)))
            else:
                copy(str(node.path), str(dest.path))
            self.rm_node(node)
        dest.refresh()

    def get_path(self, path):
        return self.root.get_path(path)

    def commit(self):
        self.rm_deleted()

    def quit(self):
        self.stop_watchers()
        self.controler.quit()

    def enable_filter(self, filters):
        for f in filters:
            for p in self.plugins:
                p.enable_filter(f)
        self.redraw()

    def disable_filter(self, filters):
        for f in filters:
            for p in self.plugins:
                p.disable_filter(f)
        self.redraw()

    def toggle_filter(self, filters):
        for f in filters:
            for p in self.plugins:
                p.toggle_filter(f)
        self.redraw()

    def evaluate(self, cmdline, node=None):
        logger.debug("evaluate %s", cmdline)
        cmdline += ' '
        cmd, args = cmdline.split(" ", 1)
        try:
            cmd = self.commands[cmd]
        except KeyError:
            logger.debug("command %s not found", cmd)
        else:
            logger.debug("calling %s on %s", cmd, node)
            try:
                cmd.call_from_string(args, node=node)
            except Exception:
                logger.exception("Error in evaluiate()")

    def close_node(self, node):
        if node.is_branch and node.status == OPEN:
            node.close()
            # try:
            #     del self.auto_goto[node]
            # except KeyError:
            #     pass
            return
        if not node.is_branch or node.status == CLOSED:
            if node.parent is not None:
                self.auto_goto[node.parent] = weakref.ref(node)
                node.parent.close()
                # self.ui.move_to_node(node.parent)
                # self.update()
                # self.ui.redraw()

    def open_node(self, node):
            if node.is_branch:
                if node.status is OPEN:
                    self.ui.move_to_line(self.ui.curline + 1)
                else:
                    # goto = None
                    node.open()
                    # if node in self.auto_goto:
                    #     goto = self.auto_goto[node]()
                    # task = self.ui.redraw()
                    # if goto:
                    #     def cb(_):
                    #         self.ui.move_to_node(goto)
                    #     task.add_done_callback(cb)
            else:
                self.controler.open_file(node)
                self.controler.focus_client()

    def ropen(self, node):
        if not node.is_branch:
            node = node.parent
        node.ropen()
        self.redraw()

    def focus_client(self):
        self.controler.focus_client()

    def get_next_sibling(self, node):
        if node.parent is None:
            return
        found_current = False
        for sibling in node.parent:
            if found_current and sibling.state["displayed"]:
                break
            found_current = sibling is node
        else:
            return
        return sibling

    def get_prev_sibling(self, node):
        if node.parent is None:
            return
        prev_node = None
        for sibling in node.parent:
            if sibling is node:
                break
            if sibling.state["displayed"]:
                prev_node = sibling
        else:
            return
        if prev_node is not None:
            return prev_node

