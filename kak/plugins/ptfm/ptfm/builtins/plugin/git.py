from pathlib import Path
import asyncio
from os.path import getmtime, dirname
from subprocess import check_output, CalledProcessError
import logging

from gitignore_parser import parse_gitignore

from ptfm.plugin import Plugin
from ptfm.processors import filter, adorner
from ptfm.command import command, Arg
from ptfm.event import listen


logger = logging.getLogger(__name__)


class Git(Plugin):
    GIT_STATUS_CMD = "git --no-optional-locks status --porcelain".split()
    GIT_TOPLEVEL_CMD = "git rev-parse --show-toplevel".split()

    def __init__(self, *args, **kwargs):
        self.root = None
        self.toplevel = None
        self.repo = None
        self.gitignore_paths = None
        self.status = {}
        super().__init__(*args, **kwargs)
        self.status_task = None

    def start_watchers(self):
        if self.status_task is None:
            self.status_task = asyncio.ensure_future(self._status_watcher())

    def stop_watchers(self):
        if self.status_task is not None:
            self.status_task.cancel()
        self.status_task = None

    @listen("fs_change")
    def on_fs_change(self, node=None):
        logger.debug("got change in %s", node)
        self.restart_watchers()

    async def _status_watcher(self):
        if not (self._adorners["gitstatus"].active or
                self._filters["git_status"].active):
            await asyncio.sleep(2)
            self.status_task = asyncio.ensure_future(self._status_watcher())
            return
        proc = await asyncio.create_subprocess_exec(
                *self.GIT_STATUS_CMD,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()
        logger.debug("got status")
        if proc.returncode == 0:
            logger.debug(stdout.decode())
            status = self._parse_status(stdout.decode("utf-8"))
            if status != self.status:
                self.status = status
                self.app.redraw()
        await asyncio.sleep(30)
        self.status_task = asyncio.ensure_future(self._status_watcher())

    def git_toplevel(self, dir):
        try:
            result = check_output(self.GIT_TOPLEVEL_CMD, cwd=dir)
        except CalledProcessError:
            return None
        return result.strip().decode("utf-8")

    def git_repo(self):
        if self.toplevel is None:
            return None
        repo_path = self.toplevel.joinpath(".git")
        if repo_path.is_dir():
            return repo_path

    def _parse_status(self, output):
        result = {}
        status_map = {
            "M ": "A",
            " M": "M",
            "MM": "AM",
            "R ": "R",
        }
        for line in output.splitlines():
            st = line[:2]
            logger.debug("`%s`", st)
            path = line[2:].strip()
            st = status_map.get(st, st.strip()[0])
            logger.debug(path)
            if st == "R":
                logger.debug("split")
                path = path.split(" -> ")[1]
            logger.debug(path)
            result[Path(path)] = set(list(st))
            path = dirname(path)
            while path:
                result.setdefault(Path(path), set()).update(st)
                path = dirname(path)
        return result

    def _ignore_mtimes(self):
        return tuple([getmtime(p) for p in self.gitignore_paths]) 

    def set_root(self, root):
        logger.debug("Setup git plugin")
        self.root = root
        toplevel = self.git_toplevel(root.path)
        if toplevel is None:
            self.toplevel = None
            self.gitignore_paths = None
            self.status = {}
            return
        self.toplevel = Path(toplevel).absolute()
        logger.debug("toplevel: %s", self.toplevel)
        self.repo = self.git_repo()
        logger.debug("repo: %s", self.repo)
        repo_node = self.app.get_path(str(self.repo))
        repo_node.set_state("fs.watch", True)
        self.gitignore_paths = [
            self.toplevel.joinpath(".gitignore"),
            self.repo.joinpath("info/exclude")]
        logger.debug(self.gitignore_paths)
        self.gitignore_mtimes = self._ignore_mtimes()
        self._gitignore_matchers = []
        for p in self.gitignore_paths:
            try:
                self.gitignore_matchers.append(parse_gitignore(p, root.path))
            except FileNotFoundError:
                logger.exception("gitignore file not found")
        if not self.gitignore_paths:
            self.gitignore_mtimes = (0, 0)
            self.gitignore_paths = None
            self._gitignore_matchers = None

    def _git_diff(self, paths=None, refs=None):
        paths = paths if paths is not None else []
        cmd = ["git", "diff"]
        if refs is not None:
            if len(refs) == 0:
                pass
            elif len(refs) == 1:
                cmd.append(refs[0])
            elif len(refs) == 2:
                cmd.append("..".join(refs))
        cmd.append("--")
        cmd.extend(paths)
        try:
            result = check_output(cmd)
        except CalledProcessError:
            return None
        return result.strip().decode("utf-8")

    def _git_add(self, paths=None):
        paths = paths if paths is not None else []
        cmd = ["git", "add"] + paths
        try:
            result = check_output(cmd)
        except CalledProcessError:
            return None
        return result.strip().decode("utf-8")

    @adorner(True)
    def gitstatus(self, node):
        theme = {
            "M": "#bf616a",
            "A": "#a3be8c",
            "R": "#a3be8c",
            "?": "#bf616a"
        }
        if self.toplevel is None:
            return
        try:
            status_path = node.path.relative_to(self.toplevel)
        except ValueError:
            return
        st = self.status.get(status_path)
        if st is None:
            return
        for status in "MARC?!":
            if status in st:
                node.add_prefix(status, theme.get(status, ""), True)

    @filter(False)
    def git_status(self, node):
        if node.parent is None:
            return True
        status_path = node.path.relative_to(self.toplevel)
        st = self.status.get(status_path)
        if st is None:
            return False
        return True

    @property
    def gitignore_matchers(self):
        if self.gitignore_paths is None:
            return None
        if self._ignore_mtimes() != self.gitignore_mtimes:
            self._gitignore_matchers = [parse_gitignore(p, self.root.path)
                                        for p in self.gitignore_paths]
        return self._gitignore_matchers

    @filter(True)
    def gitignore(self, node):
        logger.debug("#gitignore %s", node)
        if self.gitignore_paths is None:
            logger.debug("no ignore file")
            return True
        result = not any([m(str(node.path)) for m in self.gitignore_matchers])
        logger.debug(result)
        return result

    @Arg("refs", nargs="0..2")
    @command(node_name="node")
    def git_diff(self, refs, node):
        "Show git diff of the current node in a scratch buffer"
        name = "[diff]" + str(node.relative()) + "'"
        name = name.split("'", 1)[0]
        name = f"'{name}'"
        self.app.controler.open_scratch(
            self._git_diff(
                paths=[str(node.path)],
                refs=refs),
            name=name,
            filetype="diff")
        self.app.redraw()

    @command(node_name="node")
    def git_add(self, node):
        "git add selected nodes"
        self._git_add(paths=[node.path])
        self.app.redraw()
