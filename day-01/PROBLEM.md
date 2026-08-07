# Day 1 — Hotel Room Booking

**Time box: 45 minutes.** Set a timer. Stop when it rings, even if unfinished — an unfinished honest attempt tells me more than a polished one that took three hours.

**No design pattern is expected today.** This is a baseline. Just model the problem with classes that make sense to you.

---

## The problem

Build the core of a hotel room booking system.

A hotel has rooms. Each room has a number, a type (SINGLE, DOUBLE, SUITE), and a price per night. Guests book rooms for a date range.

### Must support

1. **Add rooms** to the hotel.
2. **Check availability** — is room 101 free between 2026-08-01 and 2026-08-05?
3. **Book a room** for a guest over a date range. A booking must fail if the room is already booked for any overlapping date.
4. **Cancel a booking.**
5. **Find all available rooms** of a given type for a date range.
6. **Total price** of a booking (nights × price per night).

### Rules

- A booking's date range is `[check_in, check_out)` — check-out day is *not* occupied. So a booking 1st→3rd and another 3rd→5th on the same room is legal, not a conflict.
- Booking a room that doesn't exist should fail cleanly.
- `check_out` must be strictly after `check_in`.

### Constraints

- In-memory only. No database, no file I/O, no web framework.
- Standard library only. Python: `datetime` is fine. Java: `java.time.LocalDate` is fine.
- Single file per language: `solution.py` and `Solution.java`.
- No `input()` / `Scanner` — no interactive prompts.

---

## What to hand in

Two files in this folder:

- `solution.py` — with an `if __name__ == "__main__":` block
- `Solution.java` — with a `public static void main(String[] args)`

Each one must contain **asserts that prove your code works**. At minimum, prove:

- a normal booking succeeds and its total price is right
- an overlapping booking is rejected
- a back-to-back booking (checkout day == next checkin day) is **accepted**
- after cancelling, the room is bookable again
- searching by type returns only rooms that are actually free

Print something on success so I can see it ran — e.g. `print("all checks passed")`.

---

## Deliberately not specified

Some things above are vague. **That is intentional.** How do bookings get identified for cancellation? What does "book" return? Where does a Guest live in your model? What happens on a failed booking — exception, `None`, a result object?

Make a call, and be ready to defend it. Interviewers leave gaps on purpose; noticing them and choosing deliberately is half the score. If you want to note your assumptions, put them in a comment at the top of each file.

---

When you're done, just say **done** and I'll run both files and review them.
