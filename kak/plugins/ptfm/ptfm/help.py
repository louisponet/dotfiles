from io import StringIO

INTRO = """---------
PTFM Help
---------

PTFM is a simple and plugable file manager. The main philosophy
of the project is that it integrates smoothly in a modal editor
workflow. PTFM is modal itself and most of it's bindings mimic
those of a modal editor.

"""

UNDERLINES = "=+-~"


class Indenter:
    def __init__(self, builder):
        self.builder = builder

    def __enter__(self, *args, **kwargs):
        self.builder.current_indent += 2

    def __exit__(self, *args, **kwargs):
        self.builder.current_indent -= 2


class Builder:
    def __init__(self, app):
        self.out = StringIO()
        self.app = app
        self.current_indent = 0

    def indent(self):
        return Indenter(self)

    def print_indent(self):
        self.out.write(" " * self.current_indent)

    def print_docstring(self, doc):
        doc = doc.strip("\n")
        lines = doc.splitlines()
        indent = len(lines[0]) - len(lines[0].lstrip())
        for line in lines:
            self.printl(line[indent:])

    def add_modes(self):
        return

    def add_filters(self):
        return

    def printl(self, txt):
        if "\n" in txt:
            for line in txt.splitlines():
                self.printl(line)
        else:
            self.print_indent()
            self.out.write(txt)
            self.nl()

    def nl(self):
        self.out.write("\n")

    def print_title(self, txt, level):
        self.printl(txt)
        self.printl(UNDERLINES[level-1] * len(txt))
        self.nl()

    def human_keys(self, keys):
        result = ""
        i = 0
        while i < len(keys):
            if keys[i] == 'escape':
                if i < len(keys) - 1:
                    i += 1
                    result += "<a-" + self.human_keys((keys[i],)).strip("<>") + ">"
                else:
                    result += "<esc>"
            elif keys[i] == "c-m":
                result += "<ret>"
            elif len(keys[i]) > 1:
                result += "<" + keys[i] + ">"
            else:
                result += keys[i]
            i += 1
        return result

    def add_bindings(self):
        self.print_title("Key Bindings", 1)
        for bmode in self.app.ui.bindings.registries:
            mode = bmode.ptfm_mode
            self.print_title(mode.name, 2)
            bindings = {}
            for binding in bmode.key_bindings.bindings:
                bindings.setdefault(
                    binding.handler, []).extend(
                        [self.human_keys(binding.keys)])
            for handler, keys in bindings.items():
                if handler.__name__ == "_":
                    continue
                doc = handler.__doc__
                self.printl(" – ".join(keys))
                with self.indent():
                    if doc is not None:
                        self.print_docstring(doc)
                    else:
                        self.printl(handler.__name__)
                self.nl()

    def add_commands(self):
        self.print_title("Commands", 1)
        for command in set(self.app.commands.values()):
            self.print_title(
                " – ".join([command.fn.__name__] + list(command.aliases)), 2)
            self.print_docstring(command.__doc__)
            self.nl()
            if command.args.name is not None:
                self.print_title("Args", 3)
                self.printl(
                    f"{command.args.name} ({command.args.hnargs})")
                if command.args.doc:
                    with self.indent():
                        self.print_docstring(command.args.doc)
                self.nl()


    def __call__(self):
        self.out.write(INTRO)
        self.add_modes()
        self.add_bindings()
        self.add_commands()
        return self.out.getvalue()


def build_help(app):
    return Builder(app)()
