# Temporal Knowledge Graphs from Books

A LlamaIndex-based framework for extracting **chapter-by-chapter** knowledge
graphs from literary works, with full temporal metadata: when each entity
first appears, when each relationship forms, how the graph topology evolves.

This is the companion code for the article
[**"What Happens When You Extract a Knowledge Graph One Chapter at a Time? The Topology Tells the Story"**](https://medium.com).
It produces the four figures in the article — **narrative chart**,
**topology snapshots**, **relationship heatmap**, and **cast arrival** — from
real extraction output, not synthetic data.

> The Iliad's centralization drops in its middle third — not because Homer
> lost focus, but because Achilles is sulking in his tent. The graph
> *literally decentralizes*.

**▶ Live demo — [The Narrative Observatory](https://shereshevsky.github.io/temporal-narrative-evolution/):**
an animated radial instrument that plays each book's knowledge graph chapter
by chapter. Time wraps the dial; connection is gravity. Drag your own
`*_temporal_kg.json` onto the page to chart any book.

The pipeline works on any chaptered text. Three preset schemas
(*The Iliad*, *Crime and Punishment*, *Dune*) ship in the box; a
**generic schema** handles arbitrary books.

---

## Quickstart

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add your OpenAI key
cp .env.example .env
$EDITOR .env

# 3. Drop a chaptered text into ./data/ and run the full pipeline
python run_pipeline.py --file data/my_book.txt --work-key generic
```

That single command:

1. splits the text into chapters,
2. runs `SchemaLLMPathExtractor` on each chapter,
3. merges results into a temporal graph (with `first_appearance` per node and edge),
4. computes per-chapter structural metrics,
5. renders four figures into `output/visualizations/`.

> **Note on cost.** Extraction calls the OpenAI API once per chapter chunk.
> A full novel (~80–150K words) typically costs **\$2–\$5** with `gpt-4o`.
> Use `--max-chapters 3` for a free-tier-friendly dry run.

---

## What it produces

After a run, `output/` contains:

```
output/
├── my_book_temporal_kg.json         # raw graph + temporal metadata
├── my_book_temporal_analysis.json   # per-chapter structural metrics
└── visualizations/
    ├── narrative_chart.png          # XKCD-style character flow chart
    ├── topology_snapshots.png       # graph at 25/50/75/100% of the narrative
    ├── relationship_heatmap.png     # top-12 relation types × chapters
    └── cast_arrival_strip.png       # entity first-appearance timeline
```

---

## Architecture

```
   ┌─────────────────────┐
   │ raw text (chapters) │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐    ┌────────────────────────┐
   │ temporal_extraction │ ◄──│ schemas.py             │
   │  - chapter splitter │    │  iliad / crime / dune  │
   │  - SchemaLLMPath…   │    │  + generic             │
   │  - temporal merger  │    └────────────────────────┘
   └──────────┬──────────┘
              │  *_temporal_kg.json
              ▼
   ┌─────────────────────┐
   │ temporal_analysis   │
   │  - cumulative graph │
   │  - centralization   │
   │  - density / hubs   │
   │  - phase detection  │
   └──────────┬──────────┘
              │  *_temporal_analysis.json
              ▼
   ┌─────────────────────┐    ┌────────────────────────┐
   │ figures             │ ◄──│ presets/               │
   │  - narrative chart  │    │   curated narrative    │
   │  - topology snaps   │    │   chart layouts for    │
   │  - heatmap          │    │   the demo works       │
   │  - cast arrival     │    └────────────────────────┘
   └─────────────────────┘
```

**Modules** (all importable, all CLI-runnable):

| Module                        | Role                                                                                                |
| ----------------------------- | --------------------------------------------------------------------------------------------------- |
| `temporal_extraction.py`      | Chapter splitting + LLM extraction + temporal merging. Defines `TemporalKGBuilder`.                 |
| `schemas.py`                  | Domain-specific entity/relation type vocabularies and chapter regexes.                              |
| `temporal_analysis.py`        | NetworkX-based metrics: density, centralization, hub trajectories, narrative phases.                |
| `temporal_visualization.py`   | Single-work charts: growth curves, narrative EKG, centralization trajectory, character arcs.        |
| `figures.py`                  | The four article figures, real-data only.                                                           |
| `presets/`                    | Hand-curated narrative-chart groupings for the three demo works.                                    |
| `run_pipeline.py`             | One command: text → KG → analysis → figures.                                                        |

---

## Using the framework

### From the command line

```bash
# Full pipeline with a preset schema
python run_pipeline.py --file data/iliad.txt --work-key iliad

# Generic schema with a custom output name
python run_pipeline.py --file data/war_and_peace.txt \
                       --work-key generic --name war_and_peace

# Re-render figures from an existing KG (no API calls)
python run_pipeline.py --skip-extract \
                       --kg-json output/iliad_temporal_kg.json

# Dry run — just the first 3 chapters, to estimate cost/quality
python run_pipeline.py --file data/dune.txt --work-key dune --max-chapters 3
```

### From Python

```python
from temporal_extraction import TemporalKGBuilder, TemporalExtractionConfig

config = TemporalExtractionConfig(
    llm_model="gpt-4o",
    chunk_size=1200,
    chunk_overlap=200,
    max_triplets_per_chunk=20,
)

builder = TemporalKGBuilder(config)
result = builder.extract_temporal(your_text, "iliad")  # or "generic"
```

`result` is a dict with `metadata`, `chapters`, `entities`, `relations`, and a
per-chapter `timeline` of structural snapshots. Pass it to
`analyze_temporal_kg(...)` for full metrics, or to `render_all_figures(...)`
in `figures.py` for the article visuals.

### Stage-by-stage (advanced)

```bash
python temporal_extraction.py iliad --file data/iliad.txt -o output/
python temporal_analysis.py    output/iliad_temporal_kg.json -o output/
python figures.py              output/iliad_temporal_kg.json -o output/visualizations/
```

---

## Schemas

A schema declares what entity types and relationship types the LLM is allowed
to produce, plus the regex used to split the text into chapters.

| `--work-key` | Best for                | Entity types                                                               | Chapter pattern        |
| ------------ | ----------------------- | -------------------------------------------------------------------------- | ---------------------- |
| `iliad`      | epic poetry             | `HERO, DEITY, MORTAL, ARMY, LOCATION, ARTIFACT, BATTLE`                    | `BOOK [I-XXIV]`        |
| `crime`      | psychological novel     | `PROTAGONIST, CHARACTER, PSYCHOLOGICAL_STATE, LOCATION, INSTITUTION, IDEA, EVENT` | `PART [I-VI]`    |
| `dune`       | sci-fi / world-building | `CHARACTER, FACTION, LOCATION, RESOURCE, TECHNOLOGY, CREATURE, CONCEPT, RITUAL, PROPHECY, TITLE` | `=== / BOOK ONE…`     |
| `generic`    | any chaptered novel     | `CHARACTER, LOCATION, ORGANIZATION, EVENT, OBJECT, CONCEPT`                | `Chapter \d+ / I-X`   |

If your text doesn't match any chapter pattern, the splitter falls back to
roughly equal-sized segments (paragraph-aligned where possible).

### Adding a custom schema

Edit `schemas.py`:

```python
MyEntityType   = Literal["CHARACTER", "FACTION", "TECH"]
MyRelationType = Literal["LEADS", "OPPOSES", "INVENTS"]
MY_VALIDATION  = [
    ("CHARACTER", "LEADS", "FACTION"),
    ("CHARACTER", "OPPOSES", "CHARACTER"),
    ("CHARACTER", "INVENTS", "TECH"),
]

SCHEMA_REGISTRY["mywork"] = LiterarySchema(
    name="My Work",
    work_key="mywork",
    entity_types=MyEntityType,
    relation_types=MyRelationType,
    validation_schema=MY_VALIDATION,
    primary_structure="networked",
    narrative_focus="external_action",
    chapter_pattern=r"Chapter\s+(\d+)",
    chapter_label="Chapter",
    expected_chapters=20,
)
```

Then add `"mywork"` to the `choices=` list in `temporal_extraction.py` and
`run_pipeline.py`.

---

## How the four figures are computed

| Figure                       | What it shows                                                                                              | How it's built                                                                                                                |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **narrative_chart.png**      | Character lines flowing through the story; converging when characters interact, diverging when apart.     | Top-N characters by degree. Scene clusters auto-derived from cumulative graph components, or use `--preset` for the demos.    |
| **topology_snapshots.png**   | Graph at 25/50/75/100 % of the narrative.                                                                  | `build_cumulative_graph()` at each cutoff; `nx.spring_layout` keyed off the *final* graph for positional consistency.         |
| **relationship_heatmap.png** | Frequency of each top-12 relation type across chapter bins.                                                | Tally of `relations` keyed by `first_appearance` and `label`.                                                                 |
| **cast_arrival_strip.png**   | Each entity dotted at its `first_appearance` chapter, colored by entity type, sized by total appearances. | Direct projection of the `entities` list.                                                                                     |

For *iliad / crime / dune*, run with `--preset <work_key>` (or just rely on
`run_pipeline.py` — it auto-detects presets) to use the curated narrative-chart
groupings that match the figures in the article exactly. For any other book,
the auto-derived groupings will be used.

---

## Tips

- **Where to get texts.** The Iliad and Crime and Punishment are public domain
  on [Project Gutenberg](https://www.gutenberg.org/). Dune is under copyright —
  check your jurisdiction. This repo intentionally ships **no text files**.
- **Chapter splitting.** Inspect the chapter list printed at the start of a
  run. If the splitter found 1 chapter on a multi-chapter book, your text
  probably has unusual headings — adjust `chapter_pattern` in `schemas.py`.
- **Cost control.** Each chapter triggers one or more LLM calls.
  `--max-chapters` is your friend for testing.
- **Re-rendering only.** Once you have a `*_temporal_kg.json`, you can iterate
  on visualizations with no further API calls — use `--skip-extract`.

---

## Series

This is part of a three-article series on KG extraction from literature.

1. *Building Knowledge Graphs from Homer's Iliad* — first-pass extraction,
   single-document.
2. *Knowledge Graphs Reveal the Hidden Architecture of Great Literature* —
   cross-work structural comparison (still single-pass per work).
3. **This article** — chapter-by-chapter temporal extraction, narrative EKGs,
   topology evolution.

If you build something interesting on top of this, open an issue with a link
or a screenshot — I'd love to see it.
