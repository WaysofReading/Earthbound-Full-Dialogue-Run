from . import menus, opcodes, plaintext

# Opcodes already represented as edges — skip during effect extraction.
_EDGE_OPCODES = {
    'GOTO', 'POST_FADE_GOTO', 'GOTO_IF_FLAG', 'GOTO_IF_FALSE', 'GOTO_IF_TRUE',
    'GOSUB', 'MULTI_GOTO', 'MULTI_GOSUB', 'END',
    'LOAD_FLAG', 'CHECK_EQUAL', 'CHECK_NOT_EQUAL',
    'RESULT_TO_ARG', 'COUNTER_TO_ARG', 'SWAP_ARG_RESULT',
    'COMPARE_REG', 'SET_COUNTER', 'INC_COUNTER',
    'BACKUP_REGS_LOCAL', 'RESTORE_REGS_LOCAL',
    'BACKUP_REGS_GLOBAL', 'RESTORE_REGS_GLOBAL',
}

# Opcodes represented in plaintext rendering — skip during effect extraction.
_TEXT_OPCODES = {
    'LINE_BREAK', 'START_LINE', 'WAIT', 'PAUSE', 'HALT', 'HALT_PROMPT', 'CLEAR_LINE',
    'LOAD_STRING', 'PRINT_STRINGS_HORZ', 'PRINT_STRINGS_VERT', 'CREATE_MENU',
    'PRINT_NAME', 'PRINT_LETTER', 'PRINT_ITEM', 'PRINT_STAT', 'PRINT_NUM',
    'PRINT_MONEY', 'PRINT_TELE_DEST', 'PRINT_PSI', 'PRINT_DELTA',
    'PRINT_ATTACKER', 'PRINT_TARGET', 'NUM_PADDING', 'TEXT_COLOR',
    'OPEN_TBOX', 'OPEN_HP_PP', 'CLOSE_FOCUS_TBOX', 'CLOSE_ALL_TBOXES',
    'SAVE_TBOX_CTX', 'SET_FOCUS_TBOX', 'CLEAR_TBOX', 'MENU_TBOX',
    'MENU_TBOX_NOCANCEL', 'SHOW_WALLET',
    'NORMAL_FONT', 'SATURN_FONT', 'DO_WORDWRAP', 'PARTY_DESCRIPTION',
    'ALIGN_TEXT', 'PRINT_SMASH', 'PRINT_YOU_WON',
    'GET_ATTACKER_GENDER', 'GET_ATTACKER_PARTY_LIVING_COUNT',
    'GET_TARGET_GENDER', 'GET_TARGET_PARTY_LIVING_COUNT',
    '1C_08_INVALID',
}

# Pure read-only queries that don't change game state — skip during effect extraction.
_QUERY_OPCODES = {
    'GET_PARTY_MEMBER', 'GET_NAME_LETTER', 'GET_ESCARGO',
    'GET_ESCARGO COUNTER', 'GET_INV_ITEM',
    'GET_STATUS_GROUP', 'GET_REQUIRED_EXP', 'GET_TBOX_OPTION_COUNT',
    'GET_DELTA', 'GET_ACTION_ARG', 'GET_PARTY_COUNT', 'GET_FOOD_TYPE',
    'GET_DIR_FROM_PMEMBER', 'GET_DIR_FROM_NPC', 'GET_DIR_FROM_OBJ',
    'FIND_CONDIMENT', 'GET_STAT', 'GET_STAT_LETTER',
    'GET_ITEM_PRICE', 'GET_ITEM_SELL_PRICE', 'GET_ITEM_TYPE',
    'CHECK_ITEM_TYPE', 'INV_HAS_SPACE', 'CHECK_ITEM_EQUIPPED',
    'CHECK_HAS_ITEM', 'CHECK_CAN_STORE_SLOT', 'CHECK_STATUS',
    'CHECK_SLOT_EQUIPPED', 'CHECK_CAN_EQUIP_SLOT', 'CHECK_HASNT_MONEY',
    'CHECK_HAS_ATM_MONEY', 'CHECK_PARTY_COUNT', 'CHECK_SELF_TARGETTING',
    'CHECK_EXIT_MOUSE', 'CHECK_CAN_EQUIP_ITEM',
    'CHECK_INTERACTED_PRESENT_OPENED', 'CHECK_IS_ATTACKER_ENEMY',
    'RAND_RANGE', 'GET_DIR_TO_TRUFFLE', 'GET_EARNED_MONEY',
    'UNK_19_1C', 'UNK_19_1D', 'UNK_18_0D', 'UNK_1F_60',
    'NOP_1', 'NOP_2',
}


