import sys

from collections import Counter

from extraction import nodes as nodes_mod
from extraction import entities as entities_mod
from extraction import validation as validation_mod
from extraction import analytics as analytics_mod
from extraction import output as output_mod
from extraction import opcodes, reachability, script_index, sources


def load_sources():
    with open(sources.SCRIPT_DUMPER_OUTPUT, encoding='utf-8') as f:
        raw_script = f.read()
    addresses = script_index.load_addresses_txt(sources.ADDRESSES_TXT)
    return {
        'raw_script': raw_script,
        'addresses': addresses,
    }


def index_script(raw_script):
    return script_index.parse_script(raw_script)


def parse_blocks(indexed_script):
    return {label: opcodes.parse_block(lines)
            for label, lines in indexed_script.labels.items()}


def verify_round_trip(indexed_script):
    mismatches = []
    for label, lines in indexed_script.labels.items():
        for i, line in enumerate(lines):
            tokens = opcodes.tokenize_line(line)
            if opcodes.reconstruct_line(tokens) != line:
                mismatches.append((label, i, line))
    return mismatches


def summarize_opcodes(parsed):
    counter = Counter()
    for tokens in parsed.values():
        for t in tokens:
            if isinstance(t, opcodes.Opcode):
                counter[t.name] += 1
    return counter


def build_nodes(indexed_script, parsed_blocks):
    return nodes_mod.build_nodes(indexed_script, parsed_blocks)


def summarize_edges(nodes):
    counts = Counter()
    polarity_counts = Counter()
    kind_counts = Counter()
    for node in nodes.values():
        for edge in node['edges']:
            counts[edge['type']] += 1
            if edge['type'] == 'flag_test':
                polarity_counts[edge['polarity']] += 1
            if edge['type'] == 'case_branch':
                kind_counts[edge['kind']] += 1
    return counts, polarity_counts, kind_counts


def summarize_effects(nodes):
    counts = Counter()
    other_raws = Counter()
    for node in nodes.values():
        for eff in node['effects']:
            counts[eff['type']] += 1
            if eff['type'] == 'other':
                head = eff['raw'].split(' ', 1)[0].lstrip('[').rstrip(']')
                other_raws[head] += 1
    return counts, other_raws


def build_entities(loaded_sources, nodes, indexed_script):
    entities, counts, entity_findings = entities_mod.build_entities(
        indexed_script.address_to_label)
    entity_index = entities_mod.build_entity_index(entities)
    return entities, entity_index, counts, entity_findings


def compute_reachability(nodes, entities):
    reachability.compute_reachability(nodes, entities)
    return nodes, entities


def compute_provenance(nodes, entities):
    reachability.compute_provenance(nodes, entities)
    return nodes


def run_validation(nodes, entities, addresses, address_to_label,
                   entity_counts, entity_findings,
                   menu_findings, unknown_placeholders,
                   unreachable_nodes, provenance_mismatches):
    return validation_mod.validate(
        nodes, entities, addresses, address_to_label,
        entity_counts, entity_findings,
        menu_findings, unknown_placeholders, unreachable_nodes,
        provenance_mismatches,
    )


def run_analytics(nodes, entities, entity_counts):
    return analytics_mod.compute(nodes, entities, entity_counts)


def emit_outputs(nodes, entities, entity_index, validation, analytics):
    output_mod.emit_all(nodes, entities, entity_index, validation, analytics)


def has_errors(validation):
    return validation_mod.has_errors(validation)


def print_summary(validation):
    s = validation['summary']
    error_count = sum(len(v) for v in validation['errors'].values())
    finding_count = sum(len(v) for v in validation['findings'].values())
    print(f"nodes={s['node_count']} entities={s['entity_count_total']} "
          f"edges={s['edge_count']} errors={error_count} findings={finding_count}")


