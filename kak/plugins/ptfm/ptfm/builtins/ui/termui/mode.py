class AppMode:
    next_flag = 1

    def __init__(self, name, parent=None):
        self.name = name
        self.flag = self.next_flag
        self.next_flag = self.next_flag << 1
        if parent is not None:
            self.flag = parent.flag | self.flag

    def __contains__(self, other):
        return bool(other.flag & self.flag)


NAV_MODE = AppMode("NAV")
EDIT_MODE = AppMode("EDIT")
CMD_MODE = AppMode("COMMAND")
