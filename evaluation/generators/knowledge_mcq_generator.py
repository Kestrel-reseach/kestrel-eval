"""Knowledge MCQ generator (MMLU 10-subject style) for Project Kestrel (Step 1).

Generates multiple-choice questions across the 10 representative MMLU subjects:
1. college_computer_science
2. college_physics
3. college_biology
4. college_chemistry
5. elementary_mathematics
6. high_school_world_history
7. high_school_geography
8. professional_law
9. clinical_knowledge
10. econometrics

Evaluated via answer_key matching (A, B, C, D). Deterministic with explicit seed.
Supports seen_prompts to guarantee 100% zero prompt duplication across partitions.
"""

from __future__ import annotations

import math
import random
from typing import Any

MMLU_SUBJECTS: tuple[str, ...] = (
    "college_computer_science",
    "college_physics",
    "college_biology",
    "college_chemistry",
    "elementary_mathematics",
    "high_school_world_history",
    "high_school_geography",
    "professional_law",
    "clinical_knowledge",
    "econometrics",
)


def _gen_cs(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["asymptotics", "cache", "graph", "os", "db", "tree"])
    if kind == "asymptotics":
        ds_ops = [
            (
                "inserting a key into an AVL tree containing n elements",
                "O(log n)",
                ["O(1)", "O(n)", "O(n log n)"],
            ),
            (
                "deleting the minimum element from a binary min-heap of n elements",
                "O(log n)",
                ["O(1)", "O(n)", "O(n log n)"],
            ),
            (
                "searching for a target value in an unsorted array of n elements",
                "O(n)",
                ["O(1)", "O(log n)", "O(n²)"],
            ),
            (
                "finding shortest paths between all pairs of vertices in an adjacency-matrix graph with V vertices using Floyd-Warshall",
                "O(V³)",
                ["O(V²)", "O(V log V)", "O(V + E)"],
            ),
            (
                "sorting n items using merge sort in the worst-case scenario",
                "O(n log n)",
                ["O(n²)", "O(n)", "O(log n)"],
            ),
            (
                "performing breadth-first search on an adjacency-list graph with V vertices and E edges",
                "O(V + E)",
                ["O(V * E)", "O(V²)", "O(E log V)"],
            ),
            (
                "accessing an arbitrary element by index in a dynamically allocated array",
                "O(1)",
                ["O(log n)", "O(n)", "O(n²)"],
            ),
            (
                "computing strongly connected components using Kosaraju's two-pass algorithm",
                "O(V + E)",
                ["O(V²)", "O(E²)", "O(V log E)"],
            ),
            (
                "finding a minimum spanning tree using Kruskal's algorithm with disjoint-set union",
                "O(E log E)",
                ["O(V²)", "O(V + E)", "O(E²)"],
            ),
            (
                "building a binary heap from an arbitrary array of n unordered elements",
                "O(n)",
                ["O(n log n)", "O(n²)", "O(log n)"],
            ),
            (
                "performing binary search on a pre-sorted array of n elements",
                "O(log n)",
                ["O(1)", "O(n)", "O(n log n)"],
            ),
            (
                "deleting a node from a doubly linked list given a direct pointer to the node",
                "O(1)",
                ["O(log n)", "O(n)", "O(n²)"],
            ),
        ]
        op, corr, dists = rng.choice(ds_ops)
        stem = f"In theoretical computer science, what is the tight asymptotic time complexity (Big-O) of {op}?"
        return stem, corr, dists[:3]
    elif kind == "cache":
        cache_kb = rng.choice([8, 16, 32, 64, 128, 256, 512, 1024])
        block_b = rng.choice([8, 16, 32, 64, 128])
        lines = (cache_kb * 1024) // block_b
        stem = f"A direct-mapped CPU data cache has a total data capacity of {cache_kb} KB and a cache line block size of {block_b} bytes. How many cache lines (blocks) does this cache contain?"
        corr = f"{lines}"
        dists = [f"{lines * 2}", f"{lines // 2}", f"{lines + 64}"]
        return stem, corr, dists[:3]
    elif kind == "graph":
        v = rng.randint(4, 45)
        max_edges = (v * (v - 1)) // 2
        stem = f"What is the maximum number of undirected edges possible in a simple connected graph containing exactly {v} vertices without self-loops or multi-edges?"
        corr = f"{max_edges}"
        dists = [f"{v * (v - 1)}", f"{max_edges + v}", f"{v**2}"]
        return stem, corr, dists[:3]
    elif kind == "tree":
        h = rng.randint(2, 9)
        max_nodes = (2 ** (h + 1)) - 1
        stem = f"For a perfect binary tree of height {h} (where a single root node has height 0), what is the total number of nodes in the tree?"
        corr = f"{max_nodes}"
        dists = [f"{2**h}", f"{max_nodes + 1}", f"{2**(h+1)}"]
        return stem, corr, dists[:3]
    elif kind == "os":
        terms = [
            (
                "Shortest Remaining Time First (SRTF)",
                "preemptive scheduling algorithm that provably minimizes average process waiting time",
            ),
            (
                "Banker's Algorithm",
                "deadlock avoidance algorithm that simulates maximum resource allocations to verify system safety",
            ),
            (
                "Translation Lookaside Buffer (TLB)",
                "hardware associative memory cache dedicated to storing recent virtual-to-physical address translations",
            ),
            (
                "Counting Semaphore",
                "synchronization construct initialized with integer N allowing at most N concurrent threads in a critical section",
            ),
            (
                "Page fault",
                "trap raised by the memory management unit when an instruction accesses an unmapped virtual memory page",
            ),
            (
                "Inverted Page Table",
                "page table architecture indexed by physical frame number rather than virtual page number to save memory",
            ),
            (
                "Thrashing",
                "high-paging state where the operating system spends more time servicing page faults than executing user instructions",
            ),
            (
                "Copy-on-Write (CoW)",
                "resource optimization technique delaying physical page duplication until a process modifies a shared memory page",
            ),
        ]
        term, desc = rng.choice(terms)
        stem = f"In operating systems design, which mechanism or algorithm is defined as: '{desc}'?"
        dists = [t for t, _ in terms if t != term][:3]
        return stem, term, dists[:3]
    else:  # db
        nfs = [
            (
                "Boyce-Codd Normal Form (BCNF)",
                "for every non-trivial functional dependency X -> Y, X must be a superkey",
            ),
            (
                "Third Normal Form (3NF)",
                "no non-prime attribute is transitively dependent on any candidate key",
            ),
            (
                "Second Normal Form (2NF)",
                "no non-prime attribute is partially dependent on any candidate key subset",
            ),
            (
                "First Normal Form (1NF)",
                "all column domains contain only atomic, indivisible scalar values",
            ),
            (
                "Serializability",
                "the criterion ensuring concurrent transaction execution produces state equivalent to some serial execution",
            ),
            (
                "Write-Ahead Logging (WAL)",
                "durability protocol requiring log records describing changes to be flushed to disk before actual data pages",
            ),
        ]
        nf, rule = rng.choice(nfs)
        stem = f"In relational database design theory, which concept requires that: '{rule}'?"
        dists = [n for n, _ in nfs if n != nf][:3]
        return stem, nf, dists[:3]


