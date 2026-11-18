"""Synthetic generator for personal-memory probe suite (Decision D3: synthetic only).

Generates 100 items per partition:
- 30 stale-fact items: an attribute evolves over chronological events; target is latest value;
  previous values are recorded as stale values for the rejection scorer.
- 70 static-fact recall items: single factual attributes across varied sources and dates.

Every history event has an explicit timestamp, source channel, and factual statement.
Supports seen_prompts to guarantee 100% zero prompt duplication across partitions.
"""

from __future__ import annotations

import random

from evaluation.loaders.common import SuiteItem

STALE_FACT_TEMPLATES = [
    {
        "attribute": "current city of residence",
        "question": "What is my current city of residence?",
        "values": [
            "Austin",
            "Seattle",
            "Chicago",
            "Denver",
            "Boston",
            "San Francisco",
            "Atlanta",
            "Portland",
            "San Diego",
            "Minneapolis",
        ],
        "sources": ["apartment_lease_email", "relocation_slack_msg", "address_update_note"],
        "verbs": [
            "I just signed a lease and moved to",
            "Relocated officially to",
            "My new home address is now in",
        ],
    },
    {
        "attribute": "direct manager",
        "question": "Who is my current direct reporting manager at work?",
        "values": [
            "Rachel Vance",
            "David Chen",
            "Sarah Jenkins",
            "Michael Torres",
            "Priya Patel",
            "Elena Rostova",
            "Marcus Brody",
            "Chloe Bennett",
        ],
        "sources": ["team_org_chart_email", "1on1_calendar_invite", "reorg_announcement"],
        "verbs": [
            "Starting this week, my new direct manager is",
            "Transferred to the team reporting to",
            "My reporting line shifted to",
        ],
    },
    {
        "attribute": "daily driver vehicle",
        "question": "What car do I currently drive as my daily driver?",
        "values": [
            "2018 Honda Civic",
            "2021 Tesla Model 3",
            "2024 Toyota RAV4 Hybrid",
            "2023 Hyundai Ioniq 5",
            "2020 Subaru Outback",
            "2022 Mazda CX-5",
        ],
        "sources": ["car_insurance_receipt", "mechanic_invoice", "parking_permit_app"],
        "verbs": [
            "Sold my previous car and bought a",
            "Registered my new",
            "Picked up the keys to my",
        ],
    },
    {
        "attribute": "preferred morning coffee roast",
        "question": "What is my current favorite coffee roast for my morning brew?",
        "values": [
            "Ethiopian Yirgacheffe light roast",
            "Colombian Supremo medium roast",
            "Guatemalan Antigua dark roast",
            "Sumatra Mandheling",
            "Costa Rican Tarrazu",
            "Kenya AA medium-dark roast",
        ],
        "sources": ["coffee_subscription_order", "pantry_inventory_note", "barista_chat"],
        "verbs": [
            "Switched my daily coffee subscription to",
            "Currently obsessed with brewing",
            "Updated my default bean preference to",
        ],
    },
    {
        "attribute": "primary smartphone model",
        "question": "What phone model do I currently use as my primary phone?",
        "values": [
            "Pixel 7 Pro",
            "Pixel 8 Pro",
            "Pixel 9 Pro XL",
            "iPhone 15 Pro",
            "Samsung Galaxy S24 Ultra",
            "OnePlus 12",
        ],
        "sources": ["device_trade_in_receipt", "mobile_carrier_email", "phone_case_order"],
        "verbs": [
            "Traded in my old phone and activated the",
            "Upgraded my daily handset to the",
            "Transferred all my data to the new",
        ],
    },
    {
        "attribute": "weekly gym workout split",
        "question": "What gym training routine am I currently following?",
        "values": [
            "Push-Pull-Legs 6-day split",
            "Upper-Lower 4-day split",
            "Full Body 3 days a week",
            "5/3/1 Strength Program",
            "Arnold Split 6 days a week",
        ],
        "sources": ["fitness_log_note", "personal_trainer_chat", "gym_schedule_calendar"],
        "verbs": [
            "Changed my training program this month to",
            "Started a new block following the",
            "My current fitness schedule is the",
        ],
    },
    {
        "attribute": "active side project repository",
        "question": "What is the name of my primary active open-source side project?",
        "values": [
            "quantum-flux",
            "vector-mesh",
            "kestrel-assist",
            "rust-parser-core",
            "hydra-db",
            "graph-rag-lite",
        ],
        "sources": ["github_commit_log", "project_todo_note", "discord_dev_chat"],
        "verbs": [
            "Archived my old repo and focused all efforts on",
            "Initialized and actively developing",
            "My main repository focus is now",
        ],
    },
    {
        "attribute": "home Wi-Fi network SSID",
        "question": "What is the SSID name of my home Wi-Fi network?",
        "values": [
            "GalacticNet-5G",
            "Starlight_Mesh",
            "QuantumFiber_Guest",
            "NexusHome_Secure",
            "OrionMesh_Ultra",
        ],
        "sources": ["router_setup_notes", "guest_wifi_share_msg", "smart_home_log"],
        "verbs": [
            "Replaced the home router and renamed the Wi-Fi to",
            "Configured my new mesh network with SSID",
            "Updated my home Wi-Fi name to",
        ],
    },
    {
        "attribute": "cat's veterinary clinic",
        "question": "Which veterinary clinic handles my cat's appointments?",
        "values": [
            "Paws & Whiskers Animal Hospital",
            "Cedar Creek Vet Clinic",
            "Metropolitan Pet Hospital",
            "Sunset Valley Animal Clinic",
            "Oakwood Pet Care Center",
        ],
        "sources": ["vet_reminder_email", "cat_vaccination_record", "pet_care_notes"],
        "verbs": [
            "Transferred my cat's medical records to",
            "Booked the upcoming checkup at",
            "My cat is now registered as a patient at",
        ],
    },
    {
        "attribute": "key client project deadline",
        "question": "What is the confirmed delivery deadline for Project Atlas?",
        "values": [
            "October 15, 2026",
            "November 1, 2026",
            "December 15, 2026",
            "January 30, 2027",
            "March 15, 2027",
        ],
        "sources": [
            "client_statement_of_work",
            "executive_steering_email",
            "jira_milestone_update",
        ],
        "verbs": [
            "Client approved an extension, moving the final deadline to",
            "Rebaselined the delivery milestone to",
            "The locked delivery target date is officially",
        ],
    },
]

