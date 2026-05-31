"""
Plaintext rendering: walk a token sequence and produce a display-oriented string.

Drops edges, effects, and queries (they're represented elsewhere). Translates
display-related opcodes per the spec rules. Unknown opcodes are logged but
silently dropped from the rendered output.
"""

from . import opcodes


_FORMATTING_NOISE = {'START_LINE'}  # drop entirely

_NEWLINE = {
    'LINE_BREAK': '\n',   # within-window line wrap
    'CLEAR_LINE': '\n\n', # clear textbox → paragraph break
}

_PAUSE_OPCODES = {'WAIT', 'HALT', 'HALT_PROMPT', 'PAUSE'}

_SUBSTITUTION_NULLARY = {
    'PRINT_DELTA': '[DELTA]',
    'PRINT_ATTACKER': '[ATTACKER]',
    'PRINT_TARGET': '[TARGET]',
    'PRINT_SMASH': '[SMASH]',
    'PRINT_YOU_WON': '[YOU_WON]',
}

_SUBSTITUTION_UNARY = {
    'PRINT_NAME': 'NAME',
    'PRINT_LETTER': 'LETTER',
    'PRINT_ITEM': 'ITEM',
    'PRINT_STAT': 'STAT',
    'PRINT_NUM': 'NUM',
    'PRINT_MONEY': 'MONEY',
    'PRINT_TELE_DEST': 'TELE_DEST',
    'PRINT_PSI': 'PSI',
}

_TEXT_PLUMBING = {
    # Menu UI plumbing — options appear as `menu_option` edges
    'LOAD_STRING', 'PRINT_STRINGS_HORZ', 'PRINT_STRINGS_VERT', 'CREATE_MENU',
    # Textbox plumbing
    'OPEN_TBOX', 'OPEN_HP_PP', 'CLOSE_FOCUS_TBOX', 'CLOSE_ALL_TBOXES',
    'SAVE_TBOX_CTX', 'SET_FOCUS_TBOX', 'CLEAR_TBOX', 'MENU_TBOX',
    'MENU_TBOX_NOCANCEL', 'SHOW_WALLET',
    # Fonts / formatting
    'NORMAL_FONT', 'SATURN_FONT', 'DO_WORDWRAP', 'PARTY_DESCRIPTION',
    'ALIGN_TEXT', 'NUM_PADDING', 'TEXT_COLOR',
    # Battle-text utilities
    'GET_ATTACKER_GENDER', 'GET_ATTACKER_PARTY_LIVING_COUNT',
    'GET_TARGET_GENDER', 'GET_TARGET_PARTY_LIVING_COUNT',
    '1C_08_INVALID',
}


def render(tokens, unknown_log):
    parts = []
    for t in tokens:
        if isinstance(t, opcodes.Plaintext):
            parts.append(t.text)
            continue

        name = t.name
        if name in _FORMATTING_NOISE or name in _TEXT_PLUMBING:
            continue
        if name in _NEWLINE:
            parts.append(_NEWLINE[name])
            continue
        if name in _PAUSE_OPCODES:
            parts.append('[PAUSE]')
            continue
        if name in _SUBSTITUTION_NULLARY:
            parts.append(_SUBSTITUTION_NULLARY[name])
            continue
        if name in _SUBSTITUTION_UNARY:
            prefix = _SUBSTITUTION_UNARY[name]
            arg = t.args[0] if t.args else ''
            parts.append(f'[{prefix}:{arg}]' if arg else f'[{prefix}]')
            continue
        # Anything else (edges, effects, queries) is represented elsewhere — drop silently.

    return ''.join(parts).strip()