def _gen_physics(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["thermo", "optics", "quantum", "relativity", "em", "mechanics"])
    if kind == "thermo":
        tc = rng.randint(200, 380)
        th = tc + rng.randint(150, 500)
        eta = round((1.0 - (tc / th)) * 100, 1)
        stem = f"A reversible Carnot heat engine operates between a cold reservoir at {tc} K and a hot reservoir at {th} K. What is its theoretical maximum thermal efficiency?"
        corr = f"{eta}%"
        dists = [
            f"{round(eta + 15.0, 1)}%",
            f"{round(max(5.0, eta - 20.0), 1)}%",
            f"{round(100 - eta, 1)}%",
        ]
        return stem, corr, dists[:3]
    elif kind == "optics":
        f = rng.choice([10, 15, 20, 25, 30, 40, 50])
        do = f * rng.choice([2, 3, 4, 5])
        di = round((f * do) / (do - f), 1)
        stem = f"An optical object is positioned {do} cm in front of a thin converging lens with a positive focal length of {f} cm. What is the real image distance di from the lens?"
        corr = f"{di} cm"
        dists = [f"{round(di * 2, 1)} cm", f"{round(di / 2, 1)} cm", f"{round(do + f, 1)} cm"]
        return stem, corr, dists[:3]
    elif kind == "quantum":
        n = rng.randint(2, 8)
        en = round(-13.6 / (n**2), 2)
        stem = f"According to the Bohr model of the hydrogen atom, what is the bound orbital energy of an electron in principal quantum state n = {n} (where E₁ = -13.60 eV)?"
        corr = f"{en} eV"
        dists = [f"{round(en * 2, 2)} eV", f"{round(en / 2, 2)} eV", f"{-13.6 * n:.2f} eV"]
        return stem, corr, dists[:3]
    elif kind == "relativity":
        v_frac = round(rng.uniform(0.4, 0.98), 2)
        gamma = round(1.0 / ((1.0 - v_frac**2) ** 0.5), 2)
        stem = f"In special relativity, what is the Lorentz factor γ for an inertial reference frame moving at relative velocity {v_frac}c?"
        corr = f"{gamma}"
        dists = [
            f"{round(gamma * 1.4, 2)}",
            f"{round(max(1.01, gamma - 0.6), 2)}",
            f"{round(1.0 / gamma, 2)}",
        ]
        return stem, corr, dists[:3]
    elif kind == "em":
        q = rng.choice([1, 2, 5, 10, 20])
        v = rng.choice([50, 100, 200, 500])
        b = rng.choice([1, 2, 3, 4, 5])
        f_lor = q * v * b
        stem = f"A charged particle carrying charge q = +{q} C moves at velocity v = {v} m/s perpendicular to a uniform magnetic field B = {b} T. What is the magnitude of the Lorentz magnetic force exerted on the charge?"
        corr = f"{f_lor} N"
        dists = [f"{f_lor * 2} N", f"{f_lor // 2} N", f"{f_lor + 50} N"]
        return stem, corr, dists[:3]
    else:  # mechanics
        m = rng.choice([2, 5, 10, 20])
        k = rng.choice([50, 100, 200, 450, 800])
        omega = round((k / m) ** 0.5, 2)
        stem = f"A mass-spring harmonic oscillator consists of a mass m = {m} kg attached to a massless spring with spring constant k = {k} N/m. What is the angular frequency ω of simple harmonic oscillation?"
        corr = f"{omega} rad/s"
        dists = [
            f"{round(omega * 2, 2)} rad/s",
            f"{round(omega / 2, 2)} rad/s",
            f"{round(k * m, 2)} rad/s",
        ]
        return stem, corr, dists[:3]


