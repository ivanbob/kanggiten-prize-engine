
# Technical Specification — Tournament Payout Optimization Engine

## 1. Project Objective

Build a **deterministic Tournament Payout Optimization Engine** that automatically designs, analyzes, and optimizes tournament prize/payout structures.

This is **not a simple prize calculator**.

The system should solve a constrained optimization problem:

> Given a tournament's prize pool, participant count, entry fee and desired payout philosophy, generate one or more mathematically valid, human-friendly payout structures that provide a strong balance between top-prize attractiveness, lower-tier rewards, simplicity, and adherence to configurable constraints.

The engine must also be able to:

1. analyze an existing payout structure;
2. identify structural problems;
3. optimize an existing payout structure;
4. adapt payout structures when the prize pool changes;
5. compare multiple payout strategies;
6. benchmark its results against simpler algorithms and real-world payout structures.

The initial objective is **algorithmic validation**, not building a complete SaaS product.

---

# 2. Background / Research Basis

The architecture is based on the two-stage approach described in research on tournament payout structures:

### Stage A — Ideal payout curve

Generate a mathematically ideal payout for every winning rank.

A strong initial model is the power-law curve:

[
\pi_i = E + \frac{P_1-E}{i^\alpha}
]

where:

* `i` = rank;
* `E` = minimum payout;
* `P1` = first-place payout;
* `α` = curve exponent.

`α` should be solved so that the ideal payouts exactly consume the prize pool.

The research demonstrates that power-law curves provide a useful approximation of real-world tournament payout structures and provide a good starting point for further optimization.

### Stage B — Constrained optimization

Transform the ideal curve into a practical payout structure using:

* payout buckets;
* nice numbers;
* minimum payout;
* exact prize pool reconciliation;
* monotonicity;
* bucket-size constraints;
* maximum number of payout tiers.

The research also demonstrates that heuristic optimization scales substantially better than exact integer programming for very large tournaments.  

Use this research as the conceptual foundation, but do not assume its exact objective function or parameter weights are universally optimal.

---

# 3. Core Product Concept

The engine should conceptually support four operations.

## Operation A — Generate

```text
Tournament parameters
        ↓
Generate optimal payout structures
```

Example:

```text
Prize pool:        €100,000
Entrants:          10,000
Entry fee:         €20
Paid places:       1,500
Style:             Balanced
Maximum tiers:     20
Minimum prize:     2 × entry fee
```

Output:

```text
1          €20,000
2          €12,000
3           €8,000
4–5         €5,000
6–10        €3,000
11–20       €1,500
...
```

---

# 4. Operation B — Analyze Existing Payout

Input an existing payout structure:

```text
1       €10,000
2        €5,000
3        €3,000
4        €1,500
5        €1,200
6–10       €500
11–20      €250
...
```

Return:

```text
Quality Score: 73/100

Issues:
- non-standard denomination at rank 5
- large discontinuity between ranks 5 and 6
- bucket progression is suboptimal
- structure deviates from target curve
- 3 buckets could potentially be simplified
```

This functionality is important because it creates a useful standalone product even before automatic generation is perfect.

---

# 5. Operation C — Optimize Existing Payout

Given an existing structure:

```text
Existing payout
        ↓
Analyze
        ↓
Optimize
        ↓
Improved payout
```

Example:

```text
Original score:      72
Optimized score:     94
Prize pool:          unchanged
Winner count:        unchanged
```

The engine should clearly show what changed and why.

---

# 6. Operation D — Recalibrate Dynamic Prize Pools

The engine must support applying the same payout philosophy to different prize pools.

Example:

```text
€50,000 pool
€100,000 pool
€250,000 pool
€500,000 pool
```

while preserving approximately:

* same payout style;
* same winner percentage;
* same minimum-prize policy;
* same number of tiers;
* same economic character.

This is important for tournament platforms where the final prize pool changes dynamically.

---

# 7. Architecture

Use a modular architecture.

