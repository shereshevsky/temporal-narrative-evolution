"""
End-to-end pipeline: text file → temporal KG → analysis → article figures.

This is the single command users run after cloning the repo. It chains the
three stages of the framework:

    1. temporal_extraction  — splits text into chapters and runs LlamaIndex's
                              SchemaLLMPathExtractor on each, producing a
                              temporal KG JSON with first_appearance metadata.
    2. temporal_analysis    — computes per-chapter structural metrics
                              (centralization, density, hub trajectories).
    3. figures              — renders the four article figures from the
                              extraction output.

CLI
---

    # Run with one of the preset schemas
    python run_pipeline.py --file iliad.txt --work-key iliad

    # Run on any chaptered text using the generic schema, with a custom name
    python run_pipeline.py --file my_book.txt --work-key generic --name my_book

    # Skip extraction (use existing JSON) — only re-analyze and re-render
    python run_pipeline.py --skip-extract --kg-json output/iliad_temporal_kg.json

Outputs (under --output, default ./output/):
    {name}_temporal_kg.json        — raw temporal extraction
    {name}_temporal_analysis.json  — structural metrics over time
    visualizations/                — narrative_chart.png, topology_snapshots.png,
                                     relationship_heatmap.png, cast_arrival_strip.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from figures import load_temporal_json, render_all_figures
from presets import has_preset
from temporal_analysis import analyze_temporal_kg, save_analysis
from temporal_extraction import (
    TemporalExtractionConfig,
    TemporalKGBuilder,
    save_temporal_result,
)


def _resolve_name(name: str | None, work_key: str, file_arg: str | None) -> str:
    """Pick the filename prefix for outputs."""
    if name:
        return name
    if file_arg and work_key == "generic":
        return Path(file_arg).stem
    return work_key


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ----- Stage 1: extraction (or load existing JSON) -----
    if args.skip_extract:
        if not args.kg_json:
            print("ERROR: --skip-extract requires --kg-json <path>", file=sys.stderr)
            return 2
        kg_path = Path(args.kg_json)
        if not kg_path.exists():
            print(f"ERROR: {kg_path} not found", file=sys.stderr)
            return 2
        kg_data = load_temporal_json(str(kg_path))
        name = _resolve_name(args.name, kg_data["metadata"]["work_key"], None)
        print(f"Skipping extraction. Using {kg_path}")
    else:
        if not args.file:
            print("ERROR: --file <text> is required (or use --skip-extract)",
                  file=sys.stderr)
            return 2

        text_path = Path(args.file)
        if not text_path.exists():
            print(f"ERROR: text file {text_path} not found", file=sys.stderr)
            return 2

        text = text_path.read_text(encoding="utf-8")
        name = _resolve_name(args.name, args.work_key, args.file)

        config = TemporalExtractionConfig(
            llm_model=args.model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            max_triplets_per_chunk=args.max_triplets,
        )
        builder = TemporalKGBuilder(config)
        kg_data = builder.extract_temporal(
            text, args.work_key, max_chapters=args.max_chapters,
        )

        kg_path = output_dir / f"{name}_temporal_kg.json"
        save_temporal_result(kg_data, str(kg_path))

    # ----- Stage 2: analysis -----
    print(f"\n--- Stage 2: analysis ---")
    analysis = analyze_temporal_kg(kg_data, track_characters=args.characters)
    analysis_path = output_dir / f"{name}_temporal_analysis.json"
    save_analysis(analysis, str(analysis_path))

    # ----- Stage 3: figures -----
    print(f"\n--- Stage 3: figures ---")
    work_key = kg_data["metadata"]["work_key"]
    preset_keys: dict[str, str] = {}
    if has_preset(work_key) and not args.no_presets:
        preset_keys[work_key] = work_key
        print(f"Using curated preset for narrative chart ({work_key})")

    viz_dir = output_dir / "visualizations"
    saved = render_all_figures([kg_data], str(viz_dir), preset_keys)

    print("\n=" * 1, "Pipeline complete.")
    print(f"  KG:       {kg_path}")
    print(f"  Analysis: {analysis_path}")
    print(f"  Figures:  {len(saved)} written to {viz_dir}/")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full temporal-KG pipeline: extract → analyze → render."
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to the text file to process (required unless --skip-extract).",
    )
    parser.add_argument(
        "--work-key", default="generic",
        choices=["iliad", "crime", "dune", "generic"],
        help="Schema to use. 'generic' works on any chaptered text.",
    )
    parser.add_argument(
        "--name",
        help="Output filename prefix. Defaults to --work-key, or the input "
             "filename's stem when --work-key=generic.",
    )
    parser.add_argument(
        "--output", "-o", default="output/",
        help="Directory for outputs (KG JSON, analysis JSON, figures/).",
    )
    parser.add_argument(
        "--model", default="gpt-4o", help="LLM model to use for extraction.",
    )
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    parser.add_argument("--max-triplets", type=int, default=20)
    parser.add_argument(
        "--max-chapters", type=int,
        help="Cap on chapters processed (useful for cost-controlled testing).",
    )
    parser.add_argument(
        "--characters", nargs="*",
        help="Character names to track in analysis (auto-detected by default).",
    )
    parser.add_argument(
        "--skip-extract", action="store_true",
        help="Skip extraction stage and load an existing temporal KG JSON "
             "(specify with --kg-json). Useful for re-rendering figures only.",
    )
    parser.add_argument(
        "--kg-json",
        help="Path to an existing *_temporal_kg.json to use with --skip-extract.",
    )
    parser.add_argument(
        "--no-presets", action="store_true",
        help="Skip the curated narrative-chart preset even when one exists.",
    )

    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
