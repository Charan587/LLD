# Day 5 Review — Library Lending (Python)

Reviewed 2026-08-03. Submission preserved as `solution.submitted.py`.

## Verdict

`python3 solution.py` → **AssertionError at line 156.**

**The inversion is textbook, and this was the hardest of the five.** Two Protocols, two implementations each, both injected through the constructor, and `Library` never learns which it got:

```python
class Clock(Protocol):    def today(self) -> date: ...
class Notifier(Protocol): def send(self, to: str, message: str) -> None: ...

library = Library(..., clock, notifier, ...)
```

Every fee number is right too — 0 at the boundary, 5, 25, and 200 capped, with `max(0, min(...))` correctly floored *and* ceilinged. Days 1-4 fee/boundary arithmetic has been the weak spot; today it's clean.

Then three rules that were specified didn't get built, and the assert that would have proved the day's point wasn't written.

## Score

| Axis | D1 | D2 | D3 | D4 | D5 | Why |
|---|---|---|---|---|---|---|
| Correctness | 1 | 3 | 1 | 2 | **2** / 5 | Doesn't run. Rule 2 absent — a book can be lent twice. Max-loans off by one. Reminder fires forever. |
| Extensibility | 1 | 4 | 2 | 4 | **4** / 5 | Clock, notifier, period, rate, cap, max-loans all injected — the per-tier requirement is already served |
| SOLID | 1 | 3 | 3 | 4 | **4** / 5 | DIP done properly. `Library` is drifting toward a god class; `notify_overdue_members` finds, formats, and sends |
| Readability | 2 | 2 | 2 | 3 | **3** / 5 | 10-parameter constructor on one line; method named for overdue but sends reminders; `FakeNotifier` prints |
| Communication | 1 | 2 | 1 | 2 | **3** / 5 | Assumptions present; principle named but not explained; rejected design absent |

**16 / 25.** Best so far, and the upward trend is real: 6 → 14 → 9 → 15 → 16.

---

## What actually failed

### Rule 2 was never implemented — a book can be lent to two people

```
m1 checks out b1 -> 2026-01-15
m2 checks out b1 -> 2026-01-15  <-- SAME book, two members
loans on b1 now  : 2
```

`checkout_book` checks `if book not in self.books` — *does the library own this title* — and nothing else. It never asks whether the copy is currently out. Under your own stated assumption of one copy per title, the same physical book is now in two people's hands.

**Your assert caught it.** Line 156 is exactly the right test and it failed honestly. That's the system working — you wrote the check, it found a real missing rule, and the file refused to pass. Contrast day 4, where three bugs survived because the asserts that would have caught them were never written.

The fix is the query you already wrote in `return_book`:

```python
loan = next((l for l in self.loans if l.book == book and l.checkin_date is None), None)
```

That's *"is there an open loan for this book"* — the availability check, present in `return_book` and missing from `checkout_book`. Extract it once and call it from both:

```python
def _open_loan_for(self, book):
    return next((l for l in self.loans if l.book == book and l.is_open), None)
```

**Two methods needing the same question is the signal to name the question.** Once it has a name, forgetting to ask it in one place becomes obvious.

### Max loans is off by one — W4, fifth consecutive day

```
loan #1 allowed  (member now holds 1)
loan #2 allowed  (member now holds 2)
loan #3 allowed  (member now holds 3)
loan #4 allowed  (member now holds 4)     <-- max_books_per_member = 3
loan #5 REJECTED
```

```python
if len(self.member_loans[member]) > self.max_books_per_member:
```

The check runs *before* the new loan is added, so it must ask "am I already at the limit?" — `>=`, not `>`. With `>` a member holding exactly 3 passes.

Your assert didn't catch it because earlier asserts had left stray loans on `member1`, so by line 161 he already held four. **The assert passed for the wrong reason.** That's what shared mutable state across asserts does — see the note on test isolation below.

Fifth day in a row for `>` vs `>=`: day 1's back-to-back booking, day 3's ₹1000 threshold, day 4's fee gate, and now this. Worth a deliberate habit: **every time you write a comparison against a limit, say out loud whether the limit itself is allowed**, then pick the operator.

### The reminder fires forever

```
today=2026-01-12  sent=0
today=2026-01-13  sent=1     <-- correct
today=2026-01-14  sent=1
today=2026-01-15  sent=1
today=2026-01-20  sent=1
today=2026-06-01  sent=1     <-- still reminding, 4 months later
```

```python
if today >= loan.due_date - timedelta(days=2):
```

`>=` means "on or after two days before due" — which is true forever after. Rule 6 says *two days before*, one specific day:

```python
if loan.due_on == self.clock.today() + timedelta(days=self.policy.reminder_days_before):
```

The two cases the spec named (fires on the 13th, not on the 12th) both pass with your version, which is exactly why assert 9 mattered — it would have made you test the *other* side, and the other side is where the bug is.

The method name carries the same confusion: `notify_overdue_members`, and the message says *"the book is overdue"*. But this is a **reminder before the due date** — on 2026-01-13 nothing is overdue. Rule 6 and "overdue notices" are two different features; naming one as the other is how they get merged by accident.

