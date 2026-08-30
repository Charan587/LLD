# Singleton

Derived from day 10. Every trace is real output from code that was run.

This is the pattern interviewers ask about most and like least. **Knowing how to write one is not the test — knowing what it costs is.**

---

## 1. The problem

A database connection pool. Opening a connection is expensive, so you open a fixed number up front and hand them out. The requirement:

> The whole application shares one pool. Two pools means twice the connections to the database.

That requirement is **real**. Connection pools are among the few honest uses of this pattern.

---

## 2. The pattern

> **Singleton** — one instance, globally reachable, with the class enforcing its own uniqueness.

```python
class Pool:
    _instance = None                       # on the CLASS, one copy, shared

    @classmethod                           # callable with no object in existence
    def get_instance(cls, max_size=3):
        if cls._instance is None:          # first call?
            cls._instance = cls(max_size)  # build it, remember it
        return cls._instance               # every later call gets this one
```

Two mechanics worth being precise about:

- **`_instance` lives on the class.** `self._instance` would be per-object, which defeats the purpose — there'd be nothing shared.
- **`@classmethod`, not a plain method.** A plain method needs an object; `get_instance` must run when no object exists yet. That's its entire job. `Pool.get_instance()` on a plain method gives `TypeError: missing 1 required positional argument: 'self'`.

Testing it needs `is`, not `==`:

```python
assert Pool.get_instance() is Pool.get_instance()
```

`==` compares values. Two separate pools with the same `max_size` compare equal and still hold two separate sets of connections — which is exactly the bug you're preventing.

---

## 3. Three costs, shown

### Cost 1 — the second call's arguments vanish

```
COST 1 — the initialization arguments of the second call
   asked for 10, got max_size=3   p1 is p2 -> True
   the 10 was accepted, ignored, and nobody was told.
```

`__init__` runs only on the first call. So `get_instance(max_size=10)` accepts an argument, discards it, and returns a 3-connection pool. **No error, no warning.** Whoever calls first silently decides the configuration for the whole process.

Three defensible answers, and you must pick one **deliberately**:

| Choice | Cost |
|---|---|
| ignore the arguments (the accidental default) | a caller asking for 10 quietly gets 3 |
| raise if they differ from the first call | `get_instance` now fails depending on who ran first |
| take no arguments at all — configure once at startup | honest, and admits the config isn't per-call |

The third is the cleanest, and notice it's already halfway to not needing the pattern.

### Cost 2 — tests interfere, and the result depends on order

```
COST 2 — tests interfere, in order-dependent ways
   run a then b: test_a ok | test_b sees available=2
   run b then a: test_b sees available=3 | test_a ok
   same two tests, different results, decided by ordering.
```

`test_b` gets a different answer depending on whether `test_a` ran first. Nothing in either test says so. Add a test in the middle and unrelated tests start failing.

The usual patch is a `reset_instance()` classmethod. It works, and **its existence is the smell** — it only needs to exist because the global does. It's also a method whose only purpose is to undo the pattern's one feature.

### Cost 3 — no seam

```
COST 3 — no seam: you cannot hand OrderService a failing pool
   OrderService() takes no arguments — nothing declares the pool
   -> saved order-1 on c2

   to test exhaustion, the test must reach into global state:
     Pool._instance = ExhaustedPool(1)  ->  RuntimeError: exhausted
   the test manipulates a private global the code never declared,
   and must remember to put it back or every later test is poisoned.
```

This is the worst one, and it has two halves.

**The dependency is hidden.** `OrderService()` takes nothing. Reading that constructor tells you the class needs no collaborators — and it needs a database connection pool. Every hidden dependency is a lie the signature tells.

**There is no argument to substitute.** To test exhaustion you assign `Pool._instance` from the test: reaching into a private attribute of another class, then remembering to restore it. The test now knows implementation details the code never declared, and forgetting the restore poisons everything after.

---

## 4. The fix, and the thing worth noticing about it

