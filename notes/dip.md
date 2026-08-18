# Dependency Inversion

Derived from day 5. Every trace is real output from code that was run.

---

## 1. The problem

Library lending. Books go out for 14 days; late fees are ₹5/day capped at ₹200; a reminder goes out two days before due.

**Three things you need to prove work:**

| Returned | Expected fee |
|---|---|
| on the due date | 0 |
| 5 days late | 25 |
| **137 days late** | 200 (capped) |

Plus: the reminder fires on exactly one day.

---

## 2. Why the obvious design fails

The obvious thing is to ask the system what day it is, right where you need it.

```python
class LendingServiceV1:
    def fee_for(self, book):
        due = dict(self.loans)[book]
        days_late = max(0, (date.today() - due).days)   # reaches outside
        return min(days_late * 5, 200)
```

```
ATTEMPT 1 — date.today() inside the calculation
   book due 2026-01-15, fee today -> 200
   I wanted to test 'returned 2026-01-20 -> fee 25'.
   There is no argument I can pass to make that happen.
```

**This code is not wrong. It runs. It computes correct fees.** That's what makes DIP the hardest of the five to see — with SRP, OCP, LSP, ISP the naive design at least *looks* awkward. Here it looks fine.

The failure is that there is **no input** that makes it produce the case you need to check. Your options are:

1. Change the system clock. (Breaks every other test, and your machine.)
2. Wait 137 days.
3. Monkeypatch `datetime` inside the module. (Now your test knows the internals of the code it's testing, and breaks when you move the import.)

And the notifier is worse. There is no version of "run the test suite" that doesn't send a real email, unless you never call the reminder — in which case it's never tested at all.

**The rule this reveals: anything a method reaches out to grab — the clock, the network, the disk, a random number — is a dependency it can't be asked about.**

---

## 3. The principle

> High-level modules should not depend on low-level modules. Both should depend on abstractions.

Concretely: **`LendingService` should not know that `date.today()` or SMTP exist.**

### What "inverted" means

Normally the arrow points down: the high-level policy (lending rules) depends on low-level mechanism (system clock, SMTP client).

```
LendingService  ──depends on──>  date.today(), smtplib
```

Invert it. Define the abstraction **where it's used**, and make both sides depend on it:

```
LendingService  ──depends on──>  Clock  <──implements──  SystemClock
                                        <──implements──  FixedClock
```

`LendingService` now depends on an interface it owns. `SystemClock` depends on that same interface. **The arrow from the low-level thing now points up** — that's the inversion.

---

## 4. Deriving the fix

Two questions, asked of every method:

1. **What does this reach out and grab?** → `date.today()`, an SMTP client.
2. **Could a test reasonably supply a different one?** → yes to both.

Anything answering yes to both becomes a constructor parameter.

```python
class Clock(Protocol):
    def today(self) -> date: ...

class SystemClock:                       # production
    def today(self): return date.today()

class FixedClock:                        # tests
    def __init__(self, d): self.d = d
    def today(self): return self.d

class Notifier(Protocol):
    def send(self, to: str, msg: str) -> None: ...

class EmailNotifier:
    def send(self, to, msg): ...         # smtp

class FakeNotifier:
    def __init__(self): self.sent = []
    def send(self, to, msg): self.sent.append((to, msg))   # the list IS the record


class LendingService:
    def __init__(self, clock: Clock, notifier: Notifier):
        self.clock, self.notifier = clock, notifier
```

---

## 5. Dry run of the fixed design

```
ATTEMPT 2 — the clock and the notifier are handed in
   returned 2026-01-15 -> fee 0    expected 0
   returned 2026-01-20 -> fee 25   expected 25
   returned 2026-06-01 -> fee 200  expected 200

   reminder, checked WITHOUT sending mail:
     today=2026-01-12  notifier.sent=[]
     today=2026-01-13  notifier.sent=[('a@x.com', 'Dune due 2026-01-15')]
     today=2026-01-20  notifier.sent=[]

   production wiring:  LendingService(SystemClock(), EmailNotifier())
   test wiring:        LendingService(FixedClock(...), FakeNotifier())
   SAME code path through LendingService. Nothing is test-only.
```

That last line is the whole test of whether you did it right. **If your test takes a different route through the code than production does, you aren't testing production.** Monkeypatching fails this; injection passes it.

Note the reminder rows: `notifier.sent` is a plain list, so asserting *what was sent* is as easy as asserting a number. You cannot assert against a `print`.

---

## 6. Two things that are not DIP

**Passing a value is not always inversion.** `return_book(book, returned_on)` takes the return date as a parameter — that isn't dependency inversion, it's just correct API design. *When a book came back is genuinely an input.* Inversion is needed when the method has to ask "what is today" on its own, with no caller to tell it — like the reminder scan.

**"I'll use datetime in real life"** is the misconception to kill. Production doesn't take a different path. Production passes `SystemClock()`. The abstraction is permanent; only the argument differs.

---

## 7. The shape repeats

Every dependency that crosses the process boundary gets the same treatment:

| Reaches outside for | Abstraction | Production | Test |
|---|---|---|---|
| the current time | `Clock` | `SystemClock` | `FixedClock`, `ScriptedClock` |
| sending mail | `Notifier` | `EmailNotifier` | `FakeNotifier` |
| storage | `LoanRepository` | `PostgresRepo` | `InMemoryRepo` |
| randomness | `RandomSource` | `SystemRandom` | `SeededRandom` |
| HTTP | `PaymentClient` | `StripeClient` | `FakeClient` |

The storage one has a name: **Repository**. Same inversion, applied to persistence.

### A clock that returns a different day each call

`FixedClock` tests one day. A nightly job needs several:

```python
class ScriptedClock:
    def __init__(self, *days): self.days = iter(days)
    def today(self): return next(self.days)
```

Two lines, and now you can run eight consecutive days through the real code and assert **exactly one** reminder was sent across the week. That is the bug a single `FixedClock` assert cannot see — a reminder condition written with `>=` fires every day forever, and one day of testing looks fine.

---

## 8. Bug list

- **`date.today()` / `datetime.now()` anywhere below the top layer.** Almost always wrong.
- **A dependency constructed inside a constructor** — `self.mailer = SmtpMailer()`. You can never substitute it.
- **A test that monkeypatches a module** — a signal the dependency should have been a parameter.
- **A fake that prints instead of recording.** You built the seam and then made it unassertable. The list *is* the record.
- **A global "current date" that tests reassign.** Still hidden, still shared, and now test order matters.
- **The wiring is the untested line.** Every test uses `FixedClock`; the one line choosing `SystemClock` for production is the only line no test executes. A `FixedClock` shipped to production is silent — nothing ever goes overdue, fees compute to zero, no exception. Keep the composition root tiny and eyeball it before release.
- **Injecting things that don't vary.** A plain `dict` for internal bookkeeping doesn't need a protocol. Test: *would I ever want a different implementation, in a test or in production?* Clock yes, dict no.

---

## 9. Saying it in an interview

> "The fee calculation needs today's date and the reminder needs to send mail, so I've made both injected dependencies — a `Clock` and a `Notifier` protocol, with real implementations for production and a fixed clock and recording fake for tests.
>
> That's **Dependency Inversion**: `LendingService` depends on those two abstractions rather than on `datetime` and SMTP, so the assert for 'returned 137 days late' runs instantly and nothing gets emailed.
>
> The property I care about is that the test and production take the identical path through the service — the only difference is which object I pass in."
