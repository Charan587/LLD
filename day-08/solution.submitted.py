"""a payment gateway interface with default methods , payment dataclass , and a webhook and refund protiocol which will be like urntime checkable 
but as per your suggestion creating client , verfier and refund protocol . and implements all of them for stripe and razor pay . and implementing those functionalities 

assumptions are creating different class for each one of them and thinikning only one request will come in a time not considering multithreading here .

so rejected design are - we could have used iter tools so that payment id doesnt be same for eveyrone now lets say we create different client but payment id remains same 

patterns - as far i know ISP , factory and startergy .

"""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

@dataclass(frozen=False)
class Payment:
    id:str = None
    amount:int = None
    charge:int=None
    refund_id:str = None
    is_refunded:bool=False

    @property
    def total_amount(self):
        return self.amount + self.charge if self.charge is not None else self.amount

    # @property
    # def is_refunded(self):
    #     return self.is_refunded

@runtime_checkable
class PaymentClient(Protocol):

    def charge(amount:int)->None: ...

class RazorPayClient(PaymentClient):

    def __init__(self,percentage:int, min_amount:int , prefixPay:str):
        self.percentage = percentage
        self.min_amount = min_amount
        self.prefixPay = prefixPay
        self.count =1 


    def charge(self,amount:int):
        charge = None
        if amount >= self.min_amount:
            charge =self.percentage * amount
        payment = Payment()
        payment.id = f"{self.prefixPay}{self.count}"
        self.count +=1
        payment.amount = amount
        payment.charge = charge
        return payment

class StripePayClient(PaymentClient):

    def __init__(self,percentage:int, min_amount:int , base_cost:int, prefixPay:str):
            self.percentage = percentage
            self.min_amount = min_amount
            self.base_cost = base_cost
            self.prefixPay = prefixPay
            self.count = 1
    
    
    def charge(self,amount:int):
        charge = None
        if amount >= self.min_amount:
            charge = self.percentage * amount + self.base_cost
        payment = Payment()
        payment.id = f"{self.prefixPay}{self.count}"
        self.count +=1
        payment.amount = amount
        payment.charge = charge
        return payment


class Verifier:

    def verifier(self,payment:Payment):
        pass

class RazorPayVerifier(Verifier):

    def verifier(self,payment:Payment, signature:str):
            return signature == f"rzp_{payment.id}"

class StripePayVerifier(Verifier):

    def verifier(self,payment:Payment, signature:str):
            return signature == f"whsec_{payment.id}"


class Refund:

    def refund(payment:Payment):
        pass

class RazorPayRefund(Refund):

    def refund(self,payment:Payment):
        if "rzp" not in payment.id:
            raise ValueError("only razorpay refunds here")

        if payment.is_refunded:
            raise ValueError("Already refunded")

        payment.refund_id = f"rfnd_{payment.id}"
        payment.is_refunded = True

        return payment

class StripePayRefund(Refund):

    def refund(self,payment:Payment):
        if "stripe" not in payment.id:
            raise ValueError("only stripe refunds here")

        if payment.is_refunded:
            raise ValueError("Already refunded")

        payment.refund_id = f"rfnd_{payment.id}"
        payment.is_refunded = True

        return payment

class Factory:
    def create_client(self):
        pass
    
    def create_verifier(self):
        pass

    def create_refunder(self):
        pass

class RazorPayFactory(Factory):

    def create_client(self,percentage:int, min_amount:int , prefixPay:str):
        return RazorPayClient(percentage=percentage, min_amount=min_amount , prefixPay=prefixPay)

    def create_verifier(self):
        return RazorPayVerifier()


    def create_refunder(self):
        return RazorPayRefund()

class StripeFactory(Factory):

    def create_client(self,percentage:int, min_amount:int , base_cost:int, prefixPay:str):
        return StripePayClient(percentage=percentage, min_amount=min_amount , base_cost=base_cost, prefixPay=prefixPay)
    
    def create_verifier(self):
        return StripePayVerifier()


    def create_refunder(self):
        return StripePayRefund()

class CashFreeFactory(Factory):

    def create_client(self):
        pass
    
    def create_verifier(self):
        pass

    def create_refunder(self):
        pass


class FactoryGateWay:
    def __init__(self,factoryMap : dict[str,Factory]):
        self.factoryMap = factoryMap

    def add(self,name:str , factory: Factory):
        self.factoryMap[name] = factory

    def get_factory(self,name:str):
        if name not in self.factoryMap:
            raise ValueError(f"unknown gateway: {name}")
        return self.factoryMap[name]()

def raises(fn,*args):
    try:
        fn(*args)
    except ValueError:
        return True
    return False
if __name__ == "__main__":


    razorPayClient = RazorPayClient(percentage=0.02, min_amount=50000,prefixPay="pay_rzp_")
    payment1 = razorPayClient.charge(50000)
    assert payment1.charge == 1000
    assert payment1.id == "pay_rzp_1"

    stripePayClient = StripePayClient(percentage=0.029, min_amount=50000,base_cost=300,prefixPay="ch_stripe_")
    payment2 = stripePayClient.charge(50000)


    assert payment2.charge == 1750
    assert payment2.id == "ch_stripe_1"

    payment3 = stripePayClient.charge(100)

    assert payment3.charge == None

    mapping = {"razorpay": RazorPayFactory , "stripe" : StripeFactory}

    gateway = FactoryGateWay(mapping)

    razorPayFactory = gateway.get_factory("razorpay")

    razorClient = razorPayFactory.create_client(percentage=0.02, min_amount=50000,prefixPay="pay_rzp_")
    razorVerifier = razorPayFactory.create_verifier()
    razorRefunder = razorPayFactory.create_refunder()

    assert raises(gateway.get_factory, "cashfree")

    stripePayFactory = gateway.get_factory("stripe")

    stripeClient = stripePayFactory.create_client(percentage=0.029, min_amount=50000,base_cost=300,prefixPay="ch_stripe_")
    stripeVerifier = stripePayFactory.create_verifier()
    stripeRefunder = stripePayFactory.create_refunder()

    razorRefunder.refund(payment1)

    assert payment1.refund_id == "rfnd_pay_rzp_1"

    assert raises(razorRefunder.refund,payment2)
    print("all test case passed ")


    gateway.add("cashfree", CashFreeFactory)










    






