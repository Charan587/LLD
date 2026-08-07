""" so here we will keep vehicle data class and also charge , cargo integrface class and let bike , car , truck etc implement from this we will create objects for them . also a member class 
 and have an order class which has all the order information about member , vehicle , order details and payable so that whever we change base price for above it wont affect here
 have rental overall class to track orders , members , vehciles .
  so for notification we have fake notifier and email notifier which assigns based on envinroment  
  
  assumotions - one is to one relationship between member and vehicle and one to many relationship between member and order and one to many relationship between vehicle and order
   principles used - interface segregation principle , single responsibility principle , open closed principle , liskov substitution principle , dependency inversion principle

   rejected design - we can keep individual late fee per day for each vehcile on vehicle class level
  """

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def today(self) -> date: ...


@runtime_checkable
class Notifier(Protocol):
    def send(self, to: str, message: str) -> None: ...


class SystemClock:
    def today(self) -> date:
        return date.today()


class FixedClock:
    def __init__(self, fixed: date):
        self.fixed = fixed

    def today(self) -> date:
        return self.fixed


class EmailNotifier:
    def send(self, to: str, message: str) -> None:
        ...  # smtp_send(to, message)


class FakeNotifier:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))          # no print — the list IS the record

class Vehicle:
    def __init__(self, name: str, base_price: float):
        self.name = name
        self.base_price = base_price

    def price(self) -> float:
        return self.base_price

@runtime_checkable
class Chargable(Protocol):
    def charge(self) -> float: ...

@runtime_checkable
class Cargo(Protocol):
    def load(self, weight: float) -> None: ...

    def unload(self) -> None: ...


class Bike(Vehicle):
    def __init__(self, name: str, base_price: float):
        super().__init__(name, base_price)

class Car(Vehicle):
    def __init__(self, name: str, base_price: float):
        super().__init__(name, base_price)

class ElectricCar(Car, Chargable):
    def __init__(self, name: str, base_price: float, battery_capacity: float):
        super().__init__(name, base_price)
        self.battery_capacity = battery_capacity

    def charge(self) -> float:
        print(f"Charging {self.name} with battery capacity {self.battery_capacity} kWh.")
        return True

class Truck(Vehicle, Cargo):
    def __init__(self, name: str, base_price: float, max_cargo_weight: float = 1000):
        super().__init__(name, base_price)
        self.max_cargo_weight = max_cargo_weight
        self.cargo_weight = 0

    def load(self, weight: float) -> None:
        if self.cargo_weight + weight > self.max_cargo_weight:
            raise ValueError("Cargo weight exceeds maximum capacity.")
        self.cargo_weight += weight
        return True

    def unload(self) -> None:
        self.cargo_weight = 0

class Member:
    def __init__(self, name: str, join_date: date, email: str, is_member: bool = True):
        self.name = name
        self.join_date = join_date
        self.email = email
        self.is_member = is_member

    def is_active_member(self) -> bool:
        return self.is_member

class Discount(ABC):
    def __init__(self, name: str, percentage: float):
        self.name = name
        self.percentage = percentage

    @abstractmethod
    def calculate(self, member: Member, vehicle: Vehicle, days: int, base_cost: float) -> float:
        pass

class MemberDiscount(Discount):
    def calculate(self, member: Member, vehicle: Vehicle, days: int, base_cost: float) -> float:
        if member.is_active_member():
            return base_cost * (self.percentage / 100)
        return 0.0

class LongTermRentalDiscount(Discount):
    def calculate(self, member: Member, vehicle: Vehicle, days: int, base_cost: float) -> float:
        # give 5 percent discount if rental is for more than 7 days
        return base_cost * (self.percentage / 100) if days >= 7 else 0.0

class Order:
    def __init__(self, member: Member, vehicle:Vehicle, order_date: date, return_date: date, payable, discount: int = 0, late_fee: float = 0.0, base_cost: int = 0):
        self.member = member
        self.vehicle = vehicle
        self.order_date = order_date
        self.return_date = return_date
        self.base_cost = base_cost
        self.payable = payable
        self.discount = discount
        self.late_fee = late_fee

