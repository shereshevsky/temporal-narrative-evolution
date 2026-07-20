"""
Domain-Specific Schemas for Temporal Literary KG Extraction

Reuses the schema definitions from the literature-kg-comparison article,
extended with chapter/section splitting configuration for each work.
"""

from typing import Literal
from dataclasses import dataclass, field
import re


# =============================================================================
# ILIAD SCHEMA
# =============================================================================

IliadEntityType = Literal[
    "HERO", "DEITY", "MORTAL", "ARMY",
    "LOCATION", "ARTIFACT", "BATTLE",
]

IliadRelationType = Literal[
    "FIGHTS", "KILLS", "WOUNDS", "DEFEATS", "CHALLENGES",
    "FAVORS", "OPPOSES", "INVOKES", "GRANTS_POWER",
    "COMMANDS", "SERVES", "ALLIES_WITH", "RIVALS",
    "FATHER_OF", "MOTHER_OF", "SON_OF", "MARRIED_TO",
    "DISHONORS", "AVENGES", "MOURNS",
    "LOCATED_IN", "POSSESSES", "PARTICIPATES_IN", "CAUSES",
]

ILIAD_VALIDATION = [
    ("HERO", "FIGHTS", "HERO"), ("HERO", "KILLS", "HERO"),
    ("HERO", "KILLS", "MORTAL"), ("HERO", "WOUNDS", "HERO"),
    ("HERO", "COMMANDS", "ARMY"), ("HERO", "SERVES", "HERO"),
    ("HERO", "ALLIES_WITH", "HERO"), ("HERO", "RIVALS", "HERO"),
    ("HERO", "POSSESSES", "ARTIFACT"), ("HERO", "PARTICIPATES_IN", "BATTLE"),
    ("HERO", "LOCATED_IN", "LOCATION"), ("HERO", "INVOKES", "DEITY"),
    ("HERO", "AVENGES", "HERO"), ("HERO", "MOURNS", "HERO"),
    ("DEITY", "FAVORS", "HERO"), ("DEITY", "FAVORS", "ARMY"),
    ("DEITY", "OPPOSES", "HERO"), ("DEITY", "OPPOSES", "ARMY"),
    ("DEITY", "GRANTS_POWER", "HERO"), ("DEITY", "CAUSES", "BATTLE"),
    ("DEITY", "FATHER_OF", "HERO"), ("DEITY", "MOTHER_OF", "HERO"),
    ("DEITY", "MARRIED_TO", "DEITY"), ("DEITY", "LOCATED_IN", "LOCATION"),
    ("ARMY", "FIGHTS", "ARMY"), ("ARMY", "LOCATED_IN", "LOCATION"),
    ("BATTLE", "LOCATED_IN", "LOCATION"),
    ("HERO", "FATHER_OF", "HERO"), ("HERO", "SON_OF", "HERO"),
    ("HERO", "SON_OF", "DEITY"), ("HERO", "MARRIED_TO", "HERO"),
    ("HERO", "DISHONORS", "HERO"),
]


# =============================================================================
# CRIME AND PUNISHMENT SCHEMA
# =============================================================================

CrimeEntityType = Literal[
    "PROTAGONIST", "CHARACTER", "PSYCHOLOGICAL_STATE",
    "LOCATION", "INSTITUTION", "IDEA", "EVENT",
]

CrimeRelationType = Literal[
    "EXPERIENCES", "TRIGGERS", "OBSESSES_OVER", "FEARS", "LOVES", "RESENTS",
    "SUSPECTS", "BELIEVES_IN", "REJECTS", "CONFESSES_TO", "REDEEMS",
    "CORRUPTS", "JUDGES", "FAMILY_OF", "FRIEND_OF", "LANDLORD_OF",
    "INVESTIGATES", "MANIPULATES", "SUPPORTS", "MURDERS", "WITNESSES",
    "CONCEALS", "REVEALS", "LIVES_IN", "VISITS", "FLEES_TO",
]

