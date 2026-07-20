"""
Temporal Knowledge Graph Extraction Pipeline

Extracts knowledge graphs chapter-by-chapter from literary texts,
preserving temporal metadata: when entities first appear, when
relationships form, and how the graph evolves across the narrative.

Usage:
    # Extract with chapter splitting
    python temporal_extraction.py iliad --file texts/iliad.txt -o output/

    # Use sample text for testing
    python temporal_extraction.py iliad --sample -o output/
"""

import os
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from llama_index.core import Document, Settings
from llama_index.core.indices.property_graph import PropertyGraphIndex
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.graph_stores.types import EntityNode, Relation
from llama_index.core.graph_stores import SimplePropertyGraphStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from schemas import get_schema, LiterarySchema

load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class TemporalExtractionConfig:
    """Configuration for temporal KG extraction."""
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.0
    chunk_size: int = 1200
    chunk_overlap: int = 200
    max_triplets_per_chunk: int = 20
    num_workers: int = 4
    min_chapter_length: int = 500  # Skip chapters shorter than this


# =============================================================================
# Chapter Splitter
# =============================================================================

@dataclass
class Chapter:
    """A narrative chapter or section with metadata."""
    index: int
    label: str          # e.g., "Book I", "Part III", "Section 5"
    text: str
    char_start: int     # Character offset in original text
    char_end: int
    word_count: int


def split_into_chapters(
    text: str,
    schema: LiterarySchema,
    min_length: int = 500,
) -> list[Chapter]:
    """
    Split a literary text into chapters based on the schema's pattern.

    Uses regex-based chapter detection with fallback to equal-sized
    segments if no chapter markers are found. Patterns are matched with
    re.MULTILINE only — case-sensitive, so heading words appearing in
    running prose ("the book I gave him") don't create false boundaries.
    Schemas needing case-insensitive parts use scoped (?i:...) groups.

    Args:
        text: Complete text of the literary work
        schema: Literary schema with chapter_pattern
        min_length: Minimum chapter length in characters

    Returns:
        List of Chapter objects
    """
    pattern = schema.chapter_pattern
    label = schema.chapter_label

    # Find all chapter boundaries
    matches = list(re.finditer(pattern, text, re.MULTILINE))

    if len(matches) >= 3:
        # Use detected chapter markers
        chapters = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chapter_text = text[start:end].strip()

            if len(chapter_text) < min_length:
                continue

            # Extract chapter identifier from match
            chapter_id = match.group(1) if match.lastindex else str(i + 1)
            chapters.append(Chapter(
                index=len(chapters),
                label=f"{label} {chapter_id}",
                text=chapter_text,
                char_start=start,
                char_end=end,
                word_count=len(chapter_text.split()),
            ))
        return chapters

    # Fallback: split into roughly equal segments
    target_segments = max(schema.expected_chapters, 6)
    segment_size = len(text) // target_segments

    chapters = []
    for i in range(target_segments):
        start = i * segment_size
        end = (i + 1) * segment_size if i + 1 < target_segments else len(text)

        # Try to break at paragraph boundaries
        if end < len(text):
            para_break = text.rfind("\n\n", start + segment_size // 2, end + segment_size // 2)
            if para_break > start:
                end = para_break

        chapter_text = text[start:end].strip()
        if len(chapter_text) < min_length:
            continue

        chapters.append(Chapter(
            index=len(chapters),
            label=f"{label} {len(chapters) + 1}",
            text=chapter_text,
            char_start=start,
            char_end=end,
            word_count=len(chapter_text.split()),
        ))

    return chapters


# =============================================================================
# Temporal Entity & Relation Tracking
# =============================================================================

@dataclass
class TemporalEntity:
    """An entity with temporal metadata tracking its narrative lifetime."""
    id: str
    name: str
    label: str                  # Entity type
    first_appearance: int       # Chapter index where first seen
    appearances: list = field(default_factory=list)  # All chapter indices
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label,
            "first_appearance": self.first_appearance,
            "appearances": sorted(set(self.appearances)),
            "total_appearances": len(set(self.appearances)),
            "properties": self.properties,
        }


@dataclass
class TemporalRelation:
    """A relationship with temporal metadata."""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    label: str
    first_appearance: int
    appearances: list = field(default_factory=list)
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "label": self.label,
            "first_appearance": self.first_appearance,
            "appearances": sorted(set(self.appearances)),
            "total_appearances": len(set(self.appearances)),
            "properties": self.properties,
        }


