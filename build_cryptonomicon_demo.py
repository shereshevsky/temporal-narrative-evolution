#!/usr/bin/env python3
"""
Cryptonomicon demo constellation for the Narrative Observatory.

This is NOT LLM extraction output. It is a hand-anchored temporal knowledge
graph built chapter by chapter from a published chapter-by-chapter synopsis of
Neal Stephenson's *Cryptonomicon* (Prologue + 102 chapters), cross-checked
against the novel's character and organisation lists. For every chapter it
records which era the chapter belongs to (the 1940s or the 1990s thread),
which entities are named, and which typed relationships form. Entities and
relations carry the chapter index of their *first* appearance and the list of
chapters in which they recur — exactly the format `temporal_extraction.py`
produces, so the Observatory renders it through the same code path.

Two extra fields ride along in `properties`:

  * `era`    — "1940s" or "1990s": the thread in which the entity is born
  * `bridge` — true when the entity is named in chapters of BOTH threads
  * `description` — one sentence shown by the Observatory's star inspector

They exist because Cryptonomicon is two interleaved timelines wearing one
book, and the interesting structure is where — and through whom — the two
constellations touch.

Usage:
    python build_cryptonomicon_demo.py            # writes output/ + injects HTML
    python build_cryptonomicon_demo.py --stats    # also prints article numbers
    python build_cryptonomicon_demo.py --no-inject
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

W, N = "1940s", "1990s"

# =============================================================================
# Entities:  key -> (display name, entity type, one-line description for the inspector)
# =============================================================================

ENT: dict[str, tuple[str, str, str]] = {
    # --- people, 1940s thread ------------------------------------------------
    "bobby":       ("Bobby Shaftoe", "CHARACTER",
        "US Marine Raider sergeant, haiku writer, morphine-seeky; the muscle of Detachment 2702 and later MacArthur's man among the Filipino guerrillas."),
    "lawrence":    ("Lawrence Waterhouse", "CHARACTER",
        "Mathematical savant and Navy cryptanalyst; Turing's friend at Princeton, the mind behind Detachment 2702, builder of a digital computer in Brisbane."),
    "turing":      ("Alan Turing", "CHARACTER",
        "Lawrence's Princeton bicycling companion, breaker of Enigma at Bletchley Park, designer of the bombe and Colossus."),
    "rudy":        ("Rudy von Hacklheber", "CHARACTER",
        "German mathematician and Lawrence's Princeton friend, conscripted to write ciphers for Göring; author of Arethusa and of the gold conspiracy."),
    "goto":        ("Goto Dengo", "CHARACTER",
        "Japanese mining engineer who survives the Bismarck Sea and New Guinea, then is made to build the Golgotha gold vault in Luzon; decades later, a construction magnate."),
    "glory":       ("Glory Altamira", "CHARACTER",
        "Filipina nursing student and Bobby Shaftoe's lover in 1941 Manila; later a heroine of the resistance and mother of Douglas MacArthur Shaftoe."),
    "root":        ("Enoch Root", "CHARACTER",
        "Ex-Catholic priest, physician, coast-watcher and chaplain of Detachment 2702; member of the Societas Eruditorum, and somehow alive and emailing in the 1990s."),
    "schoen":      ("Commander Schoen", "CHARACTER",
        "Bathrobe-clad Navy commander at Station Hypo who hands Lawrence the Cryptonomicon and the rule: never reveal the source."),
    "reagan":      ("Ronald Reagan", "CHARACTER",
        "A wartime Army Air Corps public-relations man who tele-interviews the hospitalized Bobby Shaftoe."),
    "chattan":     ("Colonel Chattan", "CHARACTER",
        "British colonel commanding Detachment 2702 from Bletchley Park."),
    "ethridge":    ("Lt. Ethridge", "CHARACTER",
        "Detachment 2702 officer who supervises the dressing of PFC Hott's corpse in an Algiers meat locker."),
    "hott":        ("PFC Hott", "CHARACTER",
        "A dead private whose refrigerated body Detachment 2702 turns into a decoy for Rommel."),
    "woadmire":    ("Lord Woadmire", "CHARACTER",
        "The German-born Duke of Qwghlm, whose castle roof hosts the huffduff antennas."),
    "comstock":    ("Earl Comstock", "CHARACTER",
        "Electrical Till Corporation executive turned Army officer in Brisbane; after the war, founder of the NSA."),
    "macarthur":   ("Douglas MacArthur", "CHARACTER",
        "The General. Bobby Shaftoe drives him through an air raid in Hollandia and becomes his eyes and ears in Luzon."),
    "monkberg":    ("Lt. Monkberg", "CHARACTER",
        "Lieutenant who nearly chops off his own foot demonstrating crate-chopping on the Ram-and-Run decoy freighter."),
    "bischoff":    ("Günter Bischoff", "CHARACTER",
        "Kapitänleutnant of U-691, straitjacketed by his own crew, later Bobby's drinking companion in Sweden and captain of the V-Million."),
    "beck":        ("Karl Beck", "CHARACTER",
        "Bischoff's executive officer, who takes command of U-691 and fishes Root and Shaftoe out of the Atlantic."),
    "yamamoto":    ("Isoroku Yamamoto", "CHARACTER",
        "Admiral of the Combined Fleet; his shootdown over Bougainville tells him his codes are broken."),
    "donitz":      ("Karl Dönitz", "CHARACTER",
        "Grand Admiral commanding the U-boats, target of Bletchley's Funkspiel and of Bischoff's blackmail letter."),
    "julieta":     ("Julieta Kivistik", "CHARACTER",
        "Finnish woman in Norrsbruck who shelters Bobby; mother of G.E.B. Kivistik, of three possible fathers."),
    "otto":        ("Otto Kivistik", "CHARACTER",
        "Julieta's uncle, smuggler across the Gulf of Bothnia, who betrays his guests to the Germans and is betrayed back."),
    "mary":        ("Mary cCmndhd", "CHARACTER",
        "Australian-born Qwghlmian whom Lawrence courts in Brisbane; Randy's grandmother, keeper of the trunk."),
    "goring":      ("Hermann Göring", "CHARACTER",
        "Reichsmarschall who conscripts Rudy's mathematics and moves his loot out of Germany."),
    "angelo":      ("Angelo", "CHARACTER",
        "Italian test pilot and Rudy's lover, who dies in the Luftwaffe jet that crashes near Norrsbruck."),
    "ferdinand":   ("Father Ferdinand", "CHARACTER",
        "Priest of the Societas Eruditorum who tends the hospitalized Goto Dengo in Luzon."),
    "noda":        ("Captain Noda", "CHARACTER",
        "Japanese captain running Bundok, who orders Golgotha sealed with its diggers inside."),
    "ninomiya":    ("Lt. Ninomiya", "CHARACTER",
        "Surveyor who plots Lake Yamamoto with Goto Dengo, then is 'reassigned' into a grave."),
    "wing":        ("Mr. Wing", "CHARACTER",
        "Chinese slave laborer at Golgotha who escapes with Goto; by the 1990s a general and hydroelectric mogul hunting the same gold."),
    "rodolfo":     ("Rodolfo", "CHARACTER",
        "Filipino worker Goto deputizes at Bundok, co-conspirator in the secret escape tunnels."),
    "bong":        ("Bong", "CHARACTER",
        "One of the diggers who swims out of Golgotha with Goto and Wing, diamonds in his pockets."),
    # --- people, 1990s thread ------------------------------------------------
    "randy":       ("Randy Waterhouse", "CHARACTER",
        "Systems administrator, Lawrence's grandson, Epiphyte's networking brain; goes to jail, cracks Arethusa, and finds Golgotha."),
    "avi":         ("Avi Halaby", "CHARACTER",
        "Randy's business partner and Epiphyte's CEO, descendant of Crypto-Jews, whose business plan is a moral document."),
    "charlene":    ("Charlene", "CHARACTER",
        "Randy's academic girlfriend in California, left behind for Manila and New Haven."),
    "loeb":        ("Andrew Loeb", "CHARACTER",
        "Randy's former friend, litigious survivalist, suspected Digibomber, and finally the Dentist's lawyer with a bow."),
    "geb":         ("G.E.B. Kivistik", "CHARACTER",
        "Julieta's son, Oxford-educated Yale professor who spars with Randy at a dinner party."),
    "amy":         ("Amy Shaftoe", "CHARACTER",
        "Doug Shaftoe's daughter, diver and captain of the Glory IV; Bobby Shaftoe's granddaughter."),
    "doug":        ("Doug Shaftoe", "CHARACTER",
        "Douglas MacArthur Shaftoe, Bobby's son, retired SEAL running Semper Marine; born in 1942 Manila, first seen in 1990s Manila."),
    "kepler":      ("Hubert Kepler (the Dentist)", "CHARACTER",
        "Hubert Kepler, 'the Dentist', billionaire investment manager who wants to own Epiphyte."),
    "cantrell":    ("John Cantrell", "CHARACTER",
        "Epiphyte's cryptographer and libertarian, author of Ordo."),
    "tom":         ("Tom Howard", "CHARACTER",
        "Epiphyte's hardware and firearms man, builder of the Crypt's racks and a fortress house in Kinakuta."),
    "beryl":       ("Beryl Hagen", "CHARACTER",
        "Epiphyte's CFO, veteran of a dozen startups."),
    "fohr":        ("Eberhard Föhr", "CHARACTER",
        "Epiphyte's biometrics expert, host of the NDA signing in Half Moon Bay."),
    "furudenendu": ("Goto Furudenendu", "CHARACTER",
        "Goto Dengo's heir at Goto Engineering, overseeing the Crypt's excavation."),
    "sultan":      ("The Sultan of Kinakuta", "CHARACTER",
        "Ruler of Kinakuta, whose data-haven speech is delivered to a perfectly silent room."),
    "pragasu":     ("Dr. Pragasu", "CHARACTER",
        "Kinakuta's California-educated Minister of Information, who favors Epiphyte."),
    "li":          ("Harvard Li", "CHARACTER",
        "Chinese entrepreneur with cash to shelter and a sudden interest in digital signatures."),
    "pekka":       ("Pekka", "CHARACTER",
        "The Finn Who Got Blown Up: first victim of the Digibomber, author of the Cryptonomicon's Van Eck phreaking chapter."),
    "kia":         ("Kia", "CHARACTER",
        "Epiphyte's sole California employee, and Amy's advocate."),
    "nguyen":      ("John Nguyen", "CHARACTER",
        "'John Wayne': Semper Marine crew on the jungle trek and at Golgotha."),
    "woo":         ("Jackie Woo", "CHARACTER",
        "Semper Marine crew on the jungle trek and at Golgotha."),
    "red":         ("Uncle Red", "CHARACTER",
        "Randy's uncle, who maps the family's furniture claims on a parking-lot grid."),
    "nina":        ("Aunt Nina", "CHARACTER",
        "Randy's aunt, who wants the console and ranks the trunk to get it."),
    "chester":     ("Chester", "CHARACTER",
        "Randy's Seattle friend, curator of a museum of dead technology and working card readers."),
    "marcus":      ("Marcus Aurelius Shaftoe", "CHARACTER",
        "Amy's Tennessee cousin, driver of a souped-up Impala."),
    "robin":       ("Robin Shaftoe", "CHARACTER",
        "Amy's Tennessee cousin, Marcus Aurelius's brother."),
    "pcomstock":   ("Paul Comstock", "CHARACTER",
        "Attorney General who raids Novus Ordo Seclorum's office for Epiphyte's server."),
    "alejandro":   ("Attorney Alejandro", "CHARACTER",
        "Randy's Manila lawyer during his incarceration."),
    # --- organisations -------------------------------------------------------
    "marines":     ("US Marine Corps", "ORGANIZATION",
        "Bobby Shaftoe's service, from Shanghai to Guadalcanal."),
    "navy":        ("US Navy", "ORGANIZATION",
        "Lawrence's service: Pearl Harbor glockenspiel, then cryptanalysis."),
    "hypo":        ("Station Hypo", "ORGANIZATION",
        "Pearl Harbor's naval codebreaking station, where Lawrence learns the trade."),
    "brit_intel":  ("British Intelligence", "ORGANIZATION",
        "The Broadway Buildings crowd, guardians of the Ultra secret."),
    "det2702":     ("Detachment 2702", "ORGANIZATION",
        "Ultra-secret Anglo-American deception unit that invents plausible reasons for Allied luck so the Germans never suspect Enigma is broken."),
    "etc":         ("Electrical Till Corporation", "ORGANIZATION",
        "The punched-card machine company that supplies Comstock and prefigures a certain three-letter firm."),
    "ubc":         ("U-boat Command", "ORGANIZATION",
        "Dönitz's U-boat command, whose chatty boats give Bletchley its openings."),
    "ija":         ("Imperial Japanese Army", "ORGANIZATION",
        "Goto Dengo's service, and the executioner of Golgotha's diggers."),
    "ijn":         ("Imperial Japanese Navy", "ORGANIZATION",
        "Yamamoto's Combined Fleet."),
    "div20":       ("Japanese 20th Division", "ORGANIZATION",
        "Japanese division in New Guinea whose buried codebooks end up drying in a Brisbane brothel."),
    "cbb":         ("Central Bureau, Brisbane", "ORGANIZATION",
        "MacArthur's Brisbane codebreaking shop, where Lawrence meets Comstock and Mary."),
    "eruditorum":  ("Societas Eruditorum", "ORGANIZATION",
        "Ancient learned society whose members include Enoch Root and Father Ferdinand; root@eruditorum.org in the 1990s."),
    "huks":        ("Hukbalahap guerrillas", "ORGANIZATION",
        "Filipino resistance guerrillas: Glory's cause and Bobby's last command."),
    "nsa":         ("NSA", "ORGANIZATION",
        "The agency Comstock founds after the war, with huffduff on Mindoro."),
    "wehrmacht":   ("German forces", "ORGANIZATION",
        "German roadblocks, Messerschmitts, and the hit squad sent to Norrsbruck."),
    "altamiras":   ("Altamira family", "ORGANIZATION",
        "Glory's Manila family, who honor Bobby in 1941 and are searched for in 1945."),
    "abacus":      ("Abacus slaves", "ORGANIZATION",
        "Chinese abacus virtuosi enslaved in a fort basement to compute the Azure/Pufferfish pads."),
    "epiphyte":    ("Epiphyte(2)", "ORGANIZATION",
        "Randy and Avi's startup, from Pinoy-grams to a data haven to a gold-backed e-currency."),
    "semper":      ("Semper Marine", "ORGANIZATION",
        "Doug Shaftoe's marine survey company, which finds the wreck and the gold."),
    "novus":       ("Novus Ordo Seclorum", "ORGANIZATION",
        "Los Altos ISP renting Epiphyte its Tombstone server; raided by the Attorney General."),
    "gotoeng":     ("Goto Engineering", "ORGANIZATION",
        "Goto Dengo's construction empire, digging the Crypt and financing the treasure hunt."),
    "blackchamber": ("The Black Chamber", "ORGANIZATION",
        "International Data Transfer Regulatory Organization, terrified of an untaxable Crypt."),
    # --- locations -----------------------------------------------------------
    "shanghai":    ("Shanghai", "LOCATION",
        "Where the Prologue opens: Shaftoe's convoy racing Station Alpha's equipment through money-strewn streets, November 1941."),
    "princeton":   ("Princeton", "LOCATION",
        "Where Lawrence, Turing and Rudy bicycle, compute, and argue in the late 1930s."),
    "pearl":       ("Pearl Harbor", "LOCATION",
        "Lawrence's glockenspiel posting, and his codebreaking apprenticeship."),
    "manila":      ("Manila", "LOCATION",
        "The city both threads keep returning to: Bobby's 1941 romance, Randy's 1990s office, the battle of 1945, the funeral."),
    "intramuros":  ("Intramuros", "LOCATION",
        "Manila's walled city, Epiphyte's office district and Glory's neighborhood."),
    "san_agustin": ("San Agustin Church", "LOCATION",
        "The church Glory takes Bobby to on December 7, 1941, and where MacArthur baptizes Goto Dengo in 1945."),
    "london":      ("London", "LOCATION",
        "Broadway Buildings, curb-frequency mapping, and a storm-lit stairway."),
    "north_africa": ("North Africa", "LOCATION",
        "Algiers meat locker, Rommel's front, and a coffin full of pork."),
    "bletchley":   ("Bletchley Park", "LOCATION",
        "Huts, bombes, pulley trays, and a black box that Lawrence learns not to open."),
    "malta":       ("Malta", "LOCATION",
        "Staging ground for Detachment 2702's fake observation post and the lizard story."),
    "oqwghlm":     ("Outer Qwghlm", "LOCATION",
        "The Duke's castle, the huffduff station, and the wreck of U-553 offshore."),
    "brisbane":    ("Brisbane", "LOCATION",
        "MacArthur's headquarters, the Central Bureau, and the boarding house where Lawrence meets Mary."),
    "kinakuta":    ("Kinakuta", "LOCATION",
        "Fictional sultanate between the Philippines and Borneo, host of the data haven."),
    "crypt":       ("The Crypt", "LOCATION",
        "The data haven itself, a cavern under Kinakuta's mountain, home of HEAP."),
    "los_altos":   ("Los Altos", "LOCATION",
        "The closet where Tombstone lives, and the street where the EMP van waits."),
    "new_guinea":  ("New Guinea", "LOCATION",
        "Where Goto Dengo washes ashore among cannibals, and where Bobby finds MacArthur."),
    "norrsbruck":  ("Norrsbruck", "LOCATION",
        "Swedish town where Bobby, Root, Bischoff and Rudy hide, plot, and marry."),
    "santa_monica": ("Santa Monica", "LOCATION",
        "The beach where Lawrence decides the ocean is a Turing machine."),
    "palawan":     ("Palawan", "LOCATION",
        "Off whose coast the V-Million lies in 154 meters of water."),
    "whitman":     ("Whitman, Washington", "LOCATION",
        "Randy's hometown in Washington, where the furniture is divided."),
    "seattle":     ("Seattle", "LOCATION",
        "Chester's museum of dead technology, where Randy reads his grandfather's cards."),
    "bundok":      ("Bundok", "LOCATION",
        "The Japanese site in Luzon where Goto builds dams, tunnels, and a tomb."),
    "golgotha":    ("Golgotha", "LOCATION",
        "The main vault of the gold hoard, deep under Bundok; opened in the last chapter."),
    "lake_yamamoto": ("Lake Yamamoto", "LOCATION",
        "The artificial lake whose water is the booby trap sealing Golgotha."),
    "makati":      ("Makati jail", "LOCATION",
        "The jail where Randy meets Enoch Root in person and cracks Arethusa."),
    "tokyo":       ("Tokyo", "LOCATION",
        "Airport and Akihabara; where Goto Dengo buys dinner."),
    "caballo":     ("Caballo Island fort", "LOCATION",
        "Fortress island south of Corregidor: Bobby Shaftoe's last mission and the abacus basement."),
    "luzon":       ("Luzon", "LOCATION",
        "The Philippine main island: jungle roadblocks, Bundok, Golgotha."),
    "california":  ("California", "LOCATION",
        "Half Moon Bay, Pacifica, the earthquake, and Randy's collapsed house."),
    # --- technology / ciphers / concepts ------------------------------------
    "turing_machine": ("Turing machine", "CONCEPT",
        "Turing's abstract machine, explained via pipe organ and bicycle chain; Lawrence sees the ocean as one."),
    "cryptonomicon":  ("The Cryptonomicon", "CONCEPT",
        "The cryptographer's bible, begun by John Wilkins, amended by Friedman and Waterhouse, read by Randy on a plane."),
    "ultra":       ("The Ultra secret", "CONCEPT",
        "The secret that Enigma is broken; everything Detachment 2702 does exists to protect it."),
    "haiku":       ("Haiku", "CONCEPT",
        "Bobby Shaftoe's poetic form, from Shanghai to the Swedish beach."),
    "pinoygrams":  ("Pinoy-grams", "CONCEPT",
        "Cheap video messages for overseas Filipinos: Epiphyte's first product."),
    "ecurrency":   ("Electronic gold currency", "CONCEPT",
        "Digital cash backed by gold, Avi's plan for the Crypt."),
    "heap":        ("HEAP", "CONCEPT",
        "Holocaust Education and Avoidance Pod: Avi's reason for the Crypt."),
    "enigma":      ("Enigma", "CIPHER",
        "The German rotor cipher, including the four-wheel Shark; broken, and the breaking hidden."),
    "otp":         ("One-time pad", "CIPHER",
        "Unbreakable if random and never reused; Detachment 2702's pads were neither."),
    "pontifex":    ("Pontifex (Solitaire)", "CIPHER",
        "Root's playing-card cipher, sent to Randy in Perl; Bruce Schneier's Solitaire in the appendix."),
    "arethusa":    ("Arethusa", "CIPHER",
        "Rudy's uncrippled cipher, used by the gold conspirators; cracked by Randy in jail and by Lawrence with card readers."),
    "azure":       ("Azure/Pufferfish", "CIPHER",
        "The Axis gold-hoarding code, keyed to a zeta function computed by abacus slaves."),
    "bombe":       ("Turing bombe", "TECHNOLOGY",
        "Turing's electromechanical Enigma-breaker at Bletchley."),
    "colossus":    ("Colossus", "TECHNOLOGY",
        "Turing's next machine, built to attack the Fish cipher."),
    "huffduff":    ("Huffduff (HF/DF)", "TECHNOLOGY",
        "High-frequency direction finding: triangulating U-boat transmissions from Qwghlm's castle."),
    "ordo":        ("Ordo", "TECHNOLOGY",
        "Cantrell's cryptography software, with its 4096-bit keys."),
    "vaneck":      ("Van Eck phreaking", "TECHNOLOGY",
        "Reading a screen from its radio emissions; demonstrated by Pekka, defeated by Randy's blinking NUM LOCK."),
    "digicomp":    ("Digital computer", "TECHNOLOGY",
        "Lawrence's card-reader computer with RAM, invented while fixing a church organ."),
    "tombstone":   ("Tombstone (server)", "TECHNOLOGY",
        "Epiphyte's email server in a Los Altos closet, subject of a subpoena and a wipe."),
    "cable":       ("Submarine fiber cable", "TECHNOLOGY",
        "The Manila-Kinakuta submarine fiber, whose superfluousness triggers the lawsuit."),
    # --- objects, vessels, resources ----------------------------------------
    "gold":        ("The gold", "RESOURCE",
        "Axis gold: on U-553, in Norrsbruck rumors, buried in Golgotha, salvaged from the wreck, and finally melted and flowing."),
    "codebooks":   ("Japanese Army codebooks", "OBJECT",
        "Buried in a New Guinea riverbank and dried page by page in Brisbane."),
    "trunk":       ("Waterhouse trunk of punch cards", "OBJECT",
        "Grandma Waterhouse's trunk of Lawrence's punch cards, the Arethusa key material, inherited by Randy."),
    "envelope":    ("Lavender Rose envelope", "OBJECT",
        "Rudy's stationery marked WATERHOUSE LAVENDER ROSE: found in the wreck in the 1990s, written in 1945."),
    "glory_iv":    ("Glory IV", "VESSEL",
        "Semper Marine's boat, Amy's command."),
    "u553":        ("U-553", "VESSEL",
        "The U-boat grounded off Qwghlm with a four-wheel Enigma, a safe, and gold bricks."),
    "u691":        ("U-691", "VESSEL",
        "Bischoff's U-boat, which captures Root and Shaftoe and is disowned by Berlin."),
    "vmillion":    ("V-Million (the U-boat wreck)", "VESSEL",
        "Bischoff's last submarine, sunk off Palawan with Rudy aboard; the wreck Semper Marine finds fifty years later."),
    # --- events --------------------------------------------------------------
    "hindenburg":  ("Hindenburg disaster", "EVENT",
        "The airship disaster Lawrence witnesses from a fire tower in the Pine Barrens."),
    "pearl_attack": ("Attack on Pearl Harbor", "EVENT",
        "December 7, 1941, seen from a hospital by Lawrence; heard as sirens by Bobby in Manila."),
    "guadalcanal": ("Battle of Guadalcanal", "EVENT",
        "The beach where Bobby's comrades die and Enoch Root carries him off."),
    "bismarck":    ("Battle of the Bismarck Sea", "EVENT",
        "March 1943: skip-bombing sinks Goto Dengo's convoy."),
    "yamamoto_death": ("Shootdown of Yamamoto", "EVENT",
        "April 1943: American cryptographers' work puts P-38s on the admiral's plane."),
    "jetcrash":    ("Luftwaffe jet crash", "EVENT",
        "A Luftwaffe jet prototype falls burning into the woods north of Norrsbruck."),
    "leyte":       ("Return to Leyte", "EVENT",
        "MacArthur's return, October 1944; the signal to hurry at Bundok."),
    "sealing":     ("Sealing of Golgotha", "EVENT",
        "Noda dynamites the Lake Yamamoto plug; the diggers escape through Goto's air bubbles."),
    "manila_battle": ("Battle of Manila", "EVENT",
        "February 1945: Bobby leads the Huks into Ermita, and finds Goto Dengo in a bathroom."),
    "lastmission": ("Shaftoe's last mission", "EVENT",
        "Bobby parachutes onto the Caballo fort, pumps in fuel oil, and follows the grenade down."),
    "funeral":     ("Shaftoe's funeral", "EVENT",
        "Where Root, Goto, Rudy and Bischoff gather, and Lawrence spies on them."),
    "vm_sinking":  ("Sinking of the V-Million", "EVENT",
        "Catalinas sink the V-Million off Borneo; Rudy stays down with the coordinates."),
    "quake":       ("California earthquake", "EVENT",
        "The earthquake that collapses Randy's California house."),
    "conference":  ("The Sultan's conference", "EVENT",
        "The Sultan's palace meeting where Epiphyte pitches the Crypt to the world's money."),
    "lawsuit":     ("The Dentist's lawsuit", "EVENT",
        "The Dentist's tactical suit, argued by Andrew Loeb, over an undisclosed cable and an undisclosed wreck."),
    "raid":        ("Raid on Novus Ordo Seclorum", "EVENT",
        "The Attorney General's assault on Novus Ordo Seclorum, with an EMP van outside."),
    "arrest":      ("Randy's arrest", "EVENT",
        "Heroin planted in Randy's duffel at Manila airport."),
    "excavation":  ("Opening of Golgotha", "EVENT",
        "Drilling into Golgotha from above while Wing tunnels from the side; the gold flows out molten."),
}

# =============================================================================
# Scenes: (chapter title, era, relations formed in that chapter)
# A relation is (subject, PREDICATE, object). Entities named in a chapter but
# with no new relation are listed in the optional 4th element.
# Chapter order and era follow the novel; the Prologue is index 0.
# =============================================================================

SCENES: list[tuple] = [
    ("Prologue", W, [("bobby", "MEMBER_OF", "marines"), ("bobby", "LOCATED_IN", "shanghai"),
                     ("bobby", "WRITES", "haiku")]),
    ("Barrens", W, [("lawrence", "FRIEND_OF", "turing"), ("lawrence", "FRIEND_OF", "rudy"),
                    ("turing", "LOVES", "rudy"), ("lawrence", "LOCATED_IN", "princeton"),
                    ("turing", "INVENTS", "turing_machine"), ("lawrence", "WITNESSES", "hindenburg"),
                    ("lawrence", "MEMBER_OF", "navy"), ("lawrence", "LOCATED_IN", "pearl")]),
    ("Novus Ordo Seclorum", N, [("randy", "PARTNERS_WITH", "avi"), ("randy", "MEMBER_OF", "epiphyte"),
                                ("avi", "LEADS", "epiphyte"), ("randy", "TRAVELS_TO", "manila"),
                                ("epiphyte", "LOCATED_IN", "intramuros"), ("randy", "LOCATED_IN", "tokyo")]),
    ("Seaweed", W, [("bobby", "FRIEND_OF", "goto"), ("bobby", "LOVES", "glory"),
                    ("glory", "MEMBER_OF", "altamiras"), ("bobby", "TRAVELS_TO", "manila"),
                    ("bobby", "TRAVELS_TO", "san_agustin"), ("goto", "WRITES", "haiku"),
                    ("pearl_attack", "LOCATED_IN", "pearl"), ("bobby", "LOCATED_IN", "intramuros")]),
    ("Forays", N, [("randy", "LOVES", "charlene"), ("randy", "FRIEND_OF", "loeb"),
                   ("loeb", "SUES", "randy"), ("randy", "USES", "ordo"),
                   ("randy", "PARTNERS_WITH", "avi"), ("randy", "LOCATED_IN", "manila")]),
    ("Indigo", W, [("lawrence", "WITNESSES", "pearl_attack"), ("schoen", "MENTORS", "lawrence"),
                   ("lawrence", "MEMBER_OF", "hypo"), ("lawrence", "STUDIES", "cryptonomicon"),
                   ("schoen", "MEMBER_OF", "hypo"), ("hypo", "LOCATED_IN", "pearl"),
                   ("hypo", "PROTECTS", "ultra")]),
    ("The Spawn of Onan", N, [("randy", "LOVES", "charlene"), ("randy", "OPPOSES", "geb"),
                              ("randy", "PARTNERS_WITH", "avi"), ("charlene", "KNOWS", "geb")]),
    ("Burn", W, [("bobby", "LOVES", "glory"), ("altamiras", "ALLIES_WITH", "bobby"),
                 ("bobby", "LOCATED_IN", "manila")]),
    ("Pedestrian", N, [("randy", "LOCATED_IN", "intramuros"), ("randy", "LOCATED_IN", "manila")]),
    ("Guadalcanal", W, [("bobby", "PARTICIPATES_IN", "guadalcanal"), ("root", "RESCUES", "bobby")]),
    ("Galleon", N, [("amy", "COMMANDS", "glory_iv"), ("amy", "MEMBER_OF", "semper"),
                    ("randy", "KNOWS", "amy"), ("epiphyte", "BUILDS", "cable"),
                    ("epiphyte", "INVENTS", "pinoygrams"), ("randy", "LOCATED_IN", "glory_iv"),
                    ("cable", "LOCATED_IN", "manila")]),
    ("Nightmare", W, [("reagan", "KNOWS", "bobby"), ("bobby", "TRAVELS_TO", "north_africa"),
                      ("bobby", "MEMBER_OF", "marines")]),
    ("Londinium", W, [("lawrence", "TRAVELS_TO", "london"), ("lawrence", "SERVES", "brit_intel"),
                      ("brit_intel", "PROTECTS", "ultra"), ("ultra", "DEPENDS_ON", "enigma"),
                      ("lawrence", "FOUNDS", "det2702"), ("lawrence", "FRIEND_OF", "rudy")]),
    ("Corregidor", N, [("doug", "PARENT_OF", "amy"), ("doug", "LEADS", "semper"),
                       ("kepler", "PARTNERS_WITH", "epiphyte"), ("semper", "SERVES", "epiphyte"),
                       ("doug", "OPPOSES", "kepler"), ("amy", "COMMANDS", "glory_iv"),
                       ("randy", "KNOWS", "doug"), ("randy", "LOCATED_IN", "glory_iv")]),
    ("Tube", W, [("lawrence", "TRAVELS_TO", "bletchley"), ("chattan", "LEADS", "det2702"),
                 ("lawrence", "MEMBER_OF", "det2702"), ("turing", "INVENTS", "bombe"),
                 ("bombe", "CRACKS", "enigma"), ("det2702", "PROTECTS", "ultra"),
                 ("chattan", "KNOWS", "lawrence"), ("turing", "LOCATED_IN", "bletchley")]),
    ("Meat", W, [("bobby", "MEMBER_OF", "det2702"), ("root", "MEMBER_OF", "det2702"),
                 ("ethridge", "MEMBER_OF", "det2702"), ("hott", "MEMBER_OF", "det2702"),
                 ("bobby", "FRIEND_OF", "root"), ("det2702", "LOCATED_IN", "north_africa")]),
    ("Cycles", W, [("lawrence", "FRIEND_OF", "turing"), ("lawrence", "STUDIES", "enigma"),
                   ("ubc", "USES", "enigma"), ("lawrence", "LOCATED_IN", "bletchley"),
                   ("turing", "STUDIES", "enigma")]),
    ("Aloft", W, [("root", "FRIEND_OF", "bobby"), ("det2702", "TRAVELS_TO", "malta"),
                  ("bobby", "PARTICIPATES_IN", "guadalcanal"), ("root", "RESCUES", "bobby"),
                  ("ethridge", "MEMBER_OF", "det2702")]),
    ("Non-disclosure", N, [("cantrell", "MEMBER_OF", "epiphyte"), ("tom", "MEMBER_OF", "epiphyte"),
                           ("beryl", "MEMBER_OF", "epiphyte"), ("fohr", "MEMBER_OF", "epiphyte"),
                           ("avi", "FOUNDS", "crypt"), ("crypt", "LOCATED_IN", "kinakuta"),
                           ("epiphyte", "BUILDS", "crypt"), ("randy", "MEMBER_OF", "epiphyte"),
                           ("avi", "LEADS", "epiphyte")]),
    ("Ultra", W, [("lawrence", "LOCATED_IN", "bletchley"), ("bletchley", "CRACKS", "enigma"),
                  ("lawrence", "STUDIES", "turing_machine"), ("bletchley", "PROTECTS", "ultra")]),
    ("Kinakuta", N, [("randy", "TRAVELS_TO", "kinakuta")]),
    ("Qwghlm House", W, [("lawrence", "KNOWS", "woadmire"), ("woadmire", "RULES", "oqwghlm"),
                         ("det2702", "USES", "huffduff"), ("huffduff", "INTERCEPTS", "ubc"),
                         ("huffduff", "LOCATED_IN", "oqwghlm"), ("chattan", "LEADS", "det2702")]),
    ("Electrical Till Corporation", W, [("comstock", "MEMBER_OF", "etc"), ("comstock", "SERVES", "macarthur")]),
    ("Crypt", N, [("randy", "KNOWS", "furudenendu"), ("furudenendu", "LEADS", "gotoeng"),
                  ("gotoeng", "BUILDS", "crypt"), ("tom", "BUILDS", "crypt"),
                  ("randy", "TRAVELS_TO", "crypt"), ("crypt", "LOCATED_IN", "kinakuta")]),
    ("Lizard", W, [("root", "FRIEND_OF", "bobby"), ("det2702", "LOCATED_IN", "malta"),
                   ("bobby", "MEMBER_OF", "det2702")]),
    ("The Castle", W, [("lawrence", "TRAVELS_TO", "oqwghlm"), ("lawrence", "USES", "otp"),
                       ("lawrence", "LOCATED_IN", "london")]),
    ("Why", N, [("root", "COMMUNICATES_WITH", "randy"), ("root", "MEMBER_OF", "eruditorum"),
                ("epiphyte", "USES", "tombstone"), ("tombstone", "LOCATED_IN", "los_altos"),
                ("novus", "SERVES", "epiphyte"), ("cantrell", "KNOWS", "randy"),
                ("loeb", "OPPOSES", "epiphyte"), ("loeb", "OPPOSES", "crypt"),
                ("randy", "KNOWS", "furudenendu"), ("fohr", "KNOWS", "randy"),
                ("tom", "KNOWS", "randy"), ("epiphyte", "BUILDS", "cable"),
                ("avi", "LEADS", "epiphyte")]),
    ("Retrograde Maneuver", W, [("div20", "LOCATED_IN", "new_guinea"), ("div20", "BURIES", "codebooks"),
                                ("div20", "MEMBER_OF", "ija")]),
    ("Huffduff", W, [("det2702", "TRAVELS_TO", "oqwghlm"), ("ubc", "USES", "enigma"),
                     ("lawrence", "PROTECTS", "ultra"), ("huffduff", "INTERCEPTS", "ubc"),
                     ("lawrence", "LOCATED_IN", "oqwghlm"), ("lawrence", "USES", "otp")]),
    ("Pages", W, [("cbb", "LOCATED_IN", "brisbane"), ("cbb", "DISCOVERS", "codebooks")]),
    ("Ram", W, [("monkberg", "MEMBER_OF", "det2702"), ("root", "RESCUES", "monkberg"),
                ("bobby", "FIGHTS", "wehrmacht"), ("det2702", "LOCATED_IN", "malta"),
                ("bobby", "MEMBER_OF", "det2702"), ("root", "MEMBER_OF", "det2702")]),
    ("Diligence", N, [("epiphyte", "PARTNERS_WITH", "kepler"), ("fohr", "KNOWS", "randy"),
                      ("avi", "LEADS", "epiphyte"), ("epiphyte", "BUILDS", "cable"),
                      ("beryl", "MEMBER_OF", "epiphyte"), ("cantrell", "MEMBER_OF", "epiphyte"),
                      ("tom", "MEMBER_OF", "epiphyte"), ("randy", "LOCATED_IN", "kinakuta"),
                      ("randy", "COMMUNICATES_WITH", "loeb")]),
    ("Spearhead", W, [("lawrence", "KNOWS", "bobby"), ("lawrence", "SALVAGES", "u553"),
                      ("bobby", "SALVAGES", "u553"), ("u553", "LOCATED_IN", "oqwghlm"),
                      ("u553", "POSSESSES", "enigma"), ("u553", "MEMBER_OF", "ubc")]),
    ("Morphium", W, [("bobby", "DISCOVERS", "gold"), ("u553", "POSSESSES", "gold"),
                     ("bobby", "SALVAGES", "u553")]),
    ("Suit", N, [("randy", "KNOWS", "kepler"), ("epiphyte", "PARTICIPATES_IN", "conference"),
                 ("kepler", "PARTICIPATES_IN", "conference"), ("sultan", "LEADS", "conference"),
                 ("avi", "LEADS", "epiphyte")]),
    ("Cracker", W, [("lawrence", "DISCOVERS", "gold"), ("root", "KNOWS", "lawrence"),
                    ("lawrence", "STUDIES", "azure"), ("u553", "POSSESSES", "gold"),
                    ("lawrence", "LOCATED_IN", "oqwghlm")]),
    ("Sultan", N, [("sultan", "RULES", "kinakuta"), ("pragasu", "SERVES", "sultan"),
                   ("li", "KNOWS", "cantrell"), ("li", "SEEKS", "crypt"),
                   ("cantrell", "STUDIES", "vaneck"), ("sultan", "LEADS", "conference"),
                   ("epiphyte", "PARTICIPATES_IN", "conference"), ("kepler", "PARTICIPATES_IN", "conference"),
                   ("conference", "LOCATED_IN", "kinakuta"), ("avi", "LEADS", "epiphyte")]),
    ("Skipping", W, [("goto", "SURVIVES", "bismarck"), ("goto", "MEMBER_OF", "ija")]),
    ("Mugs", N, [("pragasu", "ALLIES_WITH", "epiphyte"), ("cantrell", "BUILDS", "crypt"),
                 ("tom", "PARTICIPATES_IN", "conference"), ("kepler", "KNOWS", "randy"),
                 ("cantrell", "STUDIES", "ecurrency"), ("fohr", "STUDIES", "ecurrency")]),
    ("Yamamoto", W, [("yamamoto", "DIES_IN", "yamamoto_death"), ("yamamoto", "LEADS", "ijn"),
                     ("hypo", "CAUSES", "yamamoto_death")]),
    ("Antaeus", W, [("turing", "INVENTS", "colossus"), ("lawrence", "STUDIES", "azure"),
                    ("turing", "STUDIES", "azure"), ("lawrence", "SERVES", "brit_intel"),
                    ("lawrence", "LOCATED_IN", "bletchley"), ("lawrence", "FRIEND_OF", "turing")],
     ["yamamoto_death"]),
    ("Phreaking", N, [("pekka", "WRITES", "cryptonomicon"), ("pekka", "USES", "vaneck"),
                      ("cantrell", "KNOWS", "pekka"), ("randy", "COMMUNICATES_WITH", "root"),
                      ("cantrell", "KNOWS", "tom")], ["loeb"]),
    ("Afloat", W, [("goto", "SURVIVES", "bismarck"), ("goto", "TRAVELS_TO", "new_guinea")]),
    ("Shinola", W, [("bischoff", "COMMANDS", "u691"), ("beck", "SERVES", "bischoff"),
                    ("beck", "CAPTURES", "root"), ("beck", "CAPTURES", "bobby"),
                    ("u691", "MEMBER_OF", "ubc"), ("bobby", "MEMBER_OF", "det2702"),
                    ("root", "MEMBER_OF", "det2702"), ("bobby", "FRIEND_OF", "root")]),
    ("Hostilities", N, [("kepler", "PLOTS_AGAINST", "epiphyte"), ("kepler", "CAUSES", "lawsuit"),
                        ("epiphyte", "PARTICIPATES_IN", "lawsuit"), ("gotoeng", "BUILDS", "crypt"),
                        ("randy", "COMMUNICATES_WITH", "root"), ("beryl", "MEMBER_OF", "epiphyte"),
                        ("avi", "LEADS", "epiphyte"), ("crypt", "LOCATED_IN", "kinakuta")],
     ["pragasu"]),
    ("Funkspiel", W, [("donitz", "LEADS", "ubc"), ("bletchley", "INTERCEPTS", "ubc"),
                      ("u691", "MEMBER_OF", "ubc"), ("lawrence", "KNOWS", "bobby"),
                      ("lawrence", "KNOWS", "root"), ("turing", "LOCATED_IN", "bletchley"),
                      ("lawrence", "LOCATED_IN", "bletchley"), ("bletchley", "PROTECTS", "ultra")]),
    ("Heap", N, [("root", "COMMUNICATES_WITH", "randy"), ("avi", "FOUNDS", "heap"),
                 ("heap", "LOCATED_IN", "crypt"), ("doug", "DISCOVERS", "vmillion"),
                 ("semper", "DISCOVERS", "vmillion"), ("randy", "PARTNERS_WITH", "avi")]),
    ("Seeky", W, [("bischoff", "KNOWS", "bobby"), ("bischoff", "SEEKS", "gold"),
                  ("bischoff", "OPPOSES", "donitz"), ("ubc", "OPPOSES", "u691"),
                  ("bischoff", "COMMANDS", "u691"), ("bischoff", "TRAVELS_TO", "norrsbruck"),
                  ("beck", "SERVES", "bischoff"), ("root", "LOCATED_IN", "u691"),
                  ("bobby", "LOCATED_IN", "u691"), ("u553", "POSSESSES", "gold")]),
    ("Cannibals", W, [("goto", "MEMBER_OF", "ija"), ("goto", "LOCATED_IN", "new_guinea"),
                      ("ija", "LOCATED_IN", "new_guinea")]),
    ("Wreck", N, [("randy", "LOVES", "amy"), ("semper", "DISCOVERS", "vmillion"),
                  ("vmillion", "LOCATED_IN", "palawan"), ("kepler", "INVESTS_IN", "epiphyte"),
                  ("root", "COMMUNICATES_WITH", "randy"), ("randy", "TRAVELS_TO", "palawan"),
                  ("doug", "LEADS", "semper"), ("amy", "MEMBER_OF", "semper"),
                  ("randy", "LOCATED_IN", "glory_iv"), ("epiphyte", "PARTICIPATES_IN", "lawsuit")]),
    ("Santa Monica", W, [("lawrence", "TRAVELS_TO", "santa_monica"), ("lawrence", "STUDIES", "turing_machine")]),
    ("Outpost", W, [("goto", "LOCATED_IN", "new_guinea"), ("goto", "SERVES", "ija")]),
    ("Meteor", W, [("bobby", "LOVES", "julieta"), ("otto", "FAMILY_OF", "julieta"),
                   ("bobby", "SERVES", "otto"), ("bobby", "WITNESSES", "jetcrash"),
                   ("bobby", "WRITES", "haiku"), ("bobby", "LOCATED_IN", "norrsbruck"),
                   ("jetcrash", "LOCATED_IN", "norrsbruck")]),
    ("Lavender Rose", N, [("root", "INVENTS", "pontifex"), ("root", "COMMUNICATES_WITH", "randy"),
                          ("cantrell", "STUDIES", "pontifex"), ("doug", "SALVAGES", "vmillion"),
                          ("doug", "DISCOVERS", "envelope"), ("envelope", "LOCATED_IN", "vmillion"),
                          ("rudy", "POSSESSES", "envelope"), ("randy", "SEEKS", "vmillion"),
                          ("randy", "LOCATED_IN", "glory_iv"), ("amy", "MEMBER_OF", "semper")]),
    ("Brisbane", W, [("lawrence", "TRAVELS_TO", "brisbane"), ("lawrence", "SERVES", "macarthur")]),
    ("Dönitz", W, [("bischoff", "FRIEND_OF", "bobby"), ("bischoff", "LOCATED_IN", "norrsbruck"),
                   ("root", "LOCATED_IN", "norrsbruck"), ("rudy", "LOCATED_IN", "norrsbruck"),
                   ("rudy", "LOVES", "angelo"), ("angelo", "DIES_IN", "jetcrash"),
                   ("root", "KNOWS", "rudy"), ("bischoff", "OPPOSES", "donitz"),
                   ("bobby", "WITNESSES", "jetcrash")], ["julieta", "otto"]),
    ("Crunch", N, [("root", "COMMUNICATES_WITH", "randy"), ("randy", "STUDIES", "pontifex"),
                   ("randy", "LOVES", "amy"), ("randy", "TRAVELS_TO", "manila"),
                   ("doug", "KNOWS", "randy")], ["avi"]),
    ("Girl", W, [("lawrence", "MEMBER_OF", "cbb"), ("comstock", "MEMBER_OF", "cbb"),
                 ("etc", "SERVES", "cbb"), ("lawrence", "LOVES", "mary"),
                 ("mary", "LOCATED_IN", "brisbane"), ("lawrence", "LOCATED_IN", "brisbane"),
                 ("comstock", "MEMBER_OF", "etc")]),
    ("Conspiracy", W, [("rudy", "FRIEND_OF", "root"), ("rudy", "KNOWS", "bischoff"),
                       ("rudy", "OPPOSES", "goring"), ("rudy", "SERVES", "goring"),
                       ("rudy", "INVENTS", "arethusa"), ("rudy", "DISCOVERS", "ultra"),
                       ("det2702", "USES", "otp"), ("rudy", "CRACKS", "otp"),
                       ("root", "MEMBER_OF", "eruditorum"), ("rudy", "SEEKS", "gold"),
                       ("bobby", "SEEKS", "gold"), ("bischoff", "SEEKS", "gold"),
                       ("gold", "LOCATED_IN", "manila"), ("rudy", "LOVES", "angelo"),
                       ("rudy", "STUDIES", "enigma"), ("rudy", "LOCATED_IN", "norrsbruck")]),
    ("Hoard", N, [("kia", "MEMBER_OF", "epiphyte"), ("nguyen", "MEMBER_OF", "semper"),
                  ("woo", "MEMBER_OF", "semper"), ("doug", "SEEKS", "gold"),
                  ("doug", "DISCOVERS", "gold"), ("randy", "TRAVELS_TO", "luzon"),
                  ("gold", "LOCATED_IN", "luzon"), ("randy", "LOVES", "amy"),
                  ("doug", "LEADS", "semper")]),
    ("Rocket", W, [("otto", "BETRAYS", "bobby"), ("otto", "BETRAYS", "root"),
                   ("root", "LOVES", "julieta"), ("root", "MARRIES", "julieta"),
                   ("bobby", "FIGHTS", "wehrmacht"), ("bobby", "RESCUES", "root"),
                   ("rudy", "LOCATED_IN", "norrsbruck"), ("bischoff", "FRIEND_OF", "bobby")]),
    ("Courting", W, [("lawrence", "LOVES", "mary"), ("lawrence", "LOCATED_IN", "brisbane")]),
    ("I.N.R.I.", W, [("ferdinand", "KNOWS", "goto"), ("ferdinand", "MEMBER_OF", "eruditorum"),
                     ("goto", "TRAVELS_TO", "luzon"), ("goto", "SERVES", "ija")]),
    ("California", N, [("avi", "ADVOCATES", "ecurrency"), ("ecurrency", "DEPENDS_ON", "gold"),
                       ("kia", "ALLIES_WITH", "amy"), ("randy", "TRAVELS_TO", "california"),
                       ("avi", "LOCATED_IN", "california"), ("kia", "MEMBER_OF", "epiphyte")],
     ["charlene"]),
    ("Organ", W, [("lawrence", "INVENTS", "digicomp"), ("lawrence", "LOVES", "mary"),
                  ("lawrence", "LOCATED_IN", "brisbane")]),
    ("Home", N, [("randy", "SURVIVES", "quake"), ("amy", "TRAVELS_TO", "california"),
                 ("marcus", "FAMILY_OF", "amy"), ("robin", "FAMILY_OF", "amy"),
                 ("amy", "LOVES", "randy"), ("quake", "LOCATED_IN", "california")], ["charlene"]),
    ("Bundok", W, [("goto", "SERVES", "noda"), ("goto", "BUILDS", "bundok"),
                   ("bundok", "LOCATED_IN", "luzon"), ("noda", "MEMBER_OF", "ija"),
                   ("goto", "MEMBER_OF", "ija")]),
    ("Computer", W, [("lawrence", "STUDIES", "arethusa"), ("lawrence", "STUDIES", "azure"),
                     ("lawrence", "INVENTS", "digicomp"), ("comstock", "KNOWS", "lawrence"),
                     ("lawrence", "LOVES", "mary"), ("comstock", "MEMBER_OF", "etc"),
                     ("lawrence", "MEMBER_OF", "cbb")], ["goto"]),
    ("Caravan", N, [("randy", "LOVES", "amy"), ("randy", "ADVOCATES", "ecurrency"),
                    ("marcus", "FAMILY_OF", "amy"), ("robin", "FAMILY_OF", "amy")]),
    ("The General", W, [("bobby", "TRAVELS_TO", "new_guinea"), ("bobby", "SERVES", "macarthur"),
                        ("bobby", "RESCUES", "macarthur"), ("macarthur", "LOCATED_IN", "new_guinea"),
                        ("bobby", "TRAVELS_TO", "brisbane")]),
    ("Origin", N, [("red", "FAMILY_OF", "randy"), ("nina", "FAMILY_OF", "randy"),
                   ("randy", "SEEKS", "trunk"), ("randy", "TRAVELS_TO", "whitman"),
                   ("mary", "POSSESSES", "trunk"), ("amy", "LOCATED_IN", "whitman"),
                   ("red", "CHILD_OF", "mary"), ("nina", "CHILD_OF", "mary")]),
    ("Golgotha", W, [("ninomiya", "ALLIES_WITH", "goto"), ("goto", "BUILDS", "golgotha"),
                     ("goto", "BUILDS", "lake_yamamoto"), ("golgotha", "LOCATED_IN", "bundok"),
                     ("lake_yamamoto", "LOCATED_IN", "bundok"), ("wing", "SERVES", "goto"),
                     ("ija", "KILLS", "ninomiya"), ("ninomiya", "MEMBER_OF", "ija")]),
    ("Seattle", N, [("randy", "GRANDCHILD_OF", "mary"), ("mary", "MARRIES", "lawrence"),
                    ("randy", "GRANDCHILD_OF", "lawrence"), ("chester", "FRIEND_OF", "randy"),
                    ("randy", "POSSESSES", "trunk"), ("randy", "TRAVELS_TO", "seattle"),
                    ("chester", "LOCATED_IN", "seattle"), ("lawrence", "FRIEND_OF", "turing"),
                    ("lawrence", "FRIEND_OF", "rudy"), ("amy", "LOCATED_IN", "seattle")]),
    ("Rock", W, [("goto", "BUILDS", "golgotha"), ("macarthur", "LEADS", "leyte"),
                 ("lake_yamamoto", "PROTECTS", "golgotha"), ("goto", "BUILDS", "lake_yamamoto"),
                 ("ija", "BUILDS", "golgotha")]),
    ("The Most Cigarettes", N, [("loeb", "SERVES", "kepler"), ("loeb", "SUES", "epiphyte"),
                                ("kepler", "CAUSES", "lawsuit"), ("semper", "DISCOVERS", "gold"),
                                ("gold", "LOCATED_IN", "vmillion"), ("randy", "USES", "tombstone"),
                                ("novus", "SERVES", "epiphyte"), ("cantrell", "STUDIES", "pontifex"),
                                ("kepler", "SEEKS", "gold"), ("lawsuit", "DEPENDS_ON", "gold"),
                                ("cantrell", "KNOWS", "randy"), ("avi", "TRAVELS_TO", "los_altos"),
                                ("tombstone", "LOCATED_IN", "los_altos")], ["glory_iv"]),
    ("Christmas 1944", W, [("rodolfo", "SERVES", "goto"), ("goto", "ALLIES_WITH", "wing"),
                           ("ija", "BURIES", "gold"), ("gold", "LOCATED_IN", "golgotha"),
                           ("goto", "BUILDS", "golgotha"), ("macarthur", "LEADS", "leyte"),
                           ("wing", "SERVES", "goto"), ("goto", "ALLIES_WITH", "rodolfo")]),
    ("Pulse", N, [("pcomstock", "CAUSES", "raid"), ("loeb", "PARTICIPATES_IN", "raid"),
                  ("randy", "USES", "tombstone"), ("raid", "LOCATED_IN", "los_altos"),
                  ("pcomstock", "OPPOSES", "epiphyte"), ("novus", "SERVES", "epiphyte"),
                  ("avi", "TRAVELS_TO", "los_altos"), ("randy", "TRAVELS_TO", "los_altos")],
     ["heap"]),
    ("Buddha", W, [("ija", "BURIES", "gold"), ("noda", "CAUSES", "sealing"),
                   ("goto", "PARTICIPATES_IN", "sealing"), ("sealing", "LOCATED_IN", "golgotha"),
                   ("goto", "ALLIES_WITH", "wing"), ("goto", "ALLIES_WITH", "rodolfo"),
                   ("gold", "LOCATED_IN", "golgotha"), ("goto", "SERVES", "noda"),
                   ("wing", "SERVES", "goto")]),
    ("Pontifex", N, [("root", "COMMUNICATES_WITH", "randy"), ("randy", "STUDIES", "arethusa"),
                     ("randy", "TRAVELS_TO", "kinakuta"), ("randy", "COMMUNICATES_WITH", "doug"),
                     ("arethusa", "DEPENDS_ON", "comstock")], ["avi"]),
    ("Glory", W, [("doug", "CHILD_OF", "bobby"), ("doug", "CHILD_OF", "glory"),
                  ("bobby", "SERVES", "macarthur"), ("glory", "MEMBER_OF", "huks"),
                  ("bobby", "LOVES", "glory"), ("bobby", "TRAVELS_TO", "luzon")]),
    ("The Primary", N, [("tom", "LOCATED_IN", "kinakuta"), ("blackchamber", "OPPOSES", "crypt"),
                        ("pcomstock", "OPPOSES", "epiphyte"), ("randy", "STUDIES", "arethusa"),
                        ("trunk", "POSSESSES", "arethusa"), ("doug", "SEEKS", "gold"),
                        ("kepler", "SEEKS", "gold"), ("cantrell", "KNOWS", "randy"),
                        ("doug", "KNOWS", "tom"), ("randy", "LOCATED_IN", "kinakuta"),
                        ("epiphyte", "PARTICIPATES_IN", "lawsuit"), ("gold", "LOCATED_IN", "vmillion"),
                        ("lawrence", "POSSESSES", "trunk")]),
    ("Deluge", W, [("goto", "SURVIVES", "sealing"), ("wing", "SURVIVES", "sealing"),
                   ("bong", "SURVIVES", "sealing"), ("noda", "CAUSES", "sealing"),
                   ("goto", "OPPOSES", "ija"), ("sealing", "LOCATED_IN", "golgotha"),
                   ("lake_yamamoto", "PROTECTS", "golgotha"), ("rodolfo", "PARTICIPATES_IN", "sealing"),
                   ("bong", "ALLIES_WITH", "goto")]),
    ("Bust", N, [("randy", "STUDIES", "cryptonomicon"), ("randy", "PARTICIPATES_IN", "arrest"),
                 ("arrest", "LOCATED_IN", "manila"), ("amy", "LOVES", "randy"),
                 ("randy", "TRAVELS_TO", "manila")]),
    ("The Battle of Manila", W, [("bobby", "LEADS", "huks"), ("bobby", "PARTICIPATES_IN", "manila_battle"),
                                 ("huks", "FIGHTS", "ija"), ("manila_battle", "LOCATED_IN", "manila"),
                                 ("bobby", "LOVES", "glory"), ("bobby", "SEEKS", "altamiras"),
                                 ("glory", "MEMBER_OF", "huks")]),
    ("Captivity", N, [("alejandro", "SERVES", "randy"), ("randy", "LOCATED_IN", "makati"),
                      ("amy", "LOVES", "randy"), ("kepler", "SEEKS", "vmillion")]),
    ("Glamour", W, [("bobby", "FRIEND_OF", "goto"), ("bobby", "RESCUES", "goto"),
                    ("macarthur", "ALLIES_WITH", "goto"), ("macarthur", "PARTICIPATES_IN", "manila_battle"),
                    ("doug", "CHILD_OF", "bobby"), ("doug", "CHILD_OF", "glory"),
                    ("bobby", "TRAVELS_TO", "san_agustin"), ("goto", "TRAVELS_TO", "san_agustin"),
                    ("bobby", "SEEKS", "altamiras"), ("bobby", "PARTICIPATES_IN", "manila_battle"),
                    ("goto", "PARTICIPATES_IN", "manila_battle"), ("bobby", "SERVES", "macarthur")]),
    ("Wisdom", N, [("root", "KNOWS", "randy"), ("root", "LOCATED_IN", "makati"),
                   ("randy", "STUDIES", "pontifex"), ("randy", "LOCATED_IN", "makati"),
                   ("randy", "OPPOSES", "vaneck"), ("randy", "LOVES", "amy")]),
    ("Fall", W, [("bobby", "PARTICIPATES_IN", "lastmission"), ("lastmission", "LOCATED_IN", "caballo"),
                 ("bobby", "FIGHTS", "ija"), ("bobby", "DIES_IN", "lastmission")]),
    ("Metis", N, [("wing", "SEEKS", "gold"), ("wing", "SEEKS", "golgotha"),
                  ("root", "MENTORS", "randy"), ("randy", "STUDIES", "arethusa"),
                  ("randy", "USES", "pontifex"), ("randy", "OPPOSES", "vaneck"),
                  ("root", "LOCATED_IN", "makati"), ("randy", "LOCATED_IN", "makati"),
                  ("golgotha", "LOCATED_IN", "luzon")]),
    ("Slaves", W, [("lawrence", "TRAVELS_TO", "caballo"), ("lawrence", "WITNESSES", "lastmission"),
                   ("lawrence", "DISCOVERS", "abacus"), ("abacus", "LOCATED_IN", "caballo")]),
    ("Arethusa", N, [("randy", "CRACKS", "arethusa"), ("kepler", "KNOWS", "randy"),
                     ("chester", "ALLIES_WITH", "randy"), ("randy", "DISCOVERS", "golgotha"),
                     ("randy", "OPPOSES", "vaneck"), ("alejandro", "SERVES", "randy"),
                     ("avi", "TRAVELS_TO", "makati"), ("kepler", "TRAVELS_TO", "makati"),
                     ("root", "MENTORS", "randy"), ("gold", "LOCATED_IN", "golgotha")]),
    ("The Basement", W, [("lawrence", "CRACKS", "azure"), ("lawrence", "USES", "digicomp"),
                         ("azure", "DEPENDS_ON", "abacus"), ("lawrence", "STUDIES", "arethusa"),
                         ("lawrence", "LOCATED_IN", "manila")]),
    ("Akihabara", N, [("randy", "TRAVELS_TO", "tokyo"), ("avi", "TRAVELS_TO", "tokyo"),
                      ("root", "COMMUNICATES_WITH", "randy"), ("goto", "COMMUNICATES_WITH", "avi"),
                      ("crypt", "LOCATED_IN", "kinakuta"), ("epiphyte", "BUILDS", "crypt")]),
    ("Project X", W, [("lawrence", "FRIEND_OF", "turing"), ("lawrence", "COMMUNICATES_WITH", "turing")],
     ["abacus"]),
    ("Landfall", W, [("rudy", "LOCATED_IN", "vmillion"), ("bischoff", "COMMANDS", "vmillion"),
                     ("otto", "LOCATED_IN", "vmillion"), ("geb", "CHILD_OF", "julieta"),
                     ("rudy", "POSSESSES", "gold"), ("bischoff", "ALLIES_WITH", "rudy"),
                     ("vmillion", "MEMBER_OF", "ubc")], ["donitz", "bobby"]),
    ("Goto-sama", N, [("randy", "KNOWS", "goto"), ("furudenendu", "FAMILY_OF", "goto"),
                      ("avi", "POSSESSES", "gold"), ("goto", "BUILDS", "golgotha"),
                      ("randy", "DISCOVERS", "golgotha"), ("avi", "FOUNDS", "heap"),
                      ("goto", "LEADS", "gotoeng"), ("gotoeng", "INVESTS_IN", "epiphyte"),
                      ("avi", "KNOWS", "goto"), ("goto", "LOCATED_IN", "tokyo"),
                      ("randy", "LOCATED_IN", "tokyo")]),
    ("R.I.P.", W, [("goto", "PARTICIPATES_IN", "funeral"), ("root", "PARTICIPATES_IN", "funeral"),
                   ("goto", "MOURNS", "bobby"), ("root", "MOURNS", "bobby"),
                   ("root", "ALLIES_WITH", "goto"), ("funeral", "LOCATED_IN", "manila")]),
    ("Return", N, [("doug", "SALVAGES", "gold"), ("randy", "LOVES", "amy"),
                   ("root", "PARTICIPATES_IN", "excavation"), ("randy", "PARTICIPATES_IN", "excavation"),
                   ("doug", "PARTICIPATES_IN", "excavation"), ("tom", "PARTICIPATES_IN", "excavation"),
                   ("fohr", "PARTICIPATES_IN", "excavation"), ("nguyen", "PARTICIPATES_IN", "excavation"),
                   ("woo", "PARTICIPATES_IN", "excavation"), ("wing", "SEEKS", "golgotha"),
                   ("wing", "OPPOSES", "epiphyte"), ("ecurrency", "DEPENDS_ON", "gold"),
                   ("excavation", "LOCATED_IN", "golgotha"), ("randy", "TRAVELS_TO", "luzon"),
                   ("root", "LOCATED_IN", "luzon"), ("amy", "LOVES", "randy")]),
    ("Cribs", W, [("lawrence", "CRACKS", "arethusa"), ("lawrence", "WITNESSES", "funeral"),
                  ("lawrence", "KNOWS", "root"), ("lawrence", "KNOWS", "goto"),
                  ("lawrence", "FRIEND_OF", "rudy"), ("lawrence", "KNOWS", "bischoff"),
                  ("rudy", "POSSESSES", "gold"), ("lawrence", "USES", "digicomp"),
                  ("lawrence", "LOVES", "mary"), ("lawrence", "WRITES", "envelope"),
                  ("rudy", "POSSESSES", "envelope"), ("rudy", "SEEKS", "gold"),
                  ("root", "SEEKS", "gold"), ("goto", "SEEKS", "gold"),
                  ("bischoff", "SEEKS", "gold"), ("funeral", "LOCATED_IN", "manila"),
                  ("lawrence", "LOCATED_IN", "luzon")]),
    ("Cayuse", N, [("loeb", "FIGHTS", "amy"), ("loeb", "FIGHTS", "randy"),
                   ("root", "KILLS", "loeb"), ("root", "RESCUES", "randy"),
                   ("doug", "PARTICIPATES_IN", "excavation"), ("amy", "PARTICIPATES_IN", "excavation"),
                   ("randy", "PARTICIPATES_IN", "excavation"), ("root", "PARTICIPATES_IN", "excavation"),
                   ("nguyen", "PARTICIPATES_IN", "excavation")]),
    ("Black Chamber", W, [("comstock", "FOUNDS", "nsa"), ("comstock", "KNOWS", "lawrence"),
                          ("nsa", "USES", "huffduff"), ("nsa", "INTERCEPTS", "arethusa"),
                          ("lawrence", "ALLIES_WITH", "root"), ("lawrence", "ALLIES_WITH", "goto"),
                          ("lawrence", "FRIEND_OF", "turing"), ("lawrence", "PROTECTS", "arethusa"),
                          ("root", "USES", "arethusa"), ("goto", "USES", "arethusa"),
                          ("lawrence", "LOCATED_IN", "manila")]),
    ("Passage", W, [("navy", "CAUSES", "vm_sinking"), ("rudy", "DIES_IN", "vm_sinking"),
                    ("bischoff", "SURVIVES", "vm_sinking"), ("vm_sinking", "LOCATED_IN", "palawan"),
                    ("vmillion", "LOCATED_IN", "palawan"), ("bischoff", "COMMANDS", "vmillion"),
                    ("rudy", "LOCATED_IN", "vmillion"), ("rudy", "PROTECTS", "golgotha")]),
    ("Liquidity", N, [("randy", "RESCUES", "amy"), ("wing", "OPPOSES", "epiphyte"),
                      ("goto", "PARTICIPATES_IN", "excavation"), ("gotoeng", "PARTICIPATES_IN", "excavation"),
                      ("doug", "PARTICIPATES_IN", "excavation"), ("epiphyte", "SALVAGES", "gold"),
                      ("ecurrency", "DEPENDS_ON", "gold"), ("randy", "PARTICIPATES_IN", "excavation"),
                      ("furudenendu", "PARTICIPATES_IN", "excavation"), ("wing", "SEEKS", "golgotha"),
                      ("excavation", "LOCATED_IN", "golgotha"), ("randy", "LOVES", "amy"),
                      ("goto", "LOCATED_IN", "luzon")]),
]

assert len(SCENES) == 103, len(SCENES)


# =============================================================================
# Build
# =============================================================================

def _eid(key: str) -> str:
    return f"{ENT[key][1].lower()}_{key}"


def build() -> dict:
    ent_apps: dict[str, list[int]] = defaultdict(list)
    ent_eras: dict[str, set[str]] = defaultdict(set)
    rel_apps: dict[tuple, list[int]] = defaultdict(list)
    chapters = []

    for idx, scene in enumerate(SCENES):
        title, era, rels = scene[0], scene[1], scene[2]
        extra = scene[3] if len(scene) > 3 else []
        label = "Prologue" if idx == 0 else f"{idx} · {title}"
        chapters.append({"index": idx, "label": label, "word_count": 0, "era": era, "title": title})
        present: set[str] = set(extra)
        for s, p, o in rels:
            for k in (s, o):
                if k not in ENT:
                    raise KeyError(f"chapter {idx} {title!r}: unknown entity {k!r}")
            present.update((s, o))
            rel_apps[(s, p, o)].append(idx)
        for k in present:
            if k not in ENT:
                raise KeyError(f"chapter {idx} {title!r}: unknown entity {k!r}")
            ent_apps[k].append(idx)
            ent_eras[k].add(era)

    unused = [k for k in ENT if k not in ent_apps]
    if unused:
        raise ValueError(f"entities defined but never used: {unused}")

    entities = []
    for k, (name, label, desc) in ENT.items():
        apps = sorted(set(ent_apps[k]))
        birth_era = SCENES[apps[0]][1]
        entities.append({
            "id": _eid(k), "name": name, "label": label,
            "first_appearance": apps[0], "appearances": apps,
            "total_appearances": len(apps),
            "properties": {"era": birth_era, "bridge": len(ent_eras[k]) == 2, "description": desc},
        })

    relations = []
    for (s, p, o), apps in rel_apps.items():
        apps = sorted(set(apps))
        relations.append({
            "source_id": _eid(s), "source_name": ENT[s][0],
            "target_id": _eid(o), "target_name": ENT[o][0],
            "label": p, "first_appearance": apps[0], "appearances": apps,
            "total_appearances": len(apps), "properties": {},
        })
    relations.sort(key=lambda r: (r["first_appearance"], r["source_id"], r["target_id"]))

    return {
        "metadata": {
            "work_key": "cryptonomicon",
            "work_name": "Cryptonomicon",
            "extraction_model": "demo-data (hand-anchored from a chapter synopsis; not LLM extraction)",
            "total_chapters": len(chapters),
            "total_entities": len(entities),
            "total_relations": len(relations),
            "extracted_at": "2026-09-22T00:00:00",
            "chapter_label": "Chapter",
            "demo": True,
            "demo_note": "Demo constellation — hand-anchored from a chapter synopsis",
            "threads": {"1940s": "1940s thread", "1990s": "1990s thread"},
        },
        "chapters": chapters,
        "entities": entities,
        "relations": relations,
        "timeline": [],
    }


# =============================================================================
# Stats used in the article (mirrors the Observatory's own arithmetic)
# =============================================================================

def stats(data: dict) -> None:
    ents = {e["id"]: e for e in data["entities"]}
    links = [r for r in data["relations"]
             if r["source_id"] in ents and r["target_id"] in ents and r["source_id"] != r["target_id"]]
    C = len(data["chapters"])
    eras = [c["era"] for c in data["chapters"]]
    print(f"chapters: {C}  ({eras.count(W)} in the 1940s thread, {eras.count(N)} in the 1990s thread)")
    print(f"entities: {len(ents)}  relations: {len(links)}")
    by_era = Counter(e["properties"]["era"] for e in ents.values())
    print(f"stars born in 1940s thread: {by_era[W]}   born in 1990s thread: {by_era[N]}")
    bridges = [e for e in ents.values() if e["properties"]["bridge"]]
    print(f"bridge stars (named in both threads): {len(bridges)}")
    for e in sorted(bridges, key=lambda e: e["first_appearance"]):
        print(f"   {e['name']:<34} {e['label']:<12} born ch {e['first_appearance']:>3} ({e['properties']['era']})")

    # longest run of consecutive chapters in one era
    runs, cur, best = [], 1, (1, 0)
    for i in range(1, C):
        cur = cur + 1 if eras[i] == eras[i - 1] else 1
        if cur > best[0]:
            best = (cur, i)
    print(f"longest single-era run: {best[0]} chapters ending at ch {best[1]} ({eras[best[1]]})")
    switches = sum(1 for i in range(1, C) if eras[i] != eras[i - 1])
    print(f"era switches between consecutive chapters: {switches}")

    # cross-era chords
    def era_of(eid): return ents[eid]["properties"]["era"]
    cross = [l for l in links if era_of(l["source_id"]) != era_of(l["target_id"])]
    print(f"chords joining a 1940s-born star to a 1990s-born star: {len(cross)} of {len(links)}")
    for l in sorted(cross, key=lambda l: l["first_appearance"]):
        print(f"   ch {l['first_appearance']:>3}  {l['source_name']} —{l['label']}→ {l['target_name']}")

    # degree, hubs, centralization at cutoffs (Freeman, undirected, multigraph like the page)
    def snapshot(p):
        deg = Counter()
        n_ent = [e for e in ents.values() if e["first_appearance"] < p]
        born = [l for l in links if l["first_appearance"] < p]
        for l in born:
            deg[l["source_id"]] += 1; deg[l["target_id"]] += 1
        n = len(n_ent)
        if n < 3:
            return n, len(born), 0.0, None
        mx = max(deg.values(), default=0)
        cen = sum(mx - deg[e["id"]] for e in n_ent) / ((n - 1) * (n - 2))
        hub = max(n_ent, key=lambda e: deg[e["id"]])
        return n, len(born), cen, (hub["name"], deg[hub["id"]])
    print("cutoff  entities  relations  centralization  hub")
    for frac in (0.25, 0.5, 0.75, 1.0):
        p = frac * C
        n, m, cen, hub = snapshot(p + 1e-9)
        print(f"{int(frac*100):>5}%  {n:>8}  {m:>9}  {cen:>14.3f}  {hub}")
    # top stars by final degree
    deg = Counter()
    for l in links:
        deg[l["source_id"]] += 1; deg[l["target_id"]] += 1
    print("top 12 stars by degree:")
    for eid, d in deg.most_common(12):
        e = ents[eid]
        print(f"   {e['name']:<34} {d:>3}  born ch {e['first_appearance']:>3}  {e['properties']['era']}"
              f"{'  bridge' if e['properties']['bridge'] else ''}")
    # per-thread degree leaders
    for era in (W, N):
        sub = [(eid, d) for eid, d in deg.most_common() if era_of(eid) == era][:5]
        print(f"top {era}-born: " + ", ".join(f"{ents[e]['name']} ({d})" for e, d in sub))
    # EKG: busiest chapters
    ekg = Counter()
    for e in ents.values(): ekg[e["first_appearance"]] += 1
    for l in links: ekg[l["first_appearance"]] += 1
    print("busiest chapters (new stars + new chords): " +
          ", ".join(f"{data['chapters'][i]['label']} ({v})" for i, v in ekg.most_common(6)))
    # when does each thread finish casting?
    for era in (W, N):
        firsts = sorted(e["first_appearance"] for e in ents.values()
                        if e["properties"]["era"] == era and e["label"] == "CHARACTER")
        half = firsts[len(firsts) // 2]
        print(f"{era}-born characters: {len(firsts)}; half of them born by ch {half}, "
              f"last born ch {firsts[-1]}")
    # relation-type mix by thread
    mix = {W: Counter(), N: Counter()}
    for l in links:
        mix[eras[l["first_appearance"]]][l["label"]] += 1
    for era in (W, N):
        print(f"{era} top relation types: {mix[era].most_common(8)}")


# =============================================================================
# Inject into the Observatory page(s)
# =============================================================================

def inject(html_path: Path, data: dict) -> None:
    src = html_path.read_text(encoding="utf-8")
    m = re.search(r"^const DATA = (\{.*\});?\s*$", src, re.M)
    if not m:
        raise RuntimeError(f"no `const DATA = {{...}}` line in {html_path}")
    existing = json.loads(m.group(1))
    existing["cryptonomicon"] = data
    line = "const DATA = " + json.dumps(existing, ensure_ascii=False) + ";"
    src = src[:m.start()] + line + src[m.end():]
    html_path.write_text(src, encoding="utf-8")
    print(f"injected cryptonomicon into {html_path} ({len(data['entities'])} entities, "
          f"{len(data['relations'])} relations)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stats", action="store_true", help="print the numbers quoted in the article")
    ap.add_argument("--no-inject", action="store_true", help="only write output/ JSON")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    data = build()
    out = here / "output" / "cryptonomicon_temporal_kg.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    if not args.no_inject:
        for p in (here / "narrative-observatory.html", here / "docs" / "index.html"):
            if p.exists():
                inject(p, data)
    if args.stats:
        stats(data)


if __name__ == "__main__":
    main()