```python
pool = ConnectionPool(max_size=3)     # created ONCE, at startup
service = OrderService(pool)          # passed in
```

**The requirement said the app must share one pool. This satisfies it, without the pattern.**

Sharing came from *creating one object and passing it around* — not from the class refusing to be instantiated twice. That's **Dependency Inversion** (day 5), and it hands you the three costs back as features:

| | Singleton | Injected |
|---|---|---|
| one shared pool | yes | yes — create one at startup |
| two pools for replica + primary | **impossible** | `ConnectionPool(2)`, `ConnectionPool(5)` |
| test against a failing pool | reach into `_instance` | pass a fake |
| dependency visible in the signature | no | yes |
| tests isolated | needs `reset_instance()` | fresh object per test |

So what is `get_instance()` still for? It enforces *"nobody can ever make a second one"* — which is precisely the thing the read-replica requirement needs you not to enforce.

**Keep the constructor public. Treat `get_instance()` as a convenience for callers that want the default, never as the only door in.** Plenty of real codebases do exactly this, and it's the answer that survives an interviewer pushing back.

---

## 5. When a singleton is genuinely right

Not never. The honest cases share two properties: **there is exactly one in reality, and it holds no state a test would want to vary.**

- A **stateless registry** built at import time — a table of currency codes, a regex cache.
- **Python modules.** A module is already a singleton: imported once, shared. `import config` is the pattern, without the ceremony.
- **Logging.** One process, one log stream. Note even `logging` lets you inject a logger.

The test: *"would any test ever want a different one?"* If yes, it's not a singleton, it's a shared instance — and shared instances get injected.

---

## 6. Thread safety

```python
def acquire(self):
    if not self._free:            # thread A checks: one left
        raise RuntimeError(...)   # thread B checks: one left
    return self._free.pop()       # both pop. One gets IndexError, or worse, they share.
```

Check-then-act across two statements is a race. Same in `get_instance`: two threads can both see `_instance is None` and both construct, so you get two "singletons".

Fixes: a `threading.Lock` around the check-and-act, or `queue.Queue`, which is thread-safe by construction and blocks when empty — usually what you actually want from a pool anyway.

Say this out loud even in a single-threaded answer. "Not thread-safe; here's the specific race" scores; silence reads as not having thought about it.

---

## 7. Bug list

- **`self._instance` instead of `cls._instance`** — per-object, so nothing is shared and every call builds a new one.
- **A plain method instead of `@classmethod`** — `TypeError: missing 1 required positional argument: 'self'`.
- **`==` instead of `is`** in the identity assert — passes for two distinct equal pools, which is the bug itself.
- **Second-call arguments silently ignored** — pick a behaviour and comment it.
- **A class fetching the singleton inside its own methods.** The dependency vanishes from the signature and the seam vanishes with it.
- **`reset_instance()` shipped to production.** It exists for tests; if a request handler can call it, one caller can swap the pool under everyone.
- **Asserts sharing one instance.** Order-dependent results, and a bug that only appears when someone adds a test above yours.
- **Two "singletons" under threads** — unsynchronised `get_instance` races.
- **`import` cycles.** A singleton constructed at import time makes module order matter.

---

## 8. Saying it in an interview

> "The requirement is that the app shares one pool, so **Singleton** is the obvious answer — `get_instance()` caching a class attribute.
>
> I didn't make it the only door in, for two concrete reasons. First, a class that fetches the singleton itself has no seam — there's no argument to substitute, so I can't test `OrderService` against an exhausted pool without reaching into private global state from the test. Second, you mentioned a read replica and a primary; enforcing 'only one' makes two pools impossible.
>
> So the constructor stays public and the pool is injected. The sharing comes from creating one at startup and passing it around — that's **Dependency Inversion**, and it gives me the sharing without the enforcement. `get_instance()` is still there as a convenience default.
>
> Not thread-safe as written: `acquire` does check-then-pop, so two threads can take the last connection. A lock, or `queue.Queue`."
