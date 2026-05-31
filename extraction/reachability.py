"""
Graph computation: per-entity reachability (transitive closure from entry
points) and the inverse-provenance map (which entities can reach each node).
"""

from collections import deque


def _entry_targets(entity):
    return [ep['node_id'] for ep in entity.get('entry_points', []) if ep.get('node_id')]


def _outgoing_targets(node):
    """Yield every node ID this node's edges reach."""
    for edge in node.get('edges', []):
        etype = edge.get('type')
        if etype == 'unconditional':
            yield from _maybe(edge.get('target'))
        elif etype == 'flag_test':
            yield from _maybe(edge.get('target'))
            yield from _maybe(edge.get('fallthrough'))
        elif etype == 'menu_option':
            yield from _maybe(edge.get('target'))
        elif etype == 'case_branch':
            yield from _maybe(edge.get('target'))
        elif etype == 'function_call':
            yield from _maybe(edge.get('target'))


def _maybe(value):
    if value:
        yield value


def reachable_from(start_nodes, nodes):
    """BFS over the graph from a list of start node IDs."""
    visited = set()
    queue = deque()
    for s in start_nodes:
        if s in nodes and s not in visited:
            visited.add(s)
            queue.append(s)
    while queue:
        current = queue.popleft()
        node = nodes[current]
        for target in _outgoing_targets(node):
            if target in nodes and target not in visited:
                visited.add(target)
                queue.append(target)
    return visited


def compute_reachability(nodes, entities):
    """Populate `entity['reachable_nodes']` for each entity."""
    for entity in entities.values():
        starts = _entry_targets(entity)
        reachable = reachable_from(starts, nodes)
        entity['reachable_nodes'] = sorted(reachable)
    return entities


def compute_provenance(nodes, entities):
    """Populate `node['referenced_by']` by inverting `reachable_nodes`."""
    by_node = {}
    for ent_id, entity in entities.items():
        for node_id in entity.get('reachable_nodes', ()):
            by_node.setdefault(node_id, set()).add(ent_id)
    for node_id, node in nodes.items():
        node['referenced_by'] = sorted(by_node.get(node_id, ()))
    return nodes


def verify_provenance_inverse(nodes, entities):
    """
    Confirm: for every (entity E, node N) where N ∈ E.reachable_nodes,
    E ∈ N.referenced_by — and vice versa. Returns a list of mismatch records.
    """
    forward = set()
    for ent_id, entity in entities.items():
        for node_id in entity.get('reachable_nodes', ()):
            forward.add((node_id, ent_id))
    backward = set()
    for node_id, node in nodes.items():
        for ent_id in node.get('referenced_by', ()):
            backward.add((node_id, ent_id))
    mismatches = []
    for pair in forward - backward:
        mismatches.append({'node': pair[0], 'entity': pair[1], 'issue': 'reachable_not_in_referenced_by'})
    for pair in backward - forward:
        mismatches.append({'node': pair[0], 'entity': pair[1], 'issue': 'referenced_by_not_in_reachable'})
    return mismatches