def _parse_flag(arg):
    """Return (flag_id, flag_label). Numeric → (int, None); symbolic → (None, str)."""
    try:
        return int(arg), None
    except ValueError:
        return None, arg


def _find_fallthrough(op_list, start_index, current_label, label_index, script_order):
    """
    Where execution lands after the conditional at op_list[start_index] if its
    condition is false. Traces forward through the rest of the block, skipping
    side-effect opcodes and independent conditionals, and stops at the first
    unconditional terminator. Returns a node ID or None.

    Rules:
    - GOTO / POST_FADE_GOTO → that opcode's target
    - END → None (execution stops)
    - MULTI_GOTO / MULTI_GOSUB → None (control transfer is uncertain)
    - Walked off end without a terminator → next labeled block in script order
    - No next labeled block → None
    """
    j = start_index + 1
    while j < len(op_list):
        op = op_list[j]
        if op.name in ('GOTO', 'POST_FADE_GOTO'):
            return op.args[0] if op.args else None
        if op.name == 'END':
            return None
        if op.name in ('MULTI_GOTO', 'MULTI_GOSUB'):
            return None
        j += 1
    idx = label_index.get(current_label)
    if idx is not None and idx + 1 < len(script_order):
        return script_order[idx + 1]
    return None


def extract_edges(op_list, current_label, label_index, script_order, menu_matches=None):
    """
    Build the list of edges for a single node, given its opcode sequence.

    If `menu_matches` (dict from MULTI_GOTO opcode index → match info) is given,
    those MULTI_GOTO opcodes emit `menu_option` edges instead of `case_branch`.
    """
    menu_matches = menu_matches or {}
    edges = []
    i = 0
    n = len(op_list)
    while i < n:
        op = op_list[i]
        name = op.name

        if name in ('GOTO', 'POST_FADE_GOTO'):
            if op.args:
                edges.append({'type': 'unconditional', 'target': op.args[0]})

        elif name == 'GOTO_IF_FLAG' and len(op.args) >= 2:
            flag, flag_label = _parse_flag(op.args[0])
            edge = {
                'type': 'flag_test',
                'flag': flag,
                'flag_label': flag_label,
                'polarity': 'set',
                'target': op.args[1],
            }
            ft = _find_fallthrough(op_list, i, current_label, label_index, script_order)
            if ft is not None:
                edge['fallthrough'] = ft
            edges.append(edge)

        elif name == 'LOAD_FLAG' and i + 1 < n:
            next_op = op_list[i + 1]
            if next_op.name in ('GOTO_IF_FALSE', 'GOTO_IF_TRUE') and op.args and next_op.args:
                flag, flag_label = _parse_flag(op.args[0])
                polarity = 'cleared' if next_op.name == 'GOTO_IF_FALSE' else 'set'
                edge = {
                    'type': 'flag_test',
                    'flag': flag,
                    'flag_label': flag_label,
                    'polarity': polarity,
                    'target': next_op.args[0],
                }
                ft = _find_fallthrough(op_list, i + 1, current_label, label_index, script_order)
                if ft is not None:
                    edge['fallthrough'] = ft
                edges.append(edge)
                i += 1  # consume the paired conditional

        elif name == 'CHECK_EQUAL' and i + 1 < n:
            next_op = op_list[i + 1]
            if next_op.name == 'GOTO_IF_TRUE' and op.args and next_op.args:
                edges.append({
                    'type': 'case_branch',
                    'discriminant': 'REG_RESULT',
                    'value': op.args[0],
                    'kind': 'goto',
                    'target': next_op.args[0],
                })
                i += 1

        elif name == 'GOSUB':
            if op.args:
                edges.append({'type': 'function_call', 'target': op.args[0]})

        elif name == 'MULTI_GOTO':
            if i in menu_matches:
                match = menu_matches[i]
                for label_str, target in zip(match['strings'], match['targets']):
                    edges.append({'type': 'menu_option', 'label': label_str, 'target': target})
            else:
                for idx_, target in enumerate(op.args):
                    edges.append({
                        'type': 'case_branch',
                        'discriminant': 'REG_RESULT',
                        'value': str(idx_),
                        'kind': 'goto',
                        'target': target,
                    })

        elif name == 'MULTI_GOSUB':
            for idx_, target in enumerate(op.args):
                edges.append({
                    'type': 'case_branch',
                    'discriminant': 'REG_RESULT',
                    'value': str(idx_),
                    'kind': 'call',
                    'target': target,
                })

        i += 1
    return edges


