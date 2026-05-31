"""
Menu peephole pass: recognize the strict pattern
    LOAD_STRING "X" × N → PRINT_STRINGS_HORZ N (or _VERT) → CREATE_MENU → CLEAR_LINE → MULTI_GOTO L_a L_b …

When the pattern matches, the dispatching MULTI_GOTO's case_branch edges are
replaced with menu_option edges (label from LOAD_STRING, target from MULTI_GOTO).

Near-misses (CREATE_MENU not matching) are logged to findings.unrecognized_menus.
"""


def _unquote(arg):
    if len(arg) >= 2 and arg[0] == '"' and arg[-1] == '"':
        return arg[1:-1]
    return arg


def _match_menu_at(op_list, i):
    """
    Try to match the strict menu pattern centered on CREATE_MENU at op_list[i].
    Returns (matched: bool, info: dict).

    On match, info = {'strings': [...], 'targets': [...], 'multigoto_index': int}.
    On miss, info = {'reason': str}.
    """
    # Forward: CREATE_MENU → CLEAR_LINE → MULTI_GOTO
    if i + 2 >= len(op_list):
        return False, {'reason': 'other'}
    if op_list[i + 1].name != 'CLEAR_LINE':
        return False, {'reason': 'non_multigoto'}
    if op_list[i + 2].name != 'MULTI_GOTO':
        return False, {'reason': 'non_multigoto'}

    multigoto = op_list[i + 2]
    targets = list(multigoto.args)

    # Backward: PRINT_STRINGS_HORZ N or PRINT_STRINGS_VERT N immediately before CREATE_MENU
    if i == 0:
        return False, {'reason': 'other'}
    print_op = op_list[i - 1]
    if print_op.name not in ('PRINT_STRINGS_HORZ', 'PRINT_STRINGS_VERT'):
        return False, {'reason': 'other'}
    if not print_op.args:
        return False, {'reason': 'other'}
    try:
        count = int(print_op.args[0])
    except ValueError:
        return False, {'reason': 'other'}

    # Backward: `count` LOAD_STRING opcodes immediately before PRINT_STRINGS
    strings = []
    j = i - 2
    for _ in range(count):
        if j < 0 or op_list[j].name != 'LOAD_STRING' or not op_list[j].args:
            return False, {'reason': 'other'}
        strings.append(_unquote(op_list[j].args[0]))
        j -= 1
    strings.reverse()

    if len(strings) != len(targets):
        return False, {'reason': 'mismatch'}

    return True, {
        'strings': strings,
        'targets': targets,
        'multigoto_index': i + 2,
    }


def find_menus(op_list, current_label, findings):
    """
    Scan an opcode list for CREATE_MENU patterns. For each match, record it.
    For each near-miss, append to `findings`.

    Returns a dict mapping MULTI_GOTO opcode index → match info.
    """
    matches = {}
    for i, op in enumerate(op_list):
        if op.name != 'CREATE_MENU':
            continue
        matched, info = _match_menu_at(op_list, i)
        if matched:
            matches[info['multigoto_index']] = info
        else:
            findings.append({'node': current_label, 'reason': info['reason']})
    return matches
