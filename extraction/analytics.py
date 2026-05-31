"""
Analytics pass: compute aggregate metrics about the node/entity graph for the
public-facing UI and curatorial review.
"""

from collections import defaultdict


def _plaintext_bytes(node):
    return len(node.get('plaintext', '') or '')


def compute(nodes, entities, entity_counts):
    reachable_union = set()
    for entity in entities.values():
        reachable_union.update(entity.get('reachable_nodes') or ())

    dialogue_bytes_total = sum(_plaintext_bytes(n) for n in nodes.values())
    dialogue_bytes_reachable = sum(_plaintext_bytes(nodes[n])
                                   for n in reachable_union if n in nodes)

    shared = []
    for node_id, node in nodes.items():
        ref_count = len(node.get('referenced_by') or ())
        if ref_count > 1:
            sample = (node.get('plaintext') or '')[:80]
            shared.append({
                'node_id': node_id,
                'reference_count': ref_count,
                'plaintext_sample': sample,
            })
    shared.sort(key=lambda r: -r['reference_count'])

    region_buckets = defaultdict(lambda: {'entity_count': 0,
                                          'entity_count_by_type': defaultdict(int)})
    for entity in entities.values():
        region_key = entity.get('region') or '(unassigned)'
        bucket = region_buckets[region_key]
        bucket['entity_count'] += 1
        bucket['entity_count_by_type'][entity['type']] += 1
    regions_out = []
    for name in sorted(region_buckets.keys()):
        bucket = region_buckets[name]
        regions_out.append({
            'region': name,
            'entity_count': bucket['entity_count'],
            'entity_count_by_type': dict(bucket['entity_count_by_type']),
        })

    volumes = []
    for ent_id, entity in entities.items():
        reach = entity.get('reachable_nodes') or ()
        bytes_ = sum(_plaintext_bytes(nodes[n]) for n in reach if n in nodes)
        volumes.append({
            'entity': ent_id,
            'label': entity.get('label', ''),
            'reachable_node_count': len(reach),
            'reachable_byte_count': bytes_,
        })
    volumes.sort(key=lambda v: -v['reachable_byte_count'])

    return {
        'totals': {
            'nodes': len(nodes),
            'reachable_nodes': len(reachable_union),
            'unreachable_nodes': len(nodes) - len(reachable_union),
            'entities_by_type': dict(entity_counts),
            'dialogue_bytes_total': dialogue_bytes_total,
            'dialogue_bytes_reachable': dialogue_bytes_reachable,
        },
        'shared_infrastructure': shared,
        'regions': regions_out,
        'entity_dialogue_volume': volumes,
    }