def _parse_int(arg):
    try:
        return int(arg)
    except (ValueError, TypeError):
        return None


def _build_effect(op):
    """Map a side-effect opcode to a typed effect dict (or 'other' fallback)."""
    name = op.name

    if name in ('SET_FLAG', 'CLR_FLAG'):
        if not op.args:
            return None
        flag, flag_label = _parse_flag(op.args[0])
        effect_type = 'set_flag' if name == 'SET_FLAG' else 'clear_flag'
        return {'type': effect_type, 'flag': flag, 'flag_label': flag_label}

    if name in ('GIVE_ITEM', 'GIVE_ITEM_RETURN_SLOT', 'REMOVE_ITEM', 'REMOVE_ITEM_SLOT'):
        item_arg = op.args[1] if len(op.args) >= 2 else (op.args[0] if op.args else None)
        if item_arg is None:
            return None
        item_id, item_label = _parse_flag(item_arg)
        effect_type = 'give_item' if name.startswith('GIVE_') else 'take_item'
        return {'type': effect_type, 'item': item_id, 'item_label': item_label}

    if name in ('ADD_MONEY', 'REMOVE_MONEY', 'ADD_ATM_MONEY', 'REMOVE_ATM_MONEY'):
        amount = _parse_int(op.args[0]) if op.args else None
        if amount is not None and name.startswith('REMOVE_'):
            amount = -amount
        return {'type': 'change_money', 'amount': amount}

    if name == 'START_BATTLE':
        return {'type': 'start_battle', 'encounter': _parse_int(op.args[0]) if op.args else None}

    if name == 'PLAY_MUSIC':
        return {'type': 'play_music', 'track': _parse_int(op.args[0]) if op.args else None}

    if name == 'ADD_PMEMBER':
        return {'type': 'change_party', 'action': 'add',
                'member': op.args[0] if op.args else None}
    if name == 'REMOVE_PMEMBER':
        return {'type': 'change_party', 'action': 'remove',
                'member': op.args[0] if op.args else None}

    return {'type': 'other', 'raw': op.raw}


def extract_effects(op_list):
    """Build the effect list for a single node from its opcode sequence."""
    effects = []
    for op in op_list:
        name = op.name
        if name in _EDGE_OPCODES or name in _TEXT_OPCODES or name in _QUERY_OPCODES:
            continue
        eff = _build_effect(op)
        if eff is not None:
            effects.append(eff)
    return effects


def build_node(label, lines, tokens, label_index, script_order, menu_findings, unknown_log):
    op_list = [t for t in tokens if isinstance(t, opcodes.Opcode)]
    menu_matches = menus.find_menus(op_list, label, menu_findings)
    edges = extract_edges(op_list, label, label_index, script_order, menu_matches)
    effects = extract_effects(op_list)
    rendered = plaintext.render(tokens, unknown_log)
    raw = '\r\n'.join(lines)
    label_kind = 'npc' if label.startswith('Npc') else 'hex'
    return {
        'id': label,
        'label_kind': label_kind,
        'raw': raw,
        'plaintext': rendered,
        'edges': edges,
        'effects': effects,
        'referenced_by': [],
    }


def build_nodes(indexed_script, parsed_blocks):
    script_order = indexed_script.order
    label_index = {label: i for i, label in enumerate(script_order)}
    menu_findings = []
    unknown_log = set()
    nodes = {
        label: build_node(
            label,
            indexed_script.labels[label],
            tokens,
            label_index,
            script_order,
            menu_findings,
            unknown_log,
        )
        for label, tokens in parsed_blocks.items()
    }
    return nodes, menu_findings, sorted(unknown_log)
