# How to Approach an LLD Problem

Use this every day. It's a 45-minute machine-coding round budget; adjust proportionally for longer.

The single biggest mistake beginners make is **writing code first**. Twelve minutes of thinking saves thirty of rewriting. The steps below front-load the thinking deliberately.

---

## Minute 0-5 — Read and interrogate

Read the statement twice. Second pass with a pen.

### Underline every noun
Each noun is a **candidate class**. Not every one becomes a class, but dropping one must be a *decision*, not an oversight.

> "A **hotel** has **rooms**. Each **room** has a **number**, a **type**, and a **price per night**. **Guests** book rooms for a **date range**."

Nouns: Hotel, Room, RoomType, Guest, Booking, DateRange. That's your first draft class list. (Day 1 lost `Room` and `Booking` here, and requirement 5 became unimplementable as a direct result.)

### Circle every verb
Verbs are **methods**, and they tell you which class owns what. "book a room" — does `Hotel.book()` or `Room.book()`? Whoever owns the data owns the method.

### Box every number, unit, and boundary word
"per night", "at least", "up to", "between", "within 24 hours", "not occupied". Every one is an off-by-one waiting to happen. Write each as an explicit rule before coding:

```
[check_in, check_out) — checkout day NOT occupied
so 1st→3rd and 3rd→5th are BOTH legal
```

### Find the "later we must support" clause
Almost every well-written problem has one. **That sentence tells you which axis must be extensible**, which usually tells you the pattern. "Later we must support EV charging and weekend surge pricing" → pricing varies → strategy-shaped.

---

## Minute 5-8 — Clarify out loud

This is the **first of four interaction points**. See "Talking to the interviewer" below for the full protocol — this is where the bulk of your questions go.

In a real interview you *ask*. Alone, write the questions down and answer them yourself as **stated assumptions** at the top of the file. This is scored — it's the Communication axis.

Standard questions worth asking on almost any problem:

- What's the scale? (single machine, in-memory, or distributed?)
- Concurrency — multiple threads/users hitting this at once?
- What identifies an entity — natural key or generated ID?
- On failure: exception, null, or result object?
- Is anything time-dependent, and do I control the clock (for testing)?
- What must be persisted vs. what's ephemeral?

```python
# Assumptions:
# - Single-threaded, in-memory. No persistence.
# - Bookings identified by generated int ID.
# - Failure raises ValueError; caller decides how to present it.
# - [check_in, check_out) half-open; back-to-back bookings legal.
```

**Never silently pick.** An interviewer watching you state an assumption and move on scores you higher than one watching you guess correctly.

---

## Minute 8-12 — Sketch the model, not the code

On paper or in comments. Three things only:

**1. Classes and their fields.**
```
Room(number, room_type, price_per_night)      immutable
Booking(id, room_number, guest, check_in, check_out)
Hotel(rooms: dict, bookings: dict)
```

**2. The public API** — method signatures with types, no bodies.
```
Hotel.add_room(room) -> None
Hotel.is_available(room_number, check_in, check_out) -> bool
Hotel.book(room_number, guest, check_in, check_out) -> Booking
Hotel.cancel(booking_id) -> None
Hotel.available_rooms(room_type, check_in, check_out) -> list[Room]
```

**3. What varies** — the axis the "later we must support" clause pointed at. Circle it. **That's where the pattern goes, and it's the only place abstraction is justified.** Everywhere else, write the boring concrete thing.

### Two questions to ask about the model

- **Does every requirement have a home?** Walk the numbered requirements and point at the class or method that serves each. A requirement with nowhere to live means a missing class — the exact day-1 failure.
- **Does any field change on a different schedule than its object?** Room number: stable for years. Price: changes weekly. That's a smell — the fast-changing field probably belongs on a separate object.

---

## Minute 12-18 — Write the asserts FIRST

Before any implementation. This is the highest-leverage habit on this list.

```python
hotel = Hotel()
hotel.add_room(Room(101, RoomType.SINGLE, 100))

b = hotel.book(101, "charan", d(1), d(5))
assert hotel.total_price(b.id) == 400

assert raises(hotel.book, 101, "x", d(3), d(8))   # right overlap
b2 = hotel.book(101, "y", d(5), d(7))             # back-to-back is LEGAL
```

Three reasons this works:

