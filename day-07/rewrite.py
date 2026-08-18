"""Day 7 — Ride Fare Estimation. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "Four ways to price a ride, exactly one applies per ride, chosen by ride
    type with airport overriding. Then surge, then a minimum fare floor."

2. CLARIFYING QUESTIONS
   - "Does surge apply before or after the minimum?" -> changes the answer
   - "Is the minimum global, or per city?"
   - "Should the algorithm know about surge, or is that the service's job?"
     -> asking this is how you show you've spotted the boundary

3. HOW I FOUND THE CLASSES
   Nouns: ride, distance, duration, ride type, fare, surge, minimum, receipt.
     ride      -> data                                  -> Ride (frozen)
     ride type -> fixed small set                       -> enum
     the four ways to compute a fare -> ONE CLASS EACH, uniform signature
     the result -> not a float; it needs the algorithm name and whether the
                   minimum kicked in                    -> Fare value object

   THE BOUNDARY, said out loud: an algorithm computes ITS OWN number and
   nothing else. Surge and the floor belong to the service. If the algorithm
   knew about them, I couldn't test the raw fare, and every one of the 15
   future algorithms would have to remember to apply them.

4. ASSUMPTIONS
   - Airport beats ride type; precedence is explicit, not statement order.
   - Surge multiplies the base fare, then the floor applies.
   - is_airport lives on the Ride, not passed alongside it.

5. THE DESIGN I REJECTED
   "An if/elif on ride type inside the fare service. Fifteen more algorithms
    means fifteen more branches in a method that already works, and the
    pricing team can't edit my service anyway."

6. THE DESIGN + PATTERN NAME
   "STRATEGY — a family of interchangeable algorithms behind one interface,
    selected at runtime. What varies is how a fare is computed; what stays
    the same is that a fare is computed, then surged, then floored."
   "It delivers OPEN/CLOSED: algorithm 16 is a new class and one registry
    row, and FareService never changes."

7. LIMITS I'D VOLUNTEER
   - "Surge as a mutable attribute on the service is shared state — a quote
      shown at 09:00 and charged at 09:05 would disagree with no record why.
      I'd pass it per quote, or inject a SurgeProvider."
   - "A waiting charge isn't a new Strategy — it's additive. That wants a
      list of surcharges, or a Decorator if it must wrap the algorithm."
   - "Per-city minimums are a dict on the service, not a new algorithm."

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

MINIMUM_FARE = 60


class RideType(Enum):
    MINI = "MINI"
    SEDAN = "SEDAN"
    SUV = "SUV"
    AUTO = "AUTO"


@dataclass(frozen=True)
class Ride:
    km: float                 # annotation, not assignment — see REVIEW
    minutes: float
    ride_type: RideType
    is_airport: bool = False


class FareAlgorithm(Protocol):
    name: str
    def base_fare(self, ride: Ride) -> float: ...


@dataclass(frozen=True)
class PerKm:
    rate: float
    name: str = "Per-km"

    def base_fare(self, ride: Ride) -> float:
        return ride.km * self.rate


@dataclass(frozen=True)
class PerMinute:
    rate: float
    name: str = "Per-minute"

    def base_fare(self, ride: Ride) -> float:
        return ride.minutes * self.rate          # minutes, not km


@dataclass(frozen=True)
class Hybrid:
    base: float
    per_km: float
    per_minute: float
    name: str = "Hybrid"

    def base_fare(self, ride: Ride) -> float:
        return self.base + ride.km * self.per_km + ride.minutes * self.per_minute


@dataclass(frozen=True)
class FlatRate:
    amount: float
    name: str = "Flat"

    def base_fare(self, ride: Ride) -> float:
        return self.amount


@dataclass(frozen=True)
class Fare:
    """The computed result. A receipt needs nothing else."""
    algorithm_name: str
    base_fare: float
    surge: float
    minimum_applied: bool
    total: float


class FareService:
    def __init__(self, by_type: dict[RideType, FareAlgorithm],
                 airport: FareAlgorithm,
                 surge: float = 1.0,
                 minimum_fare: float = MINIMUM_FARE):
        self.by_type = by_type
        self.airport = airport
        self.surge = surge
        self.minimum_fare = minimum_fare

    def algorithm_for(self, ride: Ride) -> FareAlgorithm:
        if ride.is_airport:                       # airport wins — precedence is explicit
            return self.airport
        return self.by_type[ride.ride_type]

    def quote(self, ride: Ride, algorithm: FareAlgorithm | None = None) -> Fare:
        algo = algorithm if algorithm is not None else self.algorithm_for(ride)
        base = algo.base_fare(ride)               # raw: no surge, no floor
        surged = base * self.surge
        total = max(surged, self.minimum_fare)
        return Fare(algo.name, base, self.surge, total > surged, total)


def fare_breakdown(fare: Fare) -> str:
    lines = [f"Algorithm  {fare.algorithm_name}",
             f"Base fare  {fare.base_fare:.2f}",
             f"Surge      x{fare.surge}"]
    if fare.minimum_applied:
        lines.append(f"Minimum fare applied")
    lines.append(f"Total      {fare.total:.2f}")
    return "\n".join(lines)


if __name__ == "__main__":
    PER_KM = PerKm(12)
    PER_MIN = PerMinute(2)
    HYBRID = Hybrid(50, 10, 1)
    FLAT = FlatRate(500)

    def service(surge=1.0):
        return FareService(
            {RideType.MINI: PER_KM, RideType.SEDAN: HYBRID,
             RideType.SUV: HYBRID, RideType.AUTO: PER_MIN},
            airport=FLAT, surge=surge)

    ride_a = Ride(10, 25, RideType.AUTO)
    ride_b = Ride(5, 30, RideType.AUTO)

    # 1-4 — base fares
    assert PER_KM.base_fare(ride_a) == 120
    assert PER_MIN.base_fare(ride_a) == 50
    assert HYBRID.base_fare(ride_a) == 175
    assert FLAT.base_fare(ride_a) == 500

    # 5 — the algorithm knows nothing about surge or the floor
    svc = service(surge=1.5)
    assert PER_MIN.base_fare(ride_a) == 50          # not 60, not 75
    assert svc.quote(ride_a, PER_MIN).base_fare == 50

    # 6 — floored
    svc = service()
    q = svc.quote(ride_a)                            # AUTO -> per-minute -> 50
    assert q.total == 60 and q.minimum_applied

    # 7 — exactly the minimum: not floored, not bumped
    q = service().quote(ride_b)                      # 30 min x 2 = 60
    assert q.base_fare == 60
    assert q.total == 60 and not q.minimum_applied

    # 8, 9 — surge applies before the floor
    assert service(surge=1.5).quote(ride_a, HYBRID).total == 262.5
    assert service(surge=1.5).quote(ride_a, PER_MIN).total == 75

    # 10 — selection by type
    svc = service()
    assert svc.algorithm_for(Ride(10, 25, RideType.MINI)) is PER_KM
    assert svc.algorithm_for(Ride(10, 25, RideType.SEDAN)) is HYBRID
    assert svc.algorithm_for(Ride(10, 25, RideType.AUTO)) is PER_MIN

    # 11 — airport overrides type
    assert svc.algorithm_for(Ride(10, 25, RideType.MINI, is_airport=True)) is FLAT
    assert svc.quote(Ride(10, 25, RideType.MINI, is_airport=True)).total == 500

    # 12 — swap the algorithm on an existing ride
    ride = Ride(10, 25, RideType.MINI)
    assert svc.quote(ride).total == 120               # per-km
    assert svc.quote(ride, HYBRID).total == 175       # same ride object, different algorithm
    assert svc.quote(ride).total == 120               # and back

    # 13 — breakdown
    text = fare_breakdown(service().quote(ride_a))
    assert "Per-minute" in text and "60.00" in text and "Minimum fare applied" in text

    # algorithm 16 is a new class plus one dict entry — nothing else moves
    @dataclass(frozen=True)
    class NightSurcharge:
        per_km: float
        flat_add: float
        name: str = "Night"
        def base_fare(self, ride: Ride) -> float:
            return ride.km * self.per_km + self.flat_add

    svc.by_type[RideType.SUV] = NightSurcharge(15, 40)
    assert svc.quote(Ride(10, 25, RideType.SUV)).total == 190

    print("all checks passed")
