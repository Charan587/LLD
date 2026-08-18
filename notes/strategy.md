# Strategy

Derived from day 7. Every trace is real output from code that was run.

---

## 1. The problem

Ride-hailing fares. Four ways to price a ride, and **exactly one applies** per ride:

| Algorithm | Fare |
|---|---|
| Per-km | `km × 12` |
| Per-minute | `minutes × 2` |
| Hybrid | `50 + km×10 + min×1` |
| Flat | `500` |

Chosen by ride type — `MINI` → per-km, `AUTO` → per-minute, `SEDAN` → hybrid — and **airport overrides everything**. Then the result is multiplied by surge and floored at ₹60.

Fifteen more algorithms are coming, added by a pricing team who cannot edit the fare service.

---

## 2. Why the obvious design fails

```python
def fare_v1(ride_type, km, minutes, is_airport):
    if is_airport:             base = 500
    elif ride_type == "MINI":  base = km * 12
    elif ride_type == "AUTO":  base = minutes * 2
    elif ride_type == "SEDAN": base = 50 + km*10 + minutes*1
    else: raise ValueError("unknown type")
    return base
```

```
ATTEMPT 1 — if/elif chain
   MINI   10km 25min -> 120
   AUTO   10km 25min -> 50
   SEDAN  10km 25min -> 175
   works.
```

**It produces the right numbers.** The problems are all about what happens next:

**Every new algorithm edits a function that already works.** Nineteen branches, and each edit risks the eighteen that were fine. The pricing team can't ship it — they'd be sending pull requests against your service.

**You can't ask a hypothetical.** *"What would this MINI ride cost under hybrid pricing?"* — there's no way to express that. The only way in is `ride_type`, so you'd have to lie about the ride to get the answer. That kills A/B testing, quote comparison, and the "swap the algorithm at runtime" requirement outright.

**You can't test the algorithm alone.** `fare_v1` is one function, so testing hybrid pricing means going through the type dispatch. When one branch is wrong you find out through the front door.

**The dispatch and the arithmetic are welded together.** *Which* algorithm applies and *how* it computes are two different concerns changing for different reasons — pricing changes the arithmetic, product changes the dispatch.

---

## 3. The pattern

> **Strategy** — a family of interchangeable algorithms behind one interface, selected at runtime.

**What varies:** how a fare is computed.
**What stays the same:** that a fare *is* computed, then surged, then floored.

That two-line phrasing is worth memorising, because "what varies / what stays the same" is the question that finds Strategy in a problem statement.

### The shape

```python
class FareAlgorithm(Protocol):
    name: str
    def base_fare(self, ride: Ride) -> float: ...
```

One class per algorithm, all with the same signature, held in a registry:

```python
BY_TYPE = {"MINI": PerKm(12), "AUTO": PerMinute(2), "SEDAN": Hybrid(50,10,1)}
```

---

## 4. Dry run of the fixed design

```
ATTEMPT 2 — one object per algorithm
   the SAME ride, priced four ways, without touching the ride:
     Per-km      base 120     quote 120.0
     Per-minute  base 50      quote 60
     Hybrid      base 175     quote 175.0
     Flat        base 500     quote 500.0
```

Four fares for one ride object. In the if/elif version this line cannot be written.

```
   raw vs final — the algorithm never sees surge or the floor:
     PER_MIN.base_fare(ride)      -> 50
     svc(surge=1.0).quote(...)    -> 60     <- floored to 60
     svc(surge=1.5).quote(...)    -> 75.0   <- surge lifts it past the floor
```

```
   algorithm 16 added — new class + one dict row, FareService untouched:
     SUV 10km -> 190.0
```

---

## 5. The boundary — the part people get wrong

**The strategy computes its own number and nothing else.**

Surge and the ₹60 floor belong to the *context* (the service), not to the algorithm. Three reasons, and the third is the one that bites:

1. You can't test the raw fare if the floor is baked in — `50` and `60` become indistinguishable.
2. All 19 algorithms would each have to remember to apply surge and the floor. Nineteen chances to forget.
3. **A bug hides inside a passing test.** Day 7's per-minute algorithm mistakenly used `km` instead of `minutes`: `5 × 2 = 10`, floored to 60. The assert expected 60 and passed — but for the wrong reason. The right answer was 60 because `30 × 2 = 60` *is* the minimum, not because it was floored.

That's why the result object carries `minimum_applied`:

```python
@dataclass(frozen=True)
class Fare:
    algorithm_name: str
    base_fare: float
    surge: float
    minimum_applied: bool     # separates "floored to 60" from "is exactly 60"
    total: float
```

**A bare float can't tell you which of two paths produced it.** When two different routes give the same number, return the route as well.

---

## 6. Strategy vs the patterns next to it

| | |
|---|---|
| **Strategy** | one of N algorithms does the job. Swappable. |
| **A list of rules, all applied** | day 3's discounts and day 6's pricing — *every* rule contributes and you sum them. Same class shape, different composition. Not Strategy. |
| **Decorator** | wrap an algorithm to add behaviour, and the wrapper is still the same interface. A waiting charge on top of a fare. |
| **Factory Method** | *creating* the strategy, not being one. `algorithm_for(ride)` is a factory; `PerKm` is the strategy. |

Days 3, 6 and 7 all use one class per rule with a uniform method — the difference is only whether you pick one or sum them all. **Recognise the shape, then ask how they compose.**

---

## 7. Strategy vs plain functions

In Python a strategy can be a function:

```python
BY_TYPE = {"MINI": lambda r: r.km * 12, "AUTO": lambda r: r.minutes * 2}
```

Legitimate, and shorter. Take a class when the strategy needs **configuration** (`PerKm(12)` vs `PerKm(15)` — same code, different rate), a **name** for the receipt, or more than one method. Take a function when it's one line with nothing to configure.

Day 7 wanted classes: the rates are configuration, and the breakdown needs `algorithm.name`.

---

## 8. Bug list

- **An `if/elif` on a type code that selects a calculation.** The signature smell. Every one is a Strategy waiting to be extracted.
- **The strategy knowing about the context's rules** — surge, floors, caps, tax. If it does, you can't test it alone.
- **Non-uniform signatures.** `a.base_fare(ride)` and `b.base_fare(ride, is_member)` cannot be called from the same loop. Anything a strategy might need rides on the single argument.
- **Returning a bare number when two paths produce the same one.** Return an object that says which path.
- **Selection logic inside the strategy** — an algorithm shouldn't decide whether it applies; then something still has to pick among the ones that say yes.
- **Selection logic inside the data** — `Ride` shouldn't know all sixteen algorithms exist.
- **Precedence by statement order.** "Airport beats type" should read as one explicit branch in a selector, not as which `if` happens to come first.
- **Mutable context state shared across calls.** Surge as an attribute on a long-lived service means a quote shown at 09:00 and charged at 09:05 disagree with no record why. Pass it per call, or inject a provider.

---

## 9. Saying it in an interview

> "Each way of pricing a ride is its own class behind one `base_fare(ride)` interface, and the service picks one at runtime by ride type, with airport as an explicit override.
>
> That's **Strategy** — what varies is how the fare is computed, what stays the same is that a fare gets computed, then surged, then floored.
>
> The boundary I'd point at: the algorithms know nothing about surge or the minimum. That's the service's job, so I can test a raw fare on its own, and the fifteen new algorithms your pricing team adds can't forget to apply the floor.
>
> It gives me **Open/Closed** — algorithm sixteen is a new class and one registry row, and the service never changes."
