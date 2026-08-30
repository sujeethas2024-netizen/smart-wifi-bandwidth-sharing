# Game Theory Model

## 1. System Model

### 1.1 Players

Let N = {1, 2, ..., n} be the set of n Wi-Fi users. Each user i ∈ N is modeled as a rational, self-interested player in a non-cooperative game.

Each player i has a fixed **activity type** a_i ∈ A, where A is the set of supported activities:

- browsing
- online_class
- gaming
- streaming
- downloading

Each player also has an **activity weight** w_i > 0 reflecting the importance of bandwidth for that activity. These weights are drawn from the fixed mapping:

| Activity        | Weight w_i |
|-----------------|------------|
| browsing        | 1.0        |
| online_class    | 1.5        |
| gaming          | 1.3        |
| streaming       | 1.4        |
| downloading     | 1.1        |

### 1.2 Resources

The shared resource is a single divisible good: Wi-Fi channel capacity.

Let B_total > 0 denote the total available bandwidth (in Mbps).

Each player i submits a **request** r_i ≥ 0, representing the maximum bandwidth the player wishes to consume.

The sum of all requests is:

R = Σ_{i∈N} r_i

If R > B_total, the network is oversubscribed and a congestion game arises.

### 1.3 Strategies

The strategy space for player i is the set of feasible bandwidth allocations:

S_i = { b_i ∈ [0, r_i] }

A strategy profile is a vector s = (b_1, b_2, ..., b_n) ∈ S = S_1 × S_2 × ... × S_n.

The total allocated bandwidth is:

B_total_used = Σ_{i∈N} b_i

The congestion ratio experienced by all players is:

ρ = B_total_used / B_total

---

## 2. Utility Function

### 2.1 Full Equation

The utility of player i is:

```
U_i(B_i, B_{-i}) = w_B · ln(1 + B_i)
                 - w_C · B_i · (ΣB / B_total)
                 - w_L · latency_penalty_i
                 - w_J · jitter_penalty_i
```

In plain text, this reads as:

U_i = (benefit from own bandwidth) - (congestion cost) - (latency penalty) - (jitter penalty)

### 2.2 Term Definitions

#### Term 1: Bandwidth Benefit

```
benefit_i = w_i · ln(1 + B_i)
```

- w_i: Activity-dependent weight (see Table 1).
- B_i: Bandwidth allocated to player i (Mbps).
- ln(1 + B_i): Logarithmic benefit function giving **diminishing marginal returns**.
  - First few Mbps yield high utility.
  - Additional Mbps yield progressively smaller gains.

**Typical range**: 0 → ~4.6 (for B_i = 100 Mbps, w_i = 1.5).

#### Term 2: Congestion Cost

```
congestion_cost_i = w_C · B_i · (B_total_used / B_total)
```

- w_C: Congestion penalty coefficient. Default value: 0.5.
- B_i: Player i's allocated bandwidth.
- B_total_used / B_total: Fraction of total capacity currently in use (ρ ∈ [0, 1]).

This term penalizes players proportionally to both their own demand and the global congestion level. A player requesting more bandwidth pays a higher congestion cost when the network is busy.

**Typical range**: 0 → 50 (for B_i = 100 Mbps, w_C = 0.5, ρ = 1.0).

#### Term 3: Latency Penalty

```
latency_penalty_i = lat_w_i · lat_norm · 0.5 · B_i
```

- lat_w_i: Latency sensitivity weight for player i's activity.
- lat_norm: Normalized latency in [0, 1], computed as min(latency_ms / 100.0, 1.0).
- 0.5: Scaling factor.

**Activity-specific latency weights**:

| Activity        | lat_w_i |
|-----------------|---------|
| browsing        | 0.3     |
| online_class    | 0.9     |
| gaming          | 1.0     |
| streaming       | 0.5     |
| downloading     | 0.1     |
| default         | 0.5     |

#### Term 4: Jitter Penalty

```
jitter_penalty_i = jit_w_i · jit_norm · 0.3 · B_i
```

