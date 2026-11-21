"""Synthetic procedural generator for code tasks with unit tests.

Addresses the contamination and size deficit of HumanEval (N=164) and MBPP.
Generates fresh Python coding tasks with complete canonical solutions and
robust unit test suites asserting edge cases and typical cases.
Supports seen_prompts to guarantee 100% zero prompt duplication across partitions.
"""

from __future__ import annotations

import random

from evaluation.loaders.common import SuiteItem, check_unit_tests_pass


def _make_filter_greater(rng: random.Random, idx: int) -> dict[str, str]:
    k = rng.randint(5, 50)
    func_name = f"filter_greater_than_{k}_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> list[int]:
    """Return a new list containing only elements strictly greater than {k}.
    Preserves the relative order of elements.
    >>> {func_name}([{k - 2}, {k}, {k + 5}, {k - 3}, {k + 12}])
    [{k + 5}, {k + 12}]
    >>> {func_name}([])
    []
    """
'''
    canonical = f"""    return [x for x in nums if x > {k}]
"""
    test = f"""def check(candidate):
    assert candidate([{k - 2}, {k}, {k + 5}, {k - 3}, {k + 12}]) == [{k + 5}, {k + 12}]
    assert candidate([]) == []
    assert candidate([{k - 5}, {k - 1}, {k}]) == []
    assert candidate([{k + 1}, {k + 2}]) == [{k + 1}, {k + 2}]
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_count_divisible(rng: random.Random, idx: int) -> dict[str, str]:
    d = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    func_name = f"count_divisible_by_{d}_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> int:
    """Return the total count of numbers in nums that are evenly divisible by {d}.
    >>> {func_name}([{d}, {d * 2}, {d * 3 + 1}, {d * 4 + 1}])
    2
    >>> {func_name}([])
    0
    """
'''
    canonical = f"""    return sum(1 for x in nums if x % {d} == 0)
"""
    test = f"""def check(candidate):
    assert candidate([{d}, {d * 2}, {d * 3 + 1}, {d * 4 + 1}]) == 2
    assert candidate([]) == 0
    assert candidate([0]) == 1
    assert candidate([{d * 3}, {d * 4}, {d * 5}]) == 3
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_clamp_values(rng: random.Random, idx: int) -> dict[str, str]:
    low = rng.randint(0, 15)
    high = low + rng.randint(10, 40)
    func_name = f"clamp_range_{low}_to_{high}_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> list[int]:
    """Clamp all integers in nums to be within the inclusive range [{low}, {high}].
    If x < {low}, replace with {low}; if x > {high}, replace with {high}.
    >>> {func_name}([{low - 5}, {low + 2}, {high + 10}])
    [{low}, {low + 2}, {high}]
    >>> {func_name}([])
    []
    """
'''
    canonical = f"""    return [max({low}, min({high}, x)) for x in nums]
"""
    test = f"""def check(candidate):
    assert candidate([{low - 5}, {low + 2}, {high + 10}]) == [{low}, {low + 2}, {high}]
    assert candidate([]) == []
    assert candidate([{low}, {high}]) == [{low}, {high}]
    assert candidate([{low - 100}, {high + 200}]) == [{low}, {high}]
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_shift_right(rng: random.Random, idx: int) -> dict[str, str]:
    k = rng.randint(1, 5)
    func_name = f"cyclic_shift_right_{k}_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> list[int]:
    """Cyclically rotate list elements to the right by {k} positions.
    If len(nums) <= 1, return the list unchanged.
    >>> {func_name}([1, 2, 3, 4, 5])
    """
