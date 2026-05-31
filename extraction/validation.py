"""
Validation pass: compute the errors and findings the spec defines.

Errors → non-zero exit. Findings → informational. Both shapes match the spec's
validation.json schema.
"""

from collections import defaultdict


_VALID_LABEL_KINDS = {'hex', 'npc'}
_VALID_EDGE_TYPES = {'unconditional', 'flag_test', 'menu_option',
                     'case_branch', 'function_call'}
_VALID_ENTITY_TYPES = {'npc', 'sign', 'door', 'present', 'photo_event'}
_VALID_VISIBILITY_CONDITIONS = {'always', 'flag_set', 'flag_cleared'}

_NODE_REQUIRED = {'id', 'label_kind', 'raw', 'plaintext', 'edges', 'effects',
                  'referenced_by'}
_ENTITY_REQUIRED = {'id', 'type', 'label', 'region', 'location', 'visibility',
                    'entry_points', 'reachable_nodes', 'properties'}


# ───── error checks ────────────────────────────────────────────────────────

def _find_unresolved_edges(nodes):
    out = []
    for node_id, node in nodes.items():
        for i, edge in enumerate(node.get('edges', [])):
            for field in ('target', 'fallthrough'):
                tgt = edge.get(field)
                if tgt and tgt not in nodes:
                    out.append({'node': node_id, 'edge_index': i, 'target': tgt})
    return out


def _find_unresolved_entry_points(entities, nodes):
    out = []
    for ent_id, entity in entities.items():
        for i, ep in enumerate(entity.get('entry_points', [])):
            tgt = ep.get('node_id')
            if tgt and tgt not in nodes:
                out.append({'entity': ent_id, 'entry_index': i, 'target': tgt})
    return out


def _missing_labels(addresses, nodes, address_to_label):
    """
    Raw hex addresses from addresses.txt whose canonical label (per the
    script-dumper's labeling) isn't in the node store.
    """
    missing = []
    for hex_addr in sorted(addresses):
        canonical = address_to_label.get(hex_addr) or f'L_{hex_addr}'
        if canonical not in nodes:
            missing.append(hex_addr)
    return missing


def _schema_violations(nodes, entities):
    issues = []
    for node_id, node in nodes.items():
        missing = _NODE_REQUIRED - set(node.keys())
        if missing:
            issues.append({'object_id': node_id,
                           'issue': f'missing node fields: {sorted(missing)}'})
        if node.get('label_kind') not in _VALID_LABEL_KINDS:
            issues.append({'object_id': node_id,
                           'issue': f'invalid label_kind: {node.get("label_kind")!r}'})
        for i, edge in enumerate(node.get('edges', [])):
            if edge.get('type') not in _VALID_EDGE_TYPES:
                issues.append({
                    'object_id': f'{node_id}.edges[{i}]',
                    'issue': f'invalid edge type: {edge.get("type")!r}',
                })
    for ent_id, entity in entities.items():
        missing = _ENTITY_REQUIRED - set(entity.keys())
        if missing:
            issues.append({'object_id': ent_id,
                           'issue': f'missing entity fields: {sorted(missing)}'})
        if entity.get('type') not in _VALID_ENTITY_TYPES:
            issues.append({'object_id': ent_id,
                           'issue': f'invalid type: {entity.get("type")!r}'})
        condition = entity.get('visibility', {}).get('condition')
        if condition not in _VALID_VISIBILITY_CONDITIONS:
            issues.append({'object_id': ent_id,
                           'issue': f'invalid visibility.condition: {condition!r}'})
    return issues


# ───── finding checks ──────────────────────────────────────────────────────

def _entities_without_entry_points(entities):
    """
    Per spec: navigation-only doors and photo events legitimately have no entry
    points and are excluded. The finding flags only entities that surprise us.
    """
    out = []
    for ent_id, entity in entities.items():
        if entity.get('entry_points'):
            continue
        etype = entity.get('type')
        if etype == 'photo_event':
            continue
        if etype == 'door' and entity.get('properties', {}).get('kind') == 'navigation':
            continue
        out.append({'entity': ent_id, 'type': etype})
    return out


def _duplicate_plaintext(nodes):
    by_text = defaultdict(list)
    for node_id, node in nodes.items():
        text = node.get('plaintext', '')
        if text:
            by_text[text].append(node_id)
    out = []
    for text, ids in by_text.items():
        if len(ids) > 1:
            sample = text[:80] + ('…' if len(text) > 80 else '')
            out.append({'ids': sorted(ids), 'sample': sample})
    return sorted(out, key=lambda r: r['ids'][0])


def _addresses_txt_diagnostic(missing):
    """
    Diagnostic breakdown of missing addresses — bucket by address range so the
    user can see whether the gap is a stale addresses.txt (likely out-of-range)
    or a real extraction bug (in-range addresses we missed).
    """
    in_range = []
    out_of_range = []
    for hex_addr in missing:
        try:
            addr = int(hex_addr, 16)
            if 0xC50000 <= addr <= 0xC9FFFF:
                in_range.append(hex_addr)
            else:
                out_of_range.append(hex_addr)
        except ValueError:
            in_range.append(hex_addr)
    return {
        'in_range_count': len(in_range),
        'in_range_sample': in_range[:10],
        'out_of_range_count': len(out_of_range),
        'out_of_range_sample': out_of_range[:10],
    }


# ───── orchestration ───────────────────────────────────────────────────────

def validate(nodes, entities, addresses, address_to_label,
             entity_counts, entity_findings,
             menu_findings, unknown_placeholders, unreachable_nodes,
             provenance_mismatches):
    edge_count = sum(len(n.get('edges', [])) for n in nodes.values())

    missing_from_addresses = _missing_labels(addresses, nodes, address_to_label)
    addresses_diag = _addresses_txt_diagnostic(missing_from_addresses)

    return {
        'summary': {
            'node_count': len(nodes),
            'edge_count': edge_count,
            'entity_count_total': sum(entity_counts.values()),
            'entity_count_by_type': dict(entity_counts),
        },
        'errors': {
            'unresolved_edge_targets': _find_unresolved_edges(nodes),
            'unresolved_entity_entry_points': _find_unresolved_entry_points(entities, nodes),
            'missing_labels_from_addresses_txt': missing_from_addresses,
            'provenance_inverse_mismatch': list(provenance_mismatches),
            'schema_violations': _schema_violations(nodes, entities),
        },
        'findings': {
            'unreachable_nodes': sorted(unreachable_nodes),
            'entities_without_entry_points': _entities_without_entry_points(entities),
            'duplicate_plaintext': _duplicate_plaintext(nodes),
            'unknown_placeholders': sorted(unknown_placeholders),
            'unrecognized_menus': list(menu_findings),
            'door_coord_units_unverified': entity_findings.get('door_coord_units_unverified', []),
            'presents_missing_item': entity_findings.get('presents_missing_item', []),
            'photo_coords_unverified': entity_findings.get('photo_coords_unverified', []),
            'addresses_txt_diagnostic': addresses_diag,
        },
    }


def has_errors(validation):
    return any(v for v in validation['errors'].values())
