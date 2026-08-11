# Day 7 — Ride Fare Estimation

**Time box: 45 minutes.** Timer on.

First named pattern. I'm still not telling you which one — but you've been building it since day 2, and today has one twist you haven't hit.

**The twist:** on days 3 and 6, *every* pricing rule applied and you summed them. Today **exactly one** fare algorithm applies per ride, it's chosen at runtime, and it can be swapped on a ride that already exists.

---

## The problem

Build fare estimation for a ride-hailing app.

A **ride** has a distance in km, a duration in minutes, a ride type (`MINI`, `SEDAN`, `SUV`, `AUTO`), and whether it's an airport run.

### The four fare algorithms

| Algorithm | Fare |
|---|---|
| Per-kilometre | `distance_km × rate` |
| Per-minute | `duration_min × rate` |
| Hybrid | `base + (distance_km × per_km) + (duration_min × per_min)` |
| Flat rate | a fixed amount, ignoring distance and duration |

Configured as: per-km rate **₹12**, per-minute rate **₹2**, hybrid `base 50 / ₹10 per km / ₹1 per min`, flat **₹500**.

### How a fare is computed

1. The selected algorithm produces a **base fare**.
2. Multiply by the **surge multiplier** (1.0 when there's no surge).
3. Floor the result at the **minimum fare of ₹60**.

So: `fare = max(algorithm(ride) × surge, 60)`.

### Design constraint — this one is graded

4. **An algorithm must not know about surge or the minimum fare.** Calling an algorithm directly returns its raw base fare, un-surged and un-floored. Surge and the floor are the *service's* job, not the algorithm's.

### Selection and swapping

5. A ride is assigned an algorithm by its type: `MINI` → per-km, `SEDAN` → hybrid, `SUV` → hybrid, `AUTO` → per-minute. **Airport runs use flat rate regardless of type.**
6. **The algorithm can be swapped at runtime.** Same ride, different algorithm, different fare — no new ride object.

### Receipt

7. A fare breakdown as text, showing which algorithm was used, the base fare, the surge multiplier, whether the minimum kicked in, and the final fare.

### Worked example — use these for your asserts

**Ride A: 10 km, 25 minutes.**

| Algorithm | Base fare |
|---|---|
| Per-km (₹12) | 120 |
| Per-minute (₹2) | 50 |
| Hybrid (50 / 10 / 1) | 175 |
| Flat | 500 |

With surge 1.5, hybrid gives `175 × 1.5 = 262.5`.
Per-minute with no surge gives `50` → floored to **60**.

**Ride B: 5 km, 30 minutes**, per-minute → `60` exactly. The minimum is ₹60, so this stays **60** — it is not below the minimum.

### Later we must support (do not build it)

- Roughly 15 more fare algorithms, added by the pricing team, who may not edit the fare service.
- A per-city minimum fare.
- A waiting charge added on top for time spent stationary.

### Constraints

- In-memory, standard library only. **No `print()` in business logic.**
- `solution.py` required.

---

## Required before the code

1. **Assumptions.** One line each.
2. **The design you rejected.** One sketch, one sentence on what breaks.
3. **Name the pattern**, and say in one line what varies and what stays the same. Also name **one SOLID principle** it delivers.

---

## Required asserts

**Paste all thirteen in before you implement. Delete none.**

Day 6 you wrote 4 of 15 and all three bugs lived in the 11 you skipped. Write one happy-path assert first to prove the wiring, then go straight at the parts you're least sure of.

**Every assert starts from fresh state.** Write the helper first.

1. Ride A per-km → base fare 120
2. Ride A per-minute → base fare 50
3. Ride A hybrid → base fare 175
4. Ride A flat → base fare 500
5. **Calling an algorithm directly on Ride A returns 50 for per-minute — not 60, not 75.** The algorithm knows nothing about the floor or the surge.
6. Ride A, per-minute, no surge → final fare **60** *(floored)*
7. Ride B (5 km, 30 min), per-minute, no surge → final fare **60** *(exactly the minimum — not floored, and not bumped)*
8. Ride A, hybrid, surge 1.5 → final fare **262.5**
9. Ride A, per-minute, surge 1.5 → final fare **75** *(surge applied before the floor, so no flooring)*
10. a `MINI` ride gets per-km; a `SEDAN` gets hybrid; an `AUTO` gets per-minute
11. an airport ride of type `MINI` gets flat rate, **not** per-km
12. **swap the algorithm on an existing ride** — same ride object, per-km then hybrid, assert both fares
13. the breakdown text contains the algorithm name and the final fare

Print `all checks passed` at the end.

---

## When you say done

Paste the terminal output. Check your three required items are still in the file.
