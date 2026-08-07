# LSP and ISP

Derived from day 4. Every trace below is real output from code that was actually run — nothing here is asserted at you.

---

## 1. The problem

Four payment methods. Their capabilities differ:

| | pay | refund | recurring |
|---|---|---|---|
| Credit Card | ✓ | ✓ | ✓ |
| UPI | ✓ | ✓ | ✗ |
| Gift Card | ✓ | ✗ | ✗ |
| Cash on Delivery | ✓ | ✗ | ✗ |

Gift cards can't be refunded — the money is spent. COD refunds happen manually at the door.

**The job:** support hands you a mixed list `[card, upi, gift, cod]` and asks to refund ₹400 on each one that can be. Each has paid ₹1000 and starts with a ₹9000 balance.

**The answer we want:** ₹800 refunded (card + UPI), nothing raised, gift card and COD untouched.

---

## 2. Why the obvious design fails

The obvious design is one base class with all three methods, and subclasses that override.

### Attempt 1 — `GiftCard.refund()` raises

```python
class PaymentMethod:
    def refund(self, amount):
        self.refundable -= amount; self.balance += amount; return amount

class GiftCard(PaymentMethod):
    def refund(self, amount):
        raise ValueError("gift cards cannot be refunded")

def refund_all(methods, amount):
    total = 0
    for m in methods:
        total += m.refund(amount)
    return total
```

Run it:

```
    refunded 400 on CreditCard   running total 400
    refunded 400 on UPI          running total 800
    CRASH: gift cards cannot be refunded
    state after the crash:
      CreditCard   balance    8400  refundable 600.0
      UPI          balance    8400  refundable 600.0
      GiftCard     balance    8000  refundable 1000.0
      COD          balance    8000  refundable 1000.0
```

Look at the state, not just the crash. **Card and UPI were already refunded before the exception.** Real money moved, the function threw, and there is no rollback. Support retries the whole batch and the card gets refunded twice.

The crash isn't the worst part — the *partial state* is.

### Attempt 2 — `GiftCard.refund()` returns `False` instead

The natural next thought: don't raise, just signal failure.

```python
class GiftCard(PaymentMethod):
    def refund(self, amount):
        return False
```

```
    refunded 400 on CreditCard   running total 400
    refunded 400 on UPI          running total 800
    refunded 400 on GiftCard     running total 800
    refunded 400 on COD          running total 1200
    returned 1200  -- reported as success
    state after:
      CreditCard   balance    8400  refundable 600.0
      UPI          balance    8400  refundable 600.0
      GiftCard     balance    8000  refundable 1000.0
      COD          balance    8400  refundable 600.0    <-- refunded!
```

Two new problems, both worse than the crash:

1. **It returned 1200 and reported success.** The expected answer is 800. Nobody found out.
2. **COD got refunded** — balance 8400. COD never overrode `refund`, so it silently inherited the base implementation. **A method you forget to override is a bug that looks like working code.**

And notice `total += False` quietly worked, because `False == 0` in Python. The type error that should have caught this didn't.

### What both attempts have in common

`GiftCard` was declared a `PaymentMethod`, which advertises `refund()`. Any code holding a `PaymentMethod` is entitled to call it. **The base class made a promise the subclass can't keep**, so every subclass has to break it somehow — by raising, by lying, or by silently doing the wrong thing.

That is exactly what LSP names.

---

## 3. Liskov Substitution Principle

> If `S` is a subtype of `T`, then a `T` anywhere in the program can be replaced by an `S` **without the program breaking**.

Informally: **a subclass must be usable everywhere its base is, with no special cases.**

`refund_all` was written against `PaymentMethod`. Substituting a `GiftCard` breaks it. So `GiftCard` is not a valid subtype of `PaymentMethod` — regardless of the fact that a gift card obviously *is* a payment method in English.

**That's the trap.** LSP is not about real-world "is-a". It's about **behavioural substitutability**. A gift card is-a payment method in a sentence; it is not a `PaymentMethod` in this type system, because it cannot honour the contract that type advertises.

### The three ways to violate it

1. **Throwing on an inherited method** — attempt 1.
2. **Strengthening a precondition** — base accepts any amount, subclass demands amount < 500. Callers written against the base now break.
3. **Weakening a postcondition** — base guarantees "returns the amount refunded", subclass returns `False`. Attempt 2.

### The smell that catches it early

**`isinstance` checks or `try/except` that exist to work around one specific subclass.** If a caller needs to know which subclass it holds, substitutability has already failed. (The `isinstance` in the *fixed* design below is a different thing — it asks about a **capability**, not about a concrete class.)

---

## 4. Interface Segregation Principle

> No client should be forced to depend on methods it does not use.

Same code, different lens. `PaymentMethod` bundled three unrelated capabilities. `GiftCard` needed one of them and was handed all three.

