"""
Article figures, generated from real temporal-extraction output.

Renders the four figures referenced in the article:

  1. narrative_chart.png       — XKCD-style character flow chart
  2. topology_snapshots.png    — Graph topology at 25/50/75/100 % checkpoints
  3. relationship_heatmap.png  — Top-N relation types × chapter bins
  4. cast_arrival_strip.png    — Entity first-appearance timeline

Inputs are JSON files produced by ``temporal_extraction.py``. The script
auto-derives narrative groupings from the graph itself, so it works on any
book. For the three demo works (iliad / crime / dune) you can pass
``--preset <work_key>`` to use the hand-curated groupings shipped under
``presets/`` — these match the exact look of the figures in the article.

CLI
---

    # Single work
    python figures.py output/mybook_temporal_kg.json -o output/visualizations/

    # Multiple works (renders the multi-panel article figures)
    python figures.py output/iliad_temporal_kg.json \\
                      output/crime_temporal_kg.json \\
                      output/dune_temporal_kg.json \\
                      -o output/visualizations/

    # Use the curated preset for the narrative chart
    python figures.py output/iliad_temporal_kg.json --preset iliad -o output/

The --preset flag only affects the narrative chart; topology, heatmap, and
cast-arrival figures always derive from the real graph.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from temporal_analysis import build_cumulative_graph
from temporal_visualization import (
    ENTITY_TYPE_COLORS,
    WORK_COLORS,
    get_entity_color,
    get_work_color,
)

try:
    from presets import has_preset, get_preset
except ImportError:
    def has_preset(_work_key: str) -> bool:  # type: ignore[misc]
        return False

    def get_preset(_work_key: str) -> dict:  # type: ignore[misc]
        raise KeyError("presets package not available")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_temporal_json(path: str) -> dict:
    """Load a temporal_extraction JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_work_label(data: dict) -> str:
    """Best-effort human-readable name for a work."""
    return data.get("metadata", {}).get("work_name") or data["metadata"]["work_key"].title()


def get_work_color_safe(work_key: str) -> str:
    """Color for a work — falls back to a neutral teal for non-presets."""
    return WORK_COLORS.get(work_key, "#3D5A80")


def num_chapters(data: dict) -> int:
    return len(data.get("chapters", [])) or (
        max((e["first_appearance"] for e in data["entities"]), default=0) + 1
    )


# ---------------------------------------------------------------------------
# Auto-derive narrative groupings (used when --preset is not supplied)
# ---------------------------------------------------------------------------

def _top_characters_by_degree(data: dict, top_n: int = 10) -> list[tuple[str, str]]:
    """
    Pick the top-N most-connected character-like entities.

    Looks at entity types whose names suggest "people": HERO, CHARACTER,
    PROTAGONIST, DEITY, MORTAL. Falls back to all types if nothing matches.
    """
    person_labels = {
        "HERO", "CHARACTER", "PROTAGONIST", "DEITY", "MORTAL",
    }
    name_to_label = {e["name"]: e["label"] for e in data["entities"]}

    degree = Counter()
    for r in data["relations"]:
        degree[r["source_name"]] += 1
        degree[r["target_name"]] += 1

    person_candidates = [
        (n, c) for n, c in degree.most_common()
        if name_to_label.get(n) in person_labels
    ]
    if len(person_candidates) < 4:
        person_candidates = list(degree.most_common())

    palette = [
        "#DC143C", "#1E3A5F", "#2A9D8F", "#E9C46A",
        "#F4A261", "#8B0000", "#4682B4", "#9370DB",
        "#556B2F", "#9932CC",
    ]
    chosen = person_candidates[:top_n]
    return [(name, palette[i % len(palette)]) for i, (name, _) in enumerate(chosen)]


