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
# CRYPTONOMICON SCHEMA
# =============================================================================
# A dual-timeline techno-thriller: a 1940s cryptography/war thread and a 1990s
# start-up thread interleaved chapter by chapter. Ciphers and vessels are
# first-class entity types because the plot literally runs on them. The
# relation vocabulary is the one used by the hand-anchored demo constellation
# in build_cryptonomicon_demo.py, so real extraction output lines up with it.

CryptoEntityType = Literal[
    "CHARACTER", "ORGANIZATION", "LOCATION", "TECHNOLOGY", "CIPHER",
    "CONCEPT", "EVENT", "VESSEL", "OBJECT", "RESOURCE",
]

CryptoRelationType = Literal[
    "ADVOCATES", "ALLIES_WITH", "BETRAYS", "BUILDS", "BURIES",
    "CAPTURES", "CAUSES", "CHILD_OF", "COMMANDS", "COMMUNICATES_WITH",
    "CRACKS", "DEPENDS_ON", "DIES_IN", "DISCOVERS", "FAMILY_OF",
    "FIGHTS", "FOUNDS", "FRIEND_OF", "GRANDCHILD_OF", "INTERCEPTS",
    "INVENTS", "INVESTS_IN", "KILLS", "KNOWS", "LEADS",
    "LOCATED_IN", "LOVES", "MARRIES", "MEMBER_OF", "MENTORS",
    "MOURNS", "OPPOSES", "PARENT_OF", "PARTICIPATES_IN", "PARTNERS_WITH",
    "PLOTS_AGAINST", "POSSESSES", "PROTECTS", "RESCUES", "RULES",
    "SALVAGES", "SEEKS", "SERVES", "STUDIES", "SUES",
    "SURVIVES", "TRAVELS_TO", "USES", "WITNESSES", "WRITES",
]

