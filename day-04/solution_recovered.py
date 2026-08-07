"""
Assumptions: each payment method has its own balance and can be used independently.
The design I rejected: a single giant base class would force GiftCard to inherit refund support it cannot honor, and requirement 5 would make that even worse because the refund loop would need to special-case unsupported methods.
Principles: Interface Segregation Principle and Liskov Substitution Principle.
"""

from abc import ABC, abstractmethod


class Payable(ABC):
    @abstractmethod
    def pay(self, amount: float) -> float:
        raise NotImplementedError("Subclasses must implement the pay method.")


class Refundable(ABC):
    @abstractmethod
    def refund(self, amount: float) -> float:
        raise NotImplementedError("Subclasses must implement the refund method.")


class RecurringAutoDebit(ABC):
    @abstractmethod
    def setup_autodebit(self, amount: float, day: int) -> None:
        raise NotImplementedError("Subclasses must implement recurring debit setup.")

    @abstractmethod
    def cancel_autodebit(self) -> None:
        raise NotImplementedError("Subclasses must implement recurring debit cancellation.")


class CreditCard(Payable, Refundable, RecurringAutoDebit):
    def __init__(self, balance: float, max_amount: float = 1000, fee_percentage: float = 0.02):
        self.balance = balance
        self.max_amount = max_amount
        self.fee_percentage = fee_percentage
        self.amount_used = 0
        self.autodebit_amount = None
        self.autodebit_day = None

    def fee(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        if amount >= self.max_amount:
            return amount + amount * self.fee_percentage
        return amount

    def pay(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")

        total_amount = self.fee(amount)
        if total_amount > self.balance:
            raise ValueError("Insufficient balance for payment.")

        self.balance -= total_amount
        self.amount_used += amount
        return total_amount

    def refund(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Refund amount must be positive.")
        if amount > self.amount_used:
            raise ValueError("Refund amount exceeds the amount used.")

        self.amount_used -= amount
        self.balance += amount
        return amount

    def setup_autodebit(self, amount: float, day: int) -> None:
        if amount <= 0:
            raise ValueError("Auto-debit amount must be positive.")
        if not 1 <= day <= 31:
            raise ValueError("Day must be between 1 and 31.")
        self.autodebit_amount = amount
        self.autodebit_day = day

    def cancel_autodebit(self) -> None:
        self.autodebit_amount = None
        self.autodebit_day = None

    def autodebit(self, amount: float, day: int) -> None:
        self.setup_autodebit(amount, day)


class UPI(Payable, Refundable):
    def __init__(self, balance: float):
        self.balance = balance
        self.amount_used = 0

    def fee(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        return amount

    def pay(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        self.balance -= amount
        self.amount_used += amount
        return amount

    def refund(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Refund amount must be positive.")
        if amount > self.amount_used:
            raise ValueError("Refund amount exceeds the amount used.")
        self.amount_used -= amount
        self.balance += amount
        return amount


class GiftCard(Payable):
    def __init__(self, balance: float):
        self.balance = balance
        self.amount_used = 0

    def fee(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        return amount

    def pay(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        self.balance -= amount
        self.amount_used += amount
        return amount
    def setup_autodebit(self, amount: float, day: int) -> None:
        raise NotImplementedError("Gift cards do not support recurring debits.")

    def cancel_autodebit(self) -> None:
        raise NotImplementedError("Gift cards do not support recurring debits.")


class CashOnDelivery(Payable):
    def __init__(self, balance: float, fee_amount: float = 50):
        self.balance = balance
        self.fee_amount = fee_amount
        self.amount_used = 0

    def fee(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        return amount + self.fee_amount

    def pay(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient balance.")

        total_amount = self.fee(amount)
        self.balance -= total_amount
        self.amount_used += amount
        return total_amount

    def refund(self, amount: float) -> float:
        raise NotImplementedError("Cash on delivery refunds are handled manually.")


def refund_all(payments: list[Refundable], amount: float) -> float:
    total_refunded = 0
    for payment in payments:
        if isinstance(payment, Refundable):
            try:
                refunded_amount = payment.refund(amount)
                total_refunded += refunded_amount
            except ValueError as exc:
                print(f"Refund failed for {payment.__class__.__name__}: {exc}")
    return total_refunded


def raises(fn, *args):
    try:
        fn(*args)
    except Exception as exc:
        return exc
    return None


if __name__ == "__main__":
    credit_card = CreditCard(1050, 1000, 0.02)
    upi = UPI(500)
    gift_card = GiftCard(200)
    cashon_delivery = CashOnDelivery(800, 50)

    assert credit_card.fee(1000) == 1020
    assert upi.fee(500) == 500
    assert gift_card.fee(200) == 200
    assert cashon_delivery.fee(800) == 850

    assert credit_card.pay(1000) == 1020
    assert upi.pay(500) == 500
    assert gift_card.pay(200) == 200
    assert cashon_delivery.pay(800) == 850

    gift_card_with_balance = GiftCard(5000)
    assert gift_card_with_balance.pay(1000) == 1000
    assert gift_card_with_balance.balance == 4000

    gift_card_with_insufficient_balance = GiftCard(500)
    assert raises(gift_card_with_insufficient_balance.pay, 1000) is not None
    assert gift_card_with_insufficient_balance.balance == 500

    for payment in [credit_card, upi, gift_card, cashon_delivery]:
        assert raises(payment.pay, 0) is not None
        assert raises(payment.pay, -100) is not None

    refund_card = CreditCard(2000, 1000, 0.02)
    assert refund_card.pay(1000) == 1020
    assert refund_card.refund(400) == 400
    assert raises(refund_card.refund, 1000) is not None

    assert raises(credit_card.pay, 2000) is not None
    assert raises(upi.pay, 600) is not None

    assert raises(gift_card.refund, 300) is not None
    assert raises(cashon_delivery.refund, 900) is not None

    credit_card.setup_autodebit(500, 10)
    assert credit_card.autodebit_day == 10
    credit_card.cancel_autodebit()
    assert credit_card.autodebit_day is None
    assert raises(gift_card.setup_autodebit, 600, 1) is not None

    def build_refund_payments() -> list[object]:
        card = CreditCard(5000, 1000, 0.02)
        upi = UPI(500)
        gift_card = GiftCard(500)
        cod = CashOnDelivery(1000, 50)
        assert card.pay(1000) == 1020
        assert upi.pay(500) == 500
        assert gift_card.pay(200) == 200
        assert cod.pay(800) == 850
        return [card, upi, gift_card, cod]

    payments = build_refund_payments()
    assert refund_all(payments, 100) == 200

    payments = build_refund_payments()
    assert raises(refund_all, payments, 1000) is None

    payments = build_refund_payments()
    assert refund_all(payments, 1000) == 1500

    print("all checks passed")
