# Progress Log

Append-only, verbatim record. Every entry keeps the **actual** run output and the **actual** submitted code path — nothing summarized away, so any future session can see exactly what happened rather than my recollection of it.

**Read this file at the start of every session** before writing a new problem or review.

---

## Standing weaknesses

Live list. Each entry names the day it appeared and stays here until two consecutive days show it fixed. New problems get biased toward whatever is on this list.

| # | Weakness | First seen | Status |
|---|----------|-----------|--------|
| W1 | Ships untested — no asserts written, main block left unfinished | Day 1 | **improving** — D2 had asserts, but none verified a value |
| W1b | Asserts on status flags (`== True`) instead of on values | Day 2 | **improving** — D4 all asserts check values |
| W2 | Doesn't model the nouns in the problem statement; primitives where objects belong | Day 1 | **improving** — D2 modelled correctly; now over-models (classes where data suffices) |
| W9 | Puts a rule on the wrong object (`is_dead` in `Game`, not `Character`) | Day 2 | **open** |
| W10 | **Submits without running the file.** D3 asserts added in the final save, never executed | Day 3 | **CLOSED** — D4 ran clean, output pasted |
| W1c | Asserts absence-of-exception (`raises(...) is None`) instead of the returned value | Day 4 | **open** |
| W13 | **Tests the part he's confident about, skips the part he's unsure of** | Day 4 | **open — regressed.** D5 9/10; D6 **4/15**, and all three bugs sat in the unwritten 11 |
| W14 | One field doing two jobs / terms not captured at event time | Day 4 | **split verdict.** D6 got requirement 10 right *by construction* (first time) — then reintroduced the bug in the same file via `return_date` (due → actual). 5 appearances: D2 `baseHealth`, D4 `amount_used`, D5 loan policy, D6 req-10 ✓, D6 `return_date` ✗ |
| W11 | Deletes failing asserts instead of debugging them (D3 v4→v5) | Day 3 | **open** |
| W12 | Long stretches with no execution (D3: 20 min / ~2000 bytes between runs) | Day 3 | **open** |
| W3 | Enumerates boundary cases instead of deriving them; misses an orientation | Day 1 | **open** |
| W4 | `>=` vs `>` confusion at limits/boundaries | Day 1 | **open — 5 consecutive days.** D1 back-to-back, D3 ₹1000, D4 fee gate, D5 max-loans + reminder. Habit to build: say aloud whether the limit itself is allowed, then pick the operator |
| W15 | Asserts share mutable state; later asserts depend on earlier ones' side effects | Day 5 | **open** — D5 hid the off-by-one; D3 positional-`attack`; D6 one shared service throughout |
| W16 | Method returns the running total instead of the delta its name promises | Day 3 | **open — 3 occurrences.** D3 `apply_discount`, D4 `fee()`, D6 `return_vehicle`. Check: does the method's name describe the number it returns? |
| W5 | No input validation at the boundary | Day 1 | **open — 4th appearance.** D4: negative payment adds money. He *had* written the guard; lost in the revert |
| W6 | De Morgan — flips `and`/`or` without flipping the operators | Day 1 grill | **open** — but see note below; underlying interval model is sound |
| W7 | Knows the right behavior, attaches the wrong principle name (called OCP "SRP") | Day 1 grill | **effectively MET** — D4 named ISP + LSP correctly and unprompted; artifact lost to an undo, not to ignorance |
| W8 | Conflates access patterns — answered lookup-by-ID for a search-by-range question | Day 1 grill | **open** |

---

## Scores

| Day | Problem | Topic | Lang | Cor | Ext | SOL | Rd | Com | Total |
|-----|---------|-------|------|-----|-----|-----|----|----|-------|
| 01 | Hotel Room Booking | baseline, no pattern | Python | 1 | 1 | 1 | 2 | 1 | **6** / 25 |
| 02 | Combat System | composition vs inheritance | Python | 3 | 4 | 3 | 2 | 2 | **14** / 25 |
| 03 | Shopping Cart Checkout | SRP + OCP | Python | 1 | 2 | 3 | 2 | 1 | **9** / 25 |
| 04 | Payment Methods | LSP + ISP | Python | 2 | 4 | 4 | 3 | 2 | **15** / 25 |
| 05 | Library Lending | DIP | Python | 2 | 4 | 4 | 3 | 3 | **16** / 25 |
| 06 | Vehicle Rental | consolidation | Python | 2 | 4 | 4 | 2 | 3 | **15** / 25 |

Java for day 1: not submitted.

---

## Day 01 — Hotel Room Booking

- **Date:** 2026-07-29
- **Language submitted:** Python only
- **Submitted file (verbatim, do not edit):** `day-01/solution.submitted.py`
- **Working file:** `day-01/solution.py`
- **Review:** `day-01/REVIEW.md`
- **Rewrite:** `day-01/rewrite.py` — verified `all checks passed`

### Run output, as-is

```
$ python3 solution.py
exit: 0
```

No output. No asserts. `__main__` block adds three rooms and ends mid-line — the submission was never executed by its author.

### Behavior probe, as-is

Driving the submitted `Hotel` class against the cases the problem statement listed as mandatory:

```
1. normal booking 1->5 : (True, 'Room booked successfully')
2. exact overlap 1->5  : (False, 'Room is not available')
3. inside 2->4         : (False, 'Room is not available')
4. RIGHT overlap 3->8  : (True, 'Room booked successfully')   <-- should be REJECTED
5. back-to-back 5->7   : (False, 'Room is not available')     <-- should be ACCEPTED

bookings on 101: [(date(2026, 8, 1), date(2026, 8, 5)), (date(2026, 8, 3), date(2026, 8, 8))]

6. find_available 1->5 : [102, 103]
7. bad range 5->1      : (True, 'Room booked successfully')   <-- should be REJECTED
8. missing room 999    : (False, 'Room not found')
9. price nights=1      : CRASH -> TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'
10. price 1->5         : (400, 'Price of the room is 400')
```

Case 4 leaves room 101 double-booked for Aug 3-5.

### Defects found

1. **Right-hand overlap unguarded** — three enumerated conditions cover inside / contains / left-overlap; the "starts inside, ends after" orientation has no condition. Silent double-booking.
2. **Back-to-back rejected** — condition 3 uses `t >= bf` where the half-open range needs `t > bf`. Asymmetric: the mirror boundary (`f == bt`) is correctly allowed.
3. **No `check_out > check_in` validation** — reversed ranges book successfully.
4. **No `Room` class** — rooms are bare ints, so room type and per-room price have nowhere to live; requirement 5 (find by type) is unimplementable as written. Price is a single hotel-wide value.
5. **`price_of_room` off-by-one guard** — `nights > 1` sends `nights == 1` down the date branch with `None` dates → `TypeError`.
6. **Duplicated branches** in `book_room` — both arms end in the same append.
7. **`availability` misnamed** — holds bookings, i.e. unavailability.
8. **`(bool, str)` returns never consumed** — every caller discards the message.

### Grill — answered 2026-07-29, scored ~2.5 / 5

| Q | Topic | Verdict |
|---|-------|---------|
| 1 | Derive overlap | **Partial.** Non-overlap clauses correct in spirit (both carried a redundant half). Used `t < bf` where half-open needs `t <= bf` — the *same* boundary asymmetry as the code bug, so it's a consistent mental model, not a typo. Then the negation failed: flipped `or`→`and` but left operators unflipped, yielding an always-`False` condition. → **W6** |
| 2 | Scale to 7M listings | **Wrong question answered.** Proposed booking-ID lookup; that's the `cancel` access pattern, but availability search has no ID — it's what you're finding. Sorted + binary search instinct was right (interval tree / index on `(room_id, check_in)`). Missed the bigger point: at that scale you filter by geography + capacity first, so fan-out is the bottleneck, not the scan. → **W8** |
| 3 | Result tuple vs exception | **Weak.** Said "give exact message" — exceptions carry messages too. Missed the real argument: exceptions are for *exceptional* conditions; a booking conflict is an expected outcome, and a result type puts it in the signature so callers can't skip it (Rust `Result`, Go `err`). |
| 4 | frozen vs seasonal pricing | **Dodged.** Proposed a `dict[room_type, price]` override, which moves price from per-room to per-type and loses a spec requirement; doesn't address immutability. Missed: `dataclasses.replace` replaces rather than mutates; the friction is a *diagnostic* that seasonal price isn't a room property at all (rate calendar). Missed the concrete bug — mutating `Room.price` silently changes every past booking's total. |
| 5 | Adding filter criteria | **Right behavior, wrong name.** Described OCP correctly ("extended instead of changing already written code") then labelled it SRP. Final sentence also contradicted the principle — "add logic inside available_room" *is* modification. → **W7** |
| 6 | When `Guest` becomes a class | **Correct.** ID proof, address, primary guest + companions. Addition offered: also when a guest must be recognised *across* bookings — identity, not just attributes. |

Pattern across answers: instincts are sound, formal reasoning and principle *naming* are weak. Both get tested out loud in interviews.

### Follow-up on Q1 — resolved same day

Pushed back on the `t < bf` vs `t <= bf` call, arguing the checkout day isn't occupied so the range is free. The principle was right; it's precisely what forces `<=` (last occupied night is `t-1`, so clearing on the left means `t-1 < bf`, i.e. `t <= bf`). Shown via the concrete case new `[Aug 1, Aug 5)` vs existing `[Aug 5, Aug 10)` — disjoint nights `{1,2,3,4}` and `{5..9}`, which his formula rejected.