```text
                    ┌─────────────────────┐
                    │ Tournament Input    │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Input Normalizer    │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Ideal Curve Engine  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Candidate Generator │
                    └──────────┬──────────┘
                               ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
        ┌─────────────────┐        ┌─────────────────┐
        │ Heuristic       │        │ Exact Optimizer │
        │ Optimizer       │        │                 │
        └────────┬────────┘        └────────┬────────┘
                 └─────────────┬─────────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Constraint Validator│
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Quality Engine      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Candidate Ranking   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Final Results       │
                    └─────────────────────┘
```

The core engine must remain **stateless and deterministic**.

---

# 8. Input Model

Support:

```json
{
  "currency": "EUR",
  "prize_pool": 100000,
  "entrants": 10000,
  "entry_fee": 20,

  "winners": {
    "mode": "count",
    "value": 1500
  },

  "top_prize": {
    "mode": "auto"
  },

  "minimum_prize": {
    "mode": "entry_multiple",
    "value": 2
  },

  "style": "balanced",

  "constraints": {
    "max_buckets": 20,
    "bucket_size_monotonicity": "preferred"
  }
}
```

Support both:

```text
winner count
```

and:

```text
winner percentage
```

Eventually support:

```text
winner count = auto
```

where the engine searches multiple reasonable winner counts.

---

# 9. Hard Constraints

The following must be treated as hard constraints unless explicitly configured otherwise.

## Exact Prize Pool

```text
Σ(bucket_size × bucket_prize) == prize_pool
```

No silent rounding.

---

## Monotonicity

```text
P(rank) >= P(rank + 1)
```

A lower-ranked participant must never receive a higher payout.

---

## Minimum Prize

```text
P(rank) >= minimum_prize
```

Minimum prize can be:

```text
fixed amount
entry-fee multiple
percentage of entry fee
automatic
```

Do not hard-code 1.5× or 2× as universal rules.

These are configurable heuristics.

---

## Winner Count

If configured as a hard constraint:

```text
actual_winners == requested_winners
```

---

## Maximum Number of Buckets

```text
bucket_count <= max_buckets
```

---

## Consecutive Ranks

Buckets must represent consecutive ranks.

Valid:

```text
1
2
3
4–5
6–10
11–20
```

Invalid:

```text
1–5
6
7–40
```

if this violates the selected bucket model.

---

# 10. Bucket Size Rules

Support three modes:

```text
strict
preferred
disabled
```

Preferred structure:

```text
1
1
1
2
3
5
10
20
50
100
```

The size of payout buckets generally increases toward lower ranks.

However, the engine must be able to relax this rule when necessary to achieve a better overall solution.

---

# 11. Nice Number Engine

Implement a separate module:

```text
NiceNumberGenerator
```

It should generate candidate payout denominations.

Example:

```text
10
15
20
25
30
40
50
60
75
100
125
150
200
250
300
400
500
...
```

Do not hard-code a single denomination system.

Implement profiles:

```text
STANDARD
CONSERVATIVE
POKER
ESPORTS
CUSTOM
```

A nice number is a **configurable concept**, not simply a rounded number.

---

# 12. Ideal Curve Engine

Create an abstraction:

```text
IdealCurveModel
```

Initial implementations:

```text
PowerLawCurve
ExponentialCurve
LinearDecayCurve
CustomCurve
```

The first implementation should be `PowerLawCurve`.

The optimizer should not depend directly on the power-law formula.

It should receive a generic mapping:

```text
rank → ideal payout
```

This allows additional economic models to be introduced later.

---

# 13. Power-Law Implementation

Implement:

[
\pi_i = E + \frac{P_1-E}{i^\alpha}
]

Solve for `α` numerically.

Use binary search or another robust monotonic root-finding method.

Requirements:

* deterministic;
* numerically stable;
* configurable precision;
* tested on very small and very large tournaments.

---

# 14. Payout Styles

Implement at least:

## BALANCED

Moderate top-prize concentration with strong mid-tier rewards.

---

## TOP_HEAVY

Higher first-place and upper-tier rewards.

The exact percentage must not be hard-coded. It should emerge from the optimization profile.

---

## FLAT

More value distributed across a wider portion of the field.

---

The architecture must allow future styles:

```text
BEGINNER_FRIENDLY
ESPORTS
POKER
CUSTOM
```

