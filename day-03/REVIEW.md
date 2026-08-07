# Day 3 Review — Shopping Cart Checkout (Python)

Reviewed 2026-07-30. Submission preserved as `solution.submitted.py`.

## Verdict

**`python3 solution.py` → AssertionError at line 139. It does not run.**

Say the important thing first, because the score won't: **your structure improved.** `Cart` holds line items and computes a subtotal and nothing else — that's exactly right, and it's the thing you were resisting an hour earlier. `Checkout` as a separate object holding a *list* of discounts is the right shape. You built the skeleton correctly.

Then the arithmetic came apart.

```
subtotal                      42400
flat.apply_discount   ->      42300     (you asserted 42300)  ✓
category.apply_discount ->    38200.0   (you asserted 41600)  <-- assert wrong, CODE right
loyalty.apply_discount ->     40280.0   (you asserted 40280)  ✓

calculate_discount(True)      6420.0    (you asserted 2120)   <-- code right, assert wrong
calculate_discounted_total    40280.0   <-- only the LAST discount survives
calculate_final_total         CRASH -> AttributeError: 'Cart' has no attribute 'calculate_discounted_total'

flat on a cart of exactly 1000 -> 1000  (spec says >=1000 qualifies, should be 900)
receipt method exists?        False
```

## Score

| Axis | D1 | D2 | D3 | Why |
|---|---|---|---|---|
| Correctness | 1 | 3 | **1** / 5 | Doesn't run. Only the last discount applies. One method crashes. Boundary wrong. Receipt absent. |
| Extensibility | 1 | 4 | **2** / 5 | Discounts are a list of objects — right — but returning a *total* instead of an *amount* breaks stacking |
| SOLID | 1 | 3 | **3** / 5 | `Cart` is genuinely clean now. `Checkout` separated. But `Discount` base declares no contract, and the receipt was never extracted because it was never written |
| Readability | 2 | 2 | **2** / 5 | Four `calculate_*` methods whose differences aren't guessable; `apply_discount` doesn't apply a discount |
| Communication | 1 | 2 | **1** / 5 | No assumptions, no rejected design, no principle names — third day running |

**9 / 25.** Down from 14, and I'm not going to soften it: a submission that raises an `AssertionError` fails the round regardless of how good the design underneath is. But the drop is misleading — days 1-2 you had working code and a weak model; today you have a better model and broken code. The model is the harder half.

---

## The root cause: one wrong decision, six symptoms

```python
def apply_discount(self, cart, is_loyal) -> float:
    return total - self.amount if total > 1000 else total
```

**`apply_discount` returns the new total, not the amount taken off.** Every bug below is downstream of that.

Three discounts each returning "the total after me" cannot be combined. Ask the flat discount and it says 42300. Ask loyalty and it says 40280. Now what? They're both claiming to be the answer, and neither knows the other exists.

Watch what that forced you into:

```python
def calculate_discount(self, is_loyal):
    for discount in self.discounts:
        discounted_total += total - discount.apply_discount(self.cart, is_loyal)
```

You subtract each returned total *back* from the subtotal to recover the amount. It works — that line genuinely produces 6420 — but you're converting the value back into the thing the method should have returned in the first place. **When the caller has to undo what the callee did, the callee's return type is wrong.**

And then:

```python
def calculate_discounted_total(self, is_loyal):
    total = self.cart.calculate_total()
    for discount in self.discounts:
        total = discount.apply_discount(self.cart, is_loyal)   # = not +=
    return total
```

**Assignment, not accumulation.** Each pass throws away the previous result. Three discounts in the list, only the last one — loyalty — survives. The customer loses ₹4300. Note this isn't really a typo: with `+=` it would be even more wrong (it'd sum three totals to ~120,000). There is no operator that makes this loop correct, because the return type can't be combined. **The bug is in the signature, not the loop.**

Fix the return type and everything collapses to one obvious line:

```python
def amount_off(self, cart) -> float: ...          # each discount returns what IT takes off

total_discount = sum(d.amount_off(cart) for d in discounts)
```

That's the whole design. `sum()` over a uniform contract.

## Three more real defects

**1. `calculate_final_total` crashes.**
```python
return self.cart.calculate_discounted_total(is_loyal)   # Cart doesn't have this
```
It's on `Checkout`, not `Cart`. `AttributeError` on every call. It was never executed because the asserts died first — which is the argument for running your file after each method, not once at the end.

**2. The threshold boundary is wrong — W4, third appearance.**
```python
return total - self.amount if total > 1000 else total
```
Spec: *"₹100 off if the subtotal is ₹1000 **or more**."* You wrote `>`. A cart of exactly ₹1000 gets nothing. I explicitly asked you to assert the ₹1000 boundary and that assert doesn't exist. Same `>` vs `>=` slip as day 1's back-to-back booking.

**3. No receipt. At all.** Requirement 6, and half of today's SRP lesson lived there. The JSON-later clause was the test: could a second output format be added without touching the money code? Nothing to evaluate.

## Two asserts were simply miscalculated

Worth separating, because these aren't design failures:

- Line 139 asserts the category discount yields **41600**. Your code returns **38200**, and 38200 is *correct* (42400 − 4200). The code was right and the test was wrong.
- Line 141 asserts `calculate_discount(True) == 2120`. That's the loyalty discount alone; the method sums all three and returns **6420**, which is also correct.

