#!/usr/bin/env python3
"""
Generate SOMAFRACTAL MEMORY 3D Coordinate Visualization
Deterministic fractal coordinate space from hash-derived seeds.
"""

import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

OUTDIR = Path(__file__).parent.parent / "docs" / "deployment" / "images"
OUTDIR.mkdir(parents=True, exist_ok=True)

def make_coordinate(seed: str) -> tuple[float, float, float]:
    """Generate a deterministic 3D fractal coordinate from a seed string."""
    h = hashlib.md5(seed.encode()).hexdigest()
    return (
        (int(h[0:8], 16) / 0xFFFFFFFF) * 2 - 1,
        (int(h[8:16], 16) / 0xFFFFFFFF) * 2 - 1,
        (int(h[16:24], 16) / 0xFFFFFFFF) * 2 - 1,
    )

# Memory layer seeds
seeds = [
    ('L1 Episodic: conv-001',    'somafractal:memory:l1:conversation:2026-05-26'),
    ('L2 Semantic: graph-alpha', 'somafractal:memory:l2:graph:episodic'),
    ('L3 Procedural: skill-007', 'somafractal:memory:l3:procedural:code-gen'),
    ('Sleep Consolidation',      'somabrain:sleep:consolidation:delta'),
    ('Cognitive State',          'somabrain:neuromodulator:dopamine:0.87'),
    ('Agent Workspace',          'somaagent:workspace:agentzero:session:001'),
    ('Memory Retrieval',         'somafractal:memory:retrieve:attention:0.72'),
    ('Emotional Context',        'somafractal:memory:emotional:context:joy'),
]

coords = [(label, make_coordinate(seed)) for label, seed in seeds]

fig = plt.figure(figsize=(14, 10), facecolor='#0a0a0a')
fig.suptitle('SOMAFRACTAL MEMORY — 3D Coordinate Space', fontsize=18, fontweight='bold',
             color='#e8e4dc', y=0.98)
fig.text(0.5, 0.93, 'Deterministic Fractal Coordinates | MD5-Hash Derived Memory Loci',
         ha='center', fontsize=11, color='#6b6b6b')

# 3D Scatter plot
ax = fig.add_subplot(121, projection='3d')
ax.set_facecolor('#0a0a0a')

xs, ys, zs, labels, colors_list = [], [], [], [], []
color_map = ['#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#14b8a6', '#e11d48', '#f97316']

for i, (label, (x, y, z)) in enumerate(coords):
    xs.append(x)
    ys.append(y)
    zs.append(z)
    labels.append(label)
    colors_list.append(color_map[i % len(color_map)])

scatter = ax.scatter(xs, ys, zs, c=colors_list, s=200, edgecolors='#e8e4dc', linewidths=1.5, depthshade=True)

# Draw connections between related memory nodes
for i in range(len(coords) - 1):
    ax.plot([xs[i], xs[i+1]], [ys[i], ys[i+1]], [zs[i], zs[i+1]],
            color='#2a2a2a', linestyle='--', linewidth=1, alpha=0.6)

# Labels
for i, label in enumerate(labels):
    ax.text(xs[i], ys[i], zs[i] + 0.08, label.split(':')[0], color='#ffffff', fontsize=8)

ax.set_xlabel('X (Hash[0:8])', color='#6b6b6b', fontsize=9)
ax.set_ylabel('Y (Hash[8:16])', color='#6b6b6b', fontsize=9)
ax.set_zlabel('Z (Hash[16:24])', color='#6b6b6b', fontsize=9)
ax.tick_params(colors='#6b6b6b', labelsize=7)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_zlim(-1, 1)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor('#2a2a2a')
ax.yaxis.pane.set_edgecolor('#2a2a2a')
ax.zaxis.pane.set_edgecolor('#2a2a2a')
ax.grid(True, color='#2a2a2a', linestyle='--', linewidth=0.5)
ax.set_title('Memory Loci in 3D Fractal Space', color='#e8e4dc', fontsize=12, pad=10)

# Coordinate table
ax2 = fig.add_subplot(122)
ax2.set_facecolor('#0a0a0a')
ax2.axis('off')
table_data = []
for label, (x, y, z) in coords:
    short = label.split(':')[0]
    table_data.append([short, f"{x:+.6f}", f"{y:+.6f}", f"{z:+.6f}"])

table = ax2.table(cellText=table_data,
                  colLabels=['Memory Node', 'X', 'Y', 'Z'],
                  cellLoc='center',
                  loc='center',
                  colColours=['#1e1e1e']*4)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.8)

for i, key in enumerate(table.get_celld().keys()):
    cell = table.get_celld()[key]
    cell.set_text_props(color='#a1a1a1')
    cell.set_edgecolor('#2a2a2a')
    if key[0] == 0:
        cell.set_text_props(color='#e8e4dc', fontweight='bold')
        cell.set_facecolor('#141414')
    else:
        cell.set_facecolor('#0a0a0a')

ax2.set_title('Deterministic Coordinate Table', color='#e8e4dc', fontsize=12, pad=10)

plt.tight_layout(rect=[0, 0, 1, 0.92])
outfile = OUTDIR / "somafractal_memory_3d_space.png"
plt.savefig(outfile, dpi=150, facecolor='#0a0a0a', edgecolor='none', bbox_inches='tight')
logger.info('SOMAFRACTAL Memory Space: %s', outfile)