CRIME_VALIDATION = [
    ("PROTAGONIST", "EXPERIENCES", "PSYCHOLOGICAL_STATE"),
    ("PROTAGONIST", "BELIEVES_IN", "IDEA"),
    ("PROTAGONIST", "REJECTS", "IDEA"),
    ("PROTAGONIST", "MURDERS", "CHARACTER"),
    ("PROTAGONIST", "LOVES", "CHARACTER"),
    ("PROTAGONIST", "FEARS", "CHARACTER"),
    ("PROTAGONIST", "CONFESSES_TO", "CHARACTER"),
    ("PROTAGONIST", "LIVES_IN", "LOCATION"),
    ("PROTAGONIST", "VISITS", "LOCATION"),
    ("PROTAGONIST", "FLEES_TO", "LOCATION"),
    ("PROTAGONIST", "OBSESSES_OVER", "EVENT"),
    ("CHARACTER", "EXPERIENCES", "PSYCHOLOGICAL_STATE"),
    ("CHARACTER", "LOVES", "PROTAGONIST"),
    ("CHARACTER", "LOVES", "CHARACTER"),
    ("CHARACTER", "SUPPORTS", "PROTAGONIST"),
    ("CHARACTER", "INVESTIGATES", "PROTAGONIST"),
    ("CHARACTER", "SUSPECTS", "PROTAGONIST"),
    ("CHARACTER", "MANIPULATES", "CHARACTER"),
    ("CHARACTER", "FAMILY_OF", "PROTAGONIST"),
    ("CHARACTER", "FAMILY_OF", "CHARACTER"),
    ("CHARACTER", "FRIEND_OF", "PROTAGONIST"),
    ("CHARACTER", "FRIEND_OF", "CHARACTER"),
    ("CHARACTER", "LIVES_IN", "LOCATION"),
    ("CHARACTER", "REDEEMS", "PROTAGONIST"),
    ("CHARACTER", "JUDGES", "PROTAGONIST"),
    ("EVENT", "TRIGGERS", "PSYCHOLOGICAL_STATE"),
    ("INSTITUTION", "INVESTIGATES", "PROTAGONIST"),
    ("IDEA", "CORRUPTS", "PROTAGONIST"),
]


# =============================================================================
# DUNE SCHEMA
# =============================================================================

DuneEntityType = Literal[
    "CHARACTER", "FACTION", "LOCATION", "RESOURCE",
    "TECHNOLOGY", "CREATURE", "CONCEPT", "RITUAL",
    "PROPHECY", "TITLE",
]

DuneRelationType = Literal[
    "LEADS", "SERVES", "ALLIES_WITH", "BETRAYS", "OPPOSES",
    "RULES", "PLOTS_AGAINST", "PARENT_OF", "CHILD_OF",
    "BRED_BY", "CONTROLS", "DEPENDS_ON", "MONOPOLIZES",
    "POSSESSES_ABILITY", "TRAINS_IN", "AWAKENS_TO", "PROPHESIES",
    "INHABITS", "PRODUCES", "TRANSFORMS", "WORSHIPS",
    "FULFILLS", "PERFORMS", "HOLDS_TITLE",
    "ASSASSINATES", "WAGES_WAR", "DEFEATS",
]

