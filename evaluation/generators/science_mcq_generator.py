"""Science MCQ generator (ARC-Challenge style) for Project Kestrel (Step 1).

Generates multiple-choice science questions across core domains:
- Physics (mechanics, thermodynamics, waves, electricity, optics, modern physics)
- Chemistry (matter, reactions, periodic table, stoichiometry, solutions, acids & bases)
- Biology (cellular biology, genetics, ecosystems, physiology, evolution)
- Earth & Space (astronomy, geology, atmosphere, hydrological cycle, plate tectonics)

Evaluated via answer_key matching (A, B, C, D). Deterministic with explicit seed.
Supports seen_prompts to guarantee 100% zero prompt duplication across partitions.
"""

from __future__ import annotations

import random
from typing import Any


def _make_physics_item(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(
        [
            "force",
            "kinetic_energy",
            "ohms_law",
            "wave_speed",
            "gravitation",
            "work",
            "density",
            "momentum",
            "power",
            "pressure",
            "heat",
            "acceleration",
        ]
    )
    if kind == "force":
        m = rng.randint(2, 200)
        a = rng.randint(2, 50)
        f_val = m * a
        stem = f"A mass of {m} kg accelerates at {a} m/s² on a horizontal frictionless surface. What net force is acting on the mass?"
        correct = f"{f_val} N"
        distractors = [f"{m + a} N", f"{f_val * 2} N", f"{max(1, f_val // 2)} N"]
    elif kind == "kinetic_energy":
        m = rng.choice([2, 4, 6, 8, 10, 12, 16, 20, 25])
        v = rng.randint(3, 40)
        ke = int(0.5 * m * (v**2))
        stem = f"What is the kinetic energy of a {m} kg body traveling at a velocity of {v} m/s?"
        correct = f"{ke} J"
        distractors = [f"{m * v} J", f"{ke * 2} J", f"{ke + 100} J"]
    elif kind == "ohms_law":
        r = rng.randint(5, 120)
        i = rng.randint(2, 25)
        v = r * i
        stem = f"An electrical circuit contains a steady load of {r} Ω with a current of {i} A. What is the potential difference across the load?"
        correct = f"{v} V"
        distractors = [f"{r + i} V", f"{max(1, v // 2)} V", f"{v * 2} V"]
    elif kind == "wave_speed":
        freq = rng.choice([50, 120, 250, 440, 500, 880, 1000, 1500])
        wavelength = rng.choice([0.2, 0.5, 0.8, 1.2, 1.5, 2.0, 3.4])
        speed = round(freq * wavelength, 1)
        stem = f"A periodic sound wave has a frequency of {freq} Hz and a wavelength of {wavelength} m. What is its propagation speed?"
        correct = f"{speed} m/s"
        distractors = [
            f"{round(freq / wavelength, 1)} m/s",
            f"{round(speed * 2, 1)} m/s",
            f"{round(speed / 2, 1)} m/s",
        ]
    elif kind == "work":
        force = rng.randint(10, 300)
        dist = rng.randint(3, 50)
        w = force * dist
        stem = f"A mechanical crane exerts an upward force of {force} N to lift a container through a vertical displacement of {dist} m. How much work is performed?"
        correct = f"{w} J"
        distractors = [f"{force + dist} J", f"{w * 2} J", f"{max(10, w // 2)} J"]
    elif kind == "momentum":
        mass = rng.randint(3, 50)
        vel = rng.randint(4, 40)
        p = mass * vel
        stem = f"What is the magnitude of linear momentum for an object of mass {mass} kg traveling at {vel} m/s?"
        correct = f"{p} kg·m/s"
        distractors = [
            f"{mass + vel} kg·m/s",
            f"{p * 2} kg·m/s",
            f"{int(0.5 * mass * vel**2)} kg·m/s",
        ]
    elif kind == "density":
        vol = rng.choice([5, 10, 15, 20, 25, 40, 50, 80, 100])
        density = rng.choice([2, 3, 4, 5, 7, 8, 11, 13])
        mass = vol * density
        stem = f"A solid metal sample has a volume of {vol} cm³ and a total mass of {mass} g. What is the density of the metal?"
        correct = f"{density} g/cm³"
        distractors = [
            f"{vol + mass} g/cm³",
            f"{density * 2} g/cm³",
            f"{max(1, density // 2)} g/cm³",
        ]
    elif kind == "power":
        w = rng.choice([100, 250, 500, 1000, 2000, 4500])
        t = rng.choice([2, 5, 10, 20, 25, 50])
        p = w // t
        stem = f"An electric motor completes {w} J of mechanical work in a duration of {t} seconds. What is the average power output of the motor?"
        correct = f"{p} W"
        distractors = [f"{w * t} W", f"{p * 2} W", f"{max(5, p - 15)} W"]
    elif kind == "pressure":
        f = rng.choice([100, 200, 500, 1000, 2500, 4000])
        a = rng.choice([2, 4, 5, 10, 20])
        press = f // a
        stem = f"A normal force of {f} N is uniformly distributed over a planar contact area of {a} m². What pressure is exerted on the surface?"
        correct = f"{press} Pa"
        distractors = [f"{f * a} Pa", f"{press * 2} Pa", f"{press + 50} Pa"]
    elif kind == "heat":
        m = rng.choice([2, 5, 10])
        c = rng.choice([4200, 900, 450])  # water, aluminum, iron
        dt = rng.choice([5, 10, 15, 20])
        q = m * c * dt
        subst = "water" if c == 4200 else ("aluminum" if c == 900 else "iron")
        stem = f"How much heat energy is required to raise the temperature of {m} kg of {subst} (specific heat capacity {c} J/(kg·K)) by {dt} K?"
        correct = f"{q} J"
        distractors = [f"{q // 2} J", f"{q * 2} J", f"{m * dt * 100} J"]
    elif kind == "acceleration":
        vi = rng.randint(0, 20)
        vf = vi + rng.randint(15, 60)
        t = rng.choice([2, 3, 5, 6, 10])
        a = round((vf - vi) / t, 2)
        stem = f"A vehicle uniformly accelerates along a straight road from an initial velocity of {vi} m/s to {vf} m/s in {t} seconds. What is its acceleration?"
        correct = f"{a} m/s²"
        distractors = [f"{round(a * 2, 2)} m/s²", f"{round(a / 2, 2)} m/s²", f"{vf - vi} m/s²"]
    else:  # gravitation
        factor = rng.choice([2, 3, 4, 5])
        stem = f"According to Newton's Law of Universal Gravitation, if the distance separating two point masses is increased by a factor of {factor}, the gravitational attraction between them changes by what factor?"
        correct = f"Decreases to 1/{factor**2} of original"
        distractors = [
            f"Decreases to 1/{factor} of original",
            f"Increases by {factor} times",
            f"Increases by {factor**2} times",
        ]

    return stem, correct, distractors


def _make_chemistry_item(rng: random.Random) -> tuple[str, str, list[str]]:
    elements = [
        ("Hydrogen", 1, "H", "nonmetal", 1.0),
        ("Helium", 2, "He", "noble gas", 4.0),
        ("Lithium", 3, "Li", "alkali metal", 6.9),
        ("Beryllium", 4, "Be", "alkaline earth metal", 9.0),
        ("Boron", 5, "B", "metalloid", 10.8),
        ("Carbon", 6, "C", "nonmetal", 12.0),
        ("Nitrogen", 7, "N", "nonmetal", 14.0),
        ("Oxygen", 8, "O", "chalcogen", 16.0),
        ("Fluorine", 9, "F", "halogen", 19.0),
        ("Neon", 10, "Ne", "noble gas", 20.2),
        ("Sodium", 11, "Na", "alkali metal", 23.0),
        ("Magnesium", 12, "Mg", "alkaline earth metal", 24.3),
        ("Aluminum", 13, "Al", "post-transition metal", 27.0),
        ("Silicon", 14, "Si", "metalloid", 28.1),
        ("Phosphorus", 15, "P", "nonmetal", 31.0),
        ("Sulfur", 16, "S", "chalcogen", 32.1),
        ("Chlorine", 17, "Cl", "halogen", 35.5),
        ("Argon", 18, "Ar", "noble gas", 39.9),
        ("Potassium", 19, "K", "alkali metal", 39.1),
        ("Calcium", 20, "Ca", "alkaline earth metal", 40.1),
        ("Titanium", 22, "Ti", "transition metal", 47.9),
        ("Iron", 26, "Fe", "transition metal", 55.8),
        ("Copper", 29, "Cu", "transition metal", 63.5),
        ("Zinc", 30, "Zn", "transition metal", 65.4),
        ("Bromine", 35, "Br", "halogen", 79.9),
        ("Silver", 47, "Ag", "transition metal", 107.9),
        ("Iodine", 53, "I", "halogen", 126.9),
        ("Gold", 79, "Au", "transition metal", 197.0),
    ]
    kind = rng.choice(
        [
            "atomic_number",
            "group_class",
            "ph_nature",
            "reaction_type",
            "molar_mass",
            "gas_law",
            "subatomic",
        ]
    )
    if kind == "atomic_number":
        name, z, sym, _, _ = rng.choice(elements)
        stem = f"What is the atomic number (number of nuclear protons) of the neutral chemical element {name} ({sym})?"
        correct = str(z)
        distractors = [str(z + 1), str(max(1, z - 2)), str(z + 6)]
    elif kind == "group_class":
        name, _, sym, cl, _ = rng.choice(elements)
        stem = f"To which primary group or classification family does the element {name} ({sym}) belong on the periodic table?"
        correct = cl.capitalize()
        all_classes = [
            "Alkali metal",
            "Alkaline earth metal",
            "Transition metal",
            "Halogen",
            "Noble gas",
            "Metalloid",
            "Nonmetal",
            "Post-transition metal",
            "Chalcogen",
        ]
        distractors = [c for c in all_classes if c.lower() != cl.lower()][:3]
    elif kind == "ph_nature":
        ph = round(rng.uniform(1.0, 13.5), 1)
        stem = f"At 25 °C, an aqueous experimental solution exhibits a measured pH of {ph}. What is the correct classification of this solution?"
        if ph < 6.8:
            correct = "Acidic"
            distractors = ["Basic (Alkaline)", "Neutral", "Non-polar"]
        elif 6.8 <= ph <= 7.2:
            correct = "Neutral"
            distractors = ["Acidic", "Basic (Alkaline)", "Supercritical"]
        else:
            correct = "Basic (Alkaline)"
            distractors = ["Acidic", "Neutral", "Non-polar"]
    elif kind == "subatomic":
        name, z, sym, _, mass = rng.choice(elements)
        mass_int = int(round(mass))
        neutrons = mass_int - z
        stem = f"An atom of isotope {name}-{mass_int} ({sym}) has an atomic number of {z}. How many neutrons are contained within its nucleus?"
        correct = str(neutrons)
        distractors = [str(z), str(mass_int), str(max(1, neutrons - 2))]
    elif kind == "molar_mass":
        compounds = [
            ("water (H₂O)", 18),
            ("carbon dioxide (CO₂)", 44),
            ("methane (CH₄)", 16),
            ("sodium chloride (NaCl)", 58),
            ("glucose (C₆H₁₂O₆)", 180),
            ("sulfuric acid (H₂SO₄)", 98),
            ("ammonia (NH₃)", 17),
        ]
        comp, mm = rng.choice(compounds)
        moles = rng.randint(2, 6)
        total_g = moles * mm
        stem = f"What is the total mass in grams of {moles} moles of {comp} given its molar mass of approximately {mm} g/mol?"
        correct = f"{total_g} g"
        distractors = [f"{total_g + mm} g", f"{total_g // 2} g", f"{mm * 10} g"]
    elif kind == "gas_law":
        v1 = rng.choice([2, 4, 5, 8, 10])
        p1 = rng.choice([1, 2, 3, 4])
        v2 = v1 * rng.choice([2, 4])
        p2 = round((p1 * v1) / v2, 2)
        stem = f"A sample of ideal gas occupies an initial volume of {v1} L at a pressure of {p1} atm. If the gas expands to {v2} L at constant temperature (Boyle's Law), what is the final pressure?"
        correct = f"{p2} atm"
        distractors = [f"{p2 * 2} atm", f"{p1 * 2} atm", f"{p2 + 1.0} atm"]
    else:  # reaction_type
        rxn_types = [
            (
                "Combustion",
                "Propane (C₃H₈) reacts vigorously with oxygen gas to yield carbon dioxide and water vapor.",
            ),
            (
                "Neutralization",
                "Aqueous nitric acid reacts with potassium hydroxide to form aqueous potassium nitrate and liquid water.",
            ),
            (
                "Decomposition",
                "Solid potassium chlorate is heated to produce solid potassium chloride and oxygen gas.",
            ),
            (
                "Synthesis (Combination)",
                "Magnesium ribbon burns in pure nitrogen gas to synthesize magnesium nitride powder.",
            ),
            (
                "Precipitation (Double Displacement)",
                "Aqueous lead(II) nitrate is added to aqueous potassium iodide, producing bright yellow lead(II) iodide solid precipitate.",
            ),
            (
                "Single Displacement",
                "Zinc metal placed in copper(II) sulfate solution produces solid copper metal and aqueous zinc sulfate.",
            ),
        ]
        chosen_type, desc = rng.choice(rxn_types)
        stem = f"Which fundamental category of chemical reaction is exemplified by: '{desc}'?"
        correct = chosen_type
        distractors = [t for t, _ in rxn_types if t != chosen_type][:3]

    return stem, correct, distractors


def _make_biology_item(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["organelle", "genetics_cross", "dna_base", "ecosystem", "mitosis"])
    if kind == "organelle":
        organelles = [
            (
                "Mitochondria",
                "generates cellular ATP via oxidative phosphorylation and contains its own circular DNA genome",
            ),
            (
                "Ribosome",
                "catalyzes biological protein synthesis by translating messenger RNA sequences",
            ),
            (
                "Chloroplast",
                "captures photon energy to synthesize carbohydrates via the light reactions and Calvin cycle",
            ),
            (
                "Golgi apparatus",
                "modifies, packages, and tags proteins and glycoproteins synthesized in the rough ER for exocytosis",
            ),
            (
                "Rough endoplasmic reticulum",
                "features membrane-bound ribosomes dedicated to synthesizing secretory and integral membrane proteins",
            ),
            (
                "Lysosome",
                "contains acidic hydrolases specialized for intracellular digestion of macromolecules and autophagosomes",
            ),
            (
                "Peroxisome",
                "breaks down long-chain fatty acids via beta-oxidation and detoxifies hydrogen peroxide using catalase",
            ),
            (
                "Nucleolus",
                "transcribes ribosomal RNA and orchestrates the assembly of ribosomal subunits within the nucleus",
            ),
        ]
        org_name, org_fn = rng.choice(organelles)
        stem = f"Which eukaryotic cellular structure {org_fn}?"
        correct = org_name
        distractors = [name for name, _ in organelles if name != org_name][:3]
    elif kind == "genetics_cross":
        crosses = [
            (
                "two heterozygous pea plants (Aa x Aa)",
                "dominant phenotype",
                "75% (3/4)",
                ["25% (1/4)", "50% (1/2)", "100%"],
            ),
            (
                "two heterozygous pea plants (Aa x Aa)",
                "homozygous recessive genotype (aa)",
                "25% (1/4)",
                ["50% (1/2)", "75% (3/4)", "0%"],
            ),
            (
                "a heterozygous plant (Aa) and a homozygous recessive plant (aa)",
                "recessive phenotype",
                "50% (1/2)",
                ["25% (1/4)", "75% (3/4)", "100%"],
            ),
            (
                "a homozygous dominant (AA) and a homozygous recessive plant (aa)",
                "heterozygous genotype (Aa)",
                "100%",
                ["50% (1/2)", "25% (1/4)", "0%"],
            ),
        ]
        cross_desc, outcome, corr, dists = rng.choice(crosses)
        stem = f"In classical Mendelian genetics, a monohybrid cross between {cross_desc} produces what expected probability of offspring displaying the {outcome}?"
        correct = corr
        distractors = dists
    elif kind == "dna_base":
        bases = [("Adenine (A)", "Thymine (T)"), ("Cytosine (C)", "Guanine (G)")]
        b1, b2 = rng.choice(bases)
        if rng.random() > 0.5:
            b1, b2 = b2, b1
        h_bonds = 2 if "Adenine" in b1 or "Thymine" in b1 else 3
        stem = f"In B-form double-stranded DNA, the nitrogenous base {b1} forms complementary hydrogen bonds specifically with:"
        correct = f"{b2} (via {h_bonds} hydrogen bonds)"
        other = "Guanine (G)" if "Adenine" in b1 or "Thymine" in b1 else "Adenine (A)"
        distractors = [
            f"{other} (via {h_bonds} hydrogen bonds)",
            f"{b2} (via {5 - h_bonds} hydrogen bonds)",
            "Uracil (U) (in DNA backbone)",
        ]
    elif kind == "mitosis":
        phases = [
            (
                "Prophase",
                "chromatin condenses into visible chromosomes and the mitotic spindle begins assembling",
            ),
            (
                "Metaphase",
                "sister chromatid pairs align uniformly along the central equatorial plane of the cell",
            ),
            (
                "Anaphase",
                "cohesin proteins are cleaved and sister chromatids separate toward opposite spindle poles",
            ),
            (
                "Telophase",
                "nuclear envelopes reform around separated daughter chromosomes as chromatin decondenses",
            ),
        ]
        p_name, p_desc = rng.choice(phases)
        stem = f"During which specific stage of eukaryotic mitosis do {p_desc}?"
        correct = p_name
        distractors = [name for name, _ in phases if name != p_name][:3]
    else:  # ecosystem
        roles = [
            (
                "Autotroph (Primary Producer)",
                "fixes solar or chemical energy to generate organic matter from inorganic precursors",
            ),
            (
                "Herbivore (Primary Consumer)",
                "feeds directly and exclusively on autotrophic photosynthetic organisms",
            ),
            (
                "Carnivore (Secondary Consumer)",
                "preys upon primary consumer organisms in a trophic food web",
            ),
            (
                "Decomposer (Saprotroph)",
                "secretes extracellular digestive enzymes to degrade dead organic matter into soil nutrients",
            ),
            (
                "Apex predator",
                "occupies the highest trophic level in an ecological community with no natural predators",
            ),
        ]
        r_name, r_desc = rng.choice(roles)
        stem = f"In ecological trophic systems, which functional classification designates an organism that {r_desc}?"
        correct = r_name
        distractors = [name for name, _ in roles if name != r_name][:3]

    return stem, correct, distractors


def _make_earth_space_item(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["atmosphere", "planets", "geology", "astronomy", "hydrology"])
    if kind == "atmosphere":
        layers = [
            (
                "Troposphere",
                "the lowest atmospheric layer where weather systems circulate and air temperature decreases with altitude",
            ),
            (
                "Stratosphere",
                "the layer containing the ozone layer where temperature increases with altitude due to UV absorption",
            ),
            (
                "Mesosphere",
                "the coldest atmospheric layer where the majority of meteors ablate and burn up upon entry",
            ),
            (
                "Thermosphere",
                "the high-altitude layer containing the ionosphere where auroral displays occur",
            ),
            (
                "Exosphere",
                "the outermost rarefied atmospheric fringe that gradually merges into interplanetary space",
            ),
        ]
        layer, desc = rng.choice(layers)
        stem = f"Which distinct layer of Earth's atmosphere is {desc}?"
        correct = layer
        distractors = [lay for lay, _ in layers if lay != layer][:3]
    elif kind == "planets":
        planets = [
            (
                "Mercury",
                "the smallest terrestrial planet and has the shortest orbital period around the Sun",
            ),
            (
                "Venus",
                "experiences a runaway carbon dioxide greenhouse effect, maintaining a mean surface temperature over 460 °C",
            ),
            (
                "Mars",
                "possesses Olympus Mons, the largest volcano in the Solar System, and vast iron-oxide surface deposits",
            ),
            (
                "Jupiter",
                "the most massive gas giant in the Solar System, hosting the Great Red Spot anticyclonic storm",
            ),
            ("Saturn", "features the most prominent and extensive system of icy planetary rings"),
            (
                "Uranus",
                "an ice giant with an axial tilt of approximately 98 degrees, rotating virtually on its side",
            ),
            (
                "Neptune",
                "the outermost major planet in the Solar System, characterized by dynamic supersonic wind speeds",
            ),
        ]
        p_name, p_fact = rng.choice(planets)
        stem = f"Which Solar System planet is characterized as {p_fact}?"
        correct = p_name
        distractors = [name for name, _ in planets if name != p_name][:3]
    elif kind == "geology":
        rocks = [
            (
                "Igneous rock",
                "crystallizes directly from the cooling of subterranean magma or surface lava",
            ),
            (
                "Sedimentary rock",
                "forms through the cumulative deposition, compaction, and lithification of mineral sediments",
            ),
            (
                "Metamorphic rock",
                "arises from the structural transformation of pre-existing rock under elevated pressure and temperature without melting",
            ),
        ]
        r_type, r_desc = rng.choice(rocks)
        stem = f"Which primary petrological rock classification describes rocks that {r_desc}?"
        correct = r_type
        distractors = [t for t, _ in rocks if t != r_type] + ["Regolith agglomerate"]
    elif kind == "astronomy":
        topics = [
            (
                "Light-year",
                "the distance traveled by an electromagnetic wave in a vacuum over one Julian year",
            ),
            (
                "Astronomical Unit (AU)",
                "the mean distance between the center of the Earth and the center of the Sun",
            ),
            (
                "Supernova",
                "the catastrophic energetic explosion marking the terminal collapse of a massive star",
            ),
            (
                "Neutron star",
                "the extremely dense stellar remnant composed predominantly of degenerate neutrons after a core-collapse event",
            ),
            (
                "Event horizon",
                "the gravitational boundary around a black hole beyond which no electromagnetic radiation can escape",
            ),
        ]
        term, desc = rng.choice(topics)
        stem = f"In astrophysical terminology, what is defined as '{desc}'?"
        correct = term
        distractors = [t for t, _ in topics if t != term][:3]
    else:  # hydrology / plate tectonics
        concepts = [
            (
                "Subduction zone",
                "a convergent tectonic boundary where one denser tectonic plate sinks beneath an overriding plate into the mantle",
            ),
            (
                "Mid-ocean ridge",
                "a divergent underwater tectonic mountain system formed where seafloor spreading creates new oceanic crust",
            ),
            (
                "Aquifer",
                "an underground geological stratum of permeable rock or sediment that stores and yields groundwater",
            ),
            (
                "Transform fault",
                "a tectonic boundary where lithospheric plates slide horizontally past one another, such as the San Andreas Fault",
            ),
        ]
        term, desc = rng.choice(concepts)
        stem = f"In Earth sciences, which geological feature or structure is defined as: '{desc}'?"
        correct = term
        distractors = [t for t, _ in concepts if t != term][:3]

    return stem, correct, distractors


def generate_science_mcq_suite(
    count: int = 200,
    seed: int = 20260101,
    prefix: str = "sci_val",
    split: str = "validation",
    seen_prompts: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate a suite of distinct science MCQ items deterministically."""
    rng = random.Random(seed)
    items: list[dict[str, Any]] = []
    generators = [
        _make_physics_item,
        _make_chemistry_item,
        _make_biology_item,
        _make_earth_space_item,
    ]

    attempts = 0
    max_attempts = count * 200

    while len(items) < count and attempts < max_attempts:
        attempts += 1
        gen = rng.choice(generators)
        stem, correct_text, distractors = gen(rng)

        # Check prompt uniqueness
        prompt_norm = " ".join(stem.lower().split())
        if seen_prompts is not None:
            if prompt_norm in seen_prompts:
                continue
            seen_prompts.add(prompt_norm)

        all_choices = [correct_text] + distractors
        rng.shuffle(all_choices)

        correct_letter = ["A", "B", "C", "D"][all_choices.index(correct_text)]
        choices_formatted = [
            {"label": lbl, "text": txt} for lbl, txt in zip(["A", "B", "C", "D"], all_choices)
        ]

        prompt_lines = [stem, ""]
        for c in choices_formatted:
            prompt_lines.append(f"{c['label']}) {c['text']}")
        prompt = "\n".join(prompt_lines)

        item_idx = len(items) + 1
        items.append(
            {
                "id": f"{prefix}_{item_idx:04d}",
                "group": "science_mcq",
                "stem": stem,
                "choices": choices_formatted,
                "prompt": prompt,
                "answerKey": correct_letter,
                "target": correct_letter,
                "split": split,
                "answer_check": "answer_key",
            }
        )

    if len(items) < count:
        raise RuntimeError(
            f"Could not generate {count} unique science MCQ items (reached {len(items)})"
        )

    return items
