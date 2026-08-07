"""Day 6 — interview-grade rewrite.

Your rent path is kept — discounts as classes returning amounts, terms captured
on the Order, clock/notifier injected. All of that was right.

Changed: the return path (fee vs total, cap on base, due date preserved),
Bike/Car as data, an Invoice, and the eleven asserts that were never written.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Protocol, runtime_checkable

LATE_FEE_PER_DAY = 500


@runtime_checkable
class Clock(Protocol):
    def today(self) -> date: ...


@runtime_checkable
class Notifier(Protocol):
    def send(self, to: str, message: str) -> None: ...


class SystemClock:
    def today(self) -> date: return date.today()


class FixedClock:
    def __init__(self, fixed: date): self.fixed = fixed
    def today(self) -> date: return self.fixed


class FakeNotifier:
    def __init__(self): self.sent: list[tuple[str, str]] = []
    def send(self, to: str, message: str) -> None: self.sent.append((to, message))


@runtime_checkable
class Chargeable(Protocol):
    def charge(self) -> None: ...


@runtime_checkable
class Loadable(Protocol):
    def load(self, kg: float) -> None: ...


class Vehicle:
    """Bike and Car differ only by a number — instances, not subclasses."""

    def __init__(self, name: str, rate_per_day: float):
        self.name = name
        self.rate_per_day = rate_per_day


class ElectricVehicle(Vehicle):
    def __init__(self, name, rate_per_day, battery_kwh: float = 100):
        super().__init__(name, rate_per_day)
        self.battery_kwh = battery_kwh
        self.charge_level = 0.0

    def charge(self) -> None:
        self.charge_level = self.battery_kwh


class CargoVehicle(Vehicle):
    def __init__(self, name, rate_per_day, max_kg: float = 1000):
        super().__init__(name, rate_per_day)
        self.max_kg = max_kg
        self.loaded_kg = 0.0

    def load(self, kg: float) -> None:
        if kg <= 0:
            raise ValueError("cargo must be positive")
        if self.loaded_kg + kg > self.max_kg:
            raise ValueError(f"exceeds capacity: {self.loaded_kg + kg} > {self.max_kg}")
        self.loaded_kg += kg

    def unload(self) -> None:
        self.loaded_kg = 0.0


class RefrigeratedTruck(CargoVehicle):
    """From the 'later' list — picks up BOTH capabilities, no hierarchy change."""

    def __init__(self, name, rate_per_day, max_kg=1000, battery_kwh=200):
        super().__init__(name, rate_per_day, max_kg)
        self.battery_kwh = battery_kwh
        self.charge_level = 0.0

    def charge(self) -> None:
        self.charge_level = self.battery_kwh


@dataclass(frozen=True)
class Customer:
    name: str
    email: str
    is_member: bool = False


@dataclass(frozen=True)
class Rental:
    """Terms captured at rent time. A later rate change cannot reach in here."""
    vehicle: Vehicle
    customer: Customer
    started_on: date
    due_on: date
    days: int
    base_cost: float
    breakdown: tuple[tuple[str, float], ...]
    returned_on: date | None = None
    late_fee: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.returned_on is None

    @property
    def total_discount(self) -> float:
        return sum(a for _, a in self.breakdown)

    @property
    def payable(self) -> float:
        return self.base_cost - self.total_discount + self.late_fee


class DiscountRule(Protocol):
    name: str
    def amount_off(self, rental: Rental) -> float: ...


@dataclass(frozen=True)
class LongRentalDiscount:
    percent: float = 15
    minimum_days: int = 7
    name: str = "Long rental"

    def amount_off(self, rental: Rental) -> float:
        if rental.days < self.minimum_days:          # 7 qualifies, 6 does not
            return 0.0
        return rental.base_cost * self.percent / 100


@dataclass(frozen=True)
class LoyaltyDiscount:
    percent: float = 10
    name: str = "Loyalty"

    def amount_off(self, rental: Rental) -> float:
        return rental.base_cost * self.percent / 100 if rental.customer.is_member else 0.0


class RentalService:
    def __init__(self, clock: Clock, notifier: Notifier,
                 rules: list[DiscountRule], late_fee_per_day: float = LATE_FEE_PER_DAY,
                 reminder_days_before: int = 1):
        self.clock = clock
        self.notifier = notifier
        self.rules = rules
        self.late_fee_per_day = late_fee_per_day
        self.reminder_days_before = reminder_days_before
        self.rentals: list[Rental] = []

    def open_rental_for(self, vehicle: Vehicle) -> Rental | None:
        return next((r for r in self.rentals if r.vehicle is vehicle and r.is_open), None)

    def rent(self, vehicle: Vehicle, customer: Customer, start: date, days: int) -> Rental:
        if days < 1:
            raise ValueError(f"days must be at least 1, got {days}")
        if self.open_rental_for(vehicle) is not None:
            raise ValueError(f"{vehicle.name} is already rented")

        base = vehicle.rate_per_day * days
        draft = Rental(vehicle, customer, start, start + timedelta(days=days),
                       days, base, ())
        breakdown = tuple((r.name, r.amount_off(draft)) for r in self.rules)
        rental = Rental(vehicle, customer, start, draft.due_on, days, base, breakdown)
        self.rentals.append(rental)
        return rental

    def return_vehicle(self, vehicle: Vehicle, on: date) -> float:
        rental = self.open_rental_for(vehicle)
        if rental is None:
            raise ValueError(f"{vehicle.name} is not rented")
        days_late = max(0, (on - rental.due_on).days)
        fee = min(days_late * self.late_fee_per_day, rental.base_cost)   # cap on BASE
        i = self.rentals.index(rental)
        self.rentals[i] = replace_rental(rental, returned_on=on, late_fee=fee)
        return fee                                                       # the FEE, not the total

    def send_due_reminders(self) -> None:
        target = self.clock.today() + timedelta(days=self.reminder_days_before)
        for r in self.rentals:
            if r.is_open and r.due_on == target:
                self.notifier.send(r.customer.email,
                                   f"{r.vehicle.name} is due back on {r.due_on}")


def replace_rental(r: Rental, **changes) -> Rental:
    from dataclasses import replace
    return replace(r, **changes)


def text_invoice(rental: Rental) -> str:
    """Separate from the money logic. A JSON version is another function."""
    lines = [f"{rental.vehicle.name} x {rental.days} days",
             f"Base  {rental.base_cost:.2f}"]
    lines += [f"{name}  -{amt:.2f}" for name, amt in rental.breakdown if amt]
    if rental.late_fee:
        lines.append(f"Late fee  {rental.late_fee:.2f}")
    lines.append(f"Payable  {rental.payable:.2f}")
    return "\n".join(lines)


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    RULES = [LongRentalDiscount(), LoyaltyDiscount()]
    ALICE = Customer("Alice", "alice@x.com", is_member=True)
    BOB = Customer("Bob", "bob@x.com", is_member=False)
    MAR1 = date(2026, 3, 1)

    def setup(today=date(2026, 3, 7)):
        n = FakeNotifier()
        return RentalService(FixedClock(today), n, RULES), n

    def car(): return Vehicle("Car", 1000)
    def bike(): return Vehicle("Bike", 200)

    # 1 — member, car, 7 days
    svc, _ = setup()
    r = svc.rent(car(), ALICE, MAR1, 7)
    assert r.base_cost == 7000
    assert r.total_discount == 1750
    assert r.payable == 5250

    # 2 — non-member
    svc, _ = setup()
    r = svc.rent(car(), BOB, MAR1, 7)
    assert r.total_discount == 1050 and r.payable == 5950

    # 3 — 6 days: the boundary. 7 qualifies, 6 does not.
    svc, _ = setup()
    r = svc.rent(car(), ALICE, MAR1, 6)
    assert r.base_cost == 6000
    assert dict(r.breakdown)["Long rental"] == 0
    assert r.total_discount == 600 and r.payable == 5400

    # 4 — bike, non-member, no discounts
    svc, _ = setup()
    r = svc.rent(bike(), BOB, MAR1, 3)
    assert r.base_cost == 600 and r.total_discount == 0 and r.payable == 600

    # 5 — due date
    assert r.due_on == date(2026, 3, 4)
    svc, _ = setup()
    assert svc.rent(car(), ALICE, MAR1, 7).due_on == date(2026, 3, 8)

    # 6, 7, 8 — late fees, including both boundaries
    for on, expected in [(date(2026, 3, 8), 0), (date(2026, 3, 11), 1500), (date(2026, 6, 1), 7000)]:
        svc, _ = setup()
        c = car()
        svc.rent(c, ALICE, MAR1, 7)
        assert svc.return_vehicle(c, on) == expected, (on, expected)

    # 9 — already rented, and the first rental survives the attempt
    svc, _ = setup()
    c = car()
    first = svc.rent(c, ALICE, MAR1, 7)
    assert raises(svc.rent, c, BOB, MAR1, 3)
    assert len(svc.rentals) == 1
    assert svc.rentals[0].customer == ALICE and svc.rentals[0].base_cost == 7000

    # 10 — after return, rentable again
    svc.return_vehicle(c, date(2026, 3, 8))
    assert svc.rent(c, BOB, date(2026, 3, 9), 2).base_cost == 2000

    # 11 — days must be at least 1
    svc, _ = setup()
    assert raises(svc.rent, car(), ALICE, MAR1, 0)
    assert raises(svc.rent, car(), ALICE, MAR1, -1)
    assert svc.rentals == []

    # 12 — charging; a Bike has NO charge method
    ev = ElectricVehicle("Electric Car", 1200, battery_kwh=100)
    ev.charge()
    assert ev.charge_level == 100
    assert isinstance(ev, Chargeable)
    assert not hasattr(bike(), "charge")
    assert not isinstance(bike(), Chargeable)

    # 13 — loading; a Car has NO load method
    t = CargoVehicle("Truck", 2500, max_kg=1000)
    t.load(800)
    assert t.loaded_kg == 800
    assert raises(t.load, 1200)
    assert t.loaded_kg == 800
    assert not hasattr(car(), "load")
    assert not isinstance(car(), Loadable)

    # the refrigerated truck from the 'later' list: both capabilities, no rework
    rt = RefrigeratedTruck("Reefer", 3000)
    assert isinstance(rt, Loadable) and isinstance(rt, Chargeable)

    # 14 — reminder fires on exactly one day
    svc, n = setup(today=date(2026, 3, 7))
    svc.rent(car(), ALICE, MAR1, 7)                      # due 2026-03-08
    svc.send_due_reminders()
    assert n.sent == [("alice@x.com", "Car is due back on 2026-03-08")]

    for day in [date(2026, 3, 6), date(2026, 3, 8), date(2026, 3, 20)]:
        svc, n = setup(today=day)
        svc.rent(car(), ALICE, MAR1, 7)
        svc.send_due_reminders()
        assert n.sent == [], (day, n.sent)

    # a returned vehicle gets no reminder
    svc, n = setup(today=date(2026, 3, 7))
    c = car()
    svc.rent(c, ALICE, MAR1, 7)
    svc.return_vehicle(c, date(2026, 3, 3))
    svc.send_due_reminders()
    assert n.sent == []

    # 15 — a rate change must not reprice an in-progress rental
    svc, _ = setup()
    c = car()
    r = svc.rent(c, ALICE, MAR1, 7)
    c.rate_per_day = 1500
    assert r.base_cost == 7000 and r.payable == 5250
    assert svc.rent(bike(), ALICE, MAR1, 7).base_cost == 1400   # new rentals unaffected

    # invoice is separate from the money logic
    assert "Payable  5250.00" in text_invoice(r)
    assert "Long rental  -1050.00" in text_invoice(r)

    print("all checks passed")
