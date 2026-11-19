# Phase B: 50-Item Calibration Pilot Report

- **Model**: `Qwen/Qwen2.5-0.5B-Instruct` (FP16, cuda:0)
- **VRAM Footprint**: Allocated 942.3 MB (well within 1.5 GB budget)
- **Evaluation Split**: `suite/validation/` (Suite v2.1)
- **Sample**: 50 items per group (300 items total, seed 20260102)
- **Acceptance Gates**:
  1. Truncation rate < 1.0% across all groups
  2. Extractable rate = 100.0% across all groups

## 1. 50-Item Pilot Group Summary

| Group | Cap | Tokens (min/med/p95/max) | Trunc % | Trunc Pass | Extractable % | Extr Pass | Accuracy | Latency p50/p95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `math` | 768 | 133 / 261 / 421 / 504 | 0.0% | PASS | 100.0% | PASS | 21/50 (42.0%) | 5740.5 / 8744.6 |
| `science_mcq` | 32 | 2 / 2 / 2 / 2 | 0.0% | PASS | 100.0% | PASS | 22/50 (44.0%) | 658.7 / 673.5 |
| `knowledge_mcq` | 32 | 2 / 2 / 2 / 5 | 0.0% | PASS | 100.0% | PASS | 22/50 (44.0%) | 655.5 / 695.9 |
| `code` | 1024 | 26 / 152 / 330 / 336 | 0.0% | PASS | 100.0% | PASS | 13/50 (26.0%) | 3155.4 / 6804.4 |
| `knowledge_qa` | 128 | 2 / 15 / 29 / 59 | 0.0% | PASS | 100.0% | PASS | 32/50 (64.0%) | 355.2 / 660.6 |
| `memory_probe` | 128 | 4 / 18 / 29 / 33 | 0.0% | PASS | 100.0% | PASS | 36/50 (72.0%) | 393.8 / 636.2 |

## 2. 20 Random Outputs Per Group (Owner Inspection)

### Group: `math` (9/20 correct — 45.0%)

| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `math_val_0191` | synthetic | `49` | `516.0` | **FAIL** | 202 | 5935.76 | To solve this problem, we need to determine the distance eac... |
| 2 | `math_val_0031` | public | `40` | `48.0` | **FAIL** | 231 | 4796.03 | Let's break down the information given:  - The first kitten ... |
| 3 | `math_val_0029` | public | `144` | `72.0` | **FAIL** | 212 | 4560.34 | Let's break down the problem step by step:  1. **First Year*... |
| 4 | `math_val_0167` | synthetic | `156` | `156.0` | **PASS** | 200 | 4185.16 | Let's break down the scoring process step-by-step:  ### Open... |
| 5 | `math_val_0200` | synthetic | `41` | `41.0` | **PASS** | 202 | 4476.61 | Let's solve this step-by-step:  1) First, we need to find ou... |
| 6 | `math_val_0145` | synthetic | `112` | `528.0` | **FAIL** | 208 | 4369.21 | To solve this problem, we need to determine the distance eac... |
| 7 | `math_val_0082` | public | `750` | `15.0` | **FAIL** | 377 | 7944.96 | To determine how many telephone calls Jason needs to make to... |
| 8 | `math_val_0141` | synthetic | `440` | `440.0` | **PASS** | 346 | 7236.74 | To determine the total cost of fencing the perimeter of the ... |
| 9 | `math_val_0050` | public | `100` | `20.0` | **FAIL** | 237 | 4914.8 | Let's break down the information given:  1. Total number of ... |
| 10 | `math_val_0040` | public | `720` | `720.0` | **PASS** | 156 | 3264.23 | To solve this problem, we need to calculate the total cost o... |
| 11 | `math_val_0062` | public | `280` | `180.0` | **FAIL** | 421 | 8744.58 | To determine the total length of all the baked goods Bill ba... |
| 12 | `math_val_0157` | synthetic | `198` | `198.0` | **PASS** | 327 | 6807.26 | To determine the total cost of fencing the perimeter of the ... |
| 13 | `math_val_0159` | synthetic | `497` | `596.0` | **FAIL** | 235 | 4862.06 | Let's break down the problem step by step:  1. **Initial Dep... |
| 14 | `math_val_0166` | synthetic | `118` | `118.0` | **PASS** | 251 | 5193.25 | To determine the total cost of the ingredients used in the m... |
| 15 | `math_val_0129` | synthetic | `496` | `496.0` | **PASS** | 277 | 5740.46 | Let's break down the problem step by step:  1. **Initial Dep... |
| 16 | `math_val_0112` | synthetic | `10` | `3.0` | **FAIL** | 253 | 5244.59 | To solve this problem, we need to determine the amount of cr... |
| 17 | `math_val_0104` | synthetic | `1860` | `1860.0` | **PASS** | 238 | 4934.15 | To determine the total number of degrees through which the d... |
| 18 | `math_val_0020` | public | `247` | `247.0` | **PASS** | 229 | 4741.86 | To find the total number of classes that visited the Science... |
| 19 | `math_val_0078` | public | `5` | `6.67` | **FAIL** | 183 | 3785.88 | To determine how much money each of Greg's siblings received... |
| 20 | `math_val_0048` | public | `800` | `160.0` | **FAIL** | 328 | 6809.3 | Let's break down the problem step by step:  1. **Determine t... |