CRYPTO_VALIDATION = [
    ("CHARACTER", "ADVOCATES", "CONCEPT"), ("CHARACTER", "ALLIES_WITH", "CHARACTER"),
    ("CHARACTER", "ALLIES_WITH", "ORGANIZATION"), ("CHARACTER", "BETRAYS", "CHARACTER"),
    ("CHARACTER", "BUILDS", "LOCATION"), ("CHARACTER", "CAPTURES", "CHARACTER"),
    ("CHARACTER", "CAUSES", "EVENT"), ("CHARACTER", "CHILD_OF", "CHARACTER"),
    ("CHARACTER", "COMMANDS", "VESSEL"), ("CHARACTER", "COMMUNICATES_WITH", "CHARACTER"),
    ("CHARACTER", "CRACKS", "CIPHER"), ("CHARACTER", "DIES_IN", "EVENT"),
    ("CHARACTER", "DISCOVERS", "CONCEPT"), ("CHARACTER", "DISCOVERS", "LOCATION"),
    ("CHARACTER", "DISCOVERS", "OBJECT"), ("CHARACTER", "DISCOVERS", "ORGANIZATION"),
    ("CHARACTER", "DISCOVERS", "RESOURCE"), ("CHARACTER", "DISCOVERS", "VESSEL"),
    ("CHARACTER", "FAMILY_OF", "CHARACTER"), ("CHARACTER", "FIGHTS", "CHARACTER"),
    ("CHARACTER", "FIGHTS", "ORGANIZATION"), ("CHARACTER", "FOUNDS", "CONCEPT"),
    ("CHARACTER", "FOUNDS", "LOCATION"), ("CHARACTER", "FOUNDS", "ORGANIZATION"),
    ("CHARACTER", "FRIEND_OF", "CHARACTER"), ("CHARACTER", "GRANDCHILD_OF", "CHARACTER"),
    ("CHARACTER", "INVENTS", "CIPHER"), ("CHARACTER", "INVENTS", "CONCEPT"),
    ("CHARACTER", "INVENTS", "TECHNOLOGY"), ("CHARACTER", "INVESTS_IN", "ORGANIZATION"),
    ("CHARACTER", "KILLS", "CHARACTER"), ("CHARACTER", "KNOWS", "CHARACTER"),
    ("CHARACTER", "LEADS", "EVENT"), ("CHARACTER", "LEADS", "ORGANIZATION"),
    ("CHARACTER", "LOCATED_IN", "LOCATION"), ("CHARACTER", "LOCATED_IN", "VESSEL"),
    ("CHARACTER", "LOVES", "CHARACTER"), ("CHARACTER", "MARRIES", "CHARACTER"),
    ("CHARACTER", "MEMBER_OF", "ORGANIZATION"), ("CHARACTER", "MENTORS", "CHARACTER"),
    ("CHARACTER", "MOURNS", "CHARACTER"), ("CHARACTER", "OPPOSES", "CHARACTER"),
    ("CHARACTER", "OPPOSES", "LOCATION"), ("CHARACTER", "OPPOSES", "ORGANIZATION"),
    ("CHARACTER", "OPPOSES", "TECHNOLOGY"), ("CHARACTER", "PARENT_OF", "CHARACTER"),
    ("CHARACTER", "PARTICIPATES_IN", "EVENT"), ("CHARACTER", "PARTNERS_WITH", "CHARACTER"),
    ("CHARACTER", "PARTNERS_WITH", "ORGANIZATION"), ("CHARACTER", "PLOTS_AGAINST", "ORGANIZATION"),
    ("CHARACTER", "POSSESSES", "OBJECT"), ("CHARACTER", "POSSESSES", "RESOURCE"),
    ("CHARACTER", "PROTECTS", "CIPHER"), ("CHARACTER", "PROTECTS", "CONCEPT"),
    ("CHARACTER", "PROTECTS", "LOCATION"), ("CHARACTER", "RESCUES", "CHARACTER"),
    ("CHARACTER", "RULES", "LOCATION"), ("CHARACTER", "SALVAGES", "RESOURCE"),
    ("CHARACTER", "SALVAGES", "VESSEL"), ("CHARACTER", "SEEKS", "LOCATION"),
    ("CHARACTER", "SEEKS", "OBJECT"), ("CHARACTER", "SEEKS", "ORGANIZATION"),
    ("CHARACTER", "SEEKS", "RESOURCE"), ("CHARACTER", "SEEKS", "VESSEL"),
    ("CHARACTER", "SERVES", "CHARACTER"), ("CHARACTER", "SERVES", "ORGANIZATION"),
    ("CHARACTER", "STUDIES", "CIPHER"), ("CHARACTER", "STUDIES", "CONCEPT"),
    ("CHARACTER", "STUDIES", "TECHNOLOGY"), ("CHARACTER", "SUES", "CHARACTER"),
    ("CHARACTER", "SUES", "ORGANIZATION"), ("CHARACTER", "SURVIVES", "EVENT"),
    ("CHARACTER", "TRAVELS_TO", "LOCATION"), ("CHARACTER", "USES", "CIPHER"),
    ("CHARACTER", "USES", "TECHNOLOGY"), ("CHARACTER", "WITNESSES", "EVENT"),
    ("CHARACTER", "WRITES", "CONCEPT"), ("CHARACTER", "WRITES", "OBJECT"),
    ("CIPHER", "DEPENDS_ON", "CHARACTER"), ("CIPHER", "DEPENDS_ON", "ORGANIZATION"),
    ("CONCEPT", "DEPENDS_ON", "CIPHER"), ("CONCEPT", "DEPENDS_ON", "RESOURCE"),
    ("CONCEPT", "LOCATED_IN", "LOCATION"), ("EVENT", "DEPENDS_ON", "RESOURCE"),
    ("EVENT", "LOCATED_IN", "LOCATION"), ("LOCATION", "CRACKS", "CIPHER"),
    ("LOCATION", "INTERCEPTS", "ORGANIZATION"), ("LOCATION", "LOCATED_IN", "LOCATION"),
    ("LOCATION", "PROTECTS", "CONCEPT"), ("LOCATION", "PROTECTS", "LOCATION"),
    ("OBJECT", "LOCATED_IN", "VESSEL"), ("OBJECT", "POSSESSES", "CIPHER"),
    ("ORGANIZATION", "ALLIES_WITH", "CHARACTER"), ("ORGANIZATION", "BUILDS", "LOCATION"),
    ("ORGANIZATION", "BUILDS", "TECHNOLOGY"), ("ORGANIZATION", "BURIES", "OBJECT"),
    ("ORGANIZATION", "BURIES", "RESOURCE"), ("ORGANIZATION", "CAUSES", "EVENT"),
    ("ORGANIZATION", "DISCOVERS", "OBJECT"), ("ORGANIZATION", "DISCOVERS", "RESOURCE"),
    ("ORGANIZATION", "DISCOVERS", "VESSEL"), ("ORGANIZATION", "FIGHTS", "ORGANIZATION"),
    ("ORGANIZATION", "INTERCEPTS", "CIPHER"), ("ORGANIZATION", "INVENTS", "CONCEPT"),
    ("ORGANIZATION", "INVESTS_IN", "ORGANIZATION"), ("ORGANIZATION", "KILLS", "CHARACTER"),
    ("ORGANIZATION", "LOCATED_IN", "LOCATION"), ("ORGANIZATION", "MEMBER_OF", "ORGANIZATION"),
    ("ORGANIZATION", "OPPOSES", "LOCATION"), ("ORGANIZATION", "OPPOSES", "VESSEL"),
    ("ORGANIZATION", "PARTICIPATES_IN", "EVENT"), ("ORGANIZATION", "PARTNERS_WITH", "CHARACTER"),
    ("ORGANIZATION", "PROTECTS", "CONCEPT"), ("ORGANIZATION", "SALVAGES", "RESOURCE"),
    ("ORGANIZATION", "SERVES", "ORGANIZATION"), ("ORGANIZATION", "TRAVELS_TO", "LOCATION"),
    ("ORGANIZATION", "USES", "CIPHER"), ("ORGANIZATION", "USES", "TECHNOLOGY"),
    ("RESOURCE", "LOCATED_IN", "LOCATION"), ("RESOURCE", "LOCATED_IN", "VESSEL"),
    ("TECHNOLOGY", "CRACKS", "CIPHER"), ("TECHNOLOGY", "INTERCEPTS", "ORGANIZATION"),
    ("TECHNOLOGY", "LOCATED_IN", "LOCATION"), ("VESSEL", "LOCATED_IN", "LOCATION"),
    ("VESSEL", "MEMBER_OF", "ORGANIZATION"), ("VESSEL", "POSSESSES", "CIPHER"),
    ("VESSEL", "POSSESSES", "RESOURCE"),
]

