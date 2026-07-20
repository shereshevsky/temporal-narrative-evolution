"""
Temporal Visualization Module — The Narrative EKG

Generates visualizations that show how knowledge graph structure evolves
across a literary narrative, chapter by chapter:

1. Growth curves (cumulative entities/relations over time)
2. Narrative EKG (new entities + relations per chapter — the "heartbeat")
3. Centralization trajectory (how protagonist-centric the graph is over time)
4. Character arcs (degree evolution for key characters)
5. Entity type stacking (how the "composition" of the world changes)
6. Phase-annotated timeline (exposition → rising → climax → resolution)

Usage:
    python temporal_visualization.py output/iliad_temporal_analysis.json -o figures/
    python temporal_visualization.py output/*.json --compare -o figures/
"""

import json
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

from temporal_analysis import load_analysis


# =============================================================================
# Color Configuration
# =============================================================================

WORK_COLORS = {
    "iliad": "#E63946",
    "crime": "#457B9D",
    "dune": "#E9C46A",
}

WORK_COLORS_LIGHT = {
    "iliad": "#F4A3A8",
    "crime": "#A3C4D9",
    "dune": "#F5DFA3",
}

PHASE_COLORS = {
    "quiet": "#E8E8E8",
    "building": "#FFE0B2",
    "intense": "#FFAB91",
}

CHARACTER_COLORS = [
    "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
    "#F4A261", "#264653", "#A8DADC", "#9B2335",
]

ENTITY_TYPE_COLORS = {
    "HERO": "#DC143C", "DEITY": "#FFD700", "MORTAL": "#808080",
    "ARMY": "#228B22", "LOCATION": "#4169E1", "ARTIFACT": "#8B4513",
    "BATTLE": "#FF4500", "PROTAGONIST": "#1E3A5F", "CHARACTER": "#5C8DB8",
    "PSYCHOLOGICAL_STATE": "#9B2335", "IDEA": "#6B4984",
    "EVENT": "#CD853F", "INSTITUTION": "#2F4F4F",
    "FACTION": "#8B7355", "RESOURCE": "#DAA520", "TECHNOLOGY": "#4682B4",
    "CREATURE": "#556B2F", "CONCEPT": "#9370DB", "RITUAL": "#8B0000",
    "PROPHECY": "#9932CC", "TITLE": "#C0C0C0", "OBJECT": "#708090",
}


def get_work_color(work_key: str) -> str:
    return WORK_COLORS.get(work_key, "#666666")


def get_entity_color(label: str) -> str:
    return ENTITY_TYPE_COLORS.get(label, "#CCCCCC")


# =============================================================================
# Shared Styling
# =============================================================================

def apply_clean_style(ax, title: str = "", xlabel: str = "", ylabel: str = ""):
    """Apply consistent clean styling to a plot axis."""
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.tick_params(labelsize=9)


def add_phase_background(ax, phases: list, x_range: tuple):
    """Add colored background bands for narrative phases."""
    for phase in phases:
        color = PHASE_COLORS.get(phase["type"], "#F5F5F5")
        ax.axvspan(phase["start"], phase["end"] + 0.5, alpha=0.2, color=color)
        # Label at top
        mid = (phase["start"] + phase["end"]) / 2
        ax.text(
            mid, ax.get_ylim()[1] * 0.95, phase["label"],
            ha="center", va="top", fontsize=7, alpha=0.6, style="italic"
        )


# =============================================================================
# Figure 1: Cumulative Growth Curves
# =============================================================================

