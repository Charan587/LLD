# Day 7 Review — Ride Fare Estimation (Python)

Reviewed 2026-08-11. Submission preserved as `solution.submitted.py`.

## Verdict

```
$ python3 solution.py
exit: 0
```

**Nothing printed. Because nothing ran.**

```python
if __name__ == "main":      # should be "__main__"
```

One missing pair of underscores, and the entire assert block — every line of it — was skipped. Python imported the file, defined the classes, reached a comparison that was `False`, and exited cleanly.

**`exit 0` is not the same as "tests passed."** Your file has never printed `all test passed`, not once, and the spec asked you to paste the terminal output. The output was empty and it still got submitted.

Behind that guard were four separate bugs, any one of which dies on the first real run.

## Score

| Axis | D3 | D4 | D5 | D6 | D7 | Why |
|---|---|---|---|---|---|---|
| Correctness | 1 | 2 | 2 | 2 | **1** / 5 | Never executed. `Ride` cannot be constructed. Per-minute uses km. Every `Booking.calculate` path raises. |
| Extensibility | 2 | 4 | 4 | 4 | **3** / 5 | Dict-of-algorithms is right; airport handled by an extra parameter rather than off the ride |
| SOLID | 3 | 4 | 4 | 4 | **3** / 5 | Strategy shape correct — algorithms genuinely don't know surge or the floor. `Booking` selects, surges, floors; no breakdown. |
| Readability | 2 | 3 | 3 | 2 | **2** / 5 | `km = int` instead of `km: int`; `algorithm(ride)` where `.calculate` was meant; `min_base_cost` isn't a base cost |
| Communication | 1 | 2 | 3 | 3 | **1** / 5 | Assumptions thin; no rejected design; **the pattern is never named** |

**10 / 25.** Down from 15, and the drop is almost entirely one thing: the file was never run.

---

## What you got right, because it matters

The **Strategy structure is correct**, and it's the thing the day was about:

```python
class Algorithm:
    def calculate(self, ride: Ride): ...
```

Four implementations, one uniform signature, held in a dict, with `Booking` applying surge and the floor. **Requirement 4 — the graded one — is satisfied by design.** Your algorithms genuinely know nothing about surge or the ₹60 minimum. That's the boundary I said I cared about, and you held it.

Algorithm 16 really is a new class plus one dict entry. That part is done.

## The four bugs

### 1. The main guard

Covered above. The fix is one line; the habit is the point. Two defences:

- **Always print at the end, and always look at the output.** `all checks passed` appearing is the signal — not the exit code.
- Better: put a deliberate failure in while developing (`assert False`) and confirm you *see* it. If a broken assert doesn't fail, your tests aren't running.

### 2. `Ride` has no fields

```python
@dataclass(frozen=True)
class Ride:
    km = int          # assignment
    minutes = int
    typeOfVehicle = str
```

```
dataclass fields: []
Ride(10,25,"AUTO") -> TypeError: Ride.__init__() takes 1 positional argument but 4 were given
```

`km = int` **assigns the type object `int` to a class attribute.** `@dataclass` builds `__init__` from *annotations*, and there are none, so it generates a constructor taking nothing. `Ride.km` is literally the `int` class.

```python
km: int           # annotation — dataclass sees a field
km = int          # assignment — dataclass sees nothing
```

Worth knowing because it fails *silently at definition time* and only bites at construction. And note: day 1's `Hotel` had the same `name = str` pattern — it didn't matter there because you weren't using `@dataclass`.

### 3. Per-minute charges by distance

```python
def calculate(self, ride):
    return ride.km * self.per_minute
```

```
2 per_minute.calculate(r1)  -> 20   expected 50   WRONG
```

Copy-paste from `PerKmAlgo` with the rate renamed and the field left behind. Assert 2 catches it in one run.

There's a second-order effect: assert 7 (Ride B, 5 km / 30 min → exactly 60) would have **passed for the wrong reason** — `5 × 2 = 10`, floored to 60. The right answer is 60 because `30 × 2 = 60` *is* the minimum, not because it was floored. That's precisely the boundary the assert existed to check, and the bug would have hidden inside a passing test. My rewrite asserts `minimum_applied` is `False` there, which separates the two.

