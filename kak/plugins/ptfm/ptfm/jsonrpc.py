"""
Simple JSON RPC server implementation for ptfm.
"""

import os
import asyncio
from io import StringIO
import json
from json.decoder import JSONDecodeError
import logging

logger = logging.getLogger(__name__)


class JSONRPCException(Exception):
    error_code = -32603
    default_message = "internal error"

    def __init__(self, msg=None, data=None, id=None):
        self.msg = msg if msg else self.default_message
        self.data = data

    def as_dict(self):
        data = dict(
            jsonrpc="2.0",
            error=dict(
                code=self.error_code,
                message=self.msg
            ),
            id=None
        )
        if self.data:
            data["error"]["data"] = self.data
        return data


class JSONRPCParseException(JSONRPCException):
    error_code = -32700
    default_message = "JSON parsing error"


class JSONRPCInvalidRequestException(JSONRPCException):
    error_code = -32600
    default_message = "Invalid request"


class JSONRPCMethodNotFoundException(JSONRPCException):
    error_code = -32600
    default_message = "Method not found"


class JSONRPCInvalidParamsException(JSONRPCException):
    error_code = -32602
    default_message = "Invalid parameters"


class JSONRPCServer:
    """ Simple JSON-RPC server. This doesn't implement the server
    code and it must be extended to be really useful.

    >>> server = JSONRPCServer()
    >>> class MyProvider:
    ...      def add(self, a, b):
    ...            return a + b
    ...
    >>> server.register("myprov", MyProvider())
    >>> server.call('{"jsonrpc": "2.0", "method": "myprov_add",'
    ...             ' "params": [2, 40], "id": 1}')
    {"jsonrpc": "2.0", "result": 42, "id": 1}
    """

    def __init__(self):
        self.providers = {}

    def register(self, name, provider):
        """Register a method provider. The RPC method lookup uses the
        given `name` as method prefix. See :class:`JSONRPCServer`
        for a complete example
        """
        self.providers[name] = provider

    def unregister(self, name):
        "Unregister a provider"
        del self.methods[name]

    def parse(self, src):
        "Parse the JSON source. Should not be overridden"
        try:
            req = json.loads(src)
        except JSONDecodeError as e:
            raise JSONRPCParseException(data=str(e))
        try:
            id = req["id"]
        except KeyError as e:
            raise JSONRPCInvalidParamsException(data={"key not found": str(e)})
        try:
            return id, req["method"], req["params"]
        except KeyError as e:
            raise JSONRPCInvalidParamsException(data={"key not found": str(e)}, id=id)

    def call(self, src):
        """
        The main entry point for dervided classes. Those classes are supposed
        to get the raw JSON source of the RPC call and pass it to :method call:
        .

        :param src: the raw JSON string
        :returns: the result of the RPC method
        """
        id, method, params = self.parse(src)
        provname, meth = method.split("_", 1)
        provider = self.providers.get(provname)
        if provider is None:
            raise JSONRPCMethodNotFoundException("%s not found" % method, id=id)
        meth = getattr(provider, meth, None)
        if meth is None:
            raise JSONRPCMethodNotFoundException("%s not found" % method, id=id)
        if isinstance(params, list):
            result = meth(*params)
        else:
            result = meth(**params)
        return dict(
            jsonrpc="2.0",
            result=result,
            id=id)


class JSONRPCUnixServer(JSONRPCServer):
    """ Unix domain socket JSON-RPC server extending :class:`JSONRPCServer`

    >>> server = JSONRPCUnixServer("/tmp/my.sock")
    >>> class MyProvider:
    ...      def add(self, a, b):
    ...            return a + b
    ...
    >>> server.register("myprov", MyProvider())

    Using netcat (openbsd flavour):
        $ echo '{"method": "myprov_add", "params": [1, 42], "id": 2}' \
            | nc -q 0 -U /tmp/test.sock
        {"jsonrpc": "2.0", "result": 42, "id": 2}
    """

    def __init__(self, sock_path, *args, **kwargs):
        self.sock_path = sock_path
        self.connections = []
        super().__init__(*args, **kwargs)

    async def serve(self, reader, writer):
        try:
            msg = StringIO()
            while not reader.at_eof():
                chunk = await reader.read(2 ** 16)
                msg.write(chunk.decode())
            try:
                response = self.call(msg.getvalue())
                writer.write(json.dumps(response).encode("utf-8"))
            except JSONRPCException as e:
                writer.write(json.dumps(e.as_dict()).encode("utf-8"))
            finally:
                writer.write_eof()
                await writer.drain()
        except asyncio.CancelledError:
            writer.write_eof()
            await writer.drain()
            reader.close()
            writer.close()
            await reader.wait_closed()
            await writer.wait_closed()
            raise

    def _forget(self, task):
        try:
            self.connections.remove(task)
        except ValueError:
            pass

    async def on_connect(self, reader, writer):
        task = asyncio.ensure_future(self.serve(reader, writer))
        task.add_done_callback(self._forget)
        self.connections.append(task)

    async def close(self):
        for c in self.connections:
            c.cancel()
        os.unlink(self.sock_path)

    async def __call__(self):
        while True:
            try:
                logger.info("starting json rpc server")
                s = await asyncio.start_unix_server(self.on_connect,
                                                    self.sock_path)
                await s.wait_closed()
                return
            except Exception:
                logger.exception("Error while serving JSON RPC")