class RentalService:
    def __init__(self, vehicles: list[Vehicle], members: list, orders: list[Order], clock: Clock, notifier: Notifier, discounts: list[Discount], late_fee_per_day: float = 10.0, notification_days_before_due: int = 2):
        self.vehicles = vehicles
        self.members = members
        self.orders = orders
        self.clock = clock
        self.notifier = notifier
        self.discounts = discounts
        self.late_fee_per_day = late_fee_per_day
        self.notification_days_before_due = notification_days_before_due  # Notify members before the due date

    def add_member(self, member: Member) -> None:
        if member in self.members:
            raise ValueError("Member already exists.")
        self.members.append(member)

    def add_vehicle(self, vehicle: Vehicle) -> None:
        if vehicle in self.vehicles:
            raise ValueError("Vehicle already exists.")
        self.vehicles.append(vehicle)

    def base_price(self, vehicle: Vehicle) -> float:
        return vehicle.price()

    def available_vehicles(self, on_date: date) -> list[Vehicle]:
        rented_vehicles = {order.vehicle for order in self.orders if order.return_date >= on_date}
        return [vehicle for vehicle in self.vehicles if vehicle not in rented_vehicles]

    def base_cost(self, vehicle: Vehicle, days: int) -> float:
        if days <= 0:
            raise ValueError("Rental days must be positive.")
        return self.base_price(vehicle) * days

    def apply_discounts(self, member: Member, vehicle: Vehicle, base_cost: float, days: int) -> float:
        total_discount = 0
        for discount in self.discounts:
            total_discount += discount.calculate(member, vehicle, days, base_cost)
        return total_discount

    def rent(self, member, vehicle, days: int, start_date: date) -> Order:
        if days <= 0:
            raise ValueError("Rental days must be positive.")
        if vehicle not in self.vehicles:
            raise ValueError("Vehicle not available in the rental service.")
        if member not in self.members:
            raise ValueError("Member not available in the rental service.")
        if any(order.vehicle == vehicle and order.return_date >= start_date for order in self.orders):
            raise ValueError("Vehicle is already rented for the selected period.")
        today = start_date
        return_date = today + timedelta(days=days)
        print(return_date)
        base_cost = self.base_cost(vehicle, days)
        discount = self.apply_discounts(member, vehicle, base_cost, days)
        payable = max(0,base_cost - discount)
        order = Order(member, vehicle, today, return_date, payable, discount, base_cost=base_cost)
        self.orders.append(order)
        return order

    def return_vehicle(self, order: Order, return_date: date) -> float:
        if return_date < order.order_date:
            raise ValueError("Return date cannot be before the order date.")

        if return_date > order.return_date:
            extra_days = (return_date - order.return_date).days
            extra_cost = min(self.late_fee_per_day * extra_days, order.payable)
            order.payable += extra_cost
            order.late_fee = extra_cost
        order.return_date = return_date
        return order.payable

    def notify_due_returns(self) -> None:
        target = self.clock.today() + timedelta(days=self.notification_days_before_due)
        for order in self.orders:
            if order.return_date == target:
                self.notifier.send(
                    order.member.email,
                    f"Reminder: Your rental for {order.vehicle.name} is due on {order.return_date}."
                )
    


def raises(fn, *args):
    try:
        fn(*args)
    except Exception as e:
        return e
    return None   


if __name__ == "__main__":

    # Create vehicles
    bike = Bike("Bike1", 200)
    car = Car("Car1", 1000)
    car2 = Car("car2",1000)
    car3 = Car("car3",1000)
    electric_car = ElectricCar("ElectricCar1", 1200, 100)
    truck = Truck("Truck1", 1500, 1000)

    clock = FixedClock(date(2026, 1, 15))
    notifier = FakeNotifier()

    # Create members
    member1 = Member("Alice", date(2023, 1, 1), "alice@example.com", True)
    member2 = Member("Bob", date(2023, 1, 1), "bob@example.com", False)
    member3 = Member("Alice", date(2023, 1, 1), "alice@example.com1", True)
    member4 = Member("Alice", date(2023, 1, 1), "alice@example.com1", False)

    discounts = [MemberDiscount("Member Discount", 10), LongTermRentalDiscount("Long Term Rental Discount", 15)]


    rental_service = RentalService([bike, car, truck,electric_car], [member1, member2, member3, member4], [], clock, notifier, discounts, late_fee_per_day=500.0, notification_days_before_due=1)


    order1= rental_service.rent(member1, car, 7, date(2026, 1, 1))

    assert order1.base_cost == 7000
    assert order1.discount == 1750
    assert order1.payable == 5250

    assert raises(rental_service.rent,(member2, car2, 7 , date(2026, 1, 1)))

    rental_service.add_vehicle(car2)

    order2 =rental_service.rent(member2, car2, 7 , date(2026, 1, 1))

    assert order2.base_cost == 7000
    assert order2.discount == 1050
    assert order2.payable == 5950

    rental_service.add_vehicle(car3)
    
    order3 =rental_service.rent(member3, car3, 6 , date(2026, 1, 1))

    assert order3.base_cost == 6000
    assert order3.discount == 600
    assert order3.payable == 5400
        
    order4 =rental_service.rent(member4, bike, 3 , date(2026, 1, 1))

    assert order4.base_cost==600
    assert order4.discount ==0
    assert order4.payable ==600

    order5 = rental_service.rent(member1, electric_car,15, date(2026, 1, 1))

    print(order5.return_date)

    rental_service.notify_due_returns()
    print(notifier.sent)