Also surfaced the diagnostic worth reusing: his two clauses disagreed in strictness (`f >= bt` had the `=`, `t < bf` didn't). **A symmetric rule must have matching strictness at both boundaries** — when they differ, one is wrong, no test case needed to know it.

He then proposed `t <= bf or f >= bt` himself — correct. Brute-forced against ground truth (set intersection of occupied nights) over all 1296 valid range pairs: **zero mismatches**, and the De Morgan negation `t > bf and f < bt` agrees on all pairs.

**Verdict: the interval model is now solid.** W6 stays open only for the mechanical De Morgan flip, not for interval reasoning. Re-test it on a non-interval boolean condition before closing.

Technique taught: for boundary logic with more orientations than fit in your head, enumerate a small universe and compare against an oracle rather than reasoning harder. Reusable for rate limiter windows, meeting scheduler, calendar merges.

### Method note issued

`notes/how-to-approach-lld.md` — the repeatable 45-minute approach (nouns→classes, verbs→methods, boundaries→rules; find the "later we must support" clause; state assumptions; sketch API; **write asserts before code**; implement; name your design's limits). Written after Q6 at his request. Reference it in future reviews rather than re-explaining.

---

---

## Day 02 — Combat System

- **Date issued:** 2026-07-30
- **Topic:** composition vs inheritance; interfaces vs abstract classes
- **Problem:** `day-02/PROBLEM.md`
- **Status:** reviewed 2026-07-30. Python only.
- **Submitted (verbatim):** `day-02/solution.submitted.py` · **Review:** `day-02/REVIEW.md` · **Rewrite:** `day-02/rewrite.py` (passes)

### Run output, as-is

```
$ python3 solution.py
Character: warrior, Health: 120, Attack: 12
Character: mage, Health: 70, Attack: 20
Character: archer, Health: 90, Attack: 15
Character: mage, Health: 19, Attack: 20
Character: mage, Health: 2, Attack: 20
Character: mage, Health: -15, Attack: 20
{3: <__main__.mage object at 0x100827ed0>}
exit: 0
```

All asserts pass. Composition + runtime swap correct. Every spec damage number verified correct by hand-probe (22 / 25 / 53 / 120-not-healed / 22→19).

### Defects

1. **Rule 3 enforced in `Game`, not `Character`** — the only real bug. Via `Character` directly: dead characters keep taking damage *and* can still attack. Probe: `dead character ATTACKED and dealt damage -> victim at 100`. Death inferred from dict membership rather than being a property of the character.
2. **Asserts verify nothing numeric** — all seven spec-mandated numeric assertions omitted. Wrote `assert game.attack(1,2) == True`, which only proves both IDs exist in the dict; would pass with damage doubled, halved, or zero. Right code, tests blind to wrongness.
3. Five identical `assert game.attack(1,3) == True` lines where meaning is *positional* (the 5th kills) — fragile, intent invisible.
4. **Data-only subclasses** — `warrior`/`mage`/`archer`/`Sword`/`Bow`/`staff` override no behavior. Should be values. Matters concretely: the "later" clause says a *designer* adds 40 weapons — classes mean 40 code edits, data means a config file.
5. `isinstance(weapon_arg, type)` hack accepting either class or instance — absorbing an inconsistency in his own call convention (`main` passes `Sword`, `swapWeapon` passes `Sword()`).
6. `baseHealth` doing double duty as max and current health — no health bar or healing possible.
7. Class attributes mutated as instance state; works by luck of Python attribute lookup.
8. lowercase class names (inconsistent — `Sword`/`Bow` capitalised); param/class shadowing in `swapWeapon`; stray `from unicodedata import name`; defensive `getattr` for an impossible `None`.
9. `Game` registry not asked for; makes `equip` unreachable without registration.

### Required items — 1 of 3 delivered

- ✓ **Assumptions block** — present and genuinely reasoned (shield placement). Real day-1→2 progress.
- ✗ **Rejected design** — wrote a design he'd *add* (factory/abstract class), not one rejected. Missed the 3×4×3 = 36 classes argument, and the stronger point that req 5 makes inheritance *impossible*, not merely ugly.
- ✗ **Naming the principle** — **W7 drill, missed entirely.** Built composition-over-inheritance correctly and never named it, OCP, or class explosion.

### Self-reported process note

Said he wrote asserts last because he didn't know what to write until the logic existed. Addressed in the review: asserts derive from the *statement*, not the implementation — the spec handed him all seven with numbers, writable before any class existed. Tests written after the code photograph the bugs; his `== True` asserts are exactly that artifact. **"I don't know what to assert" = "I don't yet know what this should do"** → go back to the statement, write English sentences, convert to asserts.

### Interviewer-interaction protocol added

At his request, `notes/how-to-approach-lld.md` now has a **"Talking to the interviewer"** section: four speaking points (read-back + scoping questions → design agreement before coding → selective narration while coding → demo + volunteered limits), plus what to say when out of time, and a lose-marks table. Compressed checklist updated with ← ASK markers.

**He wants to practise this live.** From day 3, expect him to ask scoping questions mid-problem — answer in character as an interviewer (somewhat vague, nudging at point 2) rather than as a tutor.

### Why this problem, and what it targets

Two independent varying axes (weapon × armor) so inheritance produces combinatorial explosion, plus a **runtime swap** requirement (req 5-6) that inheritance cannot satisfy at all — a subclass is fixed at construction. That's the knockout argument, not just an aesthetic one.

Deliberately targeting open weaknesses:

- **W1** (ships untested) — spec now states an empty `__main__` scores 0 on Correctness regardless of code quality. Seven specific asserts enumerated, including the "Plate vs 12 damage must not heal" floor case.
- **W7** (wrong principle name) — the file must explicitly name the principle followed *and* the one violated by the rejected design. He described OCP correctly on day 1 and called it SRP.
- **W2** (doesn't model nouns) — requires writing the *rejected* design on the page, so the modelling decision becomes explicit rather than accidental.

The "later" clause (40 weapons added by someone forbidden from editing character classes) is the OCP seed. Not naming the pattern — Strategy lands properly on day 7; today is the principle only.

Also asked for Java, with the honest reason: Python's duck typing lets you skip the abstraction entirely, so the interfaces-vs-abstract-classes half of the topic is invisible in Python alone.

---

---

## Day 03 — Shopping Cart Checkout

- **Date issued:** 2026-07-30
- **Topic:** SRP + OCP
- **Problem:** `day-03/PROBLEM.md`
- **Status:** reviewed 2026-07-30. Python only. **Did not run** — AssertionError at line 139.
- **Submitted (verbatim):** `day-03/solution.submitted.py` · **Review:** `day-03/REVIEW.md` · **Rewrite:** `day-03/rewrite.py` (passes)

### Probe output, as-is

```
subtotal                      42400
flat.apply_discount   ->      42300     (asserted 42300)  OK
category.apply_discount ->    38200.0   (asserted 41600)  <-- assert wrong, CODE right
loyalty.apply_discount ->     40280.0   (asserted 40280)  OK
calculate_discount(True)      6420.0    (asserted 2120)   <-- code right, assert wrong
calculate_discounted_total    40280.0   <-- only the LAST discount survives
calculate_final_total         CRASH -> AttributeError: 'Cart' has no attribute 'calculate_discounted_total'
flat on cart of exactly 1000 -> 1000    (spec >=1000, should be 900)
receipt method exists?        False
```

### Root cause — one wrong decision, six symptoms

`apply_discount` **returns the new total instead of the amount off.** Three discounts each returning "the total after me" cannot compose. Forced him to write `discounted_total += total - discount.apply_discount(...)` — recovering the amount by undoing the callee. Then `calculate_discounted_total` used `total = discount.apply_discount(...)` (assignment, not accumulation) so only the last discount survives; customer loses ₹4300. **No operator fixes that loop — the bug is the signature.** With `amount_off(cart) -> float` the whole thing is `sum(d.amount_off(cart) for d in discounts)`.

### Other defects

1. `calculate_final_total` calls `self.cart.calculate_discounted_total(...)` — method is on `Checkout`, not `Cart`. AttributeError on every call; never executed because asserts died first.
2. **W4, third appearance** — `total > 1000` where spec says "₹1000 or more". Spec explicitly asked for the exact-1000 assert; not written.
3. **No receipt at all** (req 6) — half the SRP lesson lived there; the JSON-later clause was the test and there's nothing to evaluate.
4. `is_loyal` passed to all three discounts; two ignore it. He chose this after being warned. Cost noted: discount 31 needing customer state changes all 31 signatures.
5. `LineItem.line_total` cached in `__init__` — stale if quantity changes. Derived data stored.
6. `Discount` base declares no `apply_discount` — not a contract.
7. Four indistinguishable `calculate_*` methods plus `taxable_amount` that returns its input unchanged.
8. Category as raw string, `"Electronics"` vs spec `ELECTRONICS`.

### Two asserts were miscalculated, not design failures

Line 139 expected 41600; code returns 38200 which is **correct**. Line 141 expected 2120 (loyalty alone); method sums all three and returns **6420**, also correct. He had the spec's numbers in a table and didn't use them — inverse of the day-2 problem.

### Planted ambiguity — not caught

`min(sum(discounts), subtotal)` so stacked discounts can't drive the bill negative. Nudged twice in character ("marketing gets enthusiastic and stacks a few more — anything make you nervous?"). Missed. Present in the rewrite.

### Required items — 0 of 3, third consecutive day

Assumptions absent (docstring is a class sketch — regression from day 2, which had real ones). Rejected design absent. **Principle names absent for the third day** despite the spec calling it out. He *applied* OCP (discount list) and SRP (Cart/Checkout split) correctly without naming either.

### Live interviewer session — first run

Went well as an exercise. He skipped point 1 (scoping questions) and opened at point 2 (stating the design). Design instincts good: Product-as-data, LineItem composing it, discounts as classes. Two wrong turns, both pushed back on in character:
- Proposed `Cart` as an abstract class with subclasses/default methods for the JSON receipt → walked him through `JsonReceiptMaharashtraTaxCart`; he'd solved the identical shape on day 2.
- Proposed computing discounts at `LineItem` level → gave the counterexample: category discount is 10% of *all* electronics, and one line item can't see the others. Two of three discounts impossible there.
- Argued for passing `is_loyal` into `amount_off`; shown that overriding doesn't change the caller's signature and polymorphism needs a uniform one.

Stopped Socratic mode at ~15 min and gave the four-object shape directly, since he was looping and burning the box.

### Edit-history forensics (VS Code Local History, 9 versions)

Source: `~/Library/Application Support/Code/User/History/-3f5cda61/`. Readable any time — no git needed.

```
12:21:09  v1  1245 B   discounts take a LINE ITEM
12:23:30  v2  1585 B   + is_loyal, + LoyaltyDiscount        (2 min)
          ...  20 MINUTES, NO SAVES  ...
12:43:30  v3  3638 B   rewrote to take CART; + Cart, Checkout, 7 methods, main
12:48:35  v4  4338 B   first asserts appear   <-- 27 min in
12:49:04  v5  4208 B   deleted 2 asserts, fixed the third
12:49:35  v6  4208 B   (no change)
12:49:48  v7  4208 B   import reorder
12:50:18  v8  4207 B   changed Apple 300 -> Rice 100
12:52:47  v9  4955 B   +9 asserts in one burst, then "done"
```

**Process findings — more actionable than the code review:**

1. **The final 9 asserts were added in the last save and never executed.** The file fails at line 139 in under a second. Submitted without running. → new **W10**.
2. **20-minute silent stretch (12:23→12:43)** — ~2000 bytes written (Cart, Checkout, 7 methods, main) with zero executions. Explains why three independent bugs coexisted; each dies instantly on a run.
3. **Asserts appeared 27 min into a 45-min box**, after all code existed. Timestamped confirmation that the day-2 review's diagnosis was right and the correction hasn't landed yet.
4. **v4→v5: wrote 3 asserts, deleted 2 of them, corrected 1.** Did not debug — removed the failing checks. → new **W11**, catch before it becomes habit.
5. **v8 changed input data (Apple 300 → Rice 100) to make numbers line up.** Legitimate here (aligning to the spec's worked example) but the shape is one step from "change the test until it passes."

**To his credit, visible only in history:**
- Started at `apply_discount(line_item)` (12:21) and rewrote to take the whole cart by 12:43 — **on his own**, without being re-told mid-implementation.
- v1 hardcoded `- 100` while `self.amount` sat unused, and v1's `CategoryDiscount.__init__` never assigned `self.category` (latent AttributeError). Both self-corrected by v2.

**Conclusion: design judgment is improving faster than execution discipline.** Every bug that survived to submission is mechanical and dies to one `python3 solution.py`.

### Original targeting note

Targets **W7** for the third consecutive day — must name the principle behind the discount design, the one that evicts receipt-formatting from the cart, and why they differ. Day 2's grill showed both Q2 and Q4 producing OCP violations (variation pushed into the caller), so the topic is well-timed.

Also: **first day with live interviewer interaction.** He may send scoping questions before starting — answer in character (somewhat vague, push back occasionally), not as a tutor. The spec contains a deliberate ambiguity worth catching: discount *ordering/stacking* is specified ("each computed on the original subtotal"), but nothing says what happens if total discount exceeds subtotal, and nothing defines whether the flat-discount threshold is checked pre- or post-other-discounts.

Worked example given with exact numbers so asserts are writable before any code (direct fix for the day-2 "didn't know what to assert" report). Non-member total deliberately left uncomputed.

### Day 2 grill — answered 2026-07-30, scored ~3.5 / 5

| Q | Verdict |
|---|---|
| 1 | **Correct.** Got runtime class-change impossibility plus field-copying cost. Sharpened for him: the deepest version is *object identity loss* — other references (party list, targeting, DoT effects) still point at the old object. |
| 2 | **Wrong, and it repeats the day-1 pattern.** Said put the dagger rule in `attack()` — that's an if-chain in the caller growing per weapon, the exact OCP violation composition prevents. Taught the line: data when it carries values, class when it carries a rule; both coexist behind one contract. |
| 3 | Deferred to "next time I'll raise". Explained the `raises` helper mechanically. Gave the real test: *expected* outcome (room unavailable) → result value defensible; *caller bug* (attacking a corpse) → raise. |
| 4 | **Arithmetic right, structure missed.** Summing defenses is correct, but two fields → 5 slots means adding `swapShield`/`swapAmulet`/`swapRing`. Answer: `dict[Slot, Equipment]`. |
| 5 | **Didn't understand the question** — restated it as *two sources of truth that can disagree* (`deadplayers` membership vs `current_health <= 0`; bypassing `Game.attack` desyncs them). **But he caught a real gap in my rewrite**: it lets you equip a corpse. Credited. |
| 6 | SRP accepted for `is_dead`; offered *Information Expert* as the more precise name. For `Sword`-as-data, told him straight it is **not** a SOLID principle — it's the type-vs-instance distinction, no name to hunt for. |

Follow-ups delivered: `notes/inheritance-composition-abstract-interface.md` (incl. a type-vs-instance section — absurdity test `class Room101`, and the classes-are-code/instances-are-data table) and `notes/weapon_contract_demo.py` (runnable, passes).

Also corrected a misreading: he thought abstract-one/interface-many was reversed. It isn't — Java `extends` takes exactly one, `implements` takes many. Noted that Python allows multiple inheritance so the constraint is Java/C#-specific.

---

---

## Day 04 — Payment Methods

- **Date issued:** 2026-08-01
- **Topic:** LSP + ISP
- **Problem:** `day-04/PROBLEM.md`
- **Status:** reviewed 2026-08-01. Python only. **Ran clean** — output pasted as required.
- **Submitted (verbatim):** `day-04/solution.submitted.py` · **Review:** `day-04/REVIEW.md` · **Rewrite:** `day-04/rewrite.py` (passes)

### LOST WORK — read before judging the Communication score

Edit history `-50d9d3e0/vbnY.py` (16:00:10) contained the assumptions block, the rejected design (well argued), **both principles named correctly — ISP and LSP, unprompted, first time in four days**, `ABC`/`@abstractmethod`, `if amount <= 0: raise ValueError` in five places, and `cancel_autodebit`. At 16:00:58 the file reverted to an earlier state and that is what was submitted. Almost certainly an undo past a save point.

Graded the submission per the rule, but **he did the work.** With `vbnY.py` submitted this scores ~19/25. W7 should be considered effectively met even though the artifact didn't survive.

### The day's lesson landed

Three capability interfaces, each class implementing only what it can honour, `GiftCard` with **no** `refund` method, `refund_all` filtering by `isinstance` and returning a correct **800** on the mixed list. Requirement 5 never explodes. This is the right answer to LSP + ISP, reached after being stuck mid-session (needed the tabulate-by-column hint).

### Run output, as-is

```
$ python3 solution.py
Refund failed for UPI: Refund amount exceeds the amount used.
All tests passed successfully!
exit: 0
```

### Probe — money bugs

```
u.pay(-100) -> -100, UPI balance 500 -> 600      <-- paying negative ADDS money
fee(1000) -> 1020.0   fee(999) -> 999   fee(500) -> 500   <-- 2% gated by invented max_amount=1000
refund(1000) x4 on a 1000 payment -> all succeed, amount_used stuck at 1000
refund_all(mixed, 400) -> 800   (correct, never asserted)
cancel method exists? False
```

### Defects

1. **Unlimited refunds** — `refund` credits `balance` but never decrements `amount_used`. Root cause is one field doing two jobs: "total ever paid" (history) vs "still refundable" (state). Same shape as day 2's `baseHealth` as max+current.
2. **No zero/negative validation** — **W5, 4th appearance**, and it *was* in the lost version. Needed in 8 places → the duplication is the signal to hoist to one `_check_amount`.
3. **Fee threshold invented** — `max_amount=1000` isn't in the spec; 2% is unconditional. His single fee assert used exactly ₹1000, the one value where the bug is invisible. Also a ternary/arithmetic precedence trap: `a*p + a if a>=m else a` parses as `(a*p+a) if ... else a`.
4. **No `cancel`** (rule 4); `autodebit` annotated `-> float`, returns `None`.
5. **`fee()` returns the total, not the fee** — *day 3's `apply_discount` bug in a new hat.* Caller must compute `fee(amount) - amount`. Also raises on insufficient balance: validation inside a calculation, duplicated in `pay` immediately after.
6. **`refund_all` swallows failures and prints** — his own run printed `Refund failed for UPI`; an over-refund silently became ₹0 while the function reported success. Type hint `list[Refundable]` is wrong (it takes `Payable`s, else no filter needed).

### Asserts — improving, with a specific gap

**All asserts check values now — W1b closing.** But ~half the required list is missing, and it's exactly the half that protects money: gift-card balance walk, insufficient-balance, zero/negative, partial refund, over-refund, recurring cancel. **Three of the four bugs above have a required assert that finds them instantly.**

One regression in a new costume: `assert raises(refund_all, payments, 100) is None` asserts only *that it didn't crash*. `refund_all` returns 800, correct, unchecked. → **W1c: asserts absence-of-exception instead of the value.**

**Four-day pattern: he asserts what he built, not what the spec demanded.**

### Edit history — process is improving

```
15:21:14   552 B  docstring + stub main (no classes)
   +32m           <-- design being resolved, not typing
15:53:24  4761 B  entire file appears at once
15:53-16:02       9 rapid saves — tight iteration, NEW and good
16:00:10  8932 B  the good version (see LOST WORK above)
16:00:58  5362 B  reverted
16:02:43  5158 B  submitted
```

Self-reported >1 hour, ~15 min on asserts first. **Told him 15 min on asserts first is correct, not slow** — day 3 he wrote them at minute 27 and the file didn't run; today first, and it ran. The hour went to the 32-minute design gap, not to typing. Speed comes after correctness and discipline; he's on step two.

### Design of the trap

Four payment methods with **non-uniform capabilities** (card: pay/refund/recurring; UPI: pay/refund; gift card and COD: pay only). The naive design — one base class carrying all three methods — forces `GiftCard.refund()` to throw, which is the textbook **LSP** violation, and forces every method to implement things it can't do, which is **ISP**.

Requirement 5 (`refund_all` over a mixed list) is the requirement that makes it *felt* rather than theoretical: a loop calling `refund()` over `[card, upi, gift, cod]` crashes on element 3 unless the design separates capabilities. Same structural move as day 2's runtime-swap requirement — turn an aesthetic argument into a correctness one.

### Targeting

- **W10 (highest priority)** — spec now requires pasting terminal output with "done". Day 3's final nine asserts were added in the last save and never executed.
- **W12** — explicit instruction to run after each method.
- **W7, fourth attempt** — narrowed the ask: name exactly two principles, one sentence each, with the two questions they answer spelled out so there's nothing to interpret. Also told him these items now outweigh an extra feature.
- **W1b** — "values, not `== True`" restated.
- **W5** — validation is now explicit in the spec (zero/negative amounts, over-balance, over-refund) rather than implied.

### Numbers pre-computed in the spec

Fee table gives 1020 / 1000 / 1000 / 1050 on a ₹1000 payment, and the gift-card balance walk (5000 → 4000) is stated. Every required assert has its number visible in the statement, so the whole assert block is writable before any class exists — the standing fix for "I didn't know what to assert".

---

---

## Day 05 — Library Lending

- **Date issued:** 2026-08-02
- **Topic:** DIP (last of the five)
- **Problem:** `day-05/PROBLEM.md`
- **Status:** reviewed 2026-08-03. Python only. **AssertionError at line 156** — but the failing assert caught a real missing rule.
- **Submitted (verbatim):** `day-05/solution.submitted.py` · **Review:** `day-05/REVIEW.md` · **Rewrite:** `day-05/rewrite.py` (passes)

### DIP landed — textbook, on the hardest of the five

Two Protocols, two implementations each (`SystemClock`/`FixedClock`, `EmailNotifier`/`FakeNotifier`), both injected via constructor, `Library` never learns which it got. Also injected the *policy* values (period, rate, cap, max loans) unprompted — which already serves the "different period per member tier" later-clause. **All fee arithmetic correct**, including the exact-due-date boundary and the ₹200 cap: `max(0, min(days*rate, cap))` floored and ceilinged properly. Fee/boundary math has been the weak spot days 1-4; clean today.

### Probe output, as-is

```
=== rule 2: book already on loan ===
m1 checks out b1 -> 2026-01-15
m2 checks out b1 -> 2026-01-15  <-- SAME book, two members
loans on b1 now  : 2

=== rule 7: max 3 loans ===
loan #1..#4 allowed (member holds 4)   loan #5 REJECTED     <-- off by one

=== rule 6: reminder ===
today=2026-01-12 sent=0   2026-01-13 sent=1   2026-01-14 sent=1
2026-01-15 sent=1   2026-01-20 sent=1   2026-06-01 sent=1   <-- fires forever
```

### Defects

1. **Rule 2 never implemented** — `checkout_book` only checks `book not in self.books` (does the library own the title), never whether the copy is out. Same book lent twice. **His own assert 6 caught it and failed honestly** — the system working, in contrast to day 4 where unwritten asserts let three bugs through. Fix: the `next(... l.checkin_date is None)` query he already wrote in `return_book`, extracted and called from both. *Two methods needing the same question is the signal to name the question.*
2. **Max loans `>` should be `>=`** — check runs before appending, so it must ask "already at the limit". **W4, fifth consecutive day** (D1 back-to-back booking, D3 ₹1000 threshold, D4 fee gate, D5 here). His assert passed *for the wrong reason* — stray loans from earlier asserts meant the member already held 4.
3. **Reminder uses `>=` so it fires forever** — still reminding on 2026-06-01. Both cases the spec named (13th yes, 12th no) pass with his version; the bug is on the *other* side, which assert 9 would have forced him to test.
4. **`notify_overdue_members` misnamed** — it sends a pre-due reminder; message says "is overdue" when nothing is overdue on the 13th. Two different features merged by naming.

### The assert that wasn't written — the day's point

Line 163 calls `notify_overdue_members()` and **nothing follows it.** He built `FakeNotifier`, gave it `sent_messages`, appended faithfully, **never read it.** The run is identical whether it sends 1, 6, or 0 messages. Assert 9 was flagged in the spec as the requirement that decides the design. Without it, `Clock`/`Notifier` are scaffolding with nothing hanging from them. → **W13, 5th day** (9/10 written, up from ~half — real progress — but the omitted one was the flagged one).

### Test isolation — new weakness

One shared `library`/`member1`/`book1`; every loan from every earlier assert persists. Consequences: the max-loans off-by-one was hidden; line 160 checks out `book3` which was never added to the library (latent second failure, masked by 156 dying first); any inserted assert changes the meaning of later ones. Same shape as **day 3's five positional `attack` calls**. → **W15**.

### Design of the trap

Two hard dependencies that a beginner reaches for by reflex: `date.today()` inside the fee calculation, and an email sender constructed inside `LendingService`. Requirement 8 makes both *impossible* rather than merely ugly — assert 5 needs a book returned **137 days late**, and the suite must not email anyone. You cannot wait 137 days, so the clock has to become injectable. Same structural move as day 2's runtime swap and day 4's mixed refund list: turn the principle into a correctness constraint the asserts enforce by themselves.

The hint is deliberately pointed ("if your first instinct is `date.today()` inside the fee calculation, follow that thought to assert 4") because DIP is the least self-evident of the five — with the others, the naive design at least *runs*.

### Targeting

- **W13 (asserts what he built, not what the spec demanded)** — the list is now numbered 1-10 with an explicit "paste all of these in first, delete none", plus the fact that day 4's skipped lines contained three of the four bugs.
- **W1c** — "assert the value, not that a call didn't raise", and assert 9 specifically requires checking *what the notifier received*.
- **W4** — assert 2 is the exact-due-date boundary, fifth consecutive day this trap has been planted.
- **W14** — cap at ₹200 plus the 137-day case forces the fee to be derived, not accumulated.
- **Lost work** — closing line asks him to verify the assumptions block and principle name are still in the file before submitting.

Assert 9 (reminder fires 2026-01-13, not 2026-01-12) can only be written against an injected notifier that records what it was asked to send — so the test itself proves the inversion happened.

---

---

## Day 06 — Vehicle Rental (Consolidation)

- **Date issued:** 2026-08-04
- **Topic:** consolidation — SRP + OCP + LSP/ISP + DIP in one problem
- **Problem:** `day-06/PROBLEM.md`
- **Time box:** 60 min (stated as deliberately longer)
- **Status:** reviewed 2026-08-07. Python only. **Runs clean, all asserts pass** — but only 4 of 15 required asserts were written.
- **Submitted (verbatim):** `day-06/solution.submitted.py` · **Review:** `day-06/REVIEW.md` · **Rewrite:** `day-06/rewrite.py` (passes)
- Elapsed ~6 days (work); session integrity held — design decisions from the chat survived into the code.

### Three things landed

1. **Requirement 10 by construction** — stated it in the design chat before coding ("order class has all the order information so that whenever we change base price it won't affect here") and it works: rate → 1500 leaves `base_cost 7000, payable 5250`. **W14's fourth appearance, first time built for up front.**
2. **Discounts correct** — one class per rule, uniform `calculate`, each returns **the amount off** not the new total. That exact bug destroyed day 3. `apply_discounts` is a clean sum.
3. **All three required items present for the first time** — assumptions, rejected design, principles named (all five listed, though not tied to the requirement that forced each, as asked).

### Probe output, as-is

```
returned ON due date -> returned value 5250.0    (spec: late fee 0)
3 days late          -> returned 6750.0          (spec: 1500)
85 days late         -> returned 10500.0         (spec: 7000, capped at BASE)
re-rent after return -> allowed                  (right outcome, wrong reason)
raises(...) -> TypeError: rent() missing 3 required positional arguments
```

### Defects — all three in `return_vehicle`, all in unwritten-assert territory

1. **Returns the total, not the late fee** — requirement 5. **Third occurrence of this exact shape**: D3 `apply_discount` → new total; D4 `fee()` → total charged; D6 `return_vehicle` → payable. Notably he got it *right* in the discount classes the same day, where he was paying attention.
2. **Cap on `payable` (5250) instead of `base_cost` (7000)** — requirement 7. Worse: `payable` is mutated while serving as the cap.
3. **`order.return_date = return_date` destroys the due date** — field starts as "due back", becomes "actually returned". **W14, fifth appearance**, and reintroduced in the same file where requirement 10 was solved correctly. Also silently breaks his own already-rented check, which queries a field whose meaning changed. He had `checkin_date is None` on day 5 and didn't carry it forward.

### The assert that tests nothing

`assert raises(rental_service.rent, (member2, car2, 7, date(2026,1,1)))` — args wrapped in **one tuple**, so `rent()` fails on arity and never reaches the rule. Passes, proves nothing. Root cause: `raises()` catches bare `Exception` and returns the object, so any failure is truthy. Fix: catch `ValueError` specifically.

### Sharper diagnosis of W13

Not "he skips asserts" — **he tests the part he is confident about and skips the part he is unsure of.** Discounts were the interesting problem, thought about hard, tested, correct. The return path was mechanical, written fast, tested zero. Exactly backwards. Worth repeating in future reviews in this form.

### Still open from earlier days

- **Bike/Car as subclasses overriding nothing** — day-2 lesson, restated in the day-6 design chat two days prior, still not applied. Costs him: the "later" scooter needs a class instead of a config row.
- **`Discount.calculate(member, vehicle, days, base_cost)`** — 4 params. Rule 21 needing a start date changes 21 signatures. Third time (D2 `AttackContext`, D4 `is_loyal`).
- **`print` in business logic** (spec forbade it), return annotations that lie (`charge() -> float` returns `True`).
- **No invoice** — requirement 9, the SRP half of the day, not built.

### What each requirement recombines

| Requirement | Day | Principle |
|---|---|---|
| charge / load capabilities differ per vehicle | 4 | ISP + LSP |
| pricing rules all active, summed against base | 3 | OCP |
| invoice as text, JSON later | 3 | SRP |
| reminder one day before due | 5 | DIP (clock + notifier) |
| vehicle already out cannot be re-rented | 5 | (rule 2 he missed) |
| rate change must not reprice an active rental | 1/4/5 | **W14**, fourth appearance |

### Targeting

- **W4 (5 consecutive days)** — three boundaries planted: "7 days **or more**" with an explicit 6-day counter-assert (#3), "**on** the due date is free" (#6), and the reminder firing on exactly one day (#14).
- **W15 (new)** — spec explicitly requires a fresh-state helper per assert block, and cites the day-5 max-loans assert that passed for the wrong reason.
- **W13** — fifteen numbered asserts, "paste all in, delete none."
- **W1c** — #12 and #13 say *assert the method doesn't exist*, not that it raises. #14 says assert on what the notifier received.
- **W14** — requirement 10 is now its own numbered assert (#15), with the three prior appearances named so he sees the pattern rather than the instance.

No new principle introduced. Every trap is one he has already met and, in most cases, already got wrong once.

---

## Next

Day 1 Java still open (optional — the modelling lesson was already extracted via the grill).
Day 2 Java open.