- jit_w_i: Jitter sensitivity weight for player i's activity.
- jit_norm: Normalized jitter in [0, 1], computed as min(jitter_ms / 20.0, 1.0).
- 0.3: Scaling factor.

**Activity-specific jitter weights**:

| Activity        | jit_w_i |
|-----------------|---------|
| browsing        | 0.2     |
| online_class    | 0.7     |
| gaming          | 1.0     |
| streaming       | 0.4     |
| downloading     | 0.1     |
| default         | 0.5     |

#### Combined QoS Penalty

For implementation efficiency, the latency and jitter penalties are combined:

```
qos_penalty_i = (lat_w_i · lat_norm · 0.5 + jit_w_i · jit_norm · 0.3) · B_i
```

This penalty is only applied when latency or jitter values are explicitly provided (> 0). If both are zero, the QoS terms vanish.

### 2.3 Final Utility Expression

Putting all terms together, the implementation computes:

```
if B_i == 0:
    U_i = 0.0
elif B_total <= 0 or B_i < 0:
    U_i = -∞
else:
    benefit = w_i · ln(1 + B_i)
    congestion_cost = w_C · B_i · (B_total_used / B_total)
    qos_penalty = (lat_w · lat_norm · 0.5 + jit_w · jit_norm · 0.3) · B_i  (if latency/jitter > 0)
    U_i = benefit - congestion_cost - qos_penalty
```

### 2.4 Worked Numerical Example

Consider a network with B_total = 100 Mbps and two players:

- Player 1 (gaming): B_1 = 30 Mbps, w_1 = 1.3, latency = 15 ms, jitter = 3 ms
- Player 2 (streaming): B_2 = 40 Mbps, w_2 = 1.4, latency = 12 ms, jitter = 2 ms

B_total_used = 70 Mbps, ρ = 0.7

**Player 1:**
- benefit = 1.3 · ln(31) = 1.3 · 3.434 = 4.464
- congestion_cost = 0.5 · 30 · 0.7 = 10.5
- lat_norm = min(15/100, 1) = 0.15, jit_norm = min(3/20, 1) = 0.15
- qos_penalty = (1.0 · 0.15 · 0.5 + 1.0 · 0.15 · 0.3) · 30 = (0.075 + 0.045) · 30 = 3.6
- U_1 = 4.464 - 10.5 - 3.6 = -9.636

**Player 2:**
- benefit = 1.4 · ln(41) = 1.4 · 3.714 = 5.199
- congestion_cost = 0.5 · 40 · 0.7 = 14.0
- lat_norm = min(12/100, 1) = 0.12, jit_norm = min(2/20, 1) = 0.10
- qos_penalty = (0.5 · 0.12 · 0.5 + 0.4 · 0.10 · 0.3) · 40 = (0.030 + 0.012) · 40 = 1.68
- U_2 = 5.199 - 14.0 - 1.68 = -10.481

---

## 3. QoS-Aware Penalties

### 3.1 Traffic Classes and QoS Requirements

The model classifies traffic into five classes. Each class has deterministic latency and jitter sensitivity weights.

| Traffic Class | Latency Sensitivity | Jitter Sensitivity | Typical Application |
|---------------|---------------------|--------------------|---------------------|
| Real-time (gaming) | High (1.0) | High (1.0) | Online multiplayer games |
| Real-time (online_class) | High (0.9) | Medium-High (0.7) | Video conferencing, live classes |
| Interactive (browsing) | Low (0.3) | Low (0.2) | Web browsing, email |
| Streaming | Medium (0.5) | Medium (0.4) | Video/audio streaming |
| Background (downloading) | Very Low (0.1) | Very Low (0.1) | File downloads, updates |

### 3.2 Latency Modeling

Latency L_i (in ms) is normalized to [0, 1]:

```
lat_norm_i = min(L_i / 100.0, 1.0)
```

The cap of 100 ms reflects typical Wi-Fi round-trip times under moderate load. Values above 100 ms are treated as equally bad (saturated penalty).

