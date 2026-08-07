# Day 1 Review — Hotel Room Booking (Python)

Reviewed 2026-07-29. Your submission is preserved verbatim as `solution.submitted.py`.
Java not submitted — this review covers Python only.

## Verdict

`python3 solution.py` → **exit 0, no output, no asserts.** The `__main__` block adds three rooms and stops mid-line. So the first thing to say: this was never actually tested. Everything below I found by driving your `Hotel` class myself.

Here is what your code really does, run against the cases the problem statement listed as mandatory:

```
1. normal booking 1->5 : (True, 'Room booked successfully')
2. exact overlap 1->5  : (False, 'Room is not available')
3. inside 2->4         : (False, 'Room is not available')
4. RIGHT overlap 3->8  : (True, 'Room booked successfully')   <-- should be REJECTED
5. back-to-back 5->7   : (False, 'Room is not available')     <-- should be ACCEPTED
6. find_available 1->5 : [102, 103]
7. bad range 5->1      : (True, 'Room booked successfully')   <-- should be REJECTED
8. missing room 999    : (False, 'Room not found')
9. price nights=1      : CRASH -> TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'
10. price 1->5         : (400, 'Price of the room is 400')
```

After case 4, room 101 holds `[(Aug 1, Aug 5), (Aug 3, Aug 8)]` — **the same room is sold to two guests for Aug 3-5.** In a real hotel system that's the bug that puts two families in one room at 11pm.

## Score

| Axis | Score | Why |
|---|---|---|
| Correctness | **1** / 5 | Silent double-booking, back-to-back rejected, no date validation, pricing crashes, zero asserts |
| Extensibility | **1** / 5 | No `Room` object, so room type — a stated requirement — cannot be built without restructuring |
| SOLID | **1** / 5 | One class owns storage, overlap logic, booking, and pricing |
| Readability | **2** / 5 | Reads fine locally; `availability` holds bookings, duplicated branches, unused param |
| Communication | **1** / 5 | No stated assumptions, no asserts, unfinished main |

Baseline set. This is day 1 of 45 and the number that matters is the delta from here, not the number itself. But I'm not going to soften it: submitted as-is, this fails a machine-coding round on the overlap bug alone.

---

## The three real bugs

### 1. Your overlap check misses right-hand overlap

You wrote three conditions. Existing booking `[bf, bt)`, new booking `[f, t)`:

```python
if   f >= bf and t <= bt:   # new is inside existing        ✓
elif f <= bf and t >= bt:   # new contains existing         ✓
elif f <= bf and t >= bf:   # new starts before existing    ✓ (but see bug 2)
```

Now walk `existing = [Aug 1, Aug 10)`, `new = [Aug 5, Aug 15)`:

- cond 1: `5 >= 1` ✓ but `15 <= 10` ✗
- cond 2: `5 <= 1` ✗
- cond 3: `5 <= 1` ✗

Nothing fires. Booked. **The case where the new booking starts inside the existing one and ends after it has no condition at all.**

This is the classic interval trap, and the reason it's a trap is that enumerating cases *feels* complete. Four overlap orientations exist; you covered three. The fix is to stop enumerating:

```python
def overlaps(a_in, a_out, b_in, b_out):
    return a_in < b_out and b_in < a_out
```

Two comparisons, all four orientations, no cases to forget. Derive it by negation — ranges *miss* each other only when one ends at or before the other starts (`a_out <= b_in or b_out <= a_in`); overlap is just that inverted. **Memorise this one.** It comes back in calendars, rate limiters, and meeting schedulers, three of which are on your day 27-40 list.

### 2. `>=` where you needed `>` kills back-to-back

The problem statement called this out explicitly: `[check_in, check_out)`, checkout day not occupied, 1st→3rd and 3rd→5th must both succeed. Your condition 3 is `t >= bf`. When `t == bf` — new checkout exactly equals existing check-in, the legal case — it returns unavailable.

Interesting detail: the *mirror* case works. Booking `[bt, ...)`, starting exactly on an existing checkout, is correctly allowed. So your code is asymmetric — legal at one boundary, illegal at the other. That asymmetry is the tell that the conditions were reasoned case-by-case rather than derived. The strict `<` in `overlaps()` above handles both ends identically.

### 3. `check_out > check_in` is never validated

Rule 3 in the spec. `book_room(102, Aug 5, Aug 1)` returns success and stores a negative-length booking. It'll price at negative money, and any overlap check against it behaves nonsensically. Guard at the boundary where bookings enter the system.

---

## The design problem, which matters more than the bugs

Bugs are cheap to fix. This isn't:

```python
class Hotel:
    def __init__(self, price):
        self.price = price
```

**One price for the entire hotel.** But the spec says each room has a type *and* a price per night, and requirement 5 is "find all available rooms **of a given type**". Your `find_available_rooms(from, to)` has no type parameter — it can't, because a room in your model is a bare integer. There's nowhere to hang a type or a price.

That's the whole lesson of day 1. Not the interval bug — the missing noun. The problem statement contains the words *room*, *guest*, *booking*, and *room type*, and your model contains a list of ints and a dict. When a requirement had nowhere to live, it silently got dropped rather than becoming a compile error or an obviously missing method.

**Rule to take forward: read the problem statement and underline every noun. Each one is a candidate class. You don't have to promote all of them — but dropping one should be a decision you made, not one you didn't notice.** Here, `Room` and `Booking` both needed to exist. `Guest` arguably could have stayed a string, and that would have been a fine call to defend.

Two consequences followed automatically from the missing nouns:

