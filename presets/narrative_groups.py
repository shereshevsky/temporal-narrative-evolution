"""
Hand-curated narrative-chart presets for The Iliad, Crime and Punishment,
and Dune.

The "narrative chart" (XKCD-style character-flow chart) needs to know which
characters are *together* at each point in the story so their lines can
converge and diverge. The graph extraction tells us *who* is connected, but
not the dramatic clustering of scenes — for that we need narrative knowledge.

When figures.py is invoked with --preset <work_key>, these dicts are used to
lay out the narrative chart. Without --preset, figures.py auto-derives groups
from the temporal graph (see _auto_derive_groups in figures.py).

Format
------
NARRATIVE_CHARACTERS[work_key]: list of (canonical_name, hex_color) tuples
    The characters the chart will track, in the order they should appear.

NARRATIVE_GROUPS[work_key]: dict mapping narrative_progress (0.0–1.0) to a
    list of sets of character names. Each set is a "scene cluster" — characters
    in the same set converge at that point in the story.

EVENT_ANNOTATIONS[work_key]: dict mapping narrative_progress (0.0–1.0) to a
    short label (newlines allowed) for vertical event markers.
"""

NARRATIVE_CHARACTERS = {
    "iliad": [
        ("Achilles",    "#DC143C"),
        ("Hector",      "#B22222"),
        ("Agamemnon",   "#CD853F"),
        ("Patroclus",   "#FF6347"),
        ("Ajax",        "#8B4513"),
        ("Ulysses",     "#D2691E"),
        ("Jove",        "#FFD700"),
        ("Tydides",     "#FF8C00"),
        ("Paris",       "#A0522D"),
        ("Nestor",      "#808080"),
    ],
    "crime": [
        ("Raskolnikov",            "#1E3A5F"),
        ("Sonia",                  "#5C8DB8"),
        ("Razumihin",              "#2A9D8F"),
        ("Porfiry Petrovitch",     "#9B2335"),
        ("Svidrigaïlov",           "#264653"),
        ("Dounia",                 "#E9C46A"),
        ("Pulcheria Alexandrovna", "#A8DADC"),
        ("Marmeladov",             "#6B4984"),
        ("Katerina Ivanovna",      "#CD853F"),
        ("Pyotr Petrovitch",       "#808080"),
    ],
    "dune": [
        ("Paul Atreides",            "#4169E1"),
        ("Lady Jessica",             "#9370DB"),
        ("Duke Leto Atreides",       "#2F4F4F"),
        ("Baron Vladimir Harkonnen", "#8B0000"),
        ("Stilgar",                  "#DAA520"),
        ("Kynes",                    "#556B2F"),
        ("Gurney Halleck",           "#4682B4"),
        ("Chani",                    "#E9C46A"),
        ("Feyd-Rautha",              "#DC143C"),
        ("Alia",                     "#9932CC"),
    ],
}


ILIAD_GROUPS = {
    0.00: [{"Achilles", "Agamemnon", "Nestor", "Ulysses", "Jove"}, {"Hector", "Paris"}],
    0.04: [{"Achilles"}, {"Agamemnon", "Nestor", "Ulysses", "Ajax"}, {"Hector", "Paris"}, {"Jove"}],
    0.10: [{"Achilles"}, {"Agamemnon", "Nestor", "Ulysses", "Ajax", "Tydides"}, {"Hector", "Paris"}, {"Jove"}],
    0.17: [{"Achilles"}, {"Tydides", "Ulysses", "Nestor"}, {"Agamemnon", "Ajax"}, {"Hector", "Paris"}, {"Jove"}],
    0.25: [{"Achilles"}, {"Ajax", "Hector"}, {"Tydides", "Ulysses", "Nestor"}, {"Agamemnon"}, {"Paris"}, {"Jove"}],
    0.35: [{"Achilles"}, {"Ulysses", "Tydides"}, {"Agamemnon", "Nestor", "Ajax"}, {"Hector"}, {"Jove"}],
    0.46: [{"Achilles", "Patroclus"}, {"Agamemnon", "Nestor"}, {"Ajax", "Ulysses"}, {"Hector"}, {"Tydides"}, {"Jove"}],
    0.55: [{"Achilles", "Patroclus"}, {"Ajax", "Tydides"}, {"Agamemnon", "Ulysses", "Nestor"}, {"Hector"}, {"Jove"}],
    0.65: [{"Achilles"}, {"Patroclus", "Hector"}, {"Ajax"}, {"Agamemnon", "Nestor"}, {"Ulysses"}, {"Jove"}],
    0.72: [{"Achilles", "Patroclus"}, {"Ajax", "Hector"}, {"Agamemnon", "Nestor"}, {"Jove"}],
    0.80: [{"Achilles", "Agamemnon"}, {"Hector"}, {"Ajax", "Ulysses", "Tydides"}, {"Jove"}, {"Nestor"}],
    0.88: [{"Achilles", "Hector", "Jove"}, {"Agamemnon", "Ajax", "Nestor", "Ulysses"}, {"Paris"}],
    0.96: [{"Achilles", "Agamemnon", "Ajax", "Ulysses", "Nestor"}, {"Hector"}, {"Jove"}],
}