def _auto_derive_groups(data: dict, characters: list[tuple[str, str]]) -> dict:
    """
    Derive scene-clusters from the temporal graph.

    For each chapter, treat the subgraph of relations that *first appear* in
    that chapter as a "co-presence" indicator. Connected components on the
    tracked-character induced subgraph become groups; isolated characters
    form their own singletons.
    """
    char_set = {c[0] for c in characters}
    n_chapters = num_chapters(data)
    if n_chapters == 0:
        return {0.0: [char_set]}

    # Bucket relations by chapter of first appearance
    relations_by_chapter: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for r in data["relations"]:
        if r["source_name"] in char_set and r["target_name"] in char_set:
            relations_by_chapter[r["first_appearance"]].append(
                (r["source_name"], r["target_name"])
            )

    # Last-known group state, so a group "sticks" until contradicted
    groups_at_chapter: dict[float, list[set[str]]] = {}
    last_groups: list[set[str]] = [{c} for c in char_set]
    sample_every = max(1, n_chapters // 12)  # ~12 sample points across the work

    for chapter in range(n_chapters):
        # Update groups using all relations seen up to and including this chapter
        edges = [(u, v) for ch in range(chapter + 1) for (u, v) in relations_by_chapter.get(ch, [])]
        if edges:
            g = nx.Graph()
            g.add_nodes_from(char_set)
            g.add_edges_from(edges)
            components = [set(c) for c in nx.connected_components(g)]
            last_groups = components

        if chapter % sample_every == 0 or chapter == n_chapters - 1:
            pct = chapter / max(n_chapters - 1, 1)
            groups_at_chapter[pct] = [set(g) for g in last_groups]

    if 0.0 not in groups_at_chapter:
        groups_at_chapter[0.0] = [{c} for c in char_set]

    return groups_at_chapter


# ---------------------------------------------------------------------------
# FIGURE 1: Narrative chart
# ---------------------------------------------------------------------------

def _compute_narrative_positions(
    characters: list[tuple[str, str]],
    groups: dict,
    num_steps: int = 300,
) -> dict[str, np.ndarray]:
    """
    Compute y-positions for each character at each x-step.

    Characters in the same group converge to a common centroid; characters in
    different groups separate. Final positions are smoothed so transitions
    aren't jagged.
    """
    char_names = [c[0] for c in characters]
    base_spread = 1.5
    initial_y = {name: i * base_spread for i, name in enumerate(char_names)}
    positions = {name: np.zeros(num_steps) for name in char_names}

    checkpoints = sorted(groups.keys())
    if not checkpoints:
        for name in char_names:
            positions[name][:] = initial_y[name]
        return positions

    intra_spread = base_spread * 0.35
    group_spread = base_spread * 2.0

    for step in range(num_steps):
        pct = step / max(num_steps - 1, 1)

        # Snap to nearest checkpoint
        cp = min(checkpoints, key=lambda c: abs(c - pct))
        current_groups = groups[cp]

        char_group: dict[str, int] = {}
        for gi, group in enumerate(current_groups):
            for name in group:
                if name in char_names:
                    char_group[name] = gi

        # Group → ordered members
        group_members: dict[int, list[str]] = defaultdict(list)
        for name in char_names:
            gi = char_group.get(name, -1)
            if gi >= 0:
                group_members[gi].append(name)

        y_cursor = 0.0
        target: dict[str, float] = {}
        for gi in sorted(group_members):
            members = group_members[gi]
            for j, name in enumerate(members):
                target[name] = y_cursor + j * intra_spread
            y_cursor += len(members) * intra_spread + group_spread

        for name in char_names:
            if name in target:
                positions[name][step] = target[name]
            elif step > 0:
                positions[name][step] = positions[name][step - 1]
            else:
                positions[name][step] = initial_y[name]

    # Gaussian smoothing for a cleaner curve
    try:
        from scipy.ndimage import gaussian_filter1d
        for name in char_names:
            positions[name] = gaussian_filter1d(positions[name], sigma=8)
    except ImportError:
        # Fallback: simple moving average
        window = 16
        kernel = np.ones(window) / window
        for name in char_names:
            positions[name] = np.convolve(positions[name], kernel, mode="same")

    return positions


def figure_narrative_chart(
    works: list[dict],
    save_path: str,
    preset_keys: dict[str, str] | None = None,
) -> None:
    """
    XKCD-style character-flow chart, one panel per work, stacked vertically.

    Args:
        works: List of temporal-extraction dicts.
        save_path: Output PNG path.
        preset_keys: Optional dict mapping a work's filename-derived key to a
            preset key (e.g. {"iliad_temporal_kg": "iliad"}). When set, the
            preset's curated characters/groups/events are used.
    """
    preset_keys = preset_keys or {}
    n = len(works)
    fig, axes = plt.subplots(n, 1, figsize=(24, 7.3 * n))
    if n == 1:
        axes = [axes]

    for ax, data in zip(axes, works):
        work_key = data["metadata"]["work_key"]
        work_label = get_work_label(data)
        work_color = get_work_color_safe(work_key)
        preset_key = preset_keys.get(work_key)

        if preset_key and has_preset(preset_key):
            preset = get_preset(preset_key)
            characters = preset["characters"]
            groups = preset["groups"]
            events = preset["events"]
        else:
            characters = _top_characters_by_degree(data, top_n=10)
            groups = _auto_derive_groups(data, characters)
            events = {}

        if not characters:
            ax.text(0.5, 0.5, "No characters detected", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, alpha=0.6)
            ax.axis("off")
            continue

        num_steps = 300
        positions = _compute_narrative_positions(characters, groups, num_steps)
        x = np.linspace(0, 1, num_steps)

        for name, color in characters:
            y = positions[name]
            ax.plot(x, y, color=color, linewidth=3.2, alpha=0.9, solid_capstyle="round")

        for name, color in characters:
            y_start = positions[name][0]
            y_end = positions[name][-1]
            ax.text(-0.01, y_start, name, fontsize=9, fontweight="bold",
                    color=color, ha="right", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                              edgecolor="none", alpha=0.8))
            ax.text(1.01, y_end, name, fontsize=8,
                    color=color, ha="left", va="center", alpha=0.8,
                    bbox=dict(boxstyle="round,pad=0.1", facecolor="white",
                              edgecolor="none", alpha=0.7))

        for cp in sorted(groups.keys()):
            ax.axvline(cp, color="#CCCCCC", linewidth=0.5, linestyle=":", alpha=0.5)

        all_y = np.concatenate(list(positions.values()))
        y_min, y_max = all_y.min(), all_y.max()
        annotation_y = y_min - (y_max - y_min) * 0.08

        for pct, label in events.items():
            ax.text(pct, annotation_y, label, fontsize=7, ha="center",
                    va="top", style="italic", alpha=0.6, color="#333333")
            ax.plot([pct, pct], [annotation_y + (y_max - y_min) * 0.02, y_min],
                    color="#AAAAAA", linewidth=0.5, alpha=0.4)

        ax.set_title(work_label, fontsize=14, fontweight="bold",
                     color=work_color, loc="left", pad=12)
        ax.set_xlim(-0.22, 1.15)
        ax.set_ylim(annotation_y - (y_max - y_min) * 0.05,
                    y_max + (y_max - y_min) * 0.08)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.axhline(y_min - (y_max - y_min) * 0.03, color="#CCCCCC",
                   linewidth=0.8, xmin=0.15, xmax=0.88)

    plt.suptitle("Narrative Charts — Character Paths Through the Story",
                 fontsize=18, fontweight="bold", y=0.995)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ---------------------------------------------------------------------------
