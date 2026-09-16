# Day 10 Review — Connection Pool (Python)

Reviewed 2026-08-30. Submission preserved as `solution.submitted.py`.

## Verdict

```
$ python3 solution.py
all test case passed
exit: 0
```

**You made the right architectural call**, which is the whole point of today:

- **The constructor stayed public**, so `ConnectionPool(max_size=2)` works and assert 13 is expressible at all.
- **`OrderService(pool)` takes the pool.** Requirement 11 — a reader sees the dependency in the signature.
- **`AlwaysFailConnectionPool` exists**, doesn't inherit from `ConnectionPool`, and is passed in. Third appearance of the fake-collaborator move after `FakeNotifier` and `FixedClock`.
- **`max_size <= 0` validated** — W5 present without being reminded.
- **Assert 1 uses `is`.** The boundary in assert 5 is right: the third acquire succeeds, the fourth raises.

The pool logic itself is entirely correct. What's missing is the *evidence* — four asserts absent, two testing something other than what they claim, and a file that never says what pattern it is.

## Score

| Axis | D6 | D7 | D8 | D9 | D10 | Why |
|---|---|---|---|---|---|---|
| Correctness | 2 | 1 | 2 | 3 | **3** / 5 | Pool logic all correct. `OrderService` has no behaviour, so requirement 12 is untested. |
| Extensibility | 4 | 3 | 3 | 4 | **4** / 5 | Public constructor + injection: two pools and fakes both work |
| SOLID | 4 | 3 | 3 | 4 | **4** / 5 | Injection over global access — the day's actual lesson, and you took it |
| Readability | 2 | 2 | 2 | 3 | **3** / 5 | Unused import; `Connection` class the pool never uses; comment attached to the wrong line |
| Communication | 3 | 1 | 3 | 4 | **1** / 5 | **No pattern name, no costs, no rejected design.** Regression from day 9. |

**15 / 25**, down from 18.

---

## `OrderService` is an empty shell

```python
class OrderService:
    def __init__(self, pool):
        self.pool = pool
```

```
OrderService methods: ['pool']
<-- there is no save(). assert 12 tested order.pool.acquire, i.e. the POOL.
```

Requirement 12: *"`OrderService` under a pool that always fails to acquire — assert **the service** surfaces that."*

Your assert is `raises(order.pool.acquire)`. That reaches **past** the service and calls the fake pool directly. It would pass with no `OrderService` in the file at all — you're asserting that a method you wrote to raise, raises.

The service needs one method for the requirement to mean anything:

```python
def save(self, order):
    conn = self.pool.acquire()
    try:
        return f"saved {order} on {conn}"
    finally:
        self.pool.release(conn)
```

Then:

```python
assert raises(OrderService(AlwaysExhaustedPool()).save, "order-2", exc=RuntimeError)
```

Now you're testing what the requirement asked: **does the failure propagate through the service?** And the `finally` is the part worth having — it returns the connection even when saving raises, which is the bug that drains a pool over hours in production.

Note the shape of the mistake: **you tested the collaborator instead of the thing under test.** Day 6 asserted `attack()` returned `True` rather than checking damage; same reflex — assert on the nearest thing that's easy to reach.

## `raises()` catches everything

```python
def raises(fn, *args):
    try:
        fn(*args)
    except:            # bare except
        return True
    return False
```

```
raises(lambda: undefined_thing)  -> True
raises(lambda: 1/0)              -> True
any exception at all returns True.
```

A `NameError` from a typo, a `ZeroDivisionError`, a `TypeError` from calling with the wrong arity — all indistinguishable from the error you meant to test.

**This is exactly the day-6 bug's root cause.** There you wrote `raises(rental_service.rent, (member2, car2, 7, date(...)))` with the args in one tuple; it failed on arity, the assert passed, and it proved nothing. A bare `except` is what let that through.

```python
def raises(fn, *args, exc=Exception) -> bool:
    try:
        fn(*args)
    except exc:
        return True
    return False

assert raises(p.release, a, exc=ValueError)      # only the error you meant
assert raises(p.acquire, exc=RuntimeError)
```

Anything else now propagates and you see it immediately. Bare `except:` also swallows `KeyboardInterrupt`, so a hung test can't be Ctrl-C'd.

## Two asserts that don't assert what they claim

**Assert 11 — requirement 8.**

```python
conn1 = ConnectionPool.get_instance(max_size=3)
conn2 = ConnectionPool.get_instance(max_size=10)
assert conn1 is conn2
```

```
asked for 10, got max_size=3, available=3
you asserted p1 is p2 (true) but never that max_size stayed 3
```

`conn1 is conn2` is true for *any* singleton — it's assert 1 again. The requirement was to decide and pin down **what happens to the `max_size=10`**. It's silently discarded, which is a legitimate choice, but the assert has to say so:

```python
assert p2.max_size == 3          # the 10 was ignored, deliberately
```

You did write a comment — but it's on line 120, attached to the `small, big = ConnectionPool(3), ConnectionPool(10)` line, which is about two separate pools. The comment and the code it describes are five lines apart.

