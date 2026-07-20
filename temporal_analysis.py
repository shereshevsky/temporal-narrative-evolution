"""
Temporal Analysis Module for Literary Knowledge Graphs

Computes time-series structural metrics from temporal KG extraction results.
Produces the data needed for "narrative EKG" visualizations — showing how
graph properties like centralization, density, and character prominence
evolve chapter by chapter across a story.

Usage:
    python temporal_analysis.py output/iliad_temporal_kg.json -o output/iliad_analysis.json
    python temporal_analysis.py output/*.json --compare -o output/comparison.json
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
from typing import Optional

import networkx as nx

from temporal_extraction import load_temporal_result


# =============================================================================
# Graph Reconstruction from Temporal Data
# =============================================================================

def build_cumulative_graph(
    temporal_data: dict,
    up_to_chapter: int,
) -> nx.DiGraph:
    """
    Build a NetworkX graph containing all entities and relations that
    have appeared up to (and including) a given chapter.

    Args:
        temporal_data: Loaded temporal extraction result
        up_to_chapter: Include entities/relations first appearing <= this chapter

    Returns:
        NetworkX DiGraph representing the cumulative state
    """
    G = nx.DiGraph()

    # Add entities
    for entity in temporal_data["entities"]:
        if entity["first_appearance"] <= up_to_chapter:
            G.add_node(
                entity["id"],
                name=entity["name"],
                label=entity["label"],
                first_appearance=entity["first_appearance"],
            )

    # Add relations
    for rel in temporal_data["relations"]:
        if rel["first_appearance"] <= up_to_chapter:
            source = rel["source_id"]
            target = rel["target_id"]
            if source in G.nodes and target in G.nodes:
                G.add_edge(
                    source, target,
                    label=rel["label"],
                    first_appearance=rel["first_appearance"],
                )

    return G


def build_chapter_graph(
    temporal_data: dict,
    chapter_idx: int,
) -> nx.DiGraph:
    """
    Build a graph containing only entities and relations active in a
    specific chapter (not cumulative — just that chapter's activity).
    """
    G = nx.DiGraph()

    # Entities active in this chapter
    for entity in temporal_data["entities"]:
        if chapter_idx in entity.get("appearances", [entity["first_appearance"]]):
            G.add_node(
                entity["id"],
                name=entity["name"],
                label=entity["label"],
            )

    # Relations active in this chapter
    for rel in temporal_data["relations"]:
        if chapter_idx in rel.get("appearances", [rel["first_appearance"]]):
            source = rel["source_id"]
            target = rel["target_id"]
            if source in G.nodes and target in G.nodes:
                G.add_edge(source, target, label=rel["label"])

    return G


# =============================================================================
# Per-Chapter Structural Metrics
# =============================================================================

@dataclass
class ChapterMetrics:
    """Comprehensive structural metrics for one chapter's cumulative graph."""
    chapter_index: int
    chapter_label: str

    # Size
    node_count: int = 0
    edge_count: int = 0
    new_nodes: int = 0
    new_edges: int = 0

    # Structure
    density: float = 0.0
    avg_degree: float = 0.0
    max_degree: int = 0
    degree_centralization: float = 0.0

    # Clustering
    avg_clustering: float = 0.0
    transitivity: float = 0.0

    # Components
    num_components: int = 0
    largest_component_ratio: float = 0.0

    # Hub analysis
    top_hub_name: str = ""
    top_hub_degree: int = 0
    top_hub_ratio: float = 0.0  # degree / total nodes

    # Character-specific tracking
    character_degrees: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chapter_index": self.chapter_index,
            "chapter_label": self.chapter_label,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "new_nodes": self.new_nodes,
            "new_edges": self.new_edges,
            "density": round(self.density, 6),
            "avg_degree": round(self.avg_degree, 3),
            "max_degree": self.max_degree,
            "degree_centralization": round(self.degree_centralization, 4),
            "avg_clustering": round(self.avg_clustering, 4),
            "transitivity": round(self.transitivity, 4),
            "num_components": self.num_components,
            "largest_component_ratio": round(self.largest_component_ratio, 4),
            "top_hub_name": self.top_hub_name,
            "top_hub_degree": self.top_hub_degree,
            "top_hub_ratio": round(self.top_hub_ratio, 4),
            "character_degrees": self.character_degrees,
        }


