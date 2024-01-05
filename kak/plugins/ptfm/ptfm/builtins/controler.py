import os
import asyncio
from subprocess import check_output, Popen, TimeoutExpired, PIPE
from tempfile import mktemp
import logging

from ptfm.controler import ClientControler
from ptfm.jsonrpc import JSONRPCUnixServer
from ptfm.utils import Multiplexer


logger = logging.getLogger(__name__)


class XControlerMixin:
    def focus_client(self):
        check_output(["xdotool", "windowactivate", self.client_winid])


class SwayControlerMixin:
    def focus_client(self):
        check_output(["swaymsg", f"[con_id={self.client_winid}] focus"])

    def _place(self):
        check_output("swaymsg move left".split())
        check_output("swaymsg resize set width 200px".split())

    @property
    def win_id(self):
        # TODO: use jsmepath.py rather than relying on jq install
        if not hasattr(self, "_sway_win_id"):
            self._sway_win_id = check_output(
                "swaymsg -t get_tree "
                "| jq '.. "
                "| (.nodes? // empty)[] | "
                "select(.focused==true).id'",
                shell=True).decode('utf-8').strip()
        return self._sway_win_id


class TmuxControlerMixin:
    def focus_client(self):
        check_output(["tmux", "select-pane", "-t", self.client_winid])

    @property
    def win_id(self):
        if not hasattr(self, "_tmux_pane_id"):
            self._tmux_pane_id = os.environ["TMUX_PANE"]
        return self._tmux_pane_id

    def _place(self):
        pass


class BuffersWatcher:
    def __init__(self, server):
        self.server = server
        server.register("buf", self)
        self.next_buffers = asyncio.Future()

    def __aiter__(self):
        return self

    async def __anext__(self):
        result = await self.next_buffers
        self.next_buffers = asyncio.Future()
        return result

    def list_(self, *bufnames):
        self.next_buffers.set_result(bufnames)


class KakouneClientControler(ClientControler):
    def __init__(self, session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.kak_session,
            self.kak_client,
            self.client_winid
        ) = session.split(":")
        self.kak_cmd(f'set-option global ptfm_win_id %{{{self.win_id}}}')
        self.server = None
        self.socket = "/tmp/ptfm/%s" % os.getpid()
        self.start_server()
        self.buf_watcher = None

    def start_server(self):
        try:
            os.mkdir(os.path.dirname(self.socket))
        except FileExistsError:
            pass
        self.server = JSONRPCUnixServer(self.socket)
        asyncio.ensure_future(self.server())

    def kak_cmd(self, command):
        command = f"eval -client {self.kak_client} %{{{command}}}\n".encode()
        proc = Popen(["kak", "-p", self.kak_session], stdin=PIPE, stdout=PIPE,
                     stderr=PIPE)
        try:
            out, err = proc.communicate(command, 1)
        except TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
        return out, err

    def open_file(self, node):
        self.kak_cmd(f"edit {node.path}")

    def open_scratch(self, content, name="scratch", filetype=None, goto=False):
        fifo_path = mktemp(prefix="ptfm")
        try:
            os.mkfifo(fifo_path)
            self.kak_cmd(f"edit -fifo {fifo_path} {name}")
            if filetype is not None:
                self.kak_cmd(f"set buffer filetype {filetype}")
            with open(fifo_path, "w") as f:
                f.write(content)
            if goto:
                self.focus_client()
        finally:
            os.unlink(fifo_path)

    def kak_var(self, name):
        fifo_path = mktemp(prefix="ptfm")
        try:
            os.mkfifo(fifo_path)
            self.kak_cmd(f"nop %sh[echo ${name} > {fifo_path}]")
            with open(fifo_path, "r") as f:
                for line in f:
                    logger.debug(line)
                    break
            return line.split()
        finally:
            os.unlink(fifo_path)

    def kak_val(self, name):
        return self.kak_var(f"kak_{name}")

    def kak_opt(self, name):
        return self.kak_var(f"kak_opt_{name}")

    def open_buffers(self):
        return self.kak_val("buflist")

    def watch_buffers(self):
        if self.buf_watcher is None:
            logger.info("Starting buf watcher")
            try:
                self.buf_watcher = Multiplexer(BuffersWatcher(self.server))
            except Exception:
                logger.exception("")
            logger.info("cmd...")
            self.kak_cmd("rmhooks global ptfm-buffers")
            self.kak_cmd(r'hook -group ptfm-buffers global BufCreate .* '
                         r'%%{ nop %%sh{ jq -n --arg lst "${kak_buflist}" '
                         r'"{ \"jsonrpc\": \"2.0\", \"id\": $(date +%%s%%N), '
                         r'\"method\":\"buf_list_\", params: \$lst '
                         r'| split(\" \") }" '
                         r'| nc -q 0 -U %s } }' % self.socket)
            self.kak_cmd(r'hook -group ptfm-buffers global BufClose .* '
                         r'%%{ nop %%sh{ jq -n --arg lst "${kak_buflist}" '
                         r'"{ \"jsonrpc\": \"2.0\", \"id\": $(date +%%s%%N), '
                         r'\"method\":\"buf_list_\", params: \$lst '
                         r'| split(\" \") }" '
                         r'| nc -q 0 -U %s } }' % self.socket)
        return self.buf_watcher

    def quit(self):
        self.server.close()


class KakouneXClientControler(KakouneClientControler):
    pass


class KakouneTmuxClientControler(TmuxControlerMixin, KakouneClientControler):
    pass


class KakouneSwayClientControler(SwayControlerMixin, KakouneClientControler):
    pass