### 3.3 Jitter Modeling

Jitter J_i (in ms) is normalized to [0, 1]:

```
jit_norm_i = min(J_i / 20.0, 1.0)
```

The cap of 20 ms reflects acceptable variation for most interactive applications. Streaming and gaming are more sensitive to jitter than bulk downloads.

### 3.4 QoS Violation Interpretation

When latency or jitter exceeds the modeled thresholds, the QoS penalty term becomes active. A player receiving bandwidth but experiencing poor QoS has reduced marginal utility, which in equilibrium may lead the player to lower their demand (best-response dynamics).

---

## 4. Nash Equilibrium

### 4.1 Formal Definition

A strategy profile s* = (b*_1, ..., b*_n) is a **Nash Equilibrium** if no player can improve their utility by unilaterally changing their strategy:

```
U_i(b*_i, b*_{-i}) ≥ U_i(b_i, b*_{-i})   ∀ i ∈ N, ∀ b_i ∈ S_i
```

In this Wi-Fi context: no user can obtain a higher utility by requesting a different amount of bandwidth, given the bandwidth requests of all other users.

### 4.2 Best-Response Dynamics

The project uses an iterative best-response algorithm:

1. Initialize all allocations to 0.
2. In each iteration, every player i computes their best response b_i^BR to the current strategies of others.
3. Update player i's allocation to b_i^BR.
4. Check convergence: if the total change across all players is below a threshold, stop.
5. Otherwise, repeat from step 2.

The best response for player i solves:

```
b_i^BR = argmax_{b_i ∈ [0, r_i]} U_i(b_i, b_{-i})
```

Because the strategy space is continuous but bounded, the implementation uses a **grid search** with step size δ (default: 0.5 Mbps).

### 4.3 Convergence Criteria

The algorithm stops when:

```
Σ_{i∈N} |b_i^{new} - b_i^{old}| < δ
```

where δ is the search step size (default: 0.5 Mbps).

Alternatively, the algorithm stops after max_iterations (default: 100) even if convergence has not been reached.

### 4.4 Algorithm Pseudocode

```
Algorithm: FindNashEquilibrium(users, B_total, w_C, δ, max_iter)

Input:
  users       — list of Player objects with {user_id, activity, requested_bandwidth, weight}
  B_total     — total available bandwidth (Mbps)
  w_C         — congestion penalty coefficient
  δ           — search step size (Mbps)
  max_iter    — maximum number of iterations

Output:
  allocations — map from user_id to allocated bandwidth
  iterations  — number of iterations used

1.  allocations ← { user.user_id : 0.0 for user in users }
2.  iterations_used ← 0

3.  for iteration = 1 to max_iter do
4.      iterations_used ← iteration
5.      old_allocations ← copy(allocations)

6.      for each user in users do
7.          other_usage ← Σ_{j ≠ i} allocations[j.user_id]
8.          remaining ← max(B_total - other_usage, 0)
9.          b_max ← min(user.requested_bandwidth, remaining)

10.         best_bw ← 0.0
11.         best_utility ← -∞

12.         for candidate ← 0 to b_max step δ do
13.             total_usage ← other_usage + candidate
14.             u ← CalculateUtility(
15.                     bandwidth = candidate,
16.                     total_usage = total_usage,
17.                     total_bandwidth = B_total,
18.                     activity_weight = user.weight,
19.                     congestion_penalty = w_C
19.                 )
20.             if u > best_utility then
21.                 best_utility ← u
22.                 best_bw ← candidate
23.             end if
24.         end for

25.         allocations[user.user_id] ← best_bw
26.     end for

27.     total_change ← Σ_{i∈N} |allocations[i] - old_allocations[i]|
28.     if total_change < δ then
29.         break
30.     end if
31. end for

32. for each user in users do
33.     user.allocated_bandwidth ← allocations[user.user_id]
34. end for

35. total_usage ← Σ allocations.values()
36. for each user in users do
37.     user.utility ← CalculateUtility(
38.             bandwidth = user.allocated_bandwidth,
39.             total_usage = total_usage,
40.             total_bandwidth = B_total,
40.             activity_weight = user.weight,
41.             congestion_penalty = w_C
42.         )
43. end for

44. return (allocations, iterations_used)
```