---

## The assert that wasn't written

```python
library.notify_overdue_members()      # line 163. Nothing follows it.
```

You built `FakeNotifier`, gave it a `sent_messages` list, appended to it faithfully — **and never read it.** The call is made, the result is discarded, and the run is identical whether it sends one message, six, or none.

Assert 9 was the point of the day:

> *the reminder fires on 2026-01-13 and not on 2026-01-12 — assert on what the notifier received*

```python
assert notifier.sent == [("alice@example.com", "'The Great Gatsby' is due on 2026-01-15")]
```

That single line is what the whole inversion was *for*. Without it, `Clock` and `Notifier` are structure with nothing leaning on them — you built the scaffolding and didn't hang anything from it.

**This is W13, fifth day.** Nine of ten asserts written, up from about half — real progress — but the one omitted was the one the spec flagged as the requirement that decides the design.

## Test isolation

Every assert shares one `library`, one `member1`, one `book1`, and every loan from every earlier assert is still sitting in `self.loans`. Consequences:

- The max-loans assert passed for the wrong reason, hiding the off-by-one.
- Line 160 checks out `book3`, which was **never added to the library** — it would have raised `"Book not available"`, and the assert expects a due date. Another latent failure, invisible because line 156 dies first.
- Any assert you add anywhere shifts the meaning of the ones after it.

Fix is one helper:

```python
def service(today=date(2026, 1, 13)):
    n = FakeNotifier()
    return LendingService(FixedClock(today), n), n

svc, notifier = service()      # fresh state, every time
```

Three lines, and each assert becomes independently true. **Day 3 had the same shape** — five identical `attack` calls whose meaning depended on position. Tests that depend on execution order aren't tests, they're a script.

## Smaller things

- **`FakeNotifier.send` prints.** The spec said no `print` in business logic, and the fake doesn't need it — the list *is* the record. Printing is what you do when you can't assert; you built the thing that lets you assert, then printed anyway.
- **`EmailNotifier.send` prints too** — fine as a stand-in for SMTP, worth a comment saying so.
- **10-parameter constructor on one line.** The five policy values (`period`, `rate`, `cap`, `max_loans`, and a reminder offset) travel together and always will — that's a `LoanPolicy` dataclass. It also *is* the "different period and rate per member tier" requirement: pass a different policy, no new code.
- **`member_loans` never shrinks correctly on an unknown member** — `self.member_loans[member]` raises `KeyError` for a member not passed to the constructor, rather than a clear error.
- **`Loan` has `checkin_date` but no `is_open`.** You wrote `loan.checkin_date is None` inline in `return_book` and again in `notify_overdue_members`. Third time it's needed it becomes a property.
- **`raises()` returns the exception object**, so `assert raises(...)` passes on any truthy exception. Fine, but it can't distinguish "raised the error I expected" from "crashed for an unrelated reason." Catching `ValueError` specifically is stricter.

## The rewrite

`rewrite.py`, verified `all checks passed`. **Your Clock/Notifier inversion is kept exactly as you wrote it.** What changed: rule 2 via `_open_loan_for`, `>=` on max loans, `==` on the reminder day, `LoanPolicy` for the knobs, a `service()` helper so every assert starts clean, and asserts that read `notifier.sent`.

Note the last block — a premium tier with a 30-day period and ₹2/day fee is a different `LoanPolicy`, no new class and no edits. That's the payoff for having injected the config alongside the dependencies, which you did unprompted.

## Grill

1. I claimed `notify_overdue_members` is misnamed because nothing is overdue on 2026-01-13. **Now build the actual overdue feature** — a daily notice for books already late. How much of my rewrite changes?
Nothing much changes just get a common function and call two functio other for over due and under due . changed the target in common its done
2. `FixedClock` returns the same date forever. **Write the two-line clock** that a test would need if a method called `today()` twice and had to see two different days.
i didnt understand eveyrtime different days or settinng different date from to is change date would add it we can add that methid . is you question asking about threads or what 
3. My `Loan.fee(on, policy)` takes the policy as an argument instead of `Loan` holding one. **Argue for holding it instead**, and say what breaks when the library changes its rate next year.
as we sending policy it easy to use max fee and number of late fee per day . if library changed it rates and we are not sending policy or initikay doing it hardcoded it could give wrong fee 
4. Requirement: loans stored in Postgres instead of memory. **Which of my classes changes**, and what new abstraction appears? Name the principle.
loan changes as we cant have rule there for fee . loan abstraction apperas and it would be single responsibilty priciple
5. `SystemClock` and `FixedClock` both satisfy `Clock`. **Name a bug that a `FixedClock` in production would cause** that no test would catch.
when we dont have a check defining fixed clock like if env dev choose fixed else system like that 
6. You injected `clock` and `notifier` but constructed `member_loans` inside `Library`. **Is that inconsistent?** When is "make it yourself" the right call?

i was just mapping it for easy access as yiu did we could juts trackl loans for this . make it yourself would be right call if we are taking instances not classes 
