"""Day 4 — Payment Methods. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "Four payment methods with different fees, and — this is the important
    part — different CAPABILITIES. Cards refund and recur, UPI refunds,
    gift cards and COD only pay. And I get handed a mixed list to refund."

2. CLARIFYING QUESTIONS
   - "When you say a gift card can't be refunded — is that never, or
      manually outside this system?"
   - "Should refund_all fail the whole batch on one bad entry, or process
      what it can?"
   - "Does a payment method know its own balance, or is that upstream?"

3. HOW I FOUND THE CLASSES — tabulate, then cut by column
              pay   refund   recurring
   Card        Y      Y         Y
   UPI         Y      Y         .
   GiftCard    Y      .         .
   COD         Y      .         .

   EVERY COLUMN IS AN INTERFACE. EVERY ROW IS A CLASS implementing the
   columns it ticks. Which column is Y all the way down? Only pay. So
   Payable is the only thing all four share — the table is telling me there
   is no bigger common base.

4. ASSUMPTIONS
   - Amounts are positive; zero and negative raise, checked in one place.
   - "Refundable" is what has been paid and not yet refunded — it decreases.
     Total-ever-paid is a separate, append-only fact.
   - Single-threaded.

5. THE DESIGN I REJECTED
   "One PaymentMethod base with all three methods. Then GiftCard.refund has
    to do something, and every option is bad: raising means my refund loop
    dies partway with real money already moved and no rollback; returning
    False means the batch reports success while two customers never got paid.
    The second is worse — a crash at least tells you."

6. THE DESIGN + PRINCIPLE NAMES
   "Three small interfaces instead of one fat one — that's INTERFACE
    SEGREGATION. A gift card has no refund method at all, not one that
    throws."
   "That gives me LISKOV for free: anything typed Refundable really can be
    refunded, so refund_all filters by capability and never special-cases a
    class. The 'which methods support recurring' report becomes a filter on
    the type instead of attempting a debit on everything to find out."

7. LIMITS I'D VOLUNTEER
   - "_refund lives on the shared base, so a gift card technically inherits
      the machinery even though it doesn't expose it. Cleaner would be a
      mixin only the refundable classes get."
   - "isinstance against a Protocol only checks method names, not
      signatures. A type checker catches the rest; runtime doesn't."

═══════════════════════════════════════════════════════════════════════════
"""

from typing import Protocol, runtime_checkable


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


def _check_amount(amount: float) -> None:
    """One guard, called by every pay/refund. Rule 1 lives in exactly one place."""
    if amount <= 0:
        raise ValueError(f"amount must be positive, got {amount}")


class _Account:
    """Shared bookkeeping. Not a capability — just state every method happens to keep."""

    def __init__(self, balance: float):
        self.balance = balance
        self.refundable = 0.0        # what has been paid and not yet refunded

    def fee(self, amount: float) -> float:
        return 0.0

    def pay(self, amount: float) -> float:
        _check_amount(amount)
        charged = amount + self.fee(amount)
        if charged > self.balance:
            raise ValueError(f"insufficient balance: need {charged}, have {self.balance}")
        self.balance -= charged
        self.refundable += amount
        return charged

    def _refund(self, amount: float) -> float:
        _check_amount(amount)
        if amount > self.refundable:
            raise ValueError(f"cannot refund {amount}, only {self.refundable} is refundable")
        self.refundable -= amount          # <-- the line your version was missing
        self.balance += amount
        return amount


class CreditCard(_Account):
    def __init__(self, balance: float, fee_percent: float = 2.0):
        super().__init__(balance)
        self.fee_percent = fee_percent
        self.scheduled: tuple[float, int] | None = None

    def fee(self, amount: float) -> float:
        return amount * self.fee_percent / 100      # always, no threshold

    def refund(self, amount: float) -> float:
        return self._refund(amount)

    def schedule(self, amount: float, day: int) -> None:
        _check_amount(amount)
        if not 1 <= day <= 28:
            raise ValueError(f"day must be 1-28, got {day}")
        self.scheduled = (amount, day)

    def cancel(self) -> None:
        self.scheduled = None


class UPI(_Account):
    def refund(self, amount: float) -> float:
        return self._refund(amount)


class GiftCard(_Account):
    """No refund method at all — not one that raises, not one that returns False."""


class CashOnDelivery(_Account):
    def __init__(self, balance: float, flat_fee: float = 50):
        super().__init__(balance)
        self.flat_fee = flat_fee

    def fee(self, amount: float) -> float:
        return self.flat_fee


def refund_all(methods: list[Payable], amount: float) -> float:
    """Refunds every method that CAN be refunded. Never sees a gift card's refund."""
    return sum(m.refund(amount) for m in methods if isinstance(m, Refundable))


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    # fees
    assert CreditCard(100000).pay(1000) == 1020
    assert UPI(100000).pay(1000) == 1000
    assert GiftCard(100000).pay(1000) == 1000
    assert CashOnDelivery(100000).pay(1000) == 1050
    assert CreditCard(100000).fee(999) == 19.98        # 2% applies at every amount

    # gift card balance walk
    g = GiftCard(5000)
    assert g.pay(1000) == 1000 and g.balance == 4000
    poor = GiftCard(500)
    assert raises(poor.pay, 1000) and poor.balance == 500      # unchanged

    # rule 1 — zero and negative rejected everywhere
    for m in (CreditCard(9000), UPI(9000), GiftCard(9000), CashOnDelivery(9000)):
        assert raises(m.pay, 0)
        assert raises(m.pay, -100)
        assert m.balance == 9000                                # nothing moved

    # refunds
    c = CreditCard(100000)
    c.pay(1000)
    assert c.refund(400) == 400
    assert raises(c.refund, 700)          # only 600 left refundable
    assert c.refund(600) == 600
    assert raises(c.refund, 1)            # nothing left — no infinite refunds
    assert raises(c.refund, -50)

    # requirement 5 — mixed list, no explosion, real value checked
    card, upi = CreditCard(100000), UPI(100000)
    card.pay(1000); upi.pay(1000)
    assert refund_all([card, upi, GiftCard(5000), CashOnDelivery(5000)], 400) == 800

    # capabilities are visible without calling anything
    methods = [CreditCard(1), UPI(1), GiftCard(1), CashOnDelivery(1)]
    assert [type(m).__name__ for m in methods if isinstance(m, Refundable)] == ["CreditCard", "UPI"]
    assert [type(m).__name__ for m in methods if isinstance(m, Recurring)] == ["CreditCard"]
    assert not hasattr(GiftCard(1), "refund")

    # recurring
    r = CreditCard(100000)
    r.schedule(500, 5)
    assert r.scheduled == (500, 5)
    assert raises(r.schedule, 500, 31)
    r.cancel()
    assert r.scheduled is None

    print("all checks passed")