- **`availability` is misnamed** — it stores bookings, i.e. *un*availability. Name things after what they hold.
- **`price_of_room` has no idea which room.** It takes `from_date`, `to_date`, `nights` and reads `self.price`. The `nights > 1` branch is also off by one — `nights=1` falls through to the date branch with `None` dates and raises `TypeError`. A method with two mutually exclusive ways to say the same thing is a signal the data model is wrong: price belongs to a booking, and a booking already knows its own dates, so neither parameter should exist.

## Smaller things

```python
if room not in self.availability:
    self.availability[room] = []
    self.availability[room].append((from_date, to_date))
else:
    self.availability[room].append((from_date, to_date))
```

Both branches end in the same append. `self.availability.setdefault(room, []).append(...)`, or a `defaultdict(list)`.

**`(bool, str)` tuple returns everywhere.** Defensible — it's Go-style and it avoids exceptions. But you never once used the string: every caller does `available, message = ...` and drops `message`. If nobody consumes the second element, it's ceremony. In Python, raise for the exceptional path; the caller can catch it if they care, and can ignore it if they don't. A tuple return means *every* caller must remember to check, and one forgotten check is a silent bug.

**Cancel-by-`(room, from, to)` is a legitimate call** — but state it. It means a guest can't be told "your booking reference is 47", and two guests can never hold identical dates on one room (fine here, since overlap forbids it). An ID is what a real system does, and it makes cancel `O(1)`.

---

## The rewrite

`rewrite.py` in this folder. Verified: `python3 rewrite.py` → `all checks passed`.

Read it as a diff against your thinking, not as code to memorise. The shape of the change:

| Yours | Rewrite | Why |
|---|---|---|
| `rooms = [1, 2, 3]` | `Room(number, room_type, price_per_night)` | Gives type and price somewhere to live; unlocks requirement 5 |
| `availability: dict[room, list[tuple]]` | `Booking` dataclass, `dict[id, Booking]` | A booking is a thing with identity, not an anonymous tuple |
| 3 inline overlap conditions | one `overlaps()` function | Two comparisons, no cases to miss, testable alone |
| `self.price` on the hotel | `price_per_night` on the room | Matches the spec |
| `return (False, "message")` | `raise ValueError(...)` | Callers can't silently skip the check |
| no validation | `_validate()` at the boundary | One place where bad dates are rejected |

Note the assert block at the bottom of `rewrite.py` — that's the actual deliverable of a machine-coding round. Eleven asserts covering all four overlap orientations, both boundary cases, bad input, and cancel. **Write these first next time.** If you'd written the back-to-back assert before the implementation, bug 2 would have been caught in thirty seconds.

Also note the size: the rewrite does strictly more than yours — room types, per-room pricing, booking IDs, validation — in comparable lines. Correct modelling usually shrinks code. When a design forces you to write more, that's evidence against the design.

---

## Grill

Answer these in chat. I'll push back on hand-waving.

1. **Derive the overlap condition yourself.** Don't quote mine. Two ranges `[a_in, a_out)` and `[b_in, b_out)` — start from "when do they *not* overlap?" and negate it. Show your reasoning.
so here when they do not overlap is , when from date less than booking from  date and to date is also less than booking from date , from date is greater than booking to date or equal to booking to date and to date is grater than booking to date. negation means . to_date < = booking from date and from_date >= booking to date, also explain me your logic with an example

2. Your code stores bookings as a list per room and scans it linearly. A hotel with 500 rooms over 2 years is fine. **Now it's Airbnb — 7 million listings.** Where does the linear scan break, and what would you reach for instead? You don't need the perfect answer; I want to see you reason about the access pattern. 

what i will do is we will use booking id in as it gets us the booking lets assume that and using set or binary search which we assumen it will be sorted order

3. You used `(bool, str)` returns. I claimed nobody consumed the string. **Make the counter-argument** — when *is* a result tuple better than an exception? There's a real case for it.
counter argument may be why we want - may be if some one directly calls it and we will give exact message 

4. `Room` in my rewrite is `frozen=True` — immutable. But a hotel changes prices in high season. **Does frozen become wrong?** How would you handle a price change without mutating `Room`, and why might that be better than just making it mutable?
we will over write it per hotel for the specifci room type we will store dict rom_type and price . it will override the class room type price . so that we can handle specifc hotel changes as discounted price and eveything according to hotel

5. Requirement 5 says "find all available rooms of a given type". Suppose next week we need "available rooms under ₹3000 with a balcony, sorted by price". **How much of `rewrite.py` has to change, and which principle is that testing?** (You'll meet this one properly on day 3.)
it is testing single responsibility priciple and it should be extenetd instead of changing lready writen code because it needs testing all features realted to that class . we need to rewrite or add a logic isnide avaloable room to find by price also 

6. You dropped `Guest` entirely — my rewrite keeps it as a bare string. **When does that become the wrong call?** Name the specific requirement that would force `Guest` to become a class.
so if we ever need details about guest like addrss proof , name . or adding a ,ain guest and number of persons with him and their address like that.


Now i want one mre thing tell me how to approach the problems like initial steps to take and what to observe and what to note down how to plan

---

## Carrying forward

Recorded in `../PROGRESS.md`:

- **Write asserts before implementing.** Non-negotiable from day 2. Your main block was empty; that's what let three bugs through.
- **Underline the nouns in the problem statement.** Each is a candidate class. Dropping one must be a decision.
- **Derive boundary conditions, don't enumerate cases.** Enumeration feels complete and isn't.
- Watch for **`>=` vs `>` on half-open ranges** — it'll recur in Rate Limiter and Meeting Scheduler.

Java for day 1 is still open. Worth doing — the `Room`/`Booking` modelling lesson lands harder in a language that makes you declare types up front. Say **java done** when it's in, or **next** to move to day 2.
