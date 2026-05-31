import re
from typing import NamedTuple

LABEL_RE = re.compile(r'^(L_[0-9A-F]{6}|Npc[0-9]{4}):$')
ADDRESS_COMMENT_RE = re.compile(r'^; \$([0-9A-F]{6})$')
INLINE_ADDRESS_RE = re.compile(r'; \$([0-9A-F]{6})\s*$')


class ScriptIndex(NamedTuple):
    labels: dict           # label → list of opcode lines
    order: list            # labels in script linear order
    address_to_label: dict # hex address (uppercase, no prefix) → canonical label


def parse_script(raw_text):
    """
    Split the script-dumper output into a {label: [line, ...]} dict plus a
    linear-order list of labels and an address-to-label map.

    Blocks are delimited by label lines (`L_XXXXXX:` or `NpcNNNN:`). Each block
    runs from its label line up to the next label line. The `; $XXXXXX` comment
    that precedes each label gives us the address — useful because a single
    address has exactly one canonical label, and a YAML text-pointer may need
    to resolve to either `NpcNNNN` (preferred when the dumper assigned it) or
    `L_XXXXXX`.
    """
    labels = {}
    order = []
    address_to_label = {}
    current_label = None
    current_lines = []
    last_address = None

    for line in raw_text.splitlines():
        m_addr = ADDRESS_COMMENT_RE.match(line)
        if m_addr:
            last_address = m_addr.group(1)
            continue

        match = LABEL_RE.match(line)
        if match:
            if current_label is not None:
                labels[current_label] = current_lines
                order.append(current_label)
            current_label = match.group(1)
            current_lines = []
            if last_address is not None:
                address_to_label[last_address] = current_label
            continue

        if current_label is None:
            continue

        # The dumper sometimes emits `; $XXXXXX` inline at the end of an opcode
        # line, when the next instruction needs a label but the prior opcode
        # didn't add a newline. Capture the address and strip it from the line.
        m_inline = INLINE_ADDRESS_RE.search(line)
        if m_inline:
            last_address = m_inline.group(1)
            line = INLINE_ADDRESS_RE.sub('', line).rstrip()
            if not line:
                continue

        if line == '' or line.startswith('; $'):
            continue
        current_lines.append(line)

    if current_label is not None:
        labels[current_label] = current_lines
        order.append(current_label)

    return ScriptIndex(labels=labels, order=order, address_to_label=address_to_label)


def load_addresses_txt(path):
    """
    Load the canonical address list. The file is UTF-16 LE with BOM; entries are
    lowercase 6-digit hex (e.g. `c50000`), one per line. Returns a set of raw
    uppercase 6-digit hex strings (no prefix) — callers resolve to the
    canonical label via `index.address_to_label` when needed, because some
    addresses are labeled `NpcNNNN` rather than `L_XXXXXX`.
    """
    with open(path, encoding='utf-16') as f:
        return {token.strip().upper() for token in f if token.strip()}


def cross_check_addresses(index, addresses):
    """
    Return raw hex addresses in `addresses` whose canonical label is not in
    `index.labels`.
    """
    missing = []
    for hex_addr in sorted(addresses):
        canonical = index.address_to_label.get(hex_addr)
        if canonical is None or canonical not in index.labels:
            missing.append(hex_addr)
    return missing


def summarize(index):
    hex_count = sum(1 for k in index.labels if k.startswith('L_'))
    npc_count = sum(1 for k in index.labels if k.startswith('Npc'))
    return {
        'hex': hex_count,
        'npc': npc_count,
        'total': hex_count + npc_count,
    }