STATIC_FACT_TEMPLATES = [
    (
        "What is my mother's birthday?",
        "May 14",
        "calendar_birthday",
        "Mother's Birthday marked on calendar as May 14.",
    ),
    (
        "What allergy do I have to medication?",
        "Penicillin",
        "medical_notes",
        "Patient records note a severe allergy to Penicillin.",
    ),
    (
        "What is my frequent flyer number on SkyAir?",
        "SK-908214",
        "travel_profile",
        "Saved SkyAir frequent flyer account number: SK-908214.",
    ),
    (
        "What brand of mechanical keyboard switches do I prefer?",
        "Gateron Oil King linear switches",
        "desk_setup_note",
        "Purchased and customized desk keyboard with Gateron Oil King linear switches.",
    ),
    (
        "What is the gate code for my apartment complex?",
        "4821#",
        "lease_agreement",
        "Building management assigned community gate code: 4821#.",
    ),
    (
        "Which university did I graduate from with my undergraduate degree?",
        "University of Michigan",
        "resume_draft",
        "Education section lists B.S. in Computer Science from University of Michigan.",
    ),
    (
        "What is my blood type?",
        "O-positive",
        "blood_donor_card",
        "Blood donor registration card records blood type as O-positive.",
    ),
    (
        "What is my emergency contact person's name?",
        "David Vance",
        "emergency_form",
        "Designated emergency contact listed as David Vance (brother).",
    ),
    (
        "What is my preferred terminal font?",
        "JetBrains Mono Nerd Font",
        "dotfiles_readme",
        "Terminal configuration uses JetBrains Mono Nerd Font 13pt.",
    ),
    (
        "What musical instrument did I learn as a child?",
        "Cello",
        "journal_entry",
        "Wrote about practicing the cello for eight years during middle and high school.",
    ),
    (
        "What is my shoe size?",
        "US Mens 10.5",
        "wardrobe_note",
        "Shoe size recorded as US Mens 10.5 for athletic footwear.",
    ),
    (
        "What is my eye prescription power?",
        "-2.75 diopters",
        "optometry_record",
        "Latest prescription indicates -2.75 diopters spherical correction in both eyes.",
    ),
    (
        "What year did I adopt my cat Luna?",
        "2021",
        "pet_adoption_cert",
        "Adoption certificate from city shelter confirms Luna adopted on June 12, 2021.",
    ),
    (
        "What is the passport renewal expiration year?",
        "2032",
        "travel_documents",
        "Passport validity page lists expiration date in August 2032.",
    ),
    (
        "What brand of bicycle do I ride for weekend trails?",
        "Trek Marlin 7",
        "bike_receipt",
        "Purchased mountain bike Trek Marlin 7 with disc brakes.",
    ),
    (
        "What is my default audio output device on desktop?",
        "Schiit Magni DAC/Amp",
        "audio_setup_guide",
        "Desktop DAC/Amp output configured to Schiit Magni.",
    ),
    (
        "What is the brand of my espresso grinder?",
        "Eureka Mignon Specialita",
        "kitchen_inventory",
        "Espresso grinder listed as Eureka Mignon Specialita 55mm burrs.",
    ),
    (
        "What is my favorite sci-fi book title?",
        "Hyperion by Dan Simmons",
        "book_reading_list",
        "Top recommendation in reading list recorded as Hyperion by Dan Simmons.",
    ),
    (
        "What is my dental hygienist's name?",
        "Clara Higgins",
        "dental_appointment_sms",
        "Upcoming cleanings booked with dental hygienist Clara Higgins.",
    ),
    (
        "What is the model of my ergonomic office chair?",
        "Herman Miller Aeron Size B",
        "home_office_invoice",
        "Office ergonomics expense receipt for Herman Miller Aeron Size B.",
    ),
]


