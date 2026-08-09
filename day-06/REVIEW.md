# Day 6 Review — Vehicle Rental (Consolidation)

Reviewed 2026-08-07. Submission preserved as `solution.submitted.py`.

## Verdict

`python3 solution.py` → **exit 0, all asserts pass.**

Three things landed that had been open for days:

**Requirement 10, solved by construction.** You said it in the design chat before writing a line — *"order class has all the order information... so that whenever we change base price it won't affect here"* — and it works:

```
after raising rate to 1500: order.base_cost 7000  payable 5250   OK
```

Fourth time this shape has come up (day 1's room price, day 4's `amount_used`, day 5's loan policy) and the first time you built for it up front.

**Discounts are right.** Separate class per rule, uniform `calculate`, and each returns **the amount off** — not the new total. That was the bug that broke day 3 entirely. `apply_discounts` is a clean sum over the list, and discount 21 is a new file.

**All three required items are present** for the first time: assumptions, rejected design, principles named.

Then the review has to say the other thing: **you wrote 4 of the 15 required asserts, and every bug I found is in the 11 you skipped.**

## Score

| Axis | D1 | D2 | D3 | D4 | D5 | D6 | Why |
|---|---|---|---|---|---|---|---|
| Correctness | 1 | 3 | 1 | 2 | 2 | **2** / 5 | Rent path fully correct. Return path wrong on all three counts. No invoice. |
| Extensibility | 1 | 4 | 2 | 4 | 4 | **4** / 5 | Discounts, clock, notifier, fee rate all injected |
| SOLID | 1 | 3 | 3 | 4 | 4 | **4** / 5 | DIP, OCP, ISP all correct. Invoice never separated because never built. Bike/Car are data wearing classes. |
| Readability | 2 | 2 | 2 | 3 | 3 | **2** / 5 | `print` inside `rent()`; two return-type annotations lie; `return_date` does two jobs |
| Communication | 1 | 2 | 1 | 2 | 3 | **3** / 5 | All three items present — first time. Principles listed but not tied to requirements. |

**15 / 25.**

---

## The asserts: 4 of 15

Written: 1, 2, 3, 4 — the discount arithmetic. All correct.

Not written: 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15.

That block is the entire **return** flow, the capability checks, the validation, the reminder, and requirement 10. Here's what was sitting in it:

```
returned ON due date -> returned value 5250.0    (spec: late fee 0)
3 days late          -> returned 6750.0          (spec: 1500)
85 days late         -> returned 10500.0         (spec: 7000)
re-rent after return -> allowed                  (should work, but for the wrong reason)
```

**Three bugs, all in `return_vehicle`, all invisible because nothing called it with an expected value.**

The pattern is now four days old, and it's sharper than "you skip asserts." **You test the part you're confident about and skip the part you're unsure of.** Discounts were the interesting bit, you thought hard about them, you tested them, they're right. The return path was mechanical, you wrote it quickly, and you tested none of it. That's exactly backwards — *the code you're least sure of is the code that needs the assert.*

The spec numbered them 1-15 and said paste them all in first, precisely so the ordering can't happen.

## The three bugs in `return_vehicle`

```python
def return_vehicle(self, order: Order, return_date: date) -> float:
    if return_date > order.return_date:
        extra_cost = min(self.late_fee_per_day * extra_days, order.payable)
        order.payable += extra_cost
        order.late_fee = extra_cost
    order.return_date = return_date
    return order.payable
```

**1. It returns the total, not the late fee.** Requirement 5 says *"returns the late fee."* You return `order.payable`, which is base − discount + fee. Returning on the due date gives `5250` where the spec wants `0`.

**Third time.** Day 3: `apply_discount` returned the new total instead of the amount off. Day 4: `fee()` returned the total charged instead of the fee. Today: `return_vehicle` returns the payable instead of the late fee. And notice — you got it *right* in the discount classes today, deliberately, because that's where you were paying attention.

The check: **does the method's name describe the number it returns?** `return_vehicle` returning 6750 when the fee is 1500 fails it.

**2. The cap is on the wrong number.** Requirement 7: *"capped at the base cost."*

```python
min(self.late_fee_per_day * extra_days, order.payable)
```

`payable` is 5250, `base_cost` is 7000. So 85 days late caps at 5250 instead of 7000. Worse, `payable` is mutated *while* being used as the cap, so a second call would cap against a different number than the first.

**3. `order.return_date = return_date` destroys the due date.**

This field starts as *"when it's due back"* and after return becomes *"when it actually came back."* Two facts, one slot — and the moment you overwrite it, the due date is gone forever. You can no longer print an invoice showing what was agreed, recompute the fee, or audit anything.

**This is W14, and it's the fifth appearance.** Day 2 `baseHealth` (max + current), day 4 `amount_used` (history + refundable), day 5's Q3 policy, day 6's requirement 10 which you *did* get right — and then this. You solved the field-doing-two-jobs problem in one place and reintroduced it in another, in the same file.

It also breaks a rule you did implement:

```python
if any(order.vehicle == vehicle and order.return_date >= start_date for order in self.orders):
```

That's your "already rented" check. After a return, `return_date` means something else, so this line is asking a question about a field whose meaning changed underneath it. It works today by luck of the dates in your asserts. **You had the right shape on day 5** — `checkin_date is None` — and didn't bring it forward. `Rental.is_open` is the fix.

## The assert that tests nothing

```python
assert raises(rental_service.rent, (member2, car2, 7, date(2026, 1, 1)))
```

```
raises(...) returned: TypeError -> RentalService.rent() missing 3 required
positional arguments: 'vehicle', 'days', and 'start_date'
```

The arguments are wrapped in **one tuple**, so `rent()` receives a single positional argument and fails on *arity*. It never reaches the rule you were testing. The assert passes and proves nothing.

Your `raises()` returns the exception object, so any exception is truthy. Catching the specific type makes this impossible:

```python
def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:      # only the error you meant
        return True
    return False
```

`TypeError` would then propagate and you'd see the mistake immediately.

## Bike and Car are still classes

```python
class Bike(Vehicle):
    def __init__(self, name, base_price):
        super().__init__(name, base_price)
```

Overrides nothing. Adds nothing. Calls `super().__init__` with the identical arguments. Same for `Car`. These are `Vehicle("Bike", 200)` and `Vehicle("Car", 1000)`.

We covered this on day 2 (sword vs dagger) and again in the design chat two days ago. `ElectricCar` and `Truck` *earn* their classes — they carry methods nothing else has. Bike and Car don't.

The cost is concrete: the scooter in my "later" list needs a new class from you instead of a config row from someone else.

`ElectricCar(Car, Chargable)` also inherits from a `Protocol` directly, which works but mixes the two styles — you're using Protocol nominally there and structurally elsewhere. Pick one per codebase.

## Smaller things

- **`print(return_date)` inside `rent()`** — the spec said no `print` in business logic. It's also why your run output has six stray dates. `ElectricCar.charge` prints too.
- **Return annotations lie.** `charge() -> float` returns `True`; `load() -> None` returns `True`. Nobody reading the signature learns anything true.
- **`Discount.calculate(member, vehicle, days, base_cost)`** — four parameters. Rule 21 needing the start date changes all 21 signatures. Day 2's `AttackContext` and day 4's `is_loyal` were the same lesson: **one argument that can carry anything.** Pass the rental.
- **No invoice** (requirement 9). It was the SRP half of the day — text now, JSON later.
- **`late_fee_per_day` defaults to 10.0** while the spec says 500. You pass 500 at the call site, so it works, but a default that's wrong for the only domain it serves is a trap for the next caller.
- **Test data is confusing** — `member3` and `member4` are both named "Alice" with email `alice@example.com1`, differing only in `is_member`. Name them for their role: `member_alice`, `nonmember_dave`.
- **`Member.is_active_member()`** wraps a boolean field with no logic. Just read `is_member` until there's a rule.

## The rewrite

`rewrite.py`, `all checks passed`. Your rent path is kept nearly intact — discount classes returning amounts, terms captured on the rental, injected clock/notifier.

Changed: `return_vehicle` returns the fee and caps on base; `Rental` is frozen with `returned_on` separate from `due_on` and an `is_open` property; Bike/Car are instances; there's a `text_invoice`; and all fifteen asserts exist with a `setup()` helper so each block starts clean.

Note `RefrigeratedTruck` near the bottom — from your "later" list, it needs **both** capabilities, and because they're separate protocols it just picks up two. That's the payoff for the ISP split.

## Grill

1. I said "the code you're least sure of is the code that needs the assert." **Give me the counter-argument** — when is testing the confident part the better use of ten minutes?
when the time alpse in an interview and needs some asserst to showcase code so at that time it would be usefull
2. My `Rental` is frozen, so `return_vehicle` builds a new one and swaps it into the list. **Name one thing that breaks** if someone holds a reference to the old `Rental`.
eveyrtime rewriting the whole data once more which is more cost. and invoice gets differed
3. Requirement 7 caps the late fee at base cost. **Why base and not payable?** Argue the business case, then say which is easier to explain to a customer.
basecost is without discount and payable is with discount . so as we are not cosnidering with seasonal discounts or any we can keep base cost
4. You mutate `order.payable` to fold in the late fee. I keep `payable` as a computed property. **What does mine cost me**, and when would yours be right?
yours is computed eveyrtine . mine only computed when there is a change. if i didnt change me code in other changing factors of paybale my code fails here
5. `RefrigeratedTruck` in my rewrite extends `CargoVehicle` and adds `charge`. **Why not extend both `CargoVehicle` and `ElectricVehicle`?** What goes wrong?
we cant extend both because if we add charge it would be already a protocol check . no need extension
6. Your "already rented" check compares `order.return_date >= start_date`. **Construct the booking sequence** where that check gives the wrong answer, using dates only.
yes lets say a vehicle is booke for next whole month and this month its none booked . but if i want to book for this month its not possible 

---

## On the gap

Six days of elapsed time for one problem is fine — work happens. What matters is that the session itself stayed intact: you kept the design decisions from the chat, and requirement 10 landed *because* you'd thought about it before you started typing.

One thing the gap did cost you: the fifteen asserts were in the spec, and by the time you were coding you were working from the design in your head rather than the checklist on the page. **When a problem spans days, re-read the spec before the final session.** The asserts you skipped were all written down.
