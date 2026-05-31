#!/usr/bin/env python
"""
Render a single entity's reachable subgraph as an interactive HTML file using
vis-network (CDN — no install required, opens in any browser).

Usage:
  python tools/visualize_entity.py <entity_id> [<entity_id> ...]

Output: writes one HTML file per entity into tools/viz/<entity_id>.html.
"""

import argparse
import json
import os
import sys


CD = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
EXTRACTED = os.path.join(CD, 'resources', 'dialogue', 'extracted')
NODES_JSON = os.path.join(EXTRACTED, 'nodes.json')
ENTITIES_DIR = os.path.join(EXTRACTED, 'entities')
VIZ_DIR = os.path.join(CD, 'tools', 'viz')


EDGE_STYLES = {
    'unconditional': {'color': '#888', 'dashes': False},
    'flag_test':     {'color': '#3a7', 'dashes': False},
    'menu_option':   {'color': '#e63', 'dashes': False},
    'case_branch':   {'color': '#a4c', 'dashes': False},
    'function_call': {'color': '#36c', 'dashes': [4, 4]},
}


def _load_nodes():
    with open(NODES_JSON, encoding='utf-8') as f:
        return json.load(f)


def _load_entity(entity_id):
    path = os.path.join(ENTITIES_DIR, f'{entity_id}.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'no entity at {path}')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _truncate(text, max_len=80):
    text = text.replace('\n', ' / ')
    return text if len(text) <= max_len else text[:max_len] + '…'


def _node_label(node_id, plaintext):
    excerpt = _truncate(plaintext or '', 32) or '(no text)'
    return f'{node_id}\\n{excerpt}'


def _node_title(node_id, node):
    parts = [f'<b>{node_id}</b>']
    if node.get('plaintext'):
        parts.append('<i>' + _truncate(node['plaintext'], 200) + '</i>')
    if node.get('effects'):
        parts.append(f'effects: {len(node["effects"])}')
    if node.get('referenced_by'):
        parts.append(f'referenced by {len(node["referenced_by"])} entity(ies)')
    return '<br>'.join(parts)


def _edge_label(edge):
    t = edge.get('type', '')
    if t == 'flag_test':
        flag = edge.get('flag_label') or edge.get('flag') or '?'
        return f'if {edge.get("polarity", "?")} {flag}'
    if t == 'menu_option':
        return f'"{edge.get("label", "")}"'
    if t == 'case_branch':
        return f'{edge.get("discriminant", "?")}={edge.get("value", "?")}' + \
               (' (call)' if edge.get('kind') == 'call' else '')
    if t == 'function_call':
        return 'call'
    return ''


def build_graph(entity, nodes):
    reachable = set(entity.get('reachable_nodes') or [])
    entry_ids = {ep['node_id'] for ep in entity.get('entry_points', [])
                 if ep.get('node_id')}

    vis_nodes = []
    for node_id in sorted(reachable):
        if node_id not in nodes:
            continue
        node = nodes[node_id]
        is_entry = node_id in entry_ids
        vis_nodes.append({
            'id': node_id,
            'label': _node_label(node_id, node.get('plaintext', '')),
            'title': _node_title(node_id, node),
            'shape': 'box',
            'color': {
                'background': '#fef3c7' if is_entry else '#fff',
                'border': '#e63' if is_entry else '#888',
            },
            'borderWidth': 3 if is_entry else 1,
            'font': {'size': 11, 'face': 'monospace'},
        })

    vis_edges = []
    for node_id in reachable:
        if node_id not in nodes:
            continue
        node = nodes[node_id]
        for i, edge in enumerate(node.get('edges', [])):
            etype = edge.get('type')
            style = EDGE_STYLES.get(etype, {'color': '#bbb', 'dashes': False})
            for field in ('target', 'fallthrough'):
                tgt = edge.get(field)
                if not tgt or tgt not in reachable:
                    continue
                is_fall = (field == 'fallthrough')
                vis_edges.append({
                    'from': node_id,
                    'to': tgt,
                    'label': _edge_label(edge) + (' (fallthrough)' if is_fall else ''),
                    'arrows': 'to',
                    'color': style['color'],
                    'dashes': True if is_fall else style['dashes'],
                    'font': {'size': 9, 'align': 'middle'},
                    'smooth': {'type': 'dynamic'},
                })
    return vis_nodes, vis_edges


def emit_html(entity, vis_nodes, vis_edges, out_path):
    legend_html = ''.join(
        f'<span style="display:inline-block;margin-right:1em;">'
        f'<span style="display:inline-block;width:24px;height:0;border-top:3px '
        f'{"dashed" if s.get("dashes") else "solid"} {s["color"]};vertical-align:middle;"></span> '
        f'{etype}</span>'
        for etype, s in EDGE_STYLES.items()
    )

    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{entity['id']} — {entity.get('label', '')}</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1em; }}
  h1 {{ font-size: 1.2em; margin: 0 0 0.25em; }}
  .meta {{ color: #555; font-size: 0.9em; margin-bottom: 0.5em; }}
  .legend {{ font-size: 0.85em; margin-bottom: 0.5em; }}
  .entry-swatch {{ display: inline-block; width: 16px; height: 12px;
                   background: #fef3c7; border: 2px solid #e63;
                   vertical-align: middle; }}
  #graph {{ width: 100%; height: calc(100vh - 140px); border: 1px solid #ddd; }}
</style>
</head><body>
<h1>{entity['id']} — {entity.get('label') or '(unlabeled)'} <span style="font-weight:normal;color:#888;">[{entity['type']}]</span></h1>
<div class="meta">
  region: {entity.get('region', '(none)')}
  &nbsp;·&nbsp; reachable nodes: {len(vis_nodes)}
  &nbsp;·&nbsp; edges: {len(vis_edges)}
  &nbsp;·&nbsp; entry points: {len(entity.get('entry_points', []))}
</div>
<div class="legend">
  {legend_html}
  &nbsp;·&nbsp; <span class="entry-swatch"></span> entry point
</div>
<div id="graph"></div>
<script>
  const data = {{
    nodes: new vis.DataSet({json.dumps(vis_nodes)}),
    edges: new vis.DataSet({json.dumps(vis_edges)}),
  }};
  const options = {{
    layout: {{ improvedLayout: true }},
    physics: {{
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {{ gravitationalConstant: -80, springLength: 120 }},
      stabilization: {{ iterations: 200 }},
    }},
    interaction: {{ hover: true, tooltipDelay: 100 }},
  }};
  new vis.Network(document.getElementById('graph'), data, options);
</script>
</body></html>
"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entity_ids', nargs='+',
                        help='entity IDs to visualize (e.g. npc_0039)')
    args = parser.parse_args()

    os.makedirs(VIZ_DIR, exist_ok=True)
    nodes = _load_nodes()

    for eid in args.entity_ids:
        entity = _load_entity(eid)
        vis_nodes, vis_edges = build_graph(entity, nodes)
        out_path = os.path.join(VIZ_DIR, f'{eid}.html')
        emit_html(entity, vis_nodes, vis_edges, out_path)
        print(f'{eid}: {len(vis_nodes)} nodes, {len(vis_edges)} edges -> {out_path}')


if __name__ == '__main__':
    main()
