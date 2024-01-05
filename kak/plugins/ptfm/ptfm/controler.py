class ClientControler:
    def __init__(self, place=False):
        if place:
            self._place()

    def open_file(self, node):
        "open a file in the client"
        raise NotImplementedError()

    def open_scratch(self, content, name="scratch", filetype=None, goto=False):
        "open a scratch buffer in the client"
        raise NotImplementedError()

    def focus_client(self):
        "focus the client"
        raise NotImplementedError()

    def open_buffers(self):
        "get a list of open buffers from the client"
        return None

    def watch_buffers(self):
        """
        Return an asynchronous iterator yielding clients open buffers on change
        """
        raise NotImplementedError()

    def quit(self):
        "Hook called when the nain app quits"


class DumyClientControler(ClientControler):
    def open_file(self, node):
        pass

    def open_scratch(self, content, name="scratch", filetype=None, goto=False):
        pass

    def focus_client(self):
        pass
