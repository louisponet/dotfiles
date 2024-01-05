import asyncio
from io import StringIO
from weakref import ref
import logging
import os

from prompt_toolkit import Application
from prompt_toolkit.key_binding import (
    KeyBindings,
    ConditionalKeyBindings,
    merge_key_bindings,
)
from prompt_toolkit.filters import Condition, has_arg
from prompt_toolkit.layout import NumberedMargin
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.widgets import Label


from ptfm.command import command, Arg, ArgScanner
from ptfm.node import OPEN, CLOSED, TempNode, Leaf
from ptfm.ui import UI


from .mode import NAV_MODE, EDIT_MODE, CMD_MODE


logger = logging.getLogger(__name__)


class Chars:
    closed = "▸"
    open = "▾"
    file = "─"
    open_bar = "├"
    last_open_bar = "└"
    bar = "│"
    struct = "▸▾─├└│ +"


class RendererNode:
    def __init__(self, node, parent):
        self._node = ref(node)
        self.parent = parent
        self.tokens = []
        self.style = node.style
        self.prefixes = node.prefixes
        self.path = node.path
        self.sufixes = node.sufixes
        self.dirname = node.dirname
        self.basename = node.basename
        # self.display_name = node.display_name
        self.is_branch = False
        self.is_temp = False
        self.is_leaf = False
        if node.is_branch:
            self.status = node.status
            self.is_branch = True
        else:
            self.is_branch = False
            if isinstance(node, TempNode):
                self.is_temp = True
            elif isinstance(node, Leaf):
                self.is_leaf = True

    def __eq__(self, other):
        if isinstance(other, RendererNode):
            return (other.path == self.path
                    and self.is_branch == other.is_branch
                    and self.is_leaf == other.is_leaf
                    and self.is_temp == other.is_temp)
        else:
            return self._node() is other

    def __hash__(self):
        return super().__hash__()

    @property
    def display_name(self):
        return self._node().display_name


def render_nodes(nodes):
    parents = {}
    rnodes = []
    for n in nodes:
        if n.parent is None:
            new = RendererNode(n, parent=None)
            parents[n] = new
            rnodes.append(new)
            continue
        new = RendererNode(n, parent=parents[n.parent])
        if n.is_branch:
            parents[n] = new
        rnodes.append(new)
    return rnodes


class Renderer:
    def __init__(self, nodes):
        self.nodes = nodes
        self.output = StringIO()
        self.struct = ""
        self.struct_by_parent = {}
        self.prev_node = None
        self.theme = dict(
            struct="#928374",
            temp="#928374",
            uncommited="#928374",
            arrow="#fe8019",
            branch="#8ec07c",
            info="",
            warning="",
            leaf="",
        )
        self.ptr = 0

    def apply_theme(self, node):
        try:
            return (self.theme[node[0]], node[1])
        except KeyError:
            return node

    def fix_struct_for_last_child(self, node):
        if node.parent is not None:
            text = node.tokens[0][1]
            # text = Chars.last_open_bar.join(text.rsplit(Chars.open_bar))
            text = text.replace(Chars.open_bar, Chars.last_open_bar)
            node.tokens[0] = (node.tokens[0][0], text)

    def add_node(self, node, struct_tail=None):
        tail = struct_tail if struct_tail is not None else []
        if self.struct:
            node.tokens.append(self.apply_theme(("struct", self.struct)))
            node.tokens.extend([self.apply_theme(n) for n in tail])

    def render(self, node):
        if node.prefixes:
            node.tokens.append(("", "["))
            node.tokens.extend(node.prefixes)
            node.tokens.append(("", "] "))
        node.tokens.append((node.style, node.display_name))
        node.tokens.extend(node.sufixes)
        node.tokens = [self.apply_theme(t) for t in node.tokens]
        # logger.debug(node.tokens)
        self.output.write("".join(i[1] for i in node.tokens))
        self.output.write("\n")

    def is_last_child(self, node):
        ptr = self.ptr + 1
        while True:
            if ptr >= len(self.nodes):
                return True
            n = self.nodes[ptr]
            if node.dirname == n.dirname:
                return False
            if not n.dirname.startswith(node.dirname):
                return True
            ptr += 1

    def __call__(self):
        for self.ptr, node in enumerate(self.nodes):
            if node.parent is not None:
                self.struct = self.struct_by_parent[node.parent]
            if node.is_branch:
                node.style = self.theme["branch"]
                if node.parent is None:
                    struct_tail = None
                elif node.status == OPEN:
                    struct_tail = [("arrow", Chars.open + " ")]
                else:
                    struct_tail = [("arrow", Chars.closed + " ")]
                self.add_node(node, struct_tail)

                if node.status == OPEN:
                    if self.is_last_child(node):
                        rev = "".join(reversed(self.struct))
                        rev = rev.replace(Chars.open_bar, " ", 1)
                        self.struct = "".join(reversed(rev))
                    else:
                        self.struct = self.struct.replace(Chars.open_bar, Chars.bar)
                    self.struct = self.struct.replace(Chars.last_open_bar, " ")
                    self.struct = self.struct + 2 * " " + Chars.open_bar
                    self.struct_by_parent[node] = self.struct

            elif node.is_temp:
                node.style = "temp"
                self.add_node(node, [("struct", "+" + " ")])

            elif node.is_leaf:
                self.add_node(node, [("struct", Chars.file + " ")])

            else:
                assert False, "unreachable"

            if self.is_last_child(node):
                self.fix_struct_for_last_child(node)

            self.prev_node = node

        for node in self.nodes:
            self.render(node)
        return self.output.getvalue().strip()