This is what "asserts written from the code instead of from the statement" looks like in reverse — you had the spec's numbers available (subtotal 42400, discounts 100 / 4200 / 2120, total discount 6420) and didn't use them. **Copy the spec's numbers verbatim into asserts before writing code.** They were printed in a table for exactly this reason.

## The `is_loyal` parameter

You went with it after I flagged it, which is your call to make — but note what it cost:

```python
class FlatDiscount:
    def apply_discount(self, cart, is_loyal): ...     # never reads is_loyal
class CategoryDiscount:
    def apply_discount(self, cart, is_loyal): ...     # never reads is_loyal
```

Two of three ignore it. Discount 31 needs the customer's state → a third parameter → all 31 signatures change. The rewrite puts `Customer` on the `Cart`, so `amount_off(cart)` never changes no matter what a future discount wants to know. Same lesson as `AttackContext` on day 2: **give the contract one argument that can carry anything.**

## Smaller things

- **`LineItem.line_total` is computed once in `__init__`** and cached. Change `quantity` afterwards and the total is stale. Make it a `@property` — it's derived data, and derived data should never be stored.
- **`Discount` base class declares nothing.** It holds `name` and no `apply_discount`. So it's not a contract — nothing stops a discount from omitting the method, and a reader can't learn the interface from the base. Either give it an abstract method or use a `Protocol`.
- **Four methods named `calculate_*`** — `calculate_total`, `calculate_discount`, `calculate_discounted_total`, `calculate_final_total` — plus `taxable_amount` which just returns `calculate_final_total` unchanged. I can't tell them apart from the names, and two of them are wrong. Compute the numbers once into one result object.
- **`Cart.calculate_total` is the subtotal.** Call it `subtotal`; "total" already means something else in this domain.
- **Category as a raw string** — `"Electronics"` here, `ELECTRONICS` in the spec. One typo and a discount silently matches nothing. An `Enum` makes it a `NameError` instead.
- **Missing asserts**: empty cart, no-electronics cart, the ₹1000 boundary, the non-member total, receipt contains the total. All five were listed in the spec.

## The rewrite

`rewrite.py`, verified `all checks passed`. Same skeleton as yours — `Cart` / discount objects / `Checkout` — with the return type fixed and the receipt extracted. Note `checkout()` collapses to seven lines once `amount_off` composes, and `text_receipt()` never touches money logic, so the JSON version is a second function and nothing else moves.

One thing the rewrite adds that neither of us discussed: `min(sum(...), subtotal)` so stacked discounts can't drive the total negative. **That was the ambiguity I planted, and the question I nudged you toward** — *"marketing gets enthusiastic and stacks a few more. Anything about that arrangement make you nervous?"* You didn't catch it. With 30 discounts summing independently against the subtotal, exceeding 100% is inevitable, and your code would have produced a negative bill.

## Required items — 0 of 3

Third consecutive day.

- ✗ **Assumptions** — the docstring is a class sketch (`product(name, unit_price, category)`), not assumptions. Day 2 you actually wrote real ones; this is a regression.
- ✗ **Rejected design** — absent.
- ✗ **Principle names** — absent. The answers:
  - **Open/Closed** — why discounts are a list of objects behind one contract. 30 more need zero edits to `Cart` or `Checkout`.
  - **Single Responsibility** — why the receipt doesn't live in `Cart`. A Cart changes when *what it holds* changes; a receipt changes when *the output format* changes. Two different reasons to change means two classes.
  - **The difference**: OCP is about *adding* behavior without editing. SRP is about *separating* behavior that changes for different reasons. Discounts are OCP; receipt-vs-cart is SRP.

You separated `Cart` from `Checkout` and put discounts in a list — you *applied* both principles today, correctly, without naming either.

## Grill

1. I said "when the caller has to undo what the callee did, the callee's return type is wrong." **Where else in your file does a caller undo a callee?** (There's one more.)
I didnt even properly understood this caller called callee and undo and return type nothing understood but may be in final_amount calculation or calculate_disocunted_total 
2. `calculate_discounted_total` used `=` where a loop needs accumulation. I claimed `+=` wouldn't fix it either. **Why not?** What would `+=` return for the three discounts?
We should just do sub_total of all cart - discounted which we did before . this would give discounted total on cart . but at end time i used aut suggest of vs code and filled thos 
3. Marketing wants "20% off, maximum ₹500 off." **Where does the cap go** — in the discount, in `checkout`, or somewhere else? Justify it with a principle.
in discount flat disocunt we add another type called percentage or flat . if percentage calculate perecentage else calculate flat
4. My `checkout()` returns an `Order` object rather than seven separate methods. **Name two things that buys**, one of which is about testing.
what is buys please elaborate . Its buys because order doesnt have any method to do like shipping or any order only have values and no operations

5. You cached `line_total` in `__init__`. **Give me a concrete two-line sequence** where that produces a wrong receipt.
yeah when quantity changes for line item it would be inccorect instead we use prepoerty . explain me property here 
6. Now the JSON receipt actually arrives. **Which files change in my rewrite, and which change in yours?**
In yours add a return type as argument and return based on that . for me store all the details and do a if else thing .


also add notes about todays principles in notes