A style should be represented as an **optimization profile**, not a collection of hard-coded formulas.

---

# 15. Candidate Generation

Do not produce only one solution.

Generate a candidate set by varying:

* α;
* top prize;
* winner count;
* bucket count;
* bucket boundaries;
* nice-number choices;
* bucket growth ratios;
* rounding decisions;
* payout style parameters.

Example:

```text
100–500 candidates
```

depending on tournament size.

The candidate generator must be deterministic.

---

# 16. Optimization Backends

Create:

```text
PayoutOptimizer
```

with:

```text
HeuristicOptimizer
ExactOptimizer
```

---

## Heuristic Optimizer

This is the primary MVP backend.

General algorithm:

1. Generate ideal curve.
2. Initialize bucket sizes.
3. Assign candidate nice-number payouts.
4. Merge buckets when necessary.
5. Repair bucket-size ordering.
6. Reconcile leftover pool.
7. Validate.
8. Score.

The research describes a similar four-stage heuristic and reports good scalability even for very large payout structures. 

---

## Exact Optimizer

Create the abstraction and basic implementation later.

Potential technology:

```text
OR-Tools CP-SAT
```

or another appropriate integer/constraint solver.

The exact optimizer should be used primarily for:

* small/medium tournaments;
* validation of the heuristic;
* benchmark generation;
* research experiments.

Do **not** make exact optimization a blocker for the MVP.

---

# 17. Quality Engine

Separate:

```text
VALIDITY
```

from:

```text
QUALITY
```

A structure can be valid but aesthetically poor.

Implement a modular metric system.

```text
QualityMetric
 ├── PoolAccuracyMetric
 ├── MonotonicityMetric
 ├── NiceNumberMetric
 ├── CurveDistanceMetric
 ├── RelativeCurveDistanceMetric
 ├── LogCurveDistanceMetric
 ├── SmoothnessMetric
 ├── BucketProgressionMetric
 ├── ComplexityMetric
 └── TopPrizeMetric
```

---

# 18. Quality Score

Return:

```text
0–100
```

plus detailed sub-scores.

Example:

```json
{
  "score": 94.2,
  "metrics": {
    "nice_numbers": 98,
    "curve_similarity": 92,
    "smoothness": 95,
    "bucket_structure": 93,
    "simplicity": 97
  }
}
```

The weights must be configurable.

Do not assume the default weights are objectively correct.

---

# 19. Important: Pareto / Multi-Solution Output

The system should not assume that one payout structure is universally optimal.

Return several strong alternatives.

Example:

```text
Balanced      95.4
Top Heavy     93.8
Flat          92.7
```

Eventually support a Pareto frontier across:

```text
top-prize concentration
mid-tier value
minimum prize
number of winners
number of tiers
curve similarity
complexity
```

The end user should be able to choose between different economic philosophies.

---

# 20. Reverse Optimization

Implement an optimization mode where one or more parameters are unknown.

Examples:

### Find best first prize

```text
Given:

pool = €50,000
winners = 1,000
minimum prize = €50

Find:
best P1
```

---

### Find optimal number of winners

```text
Given:

pool = €100,000
entrants = 10,000
minimum prize = €50

Find:
optimal winner count
```

---

### Find optimal pool distribution

```text
Given:

P1 = €10,000
minimum prize = €50
winner percentage = 15%

Find:
best complete payout structure
```

This is an important differentiating capability.

---

# 21. Existing Payout Analyzer

Support:

```text
analyze(existing_payout)
```

Input can be:

```json
{
  "payouts": [
    {"from": 1, "to": 1, "amount": 10000},
    {"from": 2, "to": 2, "amount": 5000},
    {"from": 3, "to": 3, "amount": 3000},
    {"from": 4, "to": 5, "amount": 1500}
  ]
}
```

Return:

```text
Validity
Quality Score
Constraint violations
Metric breakdown
Target curve deviation
Bucket analysis
Potential improvements
```

---

# 22. Existing Payout Optimizer

Support:

```text
optimize(existing_payout, constraints)
```

The optimizer should try to preserve the original intent while improving the structure.

Example:

```text
Original:
72/100

Optimized:
94/100
```

