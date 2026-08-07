# Day 6 — Vehicle Rental (Consolidation)

**Time box: 60 minutes.** Longer than usual on purpose — this recombines days 2-5.

No new principle today. Every trap below is one you've already met.

---

## The problem

Build the rental core for a vehicle rental company.

### The fleet

| Vehicle | Rate / day | Can charge | Can carry cargo |
|---|---|---|---|
| Bike | ₹200 | ✗ | ✗ |
| Car | ₹1000 | ✗ | ✗ |
| Electric Car | ₹1200 | ✓ | ✗ |
| Truck | ₹2500 | ✗ | ✓ (max 1000 kg) |

- **Charging** adds range to an electric car. Nothing else can be charged.
- **Loading** puts cargo in a truck, up to 1000 kg. Nothing else can be loaded.

### Renting

1. `rent(vehicle, customer, start_date, days)` produces a rental due back on `start_date + days`.
2. **A vehicle already out on rent cannot be rented again.**
3. **Base cost** = daily rate × days.
4. `days` must be at least 1.

### Pricing rules — all active at once

| Rule | Discount |
|---|---|
| Long rental | 15% off the base cost if the rental is **7 days or more** |
| Loyalty | 10% off the base cost for members |

Each discount is computed against the **base cost**, then summed. Payable = base − total discount.

### Returning

5. `return_vehicle(vehicle, on_date)` frees the vehicle and returns the **late fee**.
6. **Late fee** = ₹500 per day past the due date. Returning **on** the due date is free.
7. The late fee is **capped at the base cost** of that rental.

### Reminders

8. **One day before** a rental is due, the customer is sent a reminder. Not two days before, not every day after — exactly one day before.

### Output

9. An **invoice** as text, showing the vehicle, the days, the base cost, each discount applied with its amount, and the payable total.

### Worked example — use these for your asserts

A **member** rents a **Car** (₹1000/day) for **7 days** from 2026-03-01:

```
base cost        = 7000      (1000 x 7)
long rental 15%  = 1050      (7 days qualifies — "7 or more")
loyalty 10%      =  700
total discount   = 1750
payable          = 5250
due back         = 2026-03-08
```

Returned 2026-03-11 → 3 days late → **₹1500**.
Returned 2026-06-01 → 85 days late → ₹42500, capped at **₹7000**.

### Later we must support (do not build it)

- A weekend surge rule, and roughly 20 more pricing rules, added by the pricing team.
- Invoices as JSON for the mobile app.
- Rentals stored in Postgres.
- Scooters (rate ₹300, chargeable) and refrigerated trucks (chargeable **and** loadable).

### Constraints

- In-memory, standard library only.
- **No `print()` in business logic.**
- `solution.py` required.

---

## Requirement 10 — the one that ties it together

**Changing a vehicle's daily rate must not change the cost of a rental already in progress.**

If the company raises the Car rate to ₹1500 while someone is mid-rental, that customer still pays the ₹7000 base they agreed to. You've hit this three times now — day 1 (mutating a room's price reprices past bookings), day 4 (`amount_used` vs `refundable`), day 5 (which policy prices an old loan). Get it right by construction this time.

---

## Required before the code

1. **Assumptions.** One line each.
2. **The design you rejected.** One sketch, one sentence on what breaks.
3. **Name three principles**, one line each, and say which requirement forced each one.

---

## Required asserts

**Paste all fourteen in before you implement. Delete none.**

**Every assert must start from fresh state.** Day 5 your max-loans assert passed for the wrong reason because earlier asserts had left rentals lying around. Write a helper that builds a clean service and call it in each block.

1. member, Car, 7 days → base 7000, discount 1750, payable 5250
2. non-member, Car, 7 days → discount 1050, payable 5950
3. member, Car, **6 days** → no long-rental discount; base 6000, discount 600, payable 5400 *(the boundary — 7 qualifies, 6 does not)*
4. Bike 3 days non-member → base 600, no discounts, payable 600
5. due date for a 7-day rental from 2026-03-01 is 2026-03-08
6. returned 2026-03-08 → late fee 0 *(the boundary — on the due date is free)*
7. returned 2026-03-11 → 1500
8. returned 2026-06-01 → 7000, not 42500
9. renting an already-rented vehicle → error, and the first rental is unchanged
10. after return, the same vehicle can be rented again
11. `days=0` and `days=-1` → error
12. charging an electric car works; **a Bike has no charge method at all** — assert that, don't assert that it raises
13. loading 800 kg into a truck works; 1200 kg → error; **a Car has no load method at all**
14. the reminder fires on 2026-03-07 and on **no other day** — assert on what the notifier *received*, and check at least 2026-03-06, 2026-03-08, and 2026-03-20

Then requirement 10:

15. rent a Car for 7 days, change the Car's rate to ₹1500, and assert the in-progress rental still costs 7000

Print `all checks passed` at the end.

---

## When you say done

Paste the terminal output, and check your three required items are still in the file before you submit.