### Group: `science_mcq` (9/20 correct — 45.0%)

| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `sci_val_0070` | public | `C` | `D` | **FAIL** | 2 | 679.85 | D |
| 2 | `sci_val_0168` | public | `A` | `C` | **FAIL** | 2 | 669.07 | C |
| 3 | `sci_val_0136` | public | `B` | `B` | **PASS** | 2 | 664.13 | B |
| 4 | `sci_val_0142` | public | `C` | `B` | **FAIL** | 2 | 662.01 | B |
| 5 | `sci_val_0123` | public | `A` | `B` | **FAIL** | 2 | 664.4 | B |
| 6 | `sci_val_0116` | public | `A` | `A` | **PASS** | 2 | 673.54 | A |
| 7 | `sci_val_0132` | public | `B` | `A` | **FAIL** | 2 | 668.86 | A |
| 8 | `sci_val_0105` | public | `D` | `D` | **PASS** | 2 | 660.69 | D |
| 9 | `sci_val_0099` | public | `C` | `C` | **PASS** | 2 | 681.08 | C |
| 10 | `sci_val_0112` | public | `C` | `C` | **PASS** | 2 | 669.66 | C |
| 11 | `sci_val_0114` | public | `B` | `B` | **PASS** | 2 | 660.31 | B |
| 12 | `sci_val_0014` | public | `D` | `A` | **FAIL** | 2 | 658.66 | A |
| 13 | `sci_val_0104` | public | `B` | `B` | **PASS** | 2 | 656.63 | B |
| 14 | `sci_val_0125` | public | `A` | `B` | **FAIL** | 2 | 658.75 | B |
| 15 | `sci_val_0028` | public | `A` | `A` | **PASS** | 2 | 658.17 | A |
| 16 | `sci_val_0184` | public | `D` | `A` | **FAIL** | 2 | 669.96 | A |
| 17 | `sci_val_0182` | public | `C` | `C` | **PASS** | 2 | 661.44 | C |
| 18 | `sci_val_0073` | public | `B` | `C` | **FAIL** | 2 | 659.07 | C |
| 19 | `sci_val_0119` | public | `B` | `D` | **FAIL** | 2 | 661.43 | D |
| 20 | `sci_val_0195` | public | `D` | `A` | **FAIL** | 2 | 660.02 | A |

### Group: `knowledge_mcq` (8/20 correct — 40.0%)

| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `know_val_0166` | public | `B` | `A` | **FAIL** | 2 | 665.58 | A |
| 2 | `know_val_0058` | public | `B` | `B` | **PASS** | 2 | 652.75 | B |
| 3 | `know_val_0202` | public | `D` | `D` | **PASS** | 2 | 653.23 | D |
| 4 | `know_val_0009` | public | `A` | `A` | **PASS** | 2 | 661.09 | A |
| 5 | `know_val_0057` | public | `B` | `B` | **PASS** | 2 | 655.5 | B |
| 6 | `know_val_0042` | public | `B` | `B` | **PASS** | 2 | 656.65 | B |
| 7 | `know_val_0015` | public | `D` | `A` | **FAIL** | 2 | 655.02 | A |
| 8 | `know_val_0269` | public | `D` | `A` | **FAIL** | 2 | 654.17 | A |
| 9 | `know_val_0156` | public | `D` | `D` | **PASS** | 2 | 680.97 | D |
| 10 | `know_val_0222` | public | `A` | `D` | **FAIL** | 2 | 659.17 | D |
| 11 | `know_val_0281` | public | `D` | `A` | **FAIL** | 2 | 651.1 | A |
| 12 | `know_val_0275` | public | `C` | `D` | **FAIL** | 2 | 659.7 | D |
| 13 | `know_val_0237` | public | `B` | `B` | **PASS** | 2 | 677.09 | B |
| 14 | `know_val_0112` | public | `D` | `C` | **FAIL** | 2 | 650.68 | C |
| 15 | `know_val_0221` | public | `B` | `C` | **FAIL** | 2 | 689.56 | C |
| 16 | `know_val_0174` | public | `B` | `A` | **FAIL** | 2 | 676.12 | A |
| 17 | `know_val_0137` | public | `A` | `A` | **PASS** | 2 | 656.05 | A |
| 18 | `know_val_0108` | public | `B` | `C` | **FAIL** | 2 | 660.14 | C |
| 19 | `know_val_0012` | public | `A` | `C` | **FAIL** | 2 | 643.11 | C |
| 20 | `know_val_0290` | public | `A` | `D` | **FAIL** | 2 | 659.34 | D |

### Group: `code` (8/20 correct — 40.0%)

| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `code_val_0024` | public | `def is_undulating(n): 
	if (len(n) <= 2): 
		return False
	for i in range(2, len(n)): 
		if (n[i - 2] != n[i]): 
			return False
	return True` | `def is_undulating(number):
    """
    Check if the given number is undulating.

    A number is considered undulating if it has at least two consecutive digits that are the same.
    
    Parameters:
    - number (int): The number to be checked.

    Returns:
    - bool: True if the number is undulating, False otherwise.
    """
    # Convert the number to a string and iterate through each character
    for i in range(len(str(number)) - 1):
        # If the current digit is equal to the next one, return False
        if str(number)[i] == str(number)[i+1]:
            return False
    # If we've gone through all characters without finding any consecutive duplicates,
    # the number is undulating
    return True

# Test cases
print(is_undulating(1234567890))  # Expected output: True
print(is_undulating(12345678901))  # Expected output: False
print(is_undulating(123456789012))  # Expected output: True` | **PASS** | 248 | 5127.09 | ```python def is_undulating(number):     """     Check if th... |
| 2 | `code_val_0040` | public | `def multiply_num(numbers):  
    total = 1
    for x in numbers:
        total *= x  
    return total/len(numbers) ` | `def multiply_and_divide(numbers):
    """
    Multiply all the numbers in the given list and divide it by the length of the list.

    Parameters:
    numbers (list): A list of integers.

    Returns:
    float: The result of multiplying all elements in the list divided by its length.
    """
    total = 1
    for num in numbers:
        total *= num
    return total / len(numbers)

# Test cases
print(multiply_and_divide([2, 3, 4]))  # Expected output: 0.6666666666666666
print(multiply_and_divide([-5, -2, -3, -4]))  # Expected output: 0.75` | **FAIL** | 165 | 3390.93 | ```python def multiply_and_divide(numbers):     """     Mult... |
| 3 | `code_val_0039` | public | `def find_Parity(x): 
    y = x ^ (x >> 1); 
    y = y ^ (y >> 2); 
    y = y ^ (y >> 4); 
    y = y ^ (y >> 8); 
    y = y ^ (y >> 16); 
    if (y & 1): 
        return ("Odd Parity"); 
    return ("Even Parity"); ` | `def find_parity(number):
    """
    This function takes an integer as input and returns 1 if the number is odd,
    otherwise it returns -1.
    
    Parameters:
    number (int): The integer to check for parity.
    
    Returns:
    int: 1 if the number is odd, -1 if the number is even.
    """
    return 1 if number % 2 != 0 else -1

# Example usage:
print(find_parity(7))  # Output: 1
print(find_parity(15)) # Output: -1` | **FAIL** | 127 | 2603.5 | ```python def find_parity(number):     """     This function... |
| 4 | `code_val_0051` | synthetic | `    return sum(1 for x in nums if x % 8 == 0)
` | `from typing import List

