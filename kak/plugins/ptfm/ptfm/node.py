import weakref
from weakref import WeakSet
from collections import defaultdict

from .event import emit

CLOSED = 0
OPEN = 1


class _IndexValues:
    def __init__(self):
        self.values = dict()

    def set_item(self, value, node):
        for k, set_ in self.values.items():
            if node in set_:
                if k == value:
                    return False
                else:
                    set_.remove(node)
                    break
        try:
            set_ = self.values[value]
        except KeyError:
            set_ = self.values.setdefault(value, WeakSet())
        set_.add(node)
        return True

    def __getitem__(self, value):
        return self.values[value]

    def __contains__(self, key):
        return key in self.values


class IndexQuery:
    def __init__(self, index):
        self.index = index
        self.excludes = dict()
        self.includes = dict()
        self.pre_includes = None
        self.pre_excludes = None
        self.sort_fn = None
        self.materialized = None

    def exclude(self, key, value):
        assert self.materialized is None
        new = self.copy()
        new.excludes[key] = value
        return new

    def filter(self, key=None, value=None, filter_fn=None):
        assert self.materialized is None
        new = self.copy()
        new.includes[key] = value
        return new

    def union(self, other):
        assert self.materialized is None
        new = IndexQuery(self.index)
        new.pre_includes = (self._select().union(other._select()))
        return new

    def sort(self, func):
        assert self.materialized is None
        new = self.copy()
        new.sort_fn = func
        return new

    def copy(self):
        new = IndexQuery(self.index)
        new.excludes.update(self.excludes)
        new.includes.update(self.includes)
        new.pre_includes = self.pre_includes
        new.pre_excludes = self.pre_excludes
        new.sort_fn = self.sort_fn
        return new

    def __len__(self):
        return len(self.select())

    def __contains__(self, item):
        return item in self.select()

    def select(self):
        if self.materialized is None:
            self.materialized = self._select()
        return self.materialized

    def _select(self):
        if self.pre_includes is not None:
            pi = self.pre_includes
            if self.pre_excludes is not None:
                pi = pi.difference(self.pre_excludes)
            results = pi
        else:
            results = None
        for k, v in self.includes.items():
            vals = self.index.values(k)
            if v not in vals:
                return set()
            if results is None:
                results = vals[v]
            else:
                results = results.intersection(vals[v])
            if len(results) == 0:
                return set()
        if results is None:
            return set()
        if self.pre_excludes:
            results = results.difference(self.pre_excludes)
        for k, v in self.excludes.items():
            if len(results) == 0:
                return set()
            vals = self.index.values(k)
            if v not in vals:
                continue
            results = results.difference(vals[v])
        return results

    def __iter__(self):
        iterable = self.select()
        if self.sort_fn is not None:
            iterable = list(iterable)
            iterable.sort(key=self.sort_fn)
        for i in iterable:
            yield i

    def _dynamic_iter(self):
        iterator = self
        version = self.index.version
        seen = set()
        while True:
            for i in iterator:
                seen.add(i)
                yield i
                if self.index.version != version:
                    version = self.index.version
                    iterator = self.copy()
                    iterator.pre_includes = self.materialized
                    iterator.pre_excludes = seen
                    break
            else:
                break

    def dynamic_iter(self):
        return self.copy()._dynamic_iter()


class _NodeIndex:
    def __init__(self):
        self.index = defaultdict(defaultdict)
        self.version = 0
        self.update_consumers = []

    def values(self, key):
        idx = self.index
        path = key.split(".")
        for k in path[:-1]:
            idx = idx[k]
        if path[-1] in idx:
            return idx[path[-1]]
        else:
            return idx.setdefault(path[-1], _IndexValues())

    def add(self, key, value, node):
        vals = self.values(key)
        changed = vals.set_item(value, node)
        if changed:
            self.version += 1
            for fn in self.update_consumers:
                fn()
        return changed

    def filter(self, key, value):
        return IndexQuery(self).filter(key, value)

    def batch_toggle(self, key, value):
        vals = self.values(key)
        if (not value) in vals: 
            toggled = vals[not value]
        else:
            return
        for node in toggled:
            node._state[key] = value
        vals.values.setdefault(value, WeakSet()).update(toggled)
        del vals.values[not value]


