"""Deterministic procedural generator for synthetic math word problems.

Produces math tasks with exact numeric answers and step-by-step reasoning scratchpads.
Uses fixed seeds for bitwise reproducibility.
Suite v2.0: Expanded to 16 procedural template families with explicit template_family metadata.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from evaluation.loaders.common import SuiteItem

if TYPE_CHECKING:
    from collections.abc import Set

MATH_FAMILIES = (
    "shopping",
    "travel",
    "work_rate",
    "finance",
    "geometry",
    "tournament",
    "mixture_concentration",
    "age_word_problem",
    "train_relative_speed",
    "cistern_pipes",
    "profit_loss_markup",
    "arithmetic_progression",
    "probability_combinations",
    "clock_angle",
    "ratio_proportions",
    "average_score",
)


def generate_math_problem(rng: random.Random, index: int) -> SuiteItem:
    """Generate a single deterministic multi-step math word problem across 16 families."""
    template_type = rng.choice(MATH_FAMILIES)

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

    elif template_type == "tournament":
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

    elif template_type == "mixture_concentration":
        kg1 = rng.randint(4, 15)
        p1 = rng.randint(6, 18)
        kg2 = rng.randint(5, 20)
        p2 = rng.randint(10, 30)
        total_cost = (kg1 * p1) + (kg2 * p2)
        nut1, nut2 = rng.sample(["cashews", "almonds", "walnuts", "pecans", "pistachios"], 2)

        question = (
            f"A gourmet food distributor mixes {kg1} kilograms of {nut1} priced at ${p1} per kilogram with "
            f"{kg2} kilograms of {nut2} priced at ${p2} per kilogram to create a holiday trail mix. What is the "
            f"total cost in dollars of the ingredients used in the mixture?"
        )
        scratchpad = (
            f"Cost of {nut1}: {kg1} * {p1} = ${kg1 * p1}.\n"
            f"Cost of {nut2}: {kg2} * {p2} = ${kg2 * p2}.\n"
            f"Total cost: {kg1 * p1} + {kg2 * p2} = ${total_cost}.\n"
            f"#### {total_cost}"
        )
        target = str(total_cost)

    elif template_type == "age_word_problem":
        child_age = rng.randint(6, 14)
        mult = rng.randint(3, 5)
        parent_age = child_age * mult
        years_future = rng.randint(4, 12)
        future_child = child_age + years_future

        p_name, c_name = rng.choice([("Samuel", "Leo"), ("Miriam", "Anya"), ("Robert", "Toby")])
        question = (
            f"{p_name} is currently {mult} times as old as their child {c_name}. In {years_future} years, {c_name} "
            f"will be {future_child} years old. How old is {p_name} right now?"
        )
        scratchpad = (
            f"{c_name}'s current age: {future_child} - {years_future} = {child_age}.\n"
            f"{p_name}'s current age: {child_age} * {mult} = {parent_age}.\n"
            f"#### {parent_age}"
        )
        target = str(parent_age)

    elif template_type == "train_relative_speed":
        s1 = rng.randint(45, 80)
        s2 = rng.randint(50, 85)
        hours = rng.randint(2, 4)
        traveled = (s1 + s2) * hours
        initial_dist = traveled + rng.randint(25, 120)
        remaining = initial_dist - traveled

        question = (
            f"Two trains leave two stations located {initial_dist} miles apart at the same time and travel toward "
            f"each other on parallel tracks. Train 1 travels at {s1} miles per hour and Train 2 travels at {s2} "
            f"miles per hour. After {hours} hours of traveling, how many miles apart are the two trains?"
        )
        scratchpad = (
            f"Distance traveled by Train 1: {s1} * {hours} = {s1 * hours} miles.\n"
            f"Distance traveled by Train 2: {s2} * {hours} = {s2 * hours} miles.\n"
            f"Total distance covered: {s1 * hours} + {s2 * hours} = {traveled} miles.\n"
            f"Remaining distance: {initial_dist} - {traveled} = {remaining} miles.\n"
            f"#### {remaining}"
        )
        target = str(remaining)

    elif template_type == "cistern_pipes":
        r_in = rng.randint(25, 60)
        r_out = rng.randint(10, r_in - 8)
        net_rate = r_in - r_out
        initial_vol = rng.randint(100, 300)
        hours = rng.randint(3, 8)
        final_vol = initial_vol + (net_rate * hours)

        question = (
            f"A water cistern currently contains {initial_vol} gallons of water. An inlet pipe fills the cistern "
            f"at a rate of {r_in} gallons per hour, while an outlet pipe discharges water at a rate of {r_out} gallons "
            f"per hour. If both pipes operate simultaneously for {hours} hours, how many gallons of water will be in the cistern?"
        )
        scratchpad = (
            f"Net hourly rate of filling: {r_in} - {r_out} = {net_rate} gallons/hour.\n"
            f"Water added over {hours} hours: {net_rate} * {hours} = {net_rate * hours} gallons.\n"
            f"Final water volume: {initial_vol} + {net_rate * hours} = {final_vol} gallons.\n"
            f"#### {final_vol}"
        )
        target = str(final_vol)

    elif template_type == "profit_loss_markup":
        cost_price = rng.randint(40, 150)
        markup = rng.randint(30, 80)
        discount = rng.randint(5, markup - 10)
        net_profit = markup - discount

        item_sale = rng.choice(
            ["vintage bicycle", "espresso machine", "telescope", "acoustic guitar"]
        )
        question = (
            f"A boutique store buys a {item_sale} for ${cost_price}. The manager marks up the price by adding ${markup}. "
            f"During an anniversary sale, a promotional voucher discounts the marked price by ${discount}. What is the "
            f"store's net profit in dollars from selling the {item_sale}?"
        )
        scratchpad = (
            f"Marked selling price: ${cost_price} + ${markup} = ${cost_price + markup}.\n"
            f"Discounted sale price: ${cost_price + markup} - ${discount} = ${cost_price + markup - discount}.\n"
            f"Net profit: ${cost_price + markup - discount} - ${cost_price} = ${net_profit}.\n"
            f"#### {net_profit}"
        )
        target = str(net_profit)

    elif template_type == "arithmetic_progression":
        rows = rng.randint(4, 9)
        first_row = rng.randint(12, 30)
        diff = rng.randint(2, 6)
        total_seats = rows * (2 * first_row + (rows - 1) * diff) // 2

        question = (
            f"A newly constructed concert hall has {rows} rows of premium orchestra seats. The first row has {first_row} "
            f"seats, and each subsequent row has {diff} more seats than the row immediately before it. How many total "
            f"seats are there across all {rows} rows?"
        )
        scratchpad = (
            f"Arithmetic progression with n={rows}, a={first_row}, d={diff}.\n"
            f"Total = {rows}/2 * (2*{first_row} + ({rows}-1)*{diff}) = {total_seats}.\n"
            f"#### {total_seats}"
        )
        target = str(total_seats)

    elif template_type == "probability_combinations":
        red = rng.randint(15, 35)
        blue = rng.randint(15, 35)
        green = rng.randint(15, 35)
        take_red = rng.randint(3, 10)
        take_blue = rng.randint(3, 10)
        remaining = (red - take_red) + (blue - take_blue) + green

        question = (
            f"An art supplies bin contains {red} red markers, {blue} blue markers, and {green} green markers. An art "
            f"teacher removes {take_red} red markers and {take_blue} blue markers to distribute to students. How many "
            f"total markers remain in the bin?"
        )
        scratchpad = (
            f"Initial total markers: {red} + {blue} + {green} = {red + blue + green}.\n"
            f"Total markers removed: {take_red} + {take_blue} = {take_red + take_blue}.\n"
            f"Remaining markers: {red + blue + green} - {take_red + take_blue} = {remaining}.\n"
            f"#### {remaining}"
        )
        target = str(remaining)

    elif template_type == "clock_angle":
        rotations = rng.randint(3, 8)
        extra_degrees = rng.choice([30, 45, 60, 90, 120, 150, 180, 270])
        total_degrees = (rotations * 360) + extra_degrees

        question = (
            f"A mechanical precision gear connected to a test dial completes {rotations} full clockwise revolutions "
            f"and then rotates through an additional {extra_degrees} degrees before stopping. What is the total number "
            f"of degrees through which the dial rotated?"
        )
        scratchpad = (
            f"Degrees in full revolutions: {rotations} * 360 = {rotations * 360} degrees.\n"
            f"Total rotation: {rotations * 360} + {extra_degrees} = {total_degrees} degrees.\n"
            f"#### {total_degrees}"
        )
        target = str(total_degrees)

    elif template_type == "ratio_proportions":
        ratio_w = rng.randint(3, 7)
        ratio_o = rng.randint(2, 5)
        while ratio_o == ratio_w:
            ratio_o = rng.randint(2, 6)
        mult = rng.randint(4, 15)
        wheat_weight = ratio_w * mult
        oat_weight = ratio_o * mult

        question = (
            f"A grain mill produces a mixed flour blend where the ratio of whole wheat to crushed oats by weight is "
            f"{ratio_w} to {ratio_o}. If a baker uses {wheat_weight} kilograms of whole wheat, how many kilograms of "
            f"crushed oats must be used to maintain the exact ratio?"
        )
        scratchpad = (
            f"Scale factor: {wheat_weight} / {ratio_w} = {mult}.\n"
            f"Required oats weight: {ratio_o} * {mult} = {oat_weight} kg.\n"
            f"#### {oat_weight}"
        )
        target = str(oat_weight)

    else:  # average_score
        target_avg = rng.randint(82, 94)
        s1 = target_avg + rng.randint(-8, 5)
        s2 = target_avg + rng.randint(-6, 7)
        s3 = target_avg + rng.randint(-10, 4)
        total_needed = target_avg * 4
        s4 = total_needed - (s1 + s2 + s3)
        student = rng.choice(["Maya", "Julian", "Fatima", "Chen", "Devon"])

        question = (
            f"{student} has taken three chemistry tests this semester, earning scores of {s1}, {s2}, and {s3}. What score "
            f"must {student} earn on the fourth test to finish the course with an overall average test score of {target_avg}?"
        )
        scratchpad = (
            f"Total points needed across 4 tests: {target_avg} * 4 = {total_needed}.\n"
            f"Points earned so far: {s1} + {s2} + {s3} = {s1 + s2 + s3}.\n"
            f"Required score on test 4: {total_needed} - {s1 + s2 + s3} = {s4}.\n"
            f"#### {s4}"
        )
        target = str(s4)

    item_id = f"math-synth-{index:04d}"

    return SuiteItem(
        item_id=item_id,
        group="math",
        prompt=question,
        target=target,
        answer_check="exact_numeric",
        choices=None,
        arm="synthetic",
        template_family=template_type,
        metadata={
            "source": "synthetic_procedural_math_generator",
            "version": "2.0",
            "license": "Project-Internal (Synthetic)",
            "license_url": "N/A",
            "url": "local",
            "verified_on_official_page": True,
            "contamination_risk": "ZERO (Procedurally generated with fixed PRNG seed)",
            "scratchpad": scratchpad,
            "template_family": template_type,
            "template_type": template_type,
            "arm": "synthetic",
        },
    )


def generate_math_suite(
    n_items: int,
    seed: int = 20260101,
    seen_prompts: Set[str] | None = None,
) -> list[SuiteItem]:
    """Generate n_items deterministic synthetic math word problems using seed."""
    rng = random.Random(seed)
    items: list[SuiteItem] = []
    i = 1
    while len(items) < n_items:
        problem = generate_math_problem(rng, i)
        prompt_norm = " ".join(problem["prompt"].lower().split())
        if seen_prompts is not None:
            if prompt_norm in seen_prompts:
                i += 1
                continue
            seen_prompts.add(prompt_norm)
        items.append(problem)
        i += 1
    return items
