from pathlib import Path

import pytest

from ptfm.ptfm import Tree
from ptfm.builtins.plugin.fs import FS
from ptfm.help import build_help
from ptfm.ui import DumyUI


@pytest.fixture
def tree():
    root = Path(".").absolute() 
    return Tree(root, [FS], ui=DumyUI)


def test_help(tree):
    build_help(tree)