def plot_growth_curves(
    analysis_data: dict,
    save_path: Optional[str] = None,
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """
    Plot cumulative entity and relation counts over chapters.
    Shows the "build-up" of the story world.
    """
    chapters = analysis_data["chapter_metrics"]
    work_name = analysis_data["work_name"]
    work_key = analysis_data["work_key"]
    color = get_work_color(work_key)

    x = [cm["chapter_index"] for cm in chapters]
    entities = [cm["node_count"] for cm in chapters]
    relations = [cm["edge_count"] for cm in chapters]
    labels = [cm["chapter_label"] for cm in chapters]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Entities
    ax1.fill_between(x, entities, alpha=0.3, color=color)
    ax1.plot(x, entities, "o-", color=color, linewidth=2, markersize=4)
    apply_clean_style(ax1, "Cumulative Entities", "Chapter", "Entity Count")

    # Relations
    ax2.fill_between(x, relations, alpha=0.3, color=color)
    ax2.plot(x, relations, "s-", color=color, linewidth=2, markersize=4)
    apply_clean_style(ax2, "Cumulative Relations", "Chapter", "Relation Count")

    # Add phase backgrounds if available
    if "narrative_phases" in analysis_data:
        add_phase_background(ax1, analysis_data["narrative_phases"], (x[0], x[-1]))
        add_phase_background(ax2, analysis_data["narrative_phases"], (x[0], x[-1]))

    plt.suptitle(
        f"{work_name} — Knowledge Graph Growth",
        fontsize=15, fontweight="bold", y=1.02
    )
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# =============================================================================
# Figure 2: The Narrative EKG (Heartbeat)
# =============================================================================

def plot_narrative_ekg(
    analysis_data: dict,
    save_path: Optional[str] = None,
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """
    Plot new entities and relations per chapter — the story's "heartbeat".
    Spikes indicate chapters with high narrative activity.
    """
    chapters = analysis_data["chapter_metrics"]
    work_name = analysis_data["work_name"]
    work_key = analysis_data["work_key"]
    color = get_work_color(work_key)

    x = [cm["chapter_index"] for cm in chapters]
    new_entities = [cm["new_nodes"] for cm in chapters]
    new_relations = [cm["new_edges"] for cm in chapters]
    combined = [e + r for e, r in zip(new_entities, new_relations)]

    fig, ax = plt.subplots(figsize=figsize)

    # Bar chart for new entities (below) and relations (stacked above)
    ax.bar(x, new_entities, color=color, alpha=0.7, label="New Entities", width=0.8)
    ax.bar(x, new_relations, bottom=new_entities, color=color, alpha=0.4,
           label="New Relations", width=0.8)

    # Overlay: smoothed trend line
    if len(combined) > 3:
        window = min(3, len(combined) // 2)
        smoothed = np.convolve(combined, np.ones(window) / window, mode="same")
        ax.plot(x, smoothed, "k--", linewidth=1.5, alpha=0.5, label="Trend")

    # Mark the peak
    if combined and max(combined) > 0:
        peak_idx = combined.index(max(combined))
        ax.annotate(
            f"Peak: {chapters[peak_idx]['chapter_label']}",
            xy=(x[peak_idx], combined[peak_idx]),
            xytext=(x[peak_idx] + 1, combined[peak_idx] * 1.1),
            fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="black"),
        )

    # Phase backgrounds
    if "narrative_phases" in analysis_data:
        add_phase_background(ax, analysis_data["narrative_phases"], (x[0], x[-1]))

    apply_clean_style(ax, f"{work_name} — Narrative EKG",
                      "Chapter", "New Entities + Relations")
    ax.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# =============================================================================
# Figure 3: Centralization Trajectory
# =============================================================================

def plot_centralization_trajectory(
    analysis_data: dict,
    save_path: Optional[str] = None,
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """
    Plot degree centralization and top hub ratio over time.
    Shows how protagonist-dominated the narrative is at each point.
    """
    chapters = analysis_data["chapter_metrics"]
    work_name = analysis_data["work_name"]
    work_key = analysis_data["work_key"]
    color = get_work_color(work_key)

    x = [cm["chapter_index"] for cm in chapters]
    centralization = [cm["degree_centralization"] for cm in chapters]
    hub_ratio = [cm["top_hub_ratio"] for cm in chapters]
    hub_names = [cm["top_hub_name"] for cm in chapters]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Centralization
    ax1.plot(x, centralization, "o-", color=color, linewidth=2, markersize=4)
    ax1.fill_between(x, centralization, alpha=0.2, color=color)
    apply_clean_style(ax1, "Degree Centralization Over Time",
                      "Chapter", "Centralization")

    # Hub ratio with name annotations
    ax2.plot(x, hub_ratio, "s-", color=color, linewidth=2, markersize=4)
    ax2.fill_between(x, hub_ratio, alpha=0.2, color=color)

    # Annotate when the top hub changes
    prev_hub = ""
    for i, name in enumerate(hub_names):
        if name != prev_hub and name:
            ax2.annotate(
                name, xy=(x[i], hub_ratio[i]),
                xytext=(0, 10), textcoords="offset points",
                fontsize=7, ha="center", fontweight="bold", alpha=0.8,
            )
            prev_hub = name

    apply_clean_style(ax2, "Top Hub Dominance Over Time",
                      "Chapter", "Hub Degree / Total Nodes")

    plt.suptitle(
        f"{work_name} — Centralization Trajectory",
        fontsize=15, fontweight="bold", y=1.02
    )
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# =============================================================================
# Figure 4: Character Arcs (Degree Over Time)
# =============================================================================

def plot_character_arcs(
    analysis_data: dict,
    save_path: Optional[str] = None,
    figsize: tuple = (14, 7),
    max_characters: int = 8,
) -> plt.Figure:
    """
    Plot degree evolution for top characters across the narrative.
    Shows when characters gain/lose narrative prominence.
    """
    character_arcs = analysis_data.get("character_arcs", {})
    work_name = analysis_data["work_name"]

    if not character_arcs:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No character arc data available",
                ha="center", va="center", fontsize=14)
        return fig

    # Sort characters by final degree
    sorted_chars = sorted(
        character_arcs.items(),
        key=lambda item: item[1][-1]["degree"] if item[1] else 0,
        reverse=True,
    )[:max_characters]

    fig, ax = plt.subplots(figsize=figsize)

    for i, (name, arc) in enumerate(sorted_chars):
        x = [point["chapter"] for point in arc]
        y = [point["degree"] for point in arc]
        color = CHARACTER_COLORS[i % len(CHARACTER_COLORS)]

        ax.plot(x, y, "o-", label=name, color=color, linewidth=2,
                markersize=3, alpha=0.85)

    # Phase backgrounds
    if "narrative_phases" in analysis_data:
        add_phase_background(ax, analysis_data["narrative_phases"],
                             (0, len(analysis_data["chapter_metrics"])))

    apply_clean_style(ax, f"{work_name} — Character Arcs (Degree Over Time)",
                      "Chapter", "Degree (Number of Connections)")
    ax.legend(loc="upper left", fontsize=9, ncol=2)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# =============================================================================
# Figure 5: Entity Type Composition Over Time (Stacked Area)
# =============================================================================

def plot_entity_composition(
    analysis_data: dict,
    save_path: Optional[str] = None,
    figsize: tuple = (14, 6),
) -> plt.Figure:
    """
    Stacked area chart showing how the composition of entity types
    evolves over the narrative.
    """
    chapters = analysis_data["chapter_metrics"]
    work_name = analysis_data["work_name"]

    if not chapters:
        fig, ax = plt.subplots(figsize=figsize)
        return fig

    # Collect all entity types
    all_types = set()
    for cm in chapters:
        # Use timeline data to reconstruct type distribution
        all_types.update(cm.get("entity_type_distribution", {}).keys())

    # Use the entity_type_distribution from the timeline snapshots if available
    # Otherwise, fall back to the chapter_metrics
    x = [cm["chapter_index"] for cm in chapters]
    type_series = {}

    # Get type distributions from the timeline
    timeline = analysis_data.get("chapter_metrics", [])
    for t in timeline:
        dist = t.get("entity_type_distribution", {})
        all_types.update(dist.keys())

    # We need cumulative type counts. Build from entity_timeline if available.
    entity_timeline = analysis_data.get("entity_timeline", [])
    if entity_timeline:
        for etype in all_types:
            series = []
            for ch_idx in x:
                count = sum(
                    1 for e in entity_timeline
                    if e["label"] == etype and e["first_appearance"] <= ch_idx
                )
                series.append(count)
            type_series[etype] = series
    else:
        # Fallback: use whatever is in chapter_metrics
        for etype in all_types:
            type_series[etype] = [
                cm.get("entity_type_distribution", {}).get(etype, 0)
                for cm in chapters
            ]

    # Sort types by final count (largest at bottom)
    sorted_types = sorted(
        type_series.keys(),
        key=lambda t: type_series[t][-1] if type_series[t] else 0,
        reverse=True
    )

    fig, ax = plt.subplots(figsize=figsize)

    y_stack = np.zeros(len(x))
    for etype in reversed(sorted_types):  # Reverse so largest is at bottom
        values = np.array(type_series[etype], dtype=float)
        color = get_entity_color(etype)
        ax.fill_between(x, y_stack, y_stack + values, alpha=0.7,
                        color=color, label=etype)
        y_stack += values

    apply_clean_style(ax, f"{work_name} — Entity Type Composition Over Time",
                      "Chapter", "Cumulative Entity Count")
    ax.legend(loc="upper left", fontsize=8, ncol=2)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# =============================================================================
# Figure 6: Comparative Multi-Work Dashboard
# =============================================================================

def plot_comparative_dashboard(
    analyses: dict,  # work_key -> analysis_data
    save_path: Optional[str] = None,
    figsize: tuple = (18, 12),
) -> plt.Figure:
    """
    Multi-panel comparison of temporal evolution across works.

    Panels:
    - Row 1: Cumulative growth curves (normalized)
    - Row 2: Narrative EKGs overlaid
    - Row 3: Centralization trajectories overlaid
    """
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)

    # === Row 1: Normalized growth curves ===
    ax_entities = fig.add_subplot(gs[0, 0])
    ax_relations = fig.add_subplot(gs[0, 1])

    for work_key, data in analyses.items():
        chapters = data["chapter_metrics"]
        color = get_work_color(work_key)
        name = data["work_name"]

        # Normalize x-axis to 0-1 (percentage through narrative)
        total = len(chapters)
        x_norm = [cm["chapter_index"] / max(total - 1, 1) for cm in chapters]

        entities = [cm["node_count"] for cm in chapters]
        relations = [cm["edge_count"] for cm in chapters]

        # Normalize y to percentage of final count
        max_e = max(entities) if entities else 1
        max_r = max(relations) if relations else 1

        ax_entities.plot(x_norm, [e / max_e for e in entities],
                         "-", color=color, linewidth=2, label=name)
        ax_relations.plot(x_norm, [r / max_r for r in relations],
                          "-", color=color, linewidth=2, label=name)

    apply_clean_style(ax_entities, "Entity Growth (Normalized)",
                      "Progress Through Narrative", "% of Final Count")
    ax_entities.legend(fontsize=9)
    apply_clean_style(ax_relations, "Relation Growth (Normalized)",
                      "Progress Through Narrative", "% of Final Count")

    # === Row 2: EKG overlay ===
    ax_ekg = fig.add_subplot(gs[1, :])

    for work_key, data in analyses.items():
        chapters = data["chapter_metrics"]
        color = get_work_color(work_key)
        name = data["work_name"]

        total = len(chapters)
        x_norm = [cm["chapter_index"] / max(total - 1, 1) for cm in chapters]
        combined = [cm["new_nodes"] + cm["new_edges"] for cm in chapters]

        # Normalize by max activity
        max_activity = max(combined) if combined else 1
        normalized = [c / max_activity for c in combined]

        # Smooth
        if len(normalized) > 3:
            window = min(3, len(normalized) // 2)
            smoothed = np.convolve(normalized, np.ones(window) / window, mode="same")
        else:
            smoothed = normalized

        ax_ekg.plot(x_norm, smoothed, "-", color=color, linewidth=2,
                    label=name, alpha=0.85)
        ax_ekg.fill_between(x_norm, smoothed, alpha=0.15, color=color)

    apply_clean_style(ax_ekg, "Narrative EKG Comparison (Normalized)",
                      "Progress Through Narrative", "Activity (Normalized)")
    ax_ekg.legend(fontsize=10)

    # === Row 3: Centralization trajectory ===
    ax_central = fig.add_subplot(gs[2, 0])
    ax_density = fig.add_subplot(gs[2, 1])

    for work_key, data in analyses.items():
        chapters = data["chapter_metrics"]
        color = get_work_color(work_key)
        name = data["work_name"]

        total = len(chapters)
        x_norm = [cm["chapter_index"] / max(total - 1, 1) for cm in chapters]

        centralization = [cm["degree_centralization"] for cm in chapters]
        density = [cm["density"] for cm in chapters]

        ax_central.plot(x_norm, centralization, "-", color=color,
                        linewidth=2, label=name)
        ax_density.plot(x_norm, density, "-", color=color,
                        linewidth=2, label=name)

    apply_clean_style(ax_central, "Centralization Trajectory",
                      "Progress Through Narrative", "Degree Centralization")
    ax_central.legend(fontsize=9)
    apply_clean_style(ax_density, "Density Trajectory",
                      "Progress Through Narrative", "Graph Density")

    plt.suptitle(
        "Temporal Evolution Comparison Across Literary Traditions",
        fontsize=16, fontweight="bold", y=1.01
    )

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="white")
    return fig


# =============================================================================
# Generate All Visualizations
# =============================================================================

def generate_all_visualizations(
    analysis_data: dict,
    output_dir: str,
) -> list[str]:
    """
    Generate all visualization types for a single work.

    Returns list of saved file paths.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    work_key = analysis_data["work_key"]

    saved = []
    viz_funcs = [
        ("growth_curves", plot_growth_curves),
        ("narrative_ekg", plot_narrative_ekg),
        ("centralization_trajectory", plot_centralization_trajectory),
        ("character_arcs", plot_character_arcs),
        ("entity_composition", plot_entity_composition),
    ]

    for name, func in viz_funcs:
        try:
            filepath = output_path / f"{work_key}_{name}.png"
            fig = func(analysis_data, save_path=str(filepath))
            plt.close(fig)
            saved.append(str(filepath))
            print(f"  Generated: {filepath.name}")
        except Exception as e:
            print(f"  FAILED {name}: {e}")

    return saved


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate temporal visualizations for literary KGs"
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        help="Path(s) to temporal analysis JSON files"
    )
    parser.add_argument(
        "--output", "-o",
        default="figures/",
        help="Output directory for figures"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Also generate cross-work comparison dashboard"
    )

    args = parser.parse_args()

    analyses = {}
    for input_file in args.input_files:
        data = load_analysis(input_file)
        work_key = data["work_key"]
        analyses[work_key] = data

        print(f"\nGenerating visualizations for: {data['work_name']}")
        generate_all_visualizations(data, args.output)

    if args.compare and len(analyses) > 1:
        print(f"\nGenerating comparative dashboard...")
        filepath = Path(args.output) / "comparative_dashboard.png"
        fig = plot_comparative_dashboard(analyses, save_path=str(filepath))
        plt.close(fig)
        print(f"  Generated: {filepath.name}")