def compute_chapter_metrics(
    G: nx.DiGraph,
    chapter_idx: int,
    chapter_label: str,
    prev_node_count: int = 0,
    prev_edge_count: int = 0,
    track_characters: list[str] = None,
) -> ChapterMetrics:
    """
    Compute structural metrics for a cumulative graph at a chapter checkpoint.

    Args:
        G: Cumulative NetworkX graph
        chapter_idx: Chapter index
        chapter_label: Human-readable chapter label
        prev_node_count: Node count at previous chapter
        prev_edge_count: Edge count at previous chapter
        track_characters: List of character names to track degree over time
    """
    m = ChapterMetrics(chapter_index=chapter_idx, chapter_label=chapter_label)

    if len(G.nodes) == 0:
        return m

    m.node_count = G.number_of_nodes()
    m.edge_count = G.number_of_edges()
    m.new_nodes = m.node_count - prev_node_count
    m.new_edges = m.edge_count - prev_edge_count

    # Density
    m.density = nx.density(G)

    # Degree statistics
    degrees = [d for _, d in G.degree()]
    if degrees:
        m.avg_degree = sum(degrees) / len(degrees)
        m.max_degree = max(degrees)

    # Degree centralization
    if m.node_count > 2 and degrees:
        max_deg = max(degrees)
        sum_diff = sum(max_deg - d for d in degrees)
        max_possible = (m.node_count - 1) * (m.node_count - 2)
        m.degree_centralization = sum_diff / max_possible if max_possible > 0 else 0

    # Clustering
    try:
        G_undirected = G.to_undirected()
        m.avg_clustering = nx.average_clustering(G_undirected)
        m.transitivity = nx.transitivity(G_undirected)
    except Exception:
        pass

    # Components
    try:
        components = list(nx.weakly_connected_components(G))
        m.num_components = len(components)
        if components:
            largest = max(len(c) for c in components)
            m.largest_component_ratio = largest / m.node_count
    except Exception:
        pass

    # Hub analysis
    degree_dict = dict(G.degree())
    if degree_dict:
        max_node = max(degree_dict, key=degree_dict.get)
        m.top_hub_name = G.nodes[max_node].get("name", max_node)
        m.top_hub_degree = degree_dict[max_node]
        m.top_hub_ratio = m.top_hub_degree / m.node_count if m.node_count > 0 else 0

    # Track specific characters
    if track_characters:
        name_to_degree = {}
        for node_id, data in G.nodes(data=True):
            name = data.get("name", "")
            if name in track_characters:
                name_to_degree[name] = degree_dict.get(node_id, 0)

        # Fill zeros for characters not yet appeared
        m.character_degrees = {
            name: name_to_degree.get(name, 0)
            for name in track_characters
        }

    return m


# =============================================================================
# Full Temporal Analysis
# =============================================================================

@dataclass
class TemporalAnalysisResult:
    """Complete temporal analysis for a literary work."""
    work_key: str
    work_name: str
    chapter_metrics: list         # List of ChapterMetrics dicts
    entity_timeline: list         # When each entity first appears
    relation_timeline: list       # When each relation first appears
    character_arcs: dict          # Character name -> degree at each chapter
    narrative_phases: list        # Detected narrative phases
    summary_stats: dict           # Aggregate statistics