### 4.5 Convergence Properties

- The congestion game with convex cost functions and continuous strategy spaces is known to admit pure-strategy Nash equilibria (Rosenthal, 1973).
- The best-response dynamic may not converge in all congestion games, but for the specific utility structure used here (logarithmic benefit minus linear congestion cost), empirical convergence is observed within 10-30 iterations for typical network sizes.
- Grid search with step δ introduces approximation error: the returned equilibrium is an ε-equilibrium with ε = O(δ).

---

## 5. Baseline Allocation Algorithms

### 5.1 Equal Allocation

```
E_i = min( B_total / n, r_i )
```

Every player receives an equal share of capacity, capped at their request.

**Properties**:
- Perfectly fair in the Jain sense when all requests are equal.
- Ignores activity weights and QoS requirements.
- Simple, zero computational cost.

### 5.2 Proportional Allocation

```
E_i = min( (r_i / R) · B_total, r_i )
```

Bandwidth is distributed in proportion to each player's request.

When total demand equals capacity (R = B_total), each player gets exactly what they requested.

When demand exceeds capacity (R > B_total), allocations are scaled down uniformly.

**Properties**:
- Respects individual demands.
- Can be unfair if requests vary widely (e.g., one heavy user dominates).
- Computationally trivial.

### 5.3 Priority-Based Allocation

Players are sorted by activity priority weight p_i (descending). Higher-priority activities receive preferential treatment.

Priority weights:

| Activity        | Priority p_i |
|-----------------|--------------|
| browsing        | 1.0          |
| downloading     | 1.2          |
| streaming       | 1.5          |
| online_class    | 1.8          |
| gaming          | 2.0          |

Allocation procedure:

```
1. Sort users by p_i descending.
2. remaining ← B_total
3. for each user in sorted order do
4.     share ← (p_i / Σ p_j) · B_total
5.     allocation_i ← min(share, r_i)
6.     remaining ← remaining - allocation_i
7. end for
8. if remaining > 0 then
9.     redistribute remaining equally among all users
10. end if
```

**Properties**:
- QoS-aware: gaming and video calls are prioritized.
- May starve low-priority traffic during congestion.
- Computationally O(n log n) due to sorting.

### 5.4 Max-Min Fairness

*(Planned extension — not yet implemented in the current codebase.)*

Max-min fairness maximizes the minimum allocated bandwidth:

```
maximize   min_i B_i
subject to Σ B_i ≤ B_total,  0 ≤ B_i ≤ r_i
```

Water-filling algorithm: iteratively allocate equal shares until a user's request is saturated, then redistribute the freed capacity equally among remaining unsatisfied users.

### 5.5 α-Fairness

*(Planned extension — not yet implemented in the current codebase.)*

α-fairness generalizes several objectives via a concave utility function:

```
U_i(B_i) = {
    ln(B_i)               if α = 1  (Nash / proportional fair)
    B_i^{1-α} / (1-α)     if α ≠ 1
}
```

Special cases:
- α = 0: Max-sum throughput ( utilitarian )
- α = 1: Proportional fairness
- α → ∞: Max-min fairness

The current Nash equilibrium implementation uses α = 1 implicitly through the logarithmic benefit term.

---

## 6. Fairness Metric: Jain's Fairness Index

### 6.1 Formula

```
J = ( Σ_{i=1}^n B_i )^2 / ( n · Σ_{i=1}^n B_i^2 )
```

where B_i is the bandwidth allocated to user i.

### 6.2 Properties

- **Range**: J ∈ [1/n, 1]
  - J = 1: Perfectly fair (all users receive equal bandwidth)
  - J → 1/n: Extremely unfair (one user receives almost everything)