class Node:
    index = _NodeIndex()

    def __init__(self, path, parent=None):
        self.update_consumers = []
        self.path = path
        if parent is not None:
            self._parent = weakref.ref(parent)
        else:
            self._parent = None
            self._version = 0
        self.basename = None
        self.dirname = None
        self._state = dict()
        self.set_state("deleted", False)
        self.set_state("visible", True)
        self.set_state("displayed", True)
        self.display_name = self.basename
        self.tokens = []
        self.prefixes = set()
        self.sufixes = []
        self.style = None
        self._root = None

    def updated(self):
        if self.parent is None:
            self._version += 1
        else:
            self.parent.updated()
        for fn in self.update_consumers:
            fn()

    @property
    def parent(self):
        if self._parent is None:
            return None
        return self._parent()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state is None:
            return
        self._state = state
        self.updated()

    @property
    def visible(self):
        return self.state["visible"]

    @visible.setter
    def visible(self, is_visible):
        self.set_state("visible", is_visible)

    @property
    def displayed(self):
        return self.state["displayed"]

    @displayed.setter
    def displayed(self, is_displayed):
        self.set_state("displayed", is_displayed)

    def set_state(self, key, value):
        try:
            if self.state[key] == value:
                return
        except KeyError:
            pass
        self._state[key] = value
        self.index.add(key, value, self)
        self.updated()

    def toggle_state(self, state):
        self.set_state(state, not self.state.get(state, False))
        self.updated()

    def add_prefix(self, text, style, transient=False):
        p = (style, text)
        if p not in self.prefixes:
            self.prefixes.add((style, text))
            if transient and self.parent is not None:
                self.parent.add_prefix(text, style, True)
            self.updated()

    def add_sufix(self, text, style, transient=False):
        s = (style, text)
        if s not in self.sufixes:
            self.sufixes.append(style, text)
            if transient and self.parent is not None:
                self.parent.add_sufix(text, style, True)
            self.updated()

    def relative(self):
        raise NotImplementedError()

    @property
    def root(self):
        if self._root is None:
            if self.parent is None:
                self._root = self
            else:
                self._root = self.parent.root
        return self._root

    @staticmethod
    def sort_key(node):
        return node.path

    @property
    def is_branch(self):
        return isinstance(self, Branch)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.path)

    def __str__(self):
        return str(self.path)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return self.path == other.path

    def __ne__(self, other):
        if type(self) is not type(other):
            return True
        return self.path != other.path

    def __le__(self, other):
        return self == other or self < other

    def __lt__(self, other):
        if self.path == other.path:
            return isinstance(other, TempNode)
        if self.parent is None:
            return True
        if other.parent is None:
            return False
        if self.dirname == other.dirname:
            if self.is_branch:
                if other.is_branch:
                    return self.basename < other.basename
                else:
                    return True
            else:
                if other.is_branch:
                    return False
                else:
                    if self.basename == other.basename:
                        return isinstance(other, TempNode)
                    else:
                        return self.basename < other.basename
        elif self.dirname.startswith(other.dirname):
            return self.parent < other
        else:
            return other.parent > self

    def __ge__(self, other):
        return self == other or self > other

    def __gt__(self, other):
        if self.path == other.path:
            return isinstance(self, TempNode)
        if self.parent is None:
            return False
        if other.parent is None:
            return True
        if self.dirname == other.dirname:
            if self.is_branch:
                if other.is_branch:
                    return self.basename > other.basename
                else:
                    return False
            else:
                if other.is_branch:
                    return True
                else:
                    if self.basename == other.basename:
                        return isinstance(self, TempNode)
                    else:
                        return self.basename > other.basename
        elif self.dirname.startswith(other.dirname):
            return self.parent > other
        else:
            return other.parent < self


class Leaf(Node):
    pass


class TempNode(Node):
    def commit(self, name):
        pass


class Branch(Node):
    def __init__(self, path, parent=None):
        self.children = None
        super().__init__(path, parent)
        self._state = dict()
        self.set_state("deleted", False)
        self.set_state("status", CLOSED)
        self.set_state("visible", True)

    @property
    def status(self):
        return self.state["status"]

    @status.setter
    def status(self, status):
        self.set_state("status", status)
        self.updated()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if state is None:
            return
        status = state.pop("status", self.status)
        state["status"] = self.status
        for k, v in state:
            self.set_state(k, v)
        if status == OPEN:
            self.open()
        elif status == CLOSED:
            self.close()
        self.updated()

    @property
    def visible(self):
        return self.state["visible"]

    @visible.setter
    def visible(self, is_visible):
        self.set_state("visible", is_visible)
        if is_visible:
            if self.status is OPEN:
                for c in self:
                    c.visible = True
        else:
            if self.loaded:
                for c in self:
                    c.visible = False
    @property
    def displayed(self):
        return self.state["displayed"]

    @displayed.setter
    def displayed(self, is_displayed):
        self.set_state("displayed", is_displayed)
        if self.loaded:
            for c in self:
                c.displayed = is_displayed

    @property
    def loaded(self):
        return self.children is not None

    def __iter__(self):
        for c in self.children:
            yield c

    def load(self):
        raise NotImplementedError()

    def open(self):
        if self.status == OPEN:
            return
        self.status = OPEN
        if not self.loaded:
            self.load()
        if self.visible:
            for c in self:
                c.visible = True
        emit("branch_open", node=self)

    def close(self):
        # if self.status == CLOSED:
        #     return
        for c in self:
            c.visible = False
        self.status = CLOSED
        emit("branch_closed", node=self)

    def ropen(self):
        self.open()
        for d in self.children:
            if d.is_branch:
                d.ropen()

    def insert_after(self, ref, node: Node) -> bool:
        node.dirname = str(self)
        if ref is None:
            node.basename = ""
            self.children = [node] + self.children
            return True
        node.basename = ref.basename
        try:
            idx = self.children.index(ref)
            self.children.insert(idx+1, node)
        except ValueError:
            return False
        return True

    def append(self, node: Node):
        self.children.append(node)
        self.children.sort()
        self.updated()

    def remove(self, node: Node) -> bool:
        try:
            self.children.remove(node)
            self.updated()
        except ValueError:
            return False
        return True

    def refresh(self) -> bool:
        """Create/delete children. Existing children shouldn't be changed"""
        raise NotImplementedError