# The novel's chapters are titled, not numbered. The splitter matches a line
# that consists of one title and nothing else (case-insensitive), in any
# order, so it also works on editions that number the chapters differently.
_CRYPTONOMICON_CHAPTERS = (
    "Prologue", "Barrens", "Novus Ordo Seclorum", "Seaweed", "Forays", "Indigo",
    "The Spawn of Onan", "Burn", "Pedestrian", "Guadalcanal", "Galleon", "Nightmare",
    "Londinium", "Corregidor", "Tube", "Meat", "Cycles", "Aloft",
    "Non-disclosure", "Ultra", "Kinakuta", "Qwghlm House", "Electrical Till Corporation", "Crypt",
    "Lizard", "The Castle", "Why", "Retrograde Maneuver", "Huffduff", "Pages",
    "Ram", "Diligence", "Spearhead", "Morphium", "Suit", "Cracker",
    "Sultan", "Skipping", "Mugs", "Yamamoto", "Antaeus", "Phreaking",
    "Afloat", "Shinola", "Hostilities", "Funkspiel", "Heap", "Seeky",
    "Cannibals", "Wreck", "Santa Monica", "Outpost", "Meteor", "Lavender Rose",
    "Brisbane", "D\u00f6nitz", "Crunch", "Girl", "Conspiracy", "Hoard",
    "Rocket", "Courting", "I.N.R.I.", "California", "Organ", "Home",
    "Bundok", "Computer", "Caravan", "The General", "Origin", "Golgotha",
    "Seattle", "Rock", "The Most Cigarettes", "Christmas 1944", "Pulse", "Buddha",
    "Pontifex", "Glory", "The Primary", "Deluge", "Bust", "The Battle of Manila",
    "Captivity", "Glamour", "Wisdom", "Fall", "Metis", "Slaves",
    "Arethusa", "The Basement", "Akihabara", "Project X", "Landfall", "Goto-sama",
    "R.I.P.", "Return", "Cribs", "Cayuse", "Black Chamber", "Passage",
    "Liquidity",
)


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
    "cryptonomicon": LiterarySchema(
        name="Cryptonomicon",
        work_key="cryptonomicon",
        entity_types=CryptoEntityType,
        relation_types=CryptoRelationType,
        validation_schema=CRYPTO_VALIDATION,
        primary_structure="networked",
        narrative_focus="systems",
        chapter_pattern=(
            r"^\s*(?i:" + "|".join(re.escape(t) for t in _CRYPTONOMICON_CHAPTERS) + r")\s*$"
        ),
        chapter_label="Chapter",
        expected_chapters=103,
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
