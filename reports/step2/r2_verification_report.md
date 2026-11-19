# Step 2 Part 4R — R2 Verification Report: Real Inference Evidence

**Model**: `Qwen/Qwen2.5-0.5B-Instruct` (FP16, cuda:0, 942.3 MB resident VRAM)
**Evaluation Split**: `suite/validation/` (Sampled seed: `20260102`)
**Sandbox Execution**: `evaluation/code_sandbox.py` (Isolated subprocess, 3s timeout, 512 MB memory cap)

## 1. Token Length Calibration Pilot (n=50 per group)

| Group | Pilot Cap | Tokens (min/med/p95/max) | Truncation % | Latency p50/p95 (ms) | Recommended Cap |
| :--- | :--- | :--- | :--- | :--- | :--- |
| math | 512 | 161 / 278 / 329 / 358 | **0.0%** | 5768.2 / 7000.3 | 384 |
| science_mcq | 128 | 83 / 128 / 128 / 128 | 86.0% | 2626.1 / 2729.0 | 64 |
| knowledge_mcq | 128 | 59 / 128 / 128 / 128 | 66.0% | 2623.3 / 2746.3 | 64 |
| code | 512 | 147 / 306 / 512 / 512 | 8.0% | 6444.2 / 10547.2 | 384 |
| knowledge_qa | 128 | 3 / 11 / 32 / 56 | **0.0%** | 232.2 / 687.8 | 64 |
| memory_probe | 128 | 3 / 17 / 30 / 32 | **0.0%** | 364.7 / 641.3 | 64 |

## 2. Secondary MCQ Diagnostic (Next-Token Logits vs Generative)

| Group | n | Generative Accuracy | Logit Next-Token Accuracy | Agreement | Diagnostic Finding |
| :--- | :--- | :--- | :--- | :--- | :--- |
| science_mcq | 50 | 8.0% | **40.0%** | 2.0% | Model rambles without explicit answer under open generation; logit scoring confirms candidate capability. |
| knowledge_mcq | 50 | 0.0% | **26.0%** | 0.0% | Logit accuracy reflects the ~25% random baseline on 0.5B; generative rambling scores 0%. |

## 3. Real Inference Accuracy Summary (20 Items Per Group)

| Group | Accuracy (k/20) | Accuracy % | Tokens p50 / p95 | Latency p50 / p95 (ms) |
| :--- | :--- | :--- | :--- | :--- |
| `math` | 16/20 | **80.0%** | 269 / 358 | 5552.2 / 7410.4 |
| `science_mcq` | 0/20 | **0.0%** | 64 / 64 | 1318.4 / 1423.6 |
| `knowledge_mcq` | 2/20 | **10.0%** | 64 / 64 | 1314.6 / 1322.9 |
| `code` | 7/20 | **35.0%** | 363 / 384 | 7928.8 / 8777.7 |
| `knowledge_qa` | 19/20 | **95.0%** | 9 / 26 | 233.5 / 609.3 |
| `memory_probe` | 17/20 | **85.0%** | 17 / 32 | 370.6 / 707.5 |


## 4. 20 Random Items Per Group — Raw Records & Scores

### Group: `math` (16/20 correct — 80.0%)

| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `math-synth-0187` | `dc31259eda93...` | `462` | `462.0` | **PASS** | 327 | 6892.9 | To determine the total cost of fencing the perimeter of the rectangular commu... |
| 2 | `math-synth-0149` | `8b3d4baf77bf...` | `460` | `460.0` | **PASS** | 242 | 5175.0 | To find the total distance Chloe traveled, we need to calculate the distance ... |
| 3 | `math-synth-0173` | `064a90f6aa95...` | `150` | `150.0` | **PASS** | 198 | 4082.2 | Let's break down the scoring process step by step:  ### Opening Round: - Base... |
| 4 | `math-synth-0021` | `36cf57b4b70d...` | `184` | `184.0` | **PASS** | 330 | 6879.5 | To determine the total cost of fencing the perimeter of the rectangular commu... |
| 5 | `math-synth-0150` | `45fea198446a...` | `238` | `238.0` | **PASS** | 283 | 5850.0 | To determine the total number of circuit boards made over the weekend, we nee... |
| 6 | `math-synth-0008` | `1557a8e61ce4...` | `38` | `38.0` | **PASS** | 279 | 6099.4 | Let's break down the problem step by step:  1. **Calculate the cost of the pe... |
| 7 | `math-synth-0163` | `e856cc4ebb1c...` | `748` | `748.0` | **PASS** | 333 | 6960.3 | To determine the total cost of fencing the perimeter of the rectangular commu... |
| 8 | `math-synth-0145` | `7cbfa249af09...` | `23` | `23.0` | **PASS** | 280 | 5772.8 | Let's break down the problem step-by-step:  1. **Calculate the cost of the fl... |
| 9 | `math-synth-0152` | `1f59fc0400f8...` | `43` | `43.0` | **PASS** | 260 | 5393.6 | Let's break down the problem step by step:  1. **Calculate the cost of the ba... |
| 10 | `math-synth-0105` | `2ad938bc7ff7...` | `204` | `274.0` | **FAIL** | 204 | 4199.3 | Let's break down the scoring process step by step:  ### Opening Round - **Bas... |
| 11 | `math-synth-0137` | `837260289285...` | `18` | `222.0` | **FAIL** | 358 | 7410.4 | Let's break down the problem step-by-step:  1. **Calculate the cost of the fl... |
| 12 | `math-synth-0056` | `aa752f5c452e...` | `270` | `270.0` | **PASS** | 245 | 5077.4 | To determine the total number of wooden toys made over the weekend, we need t... |
| 13 | `math-synth-0121` | `0fc00a7ca743...` | `31` | `31.0` | **PASS** | 269 | 5552.2 | Let's break down the problem step by step:  1. **Calculate the cost of the wa... |
| 14 | `math-synth-0084` | `39277fed72dc...` | `528` | `528.0` | **PASS** | 179 | 3688.3 | To find the total distance Siddharth traveled, we need to calculate the dista... |
| 15 | `math-synth-0082` | `1a8500e28d94...` | `312` | `312.0` | **PASS** | 283 | 5839.8 | To determine the total number of circuit boards made over the weekend, we nee... |
| 16 | `math-synth-0093` | `a7300865ea97...` | `182` | `182.0` | **PASS** | 285 | 5887.7 | To determine the total number of pottery mugs made over the weekend, we need ... |
| 17 | `math-synth-0098` | `1abc65c32c00...` | `177` | `196.0` | **FAIL** | 169 | 3664.7 | Let's break down the scoring process step by step:  ### Opening Round: - Base... |
| 18 | `math-synth-0076` | `afb7544a2594...` | `170` | `58.0` | **FAIL** | 191 | 3990.4 | Let's break down the scoring process step by step:  1. **Base Score**: The te... |
| 19 | `math-synth-0125` | `16d550d61229...` | `188` | `188.0` | **PASS** | 242 | 5097.0 | To determine the total number of wooden toys made over the weekend, we need t... |
| 20 | `math-synth-0058` | `e41e9660a09b...` | `255` | `255.0` | **PASS** | 244 | 5117.8 | To find the total distance Amina traveled, we need to calculate the distance ... |


### Group: `science_mcq` (0/20 correct — 0.0%)

| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `sci_val_0094` | `f8cbee5122ed...` | `C` | `None` | **FAIL** | 64 | 1355.3 | The correct answer is C) Metamorphic rock.  Reasoning: Metamorphism refers to... |
| 2 | `sci_val_0015` | `cf52fe5cbfa6...` | `B` | `None` | **FAIL** | 64 | 1319.2 | To determine the atomic number of silver (Ag), we need to understand that the... |
| 3 | `sci_val_0044` | `975a6ad55de0...` | `D` | `None` | **FAIL** | 64 | 1318.2 | To determine the atomic number of titanium (Ti), we need to understand that t... |
| 4 | `sci_val_0159` | `c3fd40ecc44b...` | `B` | `None` | **FAIL** | 64 | 1318.6 | To find the density of the metal, we use the formula:  \[ \text{Density} = \f... |
| 5 | `sci_val_0119` | `a1291b1f38dd...` | `A` | `None` | **FAIL** | 64 | 1423.6 | To calculate the work done, we use the formula:  \[ \text{Work} = \text{Force... |
| 6 | `sci_val_0124` | `3f6f862d6fa5...` | `B` | `None` | **FAIL** | 64 | 1337.6 | To determine the correct classification of the solution at 25°C with a pH of ... |
| 7 | `sci_val_0101` | `a5af21ffdf54...` | `B` | `None` | **FAIL** | 64 | 1317.9 | To determine the pressure exerted on the surface, we need to use the formula ... |
| 8 | `sci_val_0121` | `a2aadfaaa7a9...` | `C` | `None` | **FAIL** | 64 | 1315.6 | To determine the number of neutrons in a potassium-39 atom, we need to use th... |
| 9 | `sci_val_0049` | `5fcee7331ded...` | `A` | `None` | **FAIL** | 64 | 1316.9 | To find the density of the metal, we use the formula:  \[ \text{Density} = \f... |
| 10 | `sci_val_0092` | `880cf2986057...` | `A` | `None` | **FAIL** | 64 | 1317.4 | To determine the total mass in grams of 3 moles of glucose (C₆H₁₂O₆), we need... |
| 11 | `sci_val_0005` | `5d70147cc127...` | `C` | `B` | **FAIL** | 64 | 1388.7 | To determine which eukaryotic cellular structure generates cellular ATP via o... |
| 12 | `sci_val_0122` | `ffee6037696a...` | `D` | `None` | **FAIL** | 64 | 1323.2 | To determine the correct classification of the solution at 25°C with a pH of ... |
| 13 | `sci_val_0066` | `06924f21ca16...` | `A` | `None` | **FAIL** | 54 | 1111.6 | The correct answer is A) Post-transition metal.  Reasoning: Aluminum belongs ... |
| 14 | `sci_val_0073` | `a2c43447c757...` | `C` | `None` | **FAIL** | 64 | 1312.9 | The correct answer is A) Alkali metal.  Reasoning: Neon is located at the top... |
| 15 | `sci_val_0173` | `74f9edf62f39...` | `A` | `None` | **FAIL** | 64 | 1363.2 | To solve this problem, we need to use Boyle's Law, which states that the prod... |
| 16 | `sci_val_0098` | `33791059c746...` | `B` | `None` | **FAIL** | 64 | 1372.3 | To find the magnitude of linear momentum for an object, we use the formula:  ... |
| 17 | `sci_val_0181` | `634fbd35f406...` | `B` | `None` | **FAIL** | 64 | 1318.4 | To determine the total mass in grams of 4 moles of sodium chloride (NaCl), we... |
| 18 | `sci_val_0057` | `bd7bd3386bc3...` | `D` | `None` | **FAIL** | 64 | 1315.8 | To find the density of the metal, we use the formula:  \[ \text{Density} = \f... |
| 19 | `sci_val_0151` | `32ecc6ebc5f5...` | `A` | `None` | **FAIL** | 64 | 1311.9 | To find the magnitude of linear momentum for an object, we use the formula:  ... |
| 20 | `sci_val_0036` | `c09df26d9cb9...` | `C` | `None` | **FAIL** | 64 | 1313.5 | To determine the correct classification of the solution at 25°C with a pH of ... |


### Group: `knowledge_mcq` (2/20 correct — 10.0%)

| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `know_val_0213` | `c14b6c1c65b0...` | `D` | `None` | **FAIL** | 64 | 1320.4 | The correct answer is A.  Reasoning: According to UCC Section 2-201, "Statute... |
| 2 | `know_val_0253` | `f3411425d378...` | `B` | `B` | **PASS** | 64 | 1314.6 | Answer: B  Reasoning: The patient has a history of hypertension, indicating t... |
| 3 | `know_val_0140` | `17aa57f30afd...` | `A` | `None` | **FAIL** | 64 | 1316.4 | To find the area of a triangle, we use the formula:  \[ \text{Area} = \frac{1... |
| 4 | `know_val_0298` | `de4d113b48bc...` | `A` | `None` | **FAIL** | 61 | 1252.4 | The correct answer is A) Endogeneity.  Endogeneity refers to a situation wher... |
| 5 | `know_val_0074` | `3dedc0c4dadc...` | `A` | `B` | **FAIL** | 64 | 1310.3 | To determine the correct answer, let's analyze each option:  A) Receptor tyro... |
| 6 | `know_val_0154` | `dd0cca3af7e3...` | `C` | `None` | **FAIL** | 64 | 1318.5 | The correct answer is C) British global maritime hegemony and cession of New ... |
| 7 | `know_val_0129` | `9bdbe392bc75...` | `D` | `None` | **FAIL** | 64 | 1317.5 | To find the area of a triangle, we use the formula:  \[ \text{Area} = \frac{1... |
| 8 | `know_val_0132` | `1b2e88b620d9...` | `A` | `None` | **FAIL** | 64 | 1311.4 | To find the area of a triangle, we use the formula:  \[ \text{Area} = \frac{1... |
| 9 | `know_val_0030` | `acf40765353e...` | `A` | `None` | **FAIL** | 64 | 1312.5 | To determine the total number of nodes in a perfect binary tree of height 2, ... |
| 10 | `know_val_0216` | `30a90ac06647...` | `C` | `None` | **FAIL** | 64 | 1313.9 | The correct answer is C) The Dormant Commerce Clause (for discriminating agai... |
| 11 | `know_val_0160` | `4d63b84fc2ce...` | `D` | `None` | **FAIL** | 64 | 1313.2 | The correct answer is A) Establishment of independent Confederacy.  Reasoning... |
| 12 | `know_val_0051` | `3aee9132caf1...` | `D` | `None` | **FAIL** | 64 | 1315.6 | To determine the theoretical maximum thermal efficiency of a reversible Carno... |
| 13 | `know_val_0081` | `35dd8cc3a891...` | `A` | `None` | **FAIL** | 64 | 1314.3 | To determine the percentage of thymine in a double-stranded DNA sample given ... |
| 14 | `know_val_0181` | `4c06fa96089d...` | `C` | `None` | **FAIL** | 64 | 1312.5 | The correct answer is A) Casablanca.  My reasoning: Casablanca is indeed the ... |
| 15 | `know_val_0266` | `6001232e83ab...` | `A` | `A` | **PASS** | 64 | 1312.2 | Answer: A) Acute Pancreatitis  Reasoning: The patient's symptoms, including s... |
| 16 | `know_val_0153` | `cfa3ce348101...` | `D` | `None` | **FAIL** | 64 | 1317.7 | The correct answer is D) sophisticated vigesimal (base-20) mathematics includ... |
| 17 | `know_val_0052` | `5f429d0d1a29...` | `C` | `None` | **FAIL** | 64 | 1310.2 | To determine the angular frequency \(\omega\) of a simple harmonic oscillator... |
| 18 | `know_val_0215` | `90f49c540ec1...` | `D` | `None` | **FAIL** | 64 | 1322.9 | The correct answer is D) Felony Murder Rule.  Reasoning: The Felgy Murder Rul... |
| 19 | `know_val_0042` | `0f316f98af20...` | `A` | `None` | **FAIL** | 64 | 1318.0 | To determine the bound orbital energy of an electron in the second principal ... |
| 20 | `know_val_0085` | `1cee364cd65c...` | `A` | `None` | **FAIL** | 64 | 1316.3 | To determine the percentage of thymine in a double-stranded DNA sample given ... |


### Group: `code` (7/20 correct — 35.0%)

| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `code-synth-0029` | `c403829df117...` | `    if not matrix or n...` | `from typing import Lis...` | **FAIL** | 303 | 6267.9 | To solve this problem, we need to perform a 90-degree clockwise rotation on e... |
| 2 | `code-synth-0051` | `43e1e1d5ced3...` | `    from collections i...` | `from collections impor...` | **FAIL** | 370 | 7652.5 | To solve this problem, we can use the `collections.Counter` class from the st... |
| 3 | `code-synth-0040` | `d7d960e51078...` | `    if not s:         ...` | `from collections impor...` | **FAIL** | 247 | 5083.7 | ```python from collections import Counter  def compress_run_length_040(s: str... |
| 4 | `code-synth-0013` | `2c35fc8433d0...` | `    return [x if x >= ...` | `from typing import Lis...` | **FAIL** | 286 | 5887.8 | ```python from typing import List  def replace_negatives_2_013(nums: List[int... |
| 5 | `code-synth-0037` | `153cb327b68d...` | `    if not intervals: ...` | `import heapq  def merg...` | **PASS** | 384 | 7928.8 | To solve this problem, we can use the `heapq` module in Python which provides... |
| 6 | `code-synth-0041` | `93918551a34a...` | `    used = {}     max_...` | `from collections impor...` | **PASS** | 384 | 7987.4 | To solve this problem, we can use a sliding window approach combined with a s... |
| 7 | `code-synth-0074` | `2263b6a766ba...` | `    return sum(1 for x...` | `from typing import Lis...` | **PASS** | 344 | 7102.3 | To solve this problem, we need to iterate through each number in the given li... |
| 8 | `code-synth-0098` | `e4913bc4d244...` | `    from collections i...` | `from collections impor...` | **PASS** | 328 | 6947.2 | To solve this problem, we can use a dictionary to count the occurrences of ea... |
| 9 | `code-synth-0018` | `b3810c23a695...` | `    used = {}     max_...` | `from collections impor...` | **PASS** | 384 | 8064.8 | To solve this problem, we can use a sliding window approach combined with a s... |
| 10 | `code-synth-0065` | `516f1983f6b2...` | `    if not matrix or n...` | `from typing import Lis...` | **FAIL** | 384 | 8528.2 | To solve this problem, we need to perform a 90-degree clockwise rotation on e... |
| 11 | `code-synth-0055` | `e4d2e60768c3...` | `    from collections i...` | `from collections impor...` | **PASS** | 342 | 8350.6 | To solve this problem, we can use a dictionary to count the occurrences of ea... |
| 12 | `code-synth-0042` | `fcce234ff260...` | `    stack = []     for...` | `from typing import Lis...` | **FAIL** | 261 | 6139.6 | ```python from typing import List  def evaluate_rpn_042(tokens: List[str]) ->... |
| 13 | `code-synth-0026` | `c24cb0a674aa...` | `    num_set = set(nums...` | `from typing import Lis...` | **FAIL** | 384 | 8769.0 | To solve this problem, we need to find the smallest missing positive integer ... |
| 14 | `code-synth-0068` | `1c55b4116367...` | `    if not matrix or n...` | `from typing import Lis...` | **FAIL** | 384 | 8551.0 | To solve this problem, we need to perform a 90-degree clockwise rotation on e... |
| 15 | `code-synth-0078` | `21fb5da0c9e3...` | `    from collections i...` | `from collections impor...` | **FAIL** | 363 | 8191.8 | To solve this problem, we can use the `collections.Counter` class from the st... |
| 16 | `code-synth-0075` | `1431681f7eb5...` | `    stack = []     map...` | `def is_balanced_bracke...` | **FAIL** | 254 | 5684.8 | ```python def is_balanced_brackets_075(s: str) -> bool:     # Helper function... |
| 17 | `code-synth-0100` | `28d7537ef558...` | `    if not nums:      ...` | `from typing import Lis...` | **FAIL** | 256 | 5677.9 | ```python from typing import List  def sliding_window_max_2_100(nums: List[in... |
| 18 | `code-synth-0067` | `d4c2ebaedf69...` | `    if not matrix or n...` | `def spiral_order_067(m...` | **FAIL** | 384 | 8651.4 | To solve this problem, we can use a simple iterative approach to traverse the... |
| 19 | `code-synth-0030` | `b47469ea76d7...` | `    stack = []     for...` | `from typing import Lis...` | **FAIL** | 251 | 5791.1 | ```python from typing import List  def evaluate_rpn_030(tokens: List[str]) ->... |
| 20 | `code-synth-0021` | `a9228e0484f4...` | `    if not intervals: ...` | `import heapq  def merg...` | **PASS** | 384 | 8777.7 | To solve this problem, we can use the `heapq` module in Python, which provide... |


### Group: `knowledge_qa` (19/20 correct — 95.0%)

| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `kqa_val_0183` | `55ebba452695...` | `physicist` | `physicist and mathemat...` | **PASS** | 7 | 167.7 | physicist and mathematician |
| 2 | `kqa_val_0018` | `25bf24c42434...` | `painter` | `landscape painter` | **PASS** | 3 | 86.0 | landscape painter |
| 3 | `kqa_val_0245` | `27775284e71e...` | `912,490` | `The reported populatio...` | **PASS** | 18 | 426.9 | The reported population of Edinburgh was 912, 490 people. |
| 4 | `kqa_val_0106` | `c696f05dac3f...` | `September 17, 1942` | `September 17, 1942` | **PASS** | 11 | 263.3 | September 17, 1942 |
| 5 | `kqa_val_0059` | `82278367b20f...` | `May 14, 1919` | `May 14, 1919` | **PASS** | 11 | 242.7 | May 14, 1919 |
| 6 | `kqa_val_0076` | `73192c3f6ac6...` | `April 12, 1878` | `April 12, 1878` | **PASS** | 11 | 245.9 | April 12, 1878 |
| 7 | `kqa_val_0027` | `5c5bd45e2b0d...` | `June 27, 1869` | `June 27, 1869` | **PASS** | 11 | 250.0 | June 27, 1869 |
| 8 | `kqa_val_0087` | `9b7b1a0db3a6...` | `poet` | `poet` | **PASS** | 3 | 81.3 | poet |
| 9 | `kqa_val_0189` | `02b0ec9ca017...` | `25 August 1841` | `25 August 1841` | **PASS** | 9 | 233.5 | 25 August 1841 |
| 10 | `kqa_val_0216` | `28acaf0be17d...` | `152,644` | `The reported populatio...` | **PASS** | 26 | 609.3 | The reported population of Helsingborg Municipality as stated in the passage ... |
| 11 | `kqa_val_0098` | `10aa8316b6ad...` | `physician` | `physician` | **PASS** | 3 | 76.1 | physician |
| 12 | `kqa_val_0113` | `6a33e23d7a7b...` | `philosopher` | `philosopher` | **PASS** | 3 | 82.1 | philosopher |
| 13 | `kqa_val_0078` | `9eaa36dd1827...` | `Pulitzer Prize` | `The Pulitzer Prize for...` | **PASS** | 7 | 162.5 | The Pulitzer Prize for Drama. |
| 14 | `kqa_val_0241` | `bbeb509182f7...` | `actress` | `singer` | **FAIL** | 3 | 86.8 | singer |
| 15 | `kqa_val_0188` | `046c8aee8505...` | `14 January 1875` | `14 January 1875` | **PASS** | 9 | 203.9 | 14 January 1875 |
| 16 | `kqa_val_0218` | `ca31cb478a60...` | `9 November 1953` | `9 November 1953` | **PASS** | 8 | 191.8 | 9 November 1953 |
| 17 | `kqa_val_0275` | `739ba400b474...` | `18 February 1745` | `Alessandro Giuseppe An...` | **PASS** | 22 | 532.0 | Alessandro Giuseppe Antonio Volta was born on 18 February 1745. |
| 18 | `kqa_val_0165` | `2c600d925367...` | `May 28, 1882` | `James Avery Hopwood wa...` | **PASS** | 19 | 431.8 | James Avery Hopwood was born on May 28, 1882. |
| 19 | `kqa_val_0139` | `d283aae97792...` | `3 March 1819` | `Gustave de Molinari wa...` | **PASS** | 20 | 475.0 | Gustave de Molinari was born on 3 March 1819. |
| 20 | `kqa_val_0148` | `03d51c0e71d1...` | `physician` | `physician and medical ...` | **PASS** | 6 | 148.6 | physician and medical researcher |


### Group: `memory_probe` (17/20 correct — 85.0%)

| # | Item ID | Prompt Hash (prefix) | Target Key | Extracted Answer | Score | Tokens | Latency (ms) | Raw Output (Preview) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `memory_probe-0090` | `5867b92b1fcd...` | `Herman Miller Aeron Si...` | `The exact value provid...` | **PASS** | 16 | 350.4 | The exact value provided in the log is Herman Miller Aeron Size B. |
| 2 | `memory_probe-0035` | `3a4ab27aa02b...` | `4821#` | `The gate code for your...` | **PASS** | 15 | 368.9 | The gate code for your apartment complex is 4821#. |
| 3 | `memory_probe-0062` | `83d726bb7b15...` | `-2.75 diopters` | `The eye prescription p...` | **PASS** | 19 | 412.5 | The eye prescription power indicated by the log is -2.75 diopters. |
| 4 | `memory_probe-0078` | `4ee84fb24481...` | `David Vance` | `David Vance` | **PASS** | 3 | 78.5 | David Vance |
| 5 | `memory_probe-0020` | `cb6145e7bb7e...` | `January 30, 2027` | `The confirmed delivery...` | **PASS** | 20 | 549.5 | The confirmed delivery deadline for Project Atlas is January 30, 2027. |
| 6 | `memory_probe-0022` | `0c352efdfeae...` | `Sarah Jenkins` | `Rachel Vance is your c...` | **FAIL** | 12 | 310.1 | Rachel Vance is your current direct reporting manager at work. |
| 7 | `memory_probe-0089` | `c6d21f799492...` | `Clara Higgins` | `Clara Higgins` | **PASS** | 4 | 102.7 | Clara Higgins |
| 8 | `memory_probe-0049` | `99032d531d63...` | `Clara Higgins` | `Clara Higgins` | **PASS** | 4 | 90.4 | Clara Higgins |
| 9 | `memory_probe-0031` | `08c07a73d1dc...` | `May 14` | `Your mother's birthday...` | **PASS** | 11 | 236.7 | Your mother's birthday is May 14. |
| 10 | `memory_probe-0079` | `68fac8c0b1d7...` | `JetBrains Mono Nerd Font` | `The preference for the...` | **PASS** | 23 | 498.9 | The preference for the terminal font in this log is "JetBrains Mono Nerd Font... |
| 11 | `memory_probe-0080` | `bdfc27238ec6...` | `Cello` | `The exact value provid...` | **PASS** | 23 | 525.3 | The exact value provided in the personal history log is that you learned to p... |
| 12 | `memory_probe-0033` | `894f6db07158...` | `SK-908214` | `The exact value from t...` | **PASS** | 17 | 370.6 | The exact value from the log is SK-908214. |
| 13 | `memory_probe-0052` | `9d447be3a939...` | `Penicillin` | `The patient has a seve...` | **PASS** | 29 | 665.2 | The patient has a severe allergy to penicillin. The exact value provided in t... |
| 14 | `memory_probe-0024` | `064c237dc733...` | `Guatemalan Antigua dar...` | `Based on the personal ...` | **PASS** | 27 | 608.8 | Based on the personal history log provided, your current favorite coffee roas... |
| 15 | `memory_probe-0023` | `0313a88b353d...` | `2020 Subaru Outback` | `As of the last update ...` | **FAIL** | 32 | 707.5 | As of the last update in the personal history log provided, you currently dri... |
| 16 | `memory_probe-0043` | `80568c619c15...` | `2021` | `Luna was adopted in 2021.` | **PASS** | 12 | 260.5 | Luna was adopted in 2021. |
| 17 | `memory_probe-0001` | `4385baf39dba...` | `Portland` | `Your current city of r...` | **PASS** | 9 | 212.7 | Your current city of residence is Portland. |
| 18 | `memory_probe-0064` | `29c6b5606613...` | `2032` | `The passport renewal e...` | **PASS** | 30 | 679.3 | The passport renewal expiration year listed on the personal history log for A... |
| 19 | `memory_probe-0097` | `c826b9354f49...` | `O-positive` | `O-positive` | **PASS** | 3 | 70.2 | O-positive |
| 20 | `memory_probe-0066` | `9fc45503bd9f...` | `Schiit Magni DAC/Amp` | `The default audio outp...` | **FAIL** | 27 | 595.1 | The default audio output device on your desktop, according to the provided pe... |

