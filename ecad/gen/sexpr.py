"""Minimal S-expression reader and writer for KiCad files.

Atoms are kept as Python strings. Quoted strings are wrapped in Q so the writer
can quote them again; bare atoms stay plain str.
"""


class Q(str):
    """A string that was quoted in the source and must be quoted on output."""


def parse(text):
    pos = 0
    n = len(text)
    stack = [[]]
    while pos < n:
        c = text[pos]
        if c in " \t\r\n":
            pos += 1
        elif c == "(":
            stack.append([])
            pos += 1
        elif c == ")":
            node = stack.pop()
            stack[-1].append(node)
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while text[pos] != '"':
                if text[pos] == "\\":
                    buf.append(text[pos:pos + 2])
                    pos += 2
                else:
                    buf.append(text[pos])
                    pos += 1
            pos += 1
            stack[-1].append(Q("".join(buf)))
        else:
            start = pos
            while pos < n and text[pos] not in ' \t\r\n()"':
                pos += 1
            stack[-1].append(text[start:pos])
    return stack[0][0]


def dump(node, indent=0):
    """Write a node in KiCad's tab indented style."""
    if not isinstance(node, list):
        return atom(node)
    tabs = "\t" * indent
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return tabs + "(" + " ".join(atom(x) for x in node) + ")"
    head = []
    rest = []
    for i, x in enumerate(node):
        if isinstance(x, list):
            rest = node[i:]
            break
        head.append(x)
    lines = [tabs + "(" + " ".join(atom(x) for x in head)]
    for x in rest:
        if isinstance(x, list):
            lines.append(dump(x, indent + 1))
        else:
            lines.append("\t" * (indent + 1) + atom(x))
    lines.append(tabs + ")")
    return "\n".join(lines)


def atom(x):
    if isinstance(x, Q):
        return '"' + x.replace('"', '\\"') + '"' if '\\' not in x else '"' + x + '"'
    if isinstance(x, float):
        s = f"{x:.4f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(x)


def find(node, key):
    """First child list whose head is key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
