"""Day 10 — Connection Pool. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "A fixed-size pool of connections, acquired and released. The app should
    share one pool — two pools means twice the connections to the database.
    But I also need two independent pools for read-replica and primary, and
    I need to test a service against a pool that always fails."

2. CLARIFYING QUESTIONS
   - "Should a second get_instance(max_size=10) resize, raise, or be ignored?"
     -> most implementations ignore it silently; that's a decision, not a default
   - "Do I need a pool per tenant later, or is one global pool the end state?"
     -> the answer kills or keeps the singleton
   - "Should acquire block when exhausted, or fail immediately?"
     -> real pools block with a timeout; failing fast is a simplification

3. HOW I FOUND THE CLASSES
   Nouns: pool, connection, size, order service.
     pool       -> holds free/in-use, hands them out       -> ConnectionPool
     connection -> an opaque handle. No behaviour needed.  -> a value
     service    -> USES a pool; does not own one           -> OrderService(pool)

   The important modelling decision isn't a noun, it's a wiring one:
   who creates the pool? Not OrderService — if it builds its own, ten
   services means thirty connections, which is the exact bug requirement 1
   exists to prevent.

4. ASSUMPTIONS
   - Single-threaded. With threads, acquire()'s check-then-pop is a race:
     two callers both see a free connection and both take the last one.
     Fix is a lock around acquire/release, or a queue.Queue which is
     thread-safe by construction.
   - acquire() fails immediately when exhausted rather than blocking.
   - A second get_instance() ignores its arguments — decided, not accidental.

5. THE DESIGN I REJECTED
   "A classic Singleton with a private constructor — get_instance() as the
    only way in. It satisfies 'the app shares one pool' and breaks three
    other requirements: I can't build two pools for read-replica and
    primary, I can't hand OrderService a failing pool to test against, and
    every assert shares one mutable object so the tests interfere."

   "I also rejected OrderService constructing its own pool. It reads fine
    and gives every service its own connections — the opposite of pooling."

6. THE DESIGN + PATTERN NAME AND ITS COSTS
   "SINGLETON — one instance, globally reachable, the class enforcing its
    own uniqueness."
   "Two concrete problems, not 'it's global state':
      (a) A class that fetches the singleton itself has no seam. There is no
          argument to substitute, so I can't test OrderService against an
          exhausted pool without editing OrderService.
      (b) Enforcing 'only one' makes two legitimate pools impossible — read
          replica and primary, or one per tenant."
   "So I kept the constructor public and inject the pool. Sharing comes from
    creating ONE at startup and passing it around — that's DEPENDENCY
    INVERSION, and it gives me the sharing without the enforcement.
    get_instance() stays as a convenience for callers that want the default,
    but it is not the only door in."

7. LIMITS I'D VOLUNTEER
   - "Not thread-safe; see assumptions."
   - "No health check — a connection that died in the pool is handed out anyway.
      Real pools validate on acquire or ping on a timer."
   - "No max lifetime or idle eviction."
   - "get_instance() still holds process-global state, so anything using it
      is order-dependent. reset_instance() exists for tests, which is itself
      a smell — it only needs to exist because the global does."

═══════════════════════════════════════════════════════════════════════════
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Pool(Protocol):
    """What OrderService actually needs. Two lines, so a fake is trivial."""
    def acquire(self) -> str: ...
    def release(self, conn: str) -> None: ...


class ConnectionPool:
    _instance: "ConnectionPool | None" = None

    def __init__(self, max_size: int = 3):
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")
        self.max_size = max_size
        self._free = [f"conn{i}" for i in range(max_size)]
        self._in_use: set[str] = set()

    @classmethod
    def get_instance(cls, max_size: int = 3) -> "ConnectionPool":
        # DECISION (requirement 8): a second call IGNORES its arguments.
        # Resizing would change capacity under callers already holding
        # connections; raising would make get_instance() fail depending on
        # who ran first, which is worse than being predictable.
        if cls._instance is None:
            cls._instance = cls(max_size)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Only needed because the global exists. That is the point."""
        cls._instance = None

    @property
    def available(self) -> int:
        return len(self._free)

    @property
    def in_use(self) -> int:
        return len(self._in_use)

    def acquire(self) -> str:
        if not self._free:
            raise RuntimeError("pool exhausted")
        conn = self._free.pop()
        self._in_use.add(conn)
        return conn

    def release(self, conn: str) -> None:
        if conn not in self._in_use:
            raise ValueError(f"{conn!r} was not in use")
        self._in_use.remove(conn)
        self._free.append(conn)