# FIGURE 2: Topology snapshots
# ---------------------------------------------------------------------------

def figure_topology_snapshots(
    works: list[dict],
    save_path: str,
    max_display: int = 80,
) -> None:
    """4 columns (25/50/75/100 %) × N rows (one per work)."""
    checkpoints = [0.25, 0.50, 0.75, 1.00]
    n = len(works)
    fig, axes = plt.subplots(n, 4, figsize=(22, 5.3 * n))
    if n == 1:
        axes = np.array([axes])

    for row, data in enumerate(works):
        work_key = data["metadata"]["work_key"]
        work_label = get_work_label(data)
        work_color = get_work_color_safe(work_key)
        n_chapters = num_chapters(data)

        # Build the *full* graph so the layout is consistent across snapshots
        full_idx = max(n_chapters - 1, 0)
        G_full = build_cumulative_graph(data, full_idx)
        if G_full.number_of_nodes() == 0:
            for col in range(4):
                axes[row][col].text(0.5, 0.5, "No data", ha="center",
                                    va="center", fontsize=12, alpha=0.5)
                axes[row][col].axis("off")
            continue

        # Limit to top-degree nodes for readability
        degrees_full = dict(G_full.degree())
        top_nodes_full = sorted(degrees_full, key=degrees_full.get, reverse=True)[:max_display]
        G_limited = G_full.subgraph(top_nodes_full).copy()

        pos = nx.spring_layout(G_limited, k=1.8, iterations=60, seed=42)

        for col, pct in enumerate(checkpoints):
            ax = axes[row][col]
            cutoff = max(int(pct * n_chapters) - 1, 0)

            active = [
                node for node, attrs in G_limited.nodes(data=True)
                if attrs.get("first_appearance", 0) <= cutoff
            ]
            G_snap = G_limited.subgraph(active).copy()
            G_snap.remove_edges_from([
                (u, v) for u, v, d in G_snap.edges(data=True)
                if d.get("first_appearance", 0) > cutoff
            ])

            if G_snap.number_of_nodes() == 0:
                ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                        fontsize=10, alpha=0.5)
                ax.axis("off")
                continue

            node_colors = [
                get_entity_color(G_snap.nodes[node].get("label", ""))
                for node in G_snap.nodes
            ]
            snap_degrees = dict(G_snap.degree())
            max_deg = max(snap_degrees.values()) if snap_degrees else 1
            node_sizes = [
                60 + 600 * (snap_degrees.get(node, 0) / max_deg)
                for node in G_snap.nodes
            ]
            snap_pos = {node: pos[node] for node in G_snap.nodes if node in pos}

            nx.draw_networkx_nodes(
                G_snap, snap_pos, node_color=node_colors, node_size=node_sizes,
                alpha=0.85, edgecolors="black", linewidths=0.3, ax=ax,
            )
            nx.draw_networkx_edges(
                G_snap, snap_pos, alpha=0.15, arrows=True, arrowsize=5,
                edge_color="gray", ax=ax,
            )
            top3 = sorted(snap_degrees, key=snap_degrees.get, reverse=True)[:3]
            labels = {node: G_snap.nodes[node].get("name", node)[:14] for node in top3}
            nx.draw_networkx_labels(G_snap, snap_pos, labels,
                                    font_size=7, font_weight="bold", ax=ax)

            ax.set_title(
                f"{int(pct * 100)}%  ({G_snap.number_of_nodes()}n, "
                f"{G_snap.number_of_edges()}e)",
                fontsize=10, fontweight="bold", pad=6,
            )
            ax.axis("off")

        axes[row][0].annotate(
            work_label, xy=(-0.3, 0.5), xycoords="axes fraction",
            fontsize=14, fontweight="bold", color=work_color,
            rotation=90, ha="center", va="center",
        )

    plt.suptitle(
        "Knowledge Graph Topology at 25%, 50%, 75%, and 100% Through Each Narrative",
        fontsize=16, fontweight="bold", y=0.995,
    )
    plt.tight_layout(rect=(0.03, 0, 1, 0.97))
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ---------------------------------------------------------------------------
# FIGURE 3: Relationship heatmap
# ---------------------------------------------------------------------------

