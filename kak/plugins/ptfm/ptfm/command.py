from enum import Flag, auto
import string
import logging


logger = logging.getLogger(__name__)


_NO_DEFAULT = object()


class CurrentNode:
    def __init__(self, name):
        self.name = name

    def __call__(self, cmd):
        cmd.node_name = self.name
        return cmd


class Option:
    def __init__(self, name, default=None, doc="", constructor=str):
        self.name = name
        self.doc = doc
        self.default = default
        self.constructor = constructor

    def __call__(self, cmd):
        cmd.options[self.name] = self
        return cmd


class Arg:
    def __init__(self, name, default=_NO_DEFAULT, nargs=0, doc=""):
        self.name = name
        self.doc = doc
        self.nargs = nargs
        # keep a human-readble version of nargs for documentation
        self.hnargs = str(nargs)
        self.default = default
        self.nargs_validator = self.get_nargs_validator(nargs)

    def __call__(self, cmd):
        cmd.args = self
        return cmd

    def validate_exact(self, nargs):
        if self.nargs != nargs:
            raise ValueError(f"Expected {self.nargs} arguments")

    def validate_range(self, nargs):
        if self.nargs[0] > nargs:
            raise ValueError(f"Not enough arguments")
        if self.nargs[1] < nargs:
            raise ValueError(f"Too many arguments")

    def get_nargs_validator(self, nargs):
        try:
            self.nargs = int(self.nargs)
            return self.validate_exact
        except Exception:
            pass
        try:
            if self.nargs == "?":
                self.nargs = "0..1"
            elif self.nargs == "*":
                self.nargs = "0..999"
            elif self.nargs.endswith(".."):
                self.nargs += "999"
            elif self.nargs.startswith(".."):
                self.nargs = "0" + self.nargs
            self.nargs = [int(i) for i in self.nargs.split("..")]
            return self.validate_range
        except Exception:
            raise ValueError("`nargs` should be one of '*', '?', 'n', "
                             "'n..m', 'n..' or '..m' (with n and m integers)")


class TokenType(Flag):
    WHITESPACE = auto()
    OPT = auto()
    STRING = auto()
    WORD = auto()
    EOF = auto()
    VALUE = STRING | WORD


class Token:
    def __init__(self, text, ptr=None, typ=None):
        self.text = text
        self.typ = typ
        self.ptr = ptr

    def __str__(self):
        return self.text


class ScannerError(Exception):
    pass


class ArgScanner:
    opt_chars = {*tuple(string.ascii_letters + string.digits + "_")}

    def __init__(self, args):
        self.ptr = 0
        self.buffer = args + "\0"
        self.tokens = []

    @classmethod
    def tokenize(cls, text):
        scanner = cls(text)
        tokens = []
        token = scanner.next()
        while token.typ != TokenType.EOF:
            tokens.append(token)
            token = scanner.next()
        return tokens

    def emit(self, start, typ):
        if typ == TokenType.WHITESPACE:
            if self.ptr > start:
                return True
            return False
        if self.ptr > start or typ == TokenType.EOF:
            text = self.buffer[start:self.ptr]
            if typ == TokenType.STRING:
                text = text[1:-1]
                text = text.replace('\\"', '"')
                text = text.replace('\\\\', '\\')
            self.tokens.append(Token(text, ptr=start, typ=typ))
            return True
        return False

    def peek(self, index=0):
        try:
            return self.buffer[self.ptr + index]
        except IndexError:
            return None

    def prefix(self, length=1):
        try:
            return self.buffer[self.ptr:self.ptr + length]
        except IndexError:
            return None

    def forward(self, length=1):
        self.ptr += length

    def next(self):
        while not self.tokens:
            self.fetch_token()
        return self.tokens.pop(0)

    def rollback(self, token):
        self.tokens = [token] + self.tokens

    def fetch_token(self):
        if self.fetch_eof():
            return True
        if self.fetch_whitespace():
            return True
        if self.fetch_opt():
            return True
        if self.fetch_string():
            return True
        if self.fetch_word():
            return True
        assert False, "unreachable"

    def fetch_word(self):
        start = self.ptr
        while self.peek() not in " \t\0":
            self.forward()
        return self.emit(start, TokenType.WORD)

    def fetch_string(self):
        start = self.ptr
        if self.peek() != '"':
            return False
        self.forward()
        while True:
            char = self.peek()
            self.forward()
            if char == "\\":
                if self.peek() in '"\\':
                    self.forward()
            elif char == '"':
                return self.emit(start, TokenType.STRING)
            elif char == "\0":
                raise ScannerError("Found EOF while scanning string literal "
                                   "at %s" % start)

    def fetch_opt(self):
        start = self.ptr
        if self.peek() != "-":
            return False
        self.forward()
        while self.peek() in self.opt_chars:
            self.forward()
        if self.peek() not in " \t\0":
            self.ptr = start
            return False
        return self.emit(start, TokenType.OPT)

    def fetch_whitespace(self):
        start = self.ptr
        while self.peek() in " \t":
            self.forward()
        return self.emit(start, TokenType.WHITESPACE)

    def fetch_eof(self):
        if self.peek() == "\0":
            return self.emit(self.ptr, TokenType.EOF)
        return False


