# Day 5 — Library Lending

**Time box: 45 minutes.** Timer on. Ask scoping questions if you want them.

---

## The problem

Build the lending core of a library.

A **member** borrows a **book**. The loan runs **14 days** from the checkout date.

### Rules

1. **Checkout** records who borrowed what and when, and computes a **due date** = checkout date + 14 days.
2. A book already on loan **cannot** be checked out again.
3. **Return** marks the book available and computes the late fee.
4. **Late fee** = ₹5 per day *past* the due date. Returning **on** the due date is free.
5. The fee is **capped at ₹200**, however late the return is.
6. Two days before a loan is due, the member is **sent a reminder**.
7. A member may hold at most **3 loans** at once.

### Worked example — use these for your asserts

Checkout on **2026-01-01** → due **2026-01-15**.

| Returned on | Days late | Fee |
|---|---|---|
| 2026-01-15 | 0 | ₹0 |
| 2026-01-16 | 1 | ₹5 |
| 2026-01-20 | 5 | ₹25 |
| 2026-06-01 | 137 | ₹200 (capped) |

### Later we must support (do not build it)

- Reminders by SMS and by push, not just email.
- Loans stored in Postgres instead of memory.
- A different loan period and fee rate per member tier.

### Constraints

- In-memory, standard library only. `datetime.date` is fine.
- **No `print()` inside your business logic.**
- `solution.py` required.

---

## The requirement that decides your design

8. **Every assert below must run in well under a second, and must not send a real email.**

You need to test a book returned 137 days late. You are not going to wait 137 days, and your test suite is not going to email anyone. Work out what that means for how `LendingService` gets hold of *today's date* and of *the thing that sends reminders* — before you write either one.

If your first instinct is to call `date.today()` inside the fee calculation, follow that thought all the way to assert number four and see what happens.

---

## Required before the code

**1. Assumptions.** One line each.

**2. The design you rejected.** One sketch, one sentence on what breaks.

**3. Name the principle.** One this time. It's the fifth SOLID principle and today is named after it. Say in one sentence what it inverts.

---

## Required asserts

**Paste all of these in before you implement. Delete none.** Day 4 you wrote half the list and three of the four bugs I found were sitting on the lines you skipped.

Assert the **value**, not that a call didn't raise.

1. checkout on 2026-01-01 → due date is 2026-01-15
2. returned 2026-01-15 → fee 0  *(the boundary — returning on the due date is free)*
3. returned 2026-01-16 → fee 5
4. returned 2026-01-20 → fee 25
5. returned 2026-06-01 → fee 200, not 685
6. checking out a book that is already on loan → error, and the original loan is unchanged
7. after return, the same book can be checked out again
8. a member holding 3 loans cannot take a 4th → error
9. the reminder fires on 2026-01-13 and **not** on 2026-01-12 — assert on what the notifier *received*, not that nothing crashed
10. returning a book that was never checked out → error

Print `all checks passed` at the end.

---

## When you say done

**Paste the terminal output**, and before you do, check your assumptions block and principle name are still in the file. Day 4 you wrote all three required items and an undo ate them 48 seconds before you submitted.