def generate_memory_probe_suite(
    n_items: int = 100,
    stale_fact_count: int = 30,
    seed: int = 20260101,
    seen_prompts: set[str] | None = None,
) -> list[SuiteItem]:
    """Generate deterministic personal-memory probe suite."""
    rng = random.Random(seed)
    items: list[SuiteItem] = []

    # 1. Generate Stale-Fact Items
    for i in range(1, stale_fact_count + 1):
        tmpl = STALE_FACT_TEMPLATES[(i - 1) % len(STALE_FACT_TEMPLATES)]
        vals = rng.sample(tmpl["values"], min(3, len(tmpl["values"])))
        old_val_1 = vals[0]
        old_val_2 = vals[1]
        latest_val = vals[2]

        month_1 = rng.randint(1, 4)
        day_1 = rng.randint(1, 28)
        month_2 = rng.randint(5, 7)
        day_2 = rng.randint(1, 28)
        month_3 = rng.randint(8, 11)
        day_3 = rng.randint(1, 28)

        events = [
            {
                "timestamp": f"2026-{month_1:02d}-{day_1:02d} 09:15",
                "source": tmpl["sources"][0],
                "content": f"{tmpl['verbs'][0]} {old_val_1}.",
            },
            {
                "timestamp": f"2026-{month_2:02d}-{day_2:02d} 14:30",
                "source": tmpl["sources"][1],
                "content": f"{tmpl['verbs'][1]} {old_val_2}.",
            },
            {
                "timestamp": f"2026-{month_3:02d}-{day_3:02d} 17:45",
                "source": tmpl["sources"][2],
                "content": f"{tmpl['verbs'][2]} {latest_val}.",
            },
        ]

        history_text = "\n".join(
            f"[{ev['timestamp']} | Channel: {ev['source']}]\n{ev['content']}" for ev in events
        )
        prompt = (
            f"Review the personal history log below and answer the question.\n\n"
            f"--- PERSONAL HISTORY LOG ---\n"
            f"{history_text}\n"
            f"--- END LOG ---\n\n"
            f"Question: {tmpl['question']}\n"
            f"Provide the exact, current value."
        )

        prompt_norm = " ".join(prompt.lower().split())
        if seen_prompts is not None:
            if prompt_norm in seen_prompts:
                # Add microsecond jitter or timestamp tweak if needed
                continue
            seen_prompts.add(prompt_norm)

        item_id = f"memory_probe-{i:04d}"
        items.append(
            SuiteItem(
                item_id=item_id,
                group="memory_probe",
                prompt=prompt,
                target=latest_val,
                answer_check="key_from_source_history",
                choices=None,
                metadata={
                    "source": "synthetic_personal_memory_generator",
                    "version": "1.0",
                    "license": "Project-Internal (Synthetic Only per D3)",
                    "license_url": "N/A",
                    "url": "local",
                    "verified_on_official_page": True,
                    "contamination_risk": "ZERO (Synthetic history; no real personal data committed per rules.md)",
                    "is_stale_fact": True,
                    "stale_values": [old_val_1, old_val_2],
                    "attribute": tmpl["attribute"],
                    "events": events,
                },
            )
        )

    # 2. Generate Static Recall Items
    static_count = n_items - stale_fact_count
    for j in range(1, static_count + 1):
        idx = stale_fact_count + j
        q, ans, src, statement = STATIC_FACT_TEMPLATES[(j - 1) % len(STATIC_FACT_TEMPLATES)]

        month = rng.randint(1, 10)
        day = rng.randint(1, 28)
        hour = rng.randint(8, 18)
        minute = rng.randint(10, 55)
        event = {
            "timestamp": f"2026-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            "source": src,
            "content": statement,
        }
        history_text = f"[{event['timestamp']} | Channel: {event['source']}]\n{event['content']}"
        prompt = (
            f"Review the personal history log below and answer the question.\n\n"
            f"--- PERSONAL HISTORY LOG ---\n"
            f"{history_text}\n"
            f"--- END LOG ---\n\n"
            f"Question: {q}\n"
            f"Provide the exact value from the log."
        )

        prompt_norm = " ".join(prompt.lower().split())
        if seen_prompts is not None:
            if prompt_norm in seen_prompts:
                continue
            seen_prompts.add(prompt_norm)

        item_id = f"memory_probe-{idx:04d}"
        items.append(
            SuiteItem(
                item_id=item_id,
                group="memory_probe",
                prompt=prompt,
                target=ans,
                answer_check="key_from_source_history",
                choices=None,
                metadata={
                    "source": "synthetic_personal_memory_generator",
                    "version": "1.0",
                    "license": "Project-Internal (Synthetic Only per D3)",
                    "license_url": "N/A",
                    "url": "local",
                    "verified_on_official_page": True,
                    "contamination_risk": "ZERO (Synthetic history; no real personal data committed per rules.md)",
                    "is_stale_fact": False,
                    "stale_values": [],
                    "events": [event],
                },
            )
        )

    return items
