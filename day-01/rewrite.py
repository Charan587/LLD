"""Day 1 — Hotel Room Booking. Interview-grade rewrite.

═══════════════════════════════════════════════════════════════════════════
INTERVIEW WALKTHROUGH — what you say out loud, in order
═══════════════════════════════════════════════════════════════════════════

1. READ-BACK (~20s)
   "A hotel with rooms; each room has a number, a type and a nightly price.
    Guests book date ranges. I must stop double-bookings, price a stay, and
    search free rooms by type."

2. CLARIFYING QUESTIONS (3, not 10)
   - "Is checkout day occupied? i.e. can 1st-3rd and 3rd-5th both exist?"
     -> this single answer decides every comparison operator in the file
   - "How is a booking identified for cancellation — a reference, or the
      room plus dates?"
   - "In-memory, or should I assume persistence and concurrency?"

3. HOW I FOUND THE CLASSES
   Underline the nouns: hotel, room, room type, price, guest, booking, date range.
     room        -> has number, type, price          -> Room       (class)
     booking     -> has identity, dates, a guest     -> Booking    (class)
     room type   -> a fixed small set                -> RoomType   (enum)
     guest       -> only a name today                -> str, and I say so
     date range  -> two dates on the Booking         -> no class yet
   Circle the verbs: add, check availability, book, cancel, search, price.
   Whoever owns the data owns the method: Hotel owns rooms and bookings.

   THE TRAP HERE: if Room isn't a class, room type and per-room price have
   nowhere to live, and "find rooms of a given type" silently becomes
   unimplementable. A dropped noun is a dropped requirement.

4. ASSUMPTIONS
   - Half-open [check_in, check_out): checkout day is free. Back-to-back is legal.
   - Bookings get a generated integer id; cancel is by id, O(1).
   - Failure raises ValueError; the caller decides how to present it.
   - Single-threaded, in-memory.

5. THE DESIGN I REJECTED
   "Storing rooms as bare ints with a dict of booked date ranges. It works
    for availability, but there's nowhere to hang a room type or a per-room
    price, so requirement 5 can't be built. Also I'd have enumerated the
    overlap cases by hand and missed one."

6. THE DESIGN + WHAT MATTERS
   "No pattern needed — this is plain modelling. The one thing I'd highlight
    is overlaps() as a named function rather than inline conditions: two
    comparisons, derived by negating 'when do they NOT overlap', so there's
    no case to forget. Room is frozen so a price change can't retroactively
    reprice past bookings."

7. LIMITS I'D VOLUNTEER
   - "Linear scan over bookings. Fine for a hotel, wrong at Airbnb scale —
      there I'd want an index on (room_id, check_in) or an interval tree."
   - "Nothing is thread-safe; two concurrent bookings of one room would need
      a per-room lock."
   - "Seasonal pricing doesn't belong on Room — it changes weekly while the
      room number doesn't. That wants a rate calendar."

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from itertools import count


class RoomType(Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    SUITE = "SUITE"


@dataclass(frozen=True)
class Room:
    number: int
    room_type: RoomType
    price_per_night: int


@dataclass(frozen=True)
class Booking:
    id: int
    room_number: int
    guest: str
    check_in: date
    check_out: date

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days


def overlaps(a_in: date, a_out: date, b_in: date, b_out: date) -> bool:
    """Half-open [check_in, check_out): touching ranges do not overlap."""
    return a_in < b_out and b_in < a_out


class Hotel:
    def __init__(self) -> None:
        self._rooms: dict[int, Room] = {}
        self._bookings: dict[int, Booking] = {}
        self._ids = count(1)

    def add_room(self, room: Room) -> None:
        if room.number in self._rooms:
            raise ValueError(f"room {room.number} already exists")
        self._rooms[room.number] = room

    def is_available(self, room_number: int, check_in: date, check_out: date) -> bool:
        self._validate(room_number, check_in, check_out)
        return not any(
            overlaps(check_in, check_out, b.check_in, b.check_out)
            for b in self._bookings.values()
            if b.room_number == room_number
        )

    def book(self, room_number: int, guest: str, check_in: date, check_out: date) -> Booking:
        if not self.is_available(room_number, check_in, check_out):
            raise ValueError(f"room {room_number} is not free for those dates")
        booking = Booking(next(self._ids), room_number, guest, check_in, check_out)
        self._bookings[booking.id] = booking
        return booking

    def cancel(self, booking_id: int) -> None:
        if self._bookings.pop(booking_id, None) is None:
            raise ValueError(f"no booking {booking_id}")

    def available_rooms(self, room_type: RoomType, check_in: date, check_out: date) -> list[Room]:
        return [
            room
            for room in self._rooms.values()
            if room.room_type is room_type
            and self.is_available(room.number, check_in, check_out)
        ]

    def total_price(self, booking_id: int) -> int:
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise ValueError(f"no booking {booking_id}")
        return self._rooms[booking.room_number].price_per_night * booking.nights

    def _validate(self, room_number: int, check_in: date, check_out: date) -> None:
        if room_number not in self._rooms:
            raise ValueError(f"no room {room_number}")
        if check_out <= check_in:
            raise ValueError("check_out must be after check_in")


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


if __name__ == "__main__":
    d = lambda day: date(2026, 8, day)

    hotel = Hotel()
    hotel.add_room(Room(101, RoomType.SINGLE, 100))
    hotel.add_room(Room(102, RoomType.SINGLE, 100))
    hotel.add_room(Room(201, RoomType.SUITE, 500))

    # normal booking + price
    b = hotel.book(101, "charan", d(1), d(5))
    assert b.nights == 4
    assert hotel.total_price(b.id) == 400

    # every flavour of overlap is rejected
    assert raises(hotel.book, 101, "x", d(1), d(5))   # exact
    assert raises(hotel.book, 101, "x", d(2), d(4))   # inside
    assert raises(hotel.book, 101, "x", d(3), d(8))   # right overlap  <-- submitted version allowed this
    assert raises(hotel.book, 101, "x", d(1) , d(3))  # left overlap

    # back-to-back is legal: [1,5) then [5,7)
    b2 = hotel.book(101, "y", d(5), d(7))
    assert hotel.total_price(b2.id) == 200

    # bad input
    assert raises(hotel.book, 101, "x", d(5), d(1))   # reversed range
    assert raises(hotel.book, 101, "x", d(5), d(5))   # zero nights
    assert raises(hotel.book, 999, "x", d(1), d(5))   # no such room

    # search by type only returns genuinely free rooms
    assert [r.number for r in hotel.available_rooms(RoomType.SINGLE, d(1), d(5))] == [102]
    assert [r.number for r in hotel.available_rooms(RoomType.SUITE, d(1), d(5))] == [201]

    # cancel frees the room again
    hotel.cancel(b.id)
    assert hotel.is_available(101, d(1), d(5))
    assert raises(hotel.cancel, b.id)  # double cancel

    print("all checks passed")