class ParsingError(Exception):
    pass


class Command:
    def __init__(self, fn, *aliases, node_name=None, doc=None):
        self.fn = fn
        self.__doc__ = doc if doc is not None else fn.__doc__
        if self.__doc__ is None:
            self.__doc__ = "Undocumented"
        self.options = {}
        self.args = Arg(name=None, nargs="0..0")
        self.node_name = node_name
        self.self = None
        self.aliases = aliases

    def call_from_string(self, args, node=None):
        logger.debug("%s(%s, node=%s)", self, args, node)
        args = self.parse_call_args(args)
        logger.debug(node)
        logger.debug(self.node_name)
        if self.node_name is not None and node is not None:
            args[self.node_name] = node
        logger.debug(args)
        self(**args)

    def __call__(self, **kwargs):
        # if self.node_name is not None and self.self is not None:
        #     kwargs[self.node_name] = self.self.node
        if self.self is not None:
            args = (self.self,)
        else:
            args = tuple()
        logger.debug(kwargs)
        self.fn(*args, **kwargs)

    def parse_call_args(self, args):
        result = {}
        scanner = ArgScanner(args)
        while self.parse_option(scanner, result):
            pass
        for o in self.options:
            if o.name not in result:
                result[o.name] = o.default
        self.parse_args(scanner, result)
        return result

    def parse_args(self, scanner, result):
        args = []
        while True:
            token = scanner.next()
            if token.typ == TokenType.EOF:
                break
            if not token.typ & TokenType.VALUE:
                raise ParsingError(f"Expected value, got {token.typ.name}")
            args.append(str(token))
        self.args.nargs_validator(len(args))
        if self.args.name is not None:
            result[self.args.name] = args

    def parse_option(self, scanner, result):
        token = scanner.next()
        if token.typ != TokenType.OPT:
            scanner.rollback(token)
            return False
        name = token[1:]
        try:
            opt_def = self.options[name]
        except KeyError:
            raise TypeError(
                "invalid argument `%s` for %s" % (name, self.fn.__name__))
        if opt_def.constructor is bool:
            result[name] = True
        else:
            token = scanner.next()
            if not token.typ & TokenType.VALUE:
                raise ParsingError(f"Missing value for option {name}")
            result[name] = opt_def.constructor(token)
        return True


class command:
    def __init__(self, *aliases, node_name=None, doc=None):
        self.aliases = aliases
        self.doc = doc
        self.node_name = node_name

    def __call__(self, fn):
        cmd = Command(fn, *self.aliases, node_name=self.node_name, doc=self.doc)
        return cmd

    @classmethod
    def gather(cls, plugin, commands):
        klass = plugin if isinstance(plugin, type) else plugin.__class__
        for name in dir(klass):
            cmd = getattr(klass, name)
            if isinstance(cmd, Command):
                cmd = getattr(plugin, name)
                cmd.self = plugin
                commands[name] = cmd
                for a in cmd.aliases:
                    commands[a] = cmd
