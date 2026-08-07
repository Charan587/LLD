"""Q6 answer: adding Wallet with top-up.

Nothing in rewrite.py is edited. This file only ADDS.
Run: python3 wallet_extension.py
"""

from typing import Protocol, runtime_checkable

from rewrite import _Account, Payable, Refundable, Recurring, refund_all, raises


@runtime_checkable
class Topupable(Protocol):
    def topup(self, amount: float) -> float: ...


class Wallet(_Account):
    """pay ✓  refund ✓  recurring ✗  topup ✓ — a column nothing else ticks."""

    def refund(self, amount: float) -> float:
        return self._refund(amount)

    def topup(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError(f"amount must be positive, got {amount}")
        self.balance += amount
        return self.balance


if __name__ == "__main__":
    from rewrite import CreditCard, UPI, GiftCard, CashOnDelivery

    w = Wallet(1000)
    assert w.topup(500) == 1500
    assert raises(w.topup, -100) and w.balance == 1500

    # it slots into the existing capability machinery with no changes there
    w.pay(400)
    assert w.balance == 1100
    assert w.refund(400) == 400 and w.balance == 1500

    card = CreditCard(9000); card.pay(1000)
    methods = [card, Wallet(9000), GiftCard(9000), CashOnDelivery(9000)]
    methods[1].pay(1000)

    # refund_all was never touched and already handles Wallet
    assert refund_all(methods, 400) == 800

    # capability queries, still without calling anything
    assert [type(m).__name__ for m in methods if isinstance(m, Refundable)] == ["CreditCard", "Wallet"]
    assert [type(m).__name__ for m in methods if isinstance(m, Topupable)] == ["Wallet"]
    assert [type(m).__name__ for m in methods if isinstance(m, Recurring)] == ["CreditCard"]

    print("all checks passed — rewrite.py unchanged")