### 4. `Booking.calculate` never calls the algorithm

```python
return max(algorithm(ride) * self.surge, self.min_base_cost)
```

```
6 booking.calculate(r1) -> TypeError: 'PerMinuteAlgo' object is not callable
```

`algorithm(ride)` tries to *call the instance*. You meant `algorithm.calculate(ride)`. Every path through `calculate` has it, so **no fare could ever be computed** — asserts 6 through 9, all four, on every route.

And a quieter one on the line above:

```python
if algorithm and algorithm in self.algorithms:
```

```
algorithm-in-dict check: False   <-- checks KEYS, which are strings
```

`x in some_dict` tests **keys**. Your keys are `"MINI"`, `"AUTO"`, `"AIRPORT"` — strings. An `Algorithm` instance is never among them, so this is always `False` and the explicit-algorithm argument is **silently ignored**. Asserts 8 and 9 pass an algorithm and it would have been discarded even after the call bug was fixed.

If you want to check membership among the *values*: `algorithm in self.algorithms.values()`. But you don't need the check at all — if a caller hands you an algorithm, use it.

## Airport is passed in, not read off the ride

```python
def calculate(self, ride, algorithm=None, type_of_run=None):
    if type_of_run == "AIRPORT":
```

My spec says a ride *has* whether it's an airport run. Yours makes the caller remember to pass a magic string on the side. Two costs: every call site must know, and `Ride(10, 25, "MINI")` for an airport trip is now silently wrong rather than impossible.

Put it on the ride, and precedence becomes one readable method:

```python
def algorithm_for(self, ride):
    if ride.is_airport:
        return self.airport
    return self.by_type[ride.ride_type]
```

Two lines, and "airport beats type" is visible rather than implied by statement order.

## The asserts

Roughly nine of thirteen attempted — and since none executed, the count is academic. Not attempted: **10** (selection by type), **11** (airport override), **12** (swap on an existing ride), **13** (breakdown).

Assert 12 was the one carrying today's twist. Passing an algorithm as an argument on separate calls isn't quite the same as *swapping* — my rewrite asserts the same ride object quoted three times, per-km then hybrid then per-km again.

**W10 has reopened.** You closed it on day 4 and ran clean on days 4, 5 and 6. This is the first non-running submission since day 3, and the cause isn't carelessness about testing — you wrote the asserts. It's that a silent success looked identical to a real one.

## Not named

The word **Strategy** doesn't appear in your file. Requirement 3 asked for the pattern name, what varies, what stays the same, and one SOLID principle.

> **Strategy** — a family of interchangeable algorithms behind one interface, selected at runtime.
> **Varies:** how a fare is computed. **Stays the same:** that a fare *is* computed, then surged, then floored.
> **Delivers Open/Closed** — fifteen more algorithms are fifteen new classes and zero edits to `FareService`.

You built it correctly and didn't say its name, which is the fifth time now. In a round, the interviewer hears the name or assumes you arrived by accident.

## The rewrite

`rewrite.py`, verified `all checks passed`. Your structure kept: algorithm base, four implementations, uniform signature, service owns surge and floor. Changed: the four bugs, `is_airport` on the ride, a `Fare` result object, a separate `fare_breakdown`, and all thirteen asserts.

The last block adds a sixteenth algorithm as a nested class plus one dict assignment — proving the OCP claim rather than asserting it.

## Grill

1. `algorithm in self.algorithms` was always `False`, so the code silently ignored an argument. **Name the general category of bug** where a wrong answer is worse than a crash, and give one more example from your own past six days.
2. My `quote()` returns a `Fare` object; yours returns a float. **Name two things** the object buys — one of which made assert 7 possible.
3. `Ride` is frozen in my rewrite. Requirement 6 says the algorithm can be swapped at runtime. **Is that a contradiction?** What exactly is being swapped?
4. Requirement: a *per-city* minimum fare. **Where does it go** — on the algorithm, on the service, on the ride, or somewhere else? Justify with a principle.
5. My `FareService` holds `surge` as a mutable attribute. **Argue that's wrong**, and say what you'd pass instead.
6. A waiting charge is added on top of the fare. **Is that a new Strategy, or something else?** If something else, name the pattern it wants.
