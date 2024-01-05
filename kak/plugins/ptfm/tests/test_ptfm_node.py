from ptfm.node import Node, Branch, Leaf, OPEN, CLOSED, _NodeIndex


def test_tree():
    root = Branch("a")
    root.children=[]
    b = Branch("a.b", parent=root)
    b.children=[]
    root.append(b)
    l = Leaf("a.b.c", parent=b)
    b.append(l)
    assert root.is_branch
    assert b.is_branch
    assert not l.is_branch
    assert l.root is root
    assert l in list(b)
    b.remove(l)
    assert l not in list(b)
    b.append(l)
    assert l in list(b)
    assert b.status == CLOSED
    b.open()
    assert b.status == OPEN
    b.close()
    assert b.status == CLOSED


def test_index():
    Node.index = _NodeIndex()
    n = Leaf("a.b.c")
    n.set_state("x.y", 2)
    assert n in Node.index.values("x.y")[2]
    n.set_state("x.y", 3)
    assert n not in Node.index.values("x.y")[2]
    assert n in Node.index.values("x.y")[3]
    n.set_state("x.y", 3)
    assert n in Node.index.values("x.y")[3]
    n.toggle_state("x.z")
    assert n in Node.index.values("x.z")[True]
    n.toggle_state("x.z")
    assert n in Node.index.values("x.z")[False]
    assert n not in Node.index.values("x.z")[True]


def test_filter():
    Node.index = _NodeIndex()
    n1 = Leaf("a")
    n2 = Leaf("b")
    n3 = Leaf("c")
    n1.set_state("foo", True)
    n2.set_state("foo", True)
    n3.set_state("foo", False)
    s = set(Node.index.filter("foo", True))
    assert n1 in s
    assert n2 in s


def test_index_dynamic_iter():
    Node.index = _NodeIndex()
    n1 = Leaf("a")
    n2 = Leaf("b")
    n3 = Leaf("c")
    n1.set_state("foo", True)
    n2.set_state("foo", True)
    n3.set_state("foo", True)
    q = Node.index.filter("foo", True)
    assert len(q) == 3
    for idx, data in enumerate(q.dynamic_iter()):
        n1.set_state("foo", False)
        n2.set_state("foo", False)
        n3.set_state("foo", False)
    assert idx == 0
