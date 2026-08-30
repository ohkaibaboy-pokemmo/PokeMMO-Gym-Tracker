APP_NAME = "PokeMMO Gym Cooldown Tracker"
APP_VERSION = "0.6.0-dev"
COOLDOWN_HOURS = 18
REQUIRED_OTHER_TRAINERS = 5

REGIONS = ["All", "Kanto", "Johto", "Hoenn", "Sinnoh", "Unova"]
DISPLAY_MODES = [
    "All",
    "Remaining",
    "Ready only",
    "Cooldowns / blocked",
]

# Canonical vanilla PokeMMO gym table for the five currently supported regions.
# Kanto intentionally omits Viridian/Giovanni from the default rerun table.
GYMS = [
    ("Kanto", "Pewter", "Brock"),
    ("Kanto", "Cerulean", "Misty"),
    ("Kanto", "Vermilion", "Lt. Surge"),
    ("Kanto", "Celadon", "Erika"),
    ("Kanto", "Fuchsia", "Koga"),
    ("Kanto", "Saffron", "Sabrina"),
    ("Kanto", "Cinnabar", "Blaine"),
    ("Johto", "Violet", "Falkner"),
    ("Johto", "Azalea", "Bugsy"),
    ("Johto", "Goldenrod", "Whitney"),
    ("Johto", "Ecruteak", "Morty"),
    ("Johto", "Cianwood", "Chuck"),
    ("Johto", "Olivine", "Jasmine"),
    ("Johto", "Mahogany", "Pryce"),
    ("Johto", "Blackthorn", "Clair"),
    ("Hoenn", "Rustboro", "Roxanne"),
    ("Hoenn", "Dewford", "Brawly"),
    ("Hoenn", "Mauville", "Wattson"),
    ("Hoenn", "Lavaridge", "Flannery"),
    ("Hoenn", "Petalburg", "Norman"),
    ("Hoenn", "Fortree", "Winona"),
    ("Hoenn", "Mossdeep", "Tate & Liza"),
    ("Hoenn", "Sootopolis", "Juan"),
    ("Sinnoh", "Oreburgh", "Roark"),
    ("Sinnoh", "Eterna", "Gardenia"),
    ("Sinnoh", "Veilstone", "Maylene"),
    ("Sinnoh", "Pastoria", "Crasher Wake"),
    ("Sinnoh", "Hearthome", "Fantina"),
    ("Sinnoh", "Canalave", "Byron"),
    ("Sinnoh", "Snowpoint", "Candice"),
    ("Sinnoh", "Sunyshore", "Volkner"),
    ("Unova", "Striaton (Grass)", "Cilan"),
    ("Unova", "Striaton (Fire)", "Chili"),
    ("Unova", "Striaton (Water)", "Cress"),
    ("Unova", "Nacrene", "Lenora"),
    ("Unova", "Castelia", "Burgh"),
    ("Unova", "Nimbasa", "Elesa"),
    ("Unova", "Driftveil", "Clay"),
    ("Unova", "Mistralton", "Skyla"),
    ("Unova", "Icirrus", "Brycen"),
    ("Unova", "Opelucid", "Iris"),
]

LEADER_ALIASES = {
    "ltsurge": "Lt. Surge",
    "wake": "Crasher Wake",
    "crasherwake": "Crasher Wake",
    "tate&liza": "Tate & Liza",
    "tateandliza": "Tate & Liza",
    "tateliza": "Tate & Liza",
    # Older tracker builds used Drayden for Opelucid. Current project data uses Iris.
    "drayden": "Iris",
}

# v0.6 default: every detected trainer victory counts toward the 5-other-trainer
# requirement unless we have explicit evidence that a specific opponent should not.
# Keep this opt-out list narrow and evidence-driven.
EXCLUDED_5_RULE_TRAINERS = []

# Legacy verified catalogue retained for backwards-compatible state/history only.
# It is no longer an allow-list for whether a trainer counts toward the 5-rule.
VERIFIED_REMATCH_TRAINERS = [
    "PI Carlos",
    "Socialite Marian",
    "Gentleman Yan",
    "Lady Jacki",
    "Lady Gillian",
    "Lady Isabel",
    "Rich Boy Manuel",
    "Lady Cindy",
    "Ace Trainer Johan",
    "Ace Trainer Cheyenne",
    "Veteran Karla",
    "Veteran Chester",
    "Beauty Valerie",
    "Gentleman Coses",
    "Picnicker Sharon",
    "Socialite Reina",
    "Gentleman Jeremy",
    "Lady Melissa",
]

SIX_PILLOWS_ROUTE_NAME = "6 Pillows — Current 30"
SIX_PILLOWS_ROUTE = [
    "Bugsy", "Jasmine", "Whitney", "Chuck",
    "Lt. Surge", "Koga", "Sabrina", "Blaine", "Erika", "Misty",
    "Crasher Wake", "Maylene", "Gardenia", "Volkner", "Roark",
    "Burgh", "Skyla", "Iris", "Cilan", "Chili", "Cress", "Elesa", "Lenora",
    "Wattson", "Norman", "Tate & Liza", "Roxanne", "Flannery", "Juan", "Winona",
]

# Source-verified from the current Prehistoric 5 Main Route document (28 gyms).
# The document also contains alternate/test/mobile paths; only the explicitly
# labelled Main Route is built in here so the tracker never silently mixes them.
PREHISTORIC_5_MAIN_ROUTE_NAME = "Prehistoric 5 — Main 28"
PREHISTORIC_5_MAIN_ROUTE = [
    "Flannery", "Wattson", "Winona", "Brawly", "Norman",
    "Burgh", "Elesa", "Clay", "Chili", "Cilan", "Cress", "Skyla", "Brycen", "Iris",
    "Falkner", "Pryce", "Whitney", "Bugsy", "Jasmine", "Chuck",
    "Maylene", "Gardenia", "Volkner", "Crasher Wake",
    "Lt. Surge", "Brock", "Misty", "Erika",
]

BUILTIN_ROUTES = {
    SIX_PILLOWS_ROUTE_NAME: SIX_PILLOWS_ROUTE,
    PREHISTORIC_5_MAIN_ROUTE_NAME: PREHISTORIC_5_MAIN_ROUTE,
}