class OrderService:
    def __init__(self, pool: Pool):        # the signature says what it needs
        self.pool = pool

    def save(self, order: str) -> str:
        conn = self.pool.acquire()
        try:
            return f"saved {order} on {conn}"
        finally:
            self.pool.release(conn)        # returned even if saving raises


class AlwaysExhaustedPool:
    """Same shape, different behaviour. Never inherits from ConnectionPool."""
    def acquire(self) -> str:
        raise RuntimeError("pool exhausted")

    def release(self, conn: str) -> None:
        pass


class RecordingPool:
    """Proves release() is called even when the body fails."""
    def __init__(self):
        self.acquired, self.released = [], []

    def acquire(self) -> str:
        self.acquired.append("c")
        return "c"

    def release(self, conn: str) -> None:
        self.released.append(conn)


def raises(fn, *args, exc=Exception) -> bool:
    try:
        fn(*args)
    except exc:
        return True
    return False


if __name__ == "__main__":
    def fresh(max_size=3):
        """Requirement 9: every block starts clean. Only possible because
        the constructor is public."""
        return ConnectionPool(max_size=max_size)

    # 1 — get_instance returns the SAME object
    ConnectionPool.reset_instance()
    assert ConnectionPool.get_instance() is ConnectionPool.get_instance()

    # 2, 3, 4 — counts
    p = fresh()
    assert p.available == 3 and p.in_use == 0
    a = p.acquire()
    assert p.available == 2 and p.in_use == 1
    b, c = p.acquire(), p.acquire()
    assert p.available == 0 and p.in_use == 3

    # 5 — the boundary: the third succeeded above, the fourth fails
    assert raises(p.acquire, exc=RuntimeError)

    # 6 — release
    p.release(a)
    assert p.available == 1 and p.in_use == 2

    # 7 — double release
    assert raises(p.release, a, exc=ValueError)

    # 8 — a connection the pool never issued
    assert raises(p.release, "conn-from-nowhere", exc=ValueError)

    # 9 — invalid sizes
    assert raises(ConnectionPool, 0, exc=ValueError)
    assert raises(ConnectionPool, -1, exc=ValueError)

    # 10 — acquire, release, acquire again
    p = fresh(max_size=1)
    first = p.acquire()
    assert p.available == 0
    p.release(first)
    assert p.available == 1 and p.in_use == 0
    second = p.acquire()
    assert second == first and p.available == 0

    # 11 — a second get_instance IGNORES its arguments (see the comment above)
    ConnectionPool.reset_instance()
    p1 = ConnectionPool.get_instance(max_size=3)
    p2 = ConnectionPool.get_instance(max_size=10)
    assert p1 is p2
    assert p2.max_size == 3           # the 10 was silently discarded
    assert p2.available == 3

    # 12 — the SERVICE surfaces exhaustion. OrderService is not edited.
    assert OrderService(fresh()).save("order-1").startswith("saved order-1 on conn")
    assert raises(OrderService(AlwaysExhaustedPool()).save, "order-2", exc=RuntimeError)

    # and the connection goes back even on the happy path
    rec = RecordingPool()
    OrderService(rec).save("order-3")
    assert rec.acquired == ["c"] and rec.released == ["c"]

    # 13 — two pools, INDEPENDENT (not merely different objects)
    small, big = ConnectionPool(max_size=2), ConnectionPool(max_size=5)
    assert small is not big
    small.acquire(); small.acquire()
    assert small.available == 0 and small.in_use == 2
    assert big.available == 5 and big.in_use == 0          # untouched
    assert raises(small.acquire, exc=RuntimeError)
    assert big.acquire() is not None                       # big still works

    # requirement 9 demonstrated: the singleton leaks across blocks
    ConnectionPool.reset_instance()
    ConnectionPool.get_instance(max_size=3).acquire()
    assert ConnectionPool.get_instance().available == 2     # NOT 3
    ConnectionPool.reset_instance()
    assert ConnectionPool.get_instance().available == 3

    print("all checks passed")
