#!/usr/bin/env python
"""
Regenerate resources/dialogue/addresses.txt from the script-dumper output.

Replaces the stale addresses.txt — which doesn't match the current dumper's
address set and was the sole source of `missing_labels_from_addresses_txt`
errors — with the actual address set the dumper produces.

Format matches the existing file: UTF-16 LE with BOM, lowercase 6-digit hex
addresses, one per CRLF-terminated line, sorted.
"""

import os
import sys

CD = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, CD)

from extraction import script_index, sources

ADDRESSES_TXT = sources.ADDRESSES_TXT


def main():
    with open(sources.SCRIPT_DUMPER_OUTPUT, encoding='utf-8') as f:
        idx = script_index.parse_script(f.read())

    addrs = sorted(a.lower() for a in idx.address_to_label.keys())
    print(f'collected {len(addrs)} addresses from {sources.SCRIPT_DUMPER_OUTPUT}')

    backup = ADDRESSES_TXT + '.bak'
    if os.path.exists(ADDRESSES_TXT) and not os.path.exists(backup):
        os.rename(ADDRESSES_TXT, backup)
        print(f'backed up old addresses.txt to {backup}')

    with open(ADDRESSES_TXT, 'w', encoding='utf-16', newline='') as f:
        for addr in addrs:
            f.write(addr + '\r\n')
    print(f'wrote {ADDRESSES_TXT}')


if __name__ == '__main__':
    main()