def figure_relationship_heatmap(
    works: list[dict],
    save_path: str,
    top_relations: int = 12,
) -> None:
    """One panel per work: top-N relation types × chapter bins."""
    n = len(works)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 9))
    if n == 1:
        axes = [axes]

    for ax, data in zip(axes, works):
        work_key = data["metadata"]["work_key"]
        work_label = get_work_label(data)
        work_color = get_work_color_safe(work_key)
        chapter_label = data["metadata"].get("chapter_label", "Chapter")
        n_chapters = num_chapters(data)
        if n_chapters == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, alpha=0.5)
            ax.axis("off")
            continue

        if n_chapters > 20:
            n_bins = 16
        else:
            n_bins = n_chapters
        bin_size = max(1.0, n_chapters / n_bins)

        rel_counts = Counter(r["label"] for r in data["relations"])
        top_types = [t for t, _ in rel_counts.most_common(top_relations)]

        matrix = np.zeros((len(top_types), n_bins))
        for r in data["relations"]:
            if r["label"] in top_types:
                row = top_types.index(r["label"])
                col = min(int(r["first_appearance"] / bin_size), n_bins - 1)
                matrix[row, col] += 1

        rgb = mcolors.to_rgb(work_color)
        cmap = LinearSegmentedColormap.from_list(
            f"{work_key}_cmap", [(1, 1, 1), rgb], N=256,
        )
        im = ax.imshow(matrix, aspect="auto", cmap=cmap, interpolation="nearest")

        ax.set_yticks(range(len(top_types)))
        ax.set_yticklabels(top_types, fontsize=8)

        if n_bins <= 24:
            tick_positions = list(range(n_bins))
            tick_labels = (
                [f"{chapter_label} {i + 1}" for i in range(n_bins)]
                if n_chapters <= 10 else [str(i + 1) for i in range(n_bins)]
            )
        else:
            tick_positions = list(range(0, n_bins, 2))
            tick_labels = [str(int(i * bin_size) + 1) for i in tick_positions]

        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, fontsize=7, rotation=45, ha="right")
        ax.set_xlabel(chapter_label, fontsize=9)

        ax.set_title(f"{work_label}\nTop {top_relations} Relationship Types",
                     fontsize=12, fontweight="bold", color=work_color, pad=10)

        max_val = matrix.max() if matrix.size else 0
        if max_val > 0:
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    val = int(matrix[i, j])
                    if val > max_val * 0.3:
                        text_color = "white" if val > max_val * 0.6 else "black"
                        ax.text(j, i, str(val), ha="center", va="center",
                                fontsize=6, color=text_color, fontweight="bold")

        cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
        cbar.ax.tick_params(labelsize=7)
        cbar.set_label("Count", fontsize=8)

    plt.suptitle("Relationship Activity Across the Narrative",
                 fontsize=16, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ---------------------------------------------------------------------------
# FIGURE 4: Cast arrival strip
# ---------------------------------------------------------------------------

def figure_cast_arrival_strip(
    works: list[dict],
    save_path: str,
) -> None:
    """
    For each work, a horizontal strip showing each entity's chapter of first
    appearance. Marker color encodes entity type. Top-15 entities by total
    appearances are labeled.
    """
    n = len(works)
    fig, axes = plt.subplots(n, 1, figsize=(18, 3.5 * n))
    if n == 1:
        axes = [axes]

    for ax, data in zip(axes, works):
        work_key = data["metadata"]["work_key"]
        work_label = get_work_label(data)
        work_color = get_work_color_safe(work_key)
        n_chapters = num_chapters(data)
        chapter_label = data["metadata"].get("chapter_label", "Chapter")

        entities = data["entities"]
        if not entities:
            ax.text(0.5, 0.5, "No entities", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, alpha=0.5)
            ax.axis("off")
            continue

        # x: first appearance, y: small jitter so dots don't fully overlap
        rng = np.random.default_rng(seed=42)
        xs = np.array([e["first_appearance"] for e in entities], dtype=float)
        ys = rng.uniform(-0.4, 0.4, size=len(entities))
        sizes = np.array([
            30 + 4 * e.get("total_appearances", len(e.get("appearances", [1])))
            for e in entities
        ])
        colors = [get_entity_color(e["label"]) for e in entities]

        ax.scatter(xs, ys, s=sizes, c=colors, alpha=0.7, edgecolors="black",
                   linewidths=0.4)

        # Label the most prominent entities
        top = sorted(
            entities,
            key=lambda e: e.get("total_appearances", len(e.get("appearances", [1]))),
            reverse=True,
        )[:15]
        for e in top:
            x = e["first_appearance"]
            ax.annotate(
                e["name"][:18],
                xy=(x, 0),
                xytext=(0, 18 if hash(e["name"]) % 2 else -22),
                textcoords="offset points",
                fontsize=7, ha="center",
                color="#222",
                arrowprops=dict(arrowstyle="-", color="#888", lw=0.3),
            )

        ax.axhline(0, color="#CCCCCC", linewidth=0.6, zorder=0)
        ax.set_xlim(-0.5, max(n_chapters - 0.5, 1))
        ax.set_ylim(-1.2, 1.2)
        ax.set_yticks([])
        ax.set_xlabel(chapter_label, fontsize=9)
        ax.set_title(work_label, fontsize=13, fontweight="bold",
                     color=work_color, loc="left", pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.grid(axis="x", alpha=0.2, linestyle=":")

    # Legend (entity types) at the figure level
    type_set: set[str] = set()
    for data in works:
        type_set.update(e["label"] for e in data["entities"])
    handles = [
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor=ENTITY_TYPE_COLORS.get(t, "#CCCCCC"),
                   markeredgecolor="black", markersize=8, label=t)
        for t in sorted(type_set)
    ]
    fig.legend(handles=handles, loc="lower center",
               ncol=min(len(handles), 8), fontsize=8,
               bbox_to_anchor=(0.5, -0.02), frameon=False)

    plt.suptitle("Cast Arrival — Entity First Appearances",
                 fontsize=16, fontweight="bold", y=0.99)
    plt.tight_layout(rect=(0, 0.04, 1, 0.97))
    plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def render_all_figures(
    works: list[dict],
    output_dir: str,
    preset_keys: dict[str, str] | None = None,
) -> list[str]:
    """Render the four article figures from a list of temporal-extraction dicts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []

    figures = [
        ("narrative_chart.png", lambda p: figure_narrative_chart(works, p, preset_keys)),
        ("topology_snapshots.png", lambda p: figure_topology_snapshots(works, p)),
        ("relationship_heatmap.png", lambda p: figure_relationship_heatmap(works, p)),
        ("cast_arrival_strip.png", lambda p: figure_cast_arrival_strip(works, p)),
    ]
    for name, fn in figures:
        target = str(output_path / name)
        try:
            fn(target)
            saved.append(target)
        except Exception as exc:  # surface the error but keep going
            print(f"  FAILED {name}: {exc}")
    return saved


def _infer_preset_key(work_key: str, user_supplied: Optional[str]) -> Optional[str]:
    """If --preset matches a known preset, apply it to that work."""
    if user_supplied and user_supplied == work_key and has_preset(user_supplied):
        return user_supplied
    if not user_supplied and has_preset(work_key):
        return work_key
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the four article figures from temporal-extraction JSON."
    )
    parser.add_argument(
        "input_files", nargs="+",
        help="One or more *_temporal_kg.json files produced by temporal_extraction.py",
    )
    parser.add_argument(
        "-o", "--output", default="output/visualizations/",
        help="Output directory for the four PNG files",
    )
    parser.add_argument(
        "--preset",
        help="When the work_key matches a known preset (iliad/crime/dune), use "
             "the curated narrative-chart groupings. Default: auto-derive groups.",
    )
    parser.add_argument(
        "--no-presets", action="store_true",
        help="Force auto-derived narrative-chart groupings even when a preset is "
             "available (useful for comparing curated vs derived layouts).",
    )
    args = parser.parse_args()

    works = [load_temporal_json(p) for p in args.input_files]
    print(f"Loaded {len(works)} work(s):")
    for w in works:
        print(f"  {get_work_label(w)} — {len(w['entities'])} entities, "
              f"{len(w['relations'])} relations, {num_chapters(w)} chapters")

    preset_keys: dict[str, str] = {}
    if not args.no_presets:
        for w in works:
            wk = w["metadata"]["work_key"]
            inferred = _infer_preset_key(wk, args.preset)
            if inferred:
                preset_keys[wk] = inferred
                print(f"  Using preset '{inferred}' for narrative chart of '{wk}'")

    print(f"\nRendering figures to {args.output}")
    saved = render_all_figures(works, args.output, preset_keys)
    print(f"\nDone. {len(saved)} figure(s) written.")


if __name__ == "__main__":
    main()