# =============================================================================
# Temporal KG Builder
# =============================================================================

class TemporalKGBuilder:
    """
    Builds a temporal knowledge graph by extracting from each chapter
    and tracking when entities and relationships first appear.

    A single builder can be reused across works: extract_temporal()
    resets all per-work state at the start of each run.
    """

    def __init__(self, config: TemporalExtractionConfig = None):
        self.config = config or TemporalExtractionConfig()
        self.entities: dict[str, TemporalEntity] = {}
        self.relations: list[TemporalRelation] = []
        self.chapter_snapshots: list[dict] = []  # Metrics per chapter
        # Fast lookup for relation dedup: (source_id, target_id, label) -> TemporalRelation
        self._relation_index: dict[tuple, TemporalRelation] = {}
        self._setup_llm()

    def _setup_llm(self):
        """Configure LLM settings."""
        Settings.llm = OpenAI(
            model=self.config.llm_model,
            temperature=self.config.temperature,
        )
        # Embeddings are configured but not used during extraction —
        # PropertyGraphIndex is built with embed_kg_nodes=False since we
        # only read the graph structure, never query the index.
        Settings.embed_model = OpenAIEmbedding(model=self.config.embedding_model)
        Settings.chunk_size = self.config.chunk_size
        Settings.chunk_overlap = self.config.chunk_overlap

    def _normalize_id(self, name: str, label: str) -> str:
        """
        Create a consistent entity ID from name and type.

        Unicode-aware: names in any script (Cyrillic, CJK, accented Latin)
        keep their letters, so distinct non-ASCII names don't collapse
        into a single ID.
        """
        normalized = unicodedata.normalize("NFKC", name).casefold().strip()
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\s+", "_", normalized)
        if not normalized:
            # Name was entirely punctuation/symbols — fall back to raw name
            normalized = name.strip()
        return f"{label.lower()}_{normalized}"

    def _create_extractor(self, schema: LiterarySchema) -> SchemaLLMPathExtractor:
        """Create schema-guided extractor for a literary work."""
        return SchemaLLMPathExtractor(
            llm=Settings.llm,
            possible_entities=schema.entity_types,
            possible_relations=schema.relation_types,
            kg_validation_schema=schema.validation_schema,
            strict=True,
            num_workers=self.config.num_workers,
            max_triplets_per_chunk=self.config.max_triplets_per_chunk,
        )

    def _extract_chapter(
        self,
        chapter: Chapter,
        schema: LiterarySchema,
    ) -> tuple[list[EntityNode], list[Relation]]:
        """
        Extract KG from a single chapter.

        Returns:
            Tuple of (entity_nodes, relations)
        """
        document = Document(
            text=chapter.text,
            metadata={
                "chapter_index": chapter.index,
                "chapter_label": chapter.label,
            }
        )

        memory_store = SimplePropertyGraphStore()
        kg_extractor = self._create_extractor(schema)

        # Build index with extraction. embed_kg_nodes=False: we only read
        # the graph store afterwards, so paying for node embeddings would
        # be pure waste.
        PropertyGraphIndex.from_documents(
            documents=[document],
            kg_extractors=[kg_extractor],
            property_graph_store=memory_store,
            embed_kg_nodes=False,
            show_progress=False,
        )

        # Filter to entity nodes only
        all_nodes = list(memory_store.graph.nodes.values())
        nodes = [n for n in all_nodes if isinstance(n, EntityNode)]
        entity_ids = {n.id for n in nodes}

        all_relations = list(memory_store.graph.relations.values())
        relations = [
            r for r in all_relations
            if r.source_id in entity_ids and r.target_id in entity_ids
        ]

        return nodes, relations

    def _merge_chapter_results(
        self,
        nodes: list[EntityNode],
        relations: list[Relation],
        chapter_idx: int,
    ):
        """
        Merge a chapter's extraction results into the temporal graph.

        Updates entity first_appearance and appearances lists.
        """
        # Merge entities
        for node in nodes:
            eid = self._normalize_id(node.name, node.label)
            if eid not in self.entities:
                self.entities[eid] = TemporalEntity(
                    id=eid,
                    name=node.name,
                    label=node.label,
                    first_appearance=chapter_idx,
                    appearances=[chapter_idx],
                    properties=node.properties,
                )
            else:
                self.entities[eid].appearances.append(chapter_idx)
                if node.properties:
                    self.entities[eid].properties.update(node.properties)

        # Build entity name -> normalized ID mapping for relation merging
        name_to_id = {}
        node_by_id = {}
        for node in nodes:
            name_to_id[node.id] = self._normalize_id(node.name, node.label)
            name_to_id[node.name] = self._normalize_id(node.name, node.label)
            node_by_id[node.id] = node

        # Merge relations
        for rel in relations:
            source_eid = name_to_id.get(rel.source_id, rel.source_id)
            target_eid = name_to_id.get(rel.target_id, rel.target_id)

            source_node = node_by_id.get(rel.source_id)
            target_node = node_by_id.get(rel.target_id)
            source_name = source_node.name if source_node else rel.source_id
            target_name = target_node.name if target_node else rel.target_id

            key = (source_eid, target_eid, rel.label)
            existing_rel = self._relation_index.get(key)
            if existing_rel is not None:
                existing_rel.appearances.append(chapter_idx)
            else:
                new_rel = TemporalRelation(
                    source_id=source_eid,
                    source_name=source_name,
                    target_id=target_eid,
                    target_name=target_name,
                    label=rel.label,
                    first_appearance=chapter_idx,
                    appearances=[chapter_idx],
                    properties=rel.properties,
                )
                self.relations.append(new_rel)
                self._relation_index[key] = new_rel

    def _compute_chapter_snapshot(self, chapter_idx: int, chapter: Chapter) -> dict:
        """Compute cumulative graph metrics at a given chapter."""
        # Cumulative counts
        entities_so_far = [
            e for e in self.entities.values()
            if e.first_appearance <= chapter_idx
        ]
        relations_so_far = [
            r for r in self.relations
            if r.first_appearance <= chapter_idx
        ]

        # New in this chapter
        new_entities = [e for e in entities_so_far if e.first_appearance == chapter_idx]
        new_relations = [r for r in relations_so_far if r.first_appearance == chapter_idx]

        # Active in this chapter (appeared in this specific chapter)
        active_entities = [
            e for e in self.entities.values()
            if chapter_idx in e.appearances
        ]
        active_relations = [
            r for r in self.relations
            if chapter_idx in r.appearances
        ]

        # Entity type distribution (cumulative)
        type_dist = {}
        for e in entities_so_far:
            type_dist[e.label] = type_dist.get(e.label, 0) + 1

        # Relation type distribution (cumulative)
        rel_dist = {}
        for r in relations_so_far:
            rel_dist[r.label] = rel_dist.get(r.label, 0) + 1

        # Degree centrality for top entities
        degree_map = {}
        for r in relations_so_far:
            degree_map[r.source_id] = degree_map.get(r.source_id, 0) + 1
            degree_map[r.target_id] = degree_map.get(r.target_id, 0) + 1

        top_entities = sorted(degree_map.items(), key=lambda x: -x[1])[:10]
        top_hubs = []
        for eid, degree in top_entities:
            if eid in self.entities:
                e = self.entities[eid]
                top_hubs.append({
                    "name": e.name,
                    "label": e.label,
                    "degree": degree,
                })

        return {
            "chapter_index": chapter_idx,
            "chapter_label": chapter.label,
            "word_count": chapter.word_count,

            # Cumulative metrics
            "cumulative_entities": len(entities_so_far),
            "cumulative_relations": len(relations_so_far),
            "cumulative_entity_types": len(type_dist),
            "cumulative_relation_types": len(rel_dist),

            # Chapter-specific metrics
            "new_entities": len(new_entities),
            "new_relations": len(new_relations),
            "active_entities": len(active_entities),
            "active_relations": len(active_relations),

            # Density (edges / possible edges)
            "density": (
                len(relations_so_far) / (len(entities_so_far) * (len(entities_so_far) - 1))
                if len(entities_so_far) > 1 else 0.0
            ),

            # Distributions
            "entity_type_distribution": type_dist,
            "relation_type_distribution": rel_dist,
            "top_hubs": top_hubs,

            # New entity names for tracking
            "new_entity_names": [
                {"name": e.name, "label": e.label} for e in new_entities
            ],
            "new_relation_summary": [
                {"source": r.source_name, "relation": r.label, "target": r.target_name}
                for r in new_relations[:20]  # Cap at 20 for readability
            ],
        }

    def extract_temporal(
        self,
        text: str,
        work_key: str,
        max_chapters: int = None,
    ) -> dict:
        """
        Main extraction pipeline: split text into chapters, extract KG
        from each chapter, and track temporal evolution.

        Args:
            text: Complete literary text
            work_key: Schema identifier (iliad, crime, dune, generic)
            max_chapters: Optional cap on chapters to process

        Returns:
            Complete temporal extraction result as dict
        """
        schema = get_schema(work_key)

        # Reset per-work state so a reused builder never merges two books
        self.entities = {}
        self.relations = []
        self.chapter_snapshots = []
        self._relation_index = {}

        print(f"\n{'='*60}")
        print(f"TEMPORAL KG EXTRACTION: {schema.name}")
        print(f"Text length: {len(text):,} characters")
        print(f"{'='*60}\n")

        # Step 1: Split into chapters
        chapters = split_into_chapters(text, schema, self.config.min_chapter_length)
        if max_chapters:
            chapters = chapters[:max_chapters]

        print(f"Found {len(chapters)} chapters/sections")
        for ch in chapters:
            print(f"  {ch.label}: {ch.word_count:,} words")

        # Step 2: Extract from each chapter
        for chapter in chapters:
            print(f"\nExtracting: {chapter.label} ({chapter.word_count:,} words)...")

            try:
                nodes, relations = self._extract_chapter(chapter, schema)
                print(f"  Found {len(nodes)} entities, {len(relations)} relations")

                # Merge into temporal graph
                self._merge_chapter_results(nodes, relations, chapter.index)

                # Compute snapshot
                snapshot = self._compute_chapter_snapshot(chapter.index, chapter)
                self.chapter_snapshots.append(snapshot)

                print(f"  Cumulative: {snapshot['cumulative_entities']} entities, "
                      f"{snapshot['cumulative_relations']} relations")
                print(f"  New: +{snapshot['new_entities']} entities, "
                      f"+{snapshot['new_relations']} relations")

            except Exception as e:
                print(f"  ERROR extracting {chapter.label}: {e}")
                # Still record a snapshot with whatever we have
                snapshot = self._compute_chapter_snapshot(chapter.index, chapter)
                self.chapter_snapshots.append(snapshot)

        # Step 3: Build final result
        result = {
            "metadata": {
                "work_key": work_key,
                "work_name": schema.name,
                "extraction_model": self.config.llm_model,
                "total_chapters": len(chapters),
                "total_entities": len(self.entities),
                "total_relations": len(self.relations),
                "extracted_at": datetime.now().isoformat(),
                "chapter_label": schema.chapter_label,
            },
            "chapters": [
                {
                    "index": ch.index,
                    "label": ch.label,
                    "word_count": ch.word_count,
                }
                for ch in chapters
            ],
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations],
            "timeline": self.chapter_snapshots,
        }

        print(f"\n{'='*60}")
        print(f"EXTRACTION COMPLETE")
        print(f"  Chapters processed: {len(chapters)}")
        print(f"  Total entities: {len(self.entities)}")
        print(f"  Total relations: {len(self.relations)}")
        print(f"{'='*60}\n")

        return result