'''
    canonical = f"""    if not nums:
        return []
    shift = {k} % len(nums)
    if shift == 0:
        return list(nums)
    return nums[-shift:] + nums[:-shift]
"""
    test = f"""def check(candidate):
    res = candidate([1, 2, 3, 4, 5])
    shift = {k} % 5
    expected = [1, 2, 3, 4, 5][-shift:] + [1, 2, 3, 4, 5][:-shift] if shift != 0 else [1, 2, 3, 4, 5]
    assert res == expected
    assert candidate([]) == []
    assert candidate([42]) == [42]
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_replace_negatives(rng: random.Random, idx: int) -> dict[str, str]:
    fill = rng.randint(0, 50)
    func_name = f"replace_negatives_{fill}_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> list[int]:
    """Return a new list where all negative integers are replaced with {fill}.
    Non-negative integers remain unchanged.
    >>> {func_name}([-5, 10, -2, 0, 7])
    [{fill}, 10, {fill}, 0, 7]
    >>> {func_name}([])
    []
    """
'''
    canonical = f"""    return [x if x >= 0 else {fill} for x in nums]
"""
    test = f"""def check(candidate):
    assert candidate([-5, 10, -2, 0, 7]) == [{fill}, 10, {fill}, 0, 7]
    assert candidate([]) == []
    assert candidate([1, 2, 3]) == [1, 2, 3]
    assert candidate([-1, -2]) == [{fill}, {fill}]
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_run_length(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"compress_run_length_{idx:03d}"
    prompt = f'''def {func_name}(s: str) -> str:
    """Compress a string using run-length encoding.
    Consecutive duplicate characters are replaced with character and frequency count.
    Single characters are kept as just the character.
    >>> {func_name}('aaabbc')
    'a3b2c'
    >>> {func_name}('')
    ''
    """
'''
    canonical = """    if not s:
        return ""
    result = []
    current_char = s[0]
    count = 1
    for char in s[1:]:
        if char == current_char:
            count += 1
        else:
            result.append(f"{current_char}{count}" if count > 1 else current_char)
            current_char = char
            count = 1
    result.append(f"{current_char}{count}" if count > 1 else current_char)
    return "".join(result)
"""
    test = f"""def check(candidate):
    assert candidate('aaabbc') == 'a3b2c'
    assert candidate('') == ''
    assert candidate('abcdef') == 'abcdef'
    assert candidate('aaaa') == 'a4'
    assert candidate('aabcccccaaa') == 'a2bc5a3'
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_top_k(rng: random.Random, idx: int) -> dict[str, str]:
    k = rng.choice([1, 2, 3])
    func_name = f"top_k_frequent_{k}_{idx:03d}"
    prompt = f'''def {func_name}(items: list[int]) -> list[int]:
    """Return the top {k} most frequent integers in items.
    On frequency ties, the element appearing first in the original list wins.
    >>> {func_name}([1, 1, 1, 2, 2, 3])
    """
'''
    canonical = f"""    from collections import Counter
    if not items:
        return []
    counts = Counter(items)
    first_seen = {{}}
    for idx, x in enumerate(items):
        if x not in first_seen:
            first_seen[x] = idx
    unique_items = sorted(counts.keys(), key=lambda x: (-counts[x], first_seen[x]))
    return unique_items[:{k}]
"""
    test = f"""def check(candidate):
    res = candidate([1, 1, 1, 2, 2, 3])
    assert len(res) == min({k}, 3)
    assert res[0] == 1
    assert candidate([]) == []
    assert candidate([5, 5, 5]) == [5]
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_sliding_window_max(rng: random.Random, idx: int) -> dict[str, str]:
    w = rng.choice([2, 3, 4])
    func_name = f"sliding_window_max_{w}_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> list[int]:
    """Return the maximum element in each contiguous sliding window of size {w}.
    If len(nums) < {w}, return [max(nums)] if non-empty, else [].
    >>> {func_name}([1, 3, -1, -3, 5, 3, 6, 7])
    """
'''
    canonical = f"""    if not nums:
        return []
    if len(nums) < {w}:
        return [max(nums)]
    res = []
    for i in range(len(nums) - {w} + 1):
        res.append(max(nums[i : i + {w}]))
    return res