- **Interpretation**:
  - J ≥ 0.90: Excellent fairness
  - J ≥ 0.75: Good fairness
  - J ≥ 0.50: Moderate fairness
  - J < 0.50: Poor fairness
- **Sensitivity**: Jain's index is sensitive to the number of users n. For large n, even moderate inequality can yield high J values. It is most informative when comparing strategies at the same user count.

### 6.3 Worked Example

Consider 3 users with allocations: B = [30, 30, 40] Mbps.

```
numerator   = (30 + 30 + 40)^2 = 100^2 = 10000
denominator = 3 · (30^2 + 30^2 + 40^2) = 3 · (900 + 900 + 1600) = 3 · 3400 = 10200
J           = 10000 / 10200 ≈ 0.9804
```

This indicates excellent fairness despite a 33% spread between the smallest and largest allocation.

---

## 7. Complexity Analysis

### 7.1 Single Best-Response Computation

For a single player with n total players and step size δ:

- **Grid search**: O(B_max / δ) utility evaluations, where B_max = min(r_i, B_total).
- **Per evaluation**: O(1) arithmetic operations.
- **Total per player**: O(B_max / δ)

With B_max ≈ 100 Mbps and δ = 0.5 Mbps, this is ~200 evaluations per player.

### 7.2 Single Nash Iteration

All n players compute best responses sequentially:

- **Time**: O(n · B_max / δ)
- In practice, with n = 100 and B_max = 100 Mbps, δ = 0.5 Mbps: O(100 · 200) = O(20,000) operations.

### 7.3 Full Convergence

If the algorithm converges in k iterations:

- **Time**: O(k · n · B_max / δ)
- **Space**: O(n) for storing allocations and utilities.

For typical parameters (n ≤ 200, k ≤ 100, δ = 0.5), the computation completes in well under one second on modern hardware.

### 7.4 Baseline Strategies

| Strategy       | Time Complexity | Space Complexity |
|----------------|-----------------|------------------|
| Equal          | O(n)            | O(n)             |
| Proportional   | O(n)            | O(n)             |
| Priority       | O(n log n)      | O(n)             |

---

## 8. Assumptions

The model makes the following assumptions:

1. **Rational players**: Each user aims to maximize their own utility, given the strategies of others.
2. **Perfect congestion information**: Players know (or can observe) the total bandwidth currently in use. In practice, this is provided by the central controller.
3. **Single resource**: Bandwidth is modeled as a single divisible good. Multi-AP or multi-channel extensions are not modeled.
4. **Deterministic latency/jitter**: Latency and jitter are treated as fixed parameters per experiment run, not as dynamic random variables within an iteration.
5. **No strategic misreporting**: Players truthfully report their requested bandwidth. Strategic manipulation (e.g., requesting more than needed) is not modeled.
6. **Atomic allocations**: Bandwidth is allocated in 0.01 Mbps increments due to rounding; fine-grained divisibility is assumed.
7. **No packet-level simulation**: The model operates at the flow/allocation level, not at the packet or frame level.
8. **Stationary demands**: User requests are static during the convergence process. Dynamic on/off traffic patterns are not modeled within a single equilibrium computation.
9. **Single-shot game**: The game is solved once per experimental configuration. Repeated games or learning dynamics across multiple rounds are not modeled.

---

## 9. References to Implementation

| Concept | File | Key Function |
|---------|------|--------------|
| Utility calculation | `backend/game_theory/utility.py` | `calculate_utility()` |
| Activity weights | `backend/game_theory/congestion_game.py` | `ACTIVITY_WEIGHTS` |
| QoS weights | `backend/game_theory/utility.py` | `QoS_WEIGHTS` |
| Best response | `backend/game_theory/nash_equilibrium.py` | `find_best_response()` |
| Nash solver | `backend/game_theory/nash_equilibrium.py` | `find_nash_equilibrium()` |
| Fairness index | `backend/game_theory/fairness.py` | `jains_fairness_index()` |
| Priority allocation | `backend/services/evaluation_service.py` | `priority_allocation()` |