def count_divisible_by_8_001(nums: List[int]) -> int:
    return sum(1 for num in nums if num % 8 == 0)` | **PASS** | 47 | 966.04 | ```python from typing import List  def count_divisible_by_8_... |
| 5 | `code_val_0095` | synthetic | `    if not nums:
        return []
    if len(nums) < 3:
        return [max(nums)]
    res = []
    for i in range(len(nums) - 3 + 1):
        res.append(max(nums[i : i + 3]))
    return res
` | `from typing import List

class Solution:
    def sliding_window_max(self, nums: List[int]) -> List[int]:
        max_elements = []
        for i in range(len(nums)):
            # Remove elements from the start that are smaller than the current element
            while nums[i:i+3] and nums[i:i+3][-1] <= nums[i]:
                nums[i] = nums[i+3]
            max_elements.append(nums[i])
        return max_elements` | **FAIL** | 100 | 2092.92 | ```python from typing import List  class Solution:     def s... |
| 6 | `code_val_0034` | public | `def floor_Max(A,B,N):
    x = min(B - 1,N)
    return (A*x) // B` | `import numpy as np

def max_periodic_value(func):
    """
    Finds the maximum value of a given periodic function.

    Parameters:
    func (callable): A callable representing a periodic function.
                     It should take a single argument and return a float.

    Returns:
    float: The maximum value of the function.
    """

    # Generate a range of values within the period of the function
    values = np.linspace(0, 2 * np.pi, 1000)
    
    # Compute the function at each value in the range
    results = [func(value) for value in values]
    
    # Find the maximum value among all computed results
    max_result = max(results)
    
    return max_result

# Example usage:
periodic_function = lambda x: np.sin(x) + np.cos(x) / 2
print(max_periodic_value(periodic_function))  # Output will be approximately 1.5` | **FAIL** | 200 | 4246.29 | ```python import numpy as np  def max_periodic_value(func): ... |
| 7 | `code_val_0007` | public | `def largest_pos(list1): 
    max = list1[0] 
    for x in list1: 
        if x > max : 
             max = x  
    return max` | `def find_largest_positive(numbers):
    """
    Finds and returns the largest positive number in a given list of integers.

    Parameters:
    numbers (list): A list of integers.

    Returns:
    int: The largest positive integer in the list.
    """
    # Filter out non-positive numbers and return the maximum value
    return max(filter(lambda x: x > 0, numbers))

# Example usage:
numbers = [1, -2, 3, 4, -5]
largest_positive = find_largest_positive(numbers)
print(largest_positive)  # Output should be 4` | **FAIL** | 129 | 2652.61 | ```python def find_largest_positive(numbers):     """     Fi... |
| 8 | `code_val_0052` | synthetic | `    return [x for x in nums if x > 31]
` | `from typing import List

def filter_greater_than_31_002(nums: List[int]) -> List[int]:
    return [num for num in nums if num > 31]

# Test cases
print(filter_greater_than_31_002([29, 31, 36, 28, 43]))  # Output: [36, 43]
print(filter_greater_than_31_002([]))  # Output: []` | **PASS** | 110 | 2263.1 | ```python from typing import List  def filter_greater_than_3... |
| 9 | `code_val_0072` | synthetic | `    used = {}
    max_len = 0
    start = 0
    for idx, char in enumerate(s):
        if char in used and start <= used[char]:
            start = used[char] + 1
        else:
            max_len = max(max_len, idx - start + 1)
        used[char] = idx
    return max_len
` | `from collections import defaultdict

def longest_unique_substring_022(s: str) -> int:
    """
    Return the length of the longest substring without repeating characters.
    
    :param s: Input string
    :return: Length of the longest substring without repeating characters
    """
    char_index_map = defaultdict(int)
    max_length = start = 0
    
    for i, char in enumerate(s):
        if char in char_index_map and char_index_map[char] >= start:
            start = char_index_map[char] + 1
        else:
            max_length = max(max_length, i - start + 1)
        
        char_index_map[char] = i
    
    return max_length` | **PASS** | 151 | 3155.38 | ```python from collections import defaultdict  def longest_u... |
| 10 | `code_val_0062` | synthetic | `    from collections import Counter
    if not items:
        return []
    counts = Counter(items)
    first_seen = {}
    for idx, x in enumerate(items):
        if x not in first_seen:
            first_seen[x] = idx
    unique_items = sorted(counts.keys(), key=lambda x: (-counts[x], first_seen[x]))
    return unique_items[:2]
