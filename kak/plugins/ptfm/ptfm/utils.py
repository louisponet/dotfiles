import asyncio


class _MultiplexedIterator:
    def __init__(self):
        self.fut = asyncio.Future()

    async def __anext__(self):
        result = await self.fut
        self.fut = asyncio.Future()
        return result


class Multiplexer:
    def __init__(self, iter):
        self.iter = iter
        self.children = []
        self.task = None

    def __aiter__(self):
        iterator = _MultiplexedIterator()
        self.children.append(iterator)
        if not self.task:
            self.task = asyncio.ensure_future(self())
        return iterator

    async def __call__(self):
        async for i in self.iter:
            for c in self.children:
                c.fut.set_result(i)
        for c in self.children:
            c.fut.set_exception(StopAsyncIteration)
        self.children = []
        self.task = None


def rsplit(string, sep=" ", num=1):
    parts = string.split(sep)
    return [sep.join(parts[:-num])] + parts[-num:]


_DEBUG = {"handlers": ["file", "console"],
          "level": "DEBUG", "propagate": False}


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - "
            "%(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "CRITICAL",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filename": "/tmp/ptfm_log",
            "mode": "w",
        }
    },
    "loggers": {
        "ptfm": {"handlers": ["file", "console"], "level": "INFO"},
        "ptfm.ptfm": _DEBUG,
        "ptfm.builtins.plugins.fs": _DEBUG,
        "ptfm.builtins.ui.termui": _DEBUG,
        # "ptfm.processors": _DEBUG,
        "ptfm.command": _DEBUG,
        "ptfm.builtins.controler": _DEBUG,
        "ptfm.ui": _DEBUG,
    },
}