1. **It forces the API to be usable.** Awkward to call = wrong design, and you learn it in two minutes instead of forty.
2. **It catches boundary bugs before they exist.** Writing the back-to-back assert makes you *think* about `>` vs `>=` while you still have room to fix it.
3. **It's the deliverable.** In a machine-coding round the asserts are what proves it works. Code with no tests reads as untested — because it is.

### Boundary checklist — write an assert for each that applies

- empty / zero / one element
- duplicate insert
- the thing that doesn't exist
- exact-equal boundary (`==`, not just `<` and `>`)
- reversed or invalid input
- undo/remove, then verify state actually returned

---

## Minute 18-40 — Implement

Straight line now, because the thinking is done.

- **Simplest thing that passes the asserts.** No speculative flexibility. The one place you allow abstraction is the varying axis you circled.
- **Validate at the boundary.** One `_validate()` at the entry point, not scattered `if` checks in every method.
- **Extract any non-trivial condition into a named function.** `overlaps(a_in, a_out, b_in, b_out)` — testable alone, readable in place, and impossible to get subtly different in two call sites.
- **Derive boundary conditions, don't enumerate cases.** Enumeration feels complete and isn't. State the negative ("when do they *not* overlap?"), then negate with De Morgan — flip `and`↔`or` **and** flip every operator.
- Run the asserts as you go, not at the end.

---

## Minute 40-45 — Review your own code

Before saying done, check:

- [ ] Every stated requirement has a method that serves it
- [ ] Asserts cover all four boundary orientations, not three
- [ ] No method longer than ~15 lines
- [ ] No class doing storage *and* business logic *and* formatting
- [ ] Names say what things hold (`bookings`, not `availability`, if it holds bookings)
- [ ] No duplicated branches — if two `if` arms end the same way, merge them
- [ ] Nothing built that no requirement asked for

Then say, out loud, in one sentence: **"This design lets you add X without touching existing code, but adding Y would require changing Z."** Knowing your own design's limits is most of the Communication score. Interviewers ask "what would you change at 10x scale?" and the answer should already be loaded.

---

## The compressed version

```
1. Underline nouns → classes.  Circle verbs → methods.  Box boundaries → rules.
2. Find "later we must support" → that's the axis that varies → that's where the pattern goes.
3. ← ASK: read back the problem + 3-4 scoping questions.
4. Sketch fields + method signatures. Check every requirement has a home.
5. ← ASK: state the design + the requirement justifying it. Get agreement BEFORE coding.
6. Write the asserts. Yes, before the code.
7. Implement. Quiet, except decisions / shortcuts / stuck / self-caught bugs.
8. ← SPEAK: run the asserts, then name your design's limits unprompted.
```

---

## Talking to the interviewer

A machine-coding round is **not** a silent exam. Silence is scored against you — the interviewer can't distinguish "thinking hard" from "stuck and hiding it." But constant narration is worse. There are four points where you speak, and long stretches in between where you shouldn't.

The rule: **speak at decision points, not while typing.**

---

### Point 1 — after reading (minute 3-5). The big one.

Most of your questions belong here, before any design exists. Batch them; don't dribble them out one at a time.

Open with a **one-paragraph read-back**, because it catches a misunderstanding while it's still free to fix:

> "So — a hotel with rooms, each room has a type and a nightly price. Guests book date ranges, and I need to stop double-bookings. Before I design, four questions."

Then ask. Good questions, roughly in priority order:

| Question | Why it earns marks |
|---|---|
| "Scale — single machine and in-memory, or should I assume distributed?" | Sets whether concurrency and persistence are in scope. Biggest scope lever. |
| "Concurrent users, or single-threaded?" | Tells you whether locking is expected. Never assume it silently. |
| "Should I persist anything, or is in-memory fine?" | Almost always in-memory, but asking shows you know it's a choice. |
| "Is [ambiguous term] X or Y?" | Cite the actual ambiguity: "is checkout day occupied?" |
| "What's most important to you — a working core, or the extensible design?" | **Ask this one.** It tells you where to spend 40 minutes. |

