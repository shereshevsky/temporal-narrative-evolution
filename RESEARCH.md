# Research Brief: Temporal Knowledge Graph Extraction & Temporal-Data Art

Compiled 2026-07-19 for the "Temporal Narrative Evolution" article series.
Two tracks: (1) the state of the art in temporal KG extraction, mapping where
this project's chapter-wise pipeline sits; (2) the visual-art lineage behind
the Narrative Observatory visualization.

---

## Track 1 — Temporal KG extraction: landscape and positioning

### How each camp models time

| Time model | Representative systems | Semantics |
|---|---|---|
| None (static snapshot) | LlamaIndex property graphs, LangChain `LLMGraphTransformer`, Microsoft GraphRAG, Triplex, KGGen | Corpus = one timeless graph |
| Ingestion/episode order | iText2KG, AriGraph | "When the system saw it" — no world-time claim |
| Bi-temporal (valid × transaction time) | **Graphiti/Zep**, ATOM | Four timestamps per edge; contradictions close validity windows |
| Event-time quadruples (s,r,o,t) | ICEWS/GDELT tradition; TG-RAG, T-GRAG | Wall-clock timestamps on facts |
| Snapshot/interval embeddings | TTransE, HyTE, RE-NET, TGN, T-GAP | Discretized wall-clock time for link prediction |
| **Narrative time (chapter index)** | Agarwal 2012, Min & Park 2016, Renard, EvolvTrip, GraphLit, Narrative World Model — **and this pipeline** | Position in the discourse, not the clock |

Key gap: **no production framework has first-class narrative time.** Graphiti's
per-episode `reference_time` is the only hook that could carry it, and its LLM
date-inference actively fights fiction ("the next morning" has no calendar
anchor).

### What is NOT novel (avoid overclaiming in the article)

- Dynamic character networks per chapter — Agarwal et al. 2012 (Alice in
  Wonderland); formalized in Labatut & Bost's survey; industrialized by Renard.
- Graph growth curves as plot signatures — Min & Park did this for Les
  Misérables in 2016.
- LLM relationship extraction from novels — active since 2024 (CREFT etc.).
- Bi-temporal LLM-built KGs — Graphiti/Zep and ATOM own that claim.

### What IS defensible as novel

1. **Typed, schema-constrained KGs (not co-occurrence networks) in narrative
   time.** The fiction literature almost exclusively builds character–character
   interaction edges. This pipeline extracts heterogeneous, ontology-governed
   graphs (characters, places, factions, psychological states, typed relations)
   and timestamps each *fact* with its chapter of first appearance.
2. **First-appearance time as reader-knowledge bi-temporality.** Graphiti's
   valid-time/transaction-time maps onto narratology: when a fact becomes true
   in the story world (fabula / valid time) vs. when the reader learns it
   (syuzhet / transaction time = chapter index). Flashbacks are backfill;
   foreshadowing is a forward-dated fact. Nobody has made this mapping explicit.
3. **Comparative graph signatures across canonical works.** Same extractor,
   same schema discipline, three structurally extreme narratives — showing
   growth dynamics (density, centralization, entity-introduction rate,
   relation-type mix) are distinguishable fingerprints.
4. **Practitioner documentation of the gap** — how to repurpose atemporal
   commodity tooling (LlamaIndex) for discourse-time tracking, and where it breaks.

### Core references

- Rasmussen et al., *Zep: A Temporal Knowledge Graph Architecture for Agent
  Memory* (2025) — https://arxiv.org/abs/2501.13956 · https://github.com/getzep/graphiti
- Edge et al., *From Local to Global: A Graph RAG Approach* (2024) —
  https://arxiv.org/abs/2404.16130
- Labatut & Bost, *Extraction and Analysis of Fictional Character Networks: A
  Survey* (ACM CSUR 2019) — https://arxiv.org/abs/1907.02704
- Elson, Dames & McKeown, *Extracting Social Networks from Literary Fiction*
  (ACL 2010) — https://aclanthology.org/P10-1015/
- Moretti, *Network Theory, Plot Analysis* (New Left Review 2011) —
  https://newleftreview.org/issues/ii68/articles/franco-moretti-network-theory-plot-analysis.pdf
- Lairgi et al., *iText2KG* (WISE 2024) — https://arxiv.org/abs/2409.03284;
  *ATOM* (EACL 2026 Findings) — https://arxiv.org/abs/2510.22590
- *TG-RAG: RAG Meets Temporal Graphs* (2025) — https://arxiv.org/abs/2510.13590
- Yang et al., *EvolvTrip* (2025) — https://arxiv.org/abs/2506.13641;
  *Narrative World Model* (2026) — https://arxiv.org/abs/2607.05577
- Min & Park, Les Misérables as a growing network —
  https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0226025
- Agarwal et al., *SNA of Alice in Wonderland* (NAACL 2012) —
  https://aclanthology.org/W12-2513/

---

## Track 2 — Artistic temporal-network visualization lineage

### Works the Narrative Observatory draws on

| Mechanism in the Observatory | Lineage |
|---|---|
| Chapter ring as clock face, chords across the interior | Circos (Krzywinski 2009, https://circos.ca/); Jeff Clark's *Novel Views* radial (https://neoformix.com/2013/NovelViews.html) |
| Words/entities migrating inward by "semantic gravity" | TextArc (W. Bradford Paley 2002, http://wbradfordpaley.com/TextArc.html) — frequent words drift toward the center |
| Comet-arc edge births with fading trails | Wind Map (Viégas & Wattenberg 2012, http://hint.fm/projects/wind/); code_swarm (Ogawa 2008) |
| Spring-birth flare + settle | Gource (Caudwell 2009, https://gource.io/) |
| Additive-blend glow on dark ground | Kim Albrecht's *Cosmic Web* (https://kimalbrecht.com/item/cosmic-web/); Nadieh Bremer's *Figures in the Sky* |
| EKG ring amplitude per chapter | Streamgraph/ThemeRiver lineage (Byron & Wattenberg 2008); story-shape work (Vonnegut; Reagan et al. 2016, https://arxiv.org/abs/1606.07772) |
| Scrub-through-time transport | Storyline viz research (Tanahashi & Ma 2012; StoryFlow, Liu et al. 2013); xkcd #657 (https://xkcd.com/657/) |

### Design decisions taken

- **Time → angle** (one revolution = one book) rather than a linear axis: the
  whole narrative becomes a single closed artifact, and structural differences
  read as different "star charts" (Iliad seeds evenly; C&P crowds the first
  sixth; Dune fills in waves).
- **Connection → gravity** (degree pulls stars from rim toward core): makes the
  article's centralization thesis literal — Paul Atreides visibly *falls* to
  the center of Dune; Raskolnikov is born there.
- **Births staggered fractionally within chapters** so stars twinkle in
  individually instead of appearing in per-chapter blocks.
- Self-contained single HTML file (vanilla Canvas 2D, no CDN), drag-and-drop
  loader for real `*_temporal_kg.json` pipeline output, honors
  `prefers-reduced-motion`.

### Artifact

- Interactive page: `narrative-observatory.html` (repo root) — also published
  as a private Claude artifact.
- Demo data is synthetic but narratively anchored (real cast, real first
  appearances, curated key relations; filler entities with Zipf-weighted
  attachment). It is labeled as demo data in the UI; the drag-and-drop loader
  charts genuine extraction output.
