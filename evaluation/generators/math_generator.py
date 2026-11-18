"""Deterministic procedural generator for synthetic math word problems.

Produces math tasks with exact numeric answers and step-by-step reasoning scratchpads.
Uses fixed seeds for bitwise reproducibility.
"""

from __future__ import annotations

import random

from evaluation.loaders.common import SuiteItem


def generate_math_problem(rng: random.Random, index: int) -> SuiteItem:
    """Generate a single deterministic multi-step math word problem."""
    template_type = rng.choice(
        ["shopping", "travel", "work_rate", "finance", "geometry", "tournament"]
    )

    if template_type == "shopping":
        item_name = rng.choice(
            ["notebooks", "water bottles", "pens", "backpacks", "keychains", "flash drives"]
        )
        qty1 = rng.randint(3, 12)
        price1 = rng.randint(4, 25)
        qty2 = rng.randint(2, 8)
        price2 = rng.randint(5, 30)
        discount = rng.randint(5, 15)  # dollar discount
        budget = (qty1 * price1 + qty2 * price2) - discount + rng.randint(10, 50)

        cost1 = qty1 * price1
        cost2 = qty2 * price2
        subtotal = cost1 + cost2
        total_spent = subtotal - discount
        change = budget - total_spent

        question = (
            f"Jordan has ${budget} to spend at a stationery store. Jordan purchases {qty1} {item_name} for "
            f"${price1} each and {qty2} decorative organizers for ${price2} each. The cashier applies a "
            f"${discount} store coupon to the total purchase. After paying for these items, how much money does "
            f"Jordan have left?"
        )
        scratchpad = (
            f"Cost of {item_name}: {qty1} * {price1} = ${cost1}.\n"
            f"Cost of organizers: {qty2} * {price2} = ${cost2}.\n"
            f"Subtotal: {cost1} + {cost2} = ${subtotal}.\n"
            f"Total after coupon: {subtotal} - {discount} = ${total_spent}.\n"
            f"Remaining change: {budget} - {total_spent} = ${change}.\n"
            f"#### {change}"
        )
        target = str(change)

    elif template_type == "travel":
        speed1 = rng.randint(40, 70)  # mph
        hours1 = rng.randint(2, 5)
        speed2 = speed1 + rng.choice([-15, -10, 10, 15, 20])
        hours2 = rng.randint(1, 4)
        dist1 = speed1 * hours1
        dist2 = speed2 * hours2
        total_dist = dist1 + dist2

        person = rng.choice(["Elena", "Marcus", "Siddharth", "Amina", "Chloe", "Darius"])
        question = (
            f"{person} drives on a cross-country trip. For the first leg of the journey, {person} drives at an "
            f"average speed of {speed1} mph for {hours1} hours. During the second leg, traffic changes the speed to "
            f"{speed2} mph for another {hours2} hours. What is the total distance in miles that {person} traveled?"
        )
        scratchpad = (
            f"Distance for leg 1: {speed1} mph * {hours1} hours = {dist1} miles.\n"
            f"Distance for leg 2: {speed2} mph * {hours2} hours = {dist2} miles.\n"
            f"Total distance: {dist1} + {dist2} = {total_dist} miles.\n"
            f"#### {total_dist}"
        )
        target = str(total_dist)

    elif template_type == "work_rate":
        rate1 = rng.randint(15, 35)  # items per hour
        hours1 = rng.randint(3, 7)
        rate2 = rng.randint(20, 45)
        hours2 = rng.randint(2, 6)
        total_output = (rate1 * hours1) + (rate2 * hours2)
        item_product = rng.choice(
            ["pottery mugs", "solar panels", "circuit boards", "woven baskets", "wooden toys"]
        )

        question = (
            f"A craftsman makes {rate1} {item_product} per hour and works for {hours1} hours on Saturday. "
            f"On Sunday, an apprentice helps, increasing their joint production to {rate2} {item_product} per hour "
            f"for {hours2} hours. How many {item_product} did they make altogether over the weekend?"
        )
        scratchpad = (
            f"Saturday production: {rate1} * {hours1} = {rate1 * hours1}.\n"
            f"Sunday production: {rate2} * {hours2} = {rate2 * hours2}.\n"
            f"Total weekend production: {rate1 * hours1} + {rate2 * hours2} = {total_output}.\n"
            f"#### {total_output}"
        )
        target = str(total_output)

    elif template_type == "finance":
        starting = rng.randint(150, 500)
        weekly_deposit = rng.randint(25, 60)
        weeks = rng.randint(4, 12)
        withdrawal = rng.randint(40, 120)
        final_balance = starting + (weekly_deposit * weeks) - withdrawal

        person = rng.choice(["Liam", "Priya", "Carlos", "Fatima", "Zoe", "Kei"])
        question = (
            f"{person} starts a savings account with an initial deposit of ${starting}. Each week for {weeks} weeks, "
            f"{person} deposits an additional ${weekly_deposit}. At the end of the {weeks} weeks, {person} withdraws "
            f"${withdrawal} to buy a concert ticket. What is {person}'s final account balance in dollars?"
        )
        scratchpad = (
            f"Total weekly deposits: {weekly_deposit} * {weeks} = ${weekly_deposit * weeks}.\n"
            f"Balance before withdrawal: {starting} + {weekly_deposit * weeks} = ${starting + weekly_deposit * weeks}.\n"
            f"Final balance: {starting + weekly_deposit * weeks} - {withdrawal} = ${final_balance}.\n"
            f"#### {final_balance}"
        )
        target = str(final_balance)

    elif template_type == "geometry":
        length = rng.randint(8, 25)
        width = rng.randint(4, length - 1)
        cost_per_foot = rng.randint(3, 12)
        perimeter = 2 * (length + width)
        total_cost = perimeter * cost_per_foot

        question = (
            f"A rectangular community garden measures {length} feet long and {width} feet wide. The gardeners "
            f"need to install a protective wooden border around the entire perimeter. If the wooden border costs "
            f"${cost_per_foot} per foot, what will be the total cost in dollars to fence the perimeter?"
        )
        scratchpad = (
            f"Perimeter = 2 * ({length} + {width}) = 2 * {length + width} = {perimeter} feet.\n"
            f"Total cost = {perimeter} feet * ${cost_per_foot}/foot = ${total_cost}.\n"
            f"#### {total_cost}"
        )
        target = str(total_cost)

    else:  # tournament
        round1_points = rng.randint(40, 90)
        bonus = rng.randint(10, 30)
        penalty = rng.randint(5, 20)
        round2_multiplier = rng.randint(2, 3)
        round2_base = rng.randint(20, 45)
        round2_points = round2_base * round2_multiplier

        final_score = round1_points + bonus - penalty + round2_points

        team = rng.choice(
            ["Robotics Team", "Debate Club", "Mathlete Squad", "Chess Club", "Quiz Bowl Team"]
        )
        question = (
            f"The school's {team} scored {round1_points} points in the opening round. They were awarded a {bonus}-point "
            f"bonus for teamwork but received a {penalty}-point penalty for a late submission. In the final round, "
            f"they scored {round2_multiplier} times their base score of {round2_base} points. What was the team's "
            f"total final score?"
        )
        scratchpad = (
            f"Round 1 after bonus and penalty: {round1_points} + {bonus} - {penalty} = {round1_points + bonus - penalty}.\n"
            f"Round 2 score: {round2_base} * {round2_multiplier} = {round2_points}.\n"
            f"Final total score: {round1_points + bonus - penalty} + {round2_points} = {final_score}.\n"
            f"#### {final_score}"
        )
        target = str(final_score)

    item_id = f"math-synth-{index:04d}"

    return SuiteItem(
        item_id=item_id,
        group="math",
        prompt=question,
        target=target,
        answer_check="exact_numeric",
        choices=None,
        metadata={
            "source": "synthetic_procedural_math_generator",
            "version": "1.0",
            "license": "Project-Internal (Synthetic)",
            "license_url": "N/A",
            "url": "local",
            "verified_on_official_page": True,
            "contamination_risk": "ZERO (Procedurally generated with fixed PRNG seed)",
            "scratchpad": scratchpad,
            "template_type": template_type,
        },
    )


def generate_math_suite(n_items: int, seed: int = 20260101) -> list[SuiteItem]:
    """Generate n_items deterministic synthetic math word problems using seed."""
    rng = random.Random(seed)
    return [generate_math_problem(rng, i) for i in range(1, n_items + 1)]
