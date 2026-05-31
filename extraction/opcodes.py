import re
from dataclasses import dataclass
from typing import Union

ARG_RE = re.compile(r'"[^"]*"|\S+')


@dataclass(frozen=True)
class Opcode:
    name: str
    args: tuple
    raw: str


@dataclass(frozen=True)
class Plaintext:
    text: str


Token = Union[Opcode, Plaintext]


def _split_args(content):
    return ARG_RE.findall(content)


def tokenize_line(line):
    """
    Split a single line into a sequence of Opcode and Plaintext tokens.
    Bracketed segments `[NAME arg1 arg2]` become Opcodes; anything between
    or before them becomes Plaintext.
    """
    tokens = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] == '[':
            j = line.find(']', i)
            if j == -1:
                tokens.append(Plaintext(text=line[i:]))
                break
            content = line[i + 1:j]
            parts = _split_args(content)
            name = parts[0] if parts else ''
            args = tuple(parts[1:])
            tokens.append(Opcode(name=name, args=args, raw=line[i:j + 1]))
            i = j + 1
        else:
            j = line.find('[', i)
            if j == -1:
                tokens.append(Plaintext(text=line[i:]))
                break
            tokens.append(Plaintext(text=line[i:j]))
            i = j
    return tokens


def parse_block(lines):
    """Tokenize every line in a block, returning a flat token list."""
    tokens = []
    for line in lines:
        tokens.extend(tokenize_line(line))
    return tokens


def reconstruct_line(tokens):
    """Inverse of tokenize_line: rebuild the line from its tokens."""
    return ''.join(t.raw if isinstance(t, Opcode) else t.text for t in tokens)
