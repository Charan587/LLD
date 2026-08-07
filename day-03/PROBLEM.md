# Day 3 — Shopping Cart Checkout

**Time box: 45 minutes.** Timer on.

**New today: you may ask me questions before you start.** Read the problem, then send me your scoping questions the way you would to an interviewer — I'll answer in character, which means somewhat vague and occasionally pushing back. Read the "Talking to the interviewer" section of `../notes/how-to-approach-lld.md` first. There is at least one genuine ambiguity in this spec that you should catch.

---

## The problem

Build the checkout for an online store.

A **cart** holds line items. Each line item has a product name, a unit price, a quantity, and a category (`ELECTRONICS`, `GROCERY`, `CLOTHING`).

### Discounts, all active at once

| Discount | Rule |
|---|---|
| Flat | ₹100 off if the subtotal is ₹1000 or more |
| Category | 10% off the total value of `ELECTRONICS` items |
| Loyalty | 5% off the subtotal, members only |

**Every discount is computed against the original subtotal**, not against a running total. Then they're summed.

### The checkout sequence

1. **Subtotal** = sum of `unit_price × quantity` over all items.
2. **Total discount** = sum of every applicable discount, each computed on the subtotal.
3. **Taxable amount** = subtotal − total discount.
4. **Tax** = 18% of the taxable amount.
5. **Final total** = taxable amount + tax, rounded to 2 decimal places.
6. **Receipt** — a text summary showing each line item, the subtotal, each discount applied with its amount, tax, and the final total.

### Worked example — use these for your asserts

Cart:

| Product | Unit price | Qty | Category |
|---|---|---|---|
| Laptop | 40000 | 1 | ELECTRONICS |
| Mouse | 1000 | 2 | ELECTRONICS |
| Rice | 100 | 4 | GROCERY |

For a **member**:

```
subtotal          = 42400        (40000 + 2000 + 400)
flat discount     =   100        (subtotal >= 1000)
category discount =  4200        (10% of 42000 electronics)
loyalty discount  =  2120        (5% of 42400)
total discount    =  6420
taxable           = 35980
tax (18%)         =  6476.40
final total       = 42456.40
```

For a **non-member**, the loyalty discount does not apply. Work out that total yourself — it's one of your asserts.

### Later we must support (do not build it)

- **~30 more discount types**, added by the marketing team, who must not edit the cart or the checkout.
- Discounts that only apply on certain dates (a weekend sale).
- Discounts that apply to a specific product rather than a category.
- A second receipt format: JSON, for the mobile app.
- A different tax rate per state.

### Constraints

- In-memory, standard library only. `Decimal` is allowed but not required — `round()` is fine.
- No file I/O, no printing from inside your business logic.
- `solution.py` required.

---

## Required before the code

**1. Assumptions block.** Including whatever you decide about the ambiguity you (hopefully) found.

**2. The design you rejected.** Actually write it this time — day 2 you described a design you'd *add* instead of one you'd *reject*. One sketch, one sentence on what breaks.

**3. Name the principles.** Two of them are the whole point of today. Name the one your discount design follows, name the one that says the receipt doesn't belong in the cart, and say in one line why they're different. **This is the third day running that this is on the list.**

---

## Required asserts

Write these before implementing. Values, not `== True` — day 2's asserts all passed while verifying nothing.

- subtotal is 42400
- each of the three discounts, individually, on the cart above
- member final total is 42456.40
- non-member final total (you compute it)
- a cart under ₹1000 gets no flat discount — check the boundary at exactly ₹1000 too
- a cart with no electronics gets no category discount
- an empty cart totals 0 and does not crash
- the receipt contains the final total

Print `all checks passed` at the end.

---

Say **done** when it's in — or ask your questions first.