CRIME_GROUPS = {
    0.00: [{"Raskolnikov", "Marmeladov"}, {"Sonia"}, {"Razumihin"}, {"Dounia", "Pulcheria Alexandrovna"}],
    0.07: [{"Raskolnikov"}, {"Marmeladov"}, {"Razumihin"}, {"Dounia", "Pulcheria Alexandrovna", "Pyotr Petrovitch"}],
    0.16: [{"Raskolnikov", "Razumihin"}, {"Porfiry Petrovitch"}, {"Sonia", "Katerina Ivanovna", "Marmeladov"}],
    0.22: [{"Raskolnikov", "Razumihin"}, {"Porfiry Petrovitch"}, {"Dounia", "Pulcheria Alexandrovna"}, {"Sonia"}],
    0.30: [{"Raskolnikov", "Razumihin", "Porfiry Petrovitch"}, {"Sonia", "Katerina Ivanovna"}, {"Dounia", "Pulcheria Alexandrovna"}],
    0.43: [{"Raskolnikov", "Sonia"}, {"Svidrigaïlov"}, {"Razumihin", "Dounia", "Pulcheria Alexandrovna"}, {"Porfiry Petrovitch"}, {"Pyotr Petrovitch", "Katerina Ivanovna"}],
    0.52: [{"Raskolnikov", "Sonia"}, {"Svidrigaïlov"}, {"Pyotr Petrovitch", "Dounia"}, {"Razumihin", "Pulcheria Alexandrovna"}, {"Porfiry Petrovitch"}],
    0.62: [{"Raskolnikov", "Sonia", "Katerina Ivanovna"}, {"Svidrigaïlov"}, {"Razumihin", "Dounia"}, {"Porfiry Petrovitch"}, {"Pyotr Petrovitch"}],
    0.72: [{"Raskolnikov", "Porfiry Petrovitch"}, {"Svidrigaïlov", "Dounia"}, {"Razumihin"}, {"Sonia"}, {"Pulcheria Alexandrovna"}],
    0.82: [{"Raskolnikov", "Sonia"}, {"Svidrigaïlov"}, {"Razumihin", "Dounia"}, {"Porfiry Petrovitch"}, {"Pulcheria Alexandrovna"}],
    0.92: [{"Raskolnikov", "Sonia"}, {"Razumihin", "Dounia"}],
}