def analyze_temporal_kg(
    temporal_data: dict,
    track_characters: list[str] = None,
) -> TemporalAnalysisResult:
    """
    Perform complete temporal analysis on extraction results.

    Args:
        temporal_data: Loaded temporal extraction result
        track_characters: Optional list of character names to track

    Returns:
        TemporalAnalysisResult with all metrics and timelines
    """
    work_key = temporal_data["metadata"]["work_key"]
    work_name = temporal_data["metadata"]["work_name"]
    chapters = temporal_data["chapters"]

    print(f"\nAnalyzing temporal KG for: {work_name}")
    print(f"  Chapters: {len(chapters)}")
    print(f"  Entities: {temporal_data['metadata']['total_entities']}")
    print(f"  Relations: {temporal_data['metadata']['total_relations']}")

    # Auto-detect top characters to track if not specified
    if not track_characters:
        track_characters = _detect_top_characters(temporal_data, top_n=8)
        print(f"  Auto-detected characters to track: {track_characters}")

    # Compute metrics at each chapter
    chapter_metrics_list = []
    prev_nodes = 0
    prev_edges = 0

    for chapter in chapters:
        idx = chapter["index"]
        label = chapter["label"]

        G = build_cumulative_graph(temporal_data, idx)
        metrics = compute_chapter_metrics(
            G, idx, label, prev_nodes, prev_edges, track_characters
        )
        chapter_metrics_list.append(metrics.to_dict())

        prev_nodes = metrics.node_count
        prev_edges = metrics.edge_count

    # Build entity first-appearance timeline
    entity_timeline = sorted(
        [
            {
                "name": e["name"],
                "label": e["label"],
                "first_appearance": e["first_appearance"],
                "total_appearances": e.get("total_appearances", len(e.get("appearances", []))),
            }
            for e in temporal_data["entities"]
        ],
        key=lambda x: x["first_appearance"],
    )

    # Build relation first-appearance timeline
    relation_timeline = sorted(
        [
            {
                "source": r["source_name"],
                "target": r["target_name"],
                "label": r["label"],
                "first_appearance": r["first_appearance"],
            }
            for r in temporal_data["relations"]
        ],
        key=lambda x: x["first_appearance"],
    )

    # Build character arcs (degree over time)
    character_arcs = {name: [] for name in track_characters}
    for cm in chapter_metrics_list:
        for name in track_characters:
            degree = cm.get("character_degrees", {}).get(name, 0)
            character_arcs[name].append({
                "chapter": cm["chapter_index"],
                "label": cm["chapter_label"],
                "degree": degree,
            })

    # Detect narrative phases
    narrative_phases = _detect_narrative_phases(chapter_metrics_list)

    # Summary statistics
    summary = _compute_summary_stats(chapter_metrics_list, temporal_data)

    result = TemporalAnalysisResult(
        work_key=work_key,
        work_name=work_name,
        chapter_metrics=chapter_metrics_list,
        entity_timeline=entity_timeline,
        relation_timeline=relation_timeline,
        character_arcs=character_arcs,
        narrative_phases=narrative_phases,
        summary_stats=summary,
    )

    print(f"\nAnalysis complete.")
    print(f"  Narrative phases detected: {len(narrative_phases)}")
    for phase in narrative_phases:
        print(f"    {phase['label']}: chapters {phase['start']}-{phase['end']}")

    return result


def _detect_top_characters(temporal_data: dict, top_n: int = 8) -> list[str]:
    """Detect the most connected characters by counting relation involvement."""
    name_count = Counter()
    for rel in temporal_data["relations"]:
        name_count[rel["source_name"]] += 1
        name_count[rel["target_name"]] += 1

    return [name for name, _ in name_count.most_common(top_n)]


