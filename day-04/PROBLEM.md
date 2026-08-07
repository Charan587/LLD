# Day 4 — Payment Methods

**Time box: 45 minutes.** Timer on.

You may ask scoping questions before you start — I'll answer in character.

---

## The problem

Build the payment layer for a checkout.

Four payment methods, each with a processing fee:

| Method | Fee on a ₹1000 payment | Total charged |
|---|---|---|
| Credit Card | 2% | 1020 |
| UPI | none | 1000 |
| Gift Card | none | 1000 (from balance) |
| Cash on Delivery | flat ₹50 | 1050 |

### What each one can do

| | pay | refund | recurring auto-debit |
|---|---|---|---|
| Credit Card | ✓ | ✓ | ✓ |
| UPI | ✓ | ✓ | ✗ |
| Gift Card | ✓ | ✗ | ✗ |
| Cash on Delivery | ✓ | ✗ | ✗ |

**Gift cards cannot be refunded** — the money is gone once spent, that's the business rule.
**Cash on delivery cannot be refunded** through this system — it's handled manually at the door.

### Rules

1. `pay(amount)` returns the **total charged** including fee. Paying zero or a negative amount is an error.
2. A **gift card has a balance.** Paying more than the balance is an error, and the balance drops by the amount paid.
3. `refund(amount)` returns the amount refunded. You cannot refund more than was paid on that method.
4. A **recurring auto-debit** is set up once with an amount and a day-of-month, and can be cancelled.

### The requirement that decides your design

5. **`refund_all(payments, amount)`** — the support team hands you a mixed list of payment methods and asks to refund `amount` on each one that can be refunded. It must process every refundable method in the list and must **not** blow up because a gift card is sitting in the middle of it.

### Later we must support (do not build it)

- Net banking: pay, refund, recurring.
- Wallet: pay, refund, and it can be topped up — a capability nothing else has.
- A report listing every method that supports recurring debits.

### Constraints

- In-memory, standard library only. `abc` and `typing.Protocol` are both available.
- `solution.py` required.

---

## Required before the code

Keep these short — three or four lines total is fine. They've been missing three days running, so today they're worth more than an extra feature.

**1. Assumptions.** One line each.

**2. The design you rejected.** The naive one is a single base class with all four methods on it. Write down what happens to `GiftCard.refund()` in that design, and what requirement 5 does to it.

**3. Name two principles.** One says *why gift card shouldn't inherit a `refund` it can't honour*. The other says *why a class shouldn't be forced to implement methods it doesn't use*. They are two of the five SOLID principles and today is named after both of them.

---

## Required asserts

**Write these before you implement.** Values, not `== True`.

- card pays 1000 → charged 1020; UPI → 1000; COD → 1050
- gift card with balance 5000 pays 1000 → balance is now 4000
- gift card with balance 500 paying 1000 → error, balance unchanged at 500
- paying 0 or -100 → error, on every method
- card refunds 400 of a 1000 payment → 400 back
- refunding more than was paid → error
- **`refund_all` over `[card, upi, gift_card, cod]` refunds only the card and UPI, returns what it actually refunded, and does not raise**
- setting up a recurring debit on a card, then cancelling it

Print `all checks passed` at the end.

---

## When you say done

**Paste the terminal output.** Day 3's final nine asserts went in on the last save and were never run — the file failed in under a second. From today, "done" means you ran it and are showing me what it printed.

Run it after each method you finish, not once at the end.
