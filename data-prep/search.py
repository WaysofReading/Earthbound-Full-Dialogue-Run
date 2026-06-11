"""
Search index generation.

The MiniSearch indices are built by web/scripts/build-search.mjs (Node) so the
serialized format matches the client's MiniSearch version exactly. This module
just shells out to it; prep.py calls it after nodes/all.json exists. If Node or
the web deps aren't present (e.g. a data-only run), it warns and skips — the
deploy workflow always runs it after `npm ci`.
"""

import os
import shutil
import subprocess

import common


def build(out_dir, report):
    script = os.path.join(common.REPO_ROOT, 'web', 'scripts', 'build-search.mjs')
    if not os.path.exists(script):
        report.warn('web/scripts/build-search.mjs missing — skipping search index')
        return
    if shutil.which('node') is None:
        report.warn('node not on PATH — skipping search index (run in CI after npm ci)')
        return
    try:
        subprocess.run(
            ['node', script, '--out', os.path.abspath(out_dir)],
            cwd=os.path.join(common.REPO_ROOT, 'web'),
            check=True,
        )
        report.log('  search: built entity + full-text indices')
    except subprocess.CalledProcessError as e:
        report.warn(f'build-search.mjs failed ({e}); search indices not built')