` | `from collections import Counter

def top_k_frequent_2_012(items: list[int]) -> list[int]:
    # Count the frequency of each item
    freq_count = Counter(items)
    
    # Sort the items by their frequency and then by their value if frequencies are equal
    sorted_items = sorted(freq_count.items(), key=lambda x: (x[1], x[0]))
    
    return [item for item, count in sorted_items[:2]]` | **FAIL** | 102 | 2072.64 | ```python from collections import Counter  def top_k_frequen... |
| 11 | `code_val_0042` | public | `def check_Equality(s): 
    return (ord(s[0]) == ord(s[len(s) - 1])); 
def count_Substring_With_Equal_Ends(s): 
    result = 0; 
    n = len(s); 
    for i in range(n):
        for j in range(1,n-i+1): 
            if (check_Equality(s[i:i+j])): 
                result+=1; 
    return result; ` | `def count_substrings_with_same_first_last_char(s):
    """
    Counts the number of substrings in 's' that have the same first and last character.

    Parameters:
    s (str): The input string.

    Returns:
    int: The total count of such substrings.
    """
    if not s or len(s) < 2:
        return 0

    count = 1  # Base case: single-character strings are considered valid
    for i in range(1, len(s)):
        if s[i] == s[0]:
            count += 1
        else:
            count = 1

    return count

# Check function with provided data points
print(count_substrings_with_same_first_last_char("abcab"))  # Expected output: 7
print(count_substrings_with_same_first_last_char("aaa"))   # Expected output: 6
print(count_substrings_with_same_first_last_char("abcd"))  # Expected output: 5` | **FAIL** | 209 | 4305.59 | ```python def count_substrings_with_same_first_last_char(s):... |
| 12 | `code_val_0098` | synthetic | `    if not s:
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
` | `from collections import Counter

def compress_run_length_048(s: str) -> str:
    if not s:
        return ""

    # Count the frequency of each character in the string
    char_count = Counter(s)
    
    compressed_string = ""
    prev_char = None
    
    for char, freq in char_count.items():
        if prev_char is not None and prev_char != char:
            compressed_string += f"{freq}{prev_char}"  # Append the frequency followed by the previous character
        else:
            compressed_string += char  # Append the current character without any prefix
        
        prev_char = char
    
    return compressed_string` | **FAIL** | 138 | 2931.42 | ```python from collections import Counter  def compress_run_... |
| 13 | `code_val_0048` | public | `def tuple_to_float(test_tup):
  res = float('.'.join(str(ele) for ele in test_tup))
  return (res) ` | `def float_from_tuple(tup):
    """
    Convert a tuple into a floating-point number.

    Parameters:
    tup (tuple): The input tuple containing numeric values.

    Returns:
    float: The converted floating-point number.
    """
    return sum(tup) / len(tup)

# Example usage:
result = float_from_tuple((10, 20, 30))
print(result)  # Output: 20.0

result = float_from_tuple((5,))
print(result)  # Output: 5.0

result = float_from_tuple((10.5, 20.75, 30.25))
print(result)  # Output: 20.5` | **FAIL** | 156 | 3187.03 | ```python def float_from_tuple(tup):     """     Convert a t... |
| 14 | `code_val_0032` | public | `def dig_let(s):
 d=l=0
 for c in s:
    if c.isdigit():
        d=d+1
    elif c.isalpha():
        l=l+1
    else:
        pass
 return (l,d)` | `def count_digits_letters(s):
    """
    Counts the number of digits and letters in a given string.

    Parameters:
    s (str): The input string.

    Returns:
    tuple: A tuple containing two elements - the count of digits and the count of letters.
    """
    digit_count = sum(1 for char in s if char.isdigit())
    letter_count = sum(1 for char in s if not char.isalnum())
    return digit_count, letter_count