**Assert 13 — independence.**

```python
small, big = ConnectionPool(max_size=3), ConnectionPool(max_size=10)
assert small is not big
```

```
small: available 0 in_use 2
big:   available 5 in_use 0
you asserted only  small is not big  — never that big was unaffected
```

Different objects is necessary but not sufficient. The requirement is *"neither affecting the other"* — so acquire from one and check the other:

```python
small.acquire(); small.acquire()
assert small.available == 0 and big.available == 5
assert raises(small.acquire, exc=RuntimeError)
assert big.acquire() is not None                  # big still works
```

**Both asserts test the easy half.** Identity is easy to check; independence takes three more lines and is the thing that matters.

## Not written at all

**Assert 9** — `max_size=0` and `max_size=-1`. Your validation is correct:

```
ConnectionPool(0) -> max_size should be positive, got 0
```

...and nothing in your file exercises it. **Right code, no evidence.** Same as day 4, where every fee was correct and no assert checked a fee.

**Assert 10** — acquire, release, acquire again. The one that proves a released connection actually returns to circulation rather than being lost.

## Requirement 9 wasn't addressed

```
a fresh get_instance() now reports available=1, not 3
```

Every assert from line 94 to 118 mutates the same singleton. It doesn't *fail*, because nothing after line 118 checks counts — but the pollution is there, and requirement 9 asked you to solve it.

You already have the tool: your constructor is public, so `ConnectionPool(max_size=3)` gives a fresh pool per block. My rewrite uses a three-line `fresh()` helper.

**Say what it cost, because that's the answer to requirement 3:** the singleton *cannot* give you this. A `reset_instance()` classmethod is the usual workaround, and its existence is itself the smell — it only needs to exist because the global does.

## The file never says "Singleton"

Requirement 3 asked for the pattern name **and two concrete problems it causes**, tied to requirement numbers. The docstring has none of it — no name, no costs, no rejected design.

**This is a regression.** Day 9 you named Builder correctly and unprompted, and the rejected-design section was the best you'd written.

The answers, and you reached all of them out loud during the session:

> **Singleton** — one instance, globally reachable, the class enforcing its own uniqueness.
>
> **Problem 1 (requirement 10):** a class that fetches the singleton itself has no seam. There's no argument to substitute, so `OrderService` can't be tested against an exhausted pool.
>
> **Problem 2 (requirement 13):** enforcing "only one" makes two legitimate pools impossible — read replica and primary, or one per tenant.
>
> Both are solved by creating one at startup and injecting it. **The sharing was never the pattern's doing** — it came from passing one object around.

You *said* the equivalent of this in the design chat. It didn't reach the file.

## Smaller things

- **`from collections import defaultdict`** — unused.
- **`Connection` is a dataclass the pool never uses.** `_free` holds strings. Using `Connection()` as the never-issued object in assert 8 works, but only because it's a different type entirely — a `Connection` could never be in the pool, so the test is weaker than passing `"conn99"`.
- **`AlwaysFailConnectionPool.release(self)`** takes no `conn`. Nothing calls it, so it never fires — but a real `OrderService.save` with a `finally` would.
- **The threading line is missing.** The spec asked for one sentence on what breaks with threads. The answer: `acquire()` does check-then-pop, so two threads can both see a free connection and both take the last one. A lock, or `queue.Queue`.

## The rewrite

`rewrite.py`, `all checks passed`. Your design kept — public constructor, injected pool, fake pool. Added: `OrderService.save()` with `finally`, a typed `raises()`, a `Pool` protocol so the fake's shape is documented, `reset_instance()`, and all thirteen asserts including independence, the ignored `max_size`, and a `RecordingPool` proving `release` runs on the happy path.

The walkthrough block carries the requirement-8 decision as a comment on `get_instance` itself, which is where a reviewer will look for it.

## Grill

1. My `save()` uses `try/finally`. **Write the two-line sequence** that drains a pool to zero if the `finally` is missing.
It because we arent adding back the connection back to pool
2. `reset_instance()` exists only for tests. **Name one production bug** it makes possible, and say whether you'd ship it.
I would rather not ship. bceuase at a time at production many prpcess are running. if i reset eveyrthing would fall aprat which are running
3. I made `Pool` a Protocol with two methods. `ConnectionPool` has five. **Why is the Protocol smaller**, and which principle is that?
Connection Pool has its own methods. and pool has only needed methods where next people who wirte pool can extend them
4. Requirement: `acquire()` should wait up to 2 seconds for a free connection instead of failing. **What has to change**, and what does it do to your asserts?
acquire waiting for seconds helps other process to feeup conn when its full so other process can do their job instead of failing. for asssert . I will add timer?
5. You used `Connection()` as the never-issued object. I used the string `"conn-from-nowhere"`. **Which is the better test, and why?**
Yours is better to test.  mine would be best to get different type of connection like sql , psql and other
6. A singleton is sometimes genuinely right. **Name a case** where you'd keep `get_instance()` as the only door in, and say what makes it different from the pool.
making get instance only door . keeps code more safer from exploitation