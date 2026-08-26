# Day 10 — Connection Pool

**Time box: 45 minutes.**

Today's pattern is the one interviewers ask about most and like least. The problem is built so you feel why.

---

## Part 1 — the pool

A database connection pool. Opening a connection is expensive, so you open a fixed number up front and hand them out.

1. `ConnectionPool.get_instance(max_size=3)` returns the pool. **Every call returns the same object** — the whole application shares one pool. Two pools would mean twice the connections to the database, which is the bug this exists to prevent.
2. `acquire()` hands out a connection and marks it in use.
3. `release(conn)` returns it to the pool.
4. `available` and `in_use` report counts.
5. Acquiring when none are free → error.
6. Releasing a connection that isn't in use → error.
7. `max_size` of 0 or less → error.

### Worked example — `max_size=3`

```
start            available 3   in_use 0
acquire x1       available 2   in_use 1
acquire x3       available 0   in_use 3
acquire again    -> error
release one      available 1   in_use 2
```

---

## Part 2 — the costs

Now the requirements that make Part 1 hurt.

8. **`get_instance(max_size=10)` called after `get_instance(max_size=3)`.** Decide what happens, implement it, and **write down why**. There are three defensible answers and one of them is what most implementations do by accident.

9. **Your asserts must not interfere with each other.** An assert that exhausts the pool must not break the next one. You'll notice this is *hard* — that difficulty is the point of today, not an obstacle to route around.

10. **A test must be able to run against a fake pool that fails on every acquire**, to check the calling code handles exhaustion. Without editing the calling code.

11. `class OrderService` uses the pool to save an order. **From its constructor signature alone, a reader must be able to tell that it needs a pool.**

Requirements 9, 10 and 11 are the three standard objections to this pattern. Solve them and say what it cost you.

### Later we must support (do not build it)

- Two pools — one for the read replica, one for the primary.
- A pool per tenant in a multi-tenant service.

Read those twice before you commit to a design.

### Constraints

- No real database. A "connection" can be an object with an id.
- Single-threaded is fine — but **say in one line what would break with threads.**
- **No `print()` in business logic.** `solution.py` required.

---

## Required before the code

1. **Assumptions.** One line each.
2. **The design you rejected.** One sketch, one sentence.
3. **Name the pattern. Then name two concrete problems it causes** — not "it's global state", but two things that actually break, with the requirement number each one comes from.

Day 9 you named Builder correctly and unprompted. Keep that going, and today add the costs.

---

## Required asserts

**Paste all thirteen in first. Delete none — and if one is awkward to express, that's the day's lesson, not a reason to comment it out.**

Day 9 you commented out assert 12 because a bare `assert` can't catch an exception. You've written a `raises()` helper on days 4, 6 and 8. Use it.

1. `get_instance()` twice → **the same object** (`is`, not `==`)
2. fresh pool, `max_size=3` → `available == 3`, `in_use == 0`
3. after one `acquire` → `available == 2`, `in_use == 1`
4. after three acquires → `available == 0`, `in_use == 3`
5. **the fourth acquire → error** *(the boundary: the third must succeed)*
6. release one → `available == 1`, `in_use == 2`
7. releasing the same connection twice → error
8. releasing a connection the pool never issued → error
9. `max_size=0` and `max_size=-1` → error
10. acquire, release, acquire again → you get a working connection, and counts are right
11. **`get_instance(max_size=10)` after `get_instance(max_size=3)`** — assert whatever you decided in requirement 8, and comment why
12. **`OrderService` under a pool that always fails to acquire** — assert the service surfaces that, without editing `OrderService`
13. **two independent pools coexisting**, one with `max_size=2` and one with `max_size=5`, neither affecting the other

Assert 13 is the one to read carefully before you start.

Print `all checks passed` at the end.

---

## Before you say done

Run it, look for the printed line, paste the terminal output.