def _detect_narrative_phases(chapter_metrics: list[dict]) -> list[dict]:
    """
    Detect narrative phases based on growth rate changes.

    Identifies periods of:
    - Exposition (slow, steady growth)
    - Rising action (accelerating new entities/relations)
    - Climax (peak activity)
    - Falling action (deceleration)
    """
    if len(chapter_metrics) < 4:
        return [{"label": "Full Narrative", "start": 0,
                 "end": len(chapter_metrics) - 1, "type": "full"}]

    # Calculate growth rates
    new_entity_rates = [cm["new_nodes"] for cm in chapter_metrics]
    new_relation_rates = [cm["new_edges"] for cm in chapter_metrics]
    activity = [e + r for e, r in zip(new_entity_rates, new_relation_rates)]

    # Smooth with moving average (window=3)
    smoothed = []
    for i in range(len(activity)):
        window_start = max(0, i - 1)
        window_end = min(len(activity), i + 2)
        smoothed.append(sum(activity[window_start:window_end]) / (window_end - window_start))

    # Detect phases using quartile thresholds
    if not smoothed:
        return []

    sorted_activity = sorted(smoothed)
    q25 = sorted_activity[len(sorted_activity) // 4]
    q75 = sorted_activity[3 * len(sorted_activity) // 4]

    phases = []
    current_phase = None

    for i, val in enumerate(smoothed):
        if val <= q25:
            phase_type = "quiet"
        elif val >= q75:
            phase_type = "intense"
        else:
            phase_type = "building"

        if current_phase is None or current_phase["type"] != phase_type:
            if current_phase:
                current_phase["end"] = i - 1
                phases.append(current_phase)
            current_phase = {
                "type": phase_type,
                "start": i,
                "end": i,
                "label": _phase_label(phase_type, i, len(smoothed)),
            }
        else:
            current_phase["end"] = i

    if current_phase:
        current_phase["end"] = len(smoothed) - 1
        phases.append(current_phase)

    return phases


def _phase_label(phase_type: str, position: int, total: int) -> str:
    """Generate narrative-aware labels for phases."""
    progress = position / total if total > 0 else 0

    if phase_type == "quiet":
        if progress < 0.25:
            return "Exposition"
        elif progress > 0.8:
            return "Resolution"
        else:
            return "Quiet Period"
    elif phase_type == "intense":
        if progress > 0.6:
            return "Climax"
        else:
            return "Rising Intensity"
    else:
        if progress < 0.5:
            return "Rising Action"
        else:
            return "Building Tension"


def _compute_summary_stats(chapter_metrics: list[dict], temporal_data: dict) -> dict:
    """Compute aggregate summary statistics."""
    if not chapter_metrics:
        return {}

    # Growth rates
    entity_growth = [cm["new_nodes"] for cm in chapter_metrics]
    relation_growth = [cm["new_edges"] for cm in chapter_metrics]

    # Peak chapter (most new entities + relations)
    combined_growth = [e + r for e, r in zip(entity_growth, relation_growth)]
    peak_idx = combined_growth.index(max(combined_growth)) if combined_growth else 0

    # Centralization trajectory
    centralizations = [cm["degree_centralization"] for cm in chapter_metrics]

    # Density trajectory
    densities = [cm["density"] for cm in chapter_metrics]

    return {
        "total_chapters": len(chapter_metrics),
        "total_entities": chapter_metrics[-1]["node_count"] if chapter_metrics else 0,
        "total_relations": chapter_metrics[-1]["edge_count"] if chapter_metrics else 0,
        "avg_new_entities_per_chapter": sum(entity_growth) / len(entity_growth) if entity_growth else 0,
        "avg_new_relations_per_chapter": sum(relation_growth) / len(relation_growth) if relation_growth else 0,
        "peak_activity_chapter": chapter_metrics[peak_idx]["chapter_label"] if chapter_metrics else "",
        "peak_activity_index": peak_idx,
        "max_centralization": max(centralizations) if centralizations else 0,
        "final_centralization": centralizations[-1] if centralizations else 0,
        "centralization_trend": (
            "increasing" if len(centralizations) > 1 and centralizations[-1] > centralizations[0]
            else "decreasing"
        ),
        "max_density": max(densities) if densities else 0,
        "final_density": densities[-1] if densities else 0,
        "final_top_hub": chapter_metrics[-1]["top_hub_name"] if chapter_metrics else "",
        "final_top_hub_degree": chapter_metrics[-1]["top_hub_degree"] if chapter_metrics else 0,
    }


# =============================================================================
# Serialization
# =============================================================================

def save_analysis(result: TemporalAnalysisResult, output_path: str) -> str:
    """Save analysis result to JSON."""
    data = {
        "work_key": result.work_key,
        "work_name": result.work_name,
        "summary": result.summary_stats,
        "chapter_metrics": result.chapter_metrics,
        "entity_timeline": result.entity_timeline,
        "relation_timeline": result.relation_timeline,
        "character_arcs": result.character_arcs,
        "narrative_phases": result.narrative_phases,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved analysis to: {path}")
    return str(path)


def load_analysis(json_path: str) -> dict:
    """Load analysis result from JSON."""
    return json.loads(Path(json_path).read_text(encoding="utf-8"))


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze temporal evolution of literary knowledge graphs"
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        help="Path(s) to temporal KG JSON files"
    )
    parser.add_argument(
        "--output", "-o",
        default="output/",
        help="Output directory for analysis results"
    )
    parser.add_argument(
        "--characters",
        nargs="*",
        help="Specific characters to track (auto-detected if not specified)"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Generate cross-work comparison"
    )

    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for input_file in args.input_files:
        temporal_data = load_temporal_result(input_file)
        work_key = temporal_data["metadata"]["work_key"]

        analysis = analyze_temporal_kg(temporal_data, track_characters=args.characters)
        save_path = output_dir / f"{work_key}_temporal_analysis.json"
        save_analysis(analysis, str(save_path))
        results[work_key] = analysis

    if args.compare and len(results) > 1:
        print("\n\nCross-work comparison coming soon...")
