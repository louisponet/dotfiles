# -*- coding: utf-8 -*-

"""Console script for ptfm."""
import sys
import os
from pathlib import Path
from importlib import import_module

import click

import logging

from .ptfm import Tree
from .utils import rsplit

from ptfm.builtins.controler import (
    KakouneSwayClientControler,
    KakouneXClientControler,
    KakouneTmuxClientControler
)
import ptfm.builtins.ui as builtin_ui
import ptfm.builtins.plugin as builtin_plugins


def load_plugins(plugins_def):
    plugins = []
    for pdef in plugins_def.split(","):
        if "." not in pdef:
            plugins.append(getattr(builtin_plugins, pdef))
        else:
            mod_name, cls_name = rsplit(pdef, ".", 1)
            mod = import_module(mod_name)
            plugins.append(getattr(mod, mod_name))
    return plugins


def load_ui(ui_def):
    if ui_def == "none":
        from .ui import DumyUI
        return DumyUI
    if "." not in ui_def:
        return getattr(builtin_ui, ui_def)
    else:
        mod_name, cls_name = rsplit(ui_def, ".", 1)
        mod = import_module(mod_name)
        return getattr(mod, mod_name)


@click.command()
@click.argument("root", default=".", type=click.Path(file_okay=False,
                                                     exists=True))
@click.option("-k", "--kakoune", default="",
              help="Kakoune session to attach to")
@click.option("-p", "--place", default=False, is_flag=True,
              help="Try to place the window")
@click.option("--plugins", default="FS,Git",
              help="Plugins to load. These are python classes. Use dotted "
              "notation. Builtin plugins can be referenced by class name only."
              "e.g: --plugins=FS,Git,my.external.Plugin")
@click.option("--ui", default="TermUI", help="TermUI, or none")
def main(root, kakoune, place, plugins, ui):
    """A simple file manager"""
    from .utils import LOGGING_CONFIG
    logging.config.dictConfig(LOGGING_CONFIG)

    root = Path(root).absolute()
    controler = None
    if kakoune:
        if os.environ.get("TMUX"):
            controler = KakouneTmuxClientControler(kakoune, False)
        elif os.environ.get("SWAYSOCK") is not None:
            controler = KakouneSwayClientControler(kakoune, place)
        else:
            controler = KakouneXClientControler(kakoune, place)
    Tree(root, load_plugins(plugins), controler=controler, ui=load_ui(ui)).run()


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