def _gen_biology(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(
        [
            "genetics_p",
            "dna_fraction",
            "atp_yield",
            "enzymes",
            "signaling",
            "molecular",
            "cell_cycle",
        ]
    )
    if kind == "genetics_p":
        p = round(rng.uniform(0.05, 0.95), 2)
        q = round(1.0 - p, 2)
        two_pq = round(2 * p * q, 4)
        stem = f"In a diploid biological population obeying Hardy-Weinberg equilibrium, the allele frequency of dominant allele A is p = {p}. What is the expected proportion of heterozygous (Aa) genotypes in the population?"
        corr = f"{two_pq}"
        dists = [f"{round(p**2, 4)}", f"{round(q**2, 4)}", f"{round(p * q, 4)}"]
        return stem, corr, dists[:3]
    elif kind == "dna_fraction":
        gc = rng.randint(15, 40)
        at = (100 - (2 * gc)) // 2
        base = rng.choice(["Adenine", "Thymine"])
        stem = f"A double-stranded DNA sample is analyzed and found to contain {gc}% Cytosine. Under Chargaff's rules of base pairing, what percentage of the sample is {base}?"
        corr = f"{at}%"
        dists = [f"{gc}%", f"{at + 10}%", f"{max(5, at - 10)}%"]
        return stem, corr, dists[:3]
    elif kind == "atp_yield":
        moles = rng.randint(2, 15)
        atp = moles * 32
        stem = f"Assuming complete aerobic cellular respiration yielding 32 net ATP molecules per mole of glucose, how many moles of ATP are produced from the catabolism of {moles} moles of glucose?"
        corr = f"{atp} ATP"
        dists = [f"{atp // 2} ATP", f"{atp + 32} ATP", f"{moles * 2} ATP"]
        return stem, corr, dists[:3]
    elif kind == "enzymes":
        inhibition = [
            ("Competitive inhibition", "increases apparent Km without altering Vmax"),
            ("Non-competitive (Allosteric) inhibition", "decreases Vmax without altering Km"),
            ("Uncompetitive inhibition", "decreases both apparent Km and Vmax in equal proportion"),
        ]
        inh, effect = rng.choice(inhibition)
        stem = f"In enzyme kinetics (Michaelis-Menten model), which mode of reversible enzyme inhibition {effect}?"
        corr = inh
        dists = [i for i, _ in inhibition if i != inh] + ["Irreversible covalent inactivation"]
        return stem, corr, dists[:3]
    elif kind == "signaling":
        pairs = [
            (
                "Adenylate cyclase",
                "synthesizes cyclic AMP (cAMP) from ATP in response to G-protein alpha-s activation",
            ),
            (
                "Phospholipase C (PLC)",
                "cleaves phosphatidylinositol 4,5-bisphosphate (PIP2) into IP3 and diacylglycerol (DAG)",
            ),
            (
                "Receptor tyrosine kinase (RTK)",
                "dimerizes and undergoes trans-autophosphorylation upon extracellular ligand binding",
            ),
            (
                "Protein kinase A (PKA)",
                "tetrameric Ser/Thr kinase activated by allosteric binding of cAMP to its regulatory subunits",
            ),
            (
                "Calmodulin",
                "calcium-binding messenger protein that undergoes a conformational change to activate target kinases upon binding four Ca²⁺ ions",
            ),
        ]
        name, fn = rng.choice(pairs)
        stem = f"In eukaryotic cell signaling cascades, which molecular transducer {fn}?"
        corr = name
        dists = [n for n, _ in pairs if n != name][:3]
        return stem, corr, dists[:3]
    elif kind == "cell_cycle":
        checkpoints = [
            (
                "G1/S checkpoint (Restriction Point)",
                "evaluates DNA integrity, cell size, and nutrient availability before committing to DNA replication",
            ),
            (
                "G2/M checkpoint",
                "verifies that DNA replication is fully completed and undamaged prior to mitotic spindle assembly",
            ),
            (
                "M checkpoint (Spindle Assembly Checkpoint)",
                "monitors whether all sister kinetochores are properly attached to bipolar mitotic spindle microtubules",
            ),
        ]
        cp, fn = rng.choice(checkpoints)
        stem = f"In eukaryotic cell division regulation, which cell cycle checkpoint {fn}?"
        corr = cp
        dists = [c for c, _ in checkpoints if c != cp] + ["S-phase elongation checkpoint"]
        return stem, corr, dists[:3]
    else:  # molecular
        enz = [
            (
                "DNA Helicase",
                "unwinds the DNA double helix at the replication fork by breaking hydrogen bonds between base pairs",
            ),
            (
                "DNA Topoisomerase (Gyrase)",
                "relieves positive supercoiling torsional strain upstream of advancing replication forks",
            ),
            (
                "DNA Primase",
                "synthesizes short complementary RNA primers necessary for DNA polymerase extension",
            ),
            (
                "DNA Ligase",
                "catalyzes the formation of phosphodiester bonds to covalently seal Okazaki fragments on the lagging strand",
            ),
            (
                "Telomerase",
                "ribonucleoprotein reverse transcriptase that elongates chromosome ends by adding repetitive TTAGGG sequences",
            ),
        ]
        e_name, e_desc = rng.choice(enz)
        stem = f"During eukaryotic DNA replication and maintenance, which enzyme {e_desc}?"
        corr = e_name
        dists = [n for n, _ in enz if n != e_name][:3]
        return stem, corr, dists[:3]


def _gen_chemistry(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["gibbs", "buffer", "rate_law", "redox", "half_life"])
    if kind == "gibbs":
        dh = rng.randint(-350, 350)
        ds = rng.randint(-250, 250)
        stem = f"A chemical reaction system has standard enthalpy change ΔH = {dh} kJ/mol and standard entropy change ΔS = {ds} J/(mol·K). Under what temperature range is this reaction thermodynamically favored (ΔG < 0)?"
        if dh < 0 and ds > 0:
            corr = "Spontaneous at all temperatures"
            dists = [
                "Non-spontaneous at all temperatures",
                "Spontaneous only at high temperatures",
                "Spontaneous only at low temperatures",
            ]
        elif dh > 0 and ds < 0:
            corr = "Non-spontaneous at all temperatures"
            dists = [
                "Spontaneous at all temperatures",
                "Spontaneous only at high temperatures",
                "Spontaneous only at low temperatures",
            ]
        elif dh < 0 and ds < 0:
            corr = "Spontaneous only at low temperatures (below T = ΔH/ΔS)"
            dists = [
                "Spontaneous only at high temperatures",
                "Spontaneous at all temperatures",
                "Non-spontaneous at all temperatures",
            ]
        else:
            corr = "Spontaneous only at high temperatures (above T = ΔH/ΔS)"
            dists = [
                "Spontaneous only at low temperatures",
                "Spontaneous at all temperatures",
                "Non-spontaneous at all temperatures",
            ]
        return stem, corr, dists[:3]
    elif kind == "buffer":
        pka = round(rng.uniform(3.5, 9.5), 2)
        ratio = rng.choice([0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0])
        ph = round(pka + math.log10(ratio), 2)
        stem = f"According to the Henderson-Hasselbalch equation, what is the pH of a buffer solution having conjugate base to weak acid ratio [A⁻]/[HA] = {ratio} when the weak acid has pKa = {pka}?"
        corr = f"{ph}"
        dists = [f"{pka:.2f}", f"{ph + 1.5:.2f}", f"{ph - 1.5:.2f}"]
        return stem, corr, dists[:3]
    elif kind == "half_life":
        t_half = rng.choice([4, 6, 8, 12, 15, 24])
        elapsed = t_half * rng.choice([2, 3, 4, 5])
        n_half = elapsed // t_half
        frac = f"1/{2**n_half}"
        stem = f"A radioactive radioisotope has a half-life of {t_half} hours. What fraction of the original radioisotope sample remains after {elapsed} hours have elapsed?"
        corr = frac
        dists = [f"1/{2**(n_half - 1)}", f"1/{2**(n_half + 1)}", f"1/{n_half * 2}"]
        return stem, corr, dists[:3]
    elif kind == "rate_law":
        orders = [
            (
                "Zero-order kinetics",
                "the rate of reaction is constant and entirely independent of reactant concentration",
            ),
            (
                "First-order kinetics",
                "the half-life t₁/₂ = ln(2)/k is constant and independent of initial concentration",
            ),
            (
                "Second-order kinetics",
                "the half-life t₁/₂ = 1/(k[A]₀) is inversely proportional to initial concentration",
            ),
        ]
        ord_name, ord_desc = rng.choice(orders)
        stem = (
            f"In chemical reaction kinetics, which rate law behavior is described by: '{ord_desc}'?"
        )
        corr = ord_name
        dists = [o for o, _ in orders if o != ord_name] + ["Third-order fractional kinetics"]
        return stem, corr, dists[:3]
    else:  # redox
        cells = [
            (
                "Anode",
                "the electrochemical electrode at which oxidation occurs and electrons enter the external circuit",
            ),
            (
                "Cathode",
                "the electrochemical electrode at which reduction occurs and electrons exit the external circuit",
            ),
            (
                "Salt bridge",
                "maintains electrolytic charge neutrality by permitting the diffusion of inert cations and anions",
            ),
            (
                "Standard hydrogen electrode (SHE)",
                "the reference electrode defined to have an absolute potential of 0.00 V at 298 K",
            ),
        ]
        c_name, c_desc = rng.choice(cells)
        stem = f"In galvanic electrochemistry, which cell component is defined as: '{c_desc}'?"
        corr = c_name
        dists = [n for n, _ in cells if n != c_name][:3]
        return stem, corr, dists[:3]


def _gen_elementary_math(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["fraction", "perimeter", "percentage", "algebra", "ratio", "area"])
    if kind == "fraction":
        a = rng.randint(1, 10)
        b = rng.randint(11, 30)
        c = rng.randint(1, 8)
        stem = (
            f"What is the exact sum of the fractions {a}/{b} + {c}/{b} expressed in lowest terms?"
        )
        num = a + c
        g = math.gcd(num, b)
        corr = f"{num // g}/{b // g}" if b // g != 1 else f"{num // g}"
        dists = [f"{num}/{b * 2}", f"{num + 1}/{b}", f"{max(1, num - 1)}/{b}"]
        return stem, corr, dists[:3]
    elif kind == "perimeter":
        length = rng.randint(10, 80)
        w = rng.randint(5, 50)
        p = 2 * (length + w)
        stem = f"A rectangular fenced yard has a length of {length} feet and a width of {w} feet. What is the total perimeter fence length in feet?"
        corr = f"{p} feet"
        dists = [f"{length * w} feet", f"{p + 12} feet", f"{p // 2} feet"]
        return stem, corr, dists[:3]
    elif kind == "area":
        b = rng.randint(6, 40)
        h = rng.randint(4, 30)
        area = (b * h) // 2
        stem = f"What is the area in square centimeters of a triangle with a base of {b} cm and a perpendicular height of {h} cm?"
        corr = f"{area} cm²"
        dists = [f"{b * h} cm²", f"{area + 10} cm²", f"{b + h} cm²"]
        return stem, corr, dists[:3]
    elif kind == "percentage":
        cost = rng.choice([25, 30, 40, 50, 60, 75, 80, 100, 120, 140, 160, 180, 200, 250])
        disc = rng.choice([10, 15, 20, 25, 30, 40, 50, 60])
        saved = (cost * disc) // 100
        final_price = cost - saved
        stem = f"An electronic accessory priced at ${cost} is marked down by {disc}%. What is the discounted sale price before sales tax?"
        corr = f"${final_price}"
        dists = [f"${final_price + 10}", f"${cost - disc}", f"${final_price - 15}"]
        return stem, corr, dists[:3]
    elif kind == "algebra":
        x_val = rng.randint(2, 25)
        coef = rng.randint(2, 9)
        const = rng.randint(3, 40)
        rhs = coef * x_val + const
        stem = f"Solve for the unknown variable x in the linear algebraic equation: {coef}x + {const} = {rhs}."
        corr = str(x_val)
        dists = [str(x_val + 2), str(max(1, x_val - 2)), str(x_val * 2)]
        return stem, corr, dists[:3]
    else:  # ratio
        r1, r2 = rng.choice([(1, 2), (2, 3), (3, 4), (1, 4), (3, 5), (4, 5), (1, 5), (2, 5)])
        scale = rng.randint(4, 30)
        tot = (r1 + r2) * scale
        part1 = r1 * scale
        stem = f"A container holds blue and red marbles in the ratio of {r1}:{r2}. If there are {tot} marbles in the container in total, how many blue marbles are there?"
        corr = str(part1)
        dists = [str(r2 * scale), str(part1 + 6), str(max(1, part1 - 6))]
        return stem, corr, dists[:3]


def _gen_history(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(
        [
            "rulers",
            "monarch_war",
            "ancient_civ",
            "treaty_outcome",
            "century_dating",
            "us_amendment",
            "battles",
        ]
    )
    if kind == "rulers":
        rulers = [
            ("Alexander the Great", "4th century BCE", "Macedonian Empire"),
            ("Julius Caesar", "1st century BCE", "Roman Republic"),
            ("Emperor Augustus", "1st century BCE / 1st century CE", "Roman Empire"),
            ("Emperor Justinian I", "6th century CE", "Byzantine Empire"),
            ("Charlemagne", "8th-9th century CE", "Carolingian Empire"),
            ("William the Conqueror", "11th century CE", "Norman Kingdom of England"),
            ("Saladin", "12th century CE", "Ayyubid Sultanate"),
            ("Genghis Khan", "12th-13th century CE", "Mongol Empire"),
            ("Kublai Khan", "13th century CE", "Yuan Dynasty of China"),
            ("Mansa Musa", "14th century CE", "Mali Empire"),
            ("Joan of Arc", "15th century CE", "Kingdom of France"),
            ("Suleiman the Magnificent", "16th century CE", "Ottoman Empire"),
            ("Queen Elizabeth I", "16th-17th century CE", "Tudor Kingdom of England"),
            ("King Louis XIV", "17th-18th century CE", "Kingdom of France"),
            ("Peter the Great", "17th-18th century CE", "Tsardom of Russia"),
            ("George Washington", "18th century CE", "United States of America"),
            ("Napoleon Bonaparte", "18th-19th century CE", "French Empire"),
            ("Simon Bolivar", "19th century CE", "Gran Colombia"),
            ("Queen Victoria", "19th-20th century CE", "British Empire"),
            ("Otto von Bismarck", "19th century CE", "German Empire"),
            ("Meiji Emperor", "19th-20th century CE", "Empire of Japan"),
            ("Sun Yat-sen", "20th century CE", "Republic of China"),
            ("Mustafa Kemal Atatürk", "20th century CE", "Republic of Turkey"),
            ("Mahatma Gandhi", "20th century CE", "Indian Independence Movement"),
            ("Winston Churchill", "20th century CE", "United Kingdom"),
            ("Charles de Gaulle", "20th century CE", "French Fifth Republic"),
            ("Nelson Mandela", "20th century CE", "Republic of South Africa"),
        ]
        r_name, era, realm = rng.choice(rulers)
        if rng.random() > 0.5:
            stem = f"Which sovereign realm, empire, or state was led by {r_name} during the {era}?"
            corr = realm
            dists = [r for _, _, r in rulers if r != realm][:3]
        else:
            stem = f"In which historical era or century did {r_name} lead the {realm}?"
            corr = era
            dists = [e for _, e, _ in rulers if e != era][:3]
        return stem, corr, dists[:3]
    elif kind == "battles":
        battles = [
            (
                "Battle of Marathon (490 BCE)",
                "Persian invasion of Greece",
                "decisive Athenian and Plataean victory over Persian forces",
            ),
            (
                "Battle of Cannae (216 BCE)",
                "Second Punic War",
                "Hannibal's tactical double-envelopment defeat of the Roman army",
            ),
            (
                "Battle of Tours (732 CE)",
                "Umayyad invasion of Gaul",
                "Frankish victory led by Charles Martel halting northern Islamic expansion",
            ),
            (
                "Battle of Hastings (1066)",
                "Norman conquest of England",
                "Norman victory over King Harold II establishing William I on the English throne",
            ),
            (
                "Battle of Agincourt (1415)",
                "Hundred Years' War",
                "English longbow victory over numerically superior French forces",
            ),
            (
                "Battle of Lepanto (1571)",
                "Ottoman-Habsburg wars",
                "Holy League naval victory halting Ottoman maritime dominance in the Mediterranean",
            ),
            (
                "Battle of Waterloo (1815)",
                "Napoleonic Wars",
                "Seventh Coalition defeat of Napoleon Bonaparte ending the First French Empire",
            ),
            (
                "Battle of Gettysburg (1863)",
                "American Civil War",
                "Union victory halting Confederate General Robert E. Lee's northern invasion",
            ),
            (
                "Battle of Stalingrad (1942-1943)",
                "World War II Eastern Front",
                "catastrophic Soviet encirclement and destruction of the German 6th Army",
            ),
            (
                "Battle of Midway (1942)",
                "World War II Pacific Theater",
                "decisive US naval air victory sinking four Japanese fleet aircraft carriers",
            ),
        ]
        b_name, war, outcome = rng.choice(battles)
        stem = f"During which major armed conflict did the {b_name} take place, resulting in {outcome}?"
        corr = war
        dists = [w for _, w, _ in battles if w != war][:3]
        return stem, corr, dists[:3]
    elif kind == "monarch_war":
        conflicts = [
            (
                "Peloponnesian War",
                "Spartan and Athenian leagues",
                "Spartan hegemony over Greece",
                [
                    "Persian conquest of Athens",
                    "Roman annexation of Macedonia",
                    "Theban dissolution",
                ],
            ),
            (
                "Punic Wars",
                "Rome and Carthage",
                "Roman naval and terrestrial supremacy over the Western Mediterranean",
                ["Carthaginian conquest of Italy", "Egyptian domination", "Macedonian victory"],
            ),
            (
                "Hundred Years' War",
                "England and France",
                "French Valois monarchy retaining control of continental France",
                [
                    "English annexation of Paris",
                    "Burgundian supremacy",
                    "Spanish Habsburg expansion",
                ],
            ),
            (
                "Thirty Years' War",
                "Habsburg coalition and Protestant allies",
                "Peace of Westphalia decentralizing the Holy Roman Empire",
                [
                    "Complete Ottoman conquest of Vienna",
                    "Unification of German principalities",
                    "Restoration of papal absolute rule",
                ],
            ),
            (
                "Seven Years' War",
                "Great Britain and France",
                "British global maritime hegemony and cession of New France",
                [
                    "French acquisition of India",
                    "Spanish dominance over North America",
                    "Prussian partition",
                ],
            ),
            (
                "American Civil War",
                "United States (Union) and Confederate States",
                "Preservation of the Union and constitutional abolition of slavery",
                [
                    "Establishment of independent Confederacy",
                    "British intervention and annexation",
                    "French protectorate over Texas",
                ],
            ),
            (
                "Crimean War",
                "Russian Empire and allied Ottoman, British, and French forces",
                "Treaty of Paris demilitarizing the Black Sea",
                [
                    "Russian capture of Constantinople",
                    "Ottoman dissolution in 1856",
                    "Austrian annexation of Serbia",
                ],
            ),
        ]
        war, factions, outcome, dists = rng.choice(conflicts)
        stem = f"During the historical {war} fought between {factions}, which outcome was formally established?"
        return stem, outcome, dists[:3]
    elif kind == "ancient_civ":
        civs = [
            (
                "ancient Mesopotamian Sumerians",
                "cuneiform script on clay tablets",
                ["hieroglyphic papyri", "Linear B syllabary", "quipu knotted cords"],
            ),
            (
                "ancient Indus Valley civilization",
                "standardized urban grid planning and advanced subterranean drainage",
                [
                    "colossal stone pyramid tombs",
                    "monumental amphitheaters",
                    "terracotta warrior mausoleums",
                ],
            ),
            (
                "ancient Maya civilization",
                "sophisticated vigesimal (base-20) mathematics including a symbol for zero",
                [
                    "invention of magnetic compass",
                    "cuneiform legal codes",
                    "bronze chariot casting",
                ],
            ),
            (
                "ancient Shang Dynasty of China",
                "oracle bone script inscribed on turtle plastrons for divination",
                [
                    "papyrus codex scrolls",
                    "lost-wax bronze statues of deities only",
                    "quipu accounting records",
                ],
            ),
            (
                "classical Athens during the Golden Age of Pericles",
                "direct participatory democracy of male citizens in the Ecclesia",
                [
                    "representative republican senate",
                    "absolute divine-right monarchy",
                    "military oligarchy of ephors",
                ],
            ),
            (
                "classical Roman Republic",
                "bicameral-style governance comprising the Senate and popular assemblies under elected consuls",
                [
                    "monocratic pharaonic theocracy",
                    "feudal hereditary manorialism",
                    "direct lot-drawn democracy",
                ],
            ),
        ]
        civ, feat, dists = rng.choice(civs)
        stem = f"Which major technological, cultural, or administrative innovation is attributed to the {civ}?"
        return stem, feat, dists[:3]
    elif kind == "treaty_outcome":
        treaties = [
            (
                "Treaty of Utrecht (1713)",
                "concluded the War of the Spanish Succession, recognizing Philip V as king of Spain while forbidding union with France",
            ),
            (
                "Treaty of Paris (1783)",
                "formally recognized the sovereign independence of the United States of America from Great Britain",
            ),
            (
                "Treaty of Brest-Litovsk (1918)",
                "ended Russian participation in World War I following major territorial cessions to the Central Powers",
            ),
            (
                "Treaty of Guadalupe Hidalgo (1848)",
                "ended the Mexican-American War, ceding over 500,000 square miles of territory to the US",
            ),
            (
                "Treaty of Portsmouth (1905)",
                "negotiated by Theodore Roosevelt to formally conclude the Russo-Japanese War",
            ),
            (
                "Treaty of Ghent (1814)",
                "restored the status quo ante bellum between Great Britain and the United States, concluding the War of 1812",
            ),
            (
                "Treaty of Nanking (1842)",
                "ended the First Opium War, ceding Hong Kong Island to the British Empire and opening treaty ports",
            ),
        ]
        tr, desc = rng.choice(treaties)
        stem = (
            f"In diplomatic world history, what was the primary provision or outcome of the {tr}?"
        )
        dists = [d for t, d in treaties if t != tr][:3]
        return stem, desc, dists[:3]
    elif kind == "us_amendment":
        amends = [
            (
                "13th Amendment",
                "abolished slavery and involuntary servitude except as punishment for a crime",
            ),
            (
                "14th Amendment",
                "guaranteed citizenship, due process, and equal protection of the laws to all persons born or naturalized in the US",
            ),
            (
                "15th Amendment",
                "prohibited the denial of the right to vote based on race, color, or previous condition of servitude",
            ),
            (
                "16th Amendment",
                "authorized the federal government to collect an income tax without apportionment among states",
            ),
            ("17th Amendment", "established the direct popular election of United States Senators"),
            (
                "19th Amendment",
                "prohibited the denial of voting rights on the basis of sex, granting women suffrage",
            ),
            (
                "26th Amendment",
                "lowered the legal voting age in all federal and state elections to 18 years",
            ),
        ]
        am, desc = rng.choice(amends)
        stem = f"Which United States Constitutional Amendment {desc}?"
        dists = [a for a, _ in amends if a != am][:3]
        return stem, am, dists[:3]
    else:  # century_dating
        events_cent = [
            (
                "Fall of the Western Roman Empire",
                "5th century CE (476 CE)",
                ["3rd century CE", "7th century CE", "9th century CE"],
            ),
            (
                "Black Death plague pandemic across Europe",
                "14th century (1347-1351)",
                ["12th century", "16th century", "18th century"],
            ),
            (
                "Protestant Reformation sparked by Martin Luther",
                "16th century (1517)",
                ["14th century", "17th century", "18th century"],
            ),
            (
                "Invention of movable type printing by Johannes Gutenberg",
                "15th century (c. 1440)",
                ["13th century", "16th century", "17th century"],
            ),
            (
                "Apex of the Mongol conquests under Genghis Khan and successors",
                "13th century",
                ["11th century", "15th century", "16th century"],
            ),
            (
                "First commercial steam engine developed by Thomas Newcomen",
                "18th century (1712)",
                ["16th century", "19th century", "20th century"],
            ),
        ]
        ev, cent, dists = rng.choice(events_cent)
        stem = f"In which historical century did the {ev} take place?"
        return stem, cent, dists[:3]


def _gen_geography(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["capitals", "cities", "peaks", "rivers", "koppen", "straits", "deserts"])
    if kind == "capitals":
        capitals_list = [
            ("Australia", "Canberra", ["Sydney", "Melbourne", "Brisbane"]),
            ("Canada", "Ottawa", ["Toronto", "Montreal", "Vancouver"]),
            ("Brazil", "Brasília", ["Rio de Janeiro", "São Paulo", "Salvador"]),
            ("Nigeria", "Abuja", ["Lagos", "Kano", "Ibadan"]),
            ("Turkey", "Ankara", ["Istanbul", "Izmir", "Bursa"]),
            ("Switzerland", "Bern", ["Zurich", "Geneva", "Basel"]),
            ("New Zealand", "Wellington", ["Auckland", "Christchurch", "Hamilton"]),
            ("South Africa (administrative)", "Pretoria", ["Cape Town", "Johannesburg", "Durban"]),
            ("Kazakhstan", "Astana", ["Almaty", "Shymkent", "Aktobe"]),
            ("Morocco", "Rabat", ["Casablanca", "Marrakesh", "Fez"]),
            ("Argentina", "Buenos Aires", ["Córdoba", "Rosario", "Mendoza"]),
            ("Egypt", "Cairo", ["Alexandria", "Giza", "Luxor"]),
            ("Kenya", "Nairobi", ["Mombasa", "Kisumu", "Nakuru"]),
            ("India", "New Delhi", ["Mumbai", "Bengaluru", "Kolkata"]),
            ("Japan", "Tokyo", ["Kyoto", "Osaka", "Yokohama"]),
            ("Norway", "Oslo", ["Bergen", "Trondheim", "Stavanger"]),
            ("South Korea", "Seoul", ["Busan", "Incheon", "Daegu"]),
            ("Vietnam", "Hanoi", ["Ho Chi Minh City", "Da Nang", "Hai Phong"]),
            ("Colombia", "Bogotá", ["Medellín", "Cali", "Barranquilla"]),
            ("Sweden", "Stockholm", ["Gothenburg", "Malmö", "Uppsala"]),
            ("Germany", "Berlin", ["Munich", "Frankfurt", "Hamburg"]),
            ("Spain", "Madrid", ["Barcelona", "Valencia", "Seville"]),
            ("Italy", "Rome", ["Milan", "Naples", "Florence"]),
            ("Indonesia", "Jakarta", ["Surabaya", "Bandung", "Medan"]),
            ("Saudi Arabia", "Riyadh", ["Jeddah", "Mecca", "Medina"]),
            ("Poland", "Warsaw", ["Kraków", "Wrocław", "Gdańsk"]),
            ("Thailand", "Bangkok", ["Chiang Mai", "Phuket", "Pattaya"]),
            ("Chile", "Santiago", ["Valparaíso", "Concepción", "La Serena"]),
            ("Peru", "Lima", ["Cusco", "Arequipa", "Trujillo"]),
            ("Austria", "Vienna", ["Salzburg", "Innsbruck", "Graz"]),
            ("Portugal", "Lisbon", ["Porto", "Coimbra", "Braga"]),
            ("Greece", "Athens", ["Thessaloniki", "Patras", "Heraklion"]),
            ("Ireland", "Dublin", ["Cork", "Galway", "Limerick"]),
            ("Finland", "Helsinki", ["Espoo", "Tampere", "Vantaa"]),
            ("Denmark", "Copenhagen", ["Aarhus", "Odense", "Aalborg"]),
            ("Belgium", "Brussels", ["Antwerp", "Ghent", "Bruges"]),
            ("Netherlands", "Amsterdam", ["Rotterdam", "The Hague", "Utrecht"]),
            ("Czech Republic", "Prague", ["Brno", "Ostrava", "Plzeň"]),
            ("Hungary", "Budapest", ["Debrecen", "Szeged", "Miskolc"]),
            ("Philippines", "Manila", ["Cebu City", "Davao City", "Quezon City"]),
        ]
        c, cap, dists = rng.choice(capitals_list)
        stem = f"What is the official sovereign capital city of {c}?"
        return stem, cap, dists[:3]
    elif kind == "cities":
        cities_map = [
            ("Barcelona", "Spain", ["Portugal", "Italy", "France"]),
            ("Sydney", "Australia", ["New Zealand", "United Kingdom", "Canada"]),
            ("Shanghai", "China", ["Japan", "South Korea", "Taiwan"]),
            ("Rio de Janeiro", "Brazil", ["Argentina", "Colombia", "Peru"]),
            ("Munich", "Germany", ["Austria", "Switzerland", "Poland"]),
            ("Mumbai", "India", ["Pakistan", "Bangladesh", "Sri Lanka"]),
            ("Lagos", "Nigeria", ["Ghana", "Kenya", "South Africa"]),
            ("Istanbul", "Turkey", ["Greece", "Egypt", "Bulgaria"]),
            ("Casablanca", "Morocco", ["Algeria", "Tunisia", "Spain"]),
            ("Toronto", "Canada", ["United States", "Australia", "United Kingdom"]),
            ("Osaka", "Japan", ["South Korea", "China", "Philippines"]),
            ("Milan", "Italy", ["Spain", "France", "Switzerland"]),
            ("Kraków", "Poland", ["Czech Republic", "Hungary", "Slovakia"]),
            ("Auckland", "New Zealand", ["Australia", "Fiji", "Samoa"]),
            ("Medellín", "Colombia", ["Venezuela", "Ecuador", "Peru"]),
        ]
        city, country, dists = rng.choice(cities_map)
        stem = f"In which country is the prominent metropolis of {city} located?"
        return stem, country, dists[:3]
    elif kind == "peaks":
        peaks = [
            (
                "Mount Everest (8,848 m)",
                "Asia (Himalayas)",
                ["South America (Andes)", "Africa", "North America"],
            ),
            (
                "Aconcagua (6,961 m)",
                "South America (Andes)",
                ["North America (Rockies)", "Asia (Himalayas)", "Europe (Alps)"],
            ),
            (
                "Denali (6,190 m)",
                "North America (Alaska Range)",
                ["South America (Andes)", "Asia (Karakoram)", "Europe (Caucasus)"],
            ),
            (
                "Mount Kilimanjaro (5,895 m)",
                "Africa (Eastern Rift Mountains)",
                ["Asia (Tian Shan)", "South America", "Oceania"],
            ),
            (
                "Mount Elbrus (5,642 m)",
                "Europe (Caucasus Mountains)",
                ["Asia (Altai)", "Africa (Atlas)", "North America"],
            ),
            (
                "Mount Vinson (4,892 m)",
                "Antarctica (Sentinel Range)",
                ["Oceania", "Europe", "South America"],
            ),
            (
                "Puncak Jaya (4,884 m)",
                "Oceania (Sudirman Range)",
                ["Africa", "Europe", "Antarctica"],
            ),
            ("Mont Blanc (4,809 m)", "Europe (Alps)", ["North America", "South America", "Asia"]),
        ]
        pk, loc, dists = rng.choice(peaks)
        stem = f"On which continent and mountain system is the peak {pk} located?"
        return stem, loc, dists[:3]
    elif kind == "rivers":
        rivers = [
            ("Amazon River", "Atlantic Ocean", ["Pacific Ocean", "Indian Ocean", "Caribbean Sea"]),
            ("Nile River", "Mediterranean Sea", ["Red Sea", "Indian Ocean", "Atlantic Ocean"]),
            ("Yangtze River", "East China Sea", ["South China Sea", "Yellow Sea", "Sea of Japan"]),
            (
                "Mississippi River",
                "Gulf of Mexico",
                ["Atlantic Ocean", "Pacific Ocean", "Hudson Bay"],
            ),
            ("Danube River", "Black Sea", ["Baltic Sea", "North Sea", "Adriatic Sea"]),
            ("Volga River", "Caspian Sea", ["Black Sea", "White Sea", "Baltic Sea"]),
            ("Ganges River", "Bay of Bengal", ["Arabian Sea", "Indian Ocean", "Andaman Sea"]),
            (
                "Mekong River",
                "South China Sea",
                ["East China Sea", "Andaman Sea", "Gulf of Thailand"],
            ),
        ]
        riv, outflow, dists = rng.choice(rivers)
        stem = f"Into which major body of water does the {riv} empty its primary outflow?"
        return stem, outflow, dists[:3]
    elif kind == "koppen":
        k_zones = [
            (
                "Af",
                "Tropical rainforest climate (hot, humid, and rainy year-round with no dry season)",
            ),
            ("Aw", "Tropical wet-and-dry / savanna climate (pronounced dry season during winter)"),
            ("BWh", "Hot desert climate (arid, scarce precipitation, high daytime temperatures)"),
            ("Csa", "Hot-summer Mediterranean climate (dry, hot summers and mild, wet winters)"),
            (
                "Cfa",
                "Humid subtropical climate (hot, humid summers and mild winters with year-round rain)",
            ),
            ("Dfb", "Warm-summer humid continental climate (cold, snowy winters and warm summers)"),
            (
                "ET",
                "Tundra climate (at least one month with average temperature above 0 °C, but none above 10 °C)",
            ),
        ]
        code, desc = rng.choice(k_zones)
        stem = f"In the Köppen-Geiger climate classification system, which climate category is designated by the code '{code}'?"
        dists = [d for c, d in k_zones if c != code][:3]
        return stem, desc, dists[:3]
    elif kind == "straits":
        straits = [
            (
                "Strait of Malacca",
                "the maritime corridor connecting the Indian Ocean and the South China Sea between Malaysia and Sumatra",
            ),
            (
                "Strait of Hormuz",
                "the strategic chokepoint between the Persian Gulf and the Gulf of Oman",
            ),
            (
                "Bosporus Strait",
                "the narrow strait in Turkey separating Europe from Asia and linking the Black Sea to the Sea of Marmara",
            ),
            (
                "Strait of Magellan",
                "the navigable sea route in southern Chile separating mainland South America from Tierra del Fuego",
            ),
            (
                "Bab-el-Mandeb",
                "the strait linking the Red Sea to the Gulf of Aden and the Arabian Sea",
            ),
            (
                "Cook Strait",
                "the marine strait separating the North Island and South Island of New Zealand",
            ),
        ]
        str_name, desc = rng.choice(straits)
        stem = f"Which major navigable marine strait is described as: '{desc}'?"
        dists = [s for s, _ in straits if s != str_name][:3]
        return stem, str_name, dists[:3]
    else:  # deserts
        deserts = [
            ("Sahara Desert", "Africa", ["Asia", "Australia", "North America"]),
            ("Gobi Desert", "Asia", ["Africa", "South America", "Australia"]),
            ("Kalahari Desert", "Africa", ["Asia", "Europe", "South America"]),
            ("Atacama Desert", "South America", ["Africa", "Asia", "North America"]),
            ("Mojave Desert", "North America", ["South America", "Australia", "Africa"]),
            ("Great Victoria Desert", "Australia", ["Africa", "Asia", "North America"]),
            ("Thar Desert", "Asia", ["Africa", "Australia", "South America"]),
            ("Patagonian Desert", "South America", ["Africa", "Australia", "Asia"]),
        ]
        d_name, cont, dists = rng.choice(deserts)
        stem = f"On which continent is the arid expanse of the {d_name} situated?"
        return stem, cont, dists[:3]


def _gen_law(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(
        ["doctrines", "contract_scenario", "tort_scenario", "crim_scenario", "const_scenario"]
    )
    if kind == "contract_scenario":
        parties = [
            ("Alice", "Bob"),
            ("Claire", "David"),
            ("Elena", "Frank"),
            ("Grace", "Henry"),
            ("Isabel", "James"),
        ]
        p1, p2 = rng.choice(parties)
        goods = rng.choice(
            [
                "commercial restaurant equipment",
                "custom server racks",
                "fleet vehicles",
                "construction timber",
            ]
        )
        amount = rng.choice([2500, 5000, 15000, 30000, 75000])
        stem = f"{p1} enters into an oral agreement with {p2} to purchase {goods} for a total price of ${amount}. Neither party signs a written memorandum. Under the Uniform Commercial Code (UCC Section 2-201) Statute of Frauds, which statement is legally accurate?"
        corr = "The oral contract is unenforceable because the sale of goods is for $500 or more and requires a signed writing"
        dists = [
            "The oral contract is fully enforceable because merchant agreements do not require written documentation",
            f"The oral contract is enforceable only if {p1} files an affidavit in municipal court within 10 days",
            "The contract is voidable at the option of third-party creditors only",
        ]
        return stem, corr, dists[:3]
    elif kind == "tort_scenario":
        parties = [
            ("Alice", "Bob"),
            ("Claire", "David"),
            ("Elena", "Frank"),
            ("Grace", "Henry"),
            ("Isabel", "James"),
        ]
        p1, p2 = rng.choice(parties)
        speed = rng.randint(45, 65)
        limit = speed - rng.choice([15, 20, 25])
        stem = f"While driving at {speed} mph in a posted {limit} mph school zone, {p1} fails to brake in time and collides with {p2}'s stationary vehicle. In a negligence action brought by {p2}, {p1}'s statutory speeding violation establishes:"
        corr = "Negligence per se (conclusive evidence of breach of the standard of care as a matter of law)"
        dists = [
            "Res ipsa loquitur (an evidentiary inference shifting the ultimate burden of proof to the jury)",
            "Strict liability regardless of causation or damages",
            f"Assumption of the risk barring recovery by {p2}",
        ]
        return stem, corr, dists[:3]
    elif kind == "crim_scenario":
        parties = [
            ("Arthur", "Brian"),
            ("Carl", "Derek"),
            ("Edward", "Felix"),
            ("George", "Harold"),
        ]
        p1, p2 = rng.choice(parties)
        val = rng.choice([1000, 2500, 5000])
        stem = f"{p1} breaks the window latch of {p2}'s dwelling at night and enters intending to steal ${val} in jewelry, but flees upon hearing a dog bark before taking anything. Under traditional common law, {p1} is guilty of:"
        corr = "Burglary (the breaking and entering of the dwelling of another at nighttime with intent to commit a felony)"
        dists = [
            "Attempted larceny only, because no personal property was asported",
            "Criminal trespass only, because no felony was completed inside the dwelling",
            "Robbery, because the breaking was accomplished with constructive force",
        ]
        return stem, corr, dists[:3]
    elif kind == "const_scenario":
        states = ["State A", "State B", "State C", "State D"]
        st = rng.choice(states)
        tax = rng.choice([5, 8, 10, 15])
        stem = f"{st} enacts a statute imposing a {tax}% sales surcharge exclusively on goods manufactured out-of-state, while exempting locally manufactured goods. If an out-of-state merchant challenges this statute in federal court, the statute will likely be struck down under:"
        corr = "The Dormant Commerce Clause (for discriminating against interstate commerce on its face)"
        dists = [
            "The Tenth Amendment reserved police powers clause",
            "The Full Faith and Credit Clause",
            "The Privileges and Immunities Clause of the Fourteenth Amendment",
        ]
        return stem, corr, dists[:3]
    else:  # doctrines
        doctrines = [
            (
                "Res Ipsa Loquitur",
                "the tort doctrine permitting an inference of negligence when an accident would not ordinarily occur without negligence",
            ),
            (
                "Parol Evidence Rule",
                "the contract rule barring extrinsic oral evidence from contradicting a fully integrated written agreement",
            ),
            (
                "Promissory Estoppel",
                "the doctrine enforcing a promise lacking formal consideration when a promisee reasonably relied on it to their detriment",
            ),
            (
                "Exclusionary Rule",
                "the constitutional criminal principle barring evidence seized in violation of Fourth Amendment protections",
            ),
            (
                "Strict Products Liability",
                "the tort theory imposing liability on commercial product sellers for injuries caused by defective products without proving fault",
            ),
            (
                "Felony Murder Rule",
                "the rule imposing murder liability on all participants in an inherently dangerous felony if a death results",
            ),
            (
                "Mailbox Rule",
                "the contract rule that an acceptance dispatched via an authorized medium is effective immediately upon posting",
            ),
            (
                "Brady Rule",
                "the prosecutorial duty under the Fourteenth Amendment to disclose favorable exculpatory material to the defense",
            ),
            (
                "Rule Against Perpetuities",
                "the property law rule requiring future interests to vest, if at all, within 21 years of a life in being",
            ),
            (
                "Qualified Immunity",
                "the legal doctrine protecting government officials from civil liability unless they violated clearly established statutory or constitutional rights",
            ),
        ]
        doc, desc = rng.choice(doctrines)
        stem = f"In professional American jurisprudence, which fundamental legal doctrine or rule is defined as: '{desc}'?"
        dists = [d for d, _ in doctrines if d != doc][:3]
        return stem, doc, dists[:3]


def _gen_clinical(rng: random.Random) -> tuple[str, str, list[str]]:
    cases = [
        (
            "ST-Elevation Myocardial Infarction (STEMI)",
            "Crushing substernal chest pressure radiating to the left arm and jaw, diaphoresis, and new ST elevations on 12-lead ECG",
            ["Aortic dissection", "Acute pericarditis", "Esophageal spasm"],
        ),
        (
            "Diabetic Ketoacidosis (DKA)",
            "Severe hyperglycemia, polyuria, fruity acetone breath, deep Kussmaul respirations, and high serum beta-hydroxybutyrate",
            ["Hyperosmolar hyperglycemic state", "Lactic acidosis", "Central diabetes insipidus"],
        ),
        (
            "Tension Pneumothorax",
            "Sudden severe dyspnea, hypotension, unilateral absent breath sounds, hyperresonance to percussion, and contralateral tracheal deviation",
            ["Cardiac tamponade", "Spontaneous hemothorax", "Acute pulmonary edema"],
        ),
        (
            "Anaphylactic Shock",
            "Acute generalized urticaria, profound hypotension, laryngeal angioedema, and inspiratory stridor within minutes of allergen ingestion",
            ["Vasovagal syncope", "Septic shock", "Severe asthma exacerbation"],
        ),
        (
            "Acute Appendicitis",
            "Periumbilical abdominal pain migrating to the right lower quadrant with marked tenderness at McBurney's point and leukocytosis",
            ["Acute diverticulitis", "Nephrolithiasis", "Mesenteric adenitis"],
        ),
        (
            "Bacterial Meningitis",
            "Acute onset of high fever, photophobia, nuchal rigidity, and positive Kernig and Brudzinski clinical signs",
            ["Viral encephalitis", "Subarachnoid hemorrhage", "Brain abscess"],
        ),
        (
            "Graves' Disease",
            "Weight loss despite increased appetite, bilateral exophthalmos, fine tremor, heat intolerance, and suppressed serum TSH",
            ["Toxic multinodular goiter", "Hashimoto thyroiditis", "Subacute thyroiditis"],
        ),
        (
            "Cushing's Syndrome",
            "Centripetal obesity, moon facies, buffalo hump, purple abdominal striae, and elevated 24-hour urinary free cortisol",
            ["Polycystic ovary syndrome", "Metabolic syndrome", "Primary hyperaldosteronism"],
        ),
        (
            "Pulmonary Embolism",
            "Sudden-onset pleuritic chest pain, tachypnea, tachycardia, hypoxemia, and a normal initial chest radiograph in an immobilized patient",
            ["Pneumonia", "Costochondritis", "Acute myocardial infarction"],
        ),
        (
            "Hypovolemic Shock",
            "Severe blood loss resulting in tachycardia, cold clammy extremities, oliguria, and mean arterial pressure < 60 mmHg",
            ["Distributive shock", "Cardiogenic shock", "Neurogenic shock"],
        ),
        (
            "Guillain-Barré Syndrome",
            "Symmetrical ascending lower-extremity motor weakness, hyporeflexia, and albuminocytological dissociation on lumbar puncture following a diarrheal illness",
            ["Myasthenia gravis", "Amyotrophic lateral sclerosis", "Multiple sclerosis"],
        ),
        (
            "Multiple Sclerosis",
            "Episodic neurological deficits separated in time and space, including optic neuritis, Lhermitte's sign, and oligoclonal bands in CSF",
            [
                "Systemic lupus erythematosus",
                "Neurosarcoidosis",
                "Acute disseminated encephalomyelitis",
            ],
        ),
        (
            "Pheochromocytoma",
            "Paroxysmal triad of episodic severe headaches, diaphoresis, and tachycardia accompanied by marked hypertension",
            ["Essential hypertension", "Carcinoid syndrome", "Panic disorder"],
        ),
        (
            "Acute Pancreatitis",
            "Severe epigastric abdominal pain radiating straight to the back, nausea, vomiting, and a threefold elevation in serum lipase levels",
            ["Acute cholecystitis", "Perforated peptic ulcer", "Intestinal obstruction"],
        ),
        (
            "Myasthenia Gravis",
            "Fluctuating fatigable ptosis and diplopia worsening with muscle use throughout the day, caused by autoantibodies against acetylcholine receptors",
            ["Lambert-Eaton myasthenic syndrome", "Oculopharyngeal muscular dystrophy", "Botulism"],
        ),
    ]
    diag, vignette, dists = rng.choice(cases)
    age = rng.randint(21, 79)
    sex = rng.choice(["male", "female"])
    sbp = rng.randint(85, 175)
    dbp = rng.randint(55, 105)
    hr = rng.randint(65, 125)
    stem = f"A {age}-year-old {sex} presents with vital signs showing BP {sbp}/{dbp} mmHg, HR {hr} bpm, and clinical presentation of: '{vignette}'. What is the most likely clinical diagnosis?"
    return stem, diag, dists[:3]


def _gen_econometrics(rng: random.Random) -> tuple[str, str, list[str]]:
    kind = rng.choice(["df", "concept", "r_squared", "t_stat"])
    if kind == "df":
        n = rng.randint(35, 300)
        k = rng.randint(2, 9)
        df = n - k - 1
        stem = f"In an Ordinary Least Squares (OLS) multiple linear regression model estimated with n = {n} observations and k = {k} independent explanatory variables, what are the degrees of freedom for the regression residual error variance?"
        corr = f"{df}"
        dists = [f"{n - k}", f"{n - 1}", f"{df + 2}"]
        return stem, corr, dists[:3]
    elif kind == "r_squared":
        sst = rng.choice([400, 600, 800, 1000, 1500, 2000, 3000])
        ssr = sst // rng.choice([2, 4, 5, 8])
        r2 = round(ssr / sst, 2)
        stem = f"In a linear regression analysis, the Total Sum of Squares (SST) is {sst} and the Regression Explained Sum of Squares (SSR) is {ssr}. What is the coefficient of determination (R²) of the fitted model?"
        corr = f"{r2:.2f}"
        dists = [
            f"{round(1 - r2, 2):.2f}",
            f"{round(r2 / 2, 2):.2f}",
            f"{round(min(0.99, r2 + 0.25), 2):.2f}",
        ]
        return stem, corr, dists[:3]
    elif kind == "t_stat":
        beta = round(rng.uniform(1.5, 6.0), 2)
        se = round(rng.uniform(0.2, 1.2), 2)
        t_val = round(beta / se, 2)
        stem = f"In a simple regression model, an estimated coefficient is β̂ = {beta} with an estimated standard error SE(β̂) = {se}. What is the calculated t-statistic for testing the null hypothesis H₀: β = 0?"
        corr = f"{t_val:.2f}"
        dists = [
            f"{round(t_val * 2, 2):.2f}",
            f"{round(t_val / 2, 2):.2f}",
            f"{round(beta * se, 2):.2f}",
        ]
        return stem, corr, dists[:3]
    else:
        topics = [
            (
                "Heteroskedasticity",
                "the statistical condition where the variance of regression error terms conditional on regressors is non-constant",
            ),
            (
                "Endogeneity",
                "the econometric condition where an explanatory independent regressor is correlated with the regression disturbance error term",
            ),
            (
                "Multicollinearity",
                "high linear correlation among two or more independent regressor variables in a multiple regression model",
            ),
            (
                "Instrumental Variable (2SLS)",
                "estimation strategy requiring an instrument correlated with the endogenous regressor (relevance) but uncorrelated with the error term (exogeneity)",
            ),
            (
                "Hausman Specification Test",
                "hypothesis test in panel data econometrics used to determine whether fixed effects or random effects models are consistent",
            ),
            (
                "Durbin-Watson Test",
                "test statistic used to detect the presence of first-order autoregressive serial correlation in regression residuals",
            ),
            (
                "Augmented Dickey-Fuller (ADF) Test",
                "unit root test used to evaluate the null hypothesis that a time series is non-stationary",
            ),
            (
                "Gauss-Markov Theorem",
                "theorem proving that OLS estimators are Best Linear Unbiased Estimators (BLUE) under spherical error assumptions",
            ),
            (
                "White Test",
                "asymptotic statistical test used to detect general forms of heteroskedasticity in regression models without specifying its functional form",
            ),
            (
                "Variance Inflation Factor (VIF)",
                "diagnostic measure quantifying the degree to which multicollinearity inflates the variance of regression coefficients",
            ),
        ]
        term, desc = rng.choice(topics)
        stem = f"In theoretical and applied econometrics, which term designates: '{desc}'?"
        corr = term
        dists = [t for t, _ in topics if t != term][:3]
        return stem, corr, dists[:3]


SUBJECT_GENERATORS = {
    "college_computer_science": _gen_cs,
    "college_physics": _gen_physics,
    "college_biology": _gen_biology,
    "college_chemistry": _gen_chemistry,
    "elementary_mathematics": _gen_elementary_math,
    "high_school_world_history": _gen_history,
    "high_school_geography": _gen_geography,
    "professional_law": _gen_law,
    "clinical_knowledge": _gen_clinical,
    "econometrics": _gen_econometrics,
}


def generate_knowledge_mcq_suite(
    items_per_subject: int = 30,
    seed: int = 20260101,
    prefix: str = "know_val",
    split: str = "validation",
    seen_prompts: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate a suite of 300 items across 10 subjects deterministically."""
    rng = random.Random(seed)
    items: list[dict[str, Any]] = []
    idx = 1

    for subject in MMLU_SUBJECTS:
        gen_fn = SUBJECT_GENERATORS[subject]
        generated_count = 0
        attempts = 0
        max_attempts = items_per_subject * 300

        while generated_count < items_per_subject and attempts < max_attempts:
            attempts += 1
            stem, correct_text, distractors = gen_fn(rng)

            prompt_norm = " ".join(stem.lower().split())
            if seen_prompts is not None:
                if prompt_norm in seen_prompts:
                    continue
                seen_prompts.add(prompt_norm)

            all_choices = [correct_text] + list(distractors[:3])
            rng.shuffle(all_choices)

            correct_letter = ["A", "B", "C", "D"][all_choices.index(correct_text)]
            prompt_lines = [f"[{subject.replace('_', ' ').title()}] {stem}", ""]
            for lbl, txt in zip(["A", "B", "C", "D"], all_choices):
                prompt_lines.append(f"{lbl}) {txt}")
            prompt = "\n".join(prompt_lines)

            items.append(
                {
                    "id": f"{prefix}_{idx:04d}",
                    "group": "knowledge_mcq",
                    "subject": subject,
                    "stem": stem,
                    "choices": [
                        {"label": lbl, "text": txt}
                        for lbl, txt in zip(["A", "B", "C", "D"], all_choices)
                    ],
                    "prompt": prompt,
                    "answerKey": correct_letter,
                    "target": correct_letter,
                    "split": split,
                    "answer_check": "answer_key",
                }
            )
            idx += 1
            generated_count += 1

        if generated_count < items_per_subject:
            raise RuntimeError(
                f"Could not generate {items_per_subject} unique items for {subject} (got {generated_count})"
            )

    return items