It should report:

```text
Changed:
5th prize
6–10 bucket
11–20 bucket

Preserved:
prize pool
winner count
approximate top-prize percentage
```

---

# 23. Dynamic Pool Mode

Support:

```text
base payout philosophy
+
new prize pool
```

Example:

```text
Original:
€100,000

New:
€250,000
```

The engine should preserve as much as possible:

* payout style;
* winner percentage;
* minimum-prize policy;
* bucket philosophy;
* top-prize philosophy;
* number of tiers.

This should eventually allow real-time recalculation for tournament platforms.

---

# 24. Benchmark Framework

This is a **critical MVP deliverable**.

Create a benchmark framework that compares:

### Baseline A

Simple geometric/exponential formula.

### Baseline B

Raw power-law distribution.

### Baseline C

Power-law + simple rounding.

### Our heuristic

Full constrained optimizer.

### Exact solver

Where feasible.

### Real-world payout structures

Use publicly available tournament payout structures as benchmark datasets.

For every structure calculate:

```text
Pool accuracy
Curve deviation
Nice-number score
Bucket quality
Smoothness
Complexity
Overall score
Runtime
```

---

# 25. Research Validation

Reproduce a subset of the examples from the academic research.

The research includes examples from:

* Yahoo;
* DraftKings;
* FanDuel;
* Bassmaster;
* PGA;
* WSOP.

It also reports heuristic performance on very large contests. 

Use these examples to verify that our implementation behaves sensibly.

Do not attempt to reproduce the paper's implementation byte-for-byte.

---

# 26. Human Preference Validation

Prepare the system for a future human-preference experiment.

Generate pairs/triples of payout structures:

```text
A
B
C
```

and collect:

```text
Which structure looks better?
Which feels more rewarding?
Which feels more professional?
Which would you choose as an organizer?
```

The architecture should allow human preference data to eventually calibrate Quality Score weights.

This is important because "nice" and "attractive" are partly subjective.

---

# 27. Determinism

This is a hard requirement.

For identical:

```text input
configuration
engine version
optimization profile
```

the output must be identical.

No LLM or generative model may participate in the numerical calculation path.

AI may later be used only for:

* natural-language explanations;
* conversational configuration;
* documentation;
* user assistance.

The financial calculation itself must remain deterministic and auditable. 

---

# 28. API

Implement a clean API boundary.

```http
POST /v1/payouts/generate
POST /v1/payouts/analyze
POST /v1/payouts/optimize
POST /v1/payouts/recalibrate
```

The core engine must not depend on the HTTP layer.

It should be usable directly from code and CLI.

---

# 29. CLI

Provide a CLI for development and benchmarking.

Example:

```bash
payout generate \
  --pool 100000 \
  --entrants 10000 \
  --winners 1500 \
  --style balanced
```

Also:

```bash
payout analyze payout.json
```

```bash
payout optimize payout.json
```

```bash
payout benchmark dataset.json
```

---

# 30. Output Format

Return both:

### Human-readable

```text
1          €20,000
2          €12,000
3           €8,000
4–5         €5,000
6–10        €3,000
...
```

### Machine-readable JSON

Include:

```text
input
normalized parameters
ideal curve
selected curve model
optimization parameters
payout buckets
quality score
metric breakdown
constraint results
warnings
runtime
optimizer backend
engine version
```

---

# 31. Validation Layer

Every generated structure must pass a complete validator.

Checks:

```text
✓ exact prize pool
✓ no rank gaps
✓ no rank overlaps
✓ exact winner count
✓ monotonic payouts
✓ minimum payout
✓ maximum buckets
✓ valid nice-number denominations
✓ valid bucket ordering
✓ bucket-size constraints
```

Return structured errors:

```json
{
  "valid": false,
  "errors": [
    {
      "code": "POOL_MISMATCH",
      "expected": 100000,
      "actual": 99950
    }
  ]
}
```

---

# 32. Performance Targets

Initial engineering targets:

```text
Small:
<100 ms

Medium:
<500 ms

Large:
<2 sec
```

Large benchmark:

```text
100,000+ winners
```