DUNE_GROUPS = {
    0.00: [{"Paul Atreides", "Lady Jessica", "Duke Leto Atreides"}, {"Baron Vladimir Harkonnen", "Feyd-Rautha"}],
    0.06: [{"Paul Atreides", "Lady Jessica", "Duke Leto Atreides", "Gurney Halleck"}, {"Baron Vladimir Harkonnen", "Feyd-Rautha"}],
    0.12: [{"Paul Atreides", "Lady Jessica", "Duke Leto Atreides", "Gurney Halleck", "Kynes"}, {"Baron Vladimir Harkonnen"}, {"Stilgar"}],
    0.19: [{"Paul Atreides", "Duke Leto Atreides", "Kynes"}, {"Lady Jessica", "Gurney Halleck"}, {"Stilgar"}, {"Baron Vladimir Harkonnen", "Feyd-Rautha"}],
    0.27: [{"Paul Atreides", "Lady Jessica"}, {"Duke Leto Atreides", "Baron Vladimir Harkonnen"}, {"Gurney Halleck"}, {"Stilgar"}, {"Kynes"}],
    0.33: [{"Paul Atreides", "Lady Jessica"}, {"Kynes"}, {"Baron Vladimir Harkonnen"}, {"Gurney Halleck"}, {"Stilgar"}],
    0.40: [{"Paul Atreides", "Lady Jessica", "Stilgar"}, {"Kynes"}, {"Baron Vladimir Harkonnen"}, {"Gurney Halleck"}],
    0.48: [{"Paul Atreides", "Lady Jessica", "Stilgar", "Chani"}, {"Baron Vladimir Harkonnen", "Feyd-Rautha"}, {"Gurney Halleck"}],
    0.54: [{"Paul Atreides", "Chani", "Stilgar"}, {"Lady Jessica"}, {"Baron Vladimir Harkonnen"}, {"Gurney Halleck"}],
    0.62: [{"Paul Atreides", "Chani", "Stilgar"}, {"Lady Jessica", "Alia"}, {"Baron Vladimir Harkonnen", "Feyd-Rautha"}, {"Gurney Halleck"}],
    0.72: [{"Paul Atreides", "Chani", "Stilgar", "Gurney Halleck"}, {"Lady Jessica", "Alia"}, {"Baron Vladimir Harkonnen"}],
    0.81: [{"Paul Atreides", "Chani"}, {"Lady Jessica", "Alia"}, {"Stilgar", "Gurney Halleck"}, {"Baron Vladimir Harkonnen", "Feyd-Rautha"}],
    0.90: [{"Paul Atreides", "Stilgar", "Gurney Halleck", "Chani"}, {"Alia", "Baron Vladimir Harkonnen"}, {"Lady Jessica"}, {"Feyd-Rautha"}],
    0.96: [{"Paul Atreides", "Chani", "Stilgar", "Gurney Halleck", "Lady Jessica", "Alia"}, {"Feyd-Rautha"}],
}

NARRATIVE_GROUPS = {
    "iliad": ILIAD_GROUPS,
    "crime": CRIME_GROUPS,
    "dune": DUNE_GROUPS,
}


EVENT_ANNOTATIONS = {
    "iliad": {
        0.00: "Quarrel",
        0.04: "Achilles\nwithdraws",
        0.65: "Patroclus\nfalls",
        0.80: "Achilles\nreturns",
        0.88: "Duel",
        0.96: "Funeral",
    },
    "crime": {
        0.00: "The\nMurder",
        0.30: "Porfiry's\nInterview",
        0.43: "Confession\nto Sonya",
        0.72: "Final\nInterview",
        0.92: "Siberia",
    },
    "dune": {
        0.00: "Caladan",
        0.12: "Arrive\nArrakis",
        0.27: "The\nAttack",
        0.48: "Join\nFremen",
        0.81: "Water\nof Life",
        0.90: "Final\nBattle",
    },
}


def has_preset(work_key: str) -> bool:
    """Return True if a hand-curated preset exists for this work."""
    return work_key in NARRATIVE_GROUPS


def get_preset(work_key: str) -> dict:
    """
    Return the full preset bundle for a work key.

    Raises KeyError if no preset exists.
    """
    if work_key not in NARRATIVE_GROUPS:
        raise KeyError(
            f"No preset for '{work_key}'. "
            f"Available: {list(NARRATIVE_GROUPS.keys())}"
        )
    return {
        "characters": NARRATIVE_CHARACTERS[work_key],
        "groups": NARRATIVE_GROUPS[work_key],
        "events": EVENT_ANNOTATIONS.get(work_key, {}),
    }