# Test cases
print(count_digits_letters("Hello World!"))  # Output: (0, 8)
print(count_digits_letters("2023 is the year of the coronavirus."))  # Output: (4, 7)` | **FAIL** | 152 | 3173.69 | ```python def count_digits_letters(s):     """     Counts th... |
| 15 | `code_val_0093` | synthetic | `    return sum(1 for x in nums if x % 7 == 0)
` | `from typing import List

def count_divisible_by_7_043(nums: List[int]) -> int:
    return sum(1 for num in nums if num % 7 == 0)` | **PASS** | 47 | 967.68 | ```python from typing import List  def count_divisible_by_7_... |
| 16 | `code_val_0087` | synthetic | `    if not nums:
        return []
    shift = 5 % len(nums)
    if shift == 0:
        return list(nums)
    return nums[-shift:] + nums[:-shift]
` | `from typing import List

def cyclic_shift_right_5_037(nums: List[int]) -> List[int]:
    if len(nums) <= 1:
        return nums
    
    # Perform cyclic shift to the right by 5 positions
    shifted = nums[-5:] + nums[:-5]
    
    return shifted` | **PASS** | 72 | 1485.17 | ```python from typing import List  def cyclic_shift_right_5_... |
| 17 | `code_val_0094` | synthetic | `    return sum(1 for x in nums if x % 2 == 0)
` | `from typing import List

def count_divisible_by_2_044(nums: List[int]) -> int:
    return sum(1 for num in nums if num % 2 == 0)` | **PASS** | 47 | 976.56 | ```python from typing import List  def count_divisible_by_2_... |
| 18 | `code_val_0038` | public | `def Find_Min(lst): 
    minList = min((x) for x in lst) 
    return minList` | `def min_length_sublist(lst):
    """
    Finds the sublist with the minimum length from a given list of lists.

    Parameters:
    lst (List[List[int]]): A list of lists where each sublist contains integers.

    Returns:
    List[int]: The sublist with the minimum length.
    """
    # Sort the list of lists based on the lengths in descending order
    sorted_lst = sorted(lst, key=len, reverse=True)
    
    # Find the first sublist that has the smallest length
    for i in range(len(sorted_lst)):
        if len(sorted_lst[i]) == min([len(sublst) for sublst in sorted_lst]):
            return sorted_lst[i]

# Example usage
if __name__ == "__main__":
    example_list = [[1, 2], [3, 4, 5], [6]]
    print(min_length_sublist(example_list))  # Output: [3, 4, 5]` | **FAIL** | 199 | 4271.37 | ```python def min_length_sublist(lst):     """     Finds the... |
| 19 | `code_val_0073` | synthetic | `    if not s:
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
` | `from collections import Counter

def compress_run_length_023(s: str) -> str:
    if not s:
        return ""

    # Count the frequency of each character in the string
    char_count = Counter(s)
    
    compressed_string = ""
    prev_char = None
    
    for char, freq in char_count.items():
        if prev_char is not None and prev_char != char:
            compressed_string += f"{freq}{prev_char}"  # Append the frequency followed by the previous character
        else:
            compressed_string += char  # Append the current character without any prefix
        
        prev_char = char
    
    return compressed_string` | **FAIL** | 138 | 2829.5 | ```python from collections import Counter  def compress_run_... |
| 20 | `code_val_0075` | synthetic | `    if not matrix or not matrix[0]:
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
` | `from typing import List