"""
    test = f"""def check(candidate):
    res = candidate([1, 3, -1, -3, 5, 3, 6, 7])
    assert len(res) == len([1, 3, -1, -3, 5, 3, 6, 7]) - {w} + 1
    assert candidate([]) == []
    assert candidate([42]) == [42]
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_balanced_brackets(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"is_balanced_brackets_{idx:03d}"
    prompt = f'''def {func_name}(s: str) -> bool:
    """Return True if all round (), square [], and curly {{}} brackets are balanced.
    Ignore all non-bracket characters.
    >>> {func_name}('([a + b] * {{2}})')
    True
    >>> {func_name}('([)]')
    False
    """
'''
    canonical = """    stack = []
    mapping = {")": "(", "}": "{", "]": "["}
    for char in s:
        if char in "({[":
            stack.append(char)
        elif char in ")}]":
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
    return len(stack) == 0
"""
    test = f"""def check(candidate):
    assert candidate('([a + b] * {{2}})') == True
    assert candidate('([)]') == False
    assert candidate('') == True
    assert candidate('(((((') == False
    assert candidate('{{[[(())]]}}') == True
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_longest_unique_substr(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"longest_unique_substring_{idx:03d}"
    prompt = f'''def {func_name}(s: str) -> int:
    """Return the length of the longest substring without repeating characters.
    >>> {func_name}('abcabcbb')
    3
    >>> {func_name}('bbbbb')
    1
    >>> {func_name}('')
    0
    """
'''
    canonical = """    used = {}
    max_len = 0
    start = 0
    for idx, char in enumerate(s):
        if char in used and start <= used[char]:
            start = used[char] + 1
        else:
            max_len = max(max_len, idx - start + 1)
        used[char] = idx
    return max_len
"""
    test = f"""def check(candidate):
    assert candidate('abcabcbb') == 3
    assert candidate('bbbbb') == 1
    assert candidate('') == 0
    assert candidate('pwwkew') == 3
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_rotate_matrix(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"rotate_matrix_90_clockwise_{idx:03d}"
    prompt = f'''def {func_name}(matrix: list[list[int]]) -> list[list[int]]:
    """Return a new matrix rotated 90 degrees clockwise.
    >>> {func_name}([[1, 2], [3, 4]])
    [[3, 1], [4, 2]]
    """
'''
    canonical = """    if not matrix or not matrix[0]:
        return []
    return [list(row) for row in zip(*matrix[::-1])]
"""
    test = f"""def check(candidate):
    assert candidate([[1, 2], [3, 4]]) == [[3, 1], [4, 2]]
    assert candidate([[1, 2, 3]]) == [[1], [2], [3]]
    assert candidate([]) == []
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_merge_intervals(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"merge_intervals_{idx:03d}"
    prompt = f'''def {func_name}(intervals: list[list[int]]) -> list[list[int]]:
    """Merge all overlapping intervals and return a list of non-overlapping intervals.
    >>> {func_name}([[1, 3], [2, 6], [8, 10], [15, 18]])
    [[1, 6], [8, 10], [15, 18]]
    """
'''
    canonical = """    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]
    for current in sorted_intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            last[1] = max(last[1], current[1])
        else:
            merged.append(current)
    return merged
"""
    test = f"""def check(candidate):
    assert candidate([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert candidate([[1, 4], [4, 5]]) == [[1, 5]]
    assert candidate([]) == []
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_first_missing_pos(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"first_missing_positive_{idx:03d}"
    prompt = f'''def {func_name}(nums: list[int]) -> int:
    """Return the smallest positive integer (> 0) that does not appear in nums.
    >>> {func_name}([1, 2, 0])
    3
    >>> {func_name}([3, 4, -1, 1])
    2
    """
'''
    canonical = """    num_set = set(nums)
    candidate = 1
    while candidate in num_set:
        candidate += 1
    return candidate
"""
    test = f"""def check(candidate):
    assert candidate([1, 2, 0]) == 3
    assert candidate([3, 4, -1, 1]) == 2
    assert candidate([7, 8, 9, 11, 12]) == 1
    assert candidate([]) == 1
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_rpn(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"evaluate_rpn_{idx:03d}"
    prompt = f'''def {func_name}(tokens: list[str]) -> int:
    """Evaluate the value of an arithmetic expression in Reverse Polish Notation.
    Valid operators are +, -, *, /. Division truncates toward zero.
    >>> {func_name}(["2", "1", "+", "3", "*"])
    9
    """
'''
    canonical = """    stack = []
    for token in tokens:
        if token in {"+", "-", "*", "/"}:
            b = stack.pop()
            a = stack.pop()
            if token == "+":
                stack.append(a + b)
            elif token == "-":
                stack.append(a - b)
            elif token == "*":
                stack.append(a * b)
            elif token == "/":
                stack.append(int(a / b))
        else:
            stack.append(int(token))
    return stack[0]
"""
    test = f"""def check(candidate):
    assert candidate(["2", "1", "+", "3", "*"]) == 9
    assert candidate(["4", "13", "5", "/", "+"]) == 6
    assert candidate(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


def _make_spiral_matrix(rng: random.Random, idx: int) -> dict[str, str]:
    func_name = f"spiral_order_{idx:03d}"
    prompt = f'''def {func_name}(matrix: list[list[int]]) -> list[int]:
    """Return all elements of matrix in clockwise spiral order.
    >>> {func_name}([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    [1, 2, 3, 6, 9, 8, 7, 4, 5]
    """
'''
    canonical = """    if not matrix or not matrix[0]:
        return []
    res = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            res.append(matrix[top][col])
        top += 1
        for row in range(top, bottom + 1):
            res.append(matrix[row][right])
        right -= 1
        if top <= bottom:
            for col in range(right, left - 1, -1):
                res.append(matrix[bottom][col])
            bottom -= 1
        if left <= right:
            for row in range(bottom, top - 1, -1):
                res.append(matrix[row][left])
            left += 1
    return res
"""
    test = f"""def check(candidate):
    assert candidate([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert candidate([[1, 2], [3, 4]]) == [1, 2, 4, 3]
    assert candidate([]) == []
check({func_name})
"""
    return {
        "entry_point": func_name,
        "prompt": prompt,
        "canonical_solution": canonical,
        "test": test,
    }


GENERATOR_FACTORIES = [
    _make_filter_greater,
    _make_count_divisible,
    _make_clamp_values,
    _make_shift_right,
    _make_replace_negatives,
    _make_run_length,
    _make_top_k,
    _make_sliding_window_max,
    _make_balanced_brackets,
    _make_longest_unique_substr,
    _make_rotate_matrix,
    _make_merge_intervals,
    _make_first_missing_pos,
    _make_rpn,
    _make_spiral_matrix,
]


def generate_code_suite(
    n_items: int = 100,
    seed: int = 20260101,
    seen_prompts: set[str] | None = None,
) -> list[SuiteItem]:
    """Generate deterministic synthetic Python coding tasks with verified unit tests."""
    rng = random.Random(seed)
    items: list[SuiteItem] = []

    attempts = 0
    max_attempts = n_items * 100

    while len(items) < n_items and attempts < max_attempts:
        attempts += 1
        factory = rng.choice(GENERATOR_FACTORIES)
        data = factory(rng, len(items) + 1)

        prompt_norm = " ".join(data["prompt"].lower().split())
        if seen_prompts is not None:
            if prompt_norm in seen_prompts:
                continue
            seen_prompts.add(prompt_norm)

        # Pre-verify that canonical solution passes its own unit tests
        passes = check_unit_tests_pass(
            generated_code=data["canonical_solution"],
            test_code=data["test"],
            prompt=data["prompt"],
            entry_point=data["entry_point"],
        )
        if not passes:
            raise RuntimeError(
                f"Internal generation error: {data['entry_point']} failed self-verification"
            )

        item_id = f"code-synth-{len(items) + 1:04d}"
        items.append(
            SuiteItem(
                item_id=item_id,
                group="code",
                prompt=data["prompt"],
                target=data["canonical_solution"],
                answer_check="unit_tests_pass",
                choices=None,
                arm="synthetic",
                template_family=data["entry_point"],
                metadata={
                    "source": "synthetic_procedural_code_generator",
                    "version": "2.0",
                    "license": "Project-Internal (Synthetic)",
                    "license_url": "N/A",
                    "url": "local",
                    "verified_on_official_page": True,
                    "contamination_risk": "ZERO (Fresh synthetic implementation with verified unit tests)",
                    "entry_point": data["entry_point"],
                    "test_code": data["test"],
                    "template_family": data["entry_point"],
                    "arm": "synthetic",
                },
            )
        )

    if len(items) < n_items:
        raise RuntimeError(f"Could not generate {n_items} unique code items (reached {len(items)})")

    return items
