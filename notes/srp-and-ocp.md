# SRP and OCP

The two principles from day 3. They get confused constantly — including by you on day 1, where you described OCP perfectly and called it SRP. This note is mostly about telling them apart.

---

## Single Responsibility Principle

> A class should have **one reason to change**.

Not "one method". Not "do one thing" — that's the version everyone repeats and it's useless, because "one thing" can mean anything you want. The real test is about **reasons to change**.

Ask: *who would file the ticket that forces me to edit this class?*

Day 3's `Cart`, if it also rendered receipts:

| Change request | From | Edits Cart? |
|---|---|---|
| "Support gift wrapping per item" | product team | yes |
| "Receipt needs the GST number" | finance | yes |
| "Mobile app needs JSON" | mobile team | yes |
| "New tax slab for Karnataka" | finance | yes |

**Four teams can force a change to one class.** That's four reasons to change, so it's four responsibilities. Every one of those edits risks breaking the other three, and they're all in the same file being touched by people who don't know about each other.

Split it and each team edits its own thing:

```
Cart      -> changes when what a cart HOLDS changes         (product team)
Discount  -> changes when a promotion changes               (marketing)
checkout  -> changes when the money arithmetic changes      (finance)
Receipt   -> changes when the output format changes         (mobile/design)
```

### The test

**"What would make me edit this class?"** Two unrelated answers → two classes.

### Signs you've violated it

- The class name has "and" in it, or would if it were honest (`CartAndReceipt`)
- You can't describe it in one sentence without "also"
- Two different teams keep touching the same file
- A method's name doesn't match what the class is about (`Cart.to_json`)

### The failure mode of *over*-applying it

One class per method. Fifteen files where three would do. SRP says one reason to change, **not** one operation. `Cart.add`, `Cart.remove`, `Cart.subtotal` all change for the same reason — cart contents — so they belong together.

---

## Open/Closed Principle

> Open for **extension**, closed for **modification**.
> You should be able to add new behavior *without editing existing code*.

The signature violation is an `if`/`elif` chain that grows every time the business adds something:

```python
def amount_off(self, cart, kind):          # ✗
    if kind == "flat":       return 100
    elif kind == "category": return ...
    elif kind == "loyalty":  return ...
    elif kind == "bogo":     return ...    # and it never stops
```

Discount 31 means editing a method that already works, retesting all 30, and risking a regression in code nobody touched for a year.

The fix is always the same shape: **a contract, plus one implementation per variant, plus a list.**

```python
class Discount(Protocol):
    def amount_off(self, cart: Cart) -> float: ...

total_discount = sum(d.amount_off(cart) for d in discounts)
```

Discount 31 is a new class in a new file. `checkout` never changes. That loop is already correct for every discount that will ever exist.

### The test

**"When the next variant arrives, do I edit a file or add one?"** Edit → violated. Add → satisfied.

### What OCP requires to work

Two things, and yours failed on the second:

1. **A stable contract** — all variants share one method signature. This is why `is_loyal` as a parameter was wrong: discount 31 needing the customer's state would change all 31 signatures. Anything a variant might need rides on the single argument.
2. **A composable return type** — `amount_off` returns *what it takes off*, so `sum()` works. Returning the *new total* (your version) can't compose: three discounts each claiming "the total is X" cannot be combined by any operator.

Point 2 is the deeper lesson of day 3. The contract wasn't just the signature — it was the *meaning of the return value*.

### The failure mode of *over*-applying it

An interface with exactly one implementation, forever, because someone might extend it someday. That's speculative and it's the most common form of over-engineering. OCP earns its cost when the spec says *"30 more of these are coming."* When it doesn't, write the concrete thing.

---

## Telling them apart

| | SRP | OCP |
|---|---|---|
| About | **separating** things that change for different reasons | **adding** without editing |
| Trigger | one class, many teams filing tickets | a growing `if`/`elif` over variants |
| Fix | split into separate classes | contract + implementations + a list |
| Question | "what would make me edit this?" | "does the next variant edit or add?" |
| Day 3 | receipt doesn't belong in `Cart` | discounts are a list of objects |

**They often apply to the same code at once** and that's what makes them confusable. Day 3:

- Discounts are a *list of objects* → **OCP** (add discount 31 without editing).
- Discounts are *not inside Cart* → **SRP** (marketing's changes shouldn't touch the product team's class).

Same design decision, two different justifications. When you name a principle out loud, name the one matching the *reason* you gave.

---

## Saying it in an interview

Don't say "this follows SOLID." Say which, and why, tied to a requirement:

> "Discounts sit behind one `amount_off(cart)` contract with a list in checkout — that's **Open/Closed**, so the 30 new discount types you mentioned are new classes and `checkout` never changes.
>
> And the receipt is its own function rather than a `Cart` method — that's **Single Responsibility**. A cart changes when what it holds changes; a receipt changes when the output format changes. When JSON arrives for the mobile app, I add a formatter and nothing in the money path moves."

Two sentences, both anchored to a requirement I actually stated. That's what scores.