def spiral_order_025(matrix: List[List[int]]) -> List[int]:
    """
    Return all elements of matrix in clockwise spiral order.
    
    :param matrix: A 2D list representing a square matrix.
    :return: A list containing the elements of the matrix in clockwise spiral order.
    """
    if not matrix or not matrix[0]:
        return []
    
    rows, cols = len(matrix), len(matrix[0])
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    
    result = []
    while top <= bottom and left <= right:
        # Traverse the top row from left to right
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1
        
        # Traverse the right column from top to bottom
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1
        
        # If there's space on the left, traverse it
        if top <= bottom:
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1
        
        # If there's space on the right, traverse it
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1
            
    return result` | **PASS** | 316 | 6526.54 | ```python from typing import List  def spiral_order_025(matr... |

### Group: `knowledge_qa` (12/20 correct — 60.0%)

| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `kqa_val_0223` | fictional_entity | `physician` | `Doctor` | **FAIL** | 2 | 78.49 | Doctor |
| 2 | `kqa_val_0051` | real_wikipedia | `9 April 1626` | `9 April 1626` | **PASS** | 15 | 370.65 | Francis Bacon died on 9 April 1626. |
| 3 | `kqa_val_0297` | fictional_entity | `10 April 1856` | `10 April 1856` | **PASS** | 18 | 421.25 | Leopold Frost was born on 10 April 1856. |
| 4 | `kqa_val_0258` | fictional_entity | `28 June 1913` | `28 June 1913` | **PASS** | 18 | 400.14 | Percival Thornwood died on 28 June 1913. |
| 5 | `kqa_val_0035` | real_wikipedia | `mathematician` | `mathematician and electrical engineer` | **FAIL** | 7 | 202.68 | mathematician and electrical engineer |
| 6 | `kqa_val_0026` | real_wikipedia | `October 17, 1915` | `October 17, 1915` | **PASS** | 17 | 404.16 | Arthur Miller was born on October 17, 1915. |
| 7 | `kqa_val_0184` | real_wikipedia | `painter` | `Painter` | **PASS** | 2 | 109.66 | Painter |
| 8 | `kqa_val_0127` | real_wikipedia | `general` | `The profession or occupation of Charles C. Krulak is a retired United States Marine Corps four-star general who served as the 31st Commandant of the Marine Corps from July 1, 1995, to June 30, 1999` | **FAIL** | 59 | 1277.46 | The profession or occupation of Charles C. Krulak is a retir... |
| 9 | `kqa_val_0243` | fictional_entity | `philosopher` | `Philosopher` | **PASS** | 3 | 82.75 | Philosopher |
| 10 | `kqa_val_0216` | fictional_entity | `Spectrum Society Award` | `Fiona Bramblewood received the Spectrum Society Award` | **FAIL** | 12 | 272.39 | Fiona Bramblewood received the Spectrum Society Award. |
| 11 | `kqa_val_0027` | real_wikipedia | `569,353` | `569,353 as of the 2021 Canadian census` | **FAIL** | 35 | 756.08 | The reported population of Hamilton, Ontario, according to t... |
| 12 | `kqa_val_0168` | real_wikipedia | `actress` | `that of an American singer-songwriter, actress, philanthropist, and businesswoman` | **FAIL** | 29 | 660.63 | The profession or occupation of Dolly Parton was that of an ... |
| 13 | `kqa_val_0039` | real_wikipedia | `10 August 1915` | `10 August 1915` | **PASS** | 17 | 410.43 | Henry Moseley died on 10 August 1915. |
| 14 | `kqa_val_0066` | real_wikipedia | `writer` | `Economist` | **FAIL** | 4 | 137.47 | Economist |
| 15 | `kqa_val_0073` | real_wikipedia | `November 20, 1889` | `November 20, 1889` | **PASS** | 19 | 441.36 | Edwin Hubble was born on November 20, 1889. |
| 16 | `kqa_val_0108` | real_wikipedia | `486,492` | `Gdańsk had a reported population of 486, 492 people` | **PASS** | 20 | 476.19 | Gdańsk had a reported population of 486, 492 people. |
| 17 | `kqa_val_0015` | real_wikipedia | `November 7, 1964` | `November 7, 1964` | **PASS** | 10 | 265.36 | November 7, 1964 |
| 18 | `kqa_val_0072` | real_wikipedia | `August 14, 1961` | `August 14, 1961` | **PASS** | 11 | 296.78 | August 14, 1961 |
| 19 | `kqa_val_0292` | fictional_entity | `Foundry Guild Trophy` | `the Foundry Guild Trophy` | **PASS** | 17 | 400.52 | The award or prize that Arthur Ravenscroft received was the ... |
| 20 | `kqa_val_0296` | fictional_entity | `Canvas Master Distinction` | `Cassandra Cross received the Canvas Master Distinction from the Canvas Masters Award` | **FAIL** | 16 | 370.72 | Cassandra Cross received the Canvas Master Distinction from ... |

### Group: `memory_probe` (15/20 correct — 75.0%)

| # | Item ID | Arm | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output Preview |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `mem_val_0104` | synthetic | `Gateron Oil King linear switches` | `The exact value provided in the log is "Gateron Oil King linear switches".` | **PASS** | 18 | 379.81 | The exact value provided in the log is "Gateron Oil King lin... |
| 2 | `mem_val_0094` | synthetic | `Backblaze B2` | `My primary active cloud storage backup service is Backblaze B2.` | **PASS** | 15 | 319.23 | My primary active cloud storage backup service is Backblaze ... |
| 3 | `mem_val_0041` | synthetic | `Cedar Creek Vet Clinic` | `Cedar Creek Vet Clinic` | **PASS** | 6 | 127.52 | Cedar Creek Vet Clinic |
| 4 | `mem_val_0014` | synthetic | `Dropbox Professional` | `My primary active cloud storage backup service is Dropbox Professional.` | **PASS** | 12 | 252.26 | My primary active cloud storage backup service is Dropbox Pr... |
| 5 | `mem_val_0038` | synthetic | `Upper-Lower 4-day split` | `Based on the provided personal history log entries, you are currently following the Upper-Lower 4-day split training routine.` | **PASS** | 25 | 521.7 | Based on the provided personal history log entries, you are ... |
| 6 | `mem_val_0073` | synthetic | `Cedar Creek Vet Clinic` | `Cedar Creek Vet Clinic` | **PASS** | 6 | 130.15 | Cedar Creek Vet Clinic |
| 7 | `mem_val_0029` | synthetic | `Uplift V2` | `The brand of standing desk you currently use in your home office is the Uplift V2.` | **PASS** | 21 | 437.1 | The brand of standing desk you currently use in your home of... |
| 8 | `mem_val_0049` | synthetic | `Chicago` | `Your current city of residence is Chicago.` | **PASS** | 9 | 189.97 | Your current city of residence is Chicago. |
| 9 | `mem_val_0099` | synthetic | `2018 Honda Civic` | `As of the last update in the personal history log provided, you currently drive your 2021 Tesla Model 3 as your daily driver.` | **FAIL** | 31 | 646.19 | As of the last update in the personal history log provided, ... |
| 10 | `mem_val_0069` | synthetic | `Pixel 7 Pro` | `Based on the provided personal history log entries, you currently use the OnePlus 12 as your primary phone.` | **FAIL** | 23 | 477.82 | Based on the provided personal history log entries, you curr... |
| 11 | `mem_val_0061` | synthetic | `Vari Electric Desk` | `The brand of standing desk you currently use in your home office is the Vari Electric Desk.` | **PASS** | 19 | 397.06 | The brand of standing desk you currently use in your home of... |
| 12 | `mem_val_0093` | synthetic | `Uplift V2` | `The brand of standing desk you currently use in your home office is the Uplift V2.` | **PASS** | 21 | 445.12 | The brand of standing desk you currently use in your home of... |
| 13 | `mem_val_0125` | synthetic | `4821#` | `The gate code for your apartment complex is 4821#.` | **PASS** | 15 | 313.95 | The gate code for your apartment complex is 4821#. |
| 14 | `mem_val_0111` | synthetic | `US Mens 10.5` | `The exact value provided in the log is 10.5.` | **FAIL** | 15 | 325.79 | The exact value provided in the log is 10.5. |
| 15 | `mem_val_0081` | synthetic | `Minneapolis` | `Your current city of residence is Minneapolis.` | **PASS** | 9 | 193.98 | Your current city of residence is Minneapolis. |
| 16 | `mem_val_0100` | synthetic | `Colombian Supremo medium roast` | `Based on the personal history log provided, your current favorite coffee roast for your morning brew is Colombian Supremo medium roast.` | **PASS** | 26 | 554.86 | Based on the personal history log provided, your current fav... |
| 17 | `mem_val_0076` | synthetic | `Cigna Open Access` | `Based on the provided personal history log entries, your current primary health insurance provider is Blue Cross Blue Shield.` | **FAIL** | 22 | 467.49 | Based on the provided personal history log entries, your cur... |
| 18 | `mem_val_0027` | synthetic | `555-0321` | `The listed emergency contact phone number is 555-0214.` | **FAIL** | 18 | 393.19 | The listed emergency contact phone number is 555-0214. |
| 19 | `mem_val_0123` | synthetic | `SK-908214` | `The exact value from the log is SK-908214.` | **PASS** | 17 | 393.82 | The exact value from the log is SK-908214. |
| 20 | `mem_val_0085` | synthetic | `Samsung Galaxy S24 Ultra` | `As of the last update, you currently use the Samsung Galaxy S24 Ultra as your primary phone.` | **PASS** | 22 | 489.84 | As of the last update, you currently use the Samsung Galaxy ... |