DUNE_VALIDATION = [
    ("CHARACTER", "LEADS", "FACTION"), ("CHARACTER", "SERVES", "FACTION"),
    ("CHARACTER", "SERVES", "CHARACTER"), ("CHARACTER", "ALLIES_WITH", "CHARACTER"),
    ("CHARACTER", "BETRAYS", "CHARACTER"), ("CHARACTER", "BETRAYS", "FACTION"),
    ("CHARACTER", "OPPOSES", "CHARACTER"), ("CHARACTER", "PARENT_OF", "CHARACTER"),
    ("CHARACTER", "CHILD_OF", "CHARACTER"), ("CHARACTER", "BRED_BY", "FACTION"),
    ("CHARACTER", "POSSESSES_ABILITY", "CONCEPT"), ("CHARACTER", "AWAKENS_TO", "CONCEPT"),
    ("CHARACTER", "PERFORMS", "RITUAL"), ("CHARACTER", "FULFILLS", "PROPHECY"),
    ("CHARACTER", "PROPHESIES", "PROPHECY"), ("CHARACTER", "HOLDS_TITLE", "TITLE"),
    ("CHARACTER", "ASSASSINATES", "CHARACTER"), ("CHARACTER", "RULES", "LOCATION"),
    ("CHARACTER", "INHABITS", "LOCATION"), ("FACTION", "CONTROLS", "RESOURCE"),
    ("FACTION", "CONTROLS", "LOCATION"), ("FACTION", "DEPENDS_ON", "RESOURCE"),
    ("FACTION", "OPPOSES", "FACTION"), ("FACTION", "ALLIES_WITH", "FACTION"),
    ("FACTION", "PLOTS_AGAINST", "FACTION"), ("FACTION", "WAGES_WAR", "FACTION"),
    ("CREATURE", "INHABITS", "LOCATION"), ("CREATURE", "PRODUCES", "RESOURCE"),
    ("RESOURCE", "TRANSFORMS", "CHARACTER"), ("RITUAL", "TRANSFORMS", "CHARACTER"),
    ("LOCATION", "PRODUCES", "RESOURCE"),
]


# =============================================================================
# GENERIC SCHEMA (works on any chaptered text)
# =============================================================================

GenericEntityType = Literal[
    "CHARACTER", "LOCATION", "ORGANIZATION",
    "EVENT", "OBJECT", "CONCEPT",
]

GenericRelationType = Literal[
    "KNOWS", "INTERACTS_WITH", "ALLIES_WITH", "OPPOSES",
    "PARENT_OF", "CHILD_OF", "MARRIED_TO",
    "LEADS", "MEMBER_OF", "SERVES",
    "LOCATED_IN", "TRAVELS_TO", "INHABITS",
    "OWNS", "POSSESSES", "USES",
    "CAUSES", "PARTICIPATES_IN", "WITNESSES",
    "BELIEVES_IN", "DISCOVERS", "TRANSFORMS",
]

GENERIC_VALIDATION = [
    ("CHARACTER", "KNOWS", "CHARACTER"),
    ("CHARACTER", "INTERACTS_WITH", "CHARACTER"),
    ("CHARACTER", "ALLIES_WITH", "CHARACTER"),
    ("CHARACTER", "OPPOSES", "CHARACTER"),
    ("CHARACTER", "PARENT_OF", "CHARACTER"),
    ("CHARACTER", "CHILD_OF", "CHARACTER"),
    ("CHARACTER", "MARRIED_TO", "CHARACTER"),
    ("CHARACTER", "LEADS", "ORGANIZATION"),
    ("CHARACTER", "MEMBER_OF", "ORGANIZATION"),
    ("CHARACTER", "SERVES", "CHARACTER"),
    ("CHARACTER", "SERVES", "ORGANIZATION"),
    ("CHARACTER", "LOCATED_IN", "LOCATION"),
    ("CHARACTER", "TRAVELS_TO", "LOCATION"),
    ("CHARACTER", "INHABITS", "LOCATION"),
    ("CHARACTER", "OWNS", "OBJECT"),
    ("CHARACTER", "POSSESSES", "OBJECT"),
    ("CHARACTER", "USES", "OBJECT"),
    ("CHARACTER", "PARTICIPATES_IN", "EVENT"),
    ("CHARACTER", "WITNESSES", "EVENT"),
    ("CHARACTER", "BELIEVES_IN", "CONCEPT"),
    ("CHARACTER", "DISCOVERS", "CONCEPT"),
    ("CHARACTER", "DISCOVERS", "OBJECT"),
    ("ORGANIZATION", "OPPOSES", "ORGANIZATION"),
    ("ORGANIZATION", "ALLIES_WITH", "ORGANIZATION"),
    ("ORGANIZATION", "LOCATED_IN", "LOCATION"),
    ("ORGANIZATION", "OWNS", "OBJECT"),
    ("EVENT", "LOCATED_IN", "LOCATION"),
    ("EVENT", "CAUSES", "EVENT"),
    ("CONCEPT", "TRANSFORMS", "CHARACTER"),
    ("OBJECT", "LOCATED_IN", "LOCATION"),
]