**The test:** if implementing an interface forces you to write a method body that raises, returns a dummy, or is empty — the interface is too big.

LSP and ISP are two views of one mistake here: **the interface bundled capabilities that don't always travel together.** ISP says don't build that interface; LSP says what goes wrong when you do.

---

## 5. Deriving the fix

Go back to the table. It's already the answer.

```
            pay   refund   recurring
Card         ✓      ✓         ✓
UPI          ✓      ✓         ✗
Gift Card    ✓      ✗         ✗
COD          ✓      ✗         ✗
```

**Every column is an interface. Every row is a class implementing the columns it ticks.**

Which column is ✓ all the way down? Only `pay`. So `Payable` is the only thing all four share — **the table is telling you there is no bigger common base.** The fat class was trying to make one out of columns that aren't common.

```python
@runtime_checkable
class Payable(Protocol):
    def pay(self, amount: float) -> float: ...

@runtime_checkable
class Refundable(Protocol):
    def refund(self, amount: float) -> float: ...

@runtime_checkable
class Recurring(Protocol):
    def schedule(self, amount: float, day: int) -> None: ...
    def cancel(self) -> None: ...
```

`GiftCard` now has **no `refund` method at all.** Not one that raises. Not one that returns `False`. It does not exist, so it cannot be called wrongly.

---

## 6. Dry run of the fixed design

```
    CreditCard   isinstance(_, Refundable) = True  -> refunded 400, running total 400
    UPI          isinstance(_, Refundable) = True  -> refunded 400, running total 800
    GiftCard     isinstance(_, Refundable) = False -> skipped, refund() never called
    COD          isinstance(_, Refundable) = False -> skipped, refund() never called
    returned 800
    state after:
      CreditCard   balance    8400  refundable 600.0
      UPI          balance    8400  refundable 600.0
      GiftCard     balance    8000  refundable 1000.0
      COD          balance    8000  refundable 1000.0

    does GiftCard even have a refund method? False
    who is refundable, without calling anything: ['CreditCard', 'UPI']
```

Compare against the two failures:

| | Attempt 1 (raise) | Attempt 2 (False) | Fixed |
|---|---|---|---|
| Returned | crash | 1200 | **800** |
| Gift card refunded | — | no | no |
| COD refunded | — | **yes, silently** | no |
| Partial state on failure | **yes** | — | — |
| Caller knows capability in advance | no | no | **yes** |

That last row is the one that matters most.

---

## 7. The requirement that proves it

*"A report listing every method that supports recurring debits."*

With a fat base class and `return False`, building that report means **attempting a recurring debit on every payment method to see which ones fail.** To find out what something can do, you have to try to do it.

With segregated interfaces:

```python
[m for m in methods if isinstance(m, Recurring)]
```

No debits attempted. **Capability lives in the type, not in a return value** — that's the whole idea, in one line.

---

## 8. The final code

```python
def refund_all(methods: list[Payable], amount: float) -> float:
    return sum(m.refund(amount) for m in methods if isinstance(m, Refundable))
```

One line. No try/except, no special cases, no subclass names mentioned. It is already correct for net banking and wallet, which don't exist yet.

---

## 9. Bug list — what to check when you apply this

- **A method body that raises `NotImplementedError` in a concrete class.** Abstract base: fine. Concrete leaf: LSP violation.
- **A subclass that forgets to override.** COD in attempt 2 silently inherited `refund`. If the base has no implementation to inherit, this is impossible.
- **`total += False`.** Python treats `False` as 0, so a boolean sentinel in a numeric path won't error. Never mix a status value into a value-returning method.
- **`isinstance(x, ConcreteClass)` in a caller.** Working around a specific subclass = substitutability already broken. `isinstance(x, Capability)` is fine, and is a different thing.
- **`try/except` around a polymorphic call.** Often a fat interface in disguise — you're catching "this subclass can't do it," which the type system should have told you.
- **A `can_refund()` boolean method.** Halfway house: better than crashing, but the capability still isn't in the type, so a `Refundable`-typed function can't be written.
- **`@runtime_checkable` is required** for `isinstance` against a `Protocol`. Without it you get a `TypeError` at the `isinstance` call. It only checks method *names*, not signatures — a type checker catches the rest.

---

## 10. Saying it in an interview

> "Capabilities differ per payment method, so I split them into three interfaces instead of one base class. A gift card implements only `Payable` — it has no `refund` method at all, rather than one that throws.
>
> That's **ISP**: nothing is forced to implement what it can't do. And it gives me **LSP** for free — anything typed `Refundable` really can be refunded, so `refund_all` filters by capability and never special-cases a class.
>
> It also means the 'which methods support recurring debits' report is a filter on the type, instead of attempting a debit on everything to find out."