# =============================================================================
# Serialization
# =============================================================================

def save_temporal_result(result: dict, output_path: str) -> str:
    """Save temporal extraction result to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved temporal KG to: {path}")
    return str(path)


def load_temporal_result(json_path: str) -> dict:
    """Load temporal extraction result from JSON."""
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"Loaded temporal KG: {data['metadata']['work_name']} "
          f"({data['metadata']['total_entities']} entities, "
          f"{data['metadata']['total_relations']} relations)")
    return data


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract temporal knowledge graphs from literary works"
    )
    parser.add_argument(
        "work_key",
        choices=["iliad", "crime", "dune", "generic"],
        help="Schema to use: a preset (iliad/crime/dune) or 'generic' for any chaptered text"
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to text file"
    )
    parser.add_argument(
        "--output", "-o",
        default="output/",
        help="Output directory"
    )
    parser.add_argument(
        "--max-chapters",
        type=int,
        help="Limit number of chapters to process (for testing)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model to use"
    )
    parser.add_argument(
        "--name",
        help="Output filename prefix (default: work_key). "
             "Use this to give a custom name when running with --work-key generic."
    )

    args = parser.parse_args()

    config = TemporalExtractionConfig(llm_model=args.model)
    builder = TemporalKGBuilder(config)

    # Load text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        print("ERROR: --file is required. Provide path to the text file.")
        exit(1)

    # Run extraction
    result = builder.extract_temporal(
        text, args.work_key, max_chapters=args.max_chapters
    )

    # Save
    name_prefix = args.name or args.work_key
    output_path = Path(args.output) / f"{name_prefix}_temporal_kg.json"
    save_temporal_result(result, str(output_path))