def main():
    loaded = load_sources()
    raw_script = loaded.get('raw_script', '')
    indexed = index_script(raw_script)

    counts = script_index.summarize(indexed)
    missing = script_index.cross_check_addresses(indexed, loaded['addresses'])
    print(f"indexed: hex={counts['hex']} npc={counts['npc']} total={counts['total']} "
          f"missing_from_addresses_txt={len(missing)}")

    parsed = parse_blocks(indexed)
    mismatches = verify_round_trip(indexed)
    opcode_counts = summarize_opcodes(parsed)
    total_opcodes = sum(opcode_counts.values())
    distinct_opcodes = len(opcode_counts)
    top = ', '.join(f"{name}={count}" for name, count in opcode_counts.most_common(10))
    print(f"parsed: opcodes={total_opcodes} distinct={distinct_opcodes} "
          f"round_trip_mismatches={len(mismatches)}")
    print(f"top opcodes: {top}")

    nodes, menu_findings, unknown_placeholders = build_nodes(indexed, parsed)
    edge_counts, polarity_counts, kind_counts = summarize_edges(nodes)
    total_edges = sum(edge_counts.values())
    edge_breakdown = ' '.join(f"{k}={v}" for k, v in sorted(edge_counts.items()))
    print(f"edges: total={total_edges} {edge_breakdown}")
    if polarity_counts:
        print(f"  flag_test polarity: " + ' '.join(f"{k}={v}" for k, v in polarity_counts.items()))
    if kind_counts:
        print(f"  case_branch kind: " + ' '.join(f"{k}={v}" for k, v in kind_counts.items()))
    menu_reason_counts = Counter(f['reason'] for f in menu_findings)
    print(f"menus: unrecognized={len(menu_findings)} by_reason={dict(menu_reason_counts)}")
    effect_counts, other_raws = summarize_effects(nodes)
    total_effects = sum(effect_counts.values())
    effect_breakdown = ' '.join(f"{k}={v}" for k, v in sorted(effect_counts.items()))
    print(f"effects: total={total_effects} {effect_breakdown}")
    if other_raws:
        top_other = ', '.join(f"{k}={v}" for k, v in other_raws.most_common(10))
        print(f"  top 'other' opcodes: {top_other}")
    plaintext_total_bytes = sum(len(n['plaintext']) for n in nodes.values())
    nonempty_plaintext = sum(1 for n in nodes.values() if n['plaintext'])
    print(f"plaintext: nodes_with_text={nonempty_plaintext}/{len(nodes)} "
          f"total_bytes={plaintext_total_bytes} unknown_placeholders={len(unknown_placeholders)}")
    entities, entity_index, entity_counts, entity_findings = build_entities(loaded, nodes, indexed)
    print(f"entities: total={sum(entity_counts.values())} {entity_counts}")
    nodes, entities = compute_reachability(nodes, entities)
    nodes = compute_provenance(nodes, entities)

    reachable_union = set()
    reach_counts = []
    for e in entities.values():
        reach_counts.append(len(e['reachable_nodes']))
        reachable_union.update(e['reachable_nodes'])
    unreachable = [n for n in nodes if not nodes[n]['referenced_by']]
    avg_reach = sum(reach_counts) / max(len(reach_counts), 1)
    max_reach = max(reach_counts) if reach_counts else 0
    print(f"reachability: union={len(reachable_union)}/{len(nodes)} "
          f"unreachable={len(unreachable)} avg_per_entity={avg_reach:.1f} "
          f"max_per_entity={max_reach}")

    provenance_mismatches = reachability.verify_provenance_inverse(nodes, entities)
    print(f"provenance: inverse_mismatches={len(provenance_mismatches)}")

    validation = run_validation(nodes, entities, loaded['addresses'],
                                indexed.address_to_label,
                                entity_counts, entity_findings,
                                menu_findings, unknown_placeholders,
                                unreachable, provenance_mismatches)
    analytics = run_analytics(nodes, entities, entity_counts)
    emit_outputs(nodes, entities, entity_index, validation, analytics)
    print_summary(validation)
    return 1 if has_errors(validation) else 0


if __name__ == '__main__':
    sys.exit(main())
