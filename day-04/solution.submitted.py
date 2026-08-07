
"""
so here we have customer(name , payment_method) , refundable , payable , recurringautodebit these will be the classes

so the assumption is that a custner will have a payment method only ( future adding is he has multiple payment methods) 
we have a payment method which we use to do operations here

"""
class Payable():
    def pay(self, amount: float)-> float:
        raise NotImplementedError("Subclasses must implement the pay method.")

class Refundable():
    def refund(self, amount: float)-> float:
        raise NotImplementedError("Subclasses must implement the refund method.")

class RecurringAutoDebit():
    def autodebit(self, amount: float, day:int)-> None:
        raise NotImplementedError("Subclasses must implement the autodebit method.")

class CreditCard(Payable, Refundable, RecurringAutoDebit):
    def __init__(self, balance: float, max_amount: float = 1000 , fee_percentage: float = 0.02):
        self.balance = balance
        self.max_amount = max_amount
        self.fee_percentage = fee_percentage
        self.amount_used = 0
        self.autodebit_day = None

    def fee(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Amount exceeds maximum limit.")
        return amount * self.fee_percentage + amount if amount >=self.max_amount else amount

    def pay(self, amount: float) -> float:
        fee = self.fee(amount)
        self.balance -=fee
        self.amount_used += amount
        return fee
    
    def refund(self, amount: float) -> float:
        if amount > self.amount_used:
            raise ValueError("Refund amount exceeds the amount used.")
        self.balance += amount
        return amount

    def autodebit(self, amount: float, day: int) -> float:
        if amount > self.balance:
            raise ValueError("Insufficient balance for auto-debit.")
        self.autodebit_day = day

class UPI(Payable, Refundable):
    def __init__(self, balance: float):
            self.balance = balance
            self.amount_used = 0

    def fee(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        return amount

    def pay(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        self.balance -= amount
        self.amount_used += amount
        return amount

    def refund(self, amount: float) -> float:
        if amount > self.amount_used:
            raise ValueError("Refund amount exceeds the amount used.")
        self.balance += amount
        return amount

class GiftCard(Payable):
    def __init__(self, balance: float):
        self.balance = balance
        self.amount_used = 0

    def fee(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        return amount

    def pay(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        self.balance -= amount
        self.amount_used += amount
        return amount

class CashOnDelivery(Payable):
    def __init__(self, balance: float, fee: float = 50):
        self.balance = balance
        self.flat_fee = fee
        self.amount_used = 0

    def fee(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Amount exceeds available balance.")
        return amount + self.flat_fee # Assuming a fixed fee of 50 for cash on delivery

    def pay(self, amount: float) -> float:
        if amount > self.balance:
            raise ValueError("Insufficient balance.")
        total_amount = self.fee(amount)
        self.balance -= total_amount
        self.amount_used += amount
        return total_amount


def refund_all(payments: list[Refundable], amount: float) -> float:
    total_refunded = 0
    for payment in payments:
        if isinstance(payment, Refundable):
            try:
                refunded_amount = payment.refund(amount)
                total_refunded += refunded_amount
            except ValueError as e:
                print(f"Refund failed for {payment.__class__.__name__}: {e}")
    return total_refunded


def raises(fn, *args):
    try:
        fn(*args)
    except Exception as e:
        return e
    return None

if __name__ == "__main__":

    credit_card = CreditCard(1050, 1000, 0.02)
    upi =UPI(500)
    gift_card = GiftCard(200)
    cashon_delivery = CashOnDelivery(900, 50)

    assert credit_card.fee(1000) == 1020
    assert upi.fee(500) == 500
    assert gift_card.fee(200) == 200
    assert cashon_delivery.fee(800) == 850

    assert credit_card.pay(1000) == 1020
    assert upi.pay(500) == 500
    assert gift_card.pay(200) == 200
    assert cashon_delivery.pay(800) == 850

    assert raises(credit_card.pay, 2000) is not None
    assert raises(upi.pay, 600) is not None


    payments = [credit_card, upi, gift_card, cashon_delivery]

    assert raises(refund_all, payments, 100) is None
    assert raises(refund_all, payments, 1000) is None

    print("All tests passed successfully!")