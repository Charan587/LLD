# LLD Training Track

Daily low-level design practice in Python + Java. ~1 hr/day, ~90 days, aimed at FAANG/MAANG machine-coding rounds.

## How this works

1. You say **`next`** (or `day N`) → I write `day-NN/PROBLEM.md`.
2. You implement `solution.py` and `Solution.java`, each with asserts in main.
3. You say **`done`** → I run both files, write `day-NN/REVIEW.md`, and update the table below.

Problems never name the pattern they're testing. You solve it your way first; the review is where the pattern, the SOLID violation, and the interview-grade rewrite show up.

## Rules for you

- **Time box every problem.** Stated at the top of each PROBLEM.md. Stop when it rings.
- **Don't look up the answer first.** A wrong attempt you reasoned through is worth more than a correct one you copied. I can tell the difference, and grading a copy teaches you nothing.
- **Write the asserts before you think you're done.** They're the spec talking back to you.

## Scoring

Each day scored 0-5 on five axes: **Correctness**, **Extensibility**, **SOLID**, **Readability**, **Communication**.
Anything below 3 gets a harder repeat problem later in the track.

## Progress

Full verbatim log — run output, defects, standing weaknesses — lives in **[PROGRESS.md](PROGRESS.md)**.

| Day | Problem | Topic | Cor | Ext | SOL | Rd | Com | Total |
|-----|---------|-------|-----|-----|-----|----|----|-------|
| 01 | Hotel Room Booking | baseline, no pattern | 1 | 1 | 1 | 2 | 1 | 6/25 (py) |

## Curriculum — 45 days

Extendable later. If day 45 arrives and the machine-coding reps feel thin, we add a Phase 5 with the problems held back below.

### Phase 1 — Foundations (days 1-6)

| Day | Topic |
|-----|-------|
| 1 | Baseline, no pattern — raw class design |
| 2 | Composition vs inheritance; interfaces vs abstract classes |
| 3 | SRP + OCP |
| 4 | LSP + ISP |
| 5 | DIP |
| 6 | Consolidation — one problem violating three principles at once |

### Phase 2 — Patterns (days 7-26)

Interview-relevant patterns only. Siblings are paired into one day where the second is a 10-minute delta on the first.

| Days | Patterns |
|------|----------|
| 7-10 | Strategy · Factory Method + Abstract Factory · Builder · Singleton (and why interviewers push back on it) |
| 11 | **Consolidation** |
| 12-15 | Observer · State · Command · Chain of Responsibility |
| 16 | **Consolidation** |
| 17-20 | Adapter · Decorator · Composite · Proxy + Facade |
| 21 | **Consolidation** |
| 22-25 | Template Method · Iterator · Flyweight · Mediator |
| 26 | **Consolidation** |

Cut from daily coverage: Bridge, Prototype, Memento, Visitor, Interpreter. They appear as a one-page note in `notes/` with a "recognise it, don't drill it" summary. They essentially never come up in machine-coding rounds, and drilling them is what would have made this 90 days.

### Phase 3 — Machine coding (days 27-40)

Fourteen problems, one per day, **45-minute box**, concurrency where realistic:

Parking Lot · Elevator · Splitwise · Vending Machine · Tic-Tac-Toe → Chess · Snake & Ladder · ATM · LRU Cache (thread-safe) · Rate Limiter · Logging Framework · Notification Service · BookMyShow · Cab Booking (Uber) · Food Delivery

Held back for a later phase: Library Management, Auction, Card Game, File System, Text Editor, Meeting Scheduler.

### Phase 4 — Interview simulation (days 41-45)

Five full 60-min rounds: 10 min clarifying questions (I play a deliberately vague interviewer), 35 min code, 15 min defending your design under pressure. These days run over an hour by design — they're the dress rehearsal.

## Setup

- Python 3.11 — `python3 solution.py`
- Java 21 via Homebrew — `/opt/homebrew/opt/openjdk@21/bin/java Solution.java`

  Optional, so plain `java` works in your shell — add to `~/.zshrc`:
  ```bash
  export PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"
  ```

No Maven, no Gradle, no pytest, no JUnit. Single file, asserts in main — that's what a machine-coding round actually allows.
