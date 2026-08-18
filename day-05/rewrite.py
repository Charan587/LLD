"""Day 5 — Library Lending. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "Members borrow books for 14 days, late fees at 5/day capped at 200,
    reminders two days before due, max 3 loans. The requirement shaping my
    design is that the tests must run instantly and must not send email."

2. CLARIFYING QUESTIONS
   - "Is the reminder exactly two days before, or two days or fewer?"
     -> 'or fewer' means it fires every day forever; worth pinning down
   - "One copy per title, or multiple copies?"
   - "Do I control the clock, or should I assume real time?"
     -> asking this out loud IS the DIP answer

3. HOW I FOUND THE CLASSES
   Nouns: member, book, loan, due date, late fee, reminder.
     book   -> title/author, data                  -> Book
     member -> name/email, data                    -> Member
     loan   -> the noun that actually matters      -> Loan
   "Checkout" is a VERB. The thing that persists is a Loan. Naming it after
   the verb is how people end up without the noun.

   Then the two nouns that aren't in the statement but are in requirement 8:
     "today"        -> Clock
     "sends email"  -> Notifier
   Anything that reaches outside the process becomes an injected dependency.

4. ASSUMPTIONS
   - Loan period, fee rate, cap and max-loans are policy values, injected —
     which also answers the per-tier requirement for free.
   - Reminder fires on exactly one day.
   - Fees computed at return time from the return date passed in.

5. THE DESIGN I REJECTED
   "Calling date.today() inside the fee calculation and constructing an SMTP
    client inside the service. It runs fine — that's what makes it dangerous.
    It's simply untestable: assert 5 needs a book 137 days late, and I'm not
    waiting 137 days or emailing anyone from a test suite."

6. THE DESIGN + PRINCIPLE NAME
   "DEPENDENCY INVERSION. Normally the high-level LendingService would depend
    on low-level things — the system clock, SMTP. Inverted, both depend on an
    abstraction: Clock and Notifier. The service never learns which
    implementation it got."
   "The tell that it's right: my test and production take the IDENTICAL path
    through LendingService. Nothing is test-only."

7. LIMITS I'D VOLUNTEER
   - "Loans are a list in memory. Postgres would mean a LoanRepository
      protocol — same inversion, third dependency."
   - "FixedClock in production would be silent and catastrophic: nothing
      ever goes overdue. The wiring is the one line tests never execute."
   - "A rate change today reprices open loans. Contract terms should be
      captured on the Loan at checkout."

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def today(self) -> date: ...


@runtime_checkable
class Notifier(Protocol):
    def send(self, to: str, message: str) -> None: ...


class SystemClock:
    def today(self) -> date:
        return date.today()


class FixedClock:
    def __init__(self, fixed: date):
        self.fixed = fixed

    def today(self) -> date:
        return self.fixed


class EmailNotifier:
    def send(self, to: str, message: str) -> None:
        ...  # smtp_send(to, message)


class FakeNotifier:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))          # no print — the list IS the record


@dataclass(frozen=True)
class Book:
    title: str
    author: str


@dataclass(frozen=True)
class Member:
    name: str
    email: str


@dataclass(frozen=True)
class LoanPolicy:
    """All the knobs in one place — serves 'different period and rate per tier'."""
    period_days: int = 14
    fee_per_day: float = 5
    max_fee: float = 200
    max_loans: int = 3
    reminder_days_before: int = 2


@dataclass
class Loan:
    book: Book
    member: Member
    checked_out_on: date
    due_on: date
    returned_on: date | None = None

    @property
    def is_open(self) -> bool:
        return self.returned_on is None

    def fee(self, on: date, policy: LoanPolicy) -> float:
        days_late = max(0, (on - self.due_on).days)
        return min(days_late * policy.fee_per_day, policy.max_fee)


class LendingService:
    def __init__(self, clock: Clock, notifier: Notifier, policy: LoanPolicy = LoanPolicy()):
        self.clock = clock
        self.notifier = notifier
        self.policy = policy
        self.loans: list[Loan] = []

    def _open_loan_for(self, book: Book) -> Loan | None:
        return next((l for l in self.loans if l.book == book and l.is_open), None)

    def open_loans_of(self, member: Member) -> list[Loan]:
        return [l for l in self.loans if l.member == member and l.is_open]

    def checkout(self, book: Book, member: Member, on: date) -> Loan:
        if self._open_loan_for(book) is not None:            # rule 2
            raise ValueError(f"{book.title!r} is already on loan")
        if len(self.open_loans_of(member)) >= self.policy.max_loans:   # >= not >
            raise ValueError(f"{member.name} already holds {self.policy.max_loans} loans")
        loan = Loan(book, member, on, on + timedelta(days=self.policy.period_days))
        self.loans.append(loan)
        return loan

    def return_book(self, book: Book, on: date) -> float:
        loan = self._open_loan_for(book)
        if loan is None:
            raise ValueError(f"{book.title!r} is not on loan")
        loan.returned_on = on
        return loan.fee(on, self.policy)

    def send_due_reminders(self) -> None:
        target = self.clock.today() + timedelta(days=self.policy.reminder_days_before)
        for loan in self.loans:
            if loan.is_open and loan.due_on == target:       # == , exactly one day
                self.notifier.send(
                    loan.member.email,
                    f"{loan.book.title!r} is due on {loan.due_on}",
                )


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    GATSBY = Book("The Great Gatsby", "Fitzgerald")
    MOCKINGBIRD = Book("To Kill a Mockingbird", "Lee")
    NINETEEN84 = Book("1984", "Orwell")
    PRIDE = Book("Pride and Prejudice", "Austen")
    ALICE = Member("Alice", "alice@example.com")
    BOB = Member("Bob", "bob@example.com")

    def service(today=date(2026, 1, 13)):
        n = FakeNotifier()
        return LendingService(FixedClock(today), n), n

    # 1 — due date
    svc, _ = service()
    assert svc.checkout(GATSBY, ALICE, date(2026, 1, 1)).due_on == date(2026, 1, 15)

    # 2-5 — fees, including the boundary and the cap
    for returned_on, expected in [(date(2026, 1, 15), 0),
                                  (date(2026, 1, 16), 5),
                                  (date(2026, 1, 20), 25),
                                  (date(2026, 6, 1), 200)]:
        svc, _ = service()
        svc.checkout(GATSBY, ALICE, date(2026, 1, 1))
        assert svc.return_book(GATSBY, returned_on) == expected, (returned_on, expected)

    # 6 — already on loan, and the original loan survives the attempt
    svc, _ = service()
    original = svc.checkout(GATSBY, ALICE, date(2026, 1, 1))
    assert raises(svc.checkout, GATSBY, BOB, date(2026, 1, 2))
    assert len(svc.loans) == 1
    assert original.member == ALICE and original.due_on == date(2026, 1, 15)

    # 7 — returned books can go out again
    svc.return_book(GATSBY, date(2026, 1, 10))
    assert svc.checkout(GATSBY, BOB, date(2026, 1, 11)).due_on == date(2026, 1, 25)

    # 8 — the 4th loan is refused, the 3rd is not
    svc, _ = service()
    for b in (GATSBY, MOCKINGBIRD, NINETEEN84):
        svc.checkout(b, ALICE, date(2026, 1, 1))
    assert len(svc.open_loans_of(ALICE)) == 3
    assert raises(svc.checkout, PRIDE, ALICE, date(2026, 1, 1))
    # returning one frees a slot
    svc.return_book(GATSBY, date(2026, 1, 2))
    assert svc.checkout(PRIDE, ALICE, date(2026, 1, 2)).due_on == date(2026, 1, 16)

    # 9 — the reminder. Assert on what the notifier RECEIVED.
    svc, notifier = service(today=date(2026, 1, 13))
    svc.checkout(GATSBY, ALICE, date(2026, 1, 1))            # due 2026-01-15
    svc.send_due_reminders()
    assert notifier.sent == [("alice@example.com", "'The Great Gatsby' is due on 2026-01-15")]

    # and on no other day — including after it is due
    for day in [date(2026, 1, 12), date(2026, 1, 14), date(2026, 1, 15), date(2026, 6, 1)]:
        svc, notifier = service(today=day)
        svc.checkout(GATSBY, ALICE, date(2026, 1, 1))
        svc.send_due_reminders()
        assert notifier.sent == [], (day, notifier.sent)

    # a returned book never gets a reminder
    svc, notifier = service(today=date(2026, 1, 13))
    svc.checkout(GATSBY, ALICE, date(2026, 1, 1))
    svc.return_book(GATSBY, date(2026, 1, 5))
    svc.send_due_reminders()
    assert notifier.sent == []

    # 10 — returning something never checked out
    svc, _ = service()
    assert raises(svc.return_book, PRIDE, date(2026, 1, 20))

    # policy is data: a premium tier needs no new code
    premium = LoanPolicy(period_days=30, fee_per_day=2, max_fee=100, max_loans=10)
    svc = LendingService(FixedClock(date(2026, 1, 13)), FakeNotifier(), premium)
    assert svc.checkout(GATSBY, ALICE, date(2026, 1, 1)).due_on == date(2026, 1, 31)
    assert svc.return_book(GATSBY, date(2026, 2, 10)) == 20

    print("all checks passed")