Bad questions here — they read as stalling or as fishing for the answer:
- "What pattern should I use?" (never)
- "Should I use inheritance or composition?" (that's the thing being tested)
- Anything answered by re-reading the statement.

**Time-box it.** Three or four questions, then move. Ten minutes of questions is a red flag.

### Point 2 — after sketching, before implementing (minute 10-12). The highest-value 90 seconds.

You've got classes and signatures, no bodies. **Say them out loud and get agreement before writing code.** This is the cheapest possible moment to be wrong.

> "Here's my plan: `Character` holds a `Weapon` and an `Armor` by composition rather than subclassing, because requirement 5 needs runtime swapping and a subclass is fixed at construction. `Weapon` and `Armor` are plain data, so a designer adds new ones without touching character code. I'll start with damage calculation and death, then equipment swapping. Does that direction work for you?"

Four things that paragraph does, all scored:
1. States the design.
2. **Justifies it with a requirement**, not a preference — "because requirement 5 needs runtime swapping."
3. Names the order you'll build in, so the interviewer knows what to expect.
4. Invites a course correction while it costs nothing.

If the interviewer pushes back here, **you just saved 30 minutes.** Interviewers frequently nudge at this exact point — that's them helping, and taking the hint is scored higher than defending your first idea.

### Point 3 — while coding (minute 12-40). Mostly quiet.

Do **not** narrate every line. Speak only for these:

- **A decision you're making that could reasonably go the other way** — one sentence. *"I'll raise here rather than return a flag, so callers can't silently skip the failure."*
- **A deliberate shortcut** — say it and say when you'd fix it. *"Linear scan for now; at scale this becomes an interval tree — flagging it rather than building it."* This converts a weakness into evidence of judgment. It's the single most underused move in these rounds.
- **You're stuck for more than ~90 seconds.** Say what you're stuck on. *"I'm deciding whether the death check belongs on Character or on the Game — thinking Character, since it's a fact about the character."* Being stuck is normal; being stuck *silently* looks like being lost.
- **You realise something earlier was wrong.** Say it and fix it out loud. Catching your own bug scores *well* — it's what the job actually is.

Otherwise: type. A running commentary makes it hard for them to read your code, and it's slower.

### Point 4 — the last 5 minutes. Never skip this.

Two things, in this order.

**Demo it.** Run the asserts. Show the output. *"All checks pass — here's damage, armor floor, runtime swap, and death."* Code that visibly runs beats code that's argued to work.

**Name your own limits, unprompted:**

> "Three things I'd flag. The linear scan over bookings is fine at hotel scale but wrong at Airbnb scale — I'd want an interval tree or a DB index on `(room_id, check_in)`. Nothing here is thread-safe; concurrent booking of the same room would need a lock per room. And a fifth equipment slot would push me toward a slot map instead of two fields."

This is the highest-leverage 60 seconds in the whole round. It shows you know what you built *and* what you didn't, which is exactly what separates a mid engineer from a senior one. **Say it before they ask** — volunteered limits read as judgment, extracted ones read as damage control.

### If you don't finish

Very common; not fatal by itself. What's fatal is going quiet or pretending.

> "I've got damage and armor working with tests. Equipment swapping isn't implemented, but it's a one-line `equip()` since weapons are already composed rather than subclassed — the design supports it, I just ran out of time."

Working core + honest gap + a design that clearly *admits* the missing piece beats a half-broken everything.

### Things that lose marks

| Don't | Instead |
|---|---|
| Go silent for 10 minutes | One sentence at each decision |
| Narrate every line you type | Speak at decisions only |
| Argue when pushed back on | "Good point — let me reconsider." Then actually reconsider. |
| Ask "what pattern do you want?" | Derive it from the requirement and *name* it yourself |
| Say "this is bad but whatever" | "Shortcut for now; here's the upgrade path" |
| Hide that you're stuck | Say what you're stuck on |
| Claim it works without running it | Run it |

---

## Anti-patterns to catch in yourself

| Smell | What it means |
|---|---|
| Primitives where the spec had nouns (`rooms = [1, 2, 3]`) | Missing class; requirements will silently vanish |
| A method with two mutually exclusive parameter styles | The data model is wrong — the object should already know |
| Enumerated `if/elif` chains for a boundary condition | You will miss an orientation; derive instead |
| A dict named after the opposite of what it holds | You didn't decide what it was for |
| Adding a parameter to a method for each new criterion | OCP violation; pass a predicate instead |
| Empty or missing `__main__` | Untested. Non-negotiable from day 2. |