class HighlightProcessor(Processor):
    def __init__(self, app):
        self.app = app

    def apply_transformation(self, ti):
        try:
            node = self.app.nodes[ti.lineno]
        except Exception:
            logger.debug((ti.fragments, ti.lineno))
            raise
        return Transformation(node.tokens)


class TermUI(UI):
    def __init__(self, tree):
        super().__init__()
        self.buffer = None
        self.tree = tree
        self.nodes = render_nodes(self.tree.nodes)
        self.curline = 0

        # plugins setup
        self.bindings = self.load_bindings()

        # UI
        self.buffer = Buffer(
            read_only=Condition(lambda: self.mode != EDIT_MODE),
            on_cursor_position_changed=self.update_pos,
            on_text_insert=self.update_text)
        self.cmdline = Buffer()
        self.tree_win = Window(
            content=BufferControl(
                buffer=self.buffer,
                input_processors=[HighlightProcessor(self)]),
            left_margins=[NumberedMargin()]
        )
        self.cmdline_win = Window(content=BufferControl(buffer=self.cmdline),
                                  height=1)
        self.status_line = Label(text=str(tree.root.path), style='bg:#666666')
        self.split = HSplit([
            self.tree_win,
            self.status_line,
            self.cmdline_win
        ])
        layout = Layout(self.split)
        # import ipdb; ipdb.set_trace()
        use_asyncio_event_loop()
        self.app = Application(
            key_bindings=self.bindings,
            layout=layout,
            # mouse_support=True,
            full_screen=True
        )
        self.app.layout.focus(self.tree_win)

        # misc
        self.mode = NAV_MODE
        self.nav_mode()
        self.show_msg("Type :help for help")

    def update_text(self, event):
        if self.mode != EDIT_MODE:
            return
        name = self.doc.current_line.strip(Chars.struct + " +")
        logger.debug("Update text: %s", name)
        self.node.display_name = name
        self.refresh()
        return True

    @property
    def async_redraw_on(self):
        return self.mode == NAV_MODE

    @property
    def node(self):
        return self.node_at_lineno(self.curline)

    def node_at_lineno(self, lineno):
        return self.nodes[lineno]._node()

    def load_bindings(self):
        nb = self.nav_bindings()
        for p in self.tree.plugins:
            p.add_bindings_for_mode(NAV_MODE, nb)
        nb = ConditionalKeyBindings(
            nb,
            filter=Condition(lambda: self.mode == NAV_MODE)
        )
        nb.ptfm_mode = NAV_MODE
        eb = self.edit_bindings()
        eb.ptfm_mode = EDIT_MODE
        for p in self.tree.plugins:
            p.bindings_for_mode(EDIT_MODE, eb)
        cb = self.cmdline_bindings()
        cb.ptfm_mode = CMD_MODE
        for p in self.tree.plugins:
            p.bindings_for_mode(CMD_MODE, cb)
        return merge_key_bindings([nb, eb, cb])

    @property
    def doc(self):
        return self.buffer.document

    @property
    def cmdline_doc(self):
        return self.cmdline.document

    def update_pos(self, event):
        if self.mode == EDIT_MODE:
            return
        linenr = self.buffer.document.cursor_position_row
        if linenr != self.curline:
            self.curline = linenr
            self.move_to_filename_start()
            if isinstance(self.node, TempNode):
                self.set_status(os.sep.join([self.node.dirname, self.node.display_name]))
            else:
                self.set_status(str(self.node.relative()))

    def move_to_filename_start(self):
        line = self.doc.current_line
        idx = 0
        for idx, char in enumerate(line):
            if char == "[":
                idx = line.find("]", idx) + 2
                break
            if char not in Chars.struct:
                break
        else:
            idx += 1
        new = Document(
            text=self.doc.text,
            cursor_position=(self.doc.cursor_position -
                             self.doc.cursor_position_col +
                             idx))
        self.buffer.set_document(new, bypass_readonly=True)

    def edit_mode(self):
        logger.debug("Enter edit mode")
        self.mode = EDIT_MODE

    def cmd_mode(self, prompt=":"):
        logger.debug("Enter command mode")
        self.mode = CMD_MODE
        new = Document(text=prompt, cursor_position=1)
        self.cmdline.set_document(new)
        self.app.layout.focus(self.cmdline_win)

    def nav_mode(self):
        if self.mode == NAV_MODE:
            return
        logger.debug("Enter nav mode")
        self.mode = NAV_MODE
        self.app.layout.focus(self.tree_win)
        self.refresh()

    # UI interface

    def show_msg(self, text):
        new = Document(text=text, cursor_position=len(text))
        self.cmdline.set_document(new)

    def set_status(self, text):
        self.status_line.text = text

    def refresh(self):
        logger.debug("Start refresh")

        try:
            if self.buffer is None:
                return
            if self.async_redraw_on:
                self.nodes = render_nodes(self.tree.nodes)
            else:
                for node in self.nodes:
                    node.tokens = []
            try:
                text = Renderer(self.nodes)()
            except Exception:
                logger.exception("Error while rendering")
            old = self.buffer.document
            pos = min(old.cursor_position, len(text))
            # logger.debug(text)
            # logger.debug([n.tokens for n in self.nodes])
            new = Document(text=text, cursor_position=pos)
            self.buffer.set_document(new, bypass_readonly=True)
            if self.mode != EDIT_MODE:
                self.move_to_filename_start()
        except Exception:
            logger.exception("Error in refresh")
        logger.debug("Refresh Done")

    def move_to_line(self, lineno):
        index = self.lineno_to_index(lineno+1)
        new = Document(text=self.doc.text, cursor_position=index)
        self.buffer.set_document(new, bypass_readonly=True)

    def lineno_to_index(self, lineno):
        index = 0
        for i in range(lineno):
            result = self.doc.text.find("\n", index+1)
            if result == -1:
                return index + 1
            index = result
        return index

    def get_node_line(self, node):
        return self.nodes.index(node)

    def move_to_node(self, node):
        try:
            lineno = self.get_node_line(node)
        except ValueError:
            return
        self.move_to_line(lineno)

    def move_to_parent(self):
        if self.node.parent is not None:
            self.move_to_node(self.node.parent)

    def run(self):
        with patch_stdout():
            asyncio.get_event_loop().run_until_complete(
                self.app.run_async().to_asyncio_future())

    @command()
    def help(self):
        self.tree.help()

    @Arg("text", nargs="1..")
    @command()
    def echo(self, text):
        text = " ".join(text)
        self.show_msg(text)

    @command("w")
    def write(self):
        self.tree.commit()

    @command("q")
    def quit(self):
        self.tree.quit()
        self.app.exit()

    @Arg("filters", nargs="1..")
    @command()
    def enable_filter(self, filters):
        self.tree.enable_filter(filters)

    @Arg("filters", nargs="1..")
    @command()
    def disable_filter(self, filters):
        self.tree.disable_filter(filters)

    @Arg("filters", nargs="1..")
    @command()
    def toggle_filter(self, filters):
        self.tree.toggle_filter(filters)

    @Arg("command", nargs="2..")
    @command()
    def bind(self, command):
        self.echo(str(command))

    def nav_bindings(self):
        kb = KeyBindings()

        @kb.add('g', filter=has_arg)
        def move_to_line(event):
            """
            Move to :range: line
            """
            self.move_to_line(event.arg - 1)

        for n in '123456789':
            @kb.add(n)
            def _(event):
                """
                Always handle numberics in navigation mode as arg.
                """
                event.append_to_arg_count(event.data)

        @kb.add('q')
        def exit_(event):
            "Quit PTFM"
            self.quit()

        @kb.add("down")
        @kb.add('j')
        def move_down(event):
            "Move the cursor downwards"
            self.buffer.cursor_down()

        @kb.add("up")
        @kb.add('k')
        def move_up(event):
            "Move the cursor upwards"
            self.buffer.cursor_up()

        @kb.add("left")
        @kb.add('h')
        def close(event):
            """
            On a branch: close the current branch
            On a leaf: move to parent branch"""
            if not self.node.is_branch or self.node.status == CLOSED:
                self.add_redraw_cb(self.move_to_node, self.node.parent)
            self.tree.close_node(self.node)

        @kb.add("enter")
        @kb.add("right")
        @kb.add('l')
        def open(event):
            """
            On a closed branch: open the branch.
            On an open branch: move to first child
            On a leaf: open the leaf
            """
            self.tree.open_node(self.node)

        @kb.add("escape", "l")
        def ropen(event):
            "Open branches recursively"
            self.tree.ropen(self.node)

        @kb.add("escape", "h")
        def move_to_parent(event):
            "Move to the parent branch"
            self.move_to_parent()

        @kb.add("escape", "j")
        def move_to_next_sibling(event):
            self.move_to_node(self.tree.get_next_sibling(self.node))

        @kb.add("escape", "k")
        def move_to_prev_sibling(event):
            self.move_to_node(self.tree.get_prev_sibling(self.node))

        @kb.add('f1')
        def client_focus(event):
            "Go to the client window"
            self.tree.focus_client()

        @kb.add(':')
        @kb.add('#')
        def entercmdline(event):
            """
            Enter in command line mode.
            ``:`` accepts commands
            ``#`` is a shortcut for ``:toggle_filter``
            """
            prompt = event.key_sequence[0].data
            self.cmd_mode(prompt)

        @kb.add("o")
        def add_node(event):
            """
            Create a new node. Enters EDIT mode
            Enters EDIT mode. If the last character is a '/', a dir is created
            """
            node = self.node
            if node.is_branch:
                node.open()
                new = self.tree.add_node(node)
            else:
                new = self.tree.add_node(node.parent, node)
            self.add_redraw_cb(self.move_to_node, new)
            self.add_redraw_cb(self.edit_mode)
            logger.debug("Node added: %s", repr(new))

        @kb.add('O')
        def add_node_in_parent(event):
            """
            Create an new node in parent.
            Enters EDIT mode. If the last character is a '/', a dir is created
            """
            if self.node.is_branch:
                new = self.tree.add_node(self.node.parent)
            else:
                new = self.tree.add_node(self.node.parent, self.node)
            self.add_redraw_cb(self.move_to_node, new)
            self.add_redraw_cb(self.edit_mode)
            logger.debug("Node added: %s", repr(new))

        @kb.add("d", "d")
        @kb.add("x", "d")
        def rm_node(event):
            """
            Toggle deleted mark.
            Note that it's just a mark. Nothing happens before you save
            your work with ``:write``.
            """
            self.node.toggle_state("deleted")
            self.add_redraw_cb(self.buffer.cursor_down)

        @kb.add("p")
        def paste(event):
            "Paste all deleted nodes in the current node"
            if self.node.is_branch:
                self.node.open()
                self.tree.paste(self.node)
            else:
                self.tree.paste(self.node.parent)

        @kb.add('R')
        def redraw(event):
            "Redraw the tree"
            self.tree.redraw()

        @kb.add('r')
        def refresh(event):
            "Refresh the current dir only (deprecated: useless)"
            if self.node.is_branch:
                changes = self.node.refresh()
            else:
                changes = self.node.parent.refresh()
            if changes and (not self.node.is_branch or self.node.status == OPEN):
                self.redraw()

        @kb.add('escape', 'r')
        def refresh_all(event):
            "Reload the whole tree"
            self.tree.redraw()

        return kb

    def edit_bindings(self):
        kb = KeyBindings()

        @kb.add("escape")
        def quit_mode(event):
            """Quit the edit mode. Nothing is changed"""
            self.tree.forget_node(self.node)
            self.nav_mode()

        @kb.add("enter")
        def commit(event):
            """Commit the edition (create the node)"""
            name = self.doc.current_line.strip(Chars.struct + " ")
            new_node = self.tree.commit_node(self.node, name)
            self.add_redraw_cb(self.move_to_node, new_node)
            self.nav_mode()

        return ConditionalKeyBindings(
            kb,
            filter=Condition(lambda: self.mode == EDIT_MODE)
        )

    def cmdline_bindings(self):
        kb = KeyBindings()

        @kb.add("escape")
        def quit_cmdline(event):
            new = Document(text="")
            self.cmdline.set_document(new)
            self.nav_mode()
            self.redraw()

        @kb.add("enter")
        def accept(event):
            prefix = self.cmdline_doc.current_line[0]
            cmdline = self.cmdline_doc.current_line[1:]
            self.nav_mode()
            if prefix == ":":
                logger.debug(self.node)
                self.tree.evaluate(cmdline, self.node)
            elif prefix == "#":
                self.toggle_filter(filters=[str(t) for t in ArgScanner.tokenize(cmdline)])
            return

        return ConditionalKeyBindings(
            kb,
            filter=Condition(lambda: self.mode == CMD_MODE)
        )
