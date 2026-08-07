"""In this we have member , books , checkout and assuming only book will one acroos all library i.e one quantity
 from date time libarary we get today . i mentioned checkout because it holds data of book , check in date checkout date of the loans
  member(name,joined_date, email) ,  book(name,author), loan(book, checkout_date, checkin_date,  due_date) , library(books, members, loans)


  so lets think about dependency inversion principle 
  """

from datetime import date, timedelta
from typing import Protocol, runtime_checkable

@runtime_checkable
class Clock(Protocol):
    def today(self) -> date:
        ...

@runtime_checkable
class Notifier(Protocol):
    def send(self, to: str,message: str) -> None:
        ...


class SystemClock:
    def today(self) -> date:
        return date.today()

class FixedClock:
    def __init__(self, fixed_date: date):
        self.fixed_date = fixed_date

    def today(self) -> date:
        return self.fixed_date

class EmailNotifier:
    def send(self, to: str, message: str) -> None:
        print(f"Sending email to {to}: {message}")

class FakeNotifier:

    def __init__(self):
        self.sent_messages = []

    def send(self, to: str, message: str) -> None:
        self.sent_messages.append((to, message))
        print(f"Fake sending email to {to}: {message}")


class Book:
    def __init__(self, title: str, author: str):
        self.title = title
        self.author = author

class Member:
    def __init__(self, name: str, joined_date: date, email: str):
        self.name = name
        self.joined_date = joined_date
        self.email = email

class Loan:
    def __init__(self, book: Book, checkout_date: date, due_date: date):
        self.book = book
        self.checkout_date = checkout_date
        self.due_date = due_date
        self.checkin_date = None

    def checkin(self, checkin_date: date) -> None:
        self.checkin_date = checkin_date

class Library:
    def __init__(self, books: list[Book], members: list[Member], loans: list[Loan], clock: Clock, notifier: Notifier, checkout_period_days: int = 14, late_fee_per_day: float = 5, max_late_fee: float = 200, max_books_per_member: int = 3):
        self.books = books
        self.members = members
        self.loans = loans
        self.clock = clock
        self.notifier = notifier
        self.checkout_period_days = checkout_period_days
        self.late_fee_per_day = late_fee_per_day
        self.max_late_fee = max_late_fee
        self.max_books_per_member = max_books_per_member
        self.member_loans = {member: [] for member in members}

    def add_book(self, book: Book) -> None:
        self.books.append(book)

    def add_member(self, member: Member) -> None:
        self.members.append(member)
        self.member_loans[member] = []

    def checkout_book(self, book: Book, member: Member, checkout_date: date) -> date:
        if book not in self.books:
            raise ValueError("Book not available in the library.")
        if len(self.member_loans[member]) > self.max_books_per_member:
            raise ValueError("Member has reached the maximum number of books allowed.")
        due_date = checkout_date + timedelta(days=self.checkout_period_days)
        loan = Loan(book, checkout_date, due_date)
        self.loans.append(loan)
        self.member_loans[member].append(loan)
        return due_date

    def return_book(self, book: Book, member: Member, checkin_date: date) -> float:
        loan = next((loan for loan in self.loans if loan.book == book and loan.checkin_date is None), None)
        if not loan:
            raise ValueError("Book not checked out.")
        loan.checkin(checkin_date)
        self.member_loans[member].remove(loan)
        late_days = (checkin_date - loan.due_date).days
        late_fee = max(0, min(late_days * self.late_fee_per_day, self.max_late_fee))
        return late_fee

    def notify_overdue_members(self) -> None:
        today = self.clock.today()
        for member, loans in self.member_loans.items():
            for loan in loans:
                # it should send notification before 2 days of due date 
                if loan.checkin_date is None and today >= loan.due_date - timedelta(days=2):
                    message = f"Dear {member.name}, the book '{loan.book.title}' is overdue. Please return it as soon as possible."
                    self.notifier.send(member.email, message)

    


def raises(fn, *args):
    try:
        fn(*args)
    except Exception as e:
        return e
    return None


if __name__ == "__main__":
    clock = FixedClock(date(2026, 1, 13))
    notifier = FakeNotifier()

    book1=Book("The Great Gatsby", "F. Scott Fitzgerald")
    book2=Book("To Kill a Mockingbird", "Harper Lee")
    book3=Book("1984", "George Orwell")
    book4=Book("Pride and Prejudice", "Jane Austen")
    member1=Member("Alice", date(2023, 1, 15), "alice@example.com")
    member2=Member("Bob", date(2023, 2, 20), "bob@example.com")

    library = Library([book1, book2], [member1, member2], [], clock, notifier, checkout_period_days=14 , late_fee_per_day=5, max_late_fee=200 , max_books_per_member=3)

    assert library.checkout_book(book1, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert library.return_book(book1, member1,date(2026,1,15))==  0

    assert library.checkout_book(book1, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert library.return_book(book1, member1,date(2026,1,16))==  5

    assert library.checkout_book(book1, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert library.return_book(book1, member1,date(2026,1,20))==  25

    assert library.checkout_book(book1, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert library.return_book(book1, member1,date(2026,6,1))==  200

    assert library.checkout_book(book1, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert raises(library.checkout_book, book1, member2,date(2026,1,1)) 

    assert library.checkout_book(book1, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert library.checkout_book(book2, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert library.checkout_book(book3, member1,date(2026,1,1))==  date(2026, 1, 15)
    assert raises(library.checkout_book, book4, member1,date(2026,1,1))

    library.notify_overdue_members() 