The research demonstrates that a heuristic approach can operate at this scale in low-second runtimes on commodity hardware. 

Optimize only after benchmarks demonstrate a real bottleneck.

---

# 33. Testing Strategy

Create automated tests for:

### Normal cases

```text
10 players / €100
100 players / €1,000
1,000 players / €10,000
10,000 players / €100,000
100,000 players / €1,000,000
```

### Edge cases

```text
1 winner
2 winners
all entrants win
very small prize pool
very large prize pool
very high entry fee
fixed first prize
fixed minimum prize
impossible constraints
```

### Invariants

Every successful payout must satisfy all configured hard constraints.

---

# 34. Project Structure

Recommended conceptual structure:

```text
payout-engine/
│
├── core/
│   ├── models/
│   ├── curves/
│   ├── constraints/
│   ├── buckets/
│   ├── optimization/
│   ├── scoring/
│   ├── validation/
│   └── reconciliation/
│
├── optimizers/
│   ├── heuristic/
│   └── exact/
│
├── analysis/
│   ├── payout_analyzer/
│   ├── benchmark/
│   └── comparison/
│
├── api/
│
├── cli/
│
├── tests/
│
├── benchmarks/
│
└── docs/
```

The exact programming language/framework is up to the implementation team, but maintain a clean separation between the mathematical engine and application/API layers.

---

# 35. What NOT to Build Yet

Do **not** build:

* authentication;
* billing;
* subscriptions;
* user accounts;
* marketing website;
* enterprise dashboard;
* payment processing;
* tournament management;
* bracket management;
* blockchain integration;
* LLM-driven payout calculation;
* complex cloud infrastructure.

The objective is to validate the **algorithmic core** first.

---

# 36. Definition of Done — MVP

The MVP is considered successful when:

### Core engine

* [ ] Generates payout structures from tournament parameters.
* [ ] Supports power-law ideal curve.
* [ ] Supports configurable nice-number profiles.
* [ ] Supports Balanced / Top-Heavy / Flat styles.
* [ ] Generates multiple candidates.
* [ ] Enforces exact prize pool.
* [ ] Enforces monotonicity.
* [ ] Enforces minimum payout.
* [ ] Supports configurable winner count.
* [ ] Supports payout buckets.
* [ ] Supports bucket-size rules.
* [ ] Produces deterministic results.

### Analysis

* [ ] Existing payout structures can be analyzed.
* [ ] Existing structures receive a quality score.
* [ ] Constraint violations are detected.
* [ ] Existing structures can be optimized.

### Optimization

* [ ] Heuristic optimizer works.
* [ ] Exact optimizer interface exists.
* [ ] Reverse optimization is supported for at least top-prize selection.
* [ ] Dynamic prize-pool recalibration works.

### Evaluation

* [ ] Benchmark suite exists.
* [ ] Baseline algorithms are implemented.
* [ ] Real-world payout examples can be imported.
* [ ] Engine outputs can be compared quantitatively.
* [ ] Performance is measured.

### API / tooling

* [ ] Core engine can run independently.
* [ ] CLI exists.
* [ ] JSON API exists.
* [ ] Documentation exists.
* [ ] Automated tests exist.

---

# 37. Most Important Success Criterion

Do **not** judge the MVP primarily by how polished the code or UI is.

The key question is:

> **Does our engine consistently produce payout structures that are measurably better than simple formulas and competitive with or better than manually designed real-world structures?**

The benchmark should answer this.

If the answer is **yes**, the next phase is:

```text
Optimization Engine
        ↓
Web Payout Designer
        ↓
Public API
        ↓
Integrations
```

If the answer is **no**, use the benchmark results to determine which part of the optimization model needs improvement before investing in SaaS infrastructure.

---

# 38. Final Engineering Principle

Build this as a **mathematical/optimization engine first and a product second**.

The core intellectual asset should be:

```text
Tournament specification
        ↓
Economic model
        ↓
Constraint system
        ↓
Candidate generation
        ↓
Optimization
        ↓
Quality evaluation
        ↓
Best payout designs
```

Everything else — UI, API, integrations, AI explanations and SaaS features — should sit on top of this deterministic core.