# Spelled-out chapter numbers, 1–59 ("One" … "Fifty-Nine"). Longer words
# come first so the regex engine prefers "Seventeen" over "Seven".
_SPELLED_NUMBER = (
    "Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|"
    "Nineteen|"
    "(?:Twenty|Thirty|Forty|Fifty)"
    "(?:-(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine))?|"
    "One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten"
)


# =============================================================================
# Schema Registry
# =============================================================================

@dataclass
class LiterarySchema:
    """Complete schema for a literary work, including temporal config."""
    name: str
    work_key: str
    entity_types: type
    relation_types: type
    validation_schema: list
    primary_structure: str      # hierarchical, radial, networked
    narrative_focus: str        # external_action, internal_psychology, systems
    chapter_pattern: str        # regex to split into chapters; matched with
                                # re.MULTILINE only (case-sensitive). Anchor
                                # headings with ^ and use (?i:...) for any
                                # case-insensitive parts, so that words like
                                # "book"/"part" in running prose don't create
                                # false chapter boundaries.
    chapter_label: str          # what to call divisions (Book, Part, Chapter)
    expected_chapters: int      # approximate number of divisions


SCHEMA_REGISTRY = {
    "iliad": LiterarySchema(
        name="The Iliad",
        work_key="iliad",
        entity_types=IliadEntityType,
        relation_types=IliadRelationType,
        validation_schema=ILIAD_VALIDATION,
        primary_structure="hierarchical",
        narrative_focus="external_action",
        chapter_pattern=r"^\s*BOOK\s+([IVXLC]+)\b",
        chapter_label="Book",
        expected_chapters=24,
    ),
    "crime": LiterarySchema(
        name="Crime and Punishment",
        work_key="crime",
        entity_types=CrimeEntityType,
        relation_types=CrimeRelationType,
        validation_schema=CRIME_VALIDATION,
        primary_structure="radial",
        narrative_focus="internal_psychology",
        chapter_pattern=r"^\s*PART\s+([IVXLC]+)\b",
        chapter_label="Part",
        expected_chapters=6,
    ),
    "dune": LiterarySchema(
        name="Dune",
        work_key="dune",
        entity_types=DuneEntityType,
        relation_types=DuneRelationType,
        validation_schema=DUNE_VALIDATION,
        primary_structure="networked",
        narrative_focus="systems",
        chapter_pattern=r"^={3,}|^\s*BOOK\s+(ONE|TWO|THREE)\b",
        chapter_label="Section",
        expected_chapters=48,
    ),
    "generic": LiterarySchema(
        name="Generic Narrative",
        work_key="generic",
        entity_types=GenericEntityType,
        relation_types=GenericRelationType,
        validation_schema=GENERIC_VALIDATION,
        primary_structure="networked",
        narrative_focus="external_action",
        # Match common chapter headings at line start: "Chapter 1",
        # "CHAPTER VII", "Chapter Twenty-Three", "Chapitre IX", in any case.
        chapter_pattern=(
            r"^\s*(?i:CHAPTER|CHAPITRE)\s+"
            rf"([IVXLC]+|\d+|(?i:{_SPELLED_NUMBER}))\b"
        ),
        chapter_label="Chapter",
        expected_chapters=20,
    ),
}


def get_schema(work_key: str) -> LiterarySchema:
    """Retrieve schema by work key."""
    if work_key not in SCHEMA_REGISTRY:
        raise ValueError(f"Unknown work: {work_key}. Available: {list(SCHEMA_REGISTRY.keys())}")
    return SCHEMA_REGISTRY[work_key]


def get_all_work_keys() -> list[str]:
    return list(SCHEMA_REGISTRY.keys())